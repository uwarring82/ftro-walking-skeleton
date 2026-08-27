#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the documented Phase-0 pipeline once and publish a structured C9 witness.

The command block is extracted from README.md rather than copied into this program.  It
is executed step-by-step, in order, with fail-fast semantics.  Provider reachability is
reported separately from access classification so a transport failure cannot silently
become an assertion that a source is restricted or unavailable.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time

# The script's clean-checkout preflight enumerates ignored residue.  Disable bytecode
# before importing the adjacent contract module so starting C9 cannot create the very
# __pycache__ that would make source_state() reject its own checkout.
sys.dont_write_bytecode = True

AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))
import c9_contract  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
EXPECTED_OPTICAL_MD5 = "4ae290f559c90b462991286c933a1147"
OPTICAL_ZIP = ROOT / "ROCIT campaign results.zip"
PIPELINE_SHELL = "/bin/zsh" if Path("/bin/zsh").exists() else "/bin/sh"
STEP_TIMEOUT_S = 3600
TERMINATION_GRACE_S = 5
DETERMINISTIC = {
    "step2_stdout": "phase0/evidence/VA-GPS2UTC-001.json",
    "step3_optical_summary": "phase0/reports/optical-inventory-summary.json",
    "step5_intersection": "phase0/reports/four-domain-intersection.json",
    "step6_deficiencies": "ledgers/deficiency-log.md",
    "step6_validity": "phase0/optical-validity-intervals.md",
}
REQUIRED_ANCESTOR = "a806bbaa573d28f1460d18110f7974189ca19213"
PIN_REPORTS = {
    "evidence_repos": {
        "step": 1,
        "path": "phase0/reports/evidence-repo-pins.json",
        "identifier": "key",
    },
    "igs": {
        "step": 4,
        "path": "phase0/reports/igs-artifact-pins.json",
        "identifier": "name",
    },
    "ppta": {
        "step": 4,
        "path": "phase0/reports/ppta-artifact-pins.json",
        "identifier": "name",
    },
    "vgosdb": {
        "step": 4,
        "path": "phase0/reports/vlbi-vgosdb-pin.json",
        "identifier": "url_basename",
    },
}
PIN_REPORT_PATHS = {row["path"] for row in PIN_REPORTS.values()}
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
# Pin reports carry live retrieval timestamps and HTTP metadata.  The optical summary
# does not: it is a deterministic transform of the digest-pinned archive and must match
# byte-for-byte.  Treating it as a retrieval report made most of its scientific fields an
# unchecked existence-only projection.
NONDETERMINISTIC_REGENERATED = PIN_REPORT_PATHS
ALLOWED_TRACKED_OUTPUTS = PIN_REPORT_PATHS | {
    "phase0/reports/optical-inventory-summary.json",
    "phase0/reports/four-domain-intersection.json",
    "ledgers/deficiency-log.md",
    "phase0/optical-validity-intervals.md",
}
REQUIRED_TOOLS = {
    "python3": ["--version"],
    "curl": ["--version"],
    "md5": ["-s", "FTRO_C9_TOOL_PROBE"],
    "unzip": ["-v"],
    "git": ["--version"],
    "mkdir": None,
}
APPROVED_TOOL_PREFIXES = (
    "/bin/", "/sbin/", "/usr/bin/", "/usr/sbin/", "/usr/local/bin/",
    "/opt/homebrew/bin/", "/opt/homebrew/Cellar/", "/Library/Developer/",
)
FORBIDDEN_ENVIRONMENT = {
    "PYTHONPATH", "PYTHONHOME", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "NO_PROXY", "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL",
    "GIT_REPLACE_REF_BASE",
}
GIT_COMMAND = None


class C9Error(Exception):
    pass


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest_bytes(body, algorithm="sha256"):
    return hashlib.new(algorithm, body).hexdigest()


