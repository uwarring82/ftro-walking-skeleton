#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the executable JSON Schema and frozen Step-2 v1.3 registration metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_VERSION = "1.3.2"
OUT = ROOT / "phase2/wp2a/step2-schema-v1.3.json"
FACTS_PATH = ROOT / "phase2/wp2a/source-facts-v1.3.json"
PRIOR_PATH = ROOT / "phase2/wp2a/prior-observation-v1.3.json"
MEMBER = "PTB_Yb_CombKnoten-INRIM_ITYb1/2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat"
OUTPUT_PATH = "phase2/wp2a/reports/step2-input-evidence-v1.3.json"
MANIFEST_PATH = "phase2/wp2a/registration-manifest-v1.3.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def const_object(properties: dict, required: list[str]) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def method_schema() -> dict:
    nullable_sha = {"oneOf": [{"$ref": "#/$defs/sha256"}, {"type": "null"}]}
    nullable_int = {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]}
    nullable_time = {"oneOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]}
    return const_object({
        "method_id": {"type": "string", "minLength": 1},
        "implementation": {"type": "string", "minLength": 1},
        "implementation_sha256": nullable_sha,
        "executable": {"type": "string", "minLength": 1},
        "executable_sha256": nullable_sha,
        "tool_available": {"type": "boolean"},
        "version_argv": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "version_exit_code": {"oneOf": [{"type": "integer"}, {"type": "null"}]},
        "version_output": {"type": "string"},
        "input_handle": {
            "oneOf": [
                {"type": "string", "pattern": "^/dev/fd/[0-9]+$"},
                {"type": "null"},
            ]
        },
        "input_binding_sha256": nullable_sha,
        "input_binding_size_bytes": nullable_int,
        "argv": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "non_execution_reason": {
            "oneOf": [
                {"type": "string", "minLength": 1},
                {"type": "null"},
            ]
        },
        "ran": {"type": "boolean"},
        "exit_code": {"oneOf": [{"type": "integer"}, {"type": "null"}]},
        "started_utc": nullable_time,
        "ended_utc": nullable_time,
        "stdout_sha256": nullable_sha,
        "stdout_size_bytes": nullable_int,
        "stderr_sha256": nullable_sha,
        "stderr_size_bytes": nullable_int,
    }, [
        "method_id", "implementation", "implementation_sha256", "executable",
        "tool_available",
        "executable_sha256", "version_argv", "version_exit_code", "version_output", "argv",
        "input_handle", "input_binding_sha256", "input_binding_size_bytes",
        "non_execution_reason",
        "ran", "exit_code", "started_utc", "ended_utc", "stdout_sha256",
        "stdout_size_bytes", "stderr_sha256", "stderr_size_bytes",
    ])


def build() -> dict:
    facts = load(FACTS_PATH)
    prior = load(PRIOR_PATH)
    products = facts["source_projection"]["family_A"]["products"]
    if [row["registered_selector"] for row in products] != [
        "igs21982.clk.Z", "igs21983.clk.Z", "igr21991.clk.Z"
    ]:
        raise ValueError("source-facts Family-A target population differs")

    input_artifacts = []
    targets = []
    for index, product in enumerate(products):
        values = product["sio_occurrence_source"]["values"]
        name = values["name"]
        input_id = f"input:{name}@SIO"
        input_path = f"data/raw/igs/{name}"
        input_artifacts.append({
            "input_id": input_id,
            "path": input_path,
            "acquisition_mode": "preexisting_local_copy_authenticated_before_any_decode",
            "registered_route": values["url"],
            "expected_outer_sha256": values["sha256"],
            "expected_outer_size_bytes": values["size_bytes"],
            "expected_source": f"phase2/wp2a/source-facts-v1.3.json#/source_projection/family_A/products/{index}/sio_occurrence_source/values",
        })
        targets.append({
            "target_id": f"decoded:{name}",
            "input_id": input_id,
            "expected_sha256": values["decoded_sha256"],
            "expected_size_bytes": values["decoded_size_bytes"],
            "expected_source": f"phase2/wp2a/source-facts-v1.3.json#/source_projection/family_A/products/{index}/sio_occurrence_source/values",
            "method_a": "ftro_unixz",
            "method_b": "system_gzip",
        })

    container = facts["source_projection"]["family_B"]["container_occurrence_source"]["values"]
    optical_input_id = "input:rocit-zip@zenodo"
    input_artifacts.append({
        "input_id": optical_input_id,
        "path": "data/raw/zenodo-17107693/ROCIT campaign results.zip",
        "acquisition_mode": "preexisting_local_copy_authenticated_before_any_extraction",
        "registered_route": container["retrieval_procedure"].removeprefix("GET "),
        "expected_outer_sha256": container["sha256"],
        "expected_outer_size_bytes": container["size_bytes"],
        "expected_source": "phase2/wp2a/source-facts-v1.3.json#/source_projection/family_B/container_occurrence_source/values",
    })
    prior_target = prior["target"]
    if prior_target["member_selector"] != MEMBER:
        raise ValueError("prior observation member differs from registered member")
    interpretation_bound = prior["report_interpretation_bound"]
    if interpretation_bound.get("applies_to_target_id") != "member:rocit-zip":
        raise ValueError("prior observation report bound differs from optical target")
    targets.append({
        "target_id": "member:rocit-zip",
        "input_id": optical_input_id,
        "member_selector": MEMBER,
        "expected_sha256": prior_target["sha256"],
        "expected_size_bytes": prior_target["size_bytes"],
        "expected_source": "phase2/wp2a/prior-observation-v1.3.json#/target",
        "method_a": "python_zipfile",
        "method_b": "system_unzip",
    })

    registration = {
        "version": REGISTRATION_VERSION,
        "registration_manifest": MANIFEST_PATH,
        "report_output_path": OUTPUT_PATH,
        "rejected_output_rule": OUTPUT_PATH + ".<run_id>.rejected",
        "registration_sources": {
            "source_facts": {"path": str(FACTS_PATH.relative_to(ROOT)), "sha256": digest(FACTS_PATH)},
            "prior_observation": {"path": str(PRIOR_PATH.relative_to(ROOT)), "sha256": digest(PRIOR_PATH)},
        },
        "input_policy": {
            "population": input_artifacts,
            "transport_preflight": "Before any provider pathname opens, reproduce an FTRO-synthetic sentinel through the same POSIX anonymous seekable descriptor and pass_fds transport used by every method. Failure means Step 2 did not start.",
            "preflight": "Read each of the four local input paths once, retain that exact byte string, and authenticate its SHA-256 and size before executing any decoder or extractor. Any missing/mismatched input prevents every method invocation and yields step2_not_executed.",
            "consumption_binding": "Populate anonymous seekable file descriptors only from the retained authenticated byte strings. Both methods consume those descriptors and never reopen a provider pathname.",
            "postflight": "After all registered method attempts are complete, re-read each current input pathname solely as mutation evidence. A changed or unavailable pathname yields step2_evidence_assurance_failed; it cannot validate, replace or alter the bytes already consumed.",
            "network_during_step2": "forbidden; acquisition is a documented prerequisite outside the Step-2 run",
        },
        "target_population": targets,
        "outcome_interpretation_bound": interpretation_bound,
        "method_contracts": {
            "ftro_unixz": {
                "implementation": "src/ftro/unixz.py:decompress",
                "argv_template": ["{python_executable}", "-I", "phase2/wp2a/run_step2_v1_3.py", "_decode-unixz", "--input", "{authenticated_input_handle}"],
                "version_argv_template": ["{python_executable}", "--version"],
            },
            "system_gzip": {
                "implementation": "system gzip -dc",
                "argv_template": ["{gzip_executable}", "-dc", "{authenticated_input_handle}"],
                "version_argv_template": ["{gzip_executable}", "--version"],
            },
            "python_zipfile": {
                "implementation": "Python standard-library zipfile.ZipFile.read after exact-one-member check",
                "argv_template": ["{python_executable}", "-I", "phase2/wp2a/run_step2_v1_3.py", "_extract-zipfile", "--input", "{authenticated_input_handle}", "--member", MEMBER],
                "version_argv_template": ["{python_executable}", "--version"],
            },
            "system_unzip": {
                "implementation": "system unzip -p",
                "argv_template": ["{unzip_executable}", "-p", "{authenticated_input_handle}", MEMBER],
                "version_argv_template": ["{unzip_executable}", "-v"],
            },
        },
        "trusted_computing_base": {
            "trusted_not_reverified": [
                "operating system process/filesystem primitives",
                "Python runtime and hashlib SHA-256",
                "git object access used to bind the clean published subject",
                "registration-manifest-v1.3.json after report-recorded SHA-256 authentication",
                "POSIX anonymous seekable file descriptors used to bind consumed bytes",
            ],
            "cross_checked": [
                "src/ftro/unixz.py against independently invoked system gzip -dc",
                "Python zipfile against independently invoked system unzip -p",
            ],
            "required_tools": ["python", "git", "gzip", "unzip"],
            "note": "gzip is explicitly inside the recorded/cross-checked tool population; it is not inherited from Phase 0.",
        },
        "byte_agreement_rule": "Runner compares the two captured byte strings directly (`method_a_bytes == method_b_bytes`), then records each full SHA-256 and size. Digest equality alone is insufficient.",
        "per_target_outcome_precedence": [
            {"priority": 1, "if": "either method did not run, exited nonzero, or emitted zero bytes", "outcome": "not_executed"},
            {"priority": 2, "if": "both methods ran successfully but captured bytes differ", "outcome": "evidence_assurance_failed"},
            {"priority": 3, "if": "bytes agree but full SHA-256 OR size differs from the committed expectation", "outcome": "contradicts"},
            {"priority": 4, "if": "bytes agree and full SHA-256 AND size equal the committed expectation", "outcome": "supports"},
        ],
        "run_outcome_precedence": [
            {"priority": 1, "if_any_target": "not_executed", "outcome": "step2_not_executed"},
            {"priority": 2, "if_any_target_or_input": "evidence_assurance_failed or changed_during_run", "outcome": "step2_evidence_assurance_failed"},
            {"priority": 3, "if_any_target": "contradicts", "outcome": "step2_contradicts"},
            {"priority": 4, "if_all_targets": "supports", "outcome": "step2_supports"},
        ],
        "publication": {
            "supports": "Atomically create the exact report_output_path; refuse to overwrite it.",
            "other_outcomes_or_invalid_report": "Atomically preserve bytes at the run-specific .rejected path; never overwrite an existing official or rejected report.",
            "check_mode": "--check-report authenticates the report-bound registration manifest from subject_commit, validates shape, re-derives populations, counters and outcomes, and performs no writes.",
            "immutable_binding": "Every report records registration_manifest path and SHA-256. The manifest pins the runner, schema, checker and all v1.3 registration artifacts; the contract is never edited to bind a result.",
        },
    }

    sha = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    nullable_sha = {"oneOf": [{"$ref": "#/$defs/sha256"}, {"type": "null"}]}
    nullable_int = {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "null"}]}
    target_result = const_object({
        "target_id": {"type": "string", "minLength": 1},
        "input_id": {"type": "string", "minLength": 1},
        "member_selector": {"oneOf": [{"type": "string", "minLength": 1}, {"type": "null"}]},
        "expected_sha256": {"$ref": "#/$defs/sha256"},
        "expected_size_bytes": {"type": "integer", "minimum": 1},
        "expected_source": {"type": "string", "minLength": 1},
        "method_a": {"$ref": "#/$defs/method_result"},
        "method_b": {"$ref": "#/$defs/method_result"},
        "byte_comparison": {"enum": ["direct_byte_equality", "not_performed"]},
        "bytes_equal": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "observed_sha256": nullable_sha,
        "observed_size_bytes": nullable_int,
        "matches_expected": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "outcome": {"enum": ["supports", "contradicts", "evidence_assurance_failed", "not_executed"]},
    }, [
        "target_id", "input_id", "member_selector", "expected_sha256", "expected_size_bytes",
        "expected_source", "method_a", "method_b", "byte_comparison", "bytes_equal",
        "observed_sha256", "observed_size_bytes", "matches_expected", "outcome",
    ])

    input_result = const_object({
        "input_id": {"type": "string", "minLength": 1},
        "path": {"type": "string", "minLength": 1},
        "acquisition_mode": {"type": "string", "minLength": 1},
        "registered_route": {"type": "string", "minLength": 1},
        "expected_outer_sha256": {"$ref": "#/$defs/sha256"},
        "expected_outer_size_bytes": {"type": "integer", "minimum": 1},
        "observed_outer_sha256": nullable_sha,
        "observed_outer_size_bytes": nullable_int,
        "post_observed_outer_sha256": nullable_sha,
        "post_observed_outer_size_bytes": nullable_int,
        "postflight_path_matches_captured_snapshot": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "outcome": {"enum": ["authenticated", "missing", "digest_mismatch", "size_mismatch", "unreadable"]},
    }, [
        "input_id", "path", "acquisition_mode", "registered_route", "expected_outer_sha256",
        "expected_outer_size_bytes", "observed_outer_sha256", "observed_outer_size_bytes", "outcome",
        "post_observed_outer_sha256", "post_observed_outer_size_bytes",
        "postflight_path_matches_captured_snapshot",
    ])

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://w3id.org/ftro/schema/wp2a-step2-report-v1.3.json",
        "title": "FTRO WP2A Step-2 input-evidence report v1.3",
        "description": "Executable shape contract. Cross-field and Git/manifest checks are enforced by check_step2_v1_3.py.",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "document", "schema_version", "run_id", "subject", "registration_manifest",
            "started_utc", "ended_utc", "input_authentication", "targets", "counters",
            "overall_outcome", "outcome_interpretation_bound", "output_path",
        ],
        "properties": {
            "document": {"const": "FTRO WP2A Step-2 input-evidence report"},
            "schema_version": {"const": REGISTRATION_VERSION},
            "run_id": {"type": "string", "pattern": "^[A-Za-z0-9._:-]+$"},
            "subject": const_object({
                "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                "tree": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                "worktree_clean": {"const": True},
                "published": {"const": True},
                "published_ref": {"type": "string", "minLength": 1},
            }, ["commit", "tree", "worktree_clean", "published", "published_ref"]),
            "registration_manifest": const_object({
                "path": {"const": MANIFEST_PATH},
                "sha256": {"$ref": "#/$defs/sha256"},
            }, ["path", "sha256"]),
            "started_utc": {"type": "string", "format": "date-time"},
            "ended_utc": {"type": "string", "format": "date-time"},
            "input_authentication": {"type": "array", "minItems": 4, "maxItems": 4, "items": input_result},
            "targets": {"type": "array", "minItems": 4, "maxItems": 4, "items": target_result},
            "counters": const_object({
                "n_targets": {"const": 4},
                "n_supports": {"type": "integer", "minimum": 0, "maximum": 4},
                "n_contradicts": {"type": "integer", "minimum": 0, "maximum": 4},
                "n_evidence_assurance_failed": {"type": "integer", "minimum": 0, "maximum": 4},
                "n_not_executed": {"type": "integer", "minimum": 0, "maximum": 4},
                "n_inputs_changed_during_run": {"type": "integer", "minimum": 0, "maximum": 4},
            }, [
                "n_targets", "n_supports", "n_contradicts", "n_evidence_assurance_failed",
                "n_not_executed", "n_inputs_changed_during_run",
            ]),
            "overall_outcome": {"enum": ["step2_supports", "step2_contradicts", "step2_evidence_assurance_failed", "step2_not_executed"]},
            "outcome_interpretation_bound": {"const": interpretation_bound},
            "output_path": {"const": OUTPUT_PATH},
        },
        "$defs": {"sha256": sha, "method_result": method_schema()},
        "x-ftro-registration": registration,
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = render()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL WP2A v1.3 Step-2 schema: {exc}", file=sys.stderr)
        return 1
    if args.check:
        try:
            observed = OUT.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL WP2A v1.3 Step-2 schema: {exc}", file=sys.stderr)
            return 1
        if observed != expected:
            print("FAIL WP2A v1.3 Step-2 schema: committed output differs", file=sys.stderr)
            return 1
        print("WP2A v1.3 Step-2 schema: PASS")
        return 0
    OUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
