#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Strict validation contract for a successful Phase-0 C9 report.

The live runner and every later consumer use this module as the one definition of a
qualifying C9 witness.  Validation is against the immutable carrier commit, rather than
against whichever generated files happen to be in the current worktree.  A producer can
additionally request checks of its freshly generated worktree outputs by setting
``output_view`` to ``"producer"`` in the carrier context.

The public entry points deliberately have a small surface:

``validate_success_report(report, root, context)``
    Return a list of errors.  An empty list is a demonstrated success.

``assert_success_report(report, root, context)``
    Return compact evidence or raise :class:`C9ContractError`.

``context`` is a mapping containing ``commit`` and ``tree``.  Optional keys are
``required_ancestor``, ``before_utc``, ``output_view`` (``carrier`` or ``producer``),
``report_path`` and ``verify_runtime_tools``.  The latter two are producer-only checks:
a later consumer validates their recorded provenance without requiring the historical
absolute report path or executable bytes to exist on its host.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


REPORT_KEYS = {
    "document", "version", "run_id", "started_utc", "ended_utc", "status",
    "qualifying", "subject", "contract", "pipeline", "runner", "environment",
    "bound_inputs", "bound_input_fingerprint_sha256", "manual_interventions",
    "manual_interventions_basis", "route_substitutions", "route_substitutions_basis",
    "first_failure", "step_results", "prepared_outputs", "regenerated_output_checks",
    "optical_archive", "expected_provider_attempts", "provider_attempts",
    "provider_report_evidence", "provider_evidence_errors",
    "n_provider_attempts_recorded", "n_provider_attempts_successful",
    "provider_population_verified", "deterministic_output_checks", "cleanup",
    "tracked_change_evidence", "provisional_witness",
}
STEP_KEYS = {
    "step", "script", "argv_prefix", "started_utc", "ended_utc", "duration_s",
    "exit_code", "spawn_error", "process_group", "stdout_n_bytes", "stderr_n_bytes",
    "stdout_sha256", "stderr_sha256", "stdout_excerpt", "stderr_excerpt", "stdout_text",
    "stderr_text",
}
PIN_ATTEMPT_KEYS = {
    "source_group", "step", "artifact", "url", "failure_class", "reachability_stage",
    "access_class_conclusion", "http_status", "bytes_received", "expected_sha256",
    "reported_expected_sha256", "observed_sha256", "content_validation_result",
    "retrieved_utc",
}
OPTICAL_ATTEMPT_KEYS = {
    "source_group", "step", "artifact", "url", "failure_class", "reachability_stage",
    "access_class_conclusion", "access_evidence", "http_status", "content_type",
    "bytes_received", "expected_md5", "observed_md5", "expected_sha256",
    "observed_sha256", "content_validation_result",
}
SUBJECT_KEYS = {
    "commit", "tree", "required_ancestor", "clean", "detached_head",
    "checkout_realpath",
}
CONTRACT_KEYS = {"id", "version", "clause", "path", "sha256"}
PIPELINE_KEYS = {
    "path", "sha256", "command_block_sha256", "steps_expected", "steps_completed",
}
RUNNER_KEYS = {"path", "sha256"}
ENVIRONMENT_KEYS = {"python", "platform", "variables", "toolchain", "stdin"}
TOOLCHAIN_KEYS = {
    "approved_prefixes", "tools", "selected_pipeline_shell", "sanitized_path",
    "forbidden_inherited_variables", "errors", "verified",
}
TOOL_KEYS = {
    "name", "invocation_path", "resolved_path", "sha256", "probe_argv",
    "probe_exit_code", "probe_output",
}
PREPARED_KEYS = {
    "path", "removed_before_step", "expected_sha256", "expected_size_bytes",
}
REGENERATED_KEYS = {
    "path", "step", "recreated", "expected_sha256", "observed_sha256", "byte_match",
    "match",
}
DETERMINISTIC_KEYS = {
    "name", "path", "expected_sha256", "observed_sha256", "match",
}
PROVIDER_REPORT_KEYS = {
    "section", "promoted", "fresh", "path", "sha256", "n_expected", "n_observed",
    "errors",
}
OPTICAL_KEYS = {
    "http_status", "effective_url", "content_type", "curl_size_download", "size_bytes",
    "md5", "expected_md5", "md5_match", "sha256", "authentication_material_supplied",
    "proxy_environment_supplied",
}
CLEANUP_KEYS = {"attempted", "removed", "errors", "provider_bytes_retained"}
TRACKED_CHANGE_KEYS = {
    "changed_paths", "changed_paths_sha256", "allowed_paths", "unexpected_paths",
    "pin_reports_not_changed", "untracked_paths", "verified",
}
PROVISIONAL_KEYS = {"path", "sha256", "retained_after_successful_finalization"}