def digest_file(path, algorithm="sha256"):
    with open(path, "rb") as handle:
        digest = hashlib.new(algorithm)
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args, ok=(0,)):
    command = GIT_COMMAND or c9_contract._trusted_git()
    environment = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }
    result = subprocess.run(
        [command, "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-c", "core.hooksPath=/dev/null", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=120, env=environment,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode not in ok:
        raise C9Error(f"git {' '.join(args)} failed: {result.stderr[-1000:]}")
    return result


def extract_pipeline(text):
    heading = text.find("## Reproducing Phase 0")
    if heading < 0:
        raise C9Error("README reproduction heading absent")
    start = text.find("```bash\n", heading)
    end = text.find("\n```", start + 8)
    if start < 0 or end < 0:
        raise C9Error("README reproduction command block absent")
    block = text[start + len("```bash\n"):end]
    matches = list(re.finditer(r"(?m)^# ([0-7])\. .+$", block))
    if [int(match.group(1)) for match in matches] != list(range(8)):
        raise C9Error("README steps are not exactly 0 through 7")
    steps = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        steps.append({"step": int(match.group(1)), "script": block[match.start():stop].strip()})
    return block, steps


def bound_inputs():
    # Bind the complete tracked tree. Earlier hand-enumeration omitted direct step inputs
    # (including the root crate and this audit manifest), which made the advertised
    # rebinding fingerprint narrower than the pipeline it described.
    names = git("ls-files").stdout.splitlines()
    rows = []
    for name in sorted(set(names)):
        path = ROOT / name
        if path.is_file():
            rows.append({"path": name, "sha256": digest_file(path),
                         "size_bytes": path.stat().st_size})
    fingerprint = digest_bytes(json.dumps(rows, sort_keys=True,
                                         separators=(",", ":")).encode())
    return rows, fingerprint


def parse_utc(value):
    if not isinstance(value, str):
        raise C9Error(f"timestamp is {type(value).__name__}, expected string")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise C9Error(f"invalid UTC timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        raise C9Error(f"timestamp has no timezone: {value!r}")
    return parsed.astimezone(dt.timezone.utc)


def expected_population():
    path = ROOT / "phase0/evidence/expected-digests.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    sections = {}
    for name in PIN_REPORTS:
        section = registry.get(name)
        if not isinstance(section, dict) or not section:
            raise C9Error(f"expected-digest section {name!r} is absent or empty")
        normalized = {}
        for key, value in section.items():
            digest = value.get("sha256") if isinstance(value, dict) else value
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise C9Error(f"malformed expected digest for {name}/{key}")
            normalized[key] = digest
        sections[name] = normalized
    return sections


def same_file(left, right):
    try:
        return os.path.samefile(left, right)
    except OSError:
        return Path(left).resolve() == Path(right).resolve()


def toolchain_evidence():
    inherited_path = os.environ.get("PATH", "")
    resolved = {}
    errors = []
    for name, probe in REQUIRED_TOOLS.items():
        invocation = shutil.which(name, path=inherited_path)
        if invocation is None:
            errors.append(f"required executable {name!r} is not on PATH")
            continue
        invocation = str(Path(invocation).absolute())
        real = str(Path(invocation).resolve())
        if Path(real).is_relative_to(ROOT.resolve()):
            errors.append(f"{name} resolves inside the candidate checkout: {real}")
        if not any(real.startswith(prefix) for prefix in APPROVED_TOOL_PREFIXES):
            errors.append(f"{name} resolves outside approved tool prefixes: {real}")
        record = {
            "name": name,
            "invocation_path": invocation,
            "resolved_path": real,
            "sha256": digest_file(real),
            "probe_argv": None,
            "probe_exit_code": None,
            "probe_output": None,
        }
        if probe is not None:
            argv = [invocation, *probe]
            completed = subprocess.run(
                argv, capture_output=True, stdin=subprocess.DEVNULL, timeout=30,
                env={"PATH": inherited_path, "LC_ALL": "C"},
            )
            record.update({
                "probe_argv": argv,
                "probe_exit_code": completed.returncode,
                "probe_output": (completed.stdout + completed.stderr)
                .decode(errors="replace")[:4000],
            })
            if completed.returncode != 0:
                errors.append(f"tool probe failed for {name}: {completed.returncode}")
        resolved[name] = record

    # The numbered commands are interpreted by this exact shell.  It belongs to the
    # declared trusted base, but that does not make its identity optional provenance.
    # Earlier reports hashed every command found through PATH while omitting the absolute
    # shell that actually orchestrated them.
    shell_invocation = str(Path(PIPELINE_SHELL).absolute())
    shell_real = str(Path(shell_invocation).resolve())
    shell_probe = [shell_invocation, "-c", "printf FTRO_C9_SHELL_PROBE"]
    if not Path(shell_real).is_file():
        errors.append(f"pipeline shell is not a file: {shell_real}")
    elif Path(shell_real).is_relative_to(ROOT.resolve()):
        errors.append(f"pipeline shell resolves inside the candidate checkout: {shell_real}")
    elif not any(shell_real.startswith(prefix) for prefix in APPROVED_TOOL_PREFIXES):
        errors.append(f"pipeline shell resolves outside approved tool prefixes: {shell_real}")
    if Path(shell_real).is_file():
        try:
            completed = subprocess.run(
                shell_probe, capture_output=True, stdin=subprocess.DEVNULL, timeout=30,
                env={"PATH": inherited_path, "LC_ALL": "C"},
            )
            probe_output = (completed.stdout + completed.stderr).decode(errors="replace")[:4000]
            if completed.returncode != 0 or probe_output != "FTRO_C9_SHELL_PROBE":
                errors.append(
                    f"pipeline shell probe failed: exit={completed.returncode}, "
                    f"output={probe_output!r}"
                )
            resolved["shell"] = {
                "name": "shell",
                "invocation_path": shell_invocation,
                "resolved_path": shell_real,
                "sha256": digest_file(shell_real),
                "probe_argv": shell_probe,
                "probe_exit_code": completed.returncode,
                "probe_output": probe_output,
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"pipeline shell probe could not execute: {type(exc).__name__}: {exc}")

    source_dirs = [str(Path(row["invocation_path"]).parent) for row in resolved.values()]
    safe_dirs = []
    for directory in source_dirs + ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]:
        if directory not in safe_dirs:
            safe_dirs.append(directory)
    safe_path = os.pathsep.join(safe_dirs)
    for name, record in resolved.items():
        lookup_name = Path(record["invocation_path"]).name if name == "shell" else name
        under_safe_path = shutil.which(lookup_name, path=safe_path)
        if under_safe_path is None or not same_file(under_safe_path, record["invocation_path"]):
            errors.append(
                f"sanitized PATH would substitute {name}: {under_safe_path!r} != "
                f"{record['invocation_path']!r}"
            )

    inherited_influences = {
        key: os.environ[key] for key in sorted(FORBIDDEN_ENVIRONMENT)
        if os.environ.get(key)
    }
    if inherited_influences:
        errors.append("proxy or Python injection variables are present: "
                      + ", ".join(inherited_influences))
    return {
        "approved_prefixes": list(APPROVED_TOOL_PREFIXES),
        "tools": [resolved[name] for name in (*REQUIRED_TOOLS, "shell") if name in resolved],
        "selected_pipeline_shell": shell_invocation,
        "sanitized_path": safe_path,
        "forbidden_inherited_variables": inherited_influences,
        "errors": errors,
        "verified": not errors,
    }


def execution_environment(toolchain, isolated_home):
    return {
        "PATH": toolchain["sanitized_path"],
        "HOME": str(isolated_home),
        "CURL_HOME": str(isolated_home),
        "XDG_CONFIG_HOME": str(isolated_home),
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "NO_COLOR": "1",
        "TMPDIR": "/tmp",
    }


def source_state():
    status = git("status", "--porcelain=v1", "--untracked-files=all").stdout
    if status:
        raise C9Error("C9 requires a clean checkout; found:\n" + status[:2000])
    if git("symbolic-ref", "-q", "HEAD", ok=(0, 1)).returncode == 0:
        raise C9Error("C9 requires a detached checkout of the candidate commit")
    commit = git("rev-parse", "HEAD").stdout.strip()
    if git("merge-base", "--is-ancestor", REQUIRED_ANCESTOR, commit,
           ok=(0, 1)).returncode != 0:
        raise C9Error(f"candidate {commit} does not descend from {REQUIRED_ANCESTOR}")
    if (ROOT / "data").exists() or OPTICAL_ZIP.exists():
        raise C9Error("C9 requires no pre-existing data/ or optical ZIP")
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard").stdout.splitlines()
    if ignored:
        raise C9Error("C9 requires a fresh checkout with no ignored residue; found: "
                      + ", ".join(ignored[:10]))
    return {
        "commit": commit,
        "tree": git("rev-parse", "HEAD^{tree}").stdout.strip(),
        "required_ancestor": REQUIRED_ANCESTOR,
        "clean": True,
        "detached_head": True,
        "checkout_realpath": str(ROOT),
    }


def terminate_process_group(process, grace_s=TERMINATION_GRACE_S):
    """Terminate and reap the complete isolated process group after a timeout."""
    evidence = {
        "attempted": True,
        "sigterm_sent": False,
        "sigkill_sent": False,
        "reaped": False,
        "error": None,
    }
    try:
        os.killpg(process.pid, signal.SIGTERM)
        evidence["sigterm_sent"] = True
    except ProcessLookupError:
        pass
    except OSError as exc:
        evidence["error"] = f"SIGTERM process group: {type(exc).__name__}: {exc}"
        try:
            process.kill()
        except OSError:
            pass
    try:
        stdout, stderr = process.communicate(timeout=grace_s)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            evidence["sigkill_sent"] = True
        except ProcessLookupError:
            pass
        except OSError as exc:
            evidence["error"] = (evidence["error"] + "; " if evidence["error"] else "") + \
                f"SIGKILL process group: {type(exc).__name__}: {exc}"
            try:
                process.kill()
            except OSError:
                pass
        stdout, stderr = process.communicate()
    evidence["reaped"] = process.poll() is not None
    evidence["returncode_after_termination"] = process.returncode
    return stdout, stderr, evidence


def run_step(step, environment, *, shell=PIPELINE_SHELL, timeout_s=STEP_TIMEOUT_S,
             termination_grace_s=TERMINATION_GRACE_S):
    started = utc_now()
    began = time.monotonic()
    argv = [shell, "-eu"]
    if shell.endswith("zsh"):
        argv += ["-o", "pipefail"]
    argv += ["-c", step["script"]]
    process_group = {
        "isolated": False,
        "timeout_termination": None,
    }
    try:
        process = subprocess.Popen(
            argv, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL, env=environment, start_new_session=True,
        )
        process_group["isolated"] = True
        try:
            stdout, stderr = process.communicate(timeout=timeout_s)
            error = None
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            stdout, stderr, termination = terminate_process_group(
                process, grace_s=termination_grace_s,
            )
            process_group["timeout_termination"] = termination
            error = f"timeout after {timeout_s}s; isolated process group terminated and reaped"
            if not termination["reaped"] or termination["error"]:
                error += "; termination proof incomplete"
            exit_code = None
    except OSError as exc:
        error = f"{type(exc).__name__}: {exc}"
        exit_code = None
        stdout, stderr = b"", b""
    return {
        "step": step["step"],
        "script": step["script"],
        "argv_prefix": argv[:-1],
        "started_utc": started,
        "ended_utc": utc_now(),
        "duration_s": round(time.monotonic() - began, 6),
        "exit_code": exit_code,
        "spawn_error": error,
        "process_group": process_group,
        "stdout_n_bytes": len(stdout),
        "stderr_n_bytes": len(stderr),
        "stdout_sha256": digest_bytes(stdout),
        "stderr_sha256": digest_bytes(stderr),
        "stdout_excerpt": stdout.decode(errors="replace")[-8000:],
        "stderr_excerpt": stderr.decode(errors="replace")[-8000:],
        "stdout_text": stdout.decode(errors="replace"),
        "stderr_text": stderr.decode(errors="replace"),
        "_stdout": stdout,
        "_combined": (stdout + b"\n" + stderr).decode(errors="replace"),
    }


def classify_failure(step, combined):
    lower = combined.lower()
    if "preflight" in lower:
        failure = "preflight_failure"
    elif any(token in lower for token in ("earthdata login", "<!doctype html", "<html")):
        failure = "authentication_or_interstitial"
    elif any(token in lower for token in
             ("could not resolve host", "name or service not known", "connection refused",
              "timed out", "ssl", "tls", "network is unreachable")):
        failure = "transport_failure"
    elif "checksum" in lower or "digest mismatch" in lower:
        failure = "digest_mismatch"
    elif "content" in lower and any(token in lower for token in ("reject", "invalid", "failed")):
        failure = "content_validation_failure"
    elif re.search(r"http[^\n]*(?:4\d\d|5\d\d)", lower):
        failure = "http_failure"
    elif any(token in lower for token in
             ("command not found", "no such file or directory", "can't open file")):
        failure = "local_environment_failure" if step == 0 else "local_workflow_failure"
    else:
        failure = "unclassified_retrieval_failure" if step in (1, 3, 4) \
            else "local_workflow_failure"

    if any(token in lower for token in ("could not resolve host", "name or service not known")):
        reachability = "dns_failed"
    elif "connection refused" in lower or "network is unreachable" in lower:
        reachability = "tcp_failed"
    elif "ssl" in lower or "tls" in lower:
        reachability = "tls_failed"
    elif re.search(r"http[^\n]*\d{3}", lower):
        reachability = "http_response"
    else:
        reachability = "not_established"
    return failure, reachability


def fresh_report(path, started_utc):
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path}: {type(exc).__name__}: {exc}"
    values = []
    if isinstance(document.get("pins"), list):
        values.extend(pin.get("retrieved_utc") for pin in document["pins"]
                      if isinstance(pin, dict) and pin.get("retrieved_utc"))
    if isinstance(document.get("failures"), list):
        values.extend(item.get("retrieved_utc") for item in document["failures"]
                      if isinstance(item, dict) and item.get("retrieved_utc"))
    if document.get("retrieved_utc"):
        values.append(document["retrieved_utc"])
    if not values:
        # The list pinners historically omitted retrieved_utc from failed attempts.  A
        # rejected report is nevertheless fresh evidence when this run created the file:
        # source_state() proved that no untracked .rejected file existed beforehand.
        started = parse_utc(started_utc)
        modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc)
        if modified < started - dt.timedelta(seconds=2):
            return None, f"{path}: no retrieval timestamp and file predates this C9 run"
        return document, None
    try:
        started = parse_utc(started_utc)
        parsed = [parse_utc(value) for value in values]
    except C9Error as exc:
        return None, f"{path}: {exc}"
    if any(value < started for value in parsed):
        return None, f"{path}: report predates this C9 run"
    return document, None


