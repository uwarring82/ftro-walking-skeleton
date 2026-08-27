#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Phase-0 audit instrument, separate from its qualification runs."""

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

REPO = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_module("ftro_audit_runner", REPO / "phase0" / "audit" / "run.py")
C9 = load_module("ftro_c9_runner", REPO / "phase0" / "audit" / "run_c9.py")
sys.path.insert(0, str(REPO / "src" / "ftro"))
from deficiency import result_bearing_current_defects  # noqa: E402


class TestConvergencePredicate(unittest.TestCase):
    def test_only_open_result_changing_current_defects_block(self):
        entries = [
            {"id": "block", "disposition": "open", "affects": "changes_result",
             "finding_type": "current_defect"},
            {"id": "assurance", "disposition": "open", "affects": "changes_result",
             "finding_type": "assurance_gap"},
            {"id": "latent", "disposition": "open", "affects": "changes_result",
             "finding_type": "latent_regression"},
            {"id": "resolved", "disposition": "resolved", "affects": "changes_result",
             "finding_type": "current_defect"},
            {"id": "workflow", "disposition": "open", "affects": "blocks_workflow",
             "finding_type": "current_defect"},
        ]
        self.assertEqual([x["id"] for x in result_bearing_current_defects(entries)], ["block"])


class TestRootCrateCompleteness(unittest.TestCase):
    def test_declared_code_collections_enumerate_their_bounded_population(self):
        crate = json.loads((REPO / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        expected = {
            "src/ftro/": sorted(
                path.relative_to(REPO).as_posix()
                for path in (REPO / "src" / "ftro").glob("*.py")
            ),
            "tests/": sorted(
                path.relative_to(REPO).as_posix()
                for path in (REPO / "tests").glob("test*.py")
            ),
            "phase0/audit/": sorted(
                path.relative_to(REPO).as_posix()
                for path in (REPO / "phase0" / "audit").iterdir()
                if path.is_file()
            ),
        }
        for collection, paths in expected.items():
            with self.subTest(collection=collection):
                declared = sorted(
                    row["@id"] for row in graph[collection]["hasPart"]
                    if collection != "tests/" or row["@id"].endswith(".py")
                )
                self.assertEqual(declared, paths)
                self.assertTrue(all(path in graph for path in paths))


class TestFrozenManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REPO / "phase0" / "audit" / "execution-manifest-v1.0.json"
        cls.manifest = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_manifest_has_exact_operator_population(self):
        cases = AUDIT.validate_manifest(self.manifest)
        self.assertEqual(len(cases), 25)
        self.assertEqual({op["id"] for op in self.manifest["operators"]},
                         AUDIT.EXPECTED_OPERATORS)

    def test_every_target_digest_is_current(self):
        for operator in self.manifest["operators"]:
            for case in operator["cases"]:
                with self.subTest(case=case["id"]):
                    got = hashlib.sha256((REPO / case["target"]).read_bytes()).hexdigest()
                    self.assertEqual(got, case["target_before_sha256"])

    def test_bound_document_digests_are_current(self):
        for key in ("semantic_model", "acceptance_contract"):
            binding = self.manifest[key]
            got = hashlib.sha256((REPO / binding["path"]).read_bytes()).hexdigest()
            self.assertEqual(got, binding["sha256"])

    def test_four_registered_non_detection_operators_are_explicit(self):
        observed = {
            op["id"] for op in self.manifest["operators"]
            if {case["expected_observation"] for case in op["cases"]} == {"not_detected"}
        }
        self.assertEqual(observed, {"M6", "M7", "M8", "M12c"})


class TestAuditRunnerStates(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ftro-audit-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def repository(self, detector_body, extra=None):
        root = self.tmp / "source"
        root.mkdir()
        (root / "target.txt").write_text("GOOD\n", encoding="utf-8")
        (root / "detector.py").write_text(detector_body, encoding="utf-8")
        for name, body in (extra or {}).items():
            (root / name).write_text(body, encoding="utf-8")
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@invalid",
        }
        for argv in (["git", "init", "--quiet", "-b", "main"],
                     ["git", "add", "-A"],
                     ["git", "commit", "--quiet", "-m", "baseline"]):
            result = subprocess.run(argv, cwd=root, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
        return root

    @staticmethod
    def case(expected, mutation, mutated_codes, required, relation="any"):
        accepted = expected == "not_detected"
        return {
            "id": "MX.case",
            "target": "target.txt",
            "target_before_sha256": hashlib.sha256(b"GOOD\n").hexdigest(),
            "mutation": mutation,
            "detector": {
                "argv": ["python3", "detector.py"],
                "timeout_s": 30,
                "execution_markers": ["DETECTOR_STARTED"],
                "infrastructure_markers": ["Traceback (most recent call last)"],
                "baseline_exit_codes": [0],
                "accept_exit_codes": mutated_codes if accepted else [0],
                "accept_output": required if accepted else ["ACCEPTED"],
                "reject_exit_codes": [20] if accepted else mutated_codes,
                "reject_output": ["REGISTERED_REJECTION"] if accepted else required,
                "output_relation": relation,
            },
            "expected_observation": expected,
            "expected_disposition": "synthetic",
        }

    def test_detected_requires_applied_mutation_and_ran_detector(self):
        root = self.repository(
            "import sys\nprint('DETECTOR_STARTED')\n"
            "bad='BAD' in open('target.txt').read()\n"
            "print('REGISTERED_REJECTION' if bad else 'ACCEPTED')\n"
            "raise SystemExit(20 if bad else 0)\n"
        )
        case = self.case("detected",
                         {"kind": "text_replace_exact", "old": "GOOD", "new": "BAD",
                          "count": 1}, [20], ["REGISTERED_REJECTION"])
        result = AUDIT.run_case(root, {}, "MX", case, {})
        self.assertEqual(result["observation"], "detected")
        self.assertEqual(result["verdict"], "pass")
        self.assertTrue(result["reset_verified"])

    def test_expected_non_detection_is_not_a_failed_recipe(self):
        root = self.repository(
            "print('DETECTOR_STARTED')\n"
            "print('ACCEPTED ' + open('target.txt').read().splitlines()[0])\n"
        )
        case = self.case("not_detected", {"kind": "text_append", "text": "# inert\n"},
                         [0], ["ACCEPTED GOOD"], relation="equal")
        result = AUDIT.run_case(root, {}, "MX", case, {})
        self.assertEqual(result["observation"], "not_detected")
        self.assertEqual(result["verdict"], "pass")
        self.assertTrue(result["reset_verified"])

    def test_zero_match_is_not_executed(self):
        root = self.repository("print('DETECTOR_STARTED')\nprint('ACCEPTED')\n")
        case = self.case("detected",
                         {"kind": "text_replace_exact", "old": "ABSENT", "new": "BAD",
                          "count": 1}, [20], ["REGISTERED_REJECTION"])
        result = AUDIT.run_case(root, {}, "MX", case, {})
        self.assertEqual(result["observation"], "not_executed")
        self.assertEqual(result["verdict"], "fail")

    def test_missing_execution_marker_is_not_executed(self):
        root = self.repository("print('something else')\n")
        case = self.case("not_detected", {"kind": "text_append", "text": "# inert\n"},
                         [0], ["something else"])
        result = AUDIT.run_case(root, {}, "MX", case, {})
        self.assertEqual(result["observation"], "not_executed")

    def test_failed_reset_forces_not_executed(self):
        root = self.repository(
            "from pathlib import Path\nprint('DETECTOR_STARTED')\n"
            "bad='BAD' in Path('target.txt').read_text()\n"
            "\nif bad: Path('other.txt').write_text('changed')\n"
            "print('REGISTERED_REJECTION' if bad else 'ACCEPTED')\n"
            "raise SystemExit(20 if bad else 0)\n",
            {"other.txt": "original\n"},
        )
        case = self.case("detected",
                         {"kind": "text_replace_exact", "old": "GOOD", "new": "BAD",
                          "count": 1}, [20], ["REGISTERED_REJECTION"])
        result = AUDIT.run_case(root, {}, "MX", case, {})
        self.assertEqual(result["observation"], "not_executed")
        self.assertFalse(result["reset_verified"])


class TestAuditProbes(unittest.TestCase):
    def run_probe(self, *args):
        return subprocess.run([sys.executable, "phase0/audit/probes.py", *args],
                              cwd=REPO, capture_output=True, text=True, timeout=180)

    def test_readme_pipeline_baseline_is_ordered(self):
        result = self.run_probe("readme-order", "--readme", "README.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FTRO_README_PIPELINE_OK", result.stdout)

    def test_m7_probe_is_coherent(self):
        result = self.run_probe("m7-coherence", "--archive-root",
                                "tests/fixtures/mini-archive")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"coherent":true', result.stdout)

    def test_igs_probe_reads_mutated_report_but_ignores_unbound_labels(self):
        with tempfile.TemporaryDirectory(prefix="ftro-m6-test-") as temporary:
            source = json.loads((REPO / "phase0/reports/igs-artifact-pins.json")
                                .read_text(encoding="utf-8"))
            baseline = self.run_probe("igs-support", "--report",
                                      "phase0/reports/igs-artifact-pins.json")
            for pin in source["pins"]:
                pin["series"], pin["mjd"] = "igr", 0
            mutated = Path(temporary, "igs.json")
            mutated.write_text(json.dumps(source), encoding="utf-8")
            changed = self.run_probe("igs-support", "--report", str(mutated))
            self.assertEqual(baseline.returncode, 0)
            self.assertEqual(changed.returncode, 0)
            self.assertEqual(baseline.stdout, changed.stdout)


class TestC9Recorder(unittest.TestCase):
    def test_extracts_exactly_eight_ordered_readme_steps(self):
        block, steps = C9.extract_pipeline((REPO / "README.md").read_text(encoding="utf-8"))
        self.assertTrue(block.startswith("# 0. Regression suite"))
        self.assertEqual([step["step"] for step in steps], list(range(8)))
        self.assertIn("mkdir -p data/raw/zenodo-17107693", steps[3]["script"])

    def test_provider_failures_do_not_imply_an_access_class(self):
        for text, expected, reachability in (
                ("Could not resolve host: x", "transport_failure", "dns_failed"),
                ("HTTP 200 Earthdata Login <html>", "authentication_or_interstitial",
                 "http_response"),
                ("checksum mismatch", "digest_mismatch", "not_established"),
                ("preflight: digest absent", "preflight_failure", "not_established")):
            with self.subTest(text=text):
                failure, stage = C9.classify_failure(4, text)
                self.assertEqual(failure, expected)
                self.assertEqual(stage, reachability)

    def test_c9_policy_invalidates_every_new_candidate_commit(self):
        manifest = json.loads((REPO / "phase0/audit/execution-manifest-v1.0.json")
                              .read_text(encoding="utf-8"))
        policy = manifest["c9_rebinding_policy"]
        self.assertEqual(
            policy["live_rerun_required_after_changes_to"],
            ["any tracked byte in a new candidate commit before qualification completes"],
        )
        self.assertEqual(
            policy["rebind_without_provider_rerun_only_for"],
            ["none; evidence publication is a descendant record about the qualified carrier, "
             "not a rebound candidate"],
        )
        self.assertIn("README step 0", policy["why_tests_rebind"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
