#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Focused regressions for the shared strict C9 success-report contract."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]


def load_module():
    path = REPO / "phase0" / "audit" / "c9_contract.py"
    spec = importlib.util.spec_from_file_location("ftro_c9_contract_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C9 = load_module()


def load_audit_runner():
    path = REPO / "phase0" / "audit" / "run.py"
    spec = importlib.util.spec_from_file_location("ftro_audit_c9_contract_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_audit_runner()


def carrier_context():
    import subprocess
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=REPO, capture_output=True, text=True,
        check=True,
    ).stdout.strip()
    return {"commit": commit, "tree": tree, "contract_version": "1.1.0"}


class TestStrictC9Contract(unittest.TestCase):
    @staticmethod
    def recorded_environment():
        safe_path = "/usr/bin:/bin"
        tools = []
        for name in C9.EXPECTED_TOOL_NAMES:
            path = "/bin/sh" if name == "shell" else f"/usr/bin/{name}"
            probe = None if name == "mkdir" else [path, "--version"]
            tools.append({
                "name": name,
                "invocation_path": path,
                "resolved_path": path,
                "sha256": "0" * 64,
                "probe_argv": probe,
                "probe_exit_code": None if probe is None else 0,
                "probe_output": None if probe is None else "recorded probe",
            })
        variables = {key: "recorded" for key in C9.SAFE_ENVIRONMENT_KEYS}
        variables.update({
            "PATH": safe_path,
            "HOME": "/tmp/c9-home", "CURL_HOME": "/tmp/c9-home",
            "XDG_CONFIG_HOME": "/tmp/c9-home", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1", "LC_ALL": "C", "TZ": "UTC",
            "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "NO_COLOR": "1",
            "TMPDIR": "/tmp",
        })
        return {
            "python": "recorded Python",
            "platform": "recorded platform",
            "variables": variables,
            "toolchain": {
                "approved_prefixes": list(C9.APPROVED_TOOL_PREFIXES),
                "tools": tools,
                "selected_pipeline_shell": "/bin/sh",
                "sanitized_path": safe_path,
                "forbidden_inherited_variables": {},
                "errors": [],
                "verified": True,
            },
            "stdin": "DEVNULL",
        }

    def test_minimal_one_row_pass_is_rejected(self):
        # This is the projection-only false PASS the shared validator exists to make
        # impossible: headline flags are green and one plausible provider row exists,
        # but none of the complete evidence populations is present.
        fabricated = {
            "document": "FTRO Phase-0 C9 live-pipeline report",
            "version": "1.1.0",
            "run_id": "fabricated-one-row",
            "started_utc": "2026-08-27T10:00:00+00:00",
            "ended_utc": "2026-08-27T10:01:00+00:00",
            "status": "pass",
            "qualifying": True,
            "first_failure": None,
            "expected_provider_attempts": 1,
            "n_provider_attempts_recorded": 1,
            "n_provider_attempts_successful": 1,
            "provider_population_verified": True,
            "provider_attempts": [{"artifact": "one", "failure_class": "success"}],
        }
        errors = C9.validate_success_report(fabricated, REPO, carrier_context())
        self.assertTrue(errors)
        self.assertTrue(any("keys differ" in error for error in errors))
        with self.assertRaises(C9.C9ContractError):
            C9.assert_success_report(fabricated, REPO, carrier_context())

    def test_audit_consumer_uses_the_same_strict_contract(self):
        fabricated = {
            "document": "FTRO Phase-0 C9 live-pipeline report",
            "version": "1.1.0",
            "run_id": "fabricated-one-row",
            "started_utc": "2026-08-27T10:00:00+00:00",
            "ended_utc": "2026-08-27T10:01:00+00:00",
            "status": "pass",
            "qualifying": True,
            "first_failure": None,
            "expected_provider_attempts": 1,
            "n_provider_attempts_recorded": 1,
            "n_provider_attempts_successful": 1,
            "provider_population_verified": True,
            "provider_attempts": [{"artifact": "one", "failure_class": "success"}],
        }
        context = carrier_context()
        source = {
            "commit": context["commit"], "tree": context["tree"], "clean": True,
            "detached_head": True, "checkout_realpath": str(REPO),
        }
        bound = {"acceptance_contract": {
            "path": "phase0/acceptance-contract-v1.0.md",
            "version": context["contract_version"],
            "sha256": "0" * 64,
        }}
        with tempfile.TemporaryDirectory(prefix="ftro-c9-contract-consumer-") as tmp:
            path = Path(tmp, "fabricated.json")
            path.write_text(json.dumps(fabricated), encoding="utf-8")
            with self.assertRaises(AUDIT.RecipeError):
                AUDIT.validate_c9_report(path, source, bound, REPO)

    def test_audit_consumer_does_not_rebind_historical_paths_or_tools(self):
        source = {
            "commit": "1" * 40, "tree": "2" * 40, "clean": True,
            "detached_head": True, "checkout_realpath": str(REPO),
        }
        bound = {"acceptance_contract": {
            "path": "phase0/acceptance-contract-v1.0.md",
            "version": "1.2.0", "sha256": "0" * 64,
        }}
        with tempfile.TemporaryDirectory(prefix="ftro-c9-portable-consumer-") as tmp:
            copied = Path(tmp, "copied-report.json")
            copied.write_text("{}", encoding="utf-8")
            moved = Path(tmp, "published", "c9.json")
            moved.parent.mkdir()
            moved.write_bytes(copied.read_bytes())
            with mock.patch.object(
                    AUDIT.c9_contract, "assert_success_report",
                    return_value={"run_id": "portable", "ended_utc":
                                  "2026-08-27T00:00:00+00:00"}) as validator:
                first = AUDIT.validate_c9_report(copied, source, bound, REPO)
                second = AUDIT.validate_c9_report(moved, source, bound, REPO)
            context = validator.call_args.args[2]
            self.assertEqual(context["output_view"], "carrier")
            self.assertNotIn("report_path", context)
            self.assertNotIn("verify_runtime_tools", context)
            self.assertNotIn("path", first)
            self.assertEqual(first, second)

    def test_provisional_path_binding_is_producer_only(self):
        report = {"provisional_witness": {
            "path": "/tmp/original-report.json.provisional",
            "sha256": "a" * 64,
            "retained_after_successful_finalization": False,
        }}
        context = {"report_path": "/tmp/copied-report.json", "output_view": "carrier"}
        carrier_errors = []
        C9._validate_provisional(report, context, carrier_errors)
        self.assertFalse(any("provisional witness path differs" in row
                             for row in carrier_errors))
        context["output_view"] = "producer"
        producer_errors = []
        C9._validate_provisional(report, context, producer_errors)
        self.assertTrue(any("provisional witness path differs" in row
                            for row in producer_errors))

    def test_runtime_tool_rehash_is_producer_only(self):
        report = {"environment": self.recorded_environment()}
        carrier_errors = []
        C9._validate_environment(
            report, {"output_view": "carrier", "verify_runtime_tools": True},
            carrier_errors,
        )
        self.assertFalse(any("runtime" in row for row in carrier_errors), carrier_errors)
        producer_errors = []
        C9._validate_environment(
            report, {"output_view": "producer", "verify_runtime_tools": True},
            producer_errors,
        )
        self.assertTrue(any("runtime" in row for row in producer_errors), producer_errors)

    def test_exact_top_level_schema_rejects_an_extra_projection(self):
        fabricated = {key: None for key in C9.REPORT_KEYS}
        fabricated["unexpected_green_tick"] = True
        errors = C9.validate_success_report(fabricated, REPO, carrier_context())
        self.assertTrue(any("unknown=['unexpected_green_tick']" in error for error in errors))

    def test_expected_population_is_65_registry_pins(self):
        errors = []
        expected, urls = C9._carrier_expectations(
            REPO, carrier_context()["commit"], errors,
        )
        self.assertEqual(errors, [])
        self.assertEqual({key: len(value) for key, value in expected.items()}, {
            "evidence_repos": 3, "igs": 57, "ppta": 4, "vgosdb": 1,
        })
        self.assertEqual(sum(map(len, expected.values())), 65)
        self.assertEqual(set(urls), set(expected))

    def test_committed_tree_population_is_not_the_dirty_worktree_projection(self):
        context = carrier_context()
        rows = C9._carrier_rows(REPO, context["commit"])
        names = {row["path"] for row in rows}
        # The independent enumeration is commit-scoped even while this checkout has
        # generated-output changes or unrelated uncommitted preparation files.
        expected = {
            row.strip() for row in __import__("subprocess").run(
                ["git", "ls-tree", "-r", "--name-only", context["commit"]], cwd=REPO,
                capture_output=True, text=True, check=True,
            ).stdout.splitlines()
        }
        self.assertEqual(names, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
