#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO PPTA DR3 artifact pinner with content-shape validation.
#
# Written to close a conformance contradiction rather than to restate it: profile §9.2
# permits evidence_state = resolvable only for content_validated retrievals, but the PPTA
# leg was pinned at status_and_checksum while asserting resolvable. Recording the
# contradiction was not a fix; validating the content is.
#
# PPTA DR3 is CC BY-SA 4.0 (FTRO-DEF-014): redistribution_mode = link_only. Bytes are
# cached under data/raw/ and never committed.

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.request

COLLECTION = 59423
HTML_MARKERS = (b"<!DOCTYPE html", b"<!doctype html", b"<html", b"<HTML")

# Inner-format signatures per artifact kind. A .par that does not declare PSRJ, or a .tim
# that does not open with a TEMPO2 FORMAT line, is not the product it claims to be.
VALIDATORS = {
    "par": lambda t: bool(re.search(r"^\s*PSRJ?\s+\S+", t, re.M)),
    "tim": lambda t: t.lstrip().startswith("FORMAT"),
    "clk": lambda t: t.lstrip().startswith("#") and bool(re.search(r"^\s*\d{5}\.\d+\s+-?\d", t, re.M)),
    "txt": lambda t: len(t.strip()) > 0,
}

TARGETS = [
    {"name": "J0437-4715.par", "file_id": 65419506, "kind": "par",
     "path": "ppta_dr3/toas_and_parameters/all/J0437-4715.par"},
    {"name": "J0437-4715.tim", "file_id": 65419499, "kind": "tim",
     "path": "ppta_dr3/toas_and_parameters/all/J0437-4715.tim"},
    {"name": "pks2gps.clk", "file_id": 65419593, "kind": "clk",
     "path": "ppta_dr3/toas_and_parameters/clock/pks2gps.clk"},
    {"name": "tai2tt_bipm2021.clk", "file_id": 65419592, "kind": "clk",
     "path": "ppta_dr3/toas_and_parameters/clock/tai2tt_bipm2021.clk"},
]


def validate(kind, body):
    if not body:
        return False, "empty body"
    if any(m in body[:2048] for m in HTML_MARKERS):
        return False, "response is HTML, not a product file"
    text = body[:8192].decode("utf-8", errors="replace")
    check = VALIDATORS.get(kind)
    if check and not check(text):
        return False, f"content does not look like a {kind} product"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="data/raw/ppta")
    ap.add_argument("--out", default="phase0/reports/ppta-artifact-pins.json")
    ap.add_argument("--expect", default="data/work/ppta-hashes.json",
                    help="optional JSON map of name -> sha256 to enforce")
    args = ap.parse_args()

    expected = {}
    if args.expect and os.path.exists(args.expect):
        expected = {k: v["sha256"] for k, v in json.load(open(args.expect, encoding="utf-8")).items()}

    os.makedirs(args.cache, exist_ok=True)
    pins, failures = [], []
    for t in TARGETS:
        url = f"https://data.csiro.au/dap/ws/v2/collections/{COLLECTION}/data/{t['file_id']}"
        retrieved = datetime.datetime.now(datetime.timezone.utc).isoformat()
        req = urllib.request.Request(url, headers={"User-Agent": "FTRO-walking-skeleton/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body, status = resp.read(), resp.status
        except Exception as exc:                                 # noqa: BLE001
            failures.append({**t, "url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue

        sha256 = hashlib.sha256(body).hexdigest()
        ok, reason = validate(t["kind"], body)
        exp = expected.get(t["name"])
        checksum_match = None if exp is None else (sha256 == exp)
        verified = ok and (checksum_match is not False)

        if verified:
            tmp = os.path.join(args.cache, t["name"] + ".part")
            with open(tmp, "wb") as fh:
                fh.write(body)
            os.replace(tmp, os.path.join(args.cache, t["name"]))
        else:
            failures.append({**t, "url": url, "error": reason if not ok else "checksum mismatch",
                             "sha256": sha256, "expected_sha256": exp})
            continue

        pins.append({
            **t, "url": url, "http_status": status, "retrieved_utc": retrieved,
            "retrieval_procedure": f"GET {url}",
            "size_bytes": len(body), "sha256": sha256, "md5": hashlib.md5(body).hexdigest(),
            "expected_sha256": exp, "checksum_match": checksum_match,
            "retrieval_validation": "content_validated",
            "content_validation": reason,
            "snapshot_id": f"ftro:snapshot:ppta/dr3/{t['name']}@sha256:{sha256}",
            "snapshot_kind": "ftro_composed",
        })

    report = {"generator": "src/ftro/pin_ppta.py", "collection": COLLECTION,
              "data_rights": "CC-BY-SA-4.0", "redistribution_mode": "link_only",
              "retrieval_validation": "content_validated" if not failures else "content_validation_incomplete",
              "n_pinned": len(pins), "n_failed": len(failures),
              "pins": pins, "failures": failures}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(report, open(args.out, "w", encoding="utf-8"), indent=2)
    print(f"pinned {len(pins)}, failed {len(failures)} -> {args.out}")
    for f in failures:
        print(f"REJECTED {f['name']}: {f['error']}", file=sys.stderr)
    return 0 if (pins and not failures) else 1


if __name__ == "__main__":
    sys.exit(main())
