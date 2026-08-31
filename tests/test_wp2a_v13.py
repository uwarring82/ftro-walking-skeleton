#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent, provider-byte-free checks for the WP2A v1.3 registration.

These tests never invoke the provider-facing ``run`` command.  They constrain the
frozen registration, exercise the report checker with synthetic rows, and execute both
registered route pairs only against FTRO-synthesised bytes.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


REPO = Path(__file__).resolve().parents[1]
WP2A = REPO / "phase2/wp2a"
sys.path.insert(0, str(WP2A))

import build_mutation_cases_v1_3 as mutations  # noqa: E402
import build_registration_manifest_v1_3 as manifest_builder  # noqa: E402
import build_source_facts_v1_3 as source_builder  # noqa: E402
import build_step2_schema_v1_3 as schema_builder  # noqa: E402
import check_step2_v1_3 as checker  # noqa: E402
import run_step2_v1_3 as runner  # noqa: E402


def load(name):
    return json.loads((WP2A / name).read_text(encoding="utf-8"))


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def resolve_pointer(document, pointer):
    value = document
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise AssertionError(f"not an RFC-6901 pointer: {pointer}")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


class TestWp2aV13Registration(unittest.TestCase):
    def test_all_generated_registration_views_are_current(self):
        self.assertEqual(
            source_builder.serialise(source_builder.build()),
            (WP2A / "source-facts-v1.3.json").read_text(),
        )
        self.assertEqual(mutations.render(), (WP2A / "mutation-cases-v1.3.json").read_text())
        self.assertEqual(schema_builder.render(), (WP2A / "step2-schema-v1.3.json").read_text())
        self.assertEqual(
            manifest_builder.render(),
            (WP2A / "registration-manifest-v1.3.json").read_text(),
        )

    def test_source_projection_is_exact_and_constructed_keys_are_separate(self):
        facts = load("source-facts-v1.3.json")
        self.assertNotIn("output_id", json.dumps(facts["source_projection"]))
        self.assertNotIn("absent_from_all_sources", json.dumps(facts))
        self.assertTrue(facts["constructed_join_keys"]["optical_member_selector"]["not_a_source_value"])
        rebuilt = source_builder.build()
        self.assertEqual(facts, rebuilt)
        for product in facts["source_projection"]["family_A"]["products"]:
            for occurrence in ("sio_occurrence_source", "bkg_occurrence_source"):
                row = product[occurrence]
                self.assertEqual(set(row), {"source_key", "source_pointer", "values"})
                self.assertTrue(row["source_pointer"].startswith("/pins/"))

        documents, _ = source_builder.load_sources()
        copied_rows = []
        for product in facts["source_projection"]["family_A"]["products"]:
            copied_rows.extend((product["sio_occurrence_source"], product["bkg_occurrence_source"]))
        family_b = facts["source_projection"]["family_B"]
        copied_rows.extend((
            family_b["container_occurrence_source"], family_b["member_inventory_source"],
            family_b["comparison_name_source"],
        ))
        for row in copied_rows:
            source_value = resolve_pointer(documents[row["source_key"]], row["source_pointer"])
            self.assertIsInstance(source_value, dict)
            self.assertEqual(
                row["values"], {key: source_value[key] for key in row["values"]}
            )

    def test_source_digest_drift_fails_before_projection(self):
        changed = copy.deepcopy(source_builder.SOURCES)
        changed["igs_sio"]["sha256"] = "0" * 64
        with mock.patch.object(source_builder, "SOURCES", changed):
            with self.assertRaises(source_builder.SourceFactsError):
                source_builder.build()

    def test_prior_observation_registers_full_non_provider_target(self):
        prior = load("prior-observation-v1.3.json")
        registered_sha = "00cc90d81c8001ca18586a9da4ca35982bde3a8c6be64e33feb8f2125363c067"
        self.assertEqual(prior["target"]["sha256"], registered_sha)
        self.assertEqual(prior["target"]["size_bytes"], 780292)
        self.assertFalse(prior["provenance"]["provider_authenticated"])
        self.assertFalse(prior["provenance"]["derived_or_recomputed_by_v1_3"])
        self.assertIn("No observed Step-2 value may populate", prior["anti_circularity_rule"])
        interpretations = load("interpretations-v1.3.json")
        self.assertEqual(interpretations["transformations"]["records"][-1]["output_sha256"], registered_sha)
        self.assertEqual(interpretations["assertions"]["records"][-1]["object"], "urn:sha256:" + registered_sha)

    def test_scientific_axes_temporal_bounds_and_decision_matrix(self):
        interpretations = load("interpretations-v1.3.json")
        queries = load("queries-v1.3.json")
        self.assertEqual(len(interpretations["transformations"]["records"]), 7)
        self.assertEqual(len(interpretations["assertions"]["records"]), 7)
        optical = interpretations["assertions"]["records"][-1]
        self.assertEqual(
            (optical["evidence_state"], optical["verification_result"], optical["execution_status"]),
            ("resolvable", "indeterminate", "not_attempted"),
        )
        for assertion in interpretations["assertions"]["records"][:-1]:
            known = assertion["temporal"]["known_from"]
            self.assertEqual(known["bound_state"], "interval")
            self.assertLessEqual(known["not_earlier_than"], known["not_later_than"])
            self.assertIn("not_later_than", assertion["temporal"]["valid_from"])
        optical_known = optical["temporal"]["known_from"]
        self.assertEqual(optical_known["bound_state"], "pending_step2_interval")
        self.assertIsNone(optical_known["not_earlier_than"])
        self.assertIsNone(optical_known["not_later_than"])
        self.assertIn("started_utc", optical_known["not_earlier_than_source"])
        self.assertEqual(queries["queries"]["Q3"]["cardinality"], "per_transformation")
        matrix = queries["trial_decision_function"]["boolean_matrix"]
        tuples = {
            (row["M1_A"], row["M1_B"], row["M2_A"], row["M2_B"])
            for row in matrix
        }
        self.assertEqual(len(matrix), 9)
        self.assertEqual(len(tuples), 9)
        for m1_a, m1_b, m2_a, m2_b in tuples:
            self.assertFalse(m2_a and not m1_a)
            self.assertFalse(m2_b and not m1_b)

    def test_mutation_population_is_exact_and_aligned_to_oracle_ids(self):
        document = load("mutation-cases-v1.3.json")
        expected_counts = {
            "R1": 14, "R2": 14, "R3": 8, "R4": 2, "R5": 4,
            "R6": 6, "R7": 14, "R8": 98, "R9": 4, "R10": 4,
        }
        self.assertEqual(document["n_enumerated_pre_fixture_cases"], 168)
        self.assertEqual(
            {key: document["cases_per_operator"][key] for key in expected_counts},
            expected_counts,
        )
        cases = document["enumerated_cases"]
        identities = {
            (row["operator"], row["fixture"], row["target_id"], row["target_field"])
            for row in cases
        }
        self.assertEqual(len(cases), len(identities))
        interpretations = load("interpretations-v1.3.json")
        transformation_ids = {
            row["transformation_id"] for row in interpretations["transformations"]["records"]
        }
        assertion_ids = {row["assertion_id"] for row in interpretations["assertions"]["records"]}
        self.assertEqual(
            {row["target_id"] for row in cases if row["operator"] == "R7"},
            transformation_ids,
        )
        self.assertEqual(
            {row["target_id"] for row in cases if row["operator"] == "R8"},
            assertion_ids,
        )
        self.assertEqual(
            {row["target_field"] for row in cases if row["operator"] == "R8"},
            set(mutations.R8_FIELDS),
        )
        self.assertIn("required_equality", document["R11_exact_id_set_rule"])
        self.assertEqual(len(document["fixture_requirements"]), 6)

    def test_schema_freezes_inputs_full_expectations_and_precedence(self):
        schema = load("step2-schema-v1.3.json")
        registration = schema["x-ftro-registration"]
        self.assertEqual(len(registration["input_policy"]["population"]), 4)
        self.assertEqual(len(registration["target_population"]), 4)
        self.assertEqual(registration["input_policy"]["network_during_step2"], "forbidden; acquisition is a documented prerequisite outside the Step-2 run")
        optical = registration["target_population"][-1]
        self.assertEqual(optical["expected_sha256"], load("prior-observation-v1.3.json")["target"]["sha256"])
        self.assertEqual(optical["expected_size_bytes"], 780292)
        self.assertIn("gzip", registration["trusted_computing_base"]["required_tools"])
        self.assertEqual(
            [row["outcome"] for row in registration["run_outcome_precedence"]],
            ["step2_not_executed", "step2_evidence_assurance_failed", "step2_contradicts", "step2_supports"],
        )

    def test_manifest_pins_every_instrument_file_and_not_itself(self):
        manifest = load("registration-manifest-v1.3.json")
        paths = manifest["required_artifact_paths"]
        self.assertEqual(paths, [row["path"] for row in manifest["artifacts"]])
        self.assertEqual(len(paths), len(set(paths)))
        self.assertNotIn("phase2/wp2a/registration-manifest-v1.3.json", paths)
        self.assertIn("phase2/wp2a/run_step2_v1_3.py", paths)
        for row in manifest["artifacts"]:
            observed = hashlib.sha256((REPO / row["path"]).read_bytes()).hexdigest()
            self.assertEqual(observed, row["sha256"], row["path"])

    def test_manifest_checker_rejects_dropped_rogue_and_unready_instruments(self):
        manifest = load("registration-manifest-v1.3.json")

        def working_bytes(_commit, relative):
            try:
                return (REPO / relative).read_bytes()
            except OSError as exc:
                raise checker.CheckError(f"absent synthetic artifact: {relative}") from exc

        with mock.patch.object(checker, "git_bytes", side_effect=working_bytes):
            body = (json.dumps(manifest, indent=2) + "\n").encode()
            self.assertEqual(checker.validate_registration_manifest(body, "0" * 40), [])
            variants = []
            dropped = copy.deepcopy(manifest)
            dropped["required_artifact_paths"].pop(0)
            dropped["artifacts"].pop(0)
            variants.append(dropped)
            rogue = copy.deepcopy(manifest)
            rogue["required_artifact_paths"].append("phase2/wp2a/rogue.py")
            rogue["artifacts"].append({"path": "phase2/wp2a/rogue.py", "sha256": "0" * 64})
            variants.append(rogue)
            unready = copy.deepcopy(manifest)
            unready["runner"]["status"] = "runner_pending"
            unready["ready_for_step2"] = False
            variants.append(unready)
            for index, changed in enumerate(variants):
                with self.subTest(index=index):
                    changed_body = (json.dumps(changed, indent=2) + "\n").encode()
                    self.assertTrue(
                        checker.validate_registration_manifest(changed_body, "0" * 40)
                    )