PIN_REPORTS = {
    "evidence_repos": {
        "step": 1, "path": "phase0/reports/evidence-repo-pins.json", "id": "key",
        "count": 3,
    },
    "igs": {
        "step": 4, "path": "phase0/reports/igs-artifact-pins.json", "id": "name",
        "count": 57,
    },
    "ppta": {
        "step": 4, "path": "phase0/reports/ppta-artifact-pins.json", "id": "name",
        "count": 4,
    },
    "vgosdb": {
        "step": 4, "path": "phase0/reports/vlbi-vgosdb-pin.json",
        "id": "url_basename", "count": 1,
    },
}
REGENERATED_BY_STEP = {
    1: ["phase0/reports/evidence-repo-pins.json"],
    3: ["phase0/reports/optical-inventory-summary.json"],
    4: [
        "phase0/reports/igs-artifact-pins.json",
        "phase0/reports/vlbi-vgosdb-pin.json",
        "phase0/reports/ppta-artifact-pins.json",
    ],
    5: ["phase0/reports/four-domain-intersection.json"],
    6: ["ledgers/deficiency-log.md", "phase0/optical-validity-intervals.md"],
}
NONDETERMINISTIC = {row["path"] for row in PIN_REPORTS.values()}
DETERMINISTIC = {
    "step2_stdout": "phase0/evidence/VA-GPS2UTC-001.json",
    "step3_optical_summary": "phase0/reports/optical-inventory-summary.json",
    "step5_intersection": "phase0/reports/four-domain-intersection.json",
    "step6_deficiencies": "ledgers/deficiency-log.md",
    "step6_validity": "phase0/optical-validity-intervals.md",
}
ALLOWED_TRACKED_OUTPUTS = {
    path for paths in REGENERATED_BY_STEP.values() for path in paths
}
EXPECTED_OPTICAL_MD5 = "4ae290f559c90b462991286c933a1147"
EXPECTED_PROVIDER_ATTEMPTS = 66
EXPECTED_CONTRACT_PATH = "phase0/acceptance-contract-v1.0.md"
EXPECTED_RUNNER_PATH = "phase0/audit/run_c9.py"
EXPECTED_REGISTRY_PATH = "phase0/evidence/expected-digests.json"
EXPECTED_TOOL_NAMES = ("python3", "curl", "md5", "unzip", "git", "mkdir", "shell")
APPROVED_TOOL_PREFIXES = (
    "/bin/", "/sbin/", "/usr/bin/", "/usr/sbin/", "/usr/local/bin/",
    "/opt/homebrew/bin/", "/opt/homebrew/Cellar/", "/Library/Developer/",
)
SAFE_ENVIRONMENT_KEYS = {
    "PATH", "HOME", "CURL_HOME", "XDG_CONFIG_HOME", "GIT_CONFIG_GLOBAL", "LC_ALL",
    "GIT_CONFIG_NOSYSTEM", "GIT_ATTR_NOSYSTEM", "GIT_NO_REPLACE_OBJECTS",
    "TZ", "PYTHONHASHSEED",
    "PYTHONNOUSERSITE", "NO_COLOR", "TMPDIR",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
MD5_RE = re.compile(r"[0-9a-f]{32}")
OID_RE = re.compile(r"[0-9a-f]{40}")
TRUSTED_GIT_CANDIDATES = (
    "/usr/bin/git",
    "/usr/local/bin/git",
    "/opt/homebrew/bin/git",
)


class C9ContractError(ValueError):
    """A purported successful C9 report does not satisfy the shared contract."""


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _true_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _utc(value, label, errors):
    if not isinstance(value, str):
        errors.append(f"{label} must be a timestamp string")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} is not ISO-8601")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{label} has no timezone")
        return None
    return parsed.astimezone(dt.timezone.utc)


