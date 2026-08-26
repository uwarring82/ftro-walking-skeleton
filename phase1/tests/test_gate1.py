#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Mutation tests for the bounded Phase-1 Gate-1 checker."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


PHASE1 = Path(__file__).resolve().parents[1]
REPO_ROOT = PHASE1.parent
sys.path.insert(0, str(PHASE1))

import check_gate1 as gate1  # noqa: E402


def manifest(domain: str) -> dict:
    return gate1.load_json(gate1.manifest_path(REPO_ROOT, domain))


def entity(document: dict, identifier: str) -> dict:
    return next(item for item in document["@graph"] if item["@id"] == identifier)


def messages(domain: str, document: dict, root: Path = REPO_ROOT) -> str:
    errors, _index = gate1.validate_manifest(domain, document, root)
    return "\n".join(errors)


def copy_captured_inputs(destination: Path) -> None:
    for relative in gate1.CAPTURED_INPUT_PATHS:
        source = REPO_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def passing_report(snapshot: gate1.Gate1Snapshot) -> dict:
    n_provider = sum(item["role"] == "provider_source" for item in snapshot.sources)
    n_catalogs = sum(item["role"] == "source_catalog" for item in snapshot.sources)
    return {
        "input_fingerprint_sha256": snapshot.input_fingerprint,
        "input_sha256": snapshot.input_hashes,
        "candidate_source_state": "parent_overlay",
        "source_state_evidence": {
            "mode": "parent_overlay",
            "data_directory_present": False,
            "git_head": gate1.PHASE1_PARENT_COMMIT,
            "candidate_paths": sorted(gate1.CANDIDATE_OVERLAY_PATHS),
            "verified": True,
        },
        "environment": {"data_directory_present_at_start": False},
        "gate1_retrieval_status": "pass",
        "n_sources": len(snapshot.sources),
        "n_provider_sources": n_provider,
        "n_source_catalogs": n_catalogs,
        "n_retrieved_and_matched": len(snapshot.sources),
        "n_failed": 0,
        "results": [
            {
                **source,
                "observed_sha256": source["expected_sha256"],
                "checksum_match": True,
                "outcome": "retrieved",
            }
            for source in snapshot.sources
        ],
    }


def make_isolated_candidate(
    destination: Path, head: str = gate1.PHASE1_PARENT_COMMIT
) -> Path:
    root = destination / "repo"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", str(REPO_ROOT), str(root)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "checkout", "--quiet", "--detach", head],
        check=True,
    )
    for relative in gate1.CANDIDATE_OVERLAY_PATHS:
        source = REPO_ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root


