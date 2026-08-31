#!/usr/bin/env python3
"""Independent controls for the WP2A v1.3 scientific registration."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
WP2A = ROOT / "phase2/wp2a"


def load(name: str) -> dict:
    with (WP2A / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_pointer(document: dict, pointer: str):
    path, fragment = pointer.split("#", 1)
    if path != "phase2/wp2a/expected-answers-v1.3.json":
        raise AssertionError(f"pointer escapes exact oracle: {pointer}")
    current = document
    for token in fragment.removeprefix("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


class TestWP2AScientificRegistrationV13(unittest.TestCase):
    def test_generated_expected_answers_are_current(self):
        result = subprocess.run(
            ["python3", "phase2/wp2a/build_expected_answers_v1_3.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_query_points_to_one_exact_fixture_array(self):
        queries = load("queries-v1.3.json")
        expected = load("expected-answers-v1.3.json")
        cardinalities = queries["cardinality_vocabulary"]
        for query_id, query in queries["queries"].items():
            pointers = query["expected_answer_pointer_by_fixture"]
            self.assertEqual(set(pointers), set(query["applies_to"]), query_id)
            for fixture, pointer in pointers.items():
                records = resolve_pointer(expected, pointer)
                self.assertIsInstance(records, list)
                self.assertEqual(
                    len(records), cardinalities[query["cardinality"]][fixture[-1]],
                    f"{fixture}/{query_id}",
                )
                for record in records:
                    self.assertEqual(set(record), set(query["fields"]), f"{fixture}/{query_id}")

    def test_q3_identifier_and_step2_placeholders_are_exact(self):
        queries = load("queries-v1.3.json")
        expected = load("expected-answers-v1.3.json")
        self.assertIn("assertion_id", queries["queries"]["Q3"]["fields"])
        transformations = load("interpretations-v1.3.json")["transformations"]["records"]
        assertions = load("interpretations-v1.3.json")["assertions"]["records"]
        assertion_by_transformation = {
            row["transformation_id"]: row["assertion_id"] for row in assertions
        }
        for fixture in expected["fixtures"].values():
            for record in fixture["Q3"]:
                self.assertEqual(
                    record["assertion_id"],
                    assertion_by_transformation[record["transformation_id"]],
                )

        tokens = []
        def visit(value):
            if isinstance(value, dict):
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str) and value.startswith("${"):
                tokens.append(value)
        visit(expected["fixtures"])
        self.assertEqual(
            sorted(tokens),
            sorted([
                "${STEP2_REPORT#/started_utc}",
                "${STEP2_REPORT#/started_utc}",
                "${STEP2_REPORT#/ended_utc}",
                "${STEP2_REPORT#/ended_utc}",
            ]),
        )

    def test_key_derived_answers_recompute_from_registered_sources(self):
        source = load("source-facts-v1.3.json")
        expected = load("expected-answers-v1.3.json")
        q2 = {row["product_name"]: row for row in expected["fixtures"]["M1xA"]["Q2"]}
        q6 = {row["product_name"]: row for row in expected["fixtures"]["M1xA"]["Q6"]}
        for product in source["source_projection"]["family_A"]["products"]:
            name = product["registered_selector"]
            sio = product["sio_occurrence_source"]["values"]
            bkg = product["bkg_occurrence_source"]["values"]
            self.assertEqual(q2[name]["sio_outer_sha256"], sio["sha256"])
            self.assertEqual(q2[name]["bkg_outer_sha256"], bkg["sha256"])
            self.assertEqual(
                q2[name]["container_identities_distinct"],
                sio["sha256"] != bkg["sha256"] and f"{name}@SIO" != f"{name}@BKG",
            )
            self.assertEqual(q6[name]["scientific_support_key"], name)
            self.assertEqual(q6[name]["shared_output_identifier"], f"urn:sha256:{sio['decoded_sha256']}")

    def test_model_relation_gate_and_matrix_are_jointly_total(self):
        decision = load("queries-v1.3.json")["trial_decision_function"]
        expected = load("expected-answers-v1.3.json")
        for m1, m2 in expected["model_relation_oracle"]["corresponding_pairs"]:
            common = set(expected["fixtures"][m1]) & set(expected["fixtures"][m2])
            for query_id in common - {"Q9"}:
                self.assertEqual(
                    expected["fixtures"][m1][query_id],
                    expected["fixtures"][m2][query_id],
                    f"{m1}/{m2}/{query_id}",
                )
            for m1_row, m2_row in zip(
                expected["fixtures"][m1]["Q9"], expected["fixtures"][m2]["Q9"]
            ):
                differing = {
                    key for key in m1_row if m1_row[key] != m2_row[key]
                }
                self.assertEqual(
                    differing,
                    {"separate_node_description_present", "transformation_output_type_present"},
                )
        rows = {
            (row["M1_A"], row["M1_B"], row["M2_A"], row["M2_B"])
            for row in decision["boolean_matrix"]
        }
        all_rows = set(itertools.product((False, True), repeat=4))
        violations = {
            row for row in all_rows
            if (row[2] and not row[0]) or (row[3] and not row[1])
        }
        self.assertEqual(len(rows), 9)
        self.assertEqual(len(violations), 7)
        self.assertFalse(rows & violations)
        self.assertEqual(rows | violations, all_rows)
        self.assertTrue(decision["deficiency_closure"]["equivalent_for_registered_queries"])
        self.assertFalse(decision["deficiency_closure"]["model_relation_assurance_failed"])

    def test_fixtures_cannot_embed_the_oracle(self):
        mutation = load("mutation-cases-v1.3.json")
        requirement = next(
            row for row in mutation["fixture_requirements"] if row["id"] == "F-REQ-6"
        )["requirement"]
        self.assertIn("only raw JSON-LD graph data", requirement)
        self.assertIn("MUST NOT embed Q1-Q9 normalized answer arrays", requirement)
        self.assertIn("derives every normalized record by traversing the raw graph", requirement)


if __name__ == "__main__":
    unittest.main()
