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
import urllib.request

# Content-shape validation (FTRO-DEF-018). A retrieval that checks only HTTP status and
# byte checksum will happily pin an authentication interstitial as if it were data --
# CDDIS returns an Earthdata login page with HTTP 200. Status and checksum are necessary
# but not sufficient; the bytes must also look like the product they claim to be.
HTML_MARKERS = (b"<!DOCTYPE html", b"<!doctype html", b"<html", b"<HTML")
AUTH_MARKERS = (b"Earthdata Login", b"oauth", b"Sign In", b"login", b"Log In", b"password")
UNIX_COMPRESS_MAGIC = b"\x1f\x9d"   # .Z files produced by compress(1)


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
    if content_type and "html" in content_type.lower():
        return False, "content_validated", f"unexpected Content-Type {content_type!r}"
    return True, "content_validated", "ok"

GPS_EPOCH_MJD = 44244


def mjd_to_gps(mjd):
    d = int(mjd) - GPS_EPOCH_MJD
    return d // 7, d % 7


def mjd_to_date(mjd):
    return (datetime.date(1858, 11, 17) + datetime.timedelta(days=int(mjd))).isoformat()


def fetch(url, dest, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": "FTRO-walking-skeleton/0.1 (Phase-0 pinning)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = dict(resp.headers)
        body = resp.read()
        status = resp.status
    with open(dest, "wb") as fh:
        fh.write(body)
    return status, headers, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mjd-start", type=float, default=59630)
    ap.add_argument("--mjd-end", type=float, default=59640)
    ap.add_argument("--base", default="https://igs.bkg.bund.de/root_ftp/IGS/products/orbits")
    ap.add_argument("--cache", default="data/raw/igs")
    ap.add_argument("--out", default="data/work/igs-pins.json")
    ap.add_argument("--series", nargs="+", default=["igs", "igr"],
                    help="product line prefixes: igs=Final, igr=Rapid, igu=Ultra-rapid")
    args = ap.parse_args()

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

    pins, failures = [], []
    for t in targets:
        url = f"{args.base}/{t['week']}/{t['name']}"
        dest = os.path.join(args.cache, t["name"])
        retrieved = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            status, headers, body = fetch(url, dest)
        except Exception as exc:                       # noqa: BLE001 - failure is recorded, not raised
            failures.append({**t, "url": url, "error": f"{type(exc).__name__}: {exc}",
                             "retrieved_utc": retrieved})
            continue
        content_type = headers.get("Content-Type")
        ok, validation_level, reason = validate_content(t["name"], body, content_type)
        if not ok:
            failures.append({**t, "url": url, "retrieved_utc": retrieved,
                             "http_status": status, "size_bytes": len(body),
                             "sha256": hashlib.sha256(body).hexdigest(),
                             "error": f"content validation failed: {reason}",
                             "retrieval_validation": validation_level,
                             "note": ("Status and checksum alone would have accepted these "
                                      "bytes; content-shape validation rejected them.")})
            continue

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
            "retrieval_validation": validation_level,
            "content_validation": reason,
            # Full 64-character digest. An identity that carries a truncated digest is a
            # different and weaker identity; short forms belong in a separate field.
            "ftro_snapshot_id": (
                f"ftro:snapshot:igs/{t['name']}@sha256:{hashlib.sha256(body).hexdigest()}"),
            "sha256_short": hashlib.sha256(body).hexdigest()[:8],
            "concept_id": f"ftro:concept:igs/{t['series']}/{t['kind']}",
        })

    report = {
        "generator": "src/ftro/pin_igs.py",
        "base_url": args.base,
        "data_centre": "BKG (Bundesamt für Kartographie und Geodäsie) IGS mirror, anonymous HTTP",
        "candidate_window_mjd": [args.mjd_start, args.mjd_end],
        "retrieval_validation": "content_validated",
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
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"pinned {len(pins)}, failed {len(failures)} -> {args.out}")


if __name__ == "__main__":
    main()