def pin_identifier(section, pin):
    kind = PIN_REPORTS[section]["identifier"]
    if kind == "url_basename":
        url = pin.get("url")
        return url.rsplit("/", 1)[-1] if isinstance(url, str) else None
    return pin.get(kind)


def attempt_from_pin(section, step, identifier, pin, expected_digest=None):
    ok = (
        pin.get("checksum_match") is True
        and pin.get("retrieval_validation") == "content_validated"
        and pin.get("sha256") == expected_digest
        and pin.get("expected_sha256") == expected_digest
        and pin.get("http_status") == 200
        and type(pin.get("size_bytes")) is int
        and pin.get("size_bytes") > 0
    )
    return {
        "source_group": section,
        "step": step,
        "artifact": identifier,
        "url": pin.get("url"),
        "failure_class": "success" if ok else "unclassified_retrieval_failure",
        "reachability_stage": "bytes_received" if pin.get("size_bytes") else
                              "http_response" if pin.get("http_status") else
                              "not_established",
        "access_class_conclusion": "not_established",
        "http_status": pin.get("http_status"),
        "bytes_received": pin.get("size_bytes"),
        "expected_sha256": expected_digest,
        "reported_expected_sha256": pin.get("expected_sha256"),
        "observed_sha256": pin.get("sha256"),
        "content_validation_result": pin.get("retrieval_validation"),
        "retrieved_utc": pin.get("retrieved_utc"),
    }


