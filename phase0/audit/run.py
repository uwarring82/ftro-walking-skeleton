#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute the frozen Phase-0 mutation manifest without a binary false pass.

The runner has three observations:

* ``detected`` -- the registered detector rejected the applied mutation;
* ``not_detected`` -- the detector demonstrably ran and accepted it;
* ``not_executed`` -- mutation, detector, or reset evidence is incomplete.

The manifest decides which of the first two is expected.  ``not_executed`` can never
pass.  Every case runs in a fresh full Git archive initialized as its own repository;
no production source is symlinked into a mutation workspace.
"""

import argparse
import copy
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

# The controller requires a residue-free carrier.  Set this before the adjacent
# c9_contract import so merely starting the audit cannot mint ignored source bytes.
sys.dont_write_bytecode = True

AUDIT_DIR = Path(__file__).resolve().parent
if str(AUDIT_DIR) not in sys.path:
    sys.path.insert(0, str(AUDIT_DIR))
import c9_contract  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = "phase0/audit/execution-manifest-v1.0.json"
C9_REQUIRED_ANCESTOR = "a806bbaa573d28f1460d18110f7974189ca19213"
RESULT_STATES = {"detected", "not_detected", "not_executed"}
EXPECTED_OPERATOR_ORDER = (
    "M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10",
    "M11", "M12", "M12a", "M12b", "M12c", "M13",
)
EXPECTED_OPERATORS = set(EXPECTED_OPERATOR_ORDER)

# This is the executable scope, not merely the semantic operator headings.  A manifest
# that silently drops one alternative, or changes a rejection into an accepted mutation,
# is a different audit and must not validate under v1.0.1.
EXPECTED_CASES = {
    "M1.missing-generator": ("M1", "detected", "rejected"),
    "M1.missing-pin-retrieved-utc": ("M1", "detected", "rejected"),
    "M1.missing-pin-retrieval-procedure": ("M1", "detected", "rejected"),
    "M2.counter-false": ("M2", "detected", "rejected"),
    "M2.counter-float": ("M2", "detected", "rejected"),
    "M2.counter-string": ("M2", "detected", "rejected"),
    "M3.list-object": ("M3", "detected", "rejected"),
    "M3.list-string": ("M3", "detected", "rejected"),
    "M4.truncate": ("M4", "detected", "rejected"),
    "M4.duplicate": ("M4", "detected", "rejected"),
    "M4.add-rogue": ("M4", "detected", "rejected"),
    "M5.fabricated-digests": ("M5", "detected", "rejected"),
    "M6.relabel-series-and-mjd": ("M6", "not_detected", "no_effect"),
    "M7.single-home-pulsar-epoch": ("M7", "not_detected", "coherent_propagation"),
    "M8.remove-caller-sort": ("M8", "not_detected", "no_effect"),
    "M9.int-to-round": ("M9", "detected", "rejected"),
    "M9.gt-to-gte": ("M9", "detected", "rejected"),
    "M10.halve-run-span": ("M10", "detected", "rejected"),
    "M11.explicit-digest-route": ("M11", "detected", "rejected"),
    "M11.registry-route": ("M11", "detected", "rejected"),
    "M12.content-without-bump": ("M12", "detected", "rejected"),
    "M12a.version-downgrade": ("M12a", "detected", "rejected"),
    "M12b.version-removed": ("M12b", "detected", "rejected"),
    "M12c.version-gained": ("M12c", "not_detected", "accepted"),
    "M13.consume-before-produce": ("M13", "detected", "rejected"),
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
COMMIT_RE = re.compile(r"[0-9a-f]{40}")
SAFE_INHERITED_ENV = (
    "PATH", "HOME", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "WINDIR",
)
FIXED_SAFE_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}
TRUSTED_GIT_CANDIDATES = (
    "/usr/bin/git",
    "/usr/local/bin/git",
    "/opt/homebrew/bin/git",
)
CONTROLLER_GIT = None
CONTROLLER_GIT_EVIDENCE = None


class RecipeError(Exception):
    """The recipe could not be applied or its execution evidence is incomplete."""


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_utc(value, where):
    require_string(value, where)
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecipeError(f"{where} is not an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise RecipeError(f"{where} has no timezone")
    return parsed.astimezone(dt.timezone.utc)


def sha256_bytes(body):
    return hashlib.sha256(body).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def true_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def sanitized_environment(overrides=None):
    """Build the complete subprocess environment from a small allowlist.

    In particular, do not inherit PYTHONPATH/PYTHONHOME/PYTHONSTARTUP or Git repository
    selectors.  Those can execute code or redirect a command before the audited checkout
    is touched.  PATH and the platform temporary/home variables are operational inputs and
    are recorded with every command.
    """
    environment = {
        key: os.environ[key]
        for key in SAFE_INHERITED_ENV
        if key in os.environ
    }
    environment.setdefault("PATH", os.defpath)
    validate_safe_path(environment["PATH"], "subprocess PATH")
    environment.update(FIXED_SAFE_ENV)
    environment.update(overrides or {})
    validate_safe_path(environment["PATH"], "subprocess PATH")
    return environment


def validate_safe_path(value, where):
    """Reject PATH entries whose meaning changes with the subprocess working directory."""
    if not isinstance(value, str) or not value:
        raise RecipeError(f"{where} must be a non-empty string")
    entries = value.split(os.pathsep)
    unsafe = [entry for entry in entries if not entry or not Path(entry).is_absolute()]
    if unsafe:
        raise RecipeError(f"{where} contains empty or relative entries: {unsafe!r}")
    return entries


def isolated_case_environment(base, home):
    """Return the complete case environment with no user/system Git configuration."""
    home = Path(home).resolve()
    home.mkdir(parents=True, exist_ok=True)
    hooks = home / "empty-git-hooks"
    hooks.mkdir()
    return sanitized_environment({
        **(base or {}),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "FTRO_EMPTY_GIT_HOOKS": str(hooks),
    })


def select_controller_git():
    """Resolve Git without consulting caller-controlled PATH and bind its bytes."""
    global CONTROLLER_GIT, CONTROLLER_GIT_EVIDENCE
    if CONTROLLER_GIT_EVIDENCE is not None:
        return dict(CONTROLLER_GIT_EVIDENCE)
    for candidate in TRUSTED_GIT_CANDIDATES:
        path = Path(candidate)
        if not path.is_file() or not os.access(path, os.X_OK):
            continue
        resolved = str(path.resolve())
        environment = {
            "PATH": os.defpath,
            "LC_ALL": "C",
            **FIXED_SAFE_ENV,
        }
        argv = [candidate, "--no-replace-objects", "--version"]
        try:
            completed = subprocess.run(
                argv, capture_output=True, text=True, timeout=30,
                env=environment, stdin=subprocess.DEVNULL,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if completed.returncode != 0:
            continue
        CONTROLLER_GIT = candidate
        CONTROLLER_GIT_EVIDENCE = {
            "invocation_path": candidate,
            "resolved_path": resolved,
            "sha256": sha256_file(resolved),
            "probe_argv": argv,
            "probe_exit_code": completed.returncode,
            "probe_output": (completed.stdout + completed.stderr)[:4000],
        }
        return dict(CONTROLLER_GIT_EVIDENCE)
    raise RecipeError(
        "no executable Git found at a fixed trusted path: "
        + ", ".join(TRUSTED_GIT_CANDIDATES)
    )


def git(root, *args, ok=(0,), text=True, environment=None):
    if CONTROLLER_GIT is None:
        select_controller_git()
    result = subprocess.run(
        [CONTROLLER_GIT, "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-c", "core.hooksPath=/dev/null", *args],
        cwd=root, capture_output=True, text=text, timeout=120,
        env=sanitized_environment(environment),
        stdin=subprocess.DEVNULL,
    )
    if result.returncode not in ok:
        raise RecipeError(
            f"git {' '.join(args)} exited {result.returncode}: "
            f"{result.stderr[-800:] if text else '<binary stderr>'}"
        )
    return result


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def ensure_exact_keys(value, required, optional=(), where="object"):
    if not isinstance(value, dict):
        raise RecipeError(f"{where} is {type(value).__name__}, expected object")
    keys = set(value)
    missing = set(required) - keys
    unknown = keys - set(required) - set(optional)
    if missing or unknown:
        raise RecipeError(f"{where} keys invalid; missing={sorted(missing)}, "
                          f"unknown={sorted(unknown)}")


def require_string(value, where, *, nonempty=True):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise RecipeError(f"{where} must be a{' non-empty' if nonempty else ''} string")


def require_string_list(value, where, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value) \
            or not all(isinstance(item, str) and item for item in value):
        raise RecipeError(f"{where} must be a{' non-empty' if nonempty else ''} string list")


def require_exit_codes(value, where, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value) \
            or not all(true_int(item) for item in value) or len(value) != len(set(value)):
        raise RecipeError(f"{where} must be a{' non-empty' if nonempty else ''} unique int list")


def require_relative_path(value, where):
    require_string(value, where)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise RecipeError(f"{where} must be a normalized relative path inside the subject")


def require_digest(value, where):
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise RecipeError(f"{where} must be a lowercase SHA-256 digest")


def validate_pointer(value, where):
    if not isinstance(value, list) or not value:
        raise RecipeError(f"{where} must be a non-empty JSON pointer array")
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (str, int)):
            raise RecipeError(f"{where} members must be string keys or integer indexes")


def validate_mutation(mutation, where="mutation", *, nested=False):
    if not isinstance(mutation, dict):
        raise RecipeError(f"{where} must be an object")
    kind = mutation.get("kind")
    require_string(kind, f"{where}.kind")
    if kind == "composite":
        if nested:
            raise RecipeError(f"{where} cannot contain a nested composite")
        ensure_exact_keys(mutation, {"kind", "operations"}, where=where)
        operations = mutation["operations"]
        if not isinstance(operations, list) or not operations:
            raise RecipeError(f"{where}.operations must be a non-empty list")
        for index, operation in enumerate(operations):
            validate_mutation(operation, f"{where}.operations[{index}]", nested=True)
        return

    specifications = {
        "json_remove": ({"kind", "pointer"}, set()),
        "json_set": ({"kind", "pointer", "new"}, {"old"}),
        "json_array_remove": (
            {"kind", "pointer", "index", "counter_pointer"}, set()
        ),
        "json_array_duplicate": (
            {"kind", "pointer", "index", "counter_pointer", "overrides"}, set()
        ),
        "json_bulk_set": (
            {"kind", "pointer", "min_items", "fields"}, set()
        ),
        "text_replace_exact": ({"kind", "old", "new", "count"}, set()),
        "text_append": ({"kind", "text"}, set()),
        "text_move_after": ({"kind", "source", "anchor", "separator"}, set()),
        "swap_exact_blocks": ({"kind", "first", "second"}, set()),
    }
    if kind not in specifications:
        raise RecipeError(f"{where}.kind {kind!r} is unsupported")
    required, optional = specifications[kind]
    ensure_exact_keys(mutation, required, optional, where=where)

    if kind.startswith("json_"):
        validate_pointer(mutation["pointer"], f"{where}.pointer")
    if kind in {"json_array_remove", "json_array_duplicate"}:
        validate_pointer(mutation["counter_pointer"], f"{where}.counter_pointer")
        if not true_int(mutation["index"]):
            raise RecipeError(f"{where}.index must be an int")
    if kind == "json_array_duplicate" and not isinstance(mutation["overrides"], dict):
        raise RecipeError(f"{where}.overrides must be an object")
    if kind == "json_bulk_set":
        if not true_int(mutation["min_items"]) or mutation["min_items"] <= 0:
            raise RecipeError(f"{where}.min_items must be a positive int")
        if not isinstance(mutation["fields"], dict) or not mutation["fields"] \
                or not all(isinstance(key, str) and key for key in mutation["fields"]):
            raise RecipeError(f"{where}.fields must be a non-empty string-keyed object")
    if kind == "text_replace_exact":
        require_string(mutation["old"], f"{where}.old")
        if not isinstance(mutation["new"], str) or mutation["new"] == mutation["old"]:
            raise RecipeError(f"{where}.new must be a different string")
        if not true_int(mutation["count"]) or mutation["count"] <= 0:
            raise RecipeError(f"{where}.count must be a positive int")
    elif kind == "text_append":
        require_string(mutation["text"], f"{where}.text")
    elif kind == "text_move_after":
        for field in ("source", "anchor"):
            require_string(mutation[field], f"{where}.{field}")
        if not isinstance(mutation["separator"], str):
            raise RecipeError(f"{where}.separator must be a string")
    elif kind == "swap_exact_blocks":
        for field in ("first", "second"):
            require_string(mutation[field], f"{where}.{field}")
        if mutation["first"] == mutation["second"]:
            raise RecipeError(f"{where} blocks must differ")


def validate_detector(detector, case_id):
    ensure_exact_keys(
        detector,
        {"argv", "timeout_s", "execution_markers", "infrastructure_markers",
         "baseline_exit_codes", "accept_exit_codes", "accept_output",
         "reject_exit_codes", "reject_output", "output_relation"},
        where=f"detector {case_id}",
    )
    require_string_list(detector["argv"], f"detector {case_id}.argv", nonempty=True)
    if not true_int(detector["timeout_s"]) or detector["timeout_s"] <= 0:
        raise RecipeError(f"detector {case_id}.timeout_s must be a positive int")
    require_string_list(
        detector["execution_markers"], f"detector {case_id}.execution_markers",
        nonempty=True,
    )
    require_string_list(
        detector["infrastructure_markers"],
        f"detector {case_id}.infrastructure_markers", nonempty=True,
    )
    require_exit_codes(
        detector["baseline_exit_codes"], f"detector {case_id}.baseline_exit_codes",
        nonempty=True,
    )
    require_exit_codes(detector["accept_exit_codes"],
                       f"detector {case_id}.accept_exit_codes")
    require_exit_codes(detector["reject_exit_codes"],
                       f"detector {case_id}.reject_exit_codes")
    if not detector["accept_exit_codes"] and not detector["reject_exit_codes"]:
        raise RecipeError(f"detector {case_id} has no accept or reject outcome")
    if set(detector["accept_exit_codes"]) & set(detector["reject_exit_codes"]):
        raise RecipeError(f"detector {case_id} accept/reject exit codes overlap")
    require_string_list(detector["accept_output"],
                        f"detector {case_id}.accept_output",
                        nonempty=bool(detector["accept_exit_codes"]))
    require_string_list(detector["reject_output"],
                        f"detector {case_id}.reject_output",
                        nonempty=bool(detector["reject_exit_codes"]))
    if detector["output_relation"] not in {"any", "equal", "different"}:
        raise RecipeError(f"invalid output_relation in {case_id}")


def validate_binding(binding, label):
    ensure_exact_keys(binding, {"path", "version", "sha256"}, where=label)
    require_relative_path(binding["path"], f"{label}.path")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", str(binding["version"])):
        raise RecipeError(f"{label}.version must be semantic version text")
    require_digest(binding["sha256"], f"{label}.sha256")


def validate_manifest(manifest):
    ensure_exact_keys(
        manifest,
        {"document", "version", "manifest_id", "semantic_model",
         "acceptance_contract", "subject_binding", "environment",
         "c9_rebinding_policy", "operators", "report_schema"},
        where="manifest",
    )
    if manifest["document"] != "FTRO Phase-0 executable audit manifest":
        raise RecipeError("unexpected manifest document type")
    if manifest["version"] != "1.0.1":
        raise RecipeError("runner supports manifest version 1.0.1 only")
    require_string(manifest["manifest_id"], "manifest.manifest_id")
    validate_binding(manifest["semantic_model"], "semantic_model")
    validate_binding(manifest["acceptance_contract"], "acceptance_contract")

    ensure_exact_keys(
        manifest["subject_binding"], {"kind", "required_ancestor", "note"},
        where="subject_binding",
    )
    if manifest["subject_binding"]["kind"] != "manifest_carrier_commit":
        raise RecipeError("subject_binding.kind must be manifest_carrier_commit")
    if not isinstance(manifest["subject_binding"]["required_ancestor"], str) or \
            COMMIT_RE.fullmatch(manifest["subject_binding"]["required_ancestor"]) is None:
        raise RecipeError("subject_binding.required_ancestor must be a full commit id")
    if manifest["subject_binding"]["required_ancestor"] != C9_REQUIRED_ANCESTOR:
        raise RecipeError("subject_binding.required_ancestor differs from the frozen baseline")
    require_string(manifest["subject_binding"]["note"], "subject_binding.note")

    ensure_exact_keys(manifest["environment"], {"network", "isolation", "variables"},
                      where="environment")
    if manifest["environment"]["network"] != "not_used_by_registered_detectors":
        raise RecipeError(
            "environment.network must say 'not_used_by_registered_detectors'; "
            "this runner does not enforce OS-level network isolation"
        )
    require_string(manifest["environment"]["isolation"], "environment.isolation")
    ensure_exact_keys(
        manifest["environment"]["variables"],
        {"LC_ALL", "TZ", "PYTHONHASHSEED", "PYTHONNOUSERSITE"},
        where="environment.variables",
    )
    expected_variables = {
        "LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    if manifest["environment"]["variables"] != expected_variables:
        raise RecipeError(f"environment.variables must equal {expected_variables!r}")

    c9 = manifest["c9_rebinding_policy"]
    ensure_exact_keys(
        c9,
        {"version", "live_run_precedes_qualifying_audits",
         "live_rerun_required_after_changes_to", "why_tests_rebind",
         "rebind_without_provider_rerun_only_for", "default_for_unclassified_change",
         "provider_failure_fields", "failure_classes"},
        where="c9_rebinding_policy",
    )
    if c9["live_run_precedes_qualifying_audits"] is not True:
        raise RecipeError("c9_rebinding_policy must require C9 before qualification")
    for field in ("live_rerun_required_after_changes_to",
                  "rebind_without_provider_rerun_only_for", "provider_failure_fields",
                  "failure_classes"):
        require_string_list(c9[field], f"c9_rebinding_policy.{field}", nonempty=True)
    for field in ("version", "why_tests_rebind", "default_for_unclassified_change"):
        require_string(c9[field], f"c9_rebinding_policy.{field}")

    ensure_exact_keys(
        manifest["report_schema"],
        {"version", "observations", "not_executed_is_always_failure",
         "atomic_create_no_overwrite"}, where="report_schema",
    )
    if manifest["report_schema"]["version"] != "1.0.0" or \
            manifest["report_schema"]["observations"] != [
                "detected", "not_detected", "not_executed"
            ] or manifest["report_schema"]["not_executed_is_always_failure"] is not True \
            or manifest["report_schema"]["atomic_create_no_overwrite"] is not True:
        raise RecipeError("report_schema does not equal the frozen v1.0.0 declaration")
    if not isinstance(manifest["operators"], list):
        raise RecipeError("operators must be a list")

    operator_ids, case_ids = [], []
    for operator in manifest["operators"]:
        ensure_exact_keys(operator, {"id", "description", "cases"}, where="operator")
        require_string(operator["id"], "operator.id")
        require_string(operator["description"], f"operator {operator['id']}.description")
        operator_ids.append(operator["id"])
        if not isinstance(operator["cases"], list) or not operator["cases"]:
            raise RecipeError(f"{operator['id']} has no cases")
        for case in operator["cases"]:
            ensure_exact_keys(
                case,
                {"id", "target", "target_before_sha256", "mutation", "detector",
                 "expected_observation", "expected_disposition"},
                where=f"case in {operator['id']}",
            )
            if not case["id"].startswith(operator["id"] + "."):
                raise RecipeError(f"case {case['id']} is outside operator {operator['id']}")
            require_relative_path(case["target"], f"case {case['id']}.target")
            require_digest(case["target_before_sha256"],
                           f"case {case['id']}.target_before_sha256")
            validate_mutation(case["mutation"], f"case {case['id']}.mutation")
            validate_detector(case["detector"], case["id"])
            case_ids.append(case["id"])
    if operator_ids != list(EXPECTED_OPERATOR_ORDER):
        raise RecipeError(f"operator population differs: {operator_ids}")
    if len(case_ids) != len(set(case_ids)):
        raise RecipeError("duplicate case id")
    if set(case_ids) != set(EXPECTED_CASES) or len(case_ids) != len(EXPECTED_CASES):
        missing = sorted(set(EXPECTED_CASES) - set(case_ids))
        unknown = sorted(set(case_ids) - set(EXPECTED_CASES))
        raise RecipeError(f"case population differs; missing={missing}, unknown={unknown}")
    for operator in manifest["operators"]:
        for case in operator["cases"]:
            expected = EXPECTED_CASES[case["id"]]
            observed = (operator["id"], case["expected_observation"],
                        case["expected_disposition"])
            if observed != expected:
                raise RecipeError(
                    f"case mapping differs for {case['id']}: {observed!r} != {expected!r}"
                )
    return case_ids


def tree_files(root):
    """Return a complete non-.git file map for reset proof.

    Bytes alone are not a reset: changing 0644 to 0755 changes the Git object state even
    when the content digest is identical.  Record filesystem type and permission mode as
    well as content (or symlink destination).
    """
    files = {}
    for path in sorted(Path(root).rglob("*")):
        if ".git" in path.relative_to(root).parts:
            continue
        rel = path.relative_to(root).as_posix()
        status = path.lstat()
        mode = stat.S_IMODE(status.st_mode)
        if stat.S_ISLNK(status.st_mode):
            files[rel] = {
                "type": "symlink", "mode": mode, "target": os.readlink(path),
            }
        elif stat.S_ISREG(status.st_mode):
            files[rel] = {
                "type": "file", "mode": mode, "sha256": sha256_file(path),
            }
        elif stat.S_ISDIR(status.st_mode):
            files[rel] = {"type": "directory", "mode": mode}
        else:
            files[rel] = {"type": "special", "mode": mode}
    return files


def tree_fingerprint(files):
    return sha256_bytes(canonical(files))


def remove_untracked(root, baseline_files):
    root = Path(root).resolve()
    for path in sorted(root.rglob("*"), reverse=True):
        rel_parts = path.relative_to(root).parts
        if ".git" in rel_parts:
            continue
        rel = path.relative_to(root).as_posix()
        status = path.lstat()
        if not stat.S_ISDIR(status.st_mode):
            if rel not in baseline_files:
                path.unlink()
        else:
            try:
                path.rmdir()
            except OSError:
                pass


def initialize_export(source_root, destination, environment):
    """Export HEAD and prove local Git initialization did not change its file tree."""
    archived = git(
        source_root, "archive", "--format=tar", "HEAD", text=False,
        environment=environment,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archived), mode="r:") as archive:
        archive.extractall(destination, filter="data")
    before_files = tree_files(destination)
    before_fingerprint = tree_fingerprint(before_files)

    hooks = environment.get("FTRO_EMPTY_GIT_HOOKS")
    if not hooks or not Path(hooks).is_dir() or any(Path(hooks).iterdir()):
        raise RecipeError("isolated empty Git hooks directory is absent or non-empty")
    env = sanitized_environment({
        **environment,
        "GIT_AUTHOR_NAME": "FTRO audit",
        "GIT_AUTHOR_EMAIL": "audit@invalid",
        "GIT_COMMITTER_NAME": "FTRO audit",
        "GIT_COMMITTER_EMAIL": "audit@invalid",
    })
    if CONTROLLER_GIT is None:
        select_controller_git()
    git_prefix = [CONTROLLER_GIT, "--no-replace-objects", "-c",
                  "core.fsmonitor=false", "-c", f"core.hooksPath={hooks}"]
    for suffix in (["init", "--quiet", "-b", "audit-baseline"],
                   ["add", "-A"],
                   ["commit", "--quiet", "-m", "immutable audit baseline"]):
        argv = [*git_prefix, *suffix]
        result = subprocess.run(argv, cwd=destination, capture_output=True, text=True,
                                timeout=120, env=env)
        if result.returncode:
            raise RecipeError(f"failed to initialize isolated Git baseline: {result.stderr}")
    after_files = tree_files(destination)
    after_fingerprint = tree_fingerprint(after_files)
    if after_files != before_files or after_fingerprint != before_fingerprint:
        raise RecipeError(
            "isolated Git initialization changed the exported candidate tree"
        )
    return {
        "archive_tree_sha256": before_fingerprint,
        "initialized_tree_sha256": after_fingerprint,
        "unchanged": True,
        "git_config_global": env["GIT_CONFIG_GLOBAL"],
        "git_config_nosystem": env["GIT_CONFIG_NOSYSTEM"],
        "git_attr_nosystem": env["GIT_ATTR_NOSYSTEM"],
        "git_no_replace_objects": env["GIT_NO_REPLACE_OBJECTS"],
        "hooks_path": hooks,
        "home": env["HOME"],
    }


def pointer_parent(document, pointer):
    if not isinstance(pointer, list) or not pointer:
        raise RecipeError("JSON pointer must be a non-empty array")
    current = document
    for part in pointer[:-1]:
        try:
            current = current[part]
        except (KeyError, IndexError, TypeError) as exc:
            raise RecipeError(f"JSON pointer does not exist: {pointer}") from exc
    return current, pointer[-1]


def set_counter_to_length(document, counter_pointer, array_pointer):
    array_parent, array_key = pointer_parent(document, array_pointer)
    counter_parent, counter_key = pointer_parent(document, counter_pointer)
    array = array_parent[array_key]
    if not isinstance(array, list):
        raise RecipeError(f"counter source is not a list: {array_pointer}")
    counter_parent[counter_key] = len(array)


def apply_json_mutation(path, mutation):
    document = load_json(path)
    kind = mutation["kind"]
    operations = mutation.get("operations") if kind == "composite" else [mutation]
    if kind == "composite" and not isinstance(operations, list):
        raise RecipeError("composite operations must be a list")

    for operation in operations:
        op_kind = operation["kind"]
        if op_kind == "json_remove":
            parent, key = pointer_parent(document, operation["pointer"])
            if key not in parent if isinstance(parent, dict) else not (0 <= key < len(parent)):
                raise RecipeError(f"remove pointer absent: {operation['pointer']}")
            del parent[key]
        elif op_kind == "json_set":
            parent, key = pointer_parent(document, operation["pointer"])
            try:
                old = parent[key]
            except (KeyError, IndexError, TypeError) as exc:
                raise RecipeError(f"set pointer absent: {operation['pointer']}") from exc
            if "old" in operation and old != operation["old"]:
                raise RecipeError(f"old JSON value differs at {operation['pointer']}")
            parent[key] = operation["new"]
        elif op_kind == "json_array_remove":
            parent, key = pointer_parent(document, operation["pointer"])
            array = parent[key]
            if not isinstance(array, list) or not array:
                raise RecipeError("array-remove target is empty or not a list")
            index = operation["index"]
            del array[index]
            set_counter_to_length(document, operation["counter_pointer"], operation["pointer"])
        elif op_kind == "json_array_duplicate":
            parent, key = pointer_parent(document, operation["pointer"])
            array = parent[key]
            if not isinstance(array, list) or not array:
                raise RecipeError("array-duplicate target is empty or not a list")
            item = copy.deepcopy(array[operation["index"]])
            item.update(operation.get("overrides", {}))
            array.append(item)
            set_counter_to_length(document, operation["counter_pointer"], operation["pointer"])
        elif op_kind == "json_bulk_set":
            parent, key = pointer_parent(document, operation["pointer"])
            array = parent[key]
            if not isinstance(array, list) or len(array) < operation["min_items"]:
                raise RecipeError("bulk-set target has too few items")
            for item in array:
                if not isinstance(item, dict):
                    raise RecipeError("bulk-set item is not an object")
                for field, value in operation["fields"].items():
                    if field not in item:
                        raise RecipeError(f"bulk-set field {field!r} absent")
                    item[field] = value
        else:
            raise RecipeError(f"unsupported JSON mutation {op_kind!r}")
    Path(path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def replace_exact(text, old, new, count):
    observed = text.count(old)
    if observed != count:
        raise RecipeError(f"text match count {observed}, expected {count}")
    return text.replace(old, new)


def apply_text_mutation(path, mutation):
    text = Path(path).read_text(encoding="utf-8")
    kind = mutation["kind"]
    if kind == "text_replace_exact":
        text = replace_exact(text, mutation["old"], mutation["new"], mutation["count"])
    elif kind == "text_append":
        text += mutation["text"]
    elif kind == "text_move_after":
        source, anchor = mutation["source"], mutation["anchor"]
        if text.count(source) != 1 or text.count(anchor) != 1:
            raise RecipeError("move source or anchor is not unique")
        if source in anchor:
            raise RecipeError("move anchor contains source")
        text = text.replace(source, "", 1)
        at = text.index(anchor) + len(anchor)
        text = text[:at] + mutation.get("separator", "\n") + source + text[at:]
    elif kind == "swap_exact_blocks":
        first, second = mutation["first"], mutation["second"]
        if text.count(first) != 1 or text.count(second) != 1:
            raise RecipeError("swap blocks are not unique")
        token = "__FTRO_AUDIT_SWAP_TOKEN__"
        if token in text:
            raise RecipeError("swap token unexpectedly present")
        text = text.replace(first, token, 1).replace(second, first, 1).replace(token, second, 1)
    else:
        raise RecipeError(f"unsupported text mutation {kind!r}")
    Path(path).write_text(text, encoding="utf-8")


def apply_mutation(work, case, environment=None):
    target = Path(work, case["target"])
    if not target.is_file():
        raise RecipeError(f"mutation target absent: {case['target']}")
    before = sha256_file(target)
    if before != case["target_before_sha256"]:
        raise RecipeError(f"target digest {before} != frozen "
                          f"{case['target_before_sha256']}")
    mutation = case["mutation"]
    kind = mutation.get("kind")
    if kind.startswith("json_") or kind == "composite":
        apply_json_mutation(target, mutation)
    elif kind.startswith("text_") or kind == "swap_exact_blocks":
        apply_text_mutation(target, mutation)
    else:
        raise RecipeError(f"unknown mutation kind {kind!r}")
    after = sha256_file(target)
    if after == before:
        raise RecipeError("not_applied: post-mutation digest equals pre-mutation digest")
    changed = sorted(git(
        work, "diff", "--name-only", environment=environment,
    ).stdout.splitlines())
    if changed != [case["target"]]:
        raise RecipeError(f"mutation changed paths {changed}, expected {[case['target']]}")
    diff = git(work, "diff", "--", case["target"], environment=environment).stdout
    if not diff:
        raise RecipeError("mutation has no Git diff")
    return {
        "target": case["target"],
        "before_sha256": before,
        "after_sha256": after,
        "diff_sha256": sha256_bytes(diff.encode()),
        "diff_excerpt": diff[:4000],
    }


def command_evidence(argv, cwd, timeout_s, environment):
    started_utc = utc_now()
    began = time.monotonic()
    execution_environment = sanitized_environment(environment)
    requested_executable = argv[0]
    executable = shutil.which(requested_executable,
                              path=execution_environment.get("PATH"))
    if executable is None:
        raise RecipeError(f"detector executable is not resolvable: {requested_executable!r}")
    executable = Path(executable).resolve()
    if not executable.is_file() or not executable.is_absolute():
        raise RecipeError(f"detector executable is not an absolute regular file: {executable}")
    if requested_executable == "python3" \
            and executable != Path(sys.executable).resolve():
        raise RecipeError(
            f"detector python3 {executable} differs from runner {Path(sys.executable).resolve()}"
        )
    executable_before = sha256_file(executable)
    executed_argv = [str(executable), *argv[1:]]
    try:
        result = subprocess.run(
            executed_argv, cwd=cwd, capture_output=True, timeout=timeout_s,
            stdin=subprocess.DEVNULL, env=execution_environment,
        )
        timed_out = False
        exit_code = result.returncode
        stdout, stderr = result.stdout, result.stderr
        error = None
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        error = f"timeout after {timeout_s}s"
    except OSError as exc:
        timed_out = False
        exit_code = None
        stdout, stderr = b"", b""
        error = f"{type(exc).__name__}: {exc}"
    try:
        executable_after = sha256_file(executable)
    except OSError:
        executable_after = None
    return {
        "argv": argv,
        "executed_argv": executed_argv,
        "stdin": "DEVNULL",
        "cwd": str(Path(cwd).resolve()),
        "environment": dict(sorted(execution_environment.items())),
        "executable_realpath": str(executable),
        "executable_sha256": executable_before,
        "executable_stable": executable_after == executable_before,
        "started_utc": started_utc,
        "ended_utc": utc_now(),
        "duration_s": round(time.monotonic() - began, 6),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "spawn_error": error,
        "stdout_n_bytes": len(stdout),
        "stderr_n_bytes": len(stderr),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_excerpt": stdout.decode(errors="replace")[-4000:],
        "stderr_excerpt": stderr.decode(errors="replace")[-4000:],
        "stdout_text": stdout.decode(errors="replace"),
        "stderr_text": stderr.decode(errors="replace"),
        "_combined": (stdout + b"\n" + stderr).decode(errors="replace"),
    }


def public_command(record):
    return {key: value for key, value in record.items() if not key.startswith("_")}


def execution_proved(record, detector):
    if record["spawn_error"] or record["timed_out"]:
        return False, record["spawn_error"] or "timeout"
    if record.get("executable_stable") is not True:
        return False, "detector executable changed or vanished during execution"
    combined = record["_combined"]
    missing = [marker for marker in detector["execution_markers"] if marker not in combined]
    infrastructure = [marker for marker in detector["infrastructure_markers"]
                      if marker in combined]
    if missing:
        return False, f"execution markers absent: {missing}"
    if infrastructure:
        return False, f"infrastructure markers present: {infrastructure}"
    return True, None


def objective_observation(record, detector):
    """Classify what the detector did without consulting the registered expectation."""
    combined = record["_combined"]
    accepted = record["exit_code"] in detector["accept_exit_codes"] and all(
        marker in combined for marker in detector["accept_output"]
    )
    rejected = record["exit_code"] in detector["reject_exit_codes"] and all(
        marker in combined for marker in detector["reject_output"]
    )
    if accepted == rejected:
        if accepted:
            raise RecipeError("detector outcome is ambiguous: both accept and reject matched")
        raise RecipeError("detector outcome is unclassified: neither accept nor reject matched")
    return ("not_detected" if accepted else "detected"), {
        "accepted": accepted,
        "rejected": rejected,
    }


def run_case(source_root, manifest, operator_id, case, environment):
    result = {
        "operator_id": operator_id,
        "case_id": case["id"],
        "expected_observation": case["expected_observation"],
        "expected_disposition": case["expected_disposition"],
        "observation": "not_executed",
        "verdict": "fail",
        "reason": None,
        "mutation": None,
        "export_initialization": None,
        "baseline_command": None,
        "mutated_command": None,
        "objective_oracle": None,
        "baseline_tree_sha256": None,
        "reset_tree_sha256": None,
        "reset_verified": False,
    }
    with tempfile.TemporaryDirectory(prefix="ftro-audit-case-") as temporary:
        work = Path(temporary, "candidate")
        home = Path(temporary, "home")
        work.mkdir()
        try:
            case_environment = isolated_case_environment(environment, home)
            result["export_initialization"] = initialize_export(
                source_root, work, case_environment,
            )
            baseline_files = tree_files(work)
            baseline_fingerprint = tree_fingerprint(baseline_files)
            result["baseline_tree_sha256"] = baseline_fingerprint
            target = Path(work, case["target"])
            original = target.read_bytes()

            detector = case["detector"]
            baseline = command_evidence(detector["argv"], work,
                                        detector["timeout_s"], case_environment)
            result["baseline_command"] = public_command(baseline)
            baseline_ran, why = execution_proved(baseline, detector)
            if not baseline_ran:
                raise RecipeError(f"baseline detector did not execute: {why}")
            if baseline["exit_code"] not in detector["baseline_exit_codes"]:
                raise RecipeError(f"baseline exit {baseline['exit_code']} not in "
                                  f"{detector['baseline_exit_codes']}")
            remove_untracked(work, baseline_files)
            if tree_fingerprint(tree_files(work)) != baseline_fingerprint:
                raise RecipeError("baseline detector changed the candidate tree")

            result["mutation"] = apply_mutation(work, case, case_environment)
            mutated = command_evidence(detector["argv"], work,
                                       detector["timeout_s"], case_environment)
            result["mutated_command"] = public_command(mutated)
            mutated_ran, why = execution_proved(mutated, detector)
            if not mutated_ran:
                raise RecipeError(f"mutated detector did not execute: {why}")

            relation = detector["output_relation"]
            relation_matched = (
                relation == "any"
                or (relation == "equal" and baseline["_combined"] == mutated["_combined"])
                or (relation == "different" and baseline["_combined"] != mutated["_combined"])
            )
            result["observation"], objective = objective_observation(mutated, detector)
            result["objective_oracle"] = {
                **objective, "output_relation_matched": relation_matched,
            }
            if result["observation"] == case["expected_observation"] and relation_matched:
                result["verdict"] = "pass"
                result["reason"] = "registered observation reproduced"
            else:
                result["reason"] = (
                    f"oracle mismatch: observed={result['observation']}, "
                    f"expected={case['expected_observation']}, "
                    f"relation_matched={relation_matched}"
                )
        except Exception as exc:  # every incomplete recipe remains visible in the report
            result["observation"] = "not_executed"
            result["verdict"] = "fail"
            result["reason"] = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                target = Path(work, case["target"])
                if "original" in locals() and target.parent.exists():
                    target.write_bytes(original)
                if "baseline_files" in locals():
                    remove_untracked(work, baseline_files)
                    result["reset_tree_sha256"] = tree_fingerprint(tree_files(work))
                    result["reset_verified"] = (
                        result["reset_tree_sha256"] == baseline_fingerprint
                    )
            except Exception as exc:
                result["reset_verified"] = False
                result["reason"] = (result["reason"] or "") + \
                    f"; reset proof failed: {type(exc).__name__}: {exc}"
            if not result["reset_verified"]:
                result["observation"] = "not_executed"
                result["verdict"] = "fail"
    return result


def source_state(root, manifest_path, runner_path, required_ancestor):
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout
    if status:
        raise RecipeError("controller checkout is not clean:\n" + status[:2000])
    commit = git(root, "rev-parse", "HEAD").stdout.strip()
    tree = git(root, "rev-parse", "HEAD^{tree}").stdout.strip()
    if git(root, "symbolic-ref", "-q", "HEAD", ok=(0, 1)).returncode == 0:
        raise RecipeError("audit execution requires a detached checkout of the carrier commit")
    if git(root, "merge-base", "--is-ancestor", required_ancestor, commit,
           ok=(0, 1)).returncode != 0:
        raise RecipeError(f"subject {commit} does not descend from {required_ancestor}")
    for path in (manifest_path, runner_path):
        rel = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
        committed = git(root, "show", f"HEAD:{rel}", text=False).stdout
        if committed != Path(path).read_bytes():
            raise RecipeError(f"{rel} differs from the carrier commit")
    return {"commit": commit, "tree": tree, "clean": True, "detached_head": True,
            "checkout_realpath": str(Path(root).resolve())}


def tracked_tree_evidence(root):
    rows = []
    for relative in git(root, "ls-files").stdout.splitlines():
        path = Path(root, relative)
        if not path.is_file():
            raise RecipeError(f"tracked C9 input is not a file: {relative}")
        rows.append({
            "path": relative,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    rows.sort(key=lambda row: row["path"])
    return rows, sha256_bytes(canonical(rows))


def validate_c9_report(path, source, bound_documents, root, *, before_utc=None):
    raw = Path(path).read_bytes()
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecipeError(f"C9 report is unreadable: {exc}") from exc
    expected_contract = bound_documents["acceptance_contract"]
    context = {
        "commit": source["commit"],
        "tree": source["tree"],
        "required_ancestor": C9_REQUIRED_ANCESTOR,
        "contract_id": "FTRO-ACC-001",
        "contract_version": expected_contract["version"],
        "before_utc": before_utc,
        "output_view": "carrier",
        "git_command": CONTROLLER_GIT,
    }
    try:
        evidence = c9_contract.assert_success_report(report, root, context)
    except c9_contract.C9ContractError as exc:
        raise RecipeError(str(exc)) from exc
    evidence.update({
        "sha256": sha256_bytes(raw),
    })
    return evidence


def verify_bound_documents(root, manifest):
    evidence = {}
    for label in ("semantic_model", "acceptance_contract"):
        binding = manifest[label]
        ensure_exact_keys(binding, {"path", "version", "sha256"}, where=label)
        path = Path(root, binding["path"])
        if not path.is_file():
            raise RecipeError(f"bound {label} is absent: {binding['path']}")
        observed = sha256_file(path)
        if observed != binding["sha256"]:
            raise RecipeError(f"bound {label} digest {observed} != {binding['sha256']}")
        evidence[label] = dict(binding)
    return evidence


COMMAND_RECORD_KEYS = {
    "argv", "executed_argv", "stdin", "cwd", "environment", "executable_realpath",
    "executable_sha256", "executable_stable", "started_utc", "ended_utc", "duration_s",
    "exit_code", "timed_out", "spawn_error", "stdout_n_bytes", "stderr_n_bytes",
    "stdout_sha256", "stderr_sha256", "stdout_excerpt", "stderr_excerpt", "stdout_text",
    "stderr_text",
}
RESULT_RECORD_KEYS = {
    "operator_id", "case_id", "expected_observation", "expected_disposition",
    "observation", "verdict", "reason", "mutation", "export_initialization",
    "baseline_command", "mutated_command", "objective_oracle", "baseline_tree_sha256",
    "reset_tree_sha256", "reset_verified",
}
REPORT_RECORD_KEYS = {
    "document", "schema_version", "run_id", "mode", "qualifying", "started_utc",
    "ended_utc", "subject", "bound_documents", "manifest_id", "manifest_sha256",
    "runner_sha256", "c9_evidence", "calibration_evidence", "execution_policy", "case_population",
    "n_cases", "n_detected", "n_not_detected", "n_not_executed", "n_failed_cases",
    "failed_cases", "overall_status", "results",
}


def validate_command_record(record, detector, *, baseline, where):
    ensure_exact_keys(record, COMMAND_RECORD_KEYS, where=where)
    require_string_list(record["argv"], f"{where}.argv", nonempty=True)
    if record["argv"] != detector["argv"]:
        raise RecipeError(f"{where}.argv differs from the frozen detector")
    require_string_list(record["executed_argv"], f"{where}.executed_argv", nonempty=True)
    if record["executed_argv"][1:] != record["argv"][1:]:
        raise RecipeError(f"{where}.executed_argv arguments differ from the frozen detector")
    if record["stdin"] != "DEVNULL":
        raise RecipeError(f"{where}.stdin was not disabled")
    require_string(record["cwd"], f"{where}.cwd")
    if not Path(record["cwd"]).is_absolute():
        raise RecipeError(f"{where}.cwd must be absolute")
    if not isinstance(record["environment"], dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in record["environment"].items()):
        raise RecipeError(f"{where}.environment must be a string map")
    allowed_environment = set(SAFE_INHERITED_ENV) | {
        "LC_ALL", "TZ", "PYTHONHASHSEED", "PYTHONNOUSERSITE",
        "XDG_CONFIG_HOME", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM",
        "GIT_ATTR_NOSYSTEM", "GIT_NO_REPLACE_OBJECTS", "FTRO_EMPTY_GIT_HOOKS",
    }
    unknown_environment = set(record["environment"]) - allowed_environment
    if unknown_environment:
        raise RecipeError(f"{where}.environment has unsafe keys: "
                          f"{sorted(unknown_environment)}")
    for key, expected in {
            "LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1"}.items():
        if record["environment"].get(key) != expected:
            raise RecipeError(f"{where}.environment {key} differs")
    validate_safe_path(record["environment"].get("PATH"), f"{where}.environment PATH")
    for key in ("HOME", "XDG_CONFIG_HOME", "FTRO_EMPTY_GIT_HOOKS"):
        value = record["environment"].get(key)
        require_string(value, f"{where}.environment {key}")
        if not Path(value).is_absolute():
            raise RecipeError(f"{where}.environment {key} must be absolute")
    require_string(record["executable_realpath"], f"{where}.executable_realpath")
    executable = Path(record["executable_realpath"])
    if not executable.is_absolute() or record["executed_argv"][0] != str(executable):
        raise RecipeError(f"{where} did not execute its recorded absolute executable")
    require_digest(record["executable_sha256"], f"{where}.executable_sha256")
    if record["executable_stable"] is not True:
        raise RecipeError(f"{where}.executable_stable is not true")
    if not executable.is_file() or sha256_file(executable) != record["executable_sha256"]:
        raise RecipeError(f"{where} executable bytes no longer match the recorded digest")
    if record["argv"][0] == "python3" \
            and executable.resolve() != Path(sys.executable).resolve():
        raise RecipeError(f"{where} did not use the qualification checker's Python")
    for field in ("started_utc", "ended_utc"):
        require_string(record[field], f"{where}.{field}")
    command_started = parse_utc(record["started_utc"], f"{where}.started_utc")
    command_ended = parse_utc(record["ended_utc"], f"{where}.ended_utc")
    if command_ended < command_started:
        raise RecipeError(f"{where} ends before it starts")
    if isinstance(record["duration_s"], bool) or not isinstance(record["duration_s"],
                                                                 (int, float)) \
            or record["duration_s"] < 0:
        raise RecipeError(f"{where}.duration_s must be non-negative")
    if not true_int(record["exit_code"]):
        raise RecipeError(f"{where}.exit_code must be an int")
    if record["timed_out"] is not False or record["spawn_error"] is not None:
        raise RecipeError(f"{where} did not complete normally")
    for field in ("stdout_n_bytes", "stderr_n_bytes"):
        if not true_int(record[field]) or record[field] < 0:
            raise RecipeError(f"{where}.{field} must be a non-negative int")
    for field in ("stdout_sha256", "stderr_sha256"):
        require_digest(record[field], f"{where}.{field}")
    for field in ("stdout_excerpt", "stderr_excerpt"):
        if not isinstance(record[field], str):
            raise RecipeError(f"{where}.{field} must be a string")

    for stream in ("stdout", "stderr"):
        text_value = record[f"{stream}_text"]
        if not isinstance(text_value, str):
            raise RecipeError(f"{where}.{stream}_text must be a string")
        body = text_value.encode()
        if len(body) != record[f"{stream}_n_bytes"] \
                or sha256_bytes(body) != record[f"{stream}_sha256"] \
                or text_value[-4000:] != record[f"{stream}_excerpt"]:
            raise RecipeError(f"{where}.{stream} content/digest/excerpt differs")

    replay = dict(record)
    replay["_combined"] = record["stdout_text"] + "\n" + record["stderr_text"]
    ran, reason = execution_proved(replay, detector)
    if not ran:
        raise RecipeError(f"{where} lacks execution proof: {reason}")
    if baseline:
        if record["exit_code"] not in detector["baseline_exit_codes"]:
            raise RecipeError(f"{where} baseline exit is not registered")
        return None
    observation, objective = objective_observation(replay, detector)
    return observation, objective


def validate_mutation_record(record, case, where):
    ensure_exact_keys(
        record,
        {"target", "before_sha256", "after_sha256", "diff_sha256", "diff_excerpt"},
        where=where,
    )
    if record["target"] != case["target"]:
        raise RecipeError(f"{where}.target differs from the frozen case")
    for field in ("before_sha256", "after_sha256", "diff_sha256"):
        require_digest(record[field], f"{where}.{field}")
    if record["before_sha256"] != case["target_before_sha256"]:
        raise RecipeError(f"{where}.before_sha256 differs from the frozen case")
    if record["after_sha256"] == record["before_sha256"]:
        raise RecipeError(f"{where} records no byte change")
    require_string(record["diff_excerpt"], f"{where}.diff_excerpt")


def validate_export_initialization(record, where):
    ensure_exact_keys(
        record,
        {"archive_tree_sha256", "initialized_tree_sha256", "unchanged",
         "git_config_global", "git_config_nosystem", "git_attr_nosystem",
         "git_no_replace_objects", "hooks_path", "home"},
        where=where,
    )
    for field in ("archive_tree_sha256", "initialized_tree_sha256"):
        require_digest(record[field], f"{where}.{field}")
    if record["archive_tree_sha256"] != record["initialized_tree_sha256"] \
            or record["unchanged"] is not True:
        raise RecipeError(f"{where} does not prove an unchanged exported tree")
    expected = {
        "git_config_global": os.devnull,
        "git_config_nosystem": "1",
        "git_attr_nosystem": "1",
        "git_no_replace_objects": "1",
    }
    for field, value in expected.items():
        if record[field] != value:
            raise RecipeError(f"{where}.{field} differs from the isolation policy")
    for field in ("hooks_path", "home"):
        require_string(record[field], f"{where}.{field}")
        if not Path(record[field]).is_absolute():
            raise RecipeError(f"{where}.{field} must be absolute")


def validate_result_population(report, manifest, case_population, where="audit report"):
    if report["case_population"] != case_population:
        raise RecipeError(f"{where} case population differs")
    if not isinstance(report["results"], list) \
            or len(report["results"]) != len(case_population):
        raise RecipeError(f"{where} results do not cover the frozen population")

    report_started = parse_utc(report["started_utc"], f"{where}.started_utc")
    report_ended = parse_utc(report["ended_utc"], f"{where}.ended_utc")
    if report_ended < report_started:
        raise RecipeError(f"{where} ends before it starts")

    case_by_id = {
        case["id"]: (operator["id"], case)
        for operator in manifest["operators"] for case in operator["cases"]
    }
    seen = []
    previous_command_end = report_started
    for index, result in enumerate(report["results"]):
        result_where = f"{where}.results[{index}]"
        ensure_exact_keys(result, RESULT_RECORD_KEYS, where=result_where)
        case_id = result["case_id"]
        if case_id not in case_by_id:
            raise RecipeError(f"{result_where} names unknown case {case_id!r}")
        operator_id, case = case_by_id[case_id]
        seen.append(case_id)
        if result["operator_id"] != operator_id \
                or result["expected_observation"] != case["expected_observation"] \
                or result["expected_disposition"] != case["expected_disposition"]:
            raise RecipeError(f"{result_where} case mapping differs")
        validate_export_initialization(
            result["export_initialization"], f"{result_where}.export_initialization",
        )
        validate_mutation_record(result["mutation"], case, f"{result_where}.mutation")
        validate_command_record(result["baseline_command"], case["detector"], baseline=True,
                                where=f"{result_where}.baseline_command")
        observation, objective = validate_command_record(
            result["mutated_command"], case["detector"], baseline=False,
            where=f"{result_where}.mutated_command",
        )
        for field in ("environment", "executable_realpath", "executable_sha256"):
            if result["baseline_command"][field] != result["mutated_command"][field]:
                raise RecipeError(f"{result_where} baseline/mutated {field} differs")
        baseline_started = parse_utc(
            result["baseline_command"]["started_utc"],
            f"{result_where}.baseline_command.started_utc",
        )
        baseline_ended = parse_utc(
            result["baseline_command"]["ended_utc"],
            f"{result_where}.baseline_command.ended_utc",
        )
        mutated_started = parse_utc(
            result["mutated_command"]["started_utc"],
            f"{result_where}.mutated_command.started_utc",
        )
        mutated_ended = parse_utc(
            result["mutated_command"]["ended_utc"],
            f"{result_where}.mutated_command.ended_utc",
        )
        if not (previous_command_end <= baseline_started <= baseline_ended
                <= mutated_started <= mutated_ended <= report_ended):
            raise RecipeError(f"{result_where} command interval/order differs")
        previous_command_end = mutated_ended
        if result["observation"] != observation \
                or result["observation"] != case["expected_observation"]:
            raise RecipeError(f"{result_where} observation is not objectively reproduced")
        ensure_exact_keys(result["objective_oracle"],
                          {"accepted", "rejected", "output_relation_matched"},
                          where=f"{result_where}.objective_oracle")
        baseline_output = result["baseline_command"]["stdout_text"] + "\n" + \
            result["baseline_command"]["stderr_text"]
        mutated_output = result["mutated_command"]["stdout_text"] + "\n" + \
            result["mutated_command"]["stderr_text"]
        relation = case["detector"]["output_relation"]
        relation_matched = (
            relation == "any"
            or (relation == "equal" and baseline_output == mutated_output)
            or (relation == "different" and baseline_output != mutated_output)
        )
        if result["objective_oracle"].get("accepted") is not objective["accepted"] \
                or result["objective_oracle"].get("rejected") is not objective["rejected"] \
                or result["objective_oracle"].get("output_relation_matched") \
                is not relation_matched or not relation_matched:
            raise RecipeError(f"{result_where} objective oracle differs or relation failed")
        for field in ("baseline_tree_sha256", "reset_tree_sha256"):
            require_digest(result[field], f"{result_where}.{field}")
        if result["baseline_tree_sha256"] \
                != result["export_initialization"]["archive_tree_sha256"]:
            raise RecipeError(f"{result_where} baseline is not the exported candidate tree")
        if result["baseline_tree_sha256"] != result["reset_tree_sha256"]:
            raise RecipeError(f"{result_where} reset fingerprint differs from baseline")
        if result["verdict"] != "pass" or result["reset_verified"] is not True:
            raise RecipeError(f"{result_where} did not pass and reset")
        require_string(result["reason"], f"{result_where}.reason")
    if seen != case_population or len(seen) != len(set(seen)):
        raise RecipeError(f"{where} result ordering/population differs")

    observations = {state: sum(item["observation"] == state for item in report["results"])
                    for state in RESULT_STATES}
    failed = [item["case_id"] for item in report["results"] if item["verdict"] != "pass"]
    expected_counts = {
        "n_cases": len(report["results"]),
        "n_detected": observations["detected"],
        "n_not_detected": observations["not_detected"],
        "n_not_executed": observations["not_executed"],
        "n_failed_cases": len(failed),
    }
    for field, expected in expected_counts.items():
        if type(report[field]) is not int or report[field] != expected:
            raise RecipeError(f"{where} {field} is not derived value {expected}")
    if report["failed_cases"] != failed or report["n_not_executed"] != 0 \
            or report["n_failed_cases"] != 0:
        raise RecipeError(f"{where} contains incomplete or failed cases")


def validate_audit_subject(record, source, where):
    ensure_exact_keys(
        record, {"commit", "tree", "clean", "detached_head", "checkout_realpath"},
        where=where,
    )
    if record["commit"] != source["commit"] or record["tree"] != source["tree"]:
        raise RecipeError(f"{where} commit/tree differs")
    if record["clean"] is not True or record["detached_head"] is not True:
        raise RecipeError(f"{where} was not a clean detached checkout")
    require_string(record["checkout_realpath"], f"{where}.checkout_realpath")
    if not Path(record["checkout_realpath"]).is_absolute():
        raise RecipeError(f"{where}.checkout_realpath must be absolute")


def validate_execution_policy(record, manifest, where, *, produced_with=None):
    ensure_exact_keys(
        record,
        {"network", "network_isolation_enforced", "environment_is_sanitized",
         "controller_git"},
        where=where,
    )
    if record["network"] != manifest["environment"]["network"] \
            or record["network_isolation_enforced"] is not False \
            or record["environment_is_sanitized"] is not True:
        raise RecipeError(f"{where} fixed policy fields differ")
    tool = record["controller_git"]
    ensure_exact_keys(
        tool,
        {"invocation_path", "resolved_path", "sha256", "probe_argv",
         "probe_exit_code", "probe_output"},
        where=f"{where}.controller_git",
    )
    for field in ("invocation_path", "resolved_path"):
        require_string(tool[field], f"{where}.controller_git.{field}")
        if not Path(tool[field]).is_absolute():
            raise RecipeError(f"{where}.controller_git.{field} must be absolute")
    if tool["invocation_path"] not in TRUSTED_GIT_CANDIDATES:
        raise RecipeError(f"{where}.controller_git invocation is not a fixed trusted path")
    require_digest(tool["sha256"], f"{where}.controller_git.sha256")
    require_string_list(tool["probe_argv"], f"{where}.controller_git.probe_argv",
                        nonempty=True)
    if tool["probe_argv"] != [tool["invocation_path"], "--no-replace-objects",
                              "--version"] \
            or tool["probe_exit_code"] != 0 \
            or not isinstance(tool["probe_output"], str) \
            or "git version" not in tool["probe_output"].lower():
        raise RecipeError(f"{where}.controller_git probe evidence differs")
    if produced_with is not None and tool != produced_with:
        raise RecipeError(f"{where}.controller_git differs from the producing executable")


def validate_calibration(path, manifest_sha, runner_sha, source, manifest,
                         bound_documents, case_population, c9_evidence,
                         *, before_utc=None):
    """Validate all calibration evidence, not self-asserted headline counters."""
    raw = Path(path).read_bytes()
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecipeError(f"calibration report is unreadable: {exc}") from exc
    ensure_exact_keys(report, REPORT_RECORD_KEYS, where="calibration report")
    if report["document"] != "FTRO Phase-0 audit execution report" \
            or report["schema_version"] != manifest["report_schema"]["version"]:
        raise RecipeError("calibration report document/schema differs")
    require_string(report["run_id"], "calibration report.run_id")
    if report["mode"] != "calibration" or report["qualifying"] is not False:
        raise RecipeError("calibration report is not a non-qualifying calibration")
    if report["overall_status"] != "pass":
        raise RecipeError("calibration did not pass")
    if report["manifest_id"] != manifest["manifest_id"] \
            or report["manifest_sha256"] != manifest_sha \
            or report["runner_sha256"] != runner_sha:
        raise RecipeError("calibration manifest/runner binding differs")
    validate_audit_subject(report["subject"], source, "calibration subject")
    if report["bound_documents"] != bound_documents:
        raise RecipeError("calibration bound-document evidence differs")
    if report["calibration_evidence"] is not None:
        raise RecipeError("calibration report recursively claims calibration evidence")
    if report["c9_evidence"] != c9_evidence:
        raise RecipeError("calibration C9 binding differs")
    validate_execution_policy(
        report["execution_policy"], manifest, "calibration execution policy",
    )
    validate_result_population(report, manifest, case_population, "calibration report")
    started = parse_utc(report["started_utc"], "calibration report.started_utc")
    ended = parse_utc(report["ended_utc"], "calibration report.ended_utc")
    if parse_utc(c9_evidence["ended_utc"], "C9 evidence.ended_utc") > started:
        raise RecipeError("calibration began before C9 completed")
    if before_utc is not None and ended > parse_utc(before_utc, "calibration check time"):
        raise RecipeError("calibration report ends after the consuming execution began")
    return {
        "sha256": sha256_bytes(raw),
        "run_id": report["run_id"],
        "started_utc": report["started_utc"],
        "ended_utc": report["ended_utc"],
        "checkout_realpath": report["subject"]["checkout_realpath"],
    }


def validate_qualifying_report(path, manifest_sha, runner_sha, source, manifest,
                               bound_documents, case_population, c9_evidence,
                               calibration_evidence, *, before_utc=None):
    raw = Path(path).read_bytes()
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecipeError(f"qualifying report is unreadable: {exc}") from exc
    ensure_exact_keys(report, REPORT_RECORD_KEYS, where="qualifying report")
    if report["document"] != "FTRO Phase-0 audit execution report" \
            or report["schema_version"] != manifest["report_schema"]["version"]:
        raise RecipeError("qualifying report document/schema differs")
    require_string(report["run_id"], "qualifying report.run_id")
    if report["mode"] != "qualifying" or report["qualifying"] is not True \
            or report["overall_status"] != "pass":
        raise RecipeError("report is not a qualifying PASS")
    if report["manifest_id"] != manifest["manifest_id"] \
            or report["manifest_sha256"] != manifest_sha \
            or report["runner_sha256"] != runner_sha \
            or report["bound_documents"] != bound_documents \
            or report["c9_evidence"] != c9_evidence \
            or report["calibration_evidence"] != calibration_evidence:
        raise RecipeError("qualifying report provenance binding differs")
    validate_audit_subject(report["subject"], source, "qualifying subject")
    validate_execution_policy(
        report["execution_policy"], manifest, "qualifying execution policy",
    )
    validate_result_population(report, manifest, case_population, "qualifying report")
    started = parse_utc(report["started_utc"], "qualifying report.started_utc")
    ended = parse_utc(report["ended_utc"], "qualifying report.ended_utc")
    if ended < started:
        raise RecipeError("qualifying report ends before it starts")
    c9_ended = parse_utc(c9_evidence["ended_utc"], "C9 evidence.ended_utc")
    calibration_ended = parse_utc(
        calibration_evidence["ended_utc"], "calibration evidence.ended_utc",
    )
    if c9_ended > started or calibration_ended > started:
        raise RecipeError("qualifying report began before C9/calibration completed")
    if before_utc is not None and ended > parse_utc(before_utc, "qualification check time"):
        raise RecipeError("qualifying report ends after the qualification check began")
    return {
        "sha256": sha256_bytes(raw),
        "run_id": report["run_id"],
        "started_utc": report["started_utc"],
        "ended_utc": report["ended_utc"],
        "checkout_realpath": report["subject"]["checkout_realpath"],
    }


def write_atomic_new(path, report):
    path = Path(path)
    if path.exists() or Path(str(path) + ".part").exists():
        raise RecipeError(f"refusing to overwrite report path {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(report, indent=2) + "\n"
    temporary = Path(str(path) + ".part")
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, path)


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--mode", required=True, choices=("calibration", "qualifying"))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--c9-report", required=True)
    ap.add_argument("--calibration-report")
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    os.chdir(ROOT)
    manifest_path = Path(args.manifest).resolve()
    runner_path = Path(__file__).resolve()
    manifest = load_json(manifest_path)
    case_population = validate_manifest(manifest)
    manifest_sha = sha256_file(manifest_path)
    runner_sha = sha256_file(runner_path)
    controller_git = select_controller_git()
    source = source_state(
        ROOT, manifest_path, runner_path,
        manifest["subject_binding"]["required_ancestor"],
    )
    bound_documents = verify_bound_documents(ROOT, manifest)
    output = Path(args.out).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise RecipeError("audit reports must be written outside the candidate checkout")

    audit_started = utc_now()
    c9_evidence = validate_c9_report(
        args.c9_report, source, bound_documents, ROOT, before_utc=audit_started,
    )
    calibration = None
    if args.mode == "qualifying":
        if not args.calibration_report:
            raise RecipeError("qualifying mode requires --calibration-report")
        calibration = validate_calibration(
            args.calibration_report, manifest_sha, runner_sha, source,
            manifest, bound_documents, case_population, c9_evidence,
            before_utc=audit_started,
        )
        git_dir = Path(git(ROOT, "rev-parse", "--git-dir").stdout.strip()).resolve()
        marker = git_dir / ("ftro-audit-" + sha256_bytes(
            f"{manifest_sha}:{source['commit']}".encode()) + ".qualifying")
        if marker.exists():
            raise RecipeError("this checkout has already attempted a qualifying run; use a "
                              "separate clean clone")
        marker.write_text(canonical({"run_id": args.run_id, "started_utc": utc_now()}).decode()
                          + "\n", encoding="utf-8")
    elif args.calibration_report:
        raise RecipeError("--calibration-report is only valid in qualifying mode")

    environment = manifest["environment"]["variables"]
    started = audit_started
    results = []
    for operator in manifest["operators"]:
        for case in operator["cases"]:
            print(f"{args.mode}: {case['id']}", flush=True)
            results.append(run_case(ROOT, manifest, operator["id"], case, environment))

    observations = {state: sum(r["observation"] == state for r in results)
                    for state in sorted(RESULT_STATES)}
    failed = [r["case_id"] for r in results if r["verdict"] != "pass"]
    report = {
        "document": "FTRO Phase-0 audit execution report",
        "schema_version": manifest["report_schema"]["version"],
        "run_id": args.run_id,
        "mode": args.mode,
        "qualifying": args.mode == "qualifying",
        "started_utc": started,
        "ended_utc": utc_now(),
        "subject": source,
        "bound_documents": bound_documents,
        "manifest_id": manifest["manifest_id"],
        "manifest_sha256": manifest_sha,
        "runner_sha256": runner_sha,
        "c9_evidence": c9_evidence,
        "calibration_evidence": calibration,
        "execution_policy": {
            "network": manifest["environment"]["network"],
            "network_isolation_enforced": False,
            "environment_is_sanitized": True,
            "controller_git": controller_git,
        },
        "case_population": case_population,
        "n_cases": len(results),
        "n_detected": observations["detected"],
        "n_not_detected": observations["not_detected"],
        "n_not_executed": observations["not_executed"],
        "n_failed_cases": len(failed),
        "failed_cases": failed,
        "overall_status": "pass" if not failed else "fail",
        "results": results,
    }
    # Report self-check: headline numbers are derived immediately before atomic create.
    if report["n_cases"] != len(case_population) or \
            report["n_detected"] + report["n_not_detected"] + \
            report["n_not_executed"] != report["n_cases"] or \
            report["n_failed_cases"] != len(report["failed_cases"]):
        raise RecipeError("internally inconsistent report; refusing publication")
    if report["overall_status"] == "pass":
        validate_execution_policy(
            report["execution_policy"], manifest, "new audit report.execution_policy",
            produced_with=controller_git,
        )
        validate_result_population(
            report, manifest, case_population, "new audit report",
        )
    write_atomic_new(output, report)
    print(f"wrote {output}")
    print(f"overall={report['overall_status']} detected={report['n_detected']} "
          f"not_detected={report['n_not_detected']} "
          f"not_executed={report['n_not_executed']}")
    return 0 if report["overall_status"] == "pass" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RecipeError as exc:
        print(f"AUDIT RUN REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
