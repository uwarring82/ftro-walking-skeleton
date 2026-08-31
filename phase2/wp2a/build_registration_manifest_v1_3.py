#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the immutable WP2A v1.3 registration/instrument manifest.

The manifest intentionally does not hash itself.  A Step-2 report records the
manifest's full SHA-256 and the clean published Git subject from which the
manifest and every artifact below are authenticated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "phase2/wp2a/registration-manifest-v1.3.json"
REPORT_OUTPUT = "phase2/wp2a/reports/step2-input-evidence-v1.3.json"

# Ordered deliberately: scientific registration, generated projections,
# executable instrument.  Every v1.3 registration artifact is present; the
# manifest itself is the sole exclusion because a file cannot hash itself.
ARTIFACT_PATHS = [
    "phase2/wp2a/contract-v1.3.md",
    "phase2/wp2a/source-facts-v1.3.json",
    "phase2/wp2a/prior-observation-v1.3.json",
    "phase2/wp2a/interpretations-v1.3.json",
    "phase2/wp2a/queries-v1.3.json",
    "phase2/wp2a/expected-answers-v1.3.json",
    "phase2/wp2a/mutation-cases-v1.3.json",
    "phase2/wp2a/step2-schema-v1.3.json",
    "phase2/wp2a/build_source_facts_v1_3.py",
    "phase2/wp2a/build_expected_answers_v1_3.py",
    "phase2/wp2a/build_mutation_cases_v1_3.py",
    "phase2/wp2a/build_step2_schema_v1_3.py",
    "phase2/wp2a/build_registration_manifest_v1_3.py",
    "phase2/wp2a/check_step2_v1_3.py",
    "phase2/wp2a/run_step2_v1_3.py",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    missing = [relative for relative in ARTIFACT_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError("registration artifacts absent: " + ", ".join(missing))
    artifacts = [
        {"path": relative, "sha256": digest(ROOT / relative)}
        for relative in ARTIFACT_PATHS
    ]
    return {
        "document": "FTRO WP2A v1.3 registration manifest",
        "version": "1.3.1",
        "ready_for_step2": True,
        "runner": {
            "path": "phase2/wp2a/run_step2_v1_3.py",
            "status": "ready",
        },
        "report_output_path": REPORT_OUTPUT,
        "self_exclusion": {
            "path": str(OUT.relative_to(ROOT)),
            "reason": "A file cannot contain its own settled byte digest; the report binds this manifest by full SHA-256.",
        },
        "required_artifact_paths": ARTIFACT_PATHS,
        "artifacts": artifacts,
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = render()
    except (OSError, ValueError, TypeError) as exc:
        print(f"FAIL WP2A v1.3 registration manifest: {exc}", file=sys.stderr)
        return 1
    if args.check:
        try:
            observed = OUT.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL WP2A v1.3 registration manifest: {exc}", file=sys.stderr)
            return 1
        if observed != expected:
            print("FAIL WP2A v1.3 registration manifest: committed output differs", file=sys.stderr)
            return 1
        print("WP2A v1.3 registration manifest: PASS")
        return 0
    OUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