def rejected_reason(document, failure):
    """Read the actual failure vocabulary emitted by all four pinners."""
    reason = failure.get("error") or failure.get("reason")
    if not reason or str(reason).strip().lower() == "see rejected_reason":
        reason = document.get("rejected_reason") or reason
    return str(reason or "")


def rejected_attempt(section, config, document, failure, population):
    # Single-pin reports keep HTTP/byte evidence at the document root and put only a
    # reason pointer in failures[].  Overlay the row so neither layer is discarded.
    evidence = {**document, **failure}
    identifier = pin_identifier(section, evidence)
    reason = rejected_reason(document, failure)
    failure_class, classified_reachability = classify_failure(config["step"], reason)
    http_status = evidence.get("http_status")
    size_bytes = evidence.get("size_bytes")
    if type(size_bytes) is int and size_bytes > 0:
        reachability = "bytes_received"
    elif type(http_status) is int:
        reachability = "http_response"
    else:
        reachability = classified_reachability
    return {
        "source_group": section,
        "step": config["step"],
        "artifact": identifier or evidence.get("name") or evidence.get("key")
                    or evidence.get("url"),
        "url": evidence.get("url"),
        "failure_class": failure_class,
        "reachability_stage": reachability,
        "access_class_conclusion": "not_established",
        "http_status": http_status,
        "bytes_received": size_bytes,
        "expected_sha256": population[section].get(identifier),
        "reported_expected_sha256": evidence.get("expected_sha256"),
        "observed_sha256": evidence.get("sha256"),
        "content_validation_result": evidence.get("retrieval_validation")
                                     or "content_rejected",
        "retrieved_utc": evidence.get("retrieved_utc"),
        "reason": reason,
    }


