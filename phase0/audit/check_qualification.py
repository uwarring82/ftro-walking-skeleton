#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate the complete Phase-0 C9/calibration/two-audit evidence tuple."""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

# Importing the adjacent runner must not create ignored bytecode before that runner's
# source-state proof executes.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import run as audit  # noqa: E402


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise audit.RecipeError(f"cannot read {path}: {exc}") from exc


def pair_invariants(calibration_document, qualifying_evidence, *, checker_subject,
                    c9_document):
    errors = []
    if len(qualifying_evidence) != 2:
        return ["exactly two qualifying reports are required"]
    if len({row["sha256"] for row in qualifying_evidence}) != 2:
        errors.append("qualifying report byte digests are not distinct")
    if len({row["run_id"] for row in qualifying_evidence}) != 2:
        errors.append("qualifying run IDs are not distinct")
    checkout_paths = [row["checkout_realpath"] for row in qualifying_evidence]
    if len(set(checkout_paths)) != 2:
        errors.append("qualifying checkout identities are not distinct")
    calibration_checkout = calibration_document.get("subject", {}).get("checkout_realpath")
    if calibration_checkout in checkout_paths:
        errors.append("a qualifying run reused the calibration checkout")
    c9_checkout = c9_document.get("subject", {}).get("checkout_realpath")
    checker_checkout = checker_subject.get("checkout_realpath")
    for label, path in (("C9", c9_checkout), ("calibration", calibration_checkout),
                        ("qualification checker", checker_checkout)):
        if not isinstance(path, str) or not path or not Path(path).is_absolute():
            errors.append(f"{label} checkout identity is absent or not absolute")
    if checker_checkout in {c9_checkout, calibration_checkout, *checkout_paths}:
        errors.append("qualification checker did not use a distinct checkout")
    calibration_end = audit.parse_utc(
        calibration_document.get("ended_utc"), "calibration report.ended_utc",
    )
    for row in qualifying_evidence:
        if audit.parse_utc(row["started_utc"], "qualifying report.started_utc") \
                < calibration_end:
            errors.append(f"{row['run_id']} started before calibration completed")
    return errors


def write_new(path, document):
    path = Path(path)
    temporary = Path(str(path) + ".part")
    if path.exists() or temporary.exists():
        raise audit.RecipeError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="phase0/audit/execution-manifest-v1.0.json")
    ap.add_argument("--c9-report", required=True)
    ap.add_argument("--calibration-report", required=True)
    ap.add_argument("--qualifying-report", action="append", required=True)
    ap.add_argument("--out", required=True)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    os.chdir(ROOT)
    if len(args.qualifying_report) != 2:
        raise audit.RecipeError("supply --qualifying-report exactly twice")
    output = Path(args.out).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise audit.RecipeError("qualification report must be outside the carrier checkout")

    manifest_path = Path(args.manifest).resolve()
    runner_path = HERE / "run.py"
    checker_path = Path(__file__).resolve()
    manifest = audit.load_json(manifest_path)
    cases = audit.validate_manifest(manifest)
    manifest_sha = audit.sha256_file(manifest_path)
    runner_sha = audit.sha256_file(runner_path)
    source = audit.source_state(
        ROOT, manifest_path, runner_path,
        manifest["subject_binding"]["required_ancestor"],
    )
    checker_relative = checker_path.relative_to(ROOT).as_posix()
    if audit.git(ROOT, "show", f"HEAD:{checker_relative}", text=False).stdout \
            != checker_path.read_bytes():
        raise audit.RecipeError("qualification checker differs from the carrier commit")
    bound = audit.verify_bound_documents(ROOT, manifest)
    now = audit.utc_now()
    c9 = audit.validate_c9_report(args.c9_report, source, bound, ROOT, before_utc=now)
    c9_document = load(args.c9_report)
    calibration = audit.validate_calibration(
        args.calibration_report, manifest_sha, runner_sha, source, manifest, bound, cases, c9,
        before_utc=now,
    )
    calibration_document = load(args.calibration_report)
    qualifying = [
        audit.validate_qualifying_report(
            path, manifest_sha, runner_sha, source, manifest, bound, cases, c9, calibration,
            before_utc=now,
        )
        for path in args.qualifying_report
    ]
    errors = pair_invariants(
        calibration_document, qualifying, checker_subject=source,
        c9_document=c9_document,
    )
    if errors:
        raise audit.RecipeError("qualification pair invalid: " + "; ".join(errors))

    report = {
        "document": "FTRO Phase-0 qualification evidence check",
        "version": "1.0.0",
        "checked_utc": now,
        "status": "pass",
        "subject": source,
        "manifest": {"path": manifest_path.relative_to(ROOT).as_posix(),
                     "sha256": manifest_sha},
        "runner": {"path": runner_path.relative_to(ROOT).as_posix(),
                   "sha256": runner_sha},
        "checker": {"path": checker_relative, "sha256": audit.sha256_file(checker_path)},
        "c9_evidence": c9,
        "calibration_evidence": calibration,
        "qualifying_evidence": qualifying,
        "n_qualifying_reports": len(qualifying),
        "distinct_report_digests": True,
        "distinct_run_ids": True,
        "distinct_checkout_identities": True,
        "distinct_checker_checkout": True,
        "calibration_preceded_qualification": True,
    }
    write_new(output, report)
    print(f"wrote {output}")
    print("Phase-0 qualification evidence: PASS (2/2)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except audit.RecipeError as exc:
        print(f"QUALIFICATION CHECK REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