class TestWp2aV13ReportContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registration = load("step2-schema-v1.3.json")["x-ftro-registration"]

    def successful_method(
        self, method_id, executable, input_handle, member, digest, size,
        input_digest, input_size,
    ):
        contract = self.registration["method_contracts"][method_id]
        return {
            "method_id": method_id,
            "implementation": contract["implementation"],
            "implementation_sha256": None,
            "executable": executable,
            "executable_sha256": "a" * 64,
            "tool_available": True,
            "version_argv": [executable, *contract["version_argv_template"][1:]],
            "version_exit_code": 0,
            "version_output": "synthetic tool 1.0",
            "input_handle": input_handle,
            "input_binding_sha256": input_digest,
            "input_binding_size_bytes": input_size,
            "argv": checker.expected_argv(method_id, executable, input_handle, member),
            "non_execution_reason": None,
            "ran": True,
            "exit_code": 0,
            "started_utc": "2026-08-31T10:00:00Z",
            "ended_utc": "2026-08-31T10:00:01Z",
            "stdout_sha256": digest,
            "stdout_size_bytes": size,
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "stderr_size_bytes": 0,
        }

    def baseline_report(self):
        inputs = []
        for expected in self.registration["input_policy"]["population"]:
            inputs.append({
                "input_id": expected["input_id"],
                "path": expected["path"],
                "acquisition_mode": expected["acquisition_mode"],
                "registered_route": expected["registered_route"],
                "expected_outer_sha256": expected["expected_outer_sha256"],
                "expected_outer_size_bytes": expected["expected_outer_size_bytes"],
                "observed_outer_sha256": expected["expected_outer_sha256"],
                "observed_outer_size_bytes": expected["expected_outer_size_bytes"],
                "post_observed_outer_sha256": expected["expected_outer_sha256"],
                "post_observed_outer_size_bytes": expected["expected_outer_size_bytes"],
                "postflight_path_matches_captured_snapshot": True,
                "outcome": "authenticated",
            })
        input_records = {row["input_id"]: row for row in inputs}
        targets = []
        for target_index, expected in enumerate(self.registration["target_population"]):
            member = expected.get("member_selector")
            input_record = input_records[expected["input_id"]]
            a = self.successful_method(
                expected["method_a"], "/synthetic/a", f"/dev/fd/{10 + target_index * 2}",
                member, expected["expected_sha256"], expected["expected_size_bytes"],
                input_record["observed_outer_sha256"], input_record["observed_outer_size_bytes"],
            )
            b = self.successful_method(
                expected["method_b"], "/synthetic/b", f"/dev/fd/{11 + target_index * 2}",
                member, expected["expected_sha256"], expected["expected_size_bytes"],
                input_record["observed_outer_sha256"], input_record["observed_outer_size_bytes"],
            )
            targets.append({
                "target_id": expected["target_id"],
                "input_id": expected["input_id"],
                "member_selector": member,
                "expected_sha256": expected["expected_sha256"],
                "expected_size_bytes": expected["expected_size_bytes"],
                "expected_source": expected["expected_source"],
                "method_a": a,
                "method_b": b,
                "byte_comparison": "direct_byte_equality",
                "bytes_equal": True,
                "observed_sha256": expected["expected_sha256"],
                "observed_size_bytes": expected["expected_size_bytes"],
                "matches_expected": True,
                "outcome": "supports",
            })
        # This is a shape-only synthetic report (`authenticate_manifest=False` in its
        # consumers), but its publication assertion must still be true even when local
        # HEAD is legitimately ahead of the remote-tracking branch.
        commit = git("rev-parse", "@{upstream}")
        return {
            "document": "FTRO WP2A Step-2 input-evidence report",
            "schema_version": "1.3.0",
            "run_id": "synthetic-v1.3",
            "subject": {
                "commit": commit,
                "tree": git("rev-parse", f"{commit}^{{tree}}"),
                "worktree_clean": True,
                "published": True,
                "published_ref": "origin/phase2",
            },
            "registration_manifest": {
                "path": checker.MANIFEST_REL,
                "sha256": "b" * 64,
            },
            "started_utc": "2026-08-31T10:00:00Z",
            "ended_utc": "2026-08-31T10:00:02Z",
            "input_authentication": inputs,
            "targets": targets,
            "counters": {
                "n_targets": 4,
                "n_supports": 4,
                "n_contradicts": 0,
                "n_evidence_assurance_failed": 0,
                "n_not_executed": 0,
                "n_inputs_changed_during_run": 0,
            },
            "overall_outcome": "step2_supports",
            "output_path": self.registration["report_output_path"],
        }

    def test_synthetic_baseline_is_valid_without_manifest_io(self):
        self.assertEqual(checker.validate_report(self.baseline_report(), authenticate_manifest=False), [])

    def test_checker_rejects_expected_population_counter_and_method_drift(self):
        mutations_to_try = []
        missing_input = self.baseline_report()
        missing_input["input_authentication"].pop()
        mutations_to_try.append(missing_input)
        changed_expected = self.baseline_report()
        changed_expected["targets"][-1]["expected_sha256"] = "0" * 64
        mutations_to_try.append(changed_expected)
        false_counter = self.baseline_report()
        false_counter["counters"]["n_supports"] = False
        mutations_to_try.append(false_counter)
        no_method = self.baseline_report()
        method = no_method["targets"][0]["method_a"]
        method.update({
            "ran": False, "exit_code": None, "started_utc": None, "ended_utc": None,
            "stdout_sha256": None, "stdout_size_bytes": None,
            "stderr_sha256": None, "stderr_size_bytes": None,
        })
        mutations_to_try.append(no_method)
        false_binding = self.baseline_report()
        false_binding["targets"][0]["method_a"]["input_binding_sha256"] = "0" * 64
        mutations_to_try.append(false_binding)
        false_binding_size = self.baseline_report()
        false_binding_size["targets"][0]["method_a"]["input_binding_size_bytes"] += 1
        mutations_to_try.append(false_binding_size)
        newline_handle = self.baseline_report()
        newline_handle["targets"][0]["method_a"]["input_handle"] += "\n"
        newline_handle["targets"][0]["method_a"]["argv"][-1] += "\n"
        mutations_to_try.append(newline_handle)
        for index, changed in enumerate(mutations_to_try):
            with self.subTest(index=index):
                self.assertTrue(checker.validate_report(changed, authenticate_manifest=False))

    def test_declared_json_schema_is_executed(self):
        changed = self.baseline_report()
        changed["targets"][0]["method_a"]["stderr_size_bytes"] = -1
        errors = checker.validate_report(changed, authenticate_manifest=False)
        self.assertTrue(
            any("stderr_size_bytes" in error and "oneOf" in error for error in errors),
            errors,
        )

    def test_local_head_is_not_publication_evidence(self):
        changed = self.baseline_report()
        changed["subject"]["published_ref"] = "HEAD"
        errors = checker.validate_report(changed, authenticate_manifest=False)
        self.assertTrue(any("not contained" in error for error in errors), errors)

    def test_historical_report_uses_subject_bound_schema_not_local_schema(self):
        report = self.baseline_report()
        report["subject"]["commit"] = "0" * 40
        report["subject"]["tree"] = "1" * 40
        manifest_body = (WP2A / "registration-manifest-v1.3.json").read_bytes()
        report["registration_manifest"]["sha256"] = hashlib.sha256(manifest_body).hexdigest()
        bound_schema = (WP2A / "step2-schema-v1.3.json").read_bytes()

        def committed_bytes(_commit, relative):
            if relative == checker.SCHEMA_REL:
                return bound_schema
            if relative == checker.MANIFEST_REL:
                return manifest_body
            return (REPO / relative).read_bytes()

        local_schema = load("step2-schema-v1.3.json")
        local_schema["properties"]["counters"]["properties"]["n_supports"] = {"const": 99}
        with tempfile.TemporaryDirectory() as directory:
            drifted = Path(directory) / "schema.json"
            drifted.write_text(json.dumps(local_schema), encoding="utf-8")
            with mock.patch.object(checker, "SCHEMA_PATH", drifted), \
                 mock.patch.object(checker, "git_bytes", side_effect=committed_bytes), \
                 mock.patch.object(checker, "git_text", return_value="1" * 40), \
                 mock.patch.object(checker, "git_contains", return_value=True):
                self.assertEqual(checker.validate_report(report), [])

    def test_post_authentication_change_controls_overall_outcome(self):
        changed = self.baseline_report()
        row = changed["input_authentication"][0]
        row["post_observed_outer_sha256"] = "0" * 64
        row["postflight_path_matches_captured_snapshot"] = False
        changed["counters"]["n_inputs_changed_during_run"] = 1
        changed["overall_outcome"] = "step2_evidence_assurance_failed"
        self.assertEqual(
            checker.validate_report(changed, authenticate_manifest=False), []
        )
        changed["overall_outcome"] = "step2_supports"
        self.assertTrue(checker.validate_report(changed, authenticate_manifest=False))

    def test_outcome_precedence_is_executable(self):
        self.assertEqual(checker.derive_run_outcome(["supports"] * 4), "step2_supports")
        self.assertEqual(
            checker.derive_run_outcome(["supports"] * 4, n_inputs_changed=1),
            "step2_evidence_assurance_failed",
        )
        self.assertEqual(checker.derive_run_outcome(["contradicts", "supports", "supports", "supports"]), "step2_contradicts")
        self.assertEqual(checker.derive_run_outcome(["contradicts", "evidence_assurance_failed", "supports", "supports"]), "step2_evidence_assurance_failed")
        self.assertEqual(checker.derive_run_outcome(["not_executed", "evidence_assurance_failed", "contradicts", "supports"]), "step2_not_executed")

    def test_complete_global_preflight_failure_report_is_valid(self):
        report = self.baseline_report()
        failed_input = report["input_authentication"][0]
        failed_input.update({
            "observed_outer_sha256": None,
            "observed_outer_size_bytes": None,
            "post_observed_outer_sha256": None,
            "post_observed_outer_size_bytes": None,
            "postflight_path_matches_captured_snapshot": None,
            "outcome": "missing",
        })
        for target in report["targets"]:
            for side in ("method_a", "method_b"):
                method = target[side]
                method.update({
                    "input_handle": None,
                    "argv": checker.expected_argv(
                        method["method_id"], method["executable"], "<not-opened>",
                        target["member_selector"],
                    ),
                    "non_execution_reason": "global_input_preflight_failed",
                    "ran": False,
                    "exit_code": None,
                    "started_utc": None,
                    "ended_utc": None,
                    "stdout_sha256": None,
                    "stdout_size_bytes": None,
                    "stderr_sha256": None,
                    "stderr_size_bytes": None,
                })
                if target["input_id"] == failed_input["input_id"]:
                    method["input_binding_sha256"] = None
                    method["input_binding_size_bytes"] = None
            target.update({
                "byte_comparison": "not_performed",
                "bytes_equal": None,
                "observed_sha256": None,
                "observed_size_bytes": None,
                "matches_expected": None,
                "outcome": "not_executed",
            })
        report["counters"].update({
            "n_supports": 0,
            "n_not_executed": 4,
        })
        report["overall_outcome"] = "step2_not_executed"
        self.assertEqual(checker.validate_report(report, authenticate_manifest=False), [])

    def test_failed_global_preflight_never_permits_any_method(self):
        def authentication(expected):
            failed = expected["input_id"] == self.registration["input_policy"]["population"][-1]["input_id"]
            return {
                "input_id": expected["input_id"], "path": expected["path"],
                "acquisition_mode": expected["acquisition_mode"],
                "registered_route": expected["registered_route"],
                "expected_outer_sha256": expected["expected_outer_sha256"],
                "expected_outer_size_bytes": expected["expected_outer_size_bytes"],
                "observed_outer_sha256": None if failed else expected["expected_outer_sha256"],
                "observed_outer_size_bytes": None if failed else expected["expected_outer_size_bytes"],
                "post_observed_outer_sha256": None,
                "post_observed_outer_size_bytes": None,
                "postflight_path_matches_captured_snapshot": None,
                "outcome": "missing" if failed else "authenticated",
            }

        def capture(expected):
            row = authentication(expected)
            body = None if row["outcome"] != "authenticated" else b"synthetic authenticated input"
            return row, body

        subject = {
            "commit": "0" * 40, "tree": "1" * 40, "worktree_clean": True,
            "published": True, "published_ref": "origin/phase2",
        }
        target_row = {"outcome": "not_executed"}
        with mock.patch.object(runner, "schema_registration", return_value=({}, self.registration)), \
             mock.patch.object(runner, "clean_published_subject", return_value=subject), \
             mock.patch.object(runner, "authenticated_manifest", return_value=({}, "a" * 64)), \
             mock.patch.object(runner, "require_anonymous_fd_transport"), \
             mock.patch.object(runner, "capture_authenticated_input", side_effect=capture), \
             mock.patch.object(runner, "authenticate_input", side_effect=authentication), \
             mock.patch.object(runner, "method_metadata", return_value={}), \
             mock.patch.object(runner, "target_result", return_value=target_row) as target:
            report = runner.build_report()
        self.assertEqual(target.call_count, 4)
        self.assertTrue(all(call.kwargs["permitted"] is False for call in target.call_args_list))
        self.assertEqual(report["overall_outcome"], "step2_not_executed")

    def test_local_upstream_is_rejected_before_any_input_capture(self):
        clean = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"", stderr=b"")
        local_upstream = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"phase2\n", stderr=b""
        )
        with mock.patch.object(runner, "git_run", side_effect=[clean, local_upstream]), \
             mock.patch.object(runner, "git_text", side_effect=["0" * 40, "1" * 40]), \
             mock.patch.object(runner, "git_contains", return_value=False), \
             mock.patch.object(runner, "capture_authenticated_input") as capture:
            with self.assertRaises(checker.CheckError):
                runner.clean_published_subject()
        capture.assert_not_called()

    def test_build_report_rejects_unpublished_subject_before_input_capture(self):
        with mock.patch.object(runner, "schema_registration", return_value=({}, self.registration)), \
             mock.patch.object(
                 runner, "clean_published_subject",
                 side_effect=checker.CheckError("synthetic unpublished subject"),
             ), \
             mock.patch.object(runner, "authenticated_manifest") as manifest, \
             mock.patch.object(runner, "capture_authenticated_input") as capture:
            with self.assertRaises(checker.CheckError):
                runner.build_report()
        manifest.assert_not_called()
        capture.assert_not_called()

    def test_descriptor_transport_preflight_fails_before_any_input_capture(self):
        subject = {
            "commit": "0" * 40, "tree": "1" * 40, "worktree_clean": True,
            "published": True, "published_ref": "origin/phase2",
        }
        with mock.patch.object(runner, "schema_registration", return_value=({}, self.registration)), \
             mock.patch.object(runner, "clean_published_subject", return_value=subject), \
             mock.patch.object(runner, "authenticated_manifest", return_value=({}, "a" * 64)), \
             mock.patch.object(
                 runner, "require_anonymous_fd_transport",
                 side_effect=checker.CheckError("synthetic transport failure"),
             ), \
             mock.patch.object(runner, "capture_authenticated_input") as capture:
            with self.assertRaises(checker.CheckError):
                runner.build_report()
        capture.assert_not_called()

    def test_registered_descriptor_transport_works_on_this_execution_host(self):
        runner.require_anonymous_fd_transport()

    def test_extractors_consume_the_authenticated_snapshot_not_the_mutated_path(self):
        member = "synthetic/member.dat"
        expected_body = b"authenticated provider-independent fixture\n"

        def make_zip(payload):
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr(member, payload)
            return stream.getvalue()

        authenticated_zip = make_zip(expected_body)
        replacement_zip = make_zip(b"changed after authentication\n")
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.zip"
            input_path.write_bytes(authenticated_zip)
            expected_input = {
                "input_id": "input:synthetic",
                "path": str(input_path),
                "acquisition_mode": "synthetic",
                "registered_route": "synthetic:none",
                "expected_outer_sha256": hashlib.sha256(authenticated_zip).hexdigest(),
                "expected_outer_size_bytes": len(authenticated_zip),
            }
            authentication, captured = runner.capture_authenticated_input(expected_input)
            self.assertEqual(authentication["outcome"], "authenticated")
            self.assertEqual(captured, authenticated_zip)
            input_path.write_bytes(replacement_zip)

            method_ids = ("python_zipfile", "system_unzip")
            metadata = {
                method_id: runner.method_metadata(
                    method_id, self.registration["method_contracts"][method_id]
                )
                for method_id in method_ids
            }
            self.assertTrue(
                all(row["tool_available"] for row in metadata.values()),
                "registered Python and unzip tools must be available",
            )
            expected_target = {
                "target_id": "member:synthetic",
                "input_id": "input:synthetic",
                "member_selector": member,
                "expected_sha256": hashlib.sha256(expected_body).hexdigest(),
                "expected_size_bytes": len(expected_body),
                "expected_source": "synthetic:test",
                "method_a": "python_zipfile",
                "method_b": "system_unzip",
            }
            result = runner.target_result(
                expected_target, captured, metadata, permitted=True
            )
            self.assertEqual(result["outcome"], "supports")
            self.assertTrue(result["bytes_equal"])
            for side in ("method_a", "method_b"):
                method = result[side]
                self.assertRegex(method["input_handle"], r"^/dev/fd/[0-9]+$")
                self.assertEqual(
                    method["input_binding_sha256"],
                    hashlib.sha256(authenticated_zip).hexdigest(),
                )
                self.assertEqual(method["input_binding_size_bytes"], len(authenticated_zip))
                self.assertEqual(
                    method["argv"],
                    checker.expected_argv(
                        method["method_id"], method["executable"], method["input_handle"], member
                    ),
                )

            post = runner.add_post_authentication(authentication, expected_input)
            self.assertFalse(post["postflight_path_matches_captured_snapshot"])

    def test_both_unix_compress_routes_consume_the_same_authenticated_descriptor_bytes(self):
        input_body = (REPO / "tests/fixtures/synthetic_sp3.Z").read_bytes()
        metadata = {
            method_id: runner.method_metadata(
                method_id, self.registration["method_contracts"][method_id]
            )
            for method_id in ("ftro_unixz", "system_gzip")
        }
        self.assertTrue(
            all(row["tool_available"] for row in metadata.values()),
            "registered Python and gzip tools must be available",
        )
        rows_and_outputs = [
            runner.execute_method(metadata[method_id], input_body, None, permitted=True)
            for method_id in ("ftro_unixz", "system_gzip")
        ]
        rows = [item[0] for item in rows_and_outputs]
        outputs = [item[1] for item in rows_and_outputs]
        self.assertIsNotNone(outputs[0])
        self.assertEqual(outputs[0], outputs[1])
        for row in rows:
            self.assertTrue(row["ran"])
            self.assertEqual(row["exit_code"], 0)
            self.assertRegex(row["input_handle"], r"^/dev/fd/[0-9]+$")
            self.assertEqual(row["input_binding_sha256"], hashlib.sha256(input_body).hexdigest())
            self.assertEqual(row["input_binding_size_bytes"], len(input_body))
            self.assertEqual(
                row["argv"],
                checker.expected_argv(
                    row["method_id"], row["executable"], row["input_handle"], None
                ),
            )

    def test_snapshot_setup_failure_becomes_typed_non_execution(self):
        metadata = {
            "method_id": "python_zipfile",
            "implementation": self.registration["method_contracts"]["python_zipfile"]["implementation"],
            "implementation_sha256": None,
            "executable": sys.executable,
            "executable_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
            "tool_available": True,
            "version_argv": [sys.executable, "--version"],
            "version_exit_code": 0,
            "version_output": "synthetic",
        }
        with mock.patch.object(
            runner.tempfile, "TemporaryFile", side_effect=OSError("synthetic allocation failure")
        ):
            row, output = runner.execute_method(
                metadata, b"synthetic bytes", "member.dat", permitted=True
            )
        self.assertIsNone(output)
        self.assertFalse(row["ran"])
        self.assertIsNone(row["input_handle"])
        self.assertEqual(
            row["non_execution_reason"], "snapshot_or_method_start_failed:OSError"
        )

    def test_method_start_failure_becomes_typed_non_execution(self):
        metadata = {
            "method_id": "python_zipfile",
            "implementation": self.registration["method_contracts"]["python_zipfile"]["implementation"],
            "implementation_sha256": None,
            "executable": sys.executable,
            "executable_sha256": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
            "tool_available": True,
            "version_argv": [sys.executable, "--version"],
            "version_exit_code": 0,
            "version_output": "synthetic",
        }
        with mock.patch.object(
            runner.subprocess, "run", side_effect=ValueError("synthetic pass_fds failure")
        ):
            row, output = runner.execute_method(
                metadata, b"synthetic bytes", "member.dat", permitted=True
            )
        self.assertIsNone(output)
        self.assertFalse(row["ran"])
        self.assertIsNone(row["input_handle"])
        self.assertEqual(
            row["non_execution_reason"], "snapshot_or_method_start_failed:ValueError"
        )

    def test_malformed_candidate_is_preserved_as_rejected(self):
        report = self.baseline_report()
        report["targets"][0]["method_a"]["method_id"] = "unknown"
        body = (json.dumps(report, indent=2) + "\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.json"
            official = Path(directory) / "official.json"
            candidate.write_bytes(body)
            destination, errors = checker.publish_candidate(candidate, official)
            self.assertTrue(errors)
            self.assertNotEqual(destination, official)
            self.assertEqual(destination.read_bytes(), body)

    def test_atomic_create_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            checker.atomic_create(path, b"first")
            with self.assertRaises(checker.CheckError):
                checker.atomic_create(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