def provider_report_evidence(started_utc, population):
    attempts, records, errors = [], [], []
    for section, config in PIN_REPORTS.items():
        official = ROOT / config["path"]
        rejected = Path(str(official) + ".rejected")
        chosen, promoted, freshness_error = None, None, None
        for path, is_promoted in ((official, True), (rejected, False)):
            if not path.exists():
                continue
            document, error = fresh_report(path, started_utc)
            if document is not None:
                chosen, promoted = (path, document), is_promoted
                break
            freshness_error = error
        if chosen is None:
            message = f"{section}: no fresh promoted or rejected report"
            if freshness_error:
                message += f" ({freshness_error})"
            errors.append(message)
            records.append({"section": section, "promoted": None, "fresh": False,
                            "path": None, "sha256": None, "errors": [message]})
            continue

        path, document = chosen
        if isinstance(document.get("pins"), list):
            pins = document["pins"]
        else:
            # A promoted vgosDB document is one pin.  A rejected one has n_pinned == 0;
            # treating the document as both a pin and a failure emitted duplicate attempts.
            pins = [document] if promoted else []
        report_errors = []
        identifiers = []
        section_attempts = []
        for pin in pins:
            if not isinstance(pin, dict):
                report_errors.append("pin is not an object")
                continue
            identifier = pin_identifier(section, pin)
            identifiers.append(identifier)
            section_attempts.append(attempt_from_pin(
                section, config["step"], identifier, pin,
                population[section].get(identifier),
            ))
        attempts.extend(section_attempts)
        expected_ids = set(population[section])
        observed_ids = set(identifiers)
        if promoted and identifiers != list(dict.fromkeys(identifiers)):
            report_errors.append("duplicate artifact identifier")
        if promoted and observed_ids != expected_ids:
            report_errors.append(
                f"population mismatch missing={sorted(expected_ids - observed_ids)} "
                f"unknown={sorted(observed_ids - expected_ids)}"
            )
        if promoted and any(item["failure_class"] != "success"
                            for item in section_attempts):
            report_errors.append("one or more promoted pins fail external population/digest checks")
        if promoted and (document.get("n_failed") != 0
                         or document.get("retrieval_validation") != "content_validated"):
            report_errors.append("promoted report does not declare a complete clean success")
        if not promoted:
            report_errors.append("current run produced a rejected report")
            failures = document.get("failures")
            if not isinstance(failures, list) or not failures:
                failures = [document]
            for failure in failures:
                if isinstance(failure, dict):
                    attempts.append(rejected_attempt(
                        section, config, document, failure, population,
                    ))
        records.append({
            "section": section,
            "promoted": promoted,
            "fresh": True,
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": digest_file(path),
            "n_expected": len(expected_ids),
            "n_observed": len(identifiers),
            "errors": report_errors,
        })
        errors.extend(f"{section}: {message}" for message in report_errors)
    return attempts, records, errors


def optical_attempt(optical, completed_steps):
    if not optical:
        return None
    ok = (optical["md5_match"] and optical.get("http_status") == 200
          and 3 in completed_steps)
    return {
        "source_group": "optical",
        "step": 3,
        "artifact": "ROCIT campaign results.zip",
        "url": optical.get("effective_url"),
        "failure_class": "success" if ok else "digest_mismatch" if not optical["md5_match"]
                         else "http_failure",
        "reachability_stage": "bytes_received",
        # Identity plus a successful unauthenticated request is recorded below, but it
        # does not establish a universal access class.
        "access_class_conclusion": "not_established",
        "access_evidence": "anonymous_request_succeeded" if ok else "not_established",
        "http_status": optical.get("http_status"),
        "content_type": optical.get("content_type"),
        "bytes_received": optical["size_bytes"],
        "expected_md5": optical["expected_md5"],
        "observed_md5": optical["md5"],
        "expected_sha256": None,
        "observed_sha256": optical["sha256"],
        "content_validation_result": "archive_extracted" if 3 in completed_steps else
                                     "not_established",
    }


def optical_http_evidence(record):
    matches = re.findall(
        r"(?m)^FTRO_CURL_HTTP (\d{3}) (\S+) (\S*) ([0-9]+(?:\.[0-9]+)?)$",
        record.get("stdout_text", ""),
    )
    if len(matches) != 1:
        raise C9Error(f"optical curl emitted {len(matches)} structured HTTP records, expected 1")
    status, effective_url, content_type, size_download = matches[0]
    return {
        "http_status": int(status),
        "effective_url": effective_url,
        "content_type": content_type or None,
        "curl_size_download": int(float(size_download)),
    }


