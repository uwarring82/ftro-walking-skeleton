#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed semantic checker and atomic publisher for WP2A Step 2 v1.3.

The JSON Schema constrains shape.  This checker enforces relations JSON Schema cannot:
authenticated registration binding, exact populations, real method execution, counters,
byte-comparison consequences and outcome precedence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_REL = "phase2/wp2a/step2-schema-v1.3.json"
SCHEMA_PATH = ROOT / SCHEMA_REL
MANIFEST_REL = "phase2/wp2a/registration-manifest-v1.3.json"
REQUIRED_REGISTRATION_PATHS = [
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
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class CheckError(RuntimeError):
    pass


def digest_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json_bytes(body: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"{label}: not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise CheckError(f"{label}: top-level value must be an object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        return load_json_bytes(path.read_bytes(), str(path))
    except OSError as exc:
        raise CheckError(f"{path}: unreadable: {exc}") from exc


def schema_registration(schema: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    schema = load_json(SCHEMA_PATH) if schema is None else schema
    registration = schema.get("x-ftro-registration")
    if not isinstance(registration, dict):
        raise CheckError("Step-2 schema has no x-ftro-registration object")
    return schema, registration


def git_bytes(commit: str, relative: str) -> bytes:
    if not HEX40.fullmatch(commit):
        raise CheckError(f"subject commit is not full lowercase Git object ID: {commit!r}")
    command = [
        "git", "--no-replace-objects", "-C", str(ROOT), "-c", "core.fsmonitor=false",
        "-c", "core.hooksPath=/dev/null", "show", f"{commit}:{relative}",
    ]
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    done = subprocess.run(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=environment, stdin=subprocess.DEVNULL, timeout=120, check=False,
    )
    if done.returncode != 0:
        raise CheckError(
            f"cannot resolve {relative} from {commit}: {done.stderr.decode(errors='replace')[-500:]}"
        )
    return done.stdout


def git_text(*arguments: str) -> str:
    command = ["git", "--no-replace-objects", "-C", str(ROOT), *arguments]
    done = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if done.returncode != 0:
        raise CheckError(f"git {' '.join(arguments)} failed: {done.stderr[-500:]}")
    return done.stdout.strip()


def git_contains(commit: str, published_ref: str) -> bool:
    if not isinstance(published_ref, str) or not published_ref:
        return False
    resolved = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), "rev-parse",
         "--symbolic-full-name", published_ref],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=120, check=False, text=True,
    )
    if resolved.returncode != 0:
        return False
    full_ref = resolved.stdout.strip()
    if not full_ref.startswith("refs/remotes/"):
        return False
    done = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), "merge-base", "--is-ancestor",
         commit, full_ref],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=120, check=False,
    )
    return done.returncode == 0


