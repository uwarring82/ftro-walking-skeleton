#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO Phase-0 IGS artifact pinner.
#
# Retrieves the IGS product files covering the candidate window from a public,
# anonymously accessible data centre and records an FTRO snapshot identity for each:
# concept identifier, retrieval time, byte checksum, size, HTTP metadata and the
# exact retrieval procedure. IGS files carry no provider-issued immutable PID, so
# section 10 of the task card requires the composed FTRO identity used here.
#
# Bytes are cached under data/raw/ and are never redistributed by this repository.

import argparse
import datetime
import hashlib
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pinning
import unixz


# Content-shape validation (FTRO-DEF-018). A retrieval that checks only HTTP status and
# byte checksum will happily pin an authentication interstitial as if it were data --
# CDDIS returns an Earthdata login page with HTTP 200. Status and checksum are necessary
# but not sufficient; the bytes must also look like the product they claim to be.
HTML_MARKERS = (b"<!DOCTYPE html", b"<!doctype html", b"<html", b"<HTML")
AUTH_MARKERS = (b"Earthdata Login", b"oauth", b"Sign In", b"login", b"Log In", b"password")
UNIX_COMPRESS_MAGIC = b"\x1f\x9d"   # .Z files produced by compress(1)
MAX_DECOMPRESSED = 64 << 20          # refuse absurd expansion rather than exhaust memory

# Inner-format signatures, checked AFTER decompression. Magic bytes alone would accept any
# payload with the right first two bytes; a .Z that will not decompress, or decompresses to
# something that is not the product it claims to be, is not validated content.
INNER_FORMAT = {
    "sp3": lambda t: t.startswith("#") and "ORBIT" in t[:120],
    "clk": lambda t: ("RINEX" in t[:400] and "CLOCK" in t[:400]) or "ANALYSIS CENTER" in t[:2000],
    # IGS ERP. Final (igs*.erp) and Rapid (igr*.erp) share almost nothing structurally:
    # Final opens "version 2 / EOP  SOLUTION" with an "X  Y" column header; Rapid opens
    # "version 2 / Source: ..." with an "Xpole Ypole" header and no EOP line. Two earlier
    # signatures guessed from memory and each rejected one of the two families. What the
    # bytes actually share is: a version line, an MJD column, and a UT1-UTC column.
    "erp": lambda t: "version" in t[:200].lower() and "MJD" in t[:3000].upper()
                     and "UT1-UTC" in t[:3000].upper(),
}


def validate_content(name, body, content_type):
    """Return (ok, retrieval_validation, reason). Never raises."""
    if len(body) == 0:
        return False, "content_validated", "empty body"
    head = body[:2048]
    if any(m in head for m in HTML_MARKERS):
        hits = [m.decode(errors="replace") for m in AUTH_MARKERS if m in body[:8192]]
        return False, "content_validated", (
            "response is HTML, not a product file"
            + (f"; authentication markers present: {hits}" if hits else ""))
    if name.endswith(".Z"):
        if not body.startswith(UNIX_COMPRESS_MAGIC):
            return False, "content_validated", (
                f"expected Unix-compress magic 1f9d for a .Z file, got {body[:2].hex()}")
        # Magic is necessary, not sufficient: actually decompress it.
        try:
            plain = unixz.decompress(body, max_output=MAX_DECOMPRESSED)
        except Exception as exc:                                 # noqa: BLE001
            return False, "content_validated", f"magic 1f9d but will not decompress: {exc}"
        if not plain:
            return False, "content_validated", "decompressed to an empty stream"
        text = plain[:4096].decode("ascii", errors="replace")
        kind = name.split(".")[-2].lower() if "." in name[:-2] else ""
        check = INNER_FORMAT.get(kind)
        if check and not check(text):
            return False, "content_validated", (
                f"decompressed, but the content does not look like a {kind.upper()} product")
    if content_type and "html" in content_type.lower():
        return False, "content_validated", f"unexpected Content-Type {content_type!r}"
    return True, "content_validated", "ok"

GPS_EPOCH_MJD = 44244


def mjd_to_gps(mjd):
    d = int(mjd) - GPS_EPOCH_MJD
    return d // 7, d % 7


def mjd_to_date(mjd):
    return (datetime.date(1858, 11, 17) + datetime.timedelta(days=int(mjd))).isoformat()