def deterministic_checks(step_results, expected):
    checks = []
    by_step = {item["step"]: item for item in step_results}
    for name, path in DETERMINISTIC.items():
        if name == "step2_stdout":
            if 2 not in by_step:
                continue
            observed = by_step[2]["stdout_sha256"]
        else:
            step = int(name[4])
            if step not in by_step or not Path(ROOT, path).is_file():
                continue
            observed = digest_file(ROOT / path)
        checks.append({"name": name, "path": path, "expected_sha256": expected[name],
                       "observed_sha256": observed, "match": observed == expected[name]})
    return checks


def prepare_regenerated_outputs(step_number, expected_bytes):
    prepared = []
    for relative in REGENERATED_BY_STEP.get(step_number, []):
        path = ROOT / relative
        if relative not in expected_bytes:
            raise C9Error(f"no committed expectation captured for generated output {relative}")
        if not path.is_file():
            raise C9Error(f"generated output absent before freshness test: {relative}")
        observed = path.read_bytes()
        if observed != expected_bytes[relative]:
            raise C9Error(f"generated output drifted before its pipeline step: {relative}")
        path.unlink()
        prepared.append({
            "path": relative,
            "removed_before_step": step_number,
            "expected_sha256": digest_bytes(observed),
            "expected_size_bytes": len(observed),
        })
    return prepared


def verify_regenerated_outputs(step_number, expected_bytes):
    checks = []
    for relative in REGENERATED_BY_STEP.get(step_number, []):
        path = ROOT / relative
        exists = path.is_file()
        observed = path.read_bytes() if exists else None
        byte_match = exists and observed == expected_bytes[relative]
        match = exists if relative in NONDETERMINISTIC_REGENERATED else byte_match
        checks.append({
            "path": relative,
            "step": step_number,
            "recreated": exists,
            "expected_sha256": digest_bytes(expected_bytes[relative]),
            "observed_sha256": digest_bytes(observed) if observed is not None else None,
            "byte_match": byte_match,
            "match": match,
        })
    return checks


def tracked_change_evidence():
    changed = sorted(git("diff", "--name-only", "HEAD").stdout.splitlines())
    untracked = sorted(git("ls-files", "--others", "--exclude-standard").stdout.splitlines())
    unexpected = sorted(set(changed) - ALLOWED_TRACKED_OUTPUTS)
    required_fresh = sorted(PIN_REPORT_PATHS)
    missing_fresh = sorted(set(required_fresh) - set(changed))
    return {
        "changed_paths": changed,
        "changed_paths_sha256": digest_bytes(
            json.dumps(changed, separators=(",", ":")).encode()
        ),
        "allowed_paths": sorted(ALLOWED_TRACKED_OUTPUTS),
        "unexpected_paths": unexpected,
        "pin_reports_not_changed": missing_fresh,
        "untracked_paths": untracked,
        "verified": not unexpected and not missing_fresh and not untracked,
    }


def clean_provider_bytes():
    removed, errors = [], []
    for path in (ROOT / "data", OPTICAL_ZIP):
        try:
            if path.is_dir():
                shutil.rmtree(path)
                removed.append(path.relative_to(ROOT).as_posix() + "/")
            elif path.exists():
                path.unlink()
                removed.append(path.relative_to(ROOT).as_posix())
        except OSError as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
    return {"attempted": True, "removed": removed, "errors": errors,
            "provider_bytes_retained": (ROOT / "data").exists() or OPTICAL_ZIP.exists()}


def write_new(path, document):
    path = Path(path)
    if path.exists() or Path(str(path) + ".part").exists():
        raise C9Error(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".part")
    temporary.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def reserve_report_paths(path):
    paths = [Path(path), Path(str(path) + ".part"), Path(str(path) + ".provisional")]
    present = [str(item) for item in paths if item.exists()]
    if present:
        raise C9Error("refusing to overwrite report evidence: " + ", ".join(present))


def write_provisional(path, document):
    provisional = Path(str(path) + ".provisional")
    body = dict(document)
    body["status"] = "provisional"
    body["qualifying"] = False
    body["cleanup"] = {"attempted": False, "provider_bytes_retained": True,
                       "errors": [], "removed": []}
    provisional.parent.mkdir(parents=True, exist_ok=True)
    provisional.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return {"path": str(provisional), "sha256": digest_file(provisional),
            "retained_after_successful_finalization": False}


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True)
    return ap


