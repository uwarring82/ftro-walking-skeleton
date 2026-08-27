#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Adversarial tests for the Phase-0 audit runner's trust boundaries."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "phase0" / "audit" / "run.py"
MANIFEST = REPO / "phase0" / "audit" / "execution-manifest-v1.0.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("ftro_audit_hardened", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_runner()


def hardened_manifest():
    """Load the frozen file, adapting its old detector spelling during transition."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["environment"]["network"] = "not_used_by_registered_detectors"
    for operator in manifest["operators"]:
        for case in operator["cases"]:
            detector = case["detector"]
            if "mutated_exit_codes" not in detector:
                continue
            outcome_codes = detector.pop("mutated_exit_codes")
            outcome_output = detector.pop("required_output")
            if case["expected_observation"] == "detected":
                detector.update({
                    "accept_exit_codes": detector["baseline_exit_codes"],
                    "accept_output": detector["execution_markers"],
                    "reject_exit_codes": outcome_codes,
                    "reject_output": outcome_output,
                })
            else:
                detector.update({
                    "accept_exit_codes": outcome_codes,
                    "accept_output": outcome_output,
                    "reject_exit_codes": [20],
                    "reject_output": ["FTRO_REGISTERED_REJECTION"],
                })
    return manifest


class AuditRepositoryMixin:
    def setUp(self):
        self.temporary = Path(tempfile.mkdtemp(prefix="ftro-audit-hardening-"))
        self.addCleanup(shutil.rmtree, self.temporary, True)

    def repository(self, detector_body, extra=None):
        root = self.temporary / "source"
        root.mkdir()
        (root / "target.txt").write_text("GOOD\n", encoding="utf-8")
        (root / "detector.py").write_text(detector_body, encoding="utf-8")
        for name, body in (extra or {}).items():
            (root / name).write_text(body, encoding="utf-8")
        environment = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@invalid",
        }
        for argv in (["git", "init", "--quiet", "-b", "main"],
                     ["git", "add", "-A"],
                     ["git", "commit", "--quiet", "-m", "baseline"]):
            result = subprocess.run(
                argv, cwd=root, capture_output=True, text=True, env=environment
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        return root

    @staticmethod
    def case(expected_observation, *, relation="different"):
        return {
            "id": "MX.case",
            "target": "target.txt",
            "target_before_sha256": hashlib.sha256(b"GOOD\n").hexdigest(),
            "mutation": {
                "kind": "text_replace_exact", "old": "GOOD", "new": "BAD",
                "count": 1,
            },
            "detector": {
                "argv": ["python3", "detector.py"],
                "timeout_s": 30,
                "execution_markers": ["DETECTOR_STARTED"],
                "infrastructure_markers": ["Traceback (most recent call last)"],
                "baseline_exit_codes": [0],
                "accept_exit_codes": [0],
                "accept_output": ["REGISTERED_ACCEPTANCE"],
                "reject_exit_codes": [20],
                "reject_output": ["REGISTERED_REJECTION"],
                "output_relation": relation,
            },
            "expected_observation": expected_observation,
            "expected_disposition": "synthetic",
        }

    @staticmethod
    def environment():
        return {"LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0",
                "PYTHONNOUSERSITE": "1"}


class TestObjectiveOracle(AuditRepositoryMixin, unittest.TestCase):
    def test_rejection_cannot_be_relabelled_as_expected_non_detection(self):
        root = self.repository(
            "from pathlib import Path\nimport sys\n"
            "print('DETECTOR_STARTED')\n"
            "bad = 'BAD' in Path('target.txt').read_text()\n"
            "print('REGISTERED_REJECTION' if bad else 'REGISTERED_ACCEPTANCE')\n"
            "raise SystemExit(20 if bad else 0)\n"
        )
        result = AUDIT.run_case(
            root, {}, "MX", self.case("not_detected"), self.environment()
        )
        self.assertEqual(result["observation"], "detected")
        self.assertEqual(result["objective_oracle"]["rejected"], True)
        self.assertEqual(result["verdict"], "fail")
        self.assertTrue(result["reset_verified"])

    def test_acceptance_cannot_be_relabelled_as_expected_detection(self):
        root = self.repository(
            "print('DETECTOR_STARTED')\nprint('REGISTERED_ACCEPTANCE')\n"
        )
        result = AUDIT.run_case(
            root, {}, "MX", self.case("detected", relation="any"), self.environment()
        )
        self.assertEqual(result["observation"], "not_detected")
        self.assertEqual(result["objective_oracle"]["accepted"], True)
        self.assertEqual(result["verdict"], "fail")

    def test_unclassified_outcome_is_not_executed(self):
        root = self.repository("print('DETECTOR_STARTED')\nprint('UNKNOWN')\n")
        result = AUDIT.run_case(
            root, {}, "MX", self.case("detected", relation="any"), self.environment()
        )
        self.assertEqual(result["observation"], "not_executed")
        self.assertEqual(result["verdict"], "fail")


class TestResetProof(AuditRepositoryMixin, unittest.TestCase):
    @staticmethod
    def rejecting_detector():
        return (
            "from pathlib import Path\nimport sys\n"
            "print('DETECTOR_STARTED')\n"
            "bad = 'BAD' in Path('target.txt').read_text()\n"
            "print('REGISTERED_REJECTION' if bad else 'REGISTERED_ACCEPTANCE')\n"
            "raise SystemExit(20 if bad else 0)\n"
        )

    def test_export_and_reset_fingerprints_bind_the_same_candidate_tree(self):
        root = self.repository(self.rejecting_detector())
        result = AUDIT.run_case(
            root, {}, "MX", self.case("detected"), self.environment()
        )
        self.assertEqual(result["verdict"], "pass", result["reason"])
        self.assertTrue(result["export_initialization"]["unchanged"])
        self.assertEqual(result["export_initialization"]["archive_tree_sha256"],
                         result["baseline_tree_sha256"])
        self.assertEqual(result["baseline_tree_sha256"], result["reset_tree_sha256"])

    def test_global_git_hook_cannot_change_the_exported_detector(self):
        root = self.repository(self.rejecting_detector())
        attacker_home = self.temporary / "attacker-home"
        hooks = attacker_home / "hooks"
        hooks.mkdir(parents=True)
        hook = hooks / "pre-commit"
        hook.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"print('DETECTOR_STARTED')\" "
            "\"print('REGISTERED_REJECTION')\" \"raise SystemExit(20)\" > detector.py\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        (attacker_home / ".gitconfig").write_text(
            f"[core]\n\thooksPath = {hooks}\n", encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {"HOME": str(attacker_home)}, clear=False):
            result = AUDIT.run_case(
                root, {}, "MX", self.case("detected"), self.environment()
            )
        self.assertEqual(result["verdict"], "pass", result["reason"])
        self.assertTrue(result["export_initialization"]["unchanged"])

    def test_permission_change_surviving_cleanup_invalidates_reset(self):
        root = self.repository(
            "from pathlib import Path\nimport sys\n"
            "print('DETECTOR_STARTED')\n"
            "bad = 'BAD' in Path('target.txt').read_text()\n"
            "if bad: Path('other.txt').chmod(0o755)\n"
            "print('REGISTERED_REJECTION' if bad else 'REGISTERED_ACCEPTANCE')\n"
            "raise SystemExit(20 if bad else 0)\n",
            {"other.txt": "unchanged bytes\n"},
        )
        result = AUDIT.run_case(
            root, {}, "MX", self.case("detected"), self.environment()
        )
        self.assertEqual(result["observation"], "not_executed")
        self.assertFalse(result["reset_verified"])

    def test_file_to_symlink_change_invalidates_reset(self):
        root = self.repository(
            "from pathlib import Path\nimport sys\n"
            "print('DETECTOR_STARTED')\n"
            "bad = 'BAD' in Path('target.txt').read_text()\n"
            "if bad:\n"
            "    Path('other.txt').unlink()\n"
            "    Path('other.txt').symlink_to('target.txt')\n"
            "print('REGISTERED_REJECTION' if bad else 'REGISTERED_ACCEPTANCE')\n"
            "raise SystemExit(20 if bad else 0)\n",
            {"other.txt": "unchanged bytes\n"},
        )
        result = AUDIT.run_case(
            root, {}, "MX", self.case("detected"), self.environment()
        )
        self.assertEqual(result["observation"], "not_executed")
        self.assertFalse(result["reset_verified"])


class TestFrozenManifestValidation(unittest.TestCase):
    def test_exact_frozen_population_and_mapping_validate(self):
        manifest = hardened_manifest()
        self.assertEqual(AUDIT.validate_manifest(manifest), list(AUDIT.EXPECTED_CASES))

    def test_case_deletion_and_mapping_flip_are_refused(self):
        deleted = hardened_manifest()
        deleted["operators"][0]["cases"].pop()
        with self.assertRaisesRegex(AUDIT.RecipeError, "case population differs"):
            AUDIT.validate_manifest(deleted)

        relabelled = hardened_manifest()
        relabelled["operators"][0]["cases"][0]["expected_observation"] = "not_detected"
        with self.assertRaisesRegex(AUDIT.RecipeError, "case mapping differs"):
            AUDIT.validate_manifest(relabelled)

    def test_nested_recipe_and_network_claim_are_validated(self):
        unsafe_target = hardened_manifest()
        unsafe_target["operators"][0]["cases"][0]["target"] = "../outside"
        with self.assertRaisesRegex(AUDIT.RecipeError, "normalized relative path"):
            AUDIT.validate_manifest(unsafe_target)

        overlapping_oracle = hardened_manifest()
        detector = overlapping_oracle["operators"][0]["cases"][0]["detector"]
        detector["reject_exit_codes"] = detector["accept_exit_codes"]
        with self.assertRaisesRegex(AUDIT.RecipeError, "exit codes overlap"):
            AUDIT.validate_manifest(overlapping_oracle)

        dishonest_network = hardened_manifest()
        dishonest_network["environment"]["network"] = "forbidden"
        with self.assertRaisesRegex(AUDIT.RecipeError, "does not enforce"):
            AUDIT.validate_manifest(dishonest_network)


class TestCalibrationAndEnvironment(AuditRepositoryMixin, unittest.TestCase):
    @staticmethod
    def controller_git_evidence():
        path = AUDIT.TRUSTED_GIT_CANDIDATES[0]
        return {
            "invocation_path": path,
            "resolved_path": path,
            "sha256": "9" * 64,
            "probe_argv": [path, "--no-replace-objects", "--version"],
            "probe_exit_code": 0,
            "probe_output": "git version synthetic",
        }

    @staticmethod
    def synthetic_report(manifest, source, bound, manifest_sha, runner_sha, *, mode,
                         c9_evidence, calibration_evidence, started, ended):
        return {
            "document": "FTRO Phase-0 audit execution report",
            "schema_version": manifest["report_schema"]["version"],
            "run_id": f"synthetic-{mode}",
            "mode": mode,
            "qualifying": mode == "qualifying",
            "started_utc": started,
            "ended_utc": ended,
            "subject": source,
            "bound_documents": bound,
            "manifest_id": manifest["manifest_id"],
            "manifest_sha256": manifest_sha,
            "runner_sha256": runner_sha,
            "c9_evidence": c9_evidence,
            "calibration_evidence": calibration_evidence,
            "execution_policy": {
                "network": "not_used_by_registered_detectors",
                "network_isolation_enforced": False,
                "environment_is_sanitized": True,
                "controller_git": TestCalibrationAndEnvironment.controller_git_evidence(),
            },
            "case_population": [],
            "n_cases": 0,
            "n_detected": 0,
            "n_not_detected": 0,
            "n_not_executed": 0,
            "n_failed_cases": 0,
            "failed_cases": [],
            "overall_status": "pass",
            "results": [],
        }

    def test_empty_self_asserted_calibration_pass_is_refused(self):
        manifest = hardened_manifest()
        population = AUDIT.validate_manifest(manifest)
        source = {
            "commit": "1" * 40, "tree": "2" * 40, "clean": True,
            "detached_head": True,
            "checkout_realpath": "/tmp/frozen-candidate",
        }
        bound = {
            "semantic_model": manifest["semantic_model"],
            "acceptance_contract": manifest["acceptance_contract"],
        }
        manifest_sha, runner_sha = "3" * 64, "4" * 64
        forged = {
            "document": "FTRO Phase-0 audit execution report",
            "schema_version": "1.0.0",
            "run_id": "forged-empty",
            "mode": "calibration",
            "qualifying": False,
            "started_utc": "2026-08-27T00:00:00+00:00",
            "ended_utc": "2026-08-27T00:00:01+00:00",
            "subject": source,
            "bound_documents": bound,
            "manifest_id": manifest["manifest_id"],
            "manifest_sha256": manifest_sha,
            "runner_sha256": runner_sha,
            "c9_evidence": {"sha256": "5" * 64},
            "calibration_evidence": None,
            "execution_policy": {
                "network": "not_used_by_registered_detectors",
                "network_isolation_enforced": False,
                "environment_is_sanitized": True,
                "controller_git": self.controller_git_evidence(),
            },
            "case_population": population,
            "n_cases": 0,
            "n_detected": 0,
            "n_not_detected": 0,
            "n_not_executed": 0,
            "n_failed_cases": 0,
            "failed_cases": [],
            "overall_status": "pass",
            "results": [],
        }
        path = self.temporary / "forged.json"
        path.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaisesRegex(AUDIT.RecipeError, "frozen population"):
            AUDIT.validate_calibration(
                path, manifest_sha, runner_sha, source, manifest, bound, population,
                {"sha256": "5" * 64},
            )

    def test_detector_environment_is_sanitized_and_recorded(self):
        environment = self.environment()
        with mock.patch.dict(os.environ, {
                "PYTHONPATH": "/attacker/python",
                "PYTHONHOME": "/attacker/home",
                "FTRO_AUDIT_SECRET": "must-not-leak"}, clear=False):
            record = AUDIT.command_evidence(
                [sys.executable, "-c",
                 "import os; print(os.getenv('PYTHONPATH')); "
                 "print(os.getenv('PYTHONHOME')); print(os.getenv('FTRO_AUDIT_SECRET'))"],
                self.temporary, 30, environment,
            )
        self.assertEqual(record["exit_code"], 0, record["stderr_excerpt"])
        self.assertEqual(record["stdout_excerpt"].splitlines(), ["None", "None", "None"])
        self.assertNotIn("PYTHONPATH", record["environment"])
        self.assertNotIn("PYTHONHOME", record["environment"])
        self.assertNotIn("FTRO_AUDIT_SECRET", record["environment"])
        self.assertEqual(record["environment"]["LC_ALL"], "C")
        self.assertEqual(record["cwd"], str(self.temporary.resolve()))
        self.assertEqual(record["executable_realpath"], str(Path(sys.executable).resolve()))
        self.assertEqual(record["executable_sha256"],
                         hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest())
        self.assertTrue(record["executable_stable"])
        self.assertEqual(record["executed_argv"][0], str(Path(sys.executable).resolve()))

    def test_relative_path_component_is_refused(self):
        with mock.patch.dict(os.environ, {"PATH": ".:/usr/bin"}, clear=False):
            with self.assertRaisesRegex(AUDIT.RecipeError, "empty or relative"):
                AUDIT.command_evidence(
                    ["python3", "-c", "print('DETECTOR_STARTED')"],
                    self.temporary, 30, self.environment(),
                )

    def test_absolute_path_shim_cannot_select_controller_git(self):
        shim_dir = self.temporary / "absolute-shim"
        shim_dir.mkdir()
        shim = shim_dir / "git"
        shim.write_text("#!/bin/sh\necho forged-git\n", encoding="utf-8")
        shim.chmod(0o755)
        old_command, old_evidence = AUDIT.CONTROLLER_GIT, AUDIT.CONTROLLER_GIT_EVIDENCE
        self.addCleanup(setattr, AUDIT, "CONTROLLER_GIT", old_command)
        self.addCleanup(setattr, AUDIT, "CONTROLLER_GIT_EVIDENCE", old_evidence)
        AUDIT.CONTROLLER_GIT = None
        AUDIT.CONTROLLER_GIT_EVIDENCE = None
        with mock.patch.dict(os.environ, {"PATH": str(shim_dir)}, clear=False):
            evidence = AUDIT.select_controller_git()
        self.assertIn(evidence["invocation_path"], AUDIT.TRUSTED_GIT_CANDIDATES)
        self.assertNotEqual(Path(evidence["invocation_path"]), shim)

    def test_controller_git_ignores_replacement_refs(self):
        root = self.repository("print('unused')\n")
        original = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, check=True,
        ).stdout.strip()
        (root / "target.txt").write_text("REPLACEMENT\n", encoding="utf-8")
        subprocess.run(["git", "add", "target.txt"], cwd=root, check=True)
        environment = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@invalid",
        }
        subprocess.run(
            ["git", "commit", "--quiet", "-m", "replacement"], cwd=root,
            check=True, env=environment,
        )
        replacement = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
            text=True, check=True,
        ).stdout.strip()
        subprocess.run(["git", "replace", original, replacement], cwd=root, check=True)
        observed = AUDIT.git(root, "show", f"{original}:target.txt", text=False).stdout
        self.assertEqual(observed, b"GOOD\n")

    def test_python_shim_cannot_impersonate_the_detector_runtime(self):
        bindir = self.temporary / "bin"
        bindir.mkdir()
        shim = bindir / "python3"
        shim.write_text("#!/bin/sh\necho DETECTOR_STARTED\n", encoding="utf-8")
        shim.chmod(0o755)
        path = str(bindir) + os.pathsep + os.environ["PATH"]
        with mock.patch.dict(os.environ, {"PATH": path}, clear=False):
            with self.assertRaisesRegex(AUDIT.RecipeError, "differs from runner"):
                AUDIT.command_evidence(
                    ["python3", "-c", "print('DETECTOR_STARTED')"],
                    self.temporary, 30, self.environment(),
                )

    def test_command_windows_must_be_ordered_inside_the_report(self):
        root = self.repository(
            "from pathlib import Path\nimport sys\n"
            "print('DETECTOR_STARTED')\n"
            "bad = 'BAD' in Path('target.txt').read_text()\n"
            "print('REGISTERED_REJECTION' if bad else 'REGISTERED_ACCEPTANCE')\n"
            "raise SystemExit(20 if bad else 0)\n"
        )
        case = self.case("detected")
        result = AUDIT.run_case(root, {}, "MX", case, self.environment())
        self.assertEqual(result["verdict"], "pass", result["reason"])
        report = {
            "started_utc": result["baseline_command"]["started_utc"],
            "ended_utc": result["mutated_command"]["ended_utc"],
            "case_population": [case["id"]],
            "results": [result],
            "n_cases": 1,
            "n_detected": 1,
            "n_not_detected": 0,
            "n_not_executed": 0,
            "n_failed_cases": 0,
            "failed_cases": [],
        }
        manifest = {"operators": [{"id": "MX", "cases": [case]}]}
        AUDIT.validate_result_population(report, manifest, [case["id"]], "synthetic")
        report["results"][0]["mutated_command"]["started_utc"] = \
            "2000-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(AUDIT.RecipeError, "command interval/order"):
            AUDIT.validate_result_population(report, manifest, [case["id"]], "synthetic")

    def test_calibration_cannot_precede_c9(self):
        manifest = hardened_manifest()
        source = {"commit": "1" * 40, "tree": "2" * 40, "clean": True,
                  "detached_head": True, "checkout_realpath": "/tmp/calibration"}
        bound = {key: manifest[key] for key in ("semantic_model", "acceptance_contract")}
        c9 = {"ended_utc": "2026-08-27T10:01:00+00:00", "sha256": "5" * 64}
        report = self.synthetic_report(
            manifest, source, bound, "3" * 64, "4" * 64, mode="calibration",
            c9_evidence=c9, calibration_evidence=None,
            started="2026-08-27T10:00:00+00:00",
            ended="2026-08-27T10:02:00+00:00",
        )
        path = self.temporary / "early-calibration.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        with mock.patch.object(AUDIT, "validate_result_population"):
            with self.assertRaisesRegex(AUDIT.RecipeError, "before C9 completed"):
                AUDIT.validate_calibration(
                    path, "3" * 64, "4" * 64, source, manifest, bound, [], c9,
                )

    def test_calibration_evidence_identity_excludes_its_locator(self):
        manifest = hardened_manifest()
        source = {"commit": "1" * 40, "tree": "2" * 40, "clean": True,
                  "detached_head": True, "checkout_realpath": "/tmp/calibration"}
        bound = {key: manifest[key] for key in ("semantic_model", "acceptance_contract")}
        c9 = {"ended_utc": "2026-08-27T09:00:00+00:00", "sha256": "5" * 64}
        report = self.synthetic_report(
            manifest, source, bound, "3" * 64, "4" * 64, mode="calibration",
            c9_evidence=c9, calibration_evidence=None,
            started="2026-08-27T10:00:00+00:00",
            ended="2026-08-27T10:01:00+00:00",
        )
        first = self.temporary / "calibration.json"
        second = self.temporary / "published" / "calibration.json"
        second.parent.mkdir()
        body = json.dumps(report)
        first.write_text(body, encoding="utf-8")
        second.write_text(body, encoding="utf-8")
        first_evidence = AUDIT.validate_calibration(
            first, "3" * 64, "4" * 64, source, manifest, bound, [], c9,
        )
        second_evidence = AUDIT.validate_calibration(
            second, "3" * 64, "4" * 64, source, manifest, bound, [], c9,
        )
        self.assertNotIn("path", first_evidence)
        self.assertEqual(first_evidence, second_evidence)

    def test_qualifying_run_cannot_precede_calibration(self):
        manifest = hardened_manifest()
        source = {"commit": "1" * 40, "tree": "2" * 40, "clean": True,
                  "detached_head": True, "checkout_realpath": "/tmp/q1"}
        bound = {key: manifest[key] for key in ("semantic_model", "acceptance_contract")}
        c9 = {"ended_utc": "2026-08-27T09:00:00+00:00", "sha256": "5" * 64}
        calibration = {
            "sha256": "6" * 64, "run_id": "calibration",
            "started_utc": "2026-08-27T09:30:00+00:00",
            "ended_utc": "2026-08-27T10:01:00+00:00",
            "checkout_realpath": "/tmp/calibration",
        }
        report = self.synthetic_report(
            manifest, source, bound, "3" * 64, "4" * 64, mode="qualifying",
            c9_evidence=c9, calibration_evidence=calibration,
            started="2026-08-27T10:00:00+00:00",
            ended="2026-08-27T10:02:00+00:00",
        )
        path = self.temporary / "early-qualifier.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        with mock.patch.object(AUDIT, "validate_result_population"):
            with self.assertRaisesRegex(AUDIT.RecipeError, "before C9/calibration"):
                AUDIT.validate_qualifying_report(
                    path, "3" * 64, "4" * 64, source, manifest, bound, [], c9,
                    calibration,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