def _exact_keys(value, expected, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        errors.append(f"{label} keys differ: missing={missing}, unknown={unknown}")
        return False
    return True


def _trusted_git():
    for candidate in TRUSTED_GIT_CANDIDATES:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return candidate
    raise C9ContractError(
        "no executable Git found at a fixed trusted path: "
        + ", ".join(TRUSTED_GIT_CANDIDATES)
    )


def _git(root, *args, text=False, git_command=None):
    command = git_command or _trusted_git()
    if not isinstance(command, str) or not Path(command).is_absolute() \
            or not Path(command).is_file() or not os.access(command, os.X_OK):
        raise C9ContractError("controller Git is not an executable absolute path")
    completed = subprocess.run(
        [command, "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-c", "core.hooksPath=/dev/null", *args],
        cwd=root, capture_output=True, text=text, timeout=120,
        env={
            "PATH": os.defpath,
            "LC_ALL": "C",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
        },
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        stderr = completed.stderr if text else completed.stderr.decode(errors="replace")
        raise C9ContractError(f"git {' '.join(args)} failed: {stderr[-800:]}")
    return completed.stdout


def _carrier_bytes(root, commit, relative, git_command=None):
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise C9ContractError(f"invalid carrier path: {relative!r}")
    return _git(root, "show", f"{commit}:{relative}", git_command=git_command)


def _carrier_rows(root, commit, git_command=None):
    names = _git(root, "ls-tree", "-r", "--name-only", "-z", commit,
                 git_command=git_command).split(b"\0")
    rows = []
    for encoded in names:
        if not encoded:
            continue
        relative = encoded.decode("utf-8")
        body = _carrier_bytes(root, commit, relative, git_command)
        rows.append({"path": relative, "sha256": _sha256(body), "size_bytes": len(body)})
    rows.sort(key=lambda row: row["path"])
    return rows


def _extract_pipeline(body, errors):
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        errors.append("carrier README.md is not UTF-8")
        return None, None
    heading = text.find("## Reproducing Phase 0")
    start = text.find("```bash\n", heading)
    end = text.find("\n```", start + 8)
    if heading < 0 or start < 0 or end < 0:
        errors.append("carrier README reproduction block is absent")
        return None, None
    block = text[start + len("```bash\n"):end]
    matches = list(re.finditer(r"(?m)^# ([0-7])\. .+$", block))
    if [int(match.group(1)) for match in matches] != list(range(8)):
        errors.append("carrier README steps are not exactly 0 through 7")
        return block, None
    steps = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        steps.append(block[match.start():stop].strip())
    return block, steps


def _pin_identifier(section, pin):
    if section == "vgosdb":
        url = pin.get("url") if isinstance(pin, dict) else None
        return url.rsplit("/", 1)[-1] if isinstance(url, str) else None
    return pin.get(PIN_REPORTS[section]["id"]) if isinstance(pin, dict) else None


def _carrier_expectations(root, commit, errors, git_command=None):
    try:
        registry = json.loads(_carrier_bytes(
            root, commit, EXPECTED_REGISTRY_PATH, git_command,
        ))
    except (C9ContractError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"cannot read carrier digest registry: {exc}")
        return None
    expected = {}
    baseline_urls = {}
    for section, config in PIN_REPORTS.items():
        values = registry.get(section)
        if not isinstance(values, dict) or len(values) != config["count"]:
            errors.append(
                f"carrier registry {section} has {len(values) if isinstance(values, dict) else 'invalid'} "
                f"items, expected {config['count']}"
            )
            continue
        normalized = {}
        for identifier, value in values.items():
            digest = value.get("sha256") if isinstance(value, dict) else value
            if not isinstance(identifier, str) or SHA256_RE.fullmatch(digest or "") is None:
                errors.append(f"carrier registry {section}/{identifier!r} is malformed")
                continue
            normalized[identifier] = digest
        expected[section] = normalized

        try:
            baseline = json.loads(_carrier_bytes(
                root, commit, config["path"], git_command,
            ))
        except (C9ContractError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read carrier {section} pin report: {exc}")
            continue
        pins = baseline.get("pins") if isinstance(baseline, dict) else None
        if not isinstance(pins, list):
            pins = [baseline] if isinstance(baseline, dict) else []
        section_urls = {}
        for pin in pins:
            identifier = _pin_identifier(section, pin)
            url = pin.get("url") if isinstance(pin, dict) else None
            if not isinstance(identifier, str) or not isinstance(url, str):
                errors.append(f"carrier {section} report has a malformed pin identity")
                continue
            if identifier in section_urls:
                errors.append(f"carrier {section} report duplicates {identifier}")
            section_urls[identifier] = url
        if set(section_urls) != set(normalized):
            errors.append(f"carrier {section} report population differs from the registry")
        baseline_urls[section] = section_urls
    if sum(len(values) for values in expected.values()) != 65:
        errors.append("carrier registry does not contain exactly 65 provider pins")
    return expected, baseline_urls


def _validate_stream(record, stream, label, errors):
    text = record.get(f"{stream}_text")
    size = record.get(f"{stream}_n_bytes")
    digest = record.get(f"{stream}_sha256")
    excerpt = record.get(f"{stream}_excerpt")
    if not isinstance(text, str):
        errors.append(f"{label}.{stream}_text must be a string")
        return
    body = text.encode("utf-8")
    if not _true_int(size) or size != len(body):
        errors.append(f"{label}.{stream}_n_bytes differs from full text")
    if digest != _sha256(body):
        errors.append(f"{label}.{stream}_sha256 differs from full text")
    if excerpt != text[-8000:]:
        errors.append(f"{label}.{stream}_excerpt differs from full text tail")


def _validate_steps(report, scripts, report_start, report_end, errors):
    rows = report.get("step_results")
    if not isinstance(rows, list) or len(rows) != 8:
        errors.append("step_results must contain exactly eight rows")
        return {}
    by_step = {}
    previous_end = report_start
    for index, row in enumerate(rows):
        label = f"step_results[{index}]"
        if not _exact_keys(row, STEP_KEYS, label, errors):
            continue
        step = row["step"]
        if not _true_int(step) or step != index:
            errors.append(f"{label}.step must be {index}")
            continue
        by_step[step] = row
        if scripts is not None and row["script"] != scripts[step]:
            errors.append(f"{label}.script differs from committed README step")
        prefix = row["argv_prefix"]
        if not isinstance(prefix, list) or prefix not in (
                ["/bin/zsh", "-eu", "-o", "pipefail", "-c"],
                ["/bin/sh", "-eu", "-c"]):
            errors.append(f"{label}.argv_prefix is not the declared shell invocation")
        started = _utc(row["started_utc"], f"{label}.started_utc", errors)
        ended = _utc(row["ended_utc"], f"{label}.ended_utc", errors)
        if started and ended:
            if started > ended:
                errors.append(f"{label} ends before it starts")
            if report_start and started < report_start:
                errors.append(f"{label} starts before the report")
            if report_end and ended > report_end:
                errors.append(f"{label} ends after the report")
            if previous_end and started < previous_end:
                errors.append(f"{label} overlaps or precedes the prior step")
            previous_end = ended
        if isinstance(row["duration_s"], bool) or not isinstance(row["duration_s"], (int, float)) \
                or row["duration_s"] < 0:
            errors.append(f"{label}.duration_s must be non-negative")
        if row["exit_code"] != 0 or not _true_int(row["exit_code"]):
            errors.append(f"{label} did not exit zero")
        if row["spawn_error"] is not None:
            errors.append(f"{label} has a spawn error")
        if row["process_group"] != {"isolated": True, "timeout_termination": None}:
            errors.append(f"{label} lacks successful process-group isolation evidence")
        _validate_stream(row, "stdout", label, errors)
        _validate_stream(row, "stderr", label, errors)
    return by_step


def _validate_environment(report, context, errors):
    environment = report.get("environment")
    if not _exact_keys(environment, ENVIRONMENT_KEYS, "environment", errors):
        return
    if not isinstance(environment["python"], str) or not environment["python"]:
        errors.append("environment.python must be non-empty")
    if not isinstance(environment["platform"], str) or not environment["platform"]:
        errors.append("environment.platform must be non-empty")
    if environment["stdin"] != "DEVNULL":
        errors.append("environment.stdin must be DEVNULL")
    variables = environment["variables"]
    if not isinstance(variables, dict) or set(variables) != SAFE_ENVIRONMENT_KEYS \
            or not all(isinstance(key, str) and isinstance(value, str)
                       for key, value in variables.items()):
        errors.append("environment.variables is not the exact sanitized environment")
    else:
        for key, value in {
            "LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1", "NO_COLOR": "1", "TMPDIR": "/tmp",
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1", "GIT_NO_REPLACE_OBJECTS": "1",
        }.items():
            if variables[key] != value:
                errors.append(f"environment.variables.{key} differs")
        if variables["HOME"] != variables["CURL_HOME"] \
                or variables["HOME"] != variables["XDG_CONFIG_HOME"]:
            errors.append("isolated HOME/CURL_HOME/XDG_CONFIG_HOME differ")
    toolchain = environment["toolchain"]
    if not _exact_keys(toolchain, TOOLCHAIN_KEYS, "environment.toolchain", errors):
        return
    if toolchain["approved_prefixes"] != list(APPROVED_TOOL_PREFIXES):
        errors.append("toolchain approved prefixes differ")
    if toolchain["forbidden_inherited_variables"] != {} or toolchain["errors"] != [] \
            or toolchain["verified"] is not True:
        errors.append("toolchain does not record a clean verified preflight")
    if isinstance(variables, dict) and variables.get("PATH") != toolchain["sanitized_path"]:
        errors.append("sanitized PATH differs between environment and toolchain")
    selected_shell = toolchain["selected_pipeline_shell"]
    if not isinstance(selected_shell, str) or not Path(selected_shell).is_absolute():
        errors.append("toolchain selected_pipeline_shell must be absolute")
    tools = toolchain["tools"]
    if not isinstance(tools, list) or [row.get("name") for row in tools
                                      if isinstance(row, dict)] != list(EXPECTED_TOOL_NAMES):
        errors.append("toolchain tool population/order differs")
        return
    safe_dirs = toolchain["sanitized_path"].split(os.pathsep) \
        if isinstance(toolchain["sanitized_path"], str) else []
    for index, tool in enumerate(tools):
        label = f"environment.toolchain.tools[{index}]"
        if not _exact_keys(tool, TOOL_KEYS, label, errors):
            continue
        for field in ("invocation_path", "resolved_path"):
            value = tool[field]
            if not isinstance(value, str) or not Path(value).is_absolute() \
                    or not any(value.startswith(prefix) for prefix in APPROVED_TOOL_PREFIXES):
                errors.append(f"{label}.{field} is outside the approved absolute prefixes")
        if SHA256_RE.fullmatch(tool["sha256"] or "") is None:
            errors.append(f"{label}.sha256 is malformed")
        if str(Path(tool["invocation_path"]).parent) not in safe_dirs:
            errors.append(f"{label} directory is absent from sanitized PATH")
        if tool["name"] == "mkdir":
            if any(tool[field] is not None
                   for field in ("probe_argv", "probe_exit_code", "probe_output")):
                errors.append(f"{label} should have no probe")
        else:
            if not isinstance(tool["probe_argv"], list) or not tool["probe_argv"] \
                    or tool["probe_argv"][0] != tool["invocation_path"] \
                    or tool["probe_exit_code"] != 0 \
                    or not isinstance(tool["probe_output"], str):
                errors.append(f"{label} probe did not execute successfully")
        if tool["name"] == "shell" and tool["invocation_path"] != selected_shell:
            errors.append(f"{label} differs from selected_pipeline_shell")
        if context.get("output_view") == "producer" \
                and context.get("verify_runtime_tools") is True:
            try:
                if _sha256(Path(tool["resolved_path"]).read_bytes()) != tool["sha256"]:
                    errors.append(f"{label} runtime digest differs")
            except OSError as exc:
                errors.append(f"{label} runtime executable cannot be read: {exc}")


def _validate_generated(report, root, commit, context, committed, step_rows, errors):
    regenerated_by_step = context.get("regenerated_by_step", REGENERATED_BY_STEP)
    deterministic = context.get("deterministic_outputs", DETERMINISTIC)
    nondeterministic = set(context.get("nondeterministic_outputs", NONDETERMINISTIC))
    expected_order = [
        (step, path) for step, paths in regenerated_by_step.items() for path in paths
    ]
    prepared = report.get("prepared_outputs")
    regenerated = report.get("regenerated_output_checks")
    if not isinstance(prepared, list) or len(prepared) != len(expected_order):
        errors.append("prepared_outputs population differs")
        prepared = []
    if not isinstance(regenerated, list) or len(regenerated) != len(expected_order):
        errors.append("regenerated_output_checks population differs")
        regenerated = []
    observed_by_path = {}
    for index, (step, path) in enumerate(expected_order):
        baseline = committed.get(path)
        if baseline is None:
            errors.append(f"carrier generated output is absent: {path}")
            continue
        expected_digest = baseline["sha256"]
        expected_size = baseline["size_bytes"]
        if index < len(prepared):
            row = prepared[index]
            label = f"prepared_outputs[{index}]"
            if _exact_keys(row, PREPARED_KEYS, label, errors):
                if row != {"path": path, "removed_before_step": step,
                           "expected_sha256": expected_digest,
                           "expected_size_bytes": expected_size}:
                    errors.append(f"{label} differs from committed output evidence")
        if index < len(regenerated):
            row = regenerated[index]
            label = f"regenerated_output_checks[{index}]"
            if _exact_keys(row, REGENERATED_KEYS, label, errors):
                if row["path"] != path or row["step"] != step \
                        or row["expected_sha256"] != expected_digest:
                    errors.append(f"{label} identity/baseline differs")
                if row["recreated"] is not True or row["match"] is not True \
                        or SHA256_RE.fullmatch(row["observed_sha256"] or "") is None:
                    errors.append(f"{label} does not demonstrate recreation")
                if path not in nondeterministic:
                    if row["byte_match"] is not True or row["observed_sha256"] != expected_digest:
                        errors.append(f"{label} deterministic bytes differ")
                elif not isinstance(row["byte_match"], bool):
                    errors.append(f"{label}.byte_match must be boolean")
                observed_by_path[path] = row["observed_sha256"]

    checks = report.get("deterministic_output_checks")
    if not isinstance(checks, list) or len(checks) != len(deterministic):
        errors.append("deterministic_output_checks population differs")
        checks = []
    for index, (name, path) in enumerate(deterministic.items()):
        baseline = committed.get(path)
        if baseline is None:
            errors.append(f"carrier deterministic expectation is absent: {path}")
            continue
        if index >= len(checks):
            continue
        row = checks[index]
        label = f"deterministic_output_checks[{index}]"
        if not _exact_keys(row, DETERMINISTIC_KEYS, label, errors):
            continue
        expected_row = {
            "name": name, "path": path, "expected_sha256": baseline["sha256"],
            "observed_sha256": baseline["sha256"], "match": True,
        }
        if row != expected_row:
            errors.append(f"{label} differs from the committed deterministic output")
        if name == "step2_stdout" and 2 in step_rows \
                and row["observed_sha256"] != step_rows[2].get("stdout_sha256"):
            errors.append("step2 stdout digest differs from its deterministic check")
        if path in observed_by_path and row["observed_sha256"] != observed_by_path[path]:
            errors.append(f"{label} differs from regenerated output evidence")

    if context.get("output_view", "carrier") == "producer":
        for path, recorded in observed_by_path.items():
            target = Path(root, path)
            try:
                observed = _sha256(target.read_bytes())
            except OSError as exc:
                errors.append(f"producer output {path} cannot be read: {exc}")
                continue
            if observed != recorded:
                errors.append(f"producer output {path} differs from report evidence")
    elif context.get("output_view", "carrier") != "carrier":
        errors.append("context.output_view must be carrier or producer")
    return observed_by_path


def _validate_provider_evidence(report, expected, baseline_urls, observed_outputs,
                                report_start, report_end, errors):
    attempts = report.get("provider_attempts")
    if not isinstance(attempts, list) or len(attempts) != EXPECTED_PROVIDER_ATTEMPTS:
        errors.append("provider_attempts must contain exactly 65 registry pins plus optical")
        attempts = []
    attempt_map = {}
    for index, row in enumerate(attempts):
        if not isinstance(row, dict):
            errors.append(f"provider_attempts[{index}] must be an object")
            continue
        key = (row.get("source_group"), row.get("artifact"))
        if key in attempt_map:
            errors.append(f"provider_attempts duplicates source identity {key!r}")
        else:
            attempt_map[key] = (index, row)
    expected_rows = []
    for section, config in PIN_REPORTS.items():
        for identifier, digest in expected.get(section, {}).items():
            expected_rows.append((section, config["step"], identifier, digest,
                                  baseline_urls.get(section, {}).get(identifier)))
    expected_keys = {(section, identifier) for section, _, identifier, _, _ in expected_rows}
    expected_keys.add(("optical", "ROCIT campaign results.zip"))
    unknown_keys = set(attempt_map) - expected_keys
    missing_keys = expected_keys - set(attempt_map)
    if unknown_keys or missing_keys:
        errors.append(
            f"provider attempt keyed population differs: missing={sorted(missing_keys)!r}, "
            f"unknown={sorted(unknown_keys)!r}"
        )
    for section, step, identifier, digest, url in expected_rows:
        found = attempt_map.get((section, identifier))
        if found is None:
            continue
        index, row = found
        label = f"provider_attempts[{index}]"
        if not _exact_keys(row, PIN_ATTEMPT_KEYS, label, errors):
            continue
        expected_identity = (step, identifier, url, digest)
        observed_identity = (
            row["step"], row["artifact"], row["url"], row["expected_sha256"],
        )
        if observed_identity != expected_identity:
            errors.append(f"{label} identity, URL or registry digest differs ({section})")
        if row["source_group"] != section:
            errors.append(f"{label}.source_group differs ({section})")
        if row["reported_expected_sha256"] != digest or row["observed_sha256"] != digest:
            errors.append(f"{label} digest evidence differs ({section})")
        if row["failure_class"] != "success" or row["reachability_stage"] != "bytes_received" \
                or row["access_class_conclusion"] != "not_established" \
                or row["http_status"] != 200 \
                or not _true_int(row["bytes_received"]) or row["bytes_received"] <= 0 \
                or row["content_validation_result"] != "content_validated":
            errors.append(f"{label} does not record a validated successful retrieval")
        retrieved = _utc(row["retrieved_utc"], f"{label}.retrieved_utc", errors)
        if retrieved and report_start and retrieved < report_start:
            errors.append(f"{label} predates the C9 run")
        if retrieved and report_end and retrieved > report_end:
            errors.append(f"{label} postdates the C9 run")

    optical = report.get("optical_archive")
    if not _exact_keys(optical, OPTICAL_KEYS, "optical_archive", errors):
        optical = {}
    optical_found = attempt_map.get(("optical", "ROCIT campaign results.zip"))
    if optical_found is not None:
        optical_index, row = optical_found
        label = f"provider_attempts[{optical_index}]"
        if _exact_keys(row, OPTICAL_ATTEMPT_KEYS, label, errors):
            if row.get("source_group") != "optical" or row.get("step") != 3 \
                    or row.get("artifact") != "ROCIT campaign results.zip" \
                    or row.get("failure_class") != "success" \
                    or row.get("reachability_stage") != "bytes_received" \
                    or row.get("access_class_conclusion") != "not_established" \
                    or row.get("access_evidence") != "anonymous_request_succeeded" \
                    or row.get("http_status") != 200 \
                    or row.get("content_validation_result") != "archive_extracted" \
                    or row.get("expected_md5") != EXPECTED_OPTICAL_MD5 \
                    or row.get("observed_md5") != EXPECTED_OPTICAL_MD5 \
                    or row.get("expected_sha256") is not None \
                    or SHA256_RE.fullmatch(row.get("observed_sha256") or "") is None \
                    or not _true_int(row.get("bytes_received")) or row["bytes_received"] <= 0:
                errors.append(f"{label} does not record the exact successful optical attempt")
            if optical and (
                optical.get("http_status") != row.get("http_status")
                or optical.get("effective_url") != row.get("url")
                or optical.get("content_type") != row.get("content_type")
                or optical.get("size_bytes") != row.get("bytes_received")
                or optical.get("expected_md5") != row.get("expected_md5")
                or optical.get("md5") != row.get("observed_md5")
                or optical.get("sha256") != row.get("observed_sha256")
            ):
                errors.append("optical attempt and archive evidence differ")
    if optical:
        if optical.get("http_status") != 200 \
                or not isinstance(optical.get("effective_url"), str) \
                or not optical["effective_url"].startswith("https://") \
                or not _true_int(optical.get("size_bytes")) or optical["size_bytes"] <= 0 \
                or optical.get("curl_size_download") != optical.get("size_bytes") \
                or optical.get("expected_md5") != EXPECTED_OPTICAL_MD5 \
                or optical.get("md5") != EXPECTED_OPTICAL_MD5 \
                or optical.get("md5_match") is not True \
                or SHA256_RE.fullmatch(optical.get("sha256") or "") is None \
                or optical.get("authentication_material_supplied") is not False \
                or optical.get("proxy_environment_supplied") is not False:
            errors.append("optical_archive is not an exact successful anonymous retrieval")

    records = report.get("provider_report_evidence")
    if not isinstance(records, list) or len(records) != len(PIN_REPORTS):
        errors.append("provider_report_evidence must contain exactly four reports")
        records = []
    for index, (section, config) in enumerate(PIN_REPORTS.items()):
        if index >= len(records):
            break
        row = records[index]
        label = f"provider_report_evidence[{index}]"
        if not _exact_keys(row, PROVIDER_REPORT_KEYS, label, errors):
            continue
        expected_row = {
            "section": section, "promoted": True, "fresh": True, "path": config["path"],
            "sha256": observed_outputs.get(config["path"]),
            "n_expected": config["count"], "n_observed": config["count"], "errors": [],
        }
        if row != expected_row:
            errors.append(f"{label} differs from exact promoted-report evidence")

    if report.get("expected_provider_attempts") != EXPECTED_PROVIDER_ATTEMPTS \
            or not _true_int(report.get("expected_provider_attempts")) \
            or report.get("n_provider_attempts_recorded") != EXPECTED_PROVIDER_ATTEMPTS \
            or not _true_int(report.get("n_provider_attempts_recorded")) \
            or report.get("n_provider_attempts_successful") != EXPECTED_PROVIDER_ATTEMPTS \
            or not _true_int(report.get("n_provider_attempts_successful")) \
            or report.get("provider_population_verified") is not True \
            or report.get("provider_evidence_errors") != []:
        errors.append("provider population counters/status do not prove 66/66")


def _validate_optical_command(step_rows, optical, errors):
    if 3 not in step_rows or not isinstance(optical, dict):
        return
    combined = step_rows[3].get("stdout_text", "") + "\n" + step_rows[3].get("stderr_text", "")
    matches = re.findall(
        r"(?m)^FTRO_CURL_HTTP (\d{3}) (\S+) (\S*) ([0-9]+(?:\.[0-9]+)?)$", combined,
    )
    if len(matches) != 1:
        errors.append("step 3 does not contain exactly one structured curl record")
        return
    status, url, content_type, size = matches[0]
    if int(status) != optical.get("http_status") or url != optical.get("effective_url") \
            or (content_type or None) != optical.get("content_type") \
            or int(float(size)) != optical.get("curl_size_download"):
        errors.append("step 3 curl record differs from optical_archive")
    if EXPECTED_OPTICAL_MD5 not in combined:
        errors.append("step 3 command output does not contain the verified optical MD5")


def _validate_cleanup_and_changes(report, observed_outputs, context, errors):
    cleanup = report.get("cleanup")
    if _exact_keys(cleanup, CLEANUP_KEYS, "cleanup", errors):
        if cleanup != {
            "attempted": True,
            "removed": ["data/", "ROCIT campaign results.zip"],
            "errors": [],
            "provider_bytes_retained": False,
        }:
            errors.append("cleanup does not prove removal of both provider-byte locations")
    changes = report.get("tracked_change_evidence")
    if not _exact_keys(changes, TRACKED_CHANGE_KEYS, "tracked_change_evidence", errors):
        return
    changed = changes["changed_paths"]
    if not isinstance(changed, list) or changed != sorted(set(changed)):
        errors.append("tracked changed_paths must be a sorted unique list")
        changed = []
    allowed_outputs = set(context.get("allowed_tracked_outputs", ALLOWED_TRACKED_OUTPUTS))
    pin_paths = {row["path"] for row in context.get("pin_reports", PIN_REPORTS).values()}
    if changes["allowed_paths"] != sorted(allowed_outputs) \
            or not set(changed).issubset(allowed_outputs) \
            or not pin_paths.issubset(changed) \
            or changes["unexpected_paths"] != [] \
            or changes["pin_reports_not_changed"] != [] \
            or changes["untracked_paths"] != [] \
            or changes["verified"] is not True:
        errors.append("tracked-change evidence is not the exact permitted fresh-output set")
    if changes["changed_paths_sha256"] != _sha256(
            json.dumps(changed, separators=(",", ":")).encode()):
        errors.append("tracked changed-path digest differs")
    if context.get("output_view", "carrier") == "producer":
        root = Path(context["_root"])
        try:
            actual = sorted(_git(
                root, "diff", "--name-only", "HEAD", text=True,
                git_command=context.get("_git_command"),
            ).splitlines())
        except C9ContractError:
            actual = None
        if actual != changed:
            errors.append("producer worktree changed paths differ from report evidence")
        for path in changed:
            if path in observed_outputs:
                try:
                    digest = _sha256(Path(root, path).read_bytes())
                except OSError as exc:
                    errors.append(f"producer changed output {path} cannot be read: {exc}")
                    continue
                if digest != observed_outputs[path]:
                    errors.append(f"producer changed output {path} differs from report evidence")


def _validate_provisional(report, context, errors):
    provisional = report.get("provisional_witness")
    if not _exact_keys(provisional, PROVISIONAL_KEYS, "provisional_witness", errors):
        return
    report_path = context.get("report_path")
    if not isinstance(provisional["path"], str) or not Path(provisional["path"]).is_absolute() \
            or SHA256_RE.fullmatch(provisional["sha256"] or "") is None \
            or provisional["retained_after_successful_finalization"] is not False:
        errors.append("provisional witness evidence is malformed")
    if context.get("output_view") == "producer" and report_path is not None \
            and Path(provisional["path"]) != Path(str(Path(report_path).resolve()) + ".provisional"):
        errors.append("provisional witness path differs from final report path")


def validate_success_report(report, root, context):
    """Return every independently checkable contract error for ``report``.

    ``root`` must be a checkout containing ``context['commit']``.  Dirty generated
    outputs are allowed.  Set ``context['output_view']`` to ``"producer"`` to bind those
    worktree outputs too; the default ``"carrier"`` validates a published report from a
    clean clone using only immutable carrier bytes and evidence embedded in the report.
    """
    errors = []
    root = Path(root).resolve()
    context = dict(context)
    context["_root"] = str(root)
    context["_git_command"] = context.get("git_command") or _trusted_git()
    commit = context.get("commit")
    tree = context.get("tree")
    if OID_RE.fullmatch(commit or "") is None or OID_RE.fullmatch(tree or "") is None:
        return ["carrier context requires lowercase 40-hex commit and tree IDs"]
    try:
        actual_tree = _git(
            root, "rev-parse", f"{commit}^{{tree}}", text=True,
            git_command=context["_git_command"],
        ).strip()
        head = _git(
            root, "rev-parse", "HEAD", text=True,
            git_command=context["_git_command"],
        ).strip()
    except C9ContractError as exc:
        return [str(exc)]
    if actual_tree != tree:
        errors.append("carrier context tree differs from commit")
    if head != commit:
        errors.append("validator checkout HEAD differs from expected carrier commit")

    if not _exact_keys(report, REPORT_KEYS, "C9 report", errors):
        # Continue only through fields which can safely provide useful population errors.
        if not isinstance(report, dict):
            return errors
    if report.get("document") != "FTRO Phase-0 C9 live-pipeline report" \
            or report.get("version") != "1.2.0":
        errors.append("C9 report document/version differs")
    if not isinstance(report.get("run_id"), str) or not report["run_id"].strip():
        errors.append("C9 run_id must be non-empty")
    if report.get("status") != "pass" or report.get("qualifying") is not True \
            or report.get("first_failure") is not None:
        errors.append("C9 report is not an unambiguous qualifying PASS")
    report_start = _utc(report.get("started_utc"), "started_utc", errors)
    report_end = _utc(report.get("ended_utc"), "ended_utc", errors)
    if report_start and report_end and report_start > report_end:
        errors.append("C9 report ends before it starts")
    if context.get("before_utc") is not None:
        before = _utc(context["before_utc"], "context.before_utc", errors)
        if report_end and before and report_end > before:
            errors.append("C9 report does not precede its consumer")

    subject = report.get("subject")
    if _exact_keys(subject, SUBJECT_KEYS, "subject", errors):
        required_ancestor = context.get("required_ancestor", subject["required_ancestor"])
        expected_subject = {
            "commit": commit, "tree": tree, "required_ancestor": required_ancestor,
            "clean": True, "detached_head": True,
        }
        for field, expected in expected_subject.items():
            if subject[field] != expected:
                errors.append(f"subject.{field} differs from carrier context")
        if not isinstance(subject["checkout_realpath"], str) \
                or not Path(subject["checkout_realpath"]).is_absolute():
            errors.append("subject.checkout_realpath must be absolute")
        try:
            _git(root, "merge-base", "--is-ancestor", required_ancestor, commit,
                 git_command=context["_git_command"])
            ancestor_ok = True
        except C9ContractError:
            ancestor_ok = False
        if not ancestor_ok:
            errors.append("required ancestor is not an ancestor of the carrier")

    try:
        readme = _carrier_bytes(root, commit, "README.md", context["_git_command"])
        contract_body = _carrier_bytes(
            root, commit, EXPECTED_CONTRACT_PATH, context["_git_command"],
        )
        runner_body = _carrier_bytes(
            root, commit, EXPECTED_RUNNER_PATH, context["_git_command"],
        )
        carrier_rows = _carrier_rows(root, commit, context["_git_command"])
    except C9ContractError as exc:
        errors.append(str(exc))
        return errors
    committed = {row["path"]: row for row in carrier_rows}
    block, scripts = _extract_pipeline(readme, errors)

    contract = report.get("contract")
    if _exact_keys(contract, CONTRACT_KEYS, "contract", errors):
        expected_contract = {
            "id": context.get("contract_id", "FTRO-ACC-001"),
            "version": context.get("contract_version", "1.3.0"),
            "clause": "C9", "path": EXPECTED_CONTRACT_PATH,
            "sha256": _sha256(contract_body),
        }
        if contract != expected_contract:
            errors.append("acceptance-contract binding differs from the carrier")
    pipeline = report.get("pipeline")
    if _exact_keys(pipeline, PIPELINE_KEYS, "pipeline", errors):
        if pipeline != {
            "path": "README.md", "sha256": _sha256(readme),
            "command_block_sha256": _sha256(block.encode()) if block is not None else None,
            "steps_expected": list(range(8)), "steps_completed": list(range(8)),
        }:
            errors.append("README command-block or eight-step binding differs")
    runner = report.get("runner")
    if _exact_keys(runner, RUNNER_KEYS, "runner", errors):
        if runner != {"path": EXPECTED_RUNNER_PATH, "sha256": _sha256(runner_body)}:
            errors.append("C9 runner binding differs from the carrier")

    if report.get("bound_inputs") != carrier_rows \
            or report.get("bound_input_fingerprint_sha256") != _sha256(_canonical(carrier_rows)):
        errors.append("complete carrier input population/fingerprint differs")
    if report.get("manual_interventions") != 0 \
            or not _true_int(report.get("manual_interventions")) \
            or report.get("manual_interventions_basis") != "all child stdin was DEVNULL":
        errors.append("manual-intervention evidence differs")
    if report.get("route_substitutions") != 0 \
            or not _true_int(report.get("route_substitutions")) \
            or report.get("route_substitutions_basis") != (
                "proxy/Python injection variables absent; README URLs unchanged; "
                "all command paths resolved under approved prefixes"
            ):
        errors.append("route-substitution evidence differs")

    _validate_environment(report, context, errors)
    steps = _validate_steps(report, scripts, report_start, report_end, errors)
    observed = _validate_generated(
        report, root, commit, context, committed, steps, errors,
    )
    population = _carrier_expectations(
        root, commit, errors, context["_git_command"],
    )
    if population is not None:
        expected, baseline_urls = population
        _validate_provider_evidence(
            report, expected, baseline_urls, observed, report_start, report_end, errors,
        )
    _validate_optical_command(steps, report.get("optical_archive"), errors)
    _validate_cleanup_and_changes(report, observed, context, errors)

    _validate_provisional(report, context, errors)
    return errors


def assert_success_report(report, root, context):
    """Validate and return compact C9 evidence, or raise ``C9ContractError``."""
    errors = validate_success_report(report, root, context)
    if errors:
        raise C9ContractError("C9 success report invalid: " + "; ".join(errors))
    raw = _canonical(report)
    return {
        "run_id": report["run_id"],
        "ended_utc": report["ended_utc"],
        "subject_commit": report["subject"]["commit"],
        "subject_tree": report["subject"]["tree"],
        "bound_input_fingerprint_sha256": report["bound_input_fingerprint_sha256"],
        "command_block_sha256": report["pipeline"]["command_block_sha256"],
        "report_content_sha256": _sha256(raw),
    }