def main(argv=None):
    global GIT_COMMAND
    args = parser().parse_args(argv)
    os.chdir(ROOT)
    output = Path(args.out).resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise C9Error("C9 report must be written outside the execution checkout")
    reserve_report_paths(output)
    toolchain = toolchain_evidence()
    if not toolchain["verified"]:
        raise C9Error("toolchain preflight failed before any provider request: "
                      + "; ".join(toolchain["errors"]))
    GIT_COMMAND = next(
        row["invocation_path"] for row in toolchain["tools"] if row["name"] == "git"
    )
    state = source_state()
    population = expected_population()
    readme_text = README.read_text(encoding="utf-8")
    block, steps = extract_pipeline(readme_text)
    inputs, input_fingerprint = bound_inputs()
    expected = {name: digest_file(ROOT / path) for name, path in DETERMINISTIC.items()}
    generated_paths = sorted({path for paths in REGENERATED_BY_STEP.values() for path in paths})
    missing_generated = [path for path in generated_paths if not (ROOT / path).is_file()]
    if missing_generated:
        raise C9Error("committed generated expectations are absent: "
                      + ", ".join(missing_generated))
    expected_bytes = {path: (ROOT / path).read_bytes() for path in generated_paths}

    started = utc_now()
    results, completed, failure = [], [], None
    optical = None
    prepared_outputs, regenerated_checks = [], []
    attempts, provider_reports, provider_errors = [], [], []
    deterministic = []
    provisional = None

    with tempfile.TemporaryDirectory(prefix="ftro-c9-home-") as isolated_home:
        environment = execution_environment(toolchain, isolated_home)
        try:
            for step in steps:
                print(f"C9 step {step['step']}", flush=True)
                prepared_outputs.extend(
                    prepare_regenerated_outputs(step["step"], expected_bytes)
                )
                record = run_step(
                    step, environment, shell=toolchain["selected_pipeline_shell"],
                )
                results.append(record)
                if record["exit_code"] != 0 or record["spawn_error"]:
                    failure_class, reachability = classify_failure(
                        step["step"], record["_combined"]
                    )
                    failure = {
                        "step": step["step"],
                        "failure_class": failure_class,
                        "reachability_stage": reachability,
                        "access_class_conclusion": "not_established",
                        "http_status": None,
                        "bytes_received": None,
                        "expected_sha256": None,
                        "observed_sha256": None,
                        "content_validation_result": "not_established",
                    }
                    break
                completed.append(step["step"])
                just_regenerated = verify_regenerated_outputs(step["step"], expected_bytes)
                regenerated_checks.extend(just_regenerated)
                if not all(item["match"] for item in just_regenerated):
                    failure = {
                        "step": step["step"],
                        "failure_class": "local_workflow_failure",
                        "reachability_stage": "not_applicable",
                        "access_class_conclusion": "not_applicable",
                        "reason": "a removed output was not freshly regenerated as required",
                    }
                    break
                if step["step"] == 3:
                    if not OPTICAL_ZIP.is_file():
                        raise C9Error("optical step exited zero without creating the archive")
                    http = optical_http_evidence(record)
                    observed_md5 = digest_file(OPTICAL_ZIP, "md5")
                    optical = {
                        **http,
                        "size_bytes": OPTICAL_ZIP.stat().st_size,
                        "md5": observed_md5,
                        "expected_md5": EXPECTED_OPTICAL_MD5,
                        "md5_match": observed_md5 == EXPECTED_OPTICAL_MD5,
                        "sha256": digest_file(OPTICAL_ZIP),
                        "authentication_material_supplied": False,
                        "proxy_environment_supplied": False,
                    }
                    if http["http_status"] != 200 or not optical["md5_match"] \
                            or http["curl_size_download"] != optical["size_bytes"]:
                        failure = {
                            "step": 3,
                            "failure_class": "digest_mismatch" if not optical["md5_match"]
                                             else "http_failure",
                            "reachability_stage": "bytes_received",
                            "access_class_conclusion": "not_established",
                            "http_status": http["http_status"],
                            "bytes_received": optical["size_bytes"],
                            "expected_sha256": None,
                            "observed_sha256": optical["sha256"],
                            "content_validation_result": "archive_extracted",
                        }
                        break
        except Exception as exc:
            if failure is None:
                failure = {
                    "step": None,
                    "failure_class": "local_workflow_failure",
                    "reachability_stage": "not_applicable",
                    "access_class_conclusion": "not_applicable",
                    "reason": f"C9 recorder exception: {type(exc).__name__}: {exc}",
                }

        deterministic = deterministic_checks(results, expected)
        exact_deterministic_names = set(DETERMINISTIC)
        observed_deterministic_names = {item["name"] for item in deterministic}
        if failure is None and (
            completed != list(range(8))
            or observed_deterministic_names != exact_deterministic_names
            or not all(item["match"] for item in deterministic)
        ):
            failure = {
                "step": None,
                "failure_class": "local_workflow_failure",
                "reachability_stage": "not_applicable",
                "access_class_conclusion": "not_applicable",
                "reason": "pipeline incomplete or deterministic check population/content mismatch",
            }

        try:
            attempts, provider_reports, provider_errors = provider_report_evidence(
                started, population,
            )
        except Exception as exc:
            provider_errors = [f"provider evidence recorder failed: {type(exc).__name__}: {exc}"]
        optical_row = optical_attempt(optical, completed)
        if optical_row:
            attempts.append(optical_row)

        expected_attempts = 1 + sum(len(section) for section in population.values())
        successful_attempts = [row for row in attempts if row["failure_class"] == "success"]
        provider_population_verified = (
            not provider_errors
            and len(attempts) == expected_attempts
            and len(successful_attempts) == expected_attempts
            and len({(row["source_group"], row["artifact"]) for row in attempts})
            == expected_attempts
        )
        if failure is None and not provider_population_verified:
            failure = {
                "step": None,
                "failure_class": "local_workflow_failure",
                "reachability_stage": "not_applicable",
                "access_class_conclusion": "not_applicable",
                "reason": "fresh provider evidence population is incomplete or invalid: "
                          + "; ".join(provider_errors[:6]),
            }

        # Prefer the structured rejected-report reason over a whole numbered step's mixed
        # stdout/stderr when one is available.
        failed_attempts = [row for row in attempts if row["failure_class"] != "success"]
        if failure is not None and failed_attempts:
            candidate = failed_attempts[-1]
            for key in (
                "failure_class", "reachability_stage", "access_class_conclusion",
                "http_status", "bytes_received", "expected_sha256", "observed_sha256",
                "content_validation_result", "url", "artifact", "reason",
            ):
                if candidate.get(key) is not None:
                    failure[key] = candidate[key]

        public_results = [
            {key: value for key, value in item.items() if not key.startswith("_")}
            for item in results
        ]
        report = {
            "document": "FTRO Phase-0 C9 live-pipeline report",
            "version": "1.1.0",
            "run_id": args.run_id,
            "started_utc": started,
            "ended_utc": utc_now(),
            "status": "pass" if failure is None else "fail",
            "qualifying": failure is None,
            "subject": state,
            "contract": {
                "id": "FTRO-ACC-001", "version": "1.2.0", "clause": "C9",
                "path": "phase0/acceptance-contract-v1.0.md",
                "sha256": digest_file(ROOT / "phase0/acceptance-contract-v1.0.md"),
            },
            "pipeline": {
                "path": "README.md", "sha256": digest_file(README),
                "command_block_sha256": digest_bytes(block.encode()),
                "steps_expected": list(range(8)), "steps_completed": completed,
            },
            "runner": {
                "path": "phase0/audit/run_c9.py",
                "sha256": digest_file(Path(__file__).resolve()),
            },
            "environment": {
                "python": sys.version,
                "platform": platform.platform(),
                "variables": environment,
                "toolchain": toolchain,
                "stdin": "DEVNULL",
            },
            "bound_inputs": inputs,
            "bound_input_fingerprint_sha256": input_fingerprint,
            "manual_interventions": 0,
            "manual_interventions_basis": "all child stdin was DEVNULL",
            "route_substitutions": 0,
            "route_substitutions_basis": (
                "proxy/Python injection variables absent; README URLs unchanged; "
                "all command paths resolved under approved prefixes"
            ),
            "first_failure": failure,
            "step_results": public_results,
            "prepared_outputs": prepared_outputs,
            "regenerated_output_checks": regenerated_checks,
            "optical_archive": optical,
            "expected_provider_attempts": expected_attempts,
            "provider_attempts": attempts,
            "provider_report_evidence": provider_reports,
            "provider_evidence_errors": provider_errors,
            "n_provider_attempts_recorded": len(attempts),
            "n_provider_attempts_successful": len(successful_attempts),
            "provider_population_verified": provider_population_verified,
            "deterministic_output_checks": deterministic,
            "cleanup": {"attempted": False, "removed": [], "errors": [],
                        "provider_bytes_retained": True},
        }

        try:
            provisional = write_provisional(output, report)
        finally:
            cleanup = clean_provider_bytes()

    tracked_changes = tracked_change_evidence()
    if cleanup["errors"] or cleanup["provider_bytes_retained"]:
        if failure is None:
            failure = {
                "step": None,
                "failure_class": "local_workflow_failure",
                "reachability_stage": "not_applicable",
                "access_class_conclusion": "not_applicable",
                "reason": "provider-byte cleanup failed",
            }
    if not tracked_changes["verified"] and failure is None:
        failure = {
            "step": None,
            "failure_class": "local_workflow_failure",
            "reachability_stage": "not_applicable",
            "access_class_conclusion": "not_applicable",
            "reason": "post-run tracked changes are outside the declared output set or a "
                      "fresh pin report did not change",
        }
    report["first_failure"] = failure
    report["status"] = "pass" if failure is None else "fail"
    report["qualifying"] = failure is None
    report["ended_utc"] = utc_now()
    report["cleanup"] = cleanup
    report["tracked_change_evidence"] = tracked_changes
    report["provisional_witness"] = provisional
    if failure is None:
        contract_errors = c9_contract.validate_success_report(
            report,
            ROOT,
            {
                "commit": state["commit"],
                "tree": state["tree"],
                "required_ancestor": REQUIRED_ANCESTOR,
                "contract_id": "FTRO-ACC-001",
                "contract_version": "1.2.0",
                "output_view": "producer",
                "report_path": str(output),
                "verify_runtime_tools": True,
                "git_command": GIT_COMMAND,
            },
        )
        if contract_errors:
            failure = {
                "step": None,
                "failure_class": "local_workflow_failure",
                "reachability_stage": "not_applicable",
                "access_class_conclusion": "not_applicable",
                "reason": "shared C9 success contract rejected producer evidence: "
                          + "; ".join(contract_errors[:12]),
            }
            report["first_failure"] = failure
            report["status"] = "fail"
            report["qualifying"] = False
    write_new(output, report)
    # A completed final report supersedes the crash-only provisional. If final creation
    # raises, this line is never reached and the provisional remains durable.
    Path(provisional["path"]).unlink()
    print(f"wrote {output}")
    print(f"C9 {report['status']}; completed steps {completed}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except C9Error as exc:
        print(f"C9 RUN REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