def commit_candidate(root: Path) -> str:
    subprocess.run(
        ["git", "-C", str(root), "add", "--", *sorted(gate1.CANDIDATE_OVERLAY_PATHS)],
        check=True,
    )
    subprocess.run(
        [
            "git", "-C", str(root),
            "-c", "user.name=FTRO test",
            "-c", "user.email=ftro-test@example.invalid",
            "commit", "--quiet", "-m", "test: publish Gate-1 candidate",
        ],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


class TestCommittedGate1State(unittest.TestCase):
    def test_all_four_manifests_pass_bounded_check(self):
        errors, documents = gate1.validate_all(REPO_ROOT)
        self.assertEqual([], errors)
        self.assertEqual(set(gate1.DOMAINS), set(documents))

    def test_clean_retrieval_population_is_complete(self):
        errors, documents = gate1.validate_all(REPO_ROOT)
        self.assertEqual([], errors)
        sources = gate1.collect_sources(documents, REPO_ROOT)
        self.assertEqual(69, len(sources))
        self.assertEqual(
            gate1.EXPECTED_RETRIEVAL_COUNTS,
            dict(Counter(item["domain"] for item in sources)),
        )
        self.assertEqual(66, sum(item["role"] == "provider_source" for item in sources))
        self.assertEqual(3, sum(item["role"] == "source_catalog" for item in sources))

    def test_snapshot_survives_a_later_catalog_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_captured_inputs(root)
            errors, snapshot = gate1.build_snapshot(root)
            self.assertEqual([], errors)
            self.assertEqual(69, len(snapshot.sources))

            report_path = root / "phase0/reports/igs-artifact-pins.json"
            report = gate1.load_json(report_path)
            removed = report["pins"].pop()
            report["n_pinned"] -= 1
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

            self.assertEqual(69, len(snapshot.sources))
            self.assertIn(
                removed["ftro_snapshot_id"],
                {item["identifier"] for item in snapshot.sources},
            )

    def test_report_fingerprint_becomes_stale_after_manifest_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_captured_inputs(root)
            errors, before = gate1.build_snapshot(root)
            self.assertEqual([], errors)
            report = passing_report(before)
            self.assertEqual([], gate1.retrieval_report_errors(before, report))

            path = gate1.manifest_path(root, "optical")
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            errors, after = gate1.build_snapshot(root)
            self.assertEqual([], errors)
            self.assertIn("input fingerprint differs", gate1.retrieval_report_errors(after, report))

    def test_report_without_source_state_evidence_is_rejected(self):
        errors, snapshot = gate1.build_snapshot(REPO_ROOT)
        self.assertEqual([], errors)
        report = passing_report(snapshot)
        report.pop("source_state_evidence")
        self.assertIn(
            "source-state evidence is absent or not an object",
            gate1.retrieval_report_errors(snapshot, report),
        )

    def test_every_result_aggregate_is_recomputed(self):
        errors, snapshot = gate1.build_snapshot(REPO_ROOT)
        self.assertEqual([], errors)
        expected = {
            "n_sources": 69,
            "n_provider_sources": 66,
            "n_source_catalogs": 3,
            "n_retrieved_and_matched": 69,
            "n_failed": 0,
        }
        baseline = passing_report(snapshot)
        self.assertEqual(expected, {field: baseline[field] for field in expected})
        for field, correct in expected.items():
            for mutation in (None, False, correct + 1):
                with self.subTest(field=field, mutation=mutation):
                    report = copy.deepcopy(baseline)
                    if mutation is None:
                        report.pop(field)
                    else:
                        report[field] = mutation
                    self.assertTrue(
                        any(
                            message.startswith(f"{field} is not integer")
                            for message in gate1.retrieval_report_errors(snapshot, report)
                        )
                    )

    def test_role_headlines_are_not_only_checked_by_their_sum(self):
        errors, snapshot = gate1.build_snapshot(REPO_ROOT)
        self.assertEqual([], errors)
        report = passing_report(snapshot)
        report["n_provider_sources"] -= 1
        report["n_source_catalogs"] += 1
        messages = gate1.retrieval_report_errors(snapshot, report)
        self.assertTrue(any(item.startswith("n_provider_sources") for item in messages))
        self.assertTrue(any(item.startswith("n_source_catalogs") for item in messages))

    def test_failure_row_invalidates_success_headlines_and_status(self):
        errors, snapshot = gate1.build_snapshot(REPO_ROOT)
        self.assertEqual([], errors)
        report = passing_report(snapshot)
        report["results"][0]["outcome"] = "digest_mismatch"
        report["results"][0]["checksum_match"] = False
        report["results"][0]["observed_sha256"] = "0" * 64
        messages = gate1.retrieval_report_errors(snapshot, report)
        self.assertTrue(any(item.startswith("n_retrieved_and_matched") for item in messages))
        self.assertTrue(any(item.startswith("n_failed") for item in messages))
        self.assertIn(
            "gate1_retrieval_status is not derived from results and source state",
            messages,
        )

    def test_duplicate_result_invalidates_serialized_source_count(self):
        errors, snapshot = gate1.build_snapshot(REPO_ROOT)
        self.assertEqual([], errors)
        report = passing_report(snapshot)
        report["results"].append(copy.deepcopy(report["results"][0]))
        messages = gate1.retrieval_report_errors(snapshot, report)
        self.assertIn("result 69 duplicates a source identity", messages)
        self.assertTrue(any(item.startswith("n_sources") for item in messages))
        self.assertIn(
            "results count does not equal the captured source population", messages
        )


class TestSourceStatePreflight(unittest.TestCase):
    def test_exact_parent_overlay_is_demonstrated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            errors, evidence = gate1.source_state_evidence(root, "parent_overlay")
            self.assertEqual([], errors)
            self.assertTrue(evidence["verified"])
            self.assertEqual(gate1.PHASE1_PARENT_COMMIT, evidence["git_head"])
            self.assertEqual(
                sorted(gate1.CANDIDATE_OVERLAY_PATHS), evidence["candidate_paths"]
            )

    def test_data_directory_stops_main_before_retrieval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            (root / "data").mkdir()
            output = root / "report.json"
            with mock.patch.object(gate1, "retrieval_report") as retrieve:
                status = gate1.main([
                    "--root", str(root),
                    "--retrieve",
                    "--source-state", "parent_overlay",
                    "--out", str(output),
                ])
            self.assertEqual(1, status)
            retrieve.assert_not_called()
            self.assertFalse(output.exists())

    def test_change_outside_candidate_overlay_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            readme = root / "phase1/README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            errors, evidence = gate1.source_state_evidence(root, "parent_overlay")
            self.assertIn(
                "parent overlay contains changes outside the candidate paths: phase1/README.md",
                errors,
            )
            self.assertFalse(evidence["verified"])

    def test_wrong_parent_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary), gate1.BASELINE_COMMIT)
            errors, evidence = gate1.source_state_evidence(root, "parent_overlay")
            self.assertTrue(any("HEAD differs from the Phase-1 parent" in item for item in errors))
            self.assertEqual(gate1.BASELINE_COMMIT, evidence["git_head"])
            self.assertFalse(evidence["verified"])

    def test_clean_committed_candidate_is_demonstrated_and_runnable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            commit = commit_candidate(root)
            errors, evidence = gate1.source_state_evidence(root, "committed_checkout")
            self.assertEqual([], errors)
            self.assertTrue(evidence["verified"])
            self.assertEqual(commit, evidence["git_head"])
            self.assertEqual([], evidence["candidate_paths"])
            self.assertTrue(evidence["phase1_parent_is_ancestor"])
            self.assertTrue(
                gate1.CANDIDATE_OVERLAY_PATHS.issubset(
                    evidence["paths_changed_since_parent"]
                )
            )

            snapshot_errors, snapshot = gate1.build_snapshot(root)
            self.assertEqual([], snapshot_errors)
            self.assertEqual(
                [], gate1.retrieval_report_errors(snapshot, passing_report(snapshot))
            )

            output = Path(temporary) / "report.json"

            def retrieved(source, _timeout):
                return {
                    **source,
                    "started_utc": "2026-08-26T00:00:00+00:00",
                    "finished_utc": "2026-08-26T00:00:00+00:00",
                    "size_bytes": 0,
                    "observed_sha256": source["expected_sha256"],
                    "checksum_match": True,
                    "outcome": "retrieved",
                }

            with mock.patch.object(gate1, "retrieve_one", side_effect=retrieved):
                status = gate1.main([
                    "--root", str(root),
                    "--retrieve",
                    "--source-state", "committed_checkout",
                    "--out", str(output),
                ])
            self.assertEqual(0, status)
            report = gate1.load_json(output)
            self.assertEqual([], gate1.retrieval_report_errors(snapshot, report))
            forged = copy.deepcopy(report)
            forged["source_state_evidence"]["paths_changed_since_parent"].append(
                "src/ftro/schema.py"
            )
            self.assertIn(
                "source-state evidence records disallowed committed paths: src/ftro/schema.py",
                gate1.retrieval_report_errors(snapshot, forged),
            )

    def test_clean_non_descendant_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary), gate1.BASELINE_COMMIT)
            commit_candidate(root)
            errors, evidence = gate1.source_state_evidence(root, "committed_checkout")
            self.assertIn(
                "committed checkout does not descend from the Phase-1 parent", errors
            )
            self.assertFalse(evidence["phase1_parent_is_ancestor"])
            self.assertFalse(evidence["verified"])

    def test_committed_candidate_may_carry_non_input_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            readme = root / "phase1/README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\npublication output\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "-C", str(root), "add", "--", "phase1/README.md"],
                check=True,
            )
            commit_candidate(root)
            errors, evidence = gate1.source_state_evidence(root, "committed_checkout")
            self.assertEqual([], errors)
            self.assertIn("phase1/README.md", evidence["paths_changed_since_parent"])
            self.assertTrue(evidence["verified"])

    def test_committed_candidate_rejects_executable_extra_paths(self):
        for relative in ("src/ftro/schema.py", "phase1/helper.py"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                root = make_isolated_candidate(Path(temporary))
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                existing = path.read_text(encoding="utf-8") if path.exists() else ""
                path.write_text(existing + "\n# disallowed carrier change\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(root), "add", "--", relative],
                    check=True,
                )
                commit_candidate(root)
                errors, evidence = gate1.source_state_evidence(
                    root, "committed_checkout"
                )
                self.assertIn(
                    "committed checkout changes paths outside the candidate and "
                    f"publication-output allowlist: {relative}",
                    errors,
                )
                self.assertFalse(evidence["verified"])

    def test_invalid_new_pass_is_not_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_isolated_candidate(Path(temporary))
            errors, snapshot = gate1.build_snapshot(root)
            self.assertEqual([], errors)
            report = passing_report(snapshot)
            report["results"][0]["observed_sha256"] = "0" * 64
            output = root / "report.json"
            with (
                mock.patch.object(gate1, "retrieval_report", return_value=report),
                mock.patch.object(gate1, "write_json") as writer,
            ):
                status = gate1.main([
                    "--root", str(root),
                    "--retrieve",
                    "--source-state", "parent_overlay",
                    "--out", str(output),
                ])
            self.assertEqual(1, status)
            writer.assert_not_called()
            self.assertFalse(output.exists())


class TestGate1MutationsAreDetected(unittest.TestCase):
    def test_duplicate_haspart_is_rejected(self):
        document = manifest("vlbi")
        root = entity(document, "./")
        root["hasPart"].append(copy.deepcopy(root["hasPart"][0]))
        self.assertIn("duplicate hasPart", messages("vlbi", document))

    def test_missing_source_catalog_is_rejected(self):
        document = manifest("pulsar")
        entity(document, "./").pop("ftro:source_catalog")
        self.assertIn("expected source catalog is missing", messages("pulsar", document))

    def test_catalog_removed_from_root_data_entities_is_rejected(self):
        document = manifest("gnss")
        root = entity(document, "./")
        catalog_id = root["ftro:source_catalog"]["@id"]
        root["hasPart"] = [item for item in root["hasPart"] if item["@id"] != catalog_id]
        self.assertIn("source catalog is not a root data entity", messages("gnss", document))

    def test_catalog_digest_corruption_is_rejected(self):
        document = manifest("vlbi")
        catalog_id = entity(document, "./")["ftro:source_catalog"]["@id"]
        entity(document, catalog_id)["ftro:sha256"] = "0" * 64
        result = messages("vlbi", document)
        self.assertIn("not bound to the frozen baseline digest", result)
        self.assertIn("digest does not match", result)

    def test_false_counter_is_rejected(self):
        report = gate1.load_json(REPO_ROOT / "phase0/reports/ppta-artifact-pins.json")
        report["n_failed"] = False
        result = "\n".join(gate1.report_is_clean(report, gate1.report_entries(report)))
        self.assertIn("n_failed is not an integer", result)
        self.assertIn("n_failed is not zero", result)

    def test_catalog_and_manifest_cannot_be_rewritten_together(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPO_ROOT / "phase1/manifests", root / "phase1/manifests")
            (root / "phase0/reports").mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / "phase0/reports/igs-artifact-pins.json",
                root / "phase0/reports/igs-artifact-pins.json",
            )
            report_path = root / "phase0/reports/igs-artifact-pins.json"
            report = gate1.load_json(report_path)
            report["pins"].pop()
            report["n_pinned"] = len(report["pins"])
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

            document = gate1.load_json(gate1.manifest_path(root, "gnss"))
            catalog_id = entity(document, "./")["ftro:source_catalog"]["@id"]
            catalog = entity(document, catalog_id)
            catalog["ftro:sha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
            catalog["ftro:expected_entry_count"] = len(report["pins"])

            result = messages("gnss", document, root)
            self.assertIn("not bound to the frozen baseline digest", result)
            self.assertIn("differs from the frozen baseline", result)
            self.assertIn("expected-entry count is absent or wrong", result)
            self.assertIn("entries, expected 57", result)

    def test_optical_source_removal_is_rejected(self):
        document = manifest("optical")
        missing_id = "git:INRIM/tintervals@2064db12777df78bc87f68f7710a47176192c2e1"
        document["@graph"] = [item for item in document["@graph"] if item["@id"] != missing_id]
        self.assertIn("provider snapshot", messages("optical", document))

    def test_optical_locator_drift_is_rejected(self):
        document = manifest("optical")
        snapshot = entity(document, "https://doi.org/10.5281/zenodo.17107693")
        snapshot["ftro:retrieval_procedure"] = "GET https://example.invalid/archive.zip"
        self.assertIn("locator disagrees", messages("optical", document))

    def test_digest_correct_filler_cannot_replace_a_registered_source(self):
        documents = {domain: manifest(domain) for domain in gate1.DOMAINS}
        gps = entity(
            documents["pulsar"],
            "git:ipta/pulsar-clock-corrections@36dc139a150efde056aa32fa13deac856a7a679d",
        )
        gps["ftro:sha256"] = "cf93ae7a8f934944230e8555941d9d1e1afac9fa59d3a6d15bacd7befbfcee98"
        gps["ftro:retrieval_procedure"] = (
            "GET https://raw.githubusercontent.com/INRIM/optical-link-data-format/"
            "689bda77000fec52c401bc0c9c3664d1dd534ecb/README.md"
        )
        result = "\n".join(gate1.source_population_errors(documents, REPO_ROOT))
        self.assertIn("expected retrieval source is absent", result)
        self.assertIn("unexpected retrieval source is present", result)

    def test_missing_pulsar_source_node_is_rejected_even_with_catalog(self):
        document = manifest("pulsar")
        missing_id = "git:ipta/pulsar-clock-corrections@36dc139a150efde056aa32fa13deac856a7a679d"
        document["@graph"] = [item for item in document["@graph"] if item["@id"] != missing_id]
        self.assertIn("provider snapshot", messages("pulsar", document))

    def test_vlbi_wrapper_digest_drift_is_rejected(self):
        document = manifest("vlbi")
        entity(document, "#wrapper-310c5815")["ftro:sha256"] = "0" * 64
        self.assertIn("wrapper digest population disagrees", messages("vlbi", document))

    def test_vlbi_wrapper_member_and_size_drift_are_rejected(self):
        document = manifest("vlbi")
        wrapper = entity(document, "#wrapper-310c5815")
        wrapper["ftro:member_paths"] = ["missing/member.wrp"]
        wrapper["contentSize"] = "1"
        result = messages("vlbi", document)
        self.assertIn("member paths disagree", result)
        self.assertIn("contentSize disagrees", result)

    def test_unresolved_assertion_without_subject_is_rejected(self):
        document = manifest("pulsar")
        entity(document, "#assertion-eop").pop("ftro:subject")
        self.assertIn("has no subject", messages("pulsar", document))

    def test_unresolved_assertion_not_mentioned_is_rejected(self):
        document = manifest("vlbi")
        root = entity(document, "./")
        root["mentions"] = [
            item for item in root["mentions"] if item["@id"] != "#assertion-downstream-eop"
        ]
        self.assertIn("is not mentioned by the root", messages("vlbi", document))

    def test_anonymous_structured_object_is_rejected(self):
        document = manifest("optical")
        entity(document, "#assertion-comparator-interpretation")["ftro:competing_readings"] = {
            "ftro:interpretation": "hidden blank node"
        }
        self.assertIn("unflattened objects", messages("optical", document))

    def test_dangling_local_reference_is_rejected(self):
        document = manifest("gnss")
        entity(document, "./")["mentions"].append({"@id": "#not-in-the-graph"})
        self.assertIn("dangling local reference", messages("gnss", document))

    def test_profile_reference_drift_is_rejected(self):
        document = manifest("optical")
        entity(document, "./")["conformsTo"] = {"@id": "profile/ftro-graph-profile-v0.0.3.md"}
        self.assertIn("commit-pinned FTRO profile", messages("optical", document))

    def test_normative_validation_cannot_be_claimed_without_evidence(self):
        document = manifest("pulsar")
        entity(document, "#conformance")["ftro:normative_validation_result"] = "passed"
        self.assertIn("must remain explicitly not_run", messages("pulsar", document))

    def test_context_redefinition_is_rejected(self):
        document = manifest("optical")
        document["@context"].append({"ftro": None, "hasPart": "https://example.invalid/rebound"})
        self.assertIn("context is absent, reordered or redefined", messages("optical", document))

    def test_root_domain_relabelling_is_rejected(self):
        document = manifest("pulsar")
        entity(document, "./")["ftro:domain"] = "optical"
        self.assertIn("root domain label", messages("pulsar", document))

    def test_conformance_report_type_removal_is_rejected(self):
        document = manifest("gnss")
        entity(document, "#conformance")["@type"] = "Thing"
        self.assertIn("conformance report is not typed", messages("gnss", document))

    def test_unresolved_assertion_without_relation_is_rejected(self):
        document = manifest("pulsar")
        entity(document, "#assertion-eop").pop("ftro:edge_class")
        self.assertIn("has no declared relation", messages("pulsar", document))

    def test_ppta_concept_member_drift_is_rejected(self):
        document = manifest("pulsar")
        entity(document, "ftro:concept:ppta/dr3")["hasPart"].pop()
        self.assertIn("concept member set disagrees", messages("pulsar", document))

    def test_gnss_product_line_count_drift_is_rejected(self):
        document = manifest("gnss")
        entity(document, "ftro:concept:igs/igr/erp")["ftro:catalog_entry_count"] = 10
        self.assertIn("product-line count", messages("gnss", document))

    def test_gnss_exemplar_field_drift_is_rejected(self):
        document = manifest("gnss")
        identifier = (
            "ftro:snapshot:igs/igr21980.erp.Z@sha256:"
            "d26e4bcc27e763daba4fda77e6a01d3f17c39659b6b4729aa2e731945b11bb5b"
        )
        entity(document, identifier)["contentSize"] = "1"
        self.assertIn("field contentSize disagrees", messages("gnss", document))

    def test_expected_source_must_be_reachable_from_root(self):
        document = manifest("optical")
        root = entity(document, "./")
        target = "git:INRIM/tintervals@2064db12777df78bc87f68f7710a47176192c2e1"
        root["hasPart"] = [item for item in root["hasPart"] if item["@id"] != target]
        root["mentions"] = [item for item in root["mentions"] if item["@id"] != "#edge-context-tintervals"]
        self.assertIn("is unreachable from the root", messages("optical", document))


if __name__ == "__main__":
    unittest.main()
