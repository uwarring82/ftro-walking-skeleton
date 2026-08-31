#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute the frozen WP2A Step-2 v1.3 input-evidence trial.

This runner has no acquisition path.  It authenticates all four pre-existing
outer artifacts before any decoder/extractor starts, executes two independent
routes per target, compares their captured bytes directly, and hands a complete
candidate report to the fail-closed atomic publisher.

The underscore-prefixed commands are isolated child-process entry points used
by the registered argv.  They write provider-derived bytes only to stdout; the
parent captures them in memory.  Merely importing this module reads no provider
payload.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from check_step2_v1_3 import (  # noqa: E402
    CheckError,
    MANIFEST_REL,
    atomic_create,
    derive_run_outcome,
    derive_target_outcome,
    digest_bytes,
    digest_file,
    git_contains,
    git_bytes,
    git_text,
    load_json,
    publish_candidate,
    schema_registration,
    validate_registration_manifest,
    validate_report,
)


TIMEOUT_SECONDS = 180
RUNNER_REL = "phase2/wp2a/run_step2_v1_3.py"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def git_run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    return subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), *arguments],
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )


def clean_published_subject() -> dict[str, Any]:
    status = git_run("status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        raise CheckError("cannot inspect source worktree: " + status.stderr.decode(errors="replace")[-500:])
    if status.stdout:
        raise CheckError("Step 2 requires a clean worktree; registration/result publication must be committed first")
    commit = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    upstream = git_run("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if upstream.returncode != 0:
        raise CheckError("Step 2 requires a configured published upstream")
    upstream_name = upstream.stdout.decode("utf-8", errors="strict").strip()
    if not git_contains(commit, upstream_name):
        raise CheckError(
            f"subject {commit} is not contained in a remote-tracking published ref: "
            f"{upstream_name}"
        )
    return {
        "commit": commit,
        "tree": tree,
        "worktree_clean": True,
        "published": True,
        "published_ref": upstream_name,
    }


def require_anonymous_fd_transport() -> None:
    """Prove the registered byte transport works before any provider pathname opens."""
    if os.name != "posix" or not Path("/dev/fd").is_dir():
        raise CheckError("Step 2 requires POSIX /dev/fd inherited-descriptor transport")
    sentinel = b"FTRO_STEP2_AUTHENTICATED_FD_PROBE\n"
    try:
        with tempfile.TemporaryFile(mode="w+b") as captured:
            captured.write(sentinel)
            captured.flush()
            captured.seek(0)
            descriptor = captured.fileno()
            handle = f"/dev/fd/{descriptor}"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    "from pathlib import Path; import sys; sys.stdout.buffer.write(Path(sys.argv[1]).read_bytes())",
                    handle,
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
                pass_fds=(descriptor,),
            )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise CheckError(
            f"anonymous descriptor transport preflight failed: {type(exc).__name__}"
        ) from exc
    if completed.returncode != 0 or completed.stdout != sentinel:
        raise CheckError(
            "anonymous descriptor transport preflight did not reproduce its synthetic sentinel"
        )


def authenticated_manifest(subject: dict[str, Any]) -> tuple[dict[str, Any], str]:
    path = ROOT / MANIFEST_REL
    try:
        local_body = path.read_bytes()
    except OSError as exc:
        raise CheckError(f"registration manifest unreadable: {exc}") from exc
    committed_body = git_bytes(subject["commit"], MANIFEST_REL)
    if local_body != committed_body:
        raise CheckError("local registration manifest differs from the clean published subject")
    errors = validate_registration_manifest(committed_body, subject["commit"])
    if errors:
        raise CheckError("registration manifest invalid: " + "; ".join(errors))
    return json.loads(committed_body), digest_bytes(committed_body)


def capture_authenticated_input(expected: dict[str, Any]) -> tuple[dict[str, Any], bytes | None]:
    path = ROOT / expected["path"]
    observed_sha = None
    observed_size = None
    body = None
    if not path.exists():
        outcome = "missing"
    else:
        try:
            # One open supplies both values.  A separate stat-plus-hash could describe
            # different file states even within a single authentication pass.
            body = path.read_bytes()
            observed_size = len(body)
            observed_sha = digest_bytes(body)
        except OSError:
            outcome = "unreadable"
        else:
            if observed_sha != expected["expected_outer_sha256"]:
                outcome = "digest_mismatch"
            elif observed_size != expected["expected_outer_size_bytes"]:
                outcome = "size_mismatch"
            else:
                outcome = "authenticated"
    row = {
        "input_id": expected["input_id"],
        "path": expected["path"],
        "acquisition_mode": expected["acquisition_mode"],
        "registered_route": expected["registered_route"],
        "expected_outer_sha256": expected["expected_outer_sha256"],
        "expected_outer_size_bytes": expected["expected_outer_size_bytes"],
        "observed_outer_sha256": observed_sha,
        "observed_outer_size_bytes": observed_size,
        "post_observed_outer_sha256": None,
        "post_observed_outer_size_bytes": None,
        "postflight_path_matches_captured_snapshot": None,
        "outcome": outcome,
    }
    return row, body if outcome == "authenticated" else None


def authenticate_input(expected: dict[str, Any]) -> dict[str, Any]:
    """Authenticate one current path state without retaining its bytes (postflight)."""
    return capture_authenticated_input(expected)[0]


def add_post_authentication(
    row: dict[str, Any], expected: dict[str, Any]
) -> dict[str, Any]:
    """Re-open an authenticated input after consumption and record TOCTOU evidence."""
    post = authenticate_input(expected)
    row["post_observed_outer_sha256"] = post["observed_outer_sha256"]
    row["post_observed_outer_size_bytes"] = post["observed_outer_size_bytes"]
    if row["outcome"] != "authenticated":
        row["postflight_path_matches_captured_snapshot"] = None
    else:
        row["postflight_path_matches_captured_snapshot"] = (
            post["outcome"] == "authenticated"
            and post["observed_outer_sha256"] == row["observed_outer_sha256"]
            and post["observed_outer_size_bytes"] == row["observed_outer_size_bytes"]
        )
    return row


def executable_path(command: str) -> str | None:
    if command == "python":
        candidate = Path(sys.executable).resolve()
        return str(candidate) if candidate.is_file() else None
    found = shutil.which(command)
    if found is None:
        return None
    candidate = Path(found).resolve()
    return str(candidate) if candidate.is_file() else None


def implementation_digest(method_id: str) -> str | None:
    if method_id == "ftro_unixz":
        return digest_file(ROOT / "src/ftro/unixz.py")
    if method_id == "python_zipfile":
        module_path = getattr(zipfile, "__file__", None)
        if module_path and Path(module_path).is_file():
            return digest_file(Path(module_path))
    return None


def method_metadata(method_id: str, contract: dict[str, Any]) -> dict[str, Any]:
    command_name = "python" if method_id in {"ftro_unixz", "python_zipfile"} else (
        "gzip" if method_id == "system_gzip" else "unzip"
    )
    resolved = executable_path(command_name)
    executable = resolved or command_name
    version_tail = contract["version_argv_template"][1:]
    version_argv = [executable, *version_tail]
    version_exit = None
    version_output = ""
    available = resolved is not None
    executable_sha = None
    if available:
        try:
            executable_sha = digest_file(Path(resolved))
            completed = subprocess.run(
                version_argv,
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            version_exit = completed.returncode
            version_output = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            available = False
            executable_sha = None
            version_exit = None
            version_output = ""
    return {
        "method_id": method_id,
        "implementation": contract["implementation"],
        "implementation_sha256": implementation_digest(method_id),
        "executable": executable,
        "executable_sha256": executable_sha,
        "tool_available": available,
        "version_argv": version_argv,
        "version_exit_code": version_exit,
        "version_output": version_output,
    }


def method_argv(method_id: str, executable: str, input_handle: str, member: str | None) -> list[str]:
    if method_id == "ftro_unixz":
        return [executable, "-I", RUNNER_REL, "_decode-unixz", "--input", input_handle]
    if method_id == "system_gzip":
        return [executable, "-dc", input_handle]
    if method_id == "python_zipfile":
        return [
            executable, "-I", RUNNER_REL, "_extract-zipfile", "--input", input_handle,
            "--member", member or "",
        ]
    if method_id == "system_unzip":
        return [executable, "-p", input_handle, member or ""]
    raise CheckError(f"unknown method {method_id}")


def unexecuted_method(
    metadata: dict[str, Any], member: str | None,
    input_sha256: str | None, input_size_bytes: int | None,
) -> tuple[dict[str, Any], None]:
    row = copy.deepcopy(metadata)
    row.update({
        "input_handle": None,
        "input_binding_sha256": input_sha256,
        "input_binding_size_bytes": input_size_bytes,
        "argv": method_argv(row["method_id"], row["executable"], "<not-opened>", member),
        "non_execution_reason": None,
        "ran": False,
        "exit_code": None,
        "started_utc": None,
        "ended_utc": None,
        "stdout_sha256": None,
        "stdout_size_bytes": None,
        "stderr_sha256": None,
        "stderr_size_bytes": None,
    })
    return row, None


def execute_method(
    metadata: dict[str, Any], input_body: bytes | None, member: str | None, *, permitted: bool
) -> tuple[dict[str, Any], bytes | None]:
    input_sha = digest_bytes(input_body) if input_body is not None else None
    input_size = len(input_body) if input_body is not None else None
    row, _ = unexecuted_method(metadata, member, input_sha, input_size)
    if not permitted:
        row["non_execution_reason"] = "global_input_preflight_failed"
        return row, None
    if input_body is None:
        row["non_execution_reason"] = "authenticated_input_snapshot_unavailable"
        return row, None
    if metadata["tool_available"] is not True:
        row["non_execution_reason"] = "tool_unavailable"
        return row, None
    # Both routes consume an anonymous seekable file populated from the exact byte string
    # hashed at preflight.  Provider pathnames are never reopened by a decoder, eliminating
    # change-consume-restore races between authentication and use.
    try:
        with tempfile.TemporaryFile(mode="w+b") as captured:
            captured.write(input_body)
            captured.flush()
            captured.seek(0)
            input_handle = f"/dev/fd/{captured.fileno()}"
            row["input_handle"] = input_handle
            row["argv"] = method_argv(row["method_id"], row["executable"], input_handle, member)
            started = utc_now()
            completed = subprocess.run(
                row["argv"],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=TIMEOUT_SECONDS,
                check=False,
                pass_fds=(captured.fileno(),),
            )
            output, stderr = completed.stdout, completed.stderr
            exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or b""
        stderr = (exc.stderr or b"") + b"\nFTRO_STEP2_TIMEOUT\n"
        exit_code = 124
    except (OSError, ValueError) as exc:
        row["input_handle"] = None
        row["argv"] = method_argv(
            row["method_id"], row["executable"], "<not-opened>", member
        )
        row["non_execution_reason"] = f"snapshot_or_method_start_failed:{type(exc).__name__}"
        return row, None
    ended = utc_now()
    row.update({
        "ran": True,
        "exit_code": exit_code,
        "started_utc": started,
        "ended_utc": ended,
        "stdout_sha256": digest_bytes(output),
        "stdout_size_bytes": len(output),
        "stderr_sha256": digest_bytes(stderr),
        "stderr_size_bytes": len(stderr),
    })
    return row, output


def target_result(
    expected: dict[str, Any], input_body: bytes | None,
    metadata: dict[str, dict[str, Any]], *, permitted: bool
) -> dict[str, Any]:
    member = expected.get("member_selector")
    method_a, bytes_a = execute_method(
        metadata[expected["method_a"]], input_body, member, permitted=permitted
    )
    method_b, bytes_b = execute_method(
        metadata[expected["method_b"]], input_body, member, permitted=permitted
    )
    both_successful = (
        method_a["ran"] is True and method_a["exit_code"] == 0 and method_a["stdout_size_bytes"] > 0
        and method_b["ran"] is True and method_b["exit_code"] == 0 and method_b["stdout_size_bytes"] > 0
    )
    row = {
        "target_id": expected["target_id"],
        "input_id": expected["input_id"],
        "member_selector": member,
        "expected_sha256": expected["expected_sha256"],
        "expected_size_bytes": expected["expected_size_bytes"],
        "expected_source": expected["expected_source"],
        "method_a": method_a,
        "method_b": method_b,
        "byte_comparison": "direct_byte_equality" if both_successful else "not_performed",
        "bytes_equal": bytes_a == bytes_b if both_successful else None,
        "observed_sha256": None,
        "observed_size_bytes": None,
        "matches_expected": None,
        "outcome": "not_executed",
    }
    outcome, observed_sha, observed_size, matches = derive_target_outcome(row)
    row.update({
        "observed_sha256": observed_sha,
        "observed_size_bytes": observed_size,
        "matches_expected": matches,
        "outcome": outcome,
    })
    return row


def build_report() -> dict[str, Any]:
    started = utc_now()
    _, registration = schema_registration()
    official = ROOT / registration["report_output_path"]
    if official.exists():
        raise CheckError(f"refusing to execute because immutable official report already exists: {official}")
    subject = clean_published_subject()
    _, manifest_sha = authenticated_manifest(subject)
    require_anonymous_fd_transport()

    # This complete population is computed before any decoder/extractor starts.
    captured_inputs = [
        capture_authenticated_input(row)
        for row in registration["input_policy"]["population"]
    ]
    input_rows = [row for row, _ in captured_inputs]
    input_bodies = {
        row["input_id"]: body for row, body in captured_inputs
    }
    preflight_ok = all(row["outcome"] == "authenticated" for row in input_rows)

    method_metadata_by_id = {
        method_id: method_metadata(method_id, contract)
        for method_id, contract in registration["method_contracts"].items()
    }
    targets = [
        target_result(
            expected,
            input_bodies[expected["input_id"]],
            method_metadata_by_id,
            permitted=preflight_ok,
        )
        for expected in registration["target_population"]
    ]
    input_rows = [
        add_post_authentication(row, expected)
        for row, expected in zip(input_rows, registration["input_policy"]["population"])
    ]
    outcomes = [row["outcome"] for row in targets]
    n_inputs_changed = sum(
        row["postflight_path_matches_captured_snapshot"] is False for row in input_rows
    )
    report = {
        "document": "FTRO WP2A Step-2 input-evidence report",
        "schema_version": "1.3.0",
        "run_id": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ-") + subject["commit"][:12],
        "subject": subject,
        "registration_manifest": {"path": MANIFEST_REL, "sha256": manifest_sha},
        "started_utc": started,
        "ended_utc": utc_now(),
        "input_authentication": input_rows,
        "targets": targets,
        "counters": {
            "n_targets": len(targets),
            "n_supports": outcomes.count("supports"),
            "n_contradicts": outcomes.count("contradicts"),
            "n_evidence_assurance_failed": outcomes.count("evidence_assurance_failed"),
            "n_not_executed": outcomes.count("not_executed"),
            "n_inputs_changed_during_run": n_inputs_changed,
        },
        "overall_outcome": derive_run_outcome(outcomes, n_inputs_changed=n_inputs_changed),
        "output_path": registration["report_output_path"],
    }
    return report


def run_and_publish() -> int:
    try:
        report = build_report()
        errors = validate_report(report)
        body = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        reports_dir = ROOT / "phase2/wp2a/reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix="step2-v1.3.", suffix=".candidate", dir=reports_dir)
        candidate = Path(temporary)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            destination, publication_errors = publish_candidate(
                candidate, ROOT / "phase2/wp2a/reports/step2-input-evidence-v1.3.json"
            )
        finally:
            candidate.unlink(missing_ok=True)
    except (CheckError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL WP2A Step 2 v1.3: {exc}", file=sys.stderr)
        return 1
    all_errors = [*errors, *publication_errors]
    if all_errors:
        print(f"REJECTED WP2A Step 2 v1.3 at {destination}: " + "; ".join(all_errors), file=sys.stderr)
        return 1
    if report["overall_outcome"] != "step2_supports":
        print(f"NON-SUPPORTING WP2A Step 2 v1.3 preserved at {destination}", file=sys.stderr)
        return 1
    print(f"WP2A Step 2 v1.3: SUPPORTS; immutable report {destination}")
    return 0


def decode_unixz(input_path: str) -> int:
    module_path = ROOT / "src/ftro/unixz.py"
    spec = importlib.util.spec_from_file_location("ftro_step2_unixz", module_path)
    if spec is None or spec.loader is None:
        print("cannot load src/ftro/unixz.py", file=sys.stderr)
        return 2
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        body = (ROOT / input_path).read_bytes()
        decoded = module.decompress(body)
    except Exception as exc:  # Child boundary: convert provider/decoder errors to evidence exit.
        print(f"unixz decode failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(decoded)
    return 0


def extract_zipfile(input_path: str, member: str) -> int:
    try:
        with zipfile.ZipFile(ROOT / input_path) as archive:
            matches = [info for info in archive.infolist() if info.filename == member]
            if len(matches) != 1:
                print(f"exact-one member precondition failed: {member!r} occurred {len(matches)} times", file=sys.stderr)
                return 2
            body = archive.read(matches[0])
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"zipfile extraction failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(body)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run")
    check = subparsers.add_parser("check")
    check.add_argument("report", nargs="?", default="phase2/wp2a/reports/step2-input-evidence-v1.3.json")
    decode = subparsers.add_parser("_decode-unixz")
    decode.add_argument("--input", required=True)
    extract = subparsers.add_parser("_extract-zipfile")
    extract.add_argument("--input", required=True)
    extract.add_argument("--member", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        return run_and_publish()
    if args.command == "check":
        try:
            report = load_json(ROOT / args.report if not Path(args.report).is_absolute() else Path(args.report))
            errors = validate_report(report)
        except CheckError as exc:
            errors = [str(exc)]
        if errors:
            print("FAIL WP2A Step-2 v1.3 report: " + "; ".join(errors), file=sys.stderr)
            return 1
        print("WP2A Step-2 v1.3 report: PASS")
        return 0
    if args.command == "_decode-unixz":
        return decode_unixz(args.input)
    return extract_zipfile(args.input, args.member)


if __name__ == "__main__":
    raise SystemExit(main())
