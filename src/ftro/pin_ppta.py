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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinning

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

# concept_id and snapshot_stem are declared here, not derived ad hoc, because the
# generator and phase0/evidence/identities.json must agree exactly. An earlier version
# invented its own stem (ppta/dr3/<name>) while the manifest used ppta/dr3/<dir>/<name>,
# so the tool built to support the manifest emitted four identities that did not match
# it and nothing noticed. tests/test_retrieval_validation.py now reconciles the two.
TARGETS = [
    {"name": "J0437-4715.par", "file_id": 65419506, "kind": "par",
     "path": "ppta_dr3/toas_and_parameters/all/J0437-4715.par",
     "concept_id": "ftro:concept:ppta/dr3/par/J0437-4715",
     "snapshot_stem": "ppta/dr3/all/J0437-4715.par"},
    {"name": "J0437-4715.tim", "file_id": 65419499, "kind": "tim",
     "path": "ppta_dr3/toas_and_parameters/all/J0437-4715.tim",
     "concept_id": "ftro:concept:ppta/dr3/toas/J0437-4715",
     "snapshot_stem": "ppta/dr3/all/J0437-4715.tim"},
    {"name": "pks2gps.clk", "file_id": 65419593, "kind": "clk",
     "path": "ppta_dr3/toas_and_parameters/clock/pks2gps.clk",
     "concept_id": "ftro:concept:ppta/dr3/clock/pks2gps",
     "snapshot_stem": "ppta/dr3/clock/pks2gps.clk"},
    {"name": "tai2tt_bipm2021.clk", "file_id": 65419592, "kind": "clk",
     "path": "ppta_dr3/toas_and_parameters/clock/tai2tt_bipm2021.clk",
     "concept_id": "ftro:concept:ppta/dr3/clock/tai2tt_bipm2021",
     "snapshot_stem": "ppta/dr3/clock/tai2tt_bipm2021.clk"},
]

# Profile §5.1: an ftro_composed identity must record what was checked and found absent.
# Emitted by the generator so a regenerated report stays conforming.
COMPOSITION_CHECKED = [
    "CSIRO DAP per-file record (id + lastUpdated only; no per-file DOI or handle)",
    "CSIRO DAP collection DOI (dataset-level only: 10.25919/j4xr-wp05, 10.25919/axvw-qa43)",
    "provider_last_updated (mutable timestamp, not a persistent identifier)",
]
COMPOSITION_WHY = ("CSIRO DAP mints DOIs at collection level only and supplies no immutable "
                   "per-file snapshot PID, so task card §10 composition applies to these members.")


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
    ap.add_argument("--expect", default="phase0/evidence/expected-digests.json",
                    help="JSON map of name -> sha256 to enforce")
    ap.add_argument("--allow-unpinned", action="store_true",
                    help="proceed when no expectation file exists (establishes a first pin)")
    args = ap.parse_args()

    # An absent expectation file used to be silently treated as an empty map, so the
    # documented cold path enforced nothing while recording checksum_match: true.
    expected = pinning.load_section(args.expect, "ppta", required=not args.allow_unpinned)
    # PREFLIGHT: an individual missing expectation is a failure, not a null field.
    uncovered = pinning.preflight(expected, [t["name"] for t in TARGETS],
                                  allow_unpinned=args.allow_unpinned, what="PPTA artifact")

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
        verified = ok and (checksum_match is True
                           or (checksum_match is None and args.allow_unpinned))

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
            "concept_id": t["concept_id"],
            "snapshot_id": f"ftro:snapshot:{t['snapshot_stem']}@sha256:{sha256}",
            "snapshot_kind": "ftro_composed",
            "composition_precondition_checked": COMPOSITION_CHECKED,
            "composition_justification": COMPOSITION_WHY,
        })

    ok = bool(pins) and not failures and not uncovered
    report = {"generator": "src/ftro/pin_ppta.py", "collection": COLLECTION,
              "n_without_expected_digest": len(uncovered), "uncovered_by_registry": uncovered,
              "data_rights": "CC-BY-SA-4.0", "redistribution_mode": "link_only",
              "retrieval_validation": "content_validated" if not failures else "content_validation_incomplete",
              "n_pinned": len(pins), "n_failed": len(failures),
              "pins": pins, "failures": failures}
    pinning.promote(report, args.out, ok)
    print(f"pinned {len(pins)}, failed {len(failures)}, uncovered {len(uncovered)} -> {args.out}")
    for f in failures:
        print(f"REJECTED {f['name']}: {f['error']}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
