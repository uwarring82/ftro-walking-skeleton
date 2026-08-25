#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Pin and content-validate the git-hosted evidence artifacts.
#
# Written because three evidence records asserted evidence_state = resolvable with no
# retrieval_validation at all, and one of them (tintervals) had no checksummed file
# whatsoever -- it was "resolvable" on commit metadata alone. Profile §9.2 permits
# resolvable only for content_validated retrievals, so the honest fix is to retrieve and
# validate, not to widen the clause.

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.request

HTML_MARKERS = (b"<!DOCTYPE html", b"<!doctype html", b"<html", b"<HTML")

# Inner-format signatures. A markdown spec that does not define the columns it is cited
# for, or a clock file with no MJD rows, is not the evidence it claims to be.
VALIDATORS = {
    "optical-format-readme": lambda t: "validity flag" in t and "ref_osc" in t,
    "tempo2-clk": lambda t: t.lstrip().startswith("#") and bool(re.search(r"^\s*\d{5}\.\d+\s+-?\d", t, re.M)),
    "python-package": lambda t: ("[project]" in t or "setup(" in t or "name" in t),
}

TARGETS = [
    {"key": "optical-link-data-format", "repo": "INRIM/optical-link-data-format",
     "commit": "689bda77000fec52c401bc0c9c3664d1dd534ecb", "path": "README.md",
     "kind": "optical-format-readme",
     "expect_sha256": "cf93ae7a8f934944230e8555941d9d1e1afac9fa59d3a6d15bacd7befbfcee98"},
    {"key": "pulsar-clock-corrections", "repo": "ipta/pulsar-clock-corrections",
     "commit": "36dc139a150efde056aa32fa13deac856a7a679d",
     "path": "T2runtime/clock/gps2utc.clk", "kind": "tempo2-clk",
     "expect_sha256": "7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a"},
    # tintervals carried NO pinned file before this script: the record asserted resolvable
    # on commit metadata alone. Pinning pyproject.toml gives it a checksummed artifact.
    {"key": "tintervals", "repo": "INRIM/tintervals",
     "commit": "2064db12777df78bc87f68f7710a47176192c2e1", "path": "pyproject.toml",
     "kind": "python-package", "expect_sha256": None},
]


def validate(kind, body):
    if not body:
        return False, "empty body"
    if any(m in body[:2048] for m in HTML_MARKERS):
        return False, "response is HTML, not a repository file"
    text = body[:16384].decode("utf-8", errors="replace")
    check = VALIDATORS.get(kind)
    if check and not check(text):
        return False, f"content does not look like a {kind}"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="data/raw/evidence")
    ap.add_argument("--out", default="phase0/reports/evidence-repo-pins.json")
    ap.add_argument("--allow-unpinned", action="store_true",
                    help="permit a target with no expected digest (records it as first-pin)")
    args = ap.parse_args()

    os.makedirs(args.cache, exist_ok=True)
    pins, failures = [], []
    for t in TARGETS:
        url = f"https://raw.githubusercontent.com/{t['repo']}/{t['commit']}/{t['path']}"
        retrieved = datetime.datetime.now(datetime.timezone.utc).isoformat()
        req = urllib.request.Request(url, headers={"User-Agent": "FTRO-walking-skeleton/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body, status = resp.read(), resp.status
        except Exception as exc:                                 # noqa: BLE001
            failures.append({**t, "url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue

        sha256 = hashlib.sha256(body).hexdigest()
        ok, reason = validate(t["kind"], body)
        exp = t["expect_sha256"]
        checksum_match = None if exp is None else (sha256 == exp)
        if checksum_match is None and not args.allow_unpinned:
            failures.append({**t, "url": url, "sha256": sha256,
                             "error": ("no expected digest recorded; rerun with --allow-unpinned "
                                       "to establish the first pin")})
            continue
        verified = ok and (checksum_match is not False)
        if not verified:
            failures.append({**t, "url": url, "sha256": sha256, "expected_sha256": exp,
                             "error": reason if not ok else "expected-checksum mismatch"})
            continue

        dest = os.path.join(args.cache, f"{t['key']}--{os.path.basename(t['path'])}")
        tmp = dest + ".part"
        with open(tmp, "wb") as fh:
            fh.write(body)
        os.replace(tmp, dest)

        pins.append({
            **{k: t[k] for k in ("key", "repo", "commit", "path", "kind")},
            "url": url, "http_status": status, "retrieved_utc": retrieved,
            "retrieval_procedure": f"GET {url}",
            "size_bytes": len(body), "sha256": sha256, "md5": hashlib.md5(body).hexdigest(),
            "expected_sha256": exp, "checksum_match": checksum_match,
            "retrieval_validation": "content_validated", "content_validation": reason,
            "concept_id": f"https://github.com/{t['repo']}",
            "snapshot_id": f"git:{t['repo']}@{t['commit']}",
            "snapshot_kind": "provider_immutable",
            "pinned_file": t["path"], "pinned_file_sha256": sha256,
        })

    report = {"generator": "src/ftro/pin_evidence_repos.py",
              "retrieval_validation": "content_validated" if not failures else "content_validation_incomplete",
              "n_pinned": len(pins), "n_failed": len(failures), "pins": pins, "failures": failures}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(report, open(args.out, "w", encoding="utf-8"), indent=2)
    print(f"pinned {len(pins)}, failed {len(failures)} -> {args.out}")
    for f in failures:
        print(f"REJECTED {f['key']}: {f['error']}", file=sys.stderr)
    return 0 if (pins and not failures) else 1


if __name__ == "__main__":
    sys.exit(main())
