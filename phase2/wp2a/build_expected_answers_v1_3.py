#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the exact, pre-fixture WP2A v1.3 normalized-answer oracle.

The builder reads only registered JSON evidence and interpretations.  It does
not read either provider payload or a trial fixture.  The two Step-2 timestamps
are represented by explicit tokens and may be substituted only from a
successful report bound to the v1.3 registration manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "phase2/wp2a/expected-answers-v1.3.json"
SOURCE_FACTS = ROOT / "phase2/wp2a/source-facts-v1.3.json"
INTERPRETATIONS = ROOT / "phase2/wp2a/interpretations-v1.3.json"
QUERIES = ROOT / "phase2/wp2a/queries-v1.3.json"
PRIOR_OBSERVATION = ROOT / "phase2/wp2a/prior-observation-v1.3.json"

STEP2_STARTED = "${STEP2_REPORT#/started_utc}"
STEP2_ENDED = "${STEP2_REPORT#/ended_utc}"


class ExpectedAnswerError(ValueError):
    """The registered sources cannot produce one unambiguous answer set."""


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ExpectedAnswerError(f"{path.relative_to(ROOT)} is not a JSON object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(items: list[dict], **conditions: object) -> dict:
    matches = [
        item for item in items
        if all(item.get(key) == value for key, value in conditions.items())
    ]
    if len(matches) != 1:
        rendered = ", ".join(f"{key}={value!r}" for key, value in conditions.items())
        raise ExpectedAnswerError(f"expected one record for {rendered}; found {len(matches)}")
    return matches[0]


def route_from_get(procedure: str) -> str:
    prefix = "GET "
    if not isinstance(procedure, str) or not procedure.startswith(prefix):
        raise ExpectedAnswerError(f"retrieval procedure is not an explicit GET route: {procedure!r}")
    return procedure[len(prefix):]


def retrieval_records(source: dict, transformations: list[dict], family: str) -> list[dict]:
    if family == "A":
        records = []
        for product in source["source_projection"]["family_A"]["products"]:
            name = product["registered_selector"]
            for origin, key in (("SIO", "sio_occurrence_source"), ("BKG", "bkg_occurrence_source")):
                values = product[key]["values"]
                records.append({
                    "retrieval_id": f"{name}@{origin}",
                    "concept_id": values["concept_id"],
                    "route": values["url"],
                    "procedure": values["retrieval_procedure"],
                    "retrieved_utc": values["retrieved_utc"],
                    "outer_sha256": values["sha256"],
                    "outer_size_bytes": values["size_bytes"],
                })
        return records

    values = source["source_projection"]["family_B"]["container_occurrence_source"]["values"]
    transformation = one(transformations, family="B")
    return [{
        "retrieval_id": transformation["source_retrieval_id"],
        "concept_id": values["concept_id"],
        "route": route_from_get(values["retrieval_procedure"]),
        "procedure": values["retrieval_procedure"],
        "retrieved_utc": values["retrieved_utc"],
        "outer_sha256": values["sha256"],
        "outer_size_bytes": values["size_bytes"],
    }]


def retrieval_identity_records(source: dict) -> list[dict]:
    records = []
    for product in source["source_projection"]["family_A"]["products"]:
        name = product["registered_selector"]
        sio = product["sio_occurrence_source"]["values"]
        bkg = product["bkg_occurrence_source"]["values"]
        sio_id = f"{name}@SIO"
        bkg_id = f"{name}@BKG"
        if sio["concept_id"] != bkg["concept_id"]:
            raise ExpectedAnswerError(f"concept mismatch for {name}")
        records.append({
            "product_name": name,
            "concept_id": sio["concept_id"],
            "sio_retrieval_id": sio_id,
            "sio_outer_sha256": sio["sha256"],
            "bkg_retrieval_id": bkg_id,
            "bkg_outer_sha256": bkg["sha256"],
            "container_identities_distinct": sio_id != bkg_id and sio["sha256"] != bkg["sha256"],
        })
    return records


def transformation_records(transformations: list[dict], assertions: list[dict], family: str) -> list[dict]:
    records = []
    for transformation in transformations:
        if transformation["family"] != family:
            continue
        assertion = one(assertions, transformation_id=transformation["transformation_id"])
        records.append({
            "assertion_id": assertion["assertion_id"],
            "transformation_id": transformation["transformation_id"],
            "source_retrieval_id": transformation["source_retrieval_id"],
            "procedure_id": transformation["procedure_id"],
            "procedure_implementation": transformation["procedure_implementation"],
            "output_identifier": transformation["output_identifier"],
            "output_sha256": transformation["output_sha256"],
            "output_size_bytes": transformation["output_size_bytes"],
            "member_selector": transformation["member_selector"],
        })
    return records


def archive_selection_records(transformations: list[dict]) -> list[dict]:
    transformation = one(transformations, family="B")
    return [{
        "transformation_id": transformation["transformation_id"],
        "member_selector": transformation["member_selector"],
    }]


def consumption_records(interpretations: dict, family: str, query: str) -> list[dict]:
    family_key = f"family_{family}"
    claim = interpretations["consumption_claims"][family_key]
    if query == "Q5a":
        value = claim["direct_scientific_input"]
        return [{"family": family, "artifact": value["artifact"], "consumer": value["consumer"]}]
    if query == "Q5b":
        value = claim["logical_support_key"]
        return [{"family": family, "field": value["field"], "consumer": value["consumer"]}]
    if query == "Q5c":
        return [{
            "family": family,
            "provider_payload_bytes_consumed_by_science": claim["provider_payload_bytes_consumed_by_science"],
        }]
    raise ExpectedAnswerError(f"unsupported consumption query: {query}")


def invariance_records(source: dict, interpretations: dict) -> list[dict]:
    transformations = interpretations["transformations"]["records"]
    support_field = interpretations["consumption_claims"]["family_A"]["logical_support_key"]["field"]
    if support_field != "pin record name":
        raise ExpectedAnswerError(f"unregistered Family-A support-field convention: {support_field!r}")
    records = []
    for product in source["source_projection"]["family_A"]["products"]:
        name = product["registered_selector"]
        sio_id = f"{name}@SIO"
        bkg_id = f"{name}@BKG"
        sio = one(transformations, source_retrieval_id=sio_id)
        bkg = one(transformations, source_retrieval_id=bkg_id)
        if sio["output_identifier"] != bkg["output_identifier"]:
            raise ExpectedAnswerError(f"registered decoded outputs differ for {name}")
        records.append({
            "product_name": name,
            "sio_retrieval_id": sio_id,
            "bkg_retrieval_id": bkg_id,
            "shared_output_identifier": sio["output_identifier"],
            "scientific_support_key": name,
            "scientific_answer_stable": True,
        })
    return records


def assertion_records(assertions: list[dict], family: str) -> list[dict]:
    records = []
    for assertion in assertions:
        if assertion["family"] != family:
            continue
        temporal = assertion["temporal"]
        verification_result = assertion["verification_result"]
        execution_status = assertion["execution_status"]
        known_earliest = temporal["known_from"]["not_earlier_than"]
        known_latest = temporal["known_from"]["not_later_than"]
        if family == "B":
            # Fixture comparison is reachable only after step2_supports.
            verification_result = "supports"
            execution_status = "reproduced"
            known_earliest = STEP2_STARTED
            known_latest = STEP2_ENDED
        records.append({
            "assertion_id": assertion["assertion_id"],
            "transformation_id": assertion["transformation_id"],
            "subject": assertion["subject"],
            "predicate": assertion["predicate"],
            "object": assertion["object"],
            "evidence_artifacts": assertion["evidence_artifacts"],
            "evidence_state": assertion["evidence_state"],
            "verification_result": verification_result,
            "execution_status": execution_status,
            "execution_procedure": assertion["execution_procedure"],
            "temporal.valid_from.value": temporal["valid_from"]["value"],
            "temporal.valid_from.bound_state": temporal["valid_from"]["bound_state"],
            "temporal.valid_from.not_later_than": temporal["valid_from"]["not_later_than"],
            "temporal.valid_to.value": temporal["valid_to"]["value"],
            "temporal.valid_to.bound_state": temporal["valid_to"]["bound_state"],
            "temporal.known_from.value": temporal["known_from"]["value"],
            "temporal.known_from.bound_state": "interval" if family == "B" else temporal["known_from"]["bound_state"],
            "temporal.known_from.not_earlier_than": known_earliest,
            "temporal.known_from.not_later_than": known_latest,
            "temporal.known_to.value": temporal["known_to"]["value"],
            "temporal.known_to.bound_state": temporal["known_to"]["bound_state"],
            "basis_pointers": assertion["basis_pointers"],
        })
    return records


def state_axis_records(source: dict, interpretations: dict) -> list[dict]:
    assignments = interpretations["evidence_state_assignments"]
    assertions = interpretations["assertions"]["records"]
    sio_state = one(assignments, subject="IGS SIO container occurrences")["evidence_state"]
    bkg_state = one(assignments, subject="IGS BKG container occurrences")["evidence_state"]
    report_state = one(assignments, subject="historical BKG pin report")["evidence_state"]
    records = []
    for product in source["source_projection"]["family_A"]["products"]:
        name = product["registered_selector"]
        sio = one(assertions, transformation_id=f"{name}#decode@SIO")
        bkg = one(assertions, transformation_id=f"{name}#decode@BKG")
        records.append({
            "product_name": name,
            "sio_container_evidence_state": sio_state,
            "bkg_container_evidence_state": bkg_state,
            "historical_bkg_report_evidence_state": report_state,
            "sio_assertion_verification_result": sio["verification_result"],
            "sio_assertion_execution_status": sio["execution_status"],
            "bkg_assertion_verification_result": bkg["verification_result"],
            "bkg_assertion_execution_status": bkg["execution_status"],
        })
    return records


def output_identity_records(transformations: list[dict], assertions: list[dict], family: str, model: str) -> list[dict]:
    by_output: dict[str, list[dict]] = {}
    for transformation in transformations:
        if transformation["family"] == family:
            by_output.setdefault(transformation["output_identifier"], []).append(transformation)
    records = []
    for output_identifier, producers in by_output.items():
        assertion_ids = {
            one(assertions, transformation_id=producer["transformation_id"])["assertion_id"]
            for producer in producers
        }
        digests = {producer["output_sha256"] for producer in producers}
        if len(digests) != 1:
            raise ExpectedAnswerError(f"one output identifier has multiple digests: {output_identifier}")
        records.append({
            "output_identifier": output_identifier,
            "output_sha256": next(iter(digests)),
            "denotes_exact_byte_state": True,
            "identifier_distinct_from_assertion_id": output_identifier not in assertion_ids,
            "occurs_in_non_presentation_statement": True,
            "separate_node_description_present": model == "M1",
            "transformation_output_type_present": model == "M1",
        })
    return records


def exact_records_by_fixture(source: dict, interpretations: dict) -> dict:
    transformations = interpretations["transformations"]["records"]
    assertions = interpretations["assertions"]["records"]
    fixtures = {}
    for fixture in ("M1xA", "M2xA", "M1xB", "M2xB"):
        model, family = fixture[:2], fixture[-1]
        records = {
            "Q1": retrieval_records(source, transformations, family),
            "Q3": transformation_records(transformations, assertions, family),
            "Q5a": consumption_records(interpretations, family, "Q5a"),
            "Q5b": consumption_records(interpretations, family, "Q5b"),
            "Q5c": consumption_records(interpretations, family, "Q5c"),
            "Q7": assertion_records(assertions, family),
            "Q9": output_identity_records(transformations, assertions, family, model),
        }
        if family == "A":
            records.update({
                "Q2": retrieval_identity_records(source),
                "Q6": invariance_records(source, interpretations),
                "Q8": state_axis_records(source, interpretations),
            })
        else:
            records["Q4"] = archive_selection_records(transformations)
        fixtures[fixture] = records
    return fixtures


def validate(fixtures: dict, queries: dict) -> None:
    vocabulary = queries["cardinality_vocabulary"]
    for fixture, actual_queries in fixtures.items():
        family = fixture[-1]
        applicable = {
            query_id for query_id, query in queries["queries"].items()
            if fixture in query["applies_to"]
        }
        if set(actual_queries) != applicable:
            raise ExpectedAnswerError(
                f"{fixture} query population differs: {sorted(actual_queries)} != {sorted(applicable)}"
            )
        for query_id, records in actual_queries.items():
            query = queries["queries"][query_id]
            expected_pointer = f"phase2/wp2a/expected-answers-v1.3.json#/fixtures/{fixture}/{query_id}"
            if query["expected_answer_pointer_by_fixture"].get(fixture) != expected_pointer:
                raise ExpectedAnswerError(f"{fixture}/{query_id} does not point directly to {expected_pointer}")
            expected_count = vocabulary[query["cardinality"]][family]
            if len(records) != expected_count:
                raise ExpectedAnswerError(
                    f"{fixture}/{query_id} has {len(records)} records, expected {expected_count}"
                )
            fields = set(query["fields"])
            for record in records:
                if set(record) != fields:
                    raise ExpectedAnswerError(
                        f"{fixture}/{query_id} field mismatch: {sorted(record)} != {sorted(fields)}"
                    )
            key = query["record_key"]
            records.sort(key=lambda record: str(record[key]))
            if query_id == "Q9":
                model_expectations = query["model_specific_expectations"][fixture[:2]]
                for record in records:
                    for field, value in model_expectations.items():
                        if record[field] != value:
                            raise ExpectedAnswerError(
                                f"{fixture}/Q9 {field} differs from its registered model expectation"
                            )


def build() -> dict:
    source = load(SOURCE_FACTS)
    interpretations = load(INTERPRETATIONS)
    queries = load(QUERIES)
    # Loading the prior target is intentional: its values must exactly match the
    # conditional Family-B transformation registered in interpretations.
    prior = load(PRIOR_OBSERVATION)
    optical = one(interpretations["transformations"]["records"], family="B")
    if (
        optical["output_sha256"] != prior["target"]["sha256"]
        or optical["output_size_bytes"] != prior["target"]["size_bytes"]
        or optical["member_selector"] != prior["target"]["member_selector"]
    ):
        raise ExpectedAnswerError("Family-B transformation differs from the registered prior target")

    fixtures = exact_records_by_fixture(source, interpretations)
    validate(fixtures, queries)
    inputs = [SOURCE_FACTS, INTERPRETATIONS, QUERIES, PRIOR_OBSERVATION]
    return {
        "document": "FTRO WP2A v1.3 exact normalized expected answers",
        "version": "1.3.0",
        "generator": "phase2/wp2a/build_expected_answers_v1_3.py",
        "status": "pre-fixture oracle; Step-2 timestamps unresolved",
        "input_sha256": {
            str(path.relative_to(ROOT)): digest(path)
            for path in inputs
        },
        "fixture_input_prohibition": "Neither this builder nor its inputs may read a trial fixture or embed normalized answers in one.",
        "placeholder_vocabulary": {
            STEP2_STARTED: {
                "report_pointer": "phase2/wp2a/reports/step2-input-evidence-v1.3.json#/started_utc",
                "admissible_only_when": "outcome == step2_supports and registration_manifest_sha256 matches the frozen manifest",
            },
            STEP2_ENDED: {
                "report_pointer": "phase2/wp2a/reports/step2-input-evidence-v1.3.json#/ended_utc",
                "admissible_only_when": "outcome == step2_supports and registration_manifest_sha256 matches the frozen manifest",
            },
        },
        "placeholder_resolution_rule": "Substitute only the two exact tokens as whole values after the evidence gate. No other expected value is conditional or evaluator-defined.",
        "model_relation_oracle": {
            "corresponding_pairs": [["M1xA", "M2xA"], ["M1xB", "M2xB"]],
            "identical_normalized_queries": ["Q1", "Q2", "Q3", "Q4", "Q5a", "Q5b", "Q5c", "Q6", "Q7", "Q8"],
            "sole_model_specific_query": "Q9",
            "rule": "For every applicable query other than Q9, corresponding M1 and M2 expected arrays are byte-for-byte equal. Q9 differs only in its two registered node-description booleans.",
        },
        "fixtures": fixtures,
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = render()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"FAIL WP2A v1.3 expected answers: {exc}", file=sys.stderr)
        return 1
    if args.check:
        try:
            observed = OUT.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL WP2A v1.3 expected answers: {exc}", file=sys.stderr)
            return 1
        if observed != expected:
            print("FAIL WP2A v1.3 expected answers: committed output differs", file=sys.stderr)
            return 1
        print("WP2A v1.3 expected answers: PASS")
        return 0
    OUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
