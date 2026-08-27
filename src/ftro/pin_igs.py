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
import urllib.error
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
DEFAULT_BASE = "https://garner.ucsd.edu/pub/products"
DEFAULT_DATA_CENTRE = (
    "SIO/SOPAC GARNER IGS global data centre, anonymous HTTPS"
)


def route_metadata(base):
    """Describe only the route actually used; an override cannot inherit SIO metadata."""
    if base.rstrip("/") == DEFAULT_BASE:
        return DEFAULT_DATA_CENTRE, (
            "last_modified is the SIO/GARNER mirror's file time, which approximates "
            "but is not identical to the IGS release time (FTRO-DEF-019)."
        )
    return "operator-supplied retrieval route; data centre not established", (
        "last_modified, when present, is the operator-supplied route's file time; its "
        "relationship to IGS release time and data-centre provenance is not established."
    )


VARIANT_EXPECTATION_KEYS = {
    "sha256", "decoded_sha256", "previous_retrieval_sha256", "change_basis",
}


def variant_expectations(records):
    """Validate structured snapshot-variant records before any provider request."""
    variants = {}
    for name, value in records.items():
        if not isinstance(value, dict):
            continue
        keys = set(value)
        if keys != VARIANT_EXPECTATION_KEYS:
            raise pinning.PreflightError(
                f"preflight: structured IGS expectation {name!r} has keys {sorted(keys)}, "
                f"expected {sorted(VARIANT_EXPECTATION_KEYS)}. Nothing was fetched.")
        malformed = [field for field in (
            "sha256", "decoded_sha256", "previous_retrieval_sha256",
        ) if not pinning.valid_digest(value.get(field))]
        if malformed:
            raise pinning.PreflightError(
                f"preflight: structured IGS expectation {name!r} has malformed "
                f"digest field(s) {malformed}. Nothing was fetched.")
        if value["sha256"] == value["previous_retrieval_sha256"]:
            raise pinning.PreflightError(
                f"preflight: structured IGS expectation {name!r} does not describe a "
                "changed retrieval snapshot. Nothing was fetched.")
        if not isinstance(value.get("change_basis"), str) or not value["change_basis"].strip():
            raise pinning.PreflightError(
                f"preflight: structured IGS expectation {name!r} has no change basis. "
                "Nothing was fetched.")
        variants[name] = value
    return variants


def decoded_variant_evidence(name, body, expectation):
    """Execute, rather than merely store, a structured decoded-content expectation."""
    if not name.endswith(".Z"):
        raise ValueError(f"decoded-content expectation on non-.Z artifact {name}")
    plain = unixz.decompress(body, max_output=MAX_DECOMPRESSED)
    observed = hashlib.sha256(plain).hexdigest()
    expected = expectation["decoded_sha256"]
    return {
        "decoded_size_bytes": len(plain),
        "decoded_sha256": observed,
        "expected_decoded_sha256": expected,
        "decoded_checksum_match": observed == expected,
        "previous_retrieval_sha256": expectation["previous_retrieval_sha256"],
        "snapshot_change_basis": expectation["change_basis"],
    }


def mjd_to_gps(mjd):
    d = int(mjd) - GPS_EPOCH_MJD
    return d // 7, d % 7


def mjd_to_date(mjd):
    return (datetime.date(1858, 11, 17) + datetime.timedelta(days=int(mjd))).isoformat()


