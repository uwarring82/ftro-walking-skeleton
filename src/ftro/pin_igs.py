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
            "ftro_snapshot_id": (
                f"ftro:snapshot:igs/{t['name']}@sha256:{hashlib.sha256(body).hexdigest()[:16]}"),
            "concept_id": f"ftro:concept:igs/{t['series']}/{t['kind']}",
        })

    report = {
        "generator": "src/ftro/pin_igs.py",
        "base_url": args.base,
        "data_centre": "BKG (Bundesamt für Kartographie und Geodäsie) IGS mirror, anonymous HTTP",
        "candidate_window_mjd": [args.mjd_start, args.mjd_end],
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