def exact_keys(value: Any, required: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected object")
        return False
    observed = set(value)
    if observed != required:
        missing = sorted(required - observed)
        extra = sorted(observed - required)
        errors.append(f"{label}: keys differ; missing={missing}, extra={extra}")
        return False
    return True


def integer(value: Any) -> bool:
    return type(value) is int


def timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def json_equal(left: Any, right: Any) -> bool:
    """JSON equality without Python's ``True == 1`` type collapse."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return type(left) is type(right) and left == right


def json_schema_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    """Execute the complete JSON-Schema subset used by the frozen v1.3 schema.

    The repository deliberately has no third-party runtime dependencies.  This validator
    therefore implements—and fails closed beyond—the small vocabulary emitted by
    ``build_step2_schema_v1_3.py`` instead of merely publishing an inert schema document.
    """
    errors: list[str] = []
    definitions = schema.get("$defs", {})
    allowed = {
        "$schema", "$id", "$defs", "$ref", "title", "description", "type",
        "additionalProperties", "required", "properties", "items", "minItems",
        "maxItems", "minLength", "minimum", "maximum", "pattern", "format",
        "enum", "const", "oneOf", "x-ftro-registration",
    }

    def visit(value: Any, rule: Any, path: str) -> None:
        if not isinstance(rule, dict):
            errors.append(f"schema {path}: rule is not an object")
            return
        unknown = set(rule) - allowed
        if unknown:
            errors.append(f"schema {path}: unsupported keywords {sorted(unknown)}")
            return
        if "$ref" in rule:
            reference = rule["$ref"]
            prefix = "#/$defs/"
            if not isinstance(reference, str) or not reference.startswith(prefix):
                errors.append(f"schema {path}: unsupported reference {reference!r}")
                return
            name = reference[len(prefix):]
            target = definitions.get(name)
            if not isinstance(target, dict):
                errors.append(f"schema {path}: unresolved reference {reference!r}")
                return
            visit(value, target, path)
            return
        if "oneOf" in rule:
            branches = rule["oneOf"]
            if not isinstance(branches, list) or not branches:
                errors.append(f"schema {path}: oneOf must be a non-empty array")
                return
            matches = 0
            for branch in branches:
                branch_errors: list[str] = []
                before = len(errors)
                visit(value, branch, path)
                branch_errors.extend(errors[before:])
                del errors[before:]
                if not branch_errors:
                    matches += 1
            if matches != 1:
                errors.append(f"{path}: expected exactly one oneOf branch, observed {matches}")
            return
        if "const" in rule and not json_equal(value, rule["const"]):
            errors.append(f"{path}: differs from schema const")
        if "enum" in rule and not any(json_equal(value, item) for item in rule["enum"]):
            errors.append(f"{path}: value is outside schema enum")
        kind = rule.get("type")
        type_ok = True
        if kind == "object":
            type_ok = isinstance(value, dict)
        elif kind == "array":
            type_ok = isinstance(value, list)
        elif kind == "string":
            type_ok = isinstance(value, str)
        elif kind == "integer":
            type_ok = type(value) is int
        elif kind == "boolean":
            type_ok = type(value) is bool
        elif kind == "null":
            type_ok = value is None
        elif kind is not None:
            errors.append(f"schema {path}: unsupported type {kind!r}")
            return
        if not type_ok:
            errors.append(f"{path}: expected schema type {kind}")
            return
        if isinstance(value, dict):
            required = rule.get("required", [])
            properties = rule.get("properties", {})
            if not isinstance(required, list) or not isinstance(properties, dict):
                errors.append(f"schema {path}: malformed object constraints")
                return
            for name in required:
                if name not in value:
                    errors.append(f"{path}: missing required property {name}")
            if rule.get("additionalProperties") is False:
                for name in set(value) - set(properties):
                    errors.append(f"{path}: additional property {name}")
            for name, child in properties.items():
                if name in value:
                    visit(value[name], child, f"{path}/{name}")
        if isinstance(value, list):
            if "minItems" in rule and len(value) < rule["minItems"]:
                errors.append(f"{path}: fewer than minItems")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                errors.append(f"{path}: more than maxItems")
            if "items" in rule:
                for index, child in enumerate(value):
                    visit(child, rule["items"], f"{path}/{index}")
        if isinstance(value, str):
            if "minLength" in rule and len(value) < rule["minLength"]:
                errors.append(f"{path}: shorter than minLength")
            if "pattern" in rule and re.search(rule["pattern"], value) is None:
                errors.append(f"{path}: does not match pattern")
            if rule.get("format") == "date-time" and not timestamp(value):
                errors.append(f"{path}: invalid date-time")
            elif "format" in rule and rule.get("format") != "date-time":
                errors.append(f"schema {path}: unsupported format {rule.get('format')!r}")
        if type(value) is int:
            if "minimum" in rule and value < rule["minimum"]:
                errors.append(f"{path}: below minimum")
            if "maximum" in rule and value > rule["maximum"]:
                errors.append(f"{path}: above maximum")

    visit(instance, schema, "$")
    return errors


def validate_registration_manifest(body: bytes, commit: str) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_json_bytes(body, "registration manifest")
    except CheckError as exc:
        return [str(exc)]
    expected_keys = {
        "document", "version", "ready_for_step2", "runner", "report_output_path",
        "self_exclusion", "required_artifact_paths", "artifacts",
    }
    if set(manifest) != expected_keys:
        errors.append(
            "registration manifest: top-level keys differ; "
            f"missing={sorted(expected_keys - set(manifest))}, "
            f"extra={sorted(set(manifest) - expected_keys)}"
        )
    if manifest.get("document") != "FTRO WP2A v1.3 registration manifest":
        errors.append("registration manifest: wrong document")
    if manifest.get("version") != "1.3.0":
        errors.append("registration manifest: wrong version")
    if manifest.get("ready_for_step2") is not True:
        errors.append("registration manifest: ready_for_step2 is not true")
    self_exclusion = manifest.get("self_exclusion")
    if not isinstance(self_exclusion, dict) or self_exclusion.get("path") != MANIFEST_REL:
        errors.append("registration manifest: self exclusion differs")
    if manifest.get("runner") != {
        "path": "phase2/wp2a/run_step2_v1_3.py", "status": "ready"
    }:
        errors.append("registration manifest: /runner/status is not ready for the frozen runner")
    if manifest.get("self_exclusion") != {
        "path": MANIFEST_REL,
        "reason": "A file cannot contain its own settled byte digest; the report binds this manifest by full SHA-256.",
    }:
        errors.append("registration manifest: self-exclusion declaration differs")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("registration manifest: artifacts must be a non-empty array")
        return errors
    paths = []
    for index, row in enumerate(artifacts):
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            errors.append(f"registration manifest artifact {index}: wrong shape")
            continue
        path, expected = row.get("path"), row.get("sha256")
        if not isinstance(path, str) or path == MANIFEST_REL or path.startswith("/") or ".." in Path(path).parts:
            errors.append(f"registration manifest artifact {index}: unsafe/self path {path!r}")
            continue
        if not isinstance(expected, str) or not HEX64.fullmatch(expected):
            errors.append(f"registration manifest artifact {path}: malformed digest")
            continue
        paths.append(path)
        try:
            observed = digest_bytes(git_bytes(commit, path))
        except CheckError as exc:
            errors.append(str(exc))
            continue
        if observed != expected:
            errors.append(f"registration manifest artifact {path}: expected {expected}, observed {observed}")
    if len(paths) != len(set(paths)):
        errors.append("registration manifest: duplicate artifact paths")
    required = manifest.get("required_artifact_paths")
    if required != REQUIRED_REGISTRATION_PATHS:
        errors.append("registration manifest: required_artifact_paths differs from checker oracle")
    if paths != REQUIRED_REGISTRATION_PATHS:
        errors.append("registration manifest: artifact population/order differs from checker oracle")
    if manifest.get("report_output_path") != "phase2/wp2a/reports/step2-input-evidence-v1.3.json":
        errors.append("registration manifest: report_output_path differs")
    return errors


def validate_local_registration_manifest() -> list[str]:
    """Apply the same fixed-population check before a subject commit exists."""
    path = ROOT / MANIFEST_REL
    try:
        body = path.read_bytes()
        manifest = load_json_bytes(body, MANIFEST_REL)
    except (OSError, CheckError) as exc:
        return [f"local registration manifest: {exc}"]
    errors: list[str] = []
    if manifest.get("required_artifact_paths") != REQUIRED_REGISTRATION_PATHS:
        errors.append("local registration manifest: required paths differ from checker oracle")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return errors + ["local registration manifest: artifacts is not an array"]
    if [row.get("path") for row in artifacts if isinstance(row, dict)] != REQUIRED_REGISTRATION_PATHS:
        errors.append("local registration manifest: artifact population/order differs")
    for row in artifacts:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            errors.append("local registration manifest: malformed artifact row")
            continue
        artifact = ROOT / row["path"]
        if not artifact.is_file():
            errors.append(f"local registration manifest: absent {row['path']}")
        elif digest_file(artifact) != row["sha256"]:
            errors.append(f"local registration manifest: stale digest for {row['path']}")
    return errors


def validate_method(value: Any, label: str, errors: list[str]) -> bool:
    keys = {
        "method_id", "implementation", "implementation_sha256", "executable",
        "executable_sha256", "tool_available", "version_argv", "version_exit_code",
        "version_output", "input_handle", "input_binding_sha256",
        "input_binding_size_bytes", "argv", "non_execution_reason",
        "ran", "exit_code", "started_utc", "ended_utc", "stdout_sha256",
        "stdout_size_bytes", "stderr_sha256", "stderr_size_bytes",
    }
    if not exact_keys(value, keys, label, errors):
        return False
    for name in ("method_id", "implementation", "executable"):
        if not isinstance(value[name], str) or not value[name]:
            errors.append(f"{label}.{name}: expected non-empty string")
    if not isinstance(value["version_output"], str):
        errors.append(f"{label}.version_output: expected string")
    if type(value["tool_available"]) is not bool:
        errors.append(f"{label}.tool_available: expected boolean")
        return False
    if value["tool_available"]:
        if not isinstance(value["executable_sha256"], str) or not HEX64.fullmatch(value["executable_sha256"]):
            errors.append(f"{label}.executable_sha256: available tool needs SHA-256")
        if not integer(value["version_exit_code"]):
            errors.append(f"{label}.version_exit_code: available tool needs integer exit code")
    else:
        if value["executable_sha256"] is not None:
            errors.append(f"{label}.executable_sha256: unavailable tool requires null")
        if value["version_exit_code"] is not None or value["version_output"] != "":
            errors.append(f"{label}: unavailable tool requires null version exit and empty output")
        if value["ran"] is not False:
            errors.append(f"{label}.ran: unavailable tool cannot run")
    if value["implementation_sha256"] is not None and (
        not isinstance(value["implementation_sha256"], str)
        or not HEX64.fullmatch(value["implementation_sha256"])
    ):
        errors.append(f"{label}.implementation_sha256: malformed SHA-256/null")
    if value["input_binding_sha256"] is not None and (
        not isinstance(value["input_binding_sha256"], str)
        or not HEX64.fullmatch(value["input_binding_sha256"])
    ):
        errors.append(f"{label}.input_binding_sha256: malformed SHA-256/null")
    if value["input_binding_size_bytes"] is not None and not integer(
        value["input_binding_size_bytes"]
    ):
        errors.append(f"{label}.input_binding_size_bytes: expected integer/null")
    if (value["input_binding_sha256"] is None) != (value["input_binding_size_bytes"] is None):
        errors.append(f"{label}: input binding digest and size must be jointly present/null")
    if value["non_execution_reason"] is not None and (
        not isinstance(value["non_execution_reason"], str)
        or not value["non_execution_reason"]
    ):
        errors.append(f"{label}.non_execution_reason: expected non-empty string/null")
    for name in ("version_argv", "argv"):
        if not isinstance(value[name], list) or not value[name] or not all(isinstance(x, str) for x in value[name]):
            errors.append(f"{label}.{name}: expected non-empty string array")
    if type(value["ran"]) is not bool:
        errors.append(f"{label}.ran: expected boolean")
        return False
    if value["ran"]:
        if value["non_execution_reason"] is not None:
            errors.append(f"{label}.non_execution_reason: executed method requires null")
        if not isinstance(value["input_handle"], str) or not re.fullmatch(
            r"/dev/fd/[0-9]+", value["input_handle"]
        ):
            errors.append(f"{label}.input_handle: executed method needs anonymous /dev/fd handle")
        if value["input_binding_sha256"] is None or value["input_binding_size_bytes"] is None:
            errors.append(f"{label}: executed method needs authenticated input binding")
        if not integer(value["exit_code"]):
            errors.append(f"{label}.exit_code: executed method needs integer exit code")
        if not timestamp(value["started_utc"]) or not timestamp(value["ended_utc"]):
            errors.append(f"{label}: executed method needs timezone-aware start/end")
        for name in ("stderr_sha256",):
            if not isinstance(value[name], str) or not HEX64.fullmatch(value[name]):
                errors.append(f"{label}.{name}: executed method needs SHA-256")
        if not integer(value["stderr_size_bytes"]):
            errors.append(f"{label}.stderr_size_bytes: executed method needs integer")
    else:
        if not isinstance(value["non_execution_reason"], str) or not value["non_execution_reason"]:
            errors.append(f"{label}.non_execution_reason: unexecuted method needs a reason")
        if value["input_handle"] is not None:
            errors.append(f"{label}.input_handle: unexecuted method must carry null")
        for name in (
            "exit_code", "started_utc", "ended_utc", "stdout_sha256", "stdout_size_bytes",
            "stderr_sha256", "stderr_size_bytes",
        ):
            if value[name] is not None:
                errors.append(f"{label}.{name}: unexecuted method must carry null")
    if value["stdout_sha256"] is not None and (
        not isinstance(value["stdout_sha256"], str) or not HEX64.fullmatch(value["stdout_sha256"])
    ):
        errors.append(f"{label}.stdout_sha256: malformed")
    if value["stdout_size_bytes"] is not None and not integer(value["stdout_size_bytes"]):
        errors.append(f"{label}.stdout_size_bytes: expected integer/null")
    return True


def method_success(value: dict[str, Any]) -> bool:
    return (
        value.get("tool_available") is True
        and integer(value.get("version_exit_code"))
        and value.get("ran") is True
        and value.get("exit_code") == 0
        and isinstance(value.get("stdout_sha256"), str)
        and bool(HEX64.fullmatch(value["stdout_sha256"]))
        and integer(value.get("stdout_size_bytes"))
        and value["stdout_size_bytes"] > 0
    )


def expected_argv(method_id: str, executable: str, input_handle: str, member: str | None) -> list[str]:
    runner = "phase2/wp2a/run_step2_v1_3.py"
    if method_id == "ftro_unixz":
        return [executable, "-I", runner, "_decode-unixz", "--input", input_handle]
    if method_id == "system_gzip":
        return [executable, "-dc", input_handle]
    if method_id == "python_zipfile":
        return [executable, "-I", runner, "_extract-zipfile", "--input", input_handle, "--member", member or ""]
    if method_id == "system_unzip":
        return [executable, "-p", input_handle, member or ""]
    raise CheckError(f"unknown method_id {method_id!r}")


def derive_target_outcome(row: dict[str, Any]) -> tuple[str, str | None, int | None, bool | None]:
    a, b = row["method_a"], row["method_b"]
    if not method_success(a) or not method_success(b):
        return "not_executed", None, None, None
    if row.get("byte_comparison") != "direct_byte_equality" or type(row.get("bytes_equal")) is not bool:
        return "not_executed", None, None, None
    if row["bytes_equal"] is False:
        return "evidence_assurance_failed", None, None, None
    # Direct byte equality implies both recorded projections must agree too.
    if a["stdout_sha256"] != b["stdout_sha256"] or a["stdout_size_bytes"] != b["stdout_size_bytes"]:
        return "evidence_assurance_failed", None, None, None
    observed_sha = a["stdout_sha256"]
    observed_size = a["stdout_size_bytes"]
    matches = observed_sha == row["expected_sha256"] and observed_size == row["expected_size_bytes"]
    return ("supports" if matches else "contradicts"), observed_sha, observed_size, matches


def derive_run_outcome(outcomes: list[str], *, n_inputs_changed: int = 0) -> str:
    if "not_executed" in outcomes:
        return "step2_not_executed"
    if n_inputs_changed or "evidence_assurance_failed" in outcomes:
        return "step2_evidence_assurance_failed"
    if "contradicts" in outcomes:
        return "step2_contradicts"
    if outcomes == ["supports"] * 4:
        return "step2_supports"
    return "step2_not_executed"


def validate_report(report: dict[str, Any], *, authenticate_manifest: bool = True) -> list[str]:
    errors: list[str] = []
    schema = None
    subject_commit = report.get("subject", {}).get("commit") if isinstance(report, dict) else None
    if authenticate_manifest and isinstance(subject_commit, str) and HEX40.fullmatch(subject_commit):
        try:
            schema = load_json_bytes(git_bytes(subject_commit, SCHEMA_REL), "subject Step-2 schema")
        except CheckError as exc:
            errors.append(str(exc))
    if schema is None:
        try:
            schema = load_json(SCHEMA_PATH)
        except CheckError as exc:
            return errors + [str(exc)]
    try:
        _, registration = schema_registration(schema)
    except CheckError as exc:
        return errors + [str(exc)]
    errors.extend(json_schema_errors(report, schema))
    top_keys = {
        "document", "schema_version", "run_id", "subject", "registration_manifest",
        "started_utc", "ended_utc", "input_authentication", "targets", "counters",
        "overall_outcome", "output_path",
    }
    if not exact_keys(report, top_keys, "report", errors):
        return errors
    if report["document"] != "FTRO WP2A Step-2 input-evidence report" or report["schema_version"] != "1.3.0":
        errors.append("report document/schema_version differs")
    if not isinstance(report["run_id"], str) or not re.fullmatch(r"[A-Za-z0-9._:-]+", report["run_id"]):
        errors.append("run_id: malformed")
    if not timestamp(report["started_utc"]) or not timestamp(report["ended_utc"]):
        errors.append("run timestamps must be timezone-aware ISO-8601")
    if report["output_path"] != registration["report_output_path"]:
        errors.append("output_path differs from registration")

    subject_keys = {"commit", "tree", "worktree_clean", "published", "published_ref"}
    subject_ok = exact_keys(report["subject"], subject_keys, "subject", errors)
    if subject_ok:
        subject = report["subject"]
        if subject["worktree_clean"] is not True or subject["published"] is not True:
            errors.append("subject must assert clean and published")
        if not isinstance(subject["commit"], str) or not HEX40.fullmatch(subject["commit"]):
            errors.append("subject.commit malformed")
        if not isinstance(subject["tree"], str) or not HEX40.fullmatch(subject["tree"]):
            errors.append("subject.tree malformed")
        elif isinstance(subject["commit"], str) and HEX40.fullmatch(subject["commit"]):
            try:
                tree = git_text("rev-parse", f"{subject['commit']}^{{tree}}")
                if tree != subject["tree"]:
                    errors.append(f"subject.tree differs from commit tree: {tree}")
            except CheckError as exc:
                errors.append(str(exc))
        if (
            isinstance(subject.get("commit"), str)
            and HEX40.fullmatch(subject["commit"])
            and not git_contains(subject["commit"], subject.get("published_ref"))
        ):
            errors.append("subject.commit is not contained in subject.published_ref")

    manifest_keys = {"path", "sha256"}
    manifest_ok = exact_keys(report["registration_manifest"], manifest_keys, "registration_manifest", errors)
    if manifest_ok:
        manifest_ref = report["registration_manifest"]
        if manifest_ref["path"] != MANIFEST_REL:
            errors.append("registration manifest path differs")
        if not isinstance(manifest_ref["sha256"], str) or not HEX64.fullmatch(manifest_ref["sha256"]):
            errors.append("registration manifest digest malformed")
        elif (
            authenticate_manifest
            and subject_ok
            and isinstance(report["subject"].get("commit"), str)
            and HEX40.fullmatch(report["subject"]["commit"])
        ):
            try:
                body = git_bytes(report["subject"]["commit"], MANIFEST_REL)
                if digest_bytes(body) != manifest_ref["sha256"]:
                    errors.append("registration manifest digest differs from subject commit")
                errors.extend(validate_registration_manifest(body, report["subject"]["commit"]))
            except CheckError as exc:
                errors.append(str(exc))

    expected_inputs = registration["input_policy"]["population"]
    inputs = report["input_authentication"]
    if not isinstance(inputs, list) or len(inputs) != len(expected_inputs):
        errors.append(f"input_authentication: expected exactly {len(expected_inputs)} rows")
        inputs = []
    input_map = {}
    input_shape = {
        "input_id", "path", "acquisition_mode", "registered_route", "expected_outer_sha256",
        "expected_outer_size_bytes", "observed_outer_sha256", "observed_outer_size_bytes",
        "post_observed_outer_sha256", "post_observed_outer_size_bytes",
        "postflight_path_matches_captured_snapshot", "outcome",
    }
    for index, (row, expected) in enumerate(zip(inputs, expected_inputs)):
        label = f"input_authentication[{index}]"
        if not exact_keys(row, input_shape, label, errors):
            continue
        for name in (
            "input_id", "path", "acquisition_mode", "registered_route", "expected_outer_sha256",
            "expected_outer_size_bytes",
        ):
            if row[name] != expected[name]:
                errors.append(f"{label}.{name}: differs from registration")
        observed_sha, observed_size = row["observed_outer_sha256"], row["observed_outer_size_bytes"]
        post_sha = row["post_observed_outer_sha256"]
        post_size = row["post_observed_outer_size_bytes"]
        if observed_sha is not None and (not isinstance(observed_sha, str) or not HEX64.fullmatch(observed_sha)):
            errors.append(f"{label}.observed_outer_sha256 malformed")
        if observed_size is not None and not integer(observed_size):
            errors.append(f"{label}.observed_outer_size_bytes malformed")
        if observed_sha is None and observed_size is None:
            if row["outcome"] not in {"missing", "unreadable"}:
                errors.append(
                    f"{label}.outcome: null observations require missing/unreadable, "
                    f"observed {row['outcome']}"
                )
        elif observed_sha is None or observed_size is None:
            if row["outcome"] != "unreadable":
                errors.append(f"{label}.outcome: partial observation requires unreadable")
        else:
            derived = (
                "digest_mismatch" if observed_sha != expected["expected_outer_sha256"]
                else "size_mismatch" if observed_size != expected["expected_outer_size_bytes"]
                else "authenticated"
            )
            if row["outcome"] != derived:
                errors.append(f"{label}.outcome: expected derived {derived}, observed {row['outcome']}")
        if post_sha is not None and (not isinstance(post_sha, str) or not HEX64.fullmatch(post_sha)):
            errors.append(f"{label}.post_observed_outer_sha256 malformed")
        if post_size is not None and not integer(post_size):
            errors.append(f"{label}.post_observed_outer_size_bytes malformed")
        if row["outcome"] == "authenticated":
            post_match = (
                post_sha == expected["expected_outer_sha256"]
                and post_size == expected["expected_outer_size_bytes"]
                and post_sha == observed_sha
                and post_size == observed_size
            )
            if row["postflight_path_matches_captured_snapshot"] is not post_match:
                errors.append(
                    f"{label}.postflight_path_matches_captured_snapshot: expected derived "
                    f"{post_match}, observed "
                    f"{row['postflight_path_matches_captured_snapshot']!r}"
                )
        elif row["postflight_path_matches_captured_snapshot"] is not None:
            errors.append(
                f"{label}.postflight_path_matches_captured_snapshot: unauthenticated "
                "preflight requires null"
            )
        input_map[row["input_id"]] = row
    if len(input_map) != len(inputs):
        errors.append("input_authentication: duplicate input_id")
    all_inputs_authenticated = len(inputs) == 4 and all(
        row.get("outcome") == "authenticated" for row in inputs
    )

    expected_targets = registration["target_population"]
    targets = report["targets"]
    if not isinstance(targets, list) or len(targets) != len(expected_targets):
        errors.append(f"targets: expected exactly {len(expected_targets)} rows")
        targets = []
    target_shape = {
        "target_id", "input_id", "member_selector", "expected_sha256", "expected_size_bytes",
        "expected_source", "method_a", "method_b", "byte_comparison", "bytes_equal",
        "observed_sha256", "observed_size_bytes", "matches_expected", "outcome",
    }
    outcomes = []
    for index, (row, expected) in enumerate(zip(targets, expected_targets)):
        label = f"targets[{index}]"
        if not exact_keys(row, target_shape, label, errors):
            continue
        for name in (
            "target_id", "input_id", "expected_sha256", "expected_size_bytes", "expected_source"
        ):
            if row[name] != expected[name]:
                errors.append(f"{label}.{name}: differs from registration")
        expected_member = expected.get("member_selector")
        if row["member_selector"] != expected_member:
            errors.append(f"{label}.member_selector differs from registration")
        a_ok = validate_method(row["method_a"], f"{label}.method_a", errors)
        b_ok = validate_method(row["method_b"], f"{label}.method_b", errors)
        if a_ok and b_ok:
            if row["method_a"]["method_id"] != expected["method_a"]:
                errors.append(f"{label}.method_a.method_id differs")
            if row["method_b"]["method_id"] != expected["method_b"]:
                errors.append(f"{label}.method_b.method_id differs")
            input_record = input_map.get(expected["input_id"])
            for side in ("method_a", "method_b"):
                method = row[side]
                try:
                    method_contract = registration["method_contracts"][method["method_id"]]
                    if method["implementation"] != method_contract["implementation"]:
                        errors.append(f"{label}.{side}.implementation differs from frozen contract")
                    expected_version = [
                        method["executable"],
                        *(method_contract["version_argv_template"][1:]),
                    ]
                    if method["version_argv"] != expected_version:
                        errors.append(f"{label}.{side}.version_argv differs from frozen template")
                    handle = method["input_handle"] if method["ran"] else "<not-opened>"
                    argv = expected_argv(
                        method["method_id"], method["executable"], handle, expected_member
                    )
                    if method["argv"] != argv:
                        errors.append(f"{label}.{side}.argv differs from frozen template")
                    if input_record is not None:
                        for field, expected_value in (
                            ("input_binding_sha256", input_record["observed_outer_sha256"]),
                            ("input_binding_size_bytes", input_record["observed_outer_size_bytes"]),
                        ):
                            if method[field] != expected_value:
                                errors.append(
                                    f"{label}.{side}.{field}: differs from authenticated input"
                                )
                    if method["ran"] is False:
                        if not all_inputs_authenticated:
                            expected_reason = "global_input_preflight_failed"
                            if method["non_execution_reason"] != expected_reason:
                                errors.append(
                                    f"{label}.{side}.non_execution_reason: expected "
                                    f"{expected_reason!r} after failed global input preflight"
                                )
                        elif method["tool_available"] is False:
                            if method["non_execution_reason"] != "tool_unavailable":
                                errors.append(
                                    f"{label}.{side}.non_execution_reason: unavailable tool "
                                    "requires 'tool_unavailable'"
                                )
                        elif (
                            not isinstance(method["non_execution_reason"], str)
                            or not method["non_execution_reason"].startswith(
                                "snapshot_or_method_start_failed:"
                            )
                        ):
                            errors.append(
                                f"{label}.{side}.non_execution_reason: authenticated input and "
                                "available tool require a snapshot/start failure"
                            )
                except (CheckError, KeyError, TypeError) as exc:
                    errors.append(str(exc))
        if not all_inputs_authenticated and (
            row.get("method_a", {}).get("ran") is not False or row.get("method_b", {}).get("ran") is not False
        ):
            errors.append(f"{label}: a method ran although input preflight was not wholly authenticated")
        try:
            derived, observed_sha, observed_size, matches = derive_target_outcome(row)
        except (KeyError, TypeError) as exc:
            errors.append(f"{label}: cannot derive outcome: {exc}")
            continue
        outcomes.append(derived)
        for name, actual in (
            ("outcome", derived), ("observed_sha256", observed_sha),
            ("observed_size_bytes", observed_size), ("matches_expected", matches),
        ):
            if row[name] != actual:
                errors.append(f"{label}.{name}: expected derived {actual!r}, observed {row[name]!r}")

    counters = report["counters"]
    counter_keys = {
        "n_targets", "n_supports", "n_contradicts", "n_evidence_assurance_failed",
        "n_not_executed", "n_inputs_changed_during_run",
    }
    if exact_keys(counters, counter_keys, "counters", errors):
        n_inputs_changed = sum(
            row.get("postflight_path_matches_captured_snapshot") is False for row in inputs
        )
        derived_counters = {
            "n_targets": len(outcomes),
            "n_supports": outcomes.count("supports"),
            "n_contradicts": outcomes.count("contradicts"),
            "n_evidence_assurance_failed": outcomes.count("evidence_assurance_failed"),
            "n_not_executed": outcomes.count("not_executed"),
            "n_inputs_changed_during_run": n_inputs_changed,
        }
        if counters != derived_counters:
            errors.append(f"counters differ from target rows: expected {derived_counters}, observed {counters}")
    n_inputs_changed = sum(
        row.get("postflight_path_matches_captured_snapshot") is False for row in inputs
    )
    derived_overall = derive_run_outcome(outcomes, n_inputs_changed=n_inputs_changed)
    if report["overall_outcome"] != derived_overall:
        errors.append(f"overall_outcome: expected {derived_overall}, observed {report['overall_outcome']}")
    return errors


def atomic_create(path: Path, body: bytes) -> None:
    """Atomically create ``path`` and refuse every overwrite, including a race."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise CheckError(f"refusing to overwrite immutable report {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".part", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            raise CheckError(f"refusing to overwrite immutable report {path}") from exc
    finally:
        temporary_path.unlink(missing_ok=True)


def rejected_path(official: Path, run_id: str | None, body: bytes) -> Path:
    safe = run_id if isinstance(run_id, str) and re.fullmatch(r"[A-Za-z0-9._:-]+", run_id) else digest_bytes(body)[:16]
    return official.with_name(official.name + f".{safe}.rejected")


def publish_candidate(candidate: Path, official: Path) -> tuple[Path, list[str]]:
    try:
        body = candidate.read_bytes()
    except OSError as exc:
        raise CheckError(f"cannot read candidate report: {exc}") from exc
    try:
        report = load_json_bytes(body, str(candidate))
        errors = validate_report(report)
    except Exception as exc:
        # Candidate bytes are evidence even when a validator branch itself cannot
        # interpret them.  Preserve rather than turning a malformed report into a
        # traceback with no durable rejected record.
        report, errors = {}, [f"validation exception {type(exc).__name__}: {exc}"]
    if errors or report.get("overall_outcome") != "step2_supports":
        destination = rejected_path(official, report.get("run_id"), body)
    else:
        destination = official
    atomic_create(destination, body)
    return destination, errors


def check_registration() -> list[str]:
    errors = validate_local_registration_manifest()
    try:
        _, registration = schema_registration()
    except CheckError as exc:
        return [str(exc)]
    for label, record in registration.get("registration_sources", {}).items():
        path = ROOT / record.get("path", "")
        if not path.is_file():
            errors.append(f"registration source {label}: absent {path}")
            continue
        observed = digest_file(path)
        if observed != record.get("sha256"):
            errors.append(f"registration source {label}: expected {record.get('sha256')}, observed {observed}")
    targets = registration.get("target_population")
    if not isinstance(targets, list) or len(targets) != 4:
        errors.append("registration target population is not exactly four")
    elif len({row.get("target_id") for row in targets}) != 4:
        errors.append("registration target IDs are not unique")
    for row in targets or []:
        if not HEX64.fullmatch(str(row.get("expected_sha256", ""))):
            errors.append(f"target {row.get('target_id')}: expected digest is not full SHA-256")
        if not integer(row.get("expected_size_bytes")) or row["expected_size_bytes"] <= 0:
            errors.append(f"target {row.get('target_id')}: invalid expected size")
    methods = registration.get("method_contracts", {})
    if set(methods) != {"ftro_unixz", "system_gzip", "python_zipfile", "system_unzip"}:
        errors.append("method population differs from the registered four")
    if "gzip" not in registration.get("trusted_computing_base", {}).get("required_tools", []):
        errors.append("gzip is absent from the TCB tool population")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-registration", action="store_true")
    group.add_argument("--check-report", metavar="PATH")
    group.add_argument("--promote", metavar="CANDIDATE")
    parser.add_argument("--out", default="phase2/wp2a/reports/step2-input-evidence-v1.3.json")
    args = parser.parse_args(argv)
    if args.check_registration:
        errors = check_registration()
        if errors:
            print("FAIL WP2A v1.3 Step-2 registration: " + "; ".join(errors), file=sys.stderr)
            return 1
        print("WP2A v1.3 Step-2 registration: PASS")
        return 0
    if args.check_report:
        try:
            report = load_json(ROOT / args.check_report if not Path(args.check_report).is_absolute() else Path(args.check_report))
            errors = validate_report(report)
        except (CheckError, KeyError, TypeError, ValueError, IndexError) as exc:
            errors = [str(exc)]
        if errors:
            print("FAIL WP2A v1.3 Step-2 report: " + "; ".join(errors), file=sys.stderr)
            return 1
        print("WP2A v1.3 Step-2 report: PASS")
        return 0
    candidate = ROOT / args.promote if not Path(args.promote).is_absolute() else Path(args.promote)
    official = ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    try:
        expected_official = ROOT / schema_registration()[1]["report_output_path"]
        if official.resolve() != expected_official.resolve():
            raise CheckError(
                f"--out must be the frozen report output {expected_official}; observed {official}"
            )
    except (OSError, CheckError, KeyError, TypeError, ValueError) as exc:
        print(f"FAIL WP2A v1.3 Step-2 promotion: {exc}", file=sys.stderr)
        return 1
    try:
        destination, errors = publish_candidate(candidate, official)
    except (CheckError, KeyError, TypeError, ValueError, IndexError) as exc:
        print(f"FAIL WP2A v1.3 Step-2 promotion: {exc}", file=sys.stderr)
        return 1
    if errors:
        print(f"REJECTED at {destination}: " + "; ".join(errors), file=sys.stderr)
        return 1
    if destination != official:
        print(f"NON-SUPPORTING Step-2 report preserved at {destination}", file=sys.stderr)
        return 1
    print(f"promoted immutable Step-2 report to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
