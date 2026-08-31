#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the fully targeted WP2A v1.3 mutation population."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "phase2/wp2a/mutation-cases-v1.3.json"

FIXTURES = ("M1xA", "M2xA", "M1xB", "M2xB")
A_FIXTURES = ("M1xA", "M2xA")
B_FIXTURES = ("M1xB", "M2xB")
A_OCCURRENCES = (
    "igs21982.clk.Z@SIO", "igs21982.clk.Z@BKG",
    "igs21983.clk.Z@SIO", "igs21983.clk.Z@BKG",
    "igr21991.clk.Z@SIO", "igr21991.clk.Z@BKG",
)
B_OCCURRENCES = ("rocit-zip@zenodo",)
A_OUTPUTS = (
    "urn:sha256:b3145e517490f6f8f4531115294ae9e52da63e656a2eb3710a64a83a5a1137ba",
    "urn:sha256:8ac65974ef7615bad9b119ea5012fdddf94c425b85491bb434a697208777e3ab",
    "urn:sha256:aa5e471c7e15a69bbaebcd907ac463bc3913d343c9269b5382d03f5db4f89a01",
)
B_OUTPUTS = (
    "urn:sha256:00cc90d81c8001ca18586a9da4ca35982bde3a8c6be64e33feb8f2125363c067",
)
A_PRODUCTS = ("igs21982.clk.Z", "igs21983.clk.Z", "igr21991.clk.Z")
A_TRANSFORMATIONS = (
    "igs21982.clk.Z#decode@SIO", "igs21982.clk.Z#decode@BKG",
    "igs21983.clk.Z#decode@SIO", "igs21983.clk.Z#decode@BKG",
    "igr21991.clk.Z#decode@SIO", "igr21991.clk.Z#decode@BKG",
)
B_TRANSFORMATIONS = ("rocit-zip#extract-member",)
A_ASSERTIONS = (
    "igs21982.clk.Z#decodes_to@SIO", "igs21982.clk.Z#same_output@BKG-SIO",
    "igs21983.clk.Z#decodes_to@SIO", "igs21983.clk.Z#same_output@BKG-SIO",
    "igr21991.clk.Z#decodes_to@SIO", "igr21991.clk.Z#same_output@BKG-SIO",
)
B_ASSERTIONS = ("rocit-zip#extracts_member",)
R8_FIELDS = (
    "evidence_state", "verification_result", "execution_status",
    "temporal.valid_from", "temporal.valid_to", "temporal.known_from", "temporal.known_to",
)


OPERATORS = {
    "R1": {
        "description": "route drift",
        "target_kind": "retrieval_occurrence",
        "target_field": "route",
        "mutation": {"operation": "replace", "value": "https://invalid.example/ftro-r1-route-drift"},
        "expected_observation": "detected",
    },
    "R2": {
        "description": "outer-digest drift",
        "target_kind": "retrieval_occurrence",
        "target_field": "outer_sha256",
        "mutation": {"operation": "replace", "value": "0" * 64},
        "expected_observation": "detected",
    },
    "R3": {
        "description": "output-digest drift",
        "target_kind": "output_state",
        "target_field": "output_sha256",
        "target_resolution": "replace every graph occurrence that describes the exact target output_identifier; the recipe freezes the complete JSON-pointer set and may not choose one duplicate occurrence",
        "mutation": {"operation": "replace", "value": "f" * 64},
        "expected_observation": "detected",
    },
    "R4": {
        "description": "wrong archive-member selector",
        "target_kind": "output_state",
        "target_field": "member_selector",
        "mutation": {"operation": "replace", "value": "FTRO-R4-WRONG-MEMBER.dat"},
        "expected_observation": "detected",
    },
    "R5": {
        "description": "wrong direct scientific-input layer",
        "target_kind": "fixture",
        "target_field": "consumption.direct_scientific_input.artifact",
        "mutation_by_family": {
            "A": {"operation": "replace", "value": "decoded provider payload bytes"},
            "B": {"operation": "replace", "value": "container metadata rather than member bytes"},
        },
        "expected_observation": "detected",
    },
    "R6": {
        "description": "collapse distinct SIO and BKG retrieval-occurrence identities",
        "target_kind": "product",
        "target_field": "retrieval_occurrences[origin=BKG].@id",
        "mutation": {
            "operation": "replace_from_target",
            "value_rule": "replace the BKG @id with the same product's SIO @id",
        },
        "expected_observation": "detected",
    },
    "R7": {
        "description": "missing transformation provenance",
        "target_kind": "transformation",
        "target_field": "source_retrieval_id",
        "target_resolution": "select every raw-graph statement that supplies source_retrieval_id for this exact transformation_id; the evaluator, not the fixture, constructs Q3",
        "mutation": {"operation": "delete"},
        "expected_observation": "detected",
    },
    "R8": {
        "description": "missing evidence, verification, execution or temporal state",
        "target_kind": "assertion",
        "target_fields": list(R8_FIELDS),
        "mutation": {"operation": "delete_exact_target_field"},
        "expected_observation": "detected",
    },
    "R9": {
        "description": "dropped fixture",
        "target_kind": "fixture",
        "target_field": "comparison.fixture_population",
        "mutation": {"operation": "remove_target_fixture_from_comparison_input"},
        "expected_observation": "detected",
    },
    "R10": {
        "description": "forged model result",
        "target_kind": "fixture",
        "target_field": "reported_verdict",
        "mutation": {"operation": "replace_without_evaluator_evidence", "value": "pass"},
        "expected_observation": "detected",
    },
    "R11": {
        "description": "presentation-only display-name change",
        "target_kind": "entity",
        "target_field": "ftro:display_name",
        "mutation": {"operation": "replace", "value": "FTRO R11 PRESENTATION-ONLY MUTATION"},
        "expected_observation": "not_detected",
    },
}