def fetch(url, timeout=120):
    """Retrieve without writing. Bytes are only cached after validation succeeds."""
    req = urllib.request.Request(url, headers={"User-Agent": "FTRO-walking-skeleton/0.1 (Phase-0 pinning)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), resp.read(), resp.geturl()


def cache(dest, body):
    tmp = dest + ".part"
    with open(tmp, "wb") as fh:
        fh.write(body)
    os.replace(tmp, dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mjd-start", type=float, default=59630)
    ap.add_argument("--mjd-end", type=float, default=59640)
    ap.add_argument("--base", default=DEFAULT_BASE)
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
    expectation_records = pinning.load_section_records(
        args.expect_sha256_manifest, args.expect_section,
        required=not args.allow_unpinned,
    ) if args.expect_sha256_manifest else {}
    expected = pinning.section_digests(expectation_records)
    variants = variant_expectations(expectation_records)

    os.makedirs(args.cache, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Duplicate --series values produced duplicate targets, so `--series igs igr igs`
    # promoted 79 pins of which only 57 were unique -- a report the consumer rejects
    # (FTRO-DEF-058).
    seen_series, series = set(), []
    for x in args.series:
        if x not in seen_series:
            seen_series.add(x)
            series.append(x)
    args.series = series

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
            status, headers, body, effective_url = fetch(url)
        except urllib.error.HTTPError as exc:
            # HTTPError is also a response object.  Treating it like a transport exception
            # discarded the status and any response-body evidence, so C9 could say that an
            # HTTP response was reached while recording http_status: null.  Preserve the
            # response metadata and a digest/size of its bytes, but never cache rejected bytes.
            try:
                response_body = exc.read()
            except Exception:                              # noqa: BLE001 - evidence is best effort
                response_body = b""
            response_headers = dict(exc.headers or {})
            failures.append({
                **t,
                "url": url,
                "effective_url": exc.geturl(),
                "http_status": exc.code,
                "size_bytes": len(response_body),
                "sha256": (hashlib.sha256(response_body).hexdigest()
                           if response_body else None),
                "content_type": response_headers.get("Content-Type"),
                "last_modified": response_headers.get("Last-Modified"),
                "etag": response_headers.get("ETag"),
                "expected_sha256": expected.get(t["name"]),
                "retrieval_validation": "content_rejected",
                "error": f"{type(exc).__name__}: {exc}",
                "retrieved_utc": retrieved,
            })
            continue
        except Exception as exc:                       # noqa: BLE001 - failure is recorded, not raised
            failures.append({**t, "url": url, "error": f"{type(exc).__name__}: {exc}",
                             "retrieved_utc": retrieved})
            continue
        content_type = headers.get("Content-Type")
        digest = hashlib.sha256(body).hexdigest()
        exp = expected.get(t["name"])
        checksum_match = None if exp is None else (digest == exp)
        if effective_url != url:
            ok, validation_level = False, "content_rejected"
            reason = f"unexpected redirect: requested {url}, effective {effective_url}"
            rejection_note = (
                "Route attribution failed before promotion; redirected bytes were not cached."
            )
        else:
            ok, validation_level, reason = validate_content(t["name"], body, content_type)
            rejection_note = (
                "Status and checksum alone would have accepted these bytes; "
                "content-shape validation rejected them."
            ) if not ok else None
            if checksum_match is False:
                ok, reason = False, f"expected-checksum mismatch: got {digest}, want {exp}"
                rejection_note = (
                    "HTTP status and content shape were insufficient; the outer-checksum "
                    "expectation rejected these bytes."
                )
        decoded_evidence = {}
        if ok and t["name"] in variants:
            decoded_evidence = decoded_variant_evidence(
                t["name"], body, variants[t["name"]],
            )
            if not decoded_evidence["decoded_checksum_match"]:
                ok, reason = False, (
                    "expected decoded-checksum mismatch: got "
                    f"{decoded_evidence['decoded_sha256']}, want "
                    f"{decoded_evidence['expected_decoded_sha256']}"
                )
                rejection_note = (
                    "HTTP status, content shape and outer checksum matched; the executed "
                    "decoded-checksum expectation rejected these bytes."
                )
        if not ok:
            failures.append({**t, "url": url, "effective_url": effective_url,
                             "retrieved_utc": retrieved,
                             "http_status": status, "size_bytes": len(body),
                             "sha256": hashlib.sha256(body).hexdigest(),
                             "error": f"content validation failed: {reason}",
                             "retrieval_validation": validation_level,
                             **decoded_evidence,
                             "note": rejection_note})
            continue

        cache(dest, body)
        pins.append({
            **t,
            "utc_date": mjd_to_date(t["mjd"]) if t["mjd"] else None,
            "url": url,
            "effective_url": effective_url,
            "http_status": status,
            "retrieved_utc": retrieved,
            "size_bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "md5": hashlib.md5(body).hexdigest(),
            "last_modified": headers.get("Last-Modified"),
            "etag": headers.get("ETag"),
            "retrieval_procedure": f"GET {url}",
            "content_type": content_type,
            "expected_sha256": exp,
            "checksum_match": checksum_match,
            "retrieval_validation": validation_level,
            "content_validation": reason,
            **decoded_evidence,
            # Full 64-character digest. An identity that carries a truncated digest is a
            # different and weaker identity; short forms belong in a separate field.
            "ftro_snapshot_id": (
                f"ftro:snapshot:igs/{t['name']}@sha256:{hashlib.sha256(body).hexdigest()}"),
            "sha256_short": hashlib.sha256(body).hexdigest()[:8],
            "concept_id": f"ftro:concept:igs/{t['series']}/{t['kind']}",
        })

    unexpected = [p["name"] for p in pins if p.get("expected_sha256") is None]

    data_centre, availability_note = route_metadata(args.base)
    report = {
        "generator": "src/ftro/pin_igs.py",
        "n_without_expected_digest": len(unexpected),
        "uncovered_by_registry": unexpected,
        "base_url": args.base,
        "data_centre": data_centre,
        "candidate_window_mjd": [args.mjd_start, args.mjd_end],
        "retrieval_validation": ("content_validated" if not failures
                                 else "content_validation_incomplete"),
        "availability_time_source": "mirror_derived",
        "availability_time_note": availability_note,
        "gps_weeks": sorted(weeks),
        "n_pinned": len(pins),
        "n_failed": len(failures),
        "pins": pins,
        "failures": failures,
    }
    ok = bool(pins) and not failures and not unexpected
    promoted = pinning.promote(report, args.out, ok)
    print(f"pinned {len(pins)}, failed {len(failures)}, uncovered {len(unexpected)} -> {args.out}")
    for f in failures:
        print(f"REJECTED {f['name']}: {f['error']}", file=sys.stderr)
    return 0 if promoted else 1


if __name__ == "__main__":
    sys.exit(main())
