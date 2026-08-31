#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Tests for the Phase-0 audit instrument, separate from its qualification runs."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
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
PROBES = load_module("ftro_audit_probes", REPO / "phase0" / "audit" / "probes.py")
sys.path.insert(0, str(REPO / "src" / "ftro"))
from deficiency import result_bearing_current_defects  # noqa: E402

# The qualified Phase-0 carrier.  The frozen manifest describes THIS commit, and its
# `c9_rebinding_policy` states that evidence publication is "a descendant record about the
# qualified carrier, not a rebound candidate".  Manifest targets must therefore be resolved
# against the carrier's own execution evidence, never against descendant working-tree bytes.
CARRIER_COMMIT = "8ddcbfacef2468b8988c331c30100d72f0912eb8"
CARRIER_TREE = "c3e05bddcdb59c578cd406d28da8247d243c5c59"
CARRIER_MANIFEST_SHA256 = "08f5db204eeafc7e9a641167314968b707705491dbd034278083ec34d1647204"
CARRIER_QUALIFICATION_SHA256 = (
    "db0d5a81537d30eed89440ee7ae5dc49f15925a26917c883b517ed45126c0618"
)
CARRIER_QUALIFICATION = "qualification-8ddcbfa.json"
CARRIER_CHILD_EVIDENCE = {
    "c9-8ddcbfa-1.json",
    "calibration-8ddcbfa-1.json",
    "qualifying-8ddcbfa-1.json",
    "qualifying-8ddcbfa-2.json",
}
CARRIER_EVIDENCE = (
    "calibration-8ddcbfa-1.json",
    "qualifying-8ddcbfa-1.json",
    "qualifying-8ddcbfa-2.json",
)


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
                for path in (REPO / "tests").glob("*.py")
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

    def test_living_document_populations_are_discovered_not_hand_enumerated(self):
        crate = json.loads((REPO / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        root_parts = {row["@id"] for row in graph["./"]["hasPart"]}
        for directory, suffixes in (("labnotes", {".md"}),
                                    ("ledgers", {".json", ".md"})):
            paths = sorted(
                path.relative_to(REPO).as_posix()
                for path in (REPO / directory).iterdir()
                if path.is_file() and path.suffix in suffixes
            )
            with self.subTest(directory=directory):
                self.assertTrue(paths)
                self.assertTrue(all(path in graph for path in paths))
                self.assertTrue(all(path in root_parts for path in paths))


class TestFrozenManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REPO / "phase0" / "audit" / "execution-manifest-v1.0.json"
        cls.manifest = json.loads(cls.path.read_text(encoding="utf-8"))
        cls.evidence_dir = REPO / "phase0" / "audit" / "evidence"

        # One independent anchor authenticates the final qualification record.  Only then
        # may its four child hashes become expectations; this avoids five hand-maintained
        # copies that could drift together.
        qualification_raw = (cls.evidence_dir / CARRIER_QUALIFICATION).read_bytes()
        if hashlib.sha256(qualification_raw).hexdigest() != CARRIER_QUALIFICATION_SHA256:
            raise AssertionError("qualified Phase-0 evidence root has changed bytes")
        cls.qualification = json.loads(qualification_raw.decode("utf-8"))
        if cls.qualification.get("n_qualifying_reports") != 2:
            raise AssertionError("qualification record does not bind exactly two qualifiers")
        child_hashes = {
            cls.qualification["c9_evidence"]["run_id"] + ".json":
                cls.qualification["c9_evidence"]["sha256"],
            cls.qualification["calibration_evidence"]["run_id"] + ".json":
                cls.qualification["calibration_evidence"]["sha256"],
            **{
                row["run_id"] + ".json": row["sha256"]
                for row in cls.qualification["qualifying_evidence"]
            },
        }
        if set(child_hashes) != CARRIER_CHILD_EVIDENCE:
            raise AssertionError("qualification record binds the wrong evidence population")
        cls.evidence_sha256 = {
            CARRIER_QUALIFICATION: CARRIER_QUALIFICATION_SHA256,
            **child_hashes,
        }

    @classmethod
    def evidence(cls, name):
        raw = (cls.evidence_dir / name).read_bytes()
        return cls.authenticated_evidence(name, raw)

    @classmethod
    def authenticated_evidence(cls, name, body):
        if hashlib.sha256(body).hexdigest() != cls.evidence_sha256[name]:
            raise AssertionError(f"qualified evidence digest mismatch: {name}")
        return json.loads(body.decode("utf-8"))

    def test_manifest_has_exact_operator_population(self):
        cases = AUDIT.validate_manifest(self.manifest)
        self.assertEqual(len(cases), 25)
        self.assertEqual({op["id"] for op in self.manifest["operators"]},
                         AUDIT.EXPECTED_OPERATORS)

    def test_the_manifest_itself_is_still_the_qualified_instrument(self):
        """The instrument is frozen; its *targets* are resolved against the carrier below."""
        got = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(got, CARRIER_MANIFEST_SHA256)

    def test_qualified_evidence_bytes_match_the_published_digest_chain(self):
        """Authenticate bytes before trusting any field projected from the reports."""
        for name in self.evidence_sha256:
            with self.subTest(report=name):
                self.evidence(name)

        qualification = self.evidence(CARRIER_QUALIFICATION)
        self.assertEqual(qualification["manifest"]["sha256"], CARRIER_MANIFEST_SHA256)

        status = (REPO / "phase0" / "phase0-qualification-v1.0.md").read_text(
            encoding="utf-8"
        )
        published = {
            name: digest
            for name, digest in re.findall(
                r"\| \[`([^`]+\.json)`\]\(audit/evidence/[^)]+\) "
                r"\| `([0-9a-f]{64})` \|",
                status,
            )
        }
        self.assertEqual(published, self.evidence_sha256)

    def test_same_size_evidence_mutation_breaks_the_digest_binding(self):
        name = "calibration-8ddcbfa-1.json"
        original = (self.evidence_dir / name).read_bytes()
        mutated = original.replace(b'"n_detected": 21', b'"n_detected": 20', 1)
        self.assertNotEqual(mutated, original)
        self.assertEqual(len(mutated), len(original))
        self.assertEqual(
            [row["mutation"] for row in json.loads(original)["results"]],
            [row["mutation"] for row in json.loads(mutated)["results"]],
        )
        with self.assertRaisesRegex(AssertionError, "qualified evidence digest mismatch"):
            self.authenticated_evidence(name, mutated)

    def test_every_target_tuple_is_bound_to_the_qualified_carrier(self):
        """Each (target, before-digest) pair must match what the carrier actually executed.

        Resolving `target_before_sha256` against the working tree was wrong: after
        qualification the tree is a descendant, and any edit to a living target -- README.md
        is one -- would report a manifest defect that does not exist.  See FTRO-P1-DEF-011.
        """
        expected = {
            case["id"]: (case["target"], case["target_before_sha256"])
            for operator in self.manifest["operators"] for case in operator["cases"]
        }
        for name in CARRIER_EVIDENCE:
            report = self.evidence(name)
            observed = {}
            for result in report["results"]:
                mutation = result.get("mutation") or {}
                observed[result["case_id"]] = (
                    mutation.get("target"), mutation.get("before_sha256")
                )
            with self.subTest(report=name):
                self.assertEqual(set(observed), set(expected))
            for case_id, pair in sorted(expected.items()):
                with self.subTest(report=name, case=case_id):
                    self.assertEqual(observed[case_id], pair)

    def test_bound_documents_are_bound_to_the_qualified_carrier(self):
        """Same latent coupling: bound documents are carrier state, not working-tree state."""
        for name in CARRIER_EVIDENCE:
            report = self.evidence(name)
            for key in ("semantic_model", "acceptance_contract"):
                with self.subTest(report=name, document=key):
                    self.assertEqual(report["bound_documents"][key], self.manifest[key])

    def test_evidence_reports_bind_the_qualified_carrier(self):
        for name in CARRIER_EVIDENCE:
            report = self.evidence(name)
            with self.subTest(report=name):
                self.assertEqual(report["subject"]["commit"], CARRIER_COMMIT)
                self.assertEqual(report["subject"]["tree"], CARRIER_TREE)
                self.assertTrue(report["subject"]["clean"])
                self.assertEqual(report["manifest_sha256"], CARRIER_MANIFEST_SHA256)
                self.assertEqual(report["overall_status"], "pass")
                self.assertEqual(report["n_not_executed"], 0)
        self.assertEqual(
            [self.evidence(name)["qualifying"] for name in CARRIER_EVIDENCE],
            [False, True, True],
        )

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


class TestWp2aSourceFacts(unittest.TestCase):
    def test_committed_source_facts_equal_regenerated_output(self):
        result = subprocess.run(
            [sys.executable, "phase2/wp2a/build_source_facts.py", "--check"],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)

    def mutated_run(self, mutate):
        """Run the generator against a scratch tree in which one pinned source is mutated."""
        with tempfile.TemporaryDirectory(prefix="ftro-wp2a-") as temporary:
            clone = Path(temporary, "repo")
            done = subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(clone)],
                                  capture_output=True, text=True, timeout=300)
            self.assertEqual(done.returncode, 0, done.stderr)
            for relative in ("phase0/reports/igs-artifact-pins.json",
                             "phase0/evidence/identities.json",
                             "phase0/reports/optical-inventory-summary.json",
                             "phase2/wp2a/build_source_facts.py",
                             "phase2/wp2a/source-facts-v1.2.json"):
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((REPO / relative).read_bytes())
            mutate(clone)
            return subprocess.run([sys.executable, "phase2/wp2a/build_source_facts.py", "--check"],
                                  cwd=clone, capture_output=True, text=True, timeout=300)

    def test_a_mutated_pinned_source_is_rejected_not_rederived(self):
        def mutate(clone):
            path = clone / "phase0/reports/igs-artifact-pins.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            for pin in report["pins"]:
                if pin["name"] == "igs21982.clk.Z":
                    pin["size_bytes"] = pin["size_bytes"] + 1
            path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        result = self.mutated_run(mutate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("pinned", result.stderr)

    def test_a_tampered_committed_output_is_detected(self):
        def mutate(clone):
            path = clone / "phase2/wp2a/source-facts-v1.2.json"
            facts = json.loads(path.read_text(encoding="utf-8"))
            facts["family_A"]["products"][0]["decoded_output"]["sha256"] = "0" * 64
            path.write_text(json.dumps(facts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = self.mutated_run(mutate)
        self.assertEqual(result.returncode, 1)
        self.assertIn("differs from freshly generated", result.stderr)

    def test_an_absent_registered_product_is_rejected(self):
        def mutate(clone):
            path = clone / "phase0/reports/igs-artifact-pins.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["pins"] = [p for p in report["pins"] if p["name"] != "igr21991.clk.Z"]
            path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        result = self.mutated_run(mutate)
        self.assertEqual(result.returncode, 1)

    def test_generated_facts_carry_no_interpretation(self):
        facts = json.loads((REPO / "phase2/wp2a/source-facts-v1.2.json").read_text(encoding="utf-8"))
        forbidden = ("evidence_state", "verification_result", "execution_status",
                     "predicate", "valid_from", "known_from", "consumer")
        blob = json.dumps(facts["family_A"])
        for term in forbidden:
            with self.subTest(term=term):
                self.assertNotIn(f'"{term}"', blob)


class TestCurrentReadmePipeline(unittest.TestCase):
    """The live README's pipeline, checked against the working tree on purpose.

    This is the correct home for a working-tree assertion about README.md.  It constrains the
    documented pipeline as it stands today, using the same two instruments the audit uses --
    the C9 recorder's extractor and the probe's producer-before-consumer oracle -- so a status
    edit is free while a reordered or truncated pipeline still fails.  It deliberately reads
    README.md itself rather than a fixture copy: a fixture would test the copy, not the
    documented pipeline.
    """

    @classmethod
    def setUpClass(cls):
        cls.readme = REPO / "README.md"
        cls.text = cls.readme.read_text(encoding="utf-8")

    def test_recorder_extracts_exactly_eight_ordered_readme_steps(self):
        block, steps = C9.extract_pipeline(self.text)
        self.assertTrue(block.startswith("# 0. Regression suite"))
        self.assertEqual([step["step"] for step in steps], list(range(8)))
        self.assertIn("mkdir -p data/raw/zenodo-17107693", steps[3]["script"])

    def test_producer_before_consumer_oracle_accepts_the_current_readme(self):
        arguments = argparse.Namespace(readme=str(self.readme))
        self.assertEqual(PROBES.readme_order(arguments), 0)

    def test_the_oracle_still_rejects_a_reordered_pipeline(self):
        producer = "python3 src/ftro/pin_evidence_repos.py"
        consumer = "python3 src/ftro/verify_gps2utc.py"
        self.assertLess(self.text.find(producer), self.text.find(consumer),
                        "precondition: the live README orders producer before consumer")
        swapped = self.text.replace(producer, "\x00MARK\x00", 1)
        swapped = swapped.replace(consumer, producer, 1).replace("\x00MARK\x00", consumer, 1)
        with tempfile.TemporaryDirectory(prefix="ftro-readme-order-") as temporary:
            path = Path(temporary, "README.md")
            path.write_text(swapped, encoding="utf-8")
            arguments = argparse.Namespace(readme=str(path))
            self.assertEqual(PROBES.readme_order(arguments), 20)


class TestGate1PublicationInstructions(unittest.TestCase):
    def test_live_retrieval_names_the_exact_eligible_candidate(self):
        text = (REPO / "phase1" / "README.md").read_text(encoding="utf-8")
        checkout = "git switch --detach d0f9e3728e26fff423237b896e9b8ce79feca5bd"
        retrieval = "python3 phase1/check_gate1.py --retrieve --source-state committed_checkout"
        self.assertIn(checkout, text)
        self.assertIn(retrieval, text)
        self.assertLess(text.index(checkout), text.index(retrieval))


class TestC9Recorder(unittest.TestCase):
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