def case(operator: str, fixture: str, target_id: str, target_field: str | None = None) -> dict:
    mutation = (
        OPERATORS[operator].get("mutation_by_family", {}).get(fixture[-1])
        or OPERATORS[operator].get("mutation")
    )
    if operator == "R6":
        mutation = {"operation": "replace", "value": f"{target_id}@SIO"}
    row = {
        "case_id": f"{operator}.{fixture}.{target_id}" + (f".{target_field}" if target_field else ""),
        "operator": operator,
        "fixture": fixture,
        "target_id": target_id,
        "target_field": target_field or OPERATORS[operator]["target_field"],
        "mutation": mutation,
        "expected_observation": OPERATORS[operator]["expected_observation"],
    }
    return row


def build() -> dict:
    rows = []
    for fixture in FIXTURES:
        family = fixture[-1]
        occurrences = A_OCCURRENCES if family == "A" else B_OCCURRENCES
        outputs = A_OUTPUTS if family == "A" else B_OUTPUTS
        transformations = A_TRANSFORMATIONS if family == "A" else B_TRANSFORMATIONS
        assertions = A_ASSERTIONS if family == "A" else B_ASSERTIONS
        for target in occurrences:
            rows.extend((case("R1", fixture, target), case("R2", fixture, target)))
        for target in outputs:
            rows.append(case("R3", fixture, target))
            if family == "B":
                rows.append(case("R4", fixture, target))
        for target in transformations:
            rows.append(case("R7", fixture, target))
        rows.append(case("R5", fixture, fixture))
        if family == "A":
            for target in A_PRODUCTS:
                rows.append(case("R6", fixture, target))
        for target in assertions:
            for field in R8_FIELDS:
                rows.append(case("R8", fixture, target, field))
        rows.extend((case("R9", fixture, fixture), case("R10", fixture, fixture)))

    counts = {operator: sum(row["operator"] == operator for row in rows) for operator in OPERATORS}
    counts["R11"] = "one per exact declared entity ID; determined only at recipe freeze"
    return {
        "document": "FTRO WP2A v1.3 mutation cases",
        "version": "1.3.0",
        "generator": "phase2/wp2a/build_mutation_cases_v1_3.py",
        "freeze_stage": "operator semantics, exact pre-fixture targets, exact fields, mutation values and expected observations",
        "operators": OPERATORS,
        "target_populations": {
            "retrieval_occurrences": {"A": list(A_OCCURRENCES), "B": list(B_OCCURRENCES)},
            "output_states": {"A": list(A_OUTPUTS), "B": list(B_OUTPUTS)},
            "transformations": {"A": list(A_TRANSFORMATIONS), "B": list(B_TRANSFORMATIONS)},
            "products": {"A": list(A_PRODUCTS), "B": []},
            "assertions": {"A": list(A_ASSERTIONS), "B": list(B_ASSERTIONS)},
            "R8_fields": list(R8_FIELDS),
        },
        "enumerated_cases": rows,
        "n_enumerated_pre_fixture_cases": len(rows),
        "cases_per_operator": counts,
        "fixture_requirements": [
            {
                "id": "F-REQ-1",
                "requirement": "Every graph entity has one non-empty, unique @id; every normalized query record is traceable to its exact graph JSON pointers.",
                "tested_by": ["Q1-Q9", "recipe preconditions"],
            },
            {
                "id": "F-REQ-2",
                "requirement": "Every assertion carries valid_from, valid_to, known_from and known_to with every field required by Q7, including both informative known_from bounds and valid_from.not_later_than.",
                "tested_by": ["Q7", "R8"],
            },
            {
                "id": "F-REQ-3",
                "requirement": "Every assertion carries evidence_state, verification_result and execution_status as independent fields.",
                "tested_by": ["Q7", "Q8", "R8"],
            },
            {
                "id": "F-REQ-4",
                "requirement": "Every graph entity carries mandatory ftro:display_name, and no registered query reads it.",
                "tested_by": ["R11"],
            },
            {
                "id": "F-REQ-5",
                "requirement": "Each fixture carries duplicate-free ftro:declared_entity_ids exactly equal, in population, to the distinct @id values in @graph.",
                "tested_by": ["R11 exact-ID-set rule"],
            },
            {
                "id": "F-REQ-6",
                "requirement": "Each fixture contains only raw JSON-LD graph data and its declared entity-ID inventory: it MUST NOT embed Q1-Q9 normalized answer arrays, expected-answers-v1.3.json, or an equivalent answer cache. The independently frozen evaluator derives every normalized record by traversing the raw graph. Before mutation, each pre-fixture target_id resolves to the complete raw-graph JSON-pointer set for its registered target_field; zero matches, an unregistered extra match or a recipe-selected subset is not_executed.",
                "tested_by": ["fixture answer-cache prohibition", "R1-R10 recipe preconditions", "evaluator binding"],
            },
        ],
        "R11_exact_id_set_rule": {
            "fixture_requirement": "Each fixture declares `ftro:declared_entity_ids` as a duplicate-free array and every graph entity has one @id and ftro:display_name.",
            "graph_id_set": "set(entity['@id'] for entity in fixture['@graph'])",
            "declared_id_set": "set(fixture['ftro:declared_entity_ids'])",
            "recipe_id_set": "set(case['target_id'] for case in recipes if case['operator']=='R11' and case['fixture']==fixture_id)",
            "required_equality": "graph_id_set == declared_id_set == recipe_id_set, with equal array lengths so duplicates cannot disappear under set conversion",
            "case_identity_rule": "R11.<fixture>.<sha256(UTF-8 target @id) first 16 lowercase hex>",
            "target_field": "ftro:display_name",
            "mutation": OPERATORS["R11"]["mutation"],
            "precondition": "the replacement must differ from the target's pre-mutation value",
            "failure_outcome": "not_executed for R11 and failure of the whole mutation-assurance run",
        },
        "outcomes": {
            "vocabulary": ["detected", "not_detected", "not_executed", "assurance_failed"],
            "rules": [
                {"priority": 1, "when": "mutation did not change the exact target, detector did not run, target population differed, or reset was not byte-exact", "outcome": "not_executed", "pass": False},
                {"priority": 2, "when": "expected_observation is detected and the registered detector detects the applied mutation", "outcome": "detected", "pass": True},
                {"priority": 3, "when": "expected_observation is not_detected and the registered detector does not detect the applied mutation", "outcome": "not_detected", "pass": True},
                {"priority": 4, "when": "observed detection differs from the registered expectation", "outcome": "assurance_failed", "pass": False},
            ],
        },
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    expected = render()
    if args.check:
        try:
            observed = OUT.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL WP2A v1.3 mutation cases: {exc}", file=sys.stderr)
            return 1
        if observed != expected:
            print("FAIL WP2A v1.3 mutation cases: committed output differs", file=sys.stderr)
            return 1
        print("WP2A v1.3 mutation cases: PASS")
        return 0
    OUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