def fetch(url, timeout=120):
    """Retrieve without writing. Bytes are only cached after validation succeeds."""
    req = urllib.request.Request(url, headers={"User-Agent": "FTRO-walking-skeleton/0.1 (Phase-0 pinning)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), resp.read()


def cache(dest, body):
    tmp = dest + ".part"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mjd-start", type=float, default=59630)
    ap.add_argument("--mjd-end", type=float, default=59640)
    ap.add_argument("--base", default="https://igs.bkg.bund.de/root_ftp/IGS/products/orbits")
    ap.add_argument("--cache", default="data/raw/igs")
    ap.add_argument("--out", default="phase0/reports/igs-artifact-pins.json",
                    help="written where the consumers read it, not to a scratch path")
    ap.add_argument("--series", nargs="+", default=["igs", "igr"],
                    help="product line prefixes: igs=Final, igr=Rapid, igu=Ultra-rapid")
    ap.add_argument("--expect-sha256-manifest", default=None,
                    help="sectioned digest registry; a listed-but-mismatched file fails")
    ap.add_argument("--expect-section", default="igs",
                    help="section of the registry to enforce")
    ap.add_argument("--allow-unpinned", action="store_true",
                    help="permit targets absent from the registry (establishes a first pin)")
    args = ap.parse_args()

    # The registry is SECTIONED ({"igs": {...}, "ppta": {...}, ...}). An earlier version
    # looked names up at the root, so all 57 artifacts pinned with expected_sha256 null
    # while the report still read as enforced (FTRO-DEF-031 v3.0.0).
    expected = pinning.load_section(args.expect_sha256_manifest, args.expect_section,
                                    required=not args.allow_unpinned) \
        if args.expect_sha256_manifest else {}

    os.makedirs(args.cache, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    targets = []
    weeks = set()
    for mjd in range(int(args.mjd_start), int(args.mjd_end) + 1):
        wk, dow = mjd_to_gps(mjd)
        weeks.add(wk)
        for series in args.series:
            for kind, ext in (("orbit", "sp3"), ("clock", "clk")):
                targets.append({"week": wk, "dow": dow, "mjd": mjd, "series": series,
                                "kind": kind, "name": f"{series}{wk}{dow}.{ext}.Z"})
            if series == "igr":
                targets.append({"week": wk, "dow": dow, "mjd": mjd, "series": series,
                                "kind": "erp", "name": f"{series}{wk}{dow}.erp.Z"})
    for wk in sorted(weeks):
        targets.append({"week": wk, "dow": 7, "mjd": None, "series": "igs",
                        "kind": "erp", "name": f"igs{wk}7.erp.Z"})

    # PREFLIGHT: nothing is fetched until every target is covered by the registry.
    uncovered = pinning.preflight(expected, [t["name"] for t in targets],
                                  allow_unpinned=args.allow_unpinned, what="IGS artifact")

    pins, failures = [], []
    for t in targets:
        url = f"{args.base}/{t['week']}/{t['name']}"
        dest = os.path.join(args.cache, t["name"])
        retrieved = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            status, headers, body = fetch(url)
        except Exception as exc:                       # noqa: BLE001 - failure is recorded, not raised
            failures.append({**t, "url": url, "error": f"{type(exc).__name__}: {exc}",
                             "retrieved_utc": retrieved})
            continue
        content_type = headers.get("Content-Type")
        ok, validation_level, reason = validate_content(t["name"], body, content_type)
        digest = hashlib.sha256(body).hexdigest()
        exp = expected.get(t["name"])
        checksum_match = None if exp is None else (digest == exp)
        if checksum_match is False:
            ok, reason = False, f"expected-checksum mismatch: got {digest}, want {exp}"
        if not ok:
            failures.append({**t, "url": url, "retrieved_utc": retrieved,
                             "http_status": status, "size_bytes": len(body),
                             "sha256": hashlib.sha256(body).hexdigest(),
                             "error": f"content validation failed: {reason}",
                             "retrieval_validation": validation_level,
                             "note": ("Status and checksum alone would have accepted these "
                                      "bytes; content-shape validation rejected them.")})
            continue

        cache(dest, body)
        pins.append({
            **t,
            "utc_date": mjd_to_date(t["mjd"]) if t["mjd"] else None,
            "url": url,
            "http_status": status,
            "retrieved_utc": retrieved,
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "md5": hashlib.md5(body).hexdigest(),
            "last_modified": headers.get("Last-Modified"),
            "etag": headers.get("ETag"),
            "content_type": content_type,
            "expected_sha256": exp,
            "checksum_match": checksum_match,
            "retrieval_validation": validation_level,
            "content_validation": reason,
            # Full 64-character digest. An identity that carries a truncated digest is a
            # different and weaker identity; short forms belong in a separate field.
            "ftro_snapshot_id": (
                f"ftro:snapshot:igs/{t['name']}@sha256:{hashlib.sha256(body).hexdigest()}"),
            "sha256_short": hashlib.sha256(body).hexdigest()[:8],
            "concept_id": f"ftro:concept:igs/{t['series']}/{t['kind']}",
        })

    unexpected = [p["name"] for p in pins if p.get("expected_sha256") is None]

    report = {
        "generator": "src/ftro/pin_igs.py",
        "n_without_expected_digest": len(unexpected),
        "uncovered_by_registry": unexpected,
        "base_url": args.base,
        "data_centre": "BKG (Bundesamt für Kartographie und Geodäsie) IGS mirror, anonymous HTTP",
        "candidate_window_mjd": [args.mjd_start, args.mjd_end],
        "retrieval_validation": ("content_validated" if not failures
                                 else "content_validation_incomplete"),
        "availability_time_source": "mirror_derived",
        "availability_time_note": ("last_modified is the BKG mirror's file time, which "
                                   "approximates but is not identical to the IGS release time "
                                   "(FTRO-DEF-019)."),
        "gps_weeks": sorted(weeks),
        "n_pinned": len(pins),
        "n_failed": len(failures),
        "pins": pins,
        "failures": failures,
    }
    ok = bool(pins) and not failures and not unexpected
    pinning.promote(report, args.out, ok)
    print(f"pinned {len(pins)}, failed {len(failures)}, uncovered {len(unexpected)} -> {args.out}")
    for f in failures:
        print(f"REJECTED {f['name']}: {f['error']}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
