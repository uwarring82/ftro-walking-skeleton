#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""False-PASS regressions for the Phase-0 C9 live-run recorder."""

import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]


def load_module():
    path = REPO / "phase0" / "audit" / "run_c9.py"
    spec = importlib.util.spec_from_file_location("ftro_c9_hardening", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


C9 = load_module()


def load_qualification_module():
    path = REPO / "phase0" / "audit" / "check_qualification.py"
    spec = importlib.util.spec_from_file_location("ftro_qualification_hardening", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUALIFICATION = load_qualification_module()


def load_refresh_module():
    path = REPO / "src" / "ftro" / "refresh_crate.py"
    spec = importlib.util.spec_from_file_location("ftro_refresh_crate_hardening", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REFRESH_CRATE = load_refresh_module()


class TestC9FreshEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ftro-c9-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    @staticmethod
    def digest(label):
        return hashlib.sha256(label.encode()).hexdigest()

    def population(self):
        return {
            "evidence_repos": {"repo": self.digest("repo")},
            "igs": {"igs.dat": self.digest("igs")},
            "ppta": {"ppta.dat": self.digest("ppta")},
            "vgosdb": {"vlbi.tgz": self.digest("vlbi")},
        }

    def pin(self, section, identifier, digest, timestamp):
        identity = {
            "evidence_repos": {"key": identifier, "url": "https://example.invalid/repo"},
            "igs": {"name": identifier, "url": "https://example.invalid/igs"},
            "ppta": {"name": identifier, "url": "https://example.invalid/ppta"},
            "vgosdb": {"url": f"https://example.invalid/{identifier}"},
        }[section]
        return {
            **identity,
            "http_status": 200,
            "retrieved_utc": timestamp,
            "size_bytes": 10,
            "sha256": digest,
            "expected_sha256": digest,
            "checksum_match": True,
            "retrieval_validation": "content_validated",
        }

    def write_full_reports(self, timestamp):
        population = self.population()
        for section, config in C9.PIN_REPORTS.items():
            path = self.root / config["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            identifier, digest = next(iter(population[section].items()))
            pin = self.pin(section, identifier, digest, timestamp)
            if section == "vgosdb":
                document = {**pin, "n_failed": 0, "n_pinned": 1,
                            "retrieval_validation": "content_validated"}
            else:
                document = {"pins": [pin], "n_failed": 0, "n_pinned": 1,
                            "retrieval_validation": "content_validated"}
            path.write_text(json.dumps(document), encoding="utf-8")

    def test_missing_fresh_report_is_an_error_not_a_silent_skip(self):
        population = self.population()
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, records, errors = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", population,
            )
        self.assertEqual(attempts, [])
        self.assertEqual(len(records), 4)
        self.assertEqual(len(errors), 4)
        self.assertTrue(all("no fresh" in error for error in errors))

    def test_exact_fresh_population_is_externally_rechecked(self):
        timestamp = "2026-08-27T10:00:01+00:00"
        self.write_full_reports(timestamp)
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, records, errors = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", self.population(),
            )
        self.assertEqual(errors, [])
        self.assertEqual(len(attempts), 4)
        self.assertTrue(all(row["failure_class"] == "success" for row in attempts))
        self.assertTrue(all(row["fresh"] and row["promoted"] for row in records))
        self.assertEqual({row["source_group"] for row in attempts}, set(C9.PIN_REPORTS))

    def test_stale_committed_report_cannot_be_fresh_evidence(self):
        self.write_full_reports("2026-08-26T10:00:00+00:00")
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, records, errors = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", self.population(),
            )
        self.assertEqual(attempts, [])
        self.assertEqual(len(errors), 4)
        self.assertTrue(all(not row["fresh"] for row in records))

    def test_fabricated_matching_report_digest_fails_external_registry_check(self):
        timestamp = "2026-08-27T10:00:01+00:00"
        self.write_full_reports(timestamp)
        path = self.root / C9.PIN_REPORTS["igs"]["path"]
        report = json.loads(path.read_text(encoding="utf-8"))
        fabricated = self.digest("fabricated")
        report["pins"][0]["sha256"] = fabricated
        report["pins"][0]["expected_sha256"] = fabricated
        path.write_text(json.dumps(report), encoding="utf-8")
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, _, errors = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", self.population(),
            )
        igs = next(row for row in attempts if row["artifact"] == "igs.dat")
        self.assertNotEqual(igs["failure_class"], "success")
        self.assertTrue(any(error.startswith("igs:") for error in errors))

    def test_rejected_list_report_uses_error_and_http_evidence(self):
        path = self.root / C9.PIN_REPORTS["igs"]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path = Path(str(path) + ".rejected")
        digest = self.population()["igs"]["igs.dat"]
        path.write_text(json.dumps({
            "pins": [],
            "failures": [{
                "name": "igs.dat",
                "url": "https://example.invalid/igs.dat",
                "http_status": 200,
                "size_bytes": 12,
                "sha256": "f" * 64,
                "expected_sha256": digest,
                "retrieved_utc": "2026-08-27T10:00:01+00:00",
                "error": "content validation failed: response is HTML",
            }],
            "n_failed": 1,
            "retrieval_validation": "content_validation_incomplete",
        }), encoding="utf-8")
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, _, _ = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", self.population(),
            )
        attempt = next(row for row in attempts if row.get("source_group") == "igs")
        self.assertEqual(attempt["reason"], "content validation failed: response is HTML")
        self.assertEqual(attempt["failure_class"], "content_validation_failure")
        self.assertEqual(attempt["reachability_stage"], "bytes_received")
        self.assertEqual(attempt["expected_sha256"], digest)

    def test_rejected_single_report_uses_top_reason_without_duplicate_attempt(self):
        path = self.root / C9.PIN_REPORTS["vgosdb"]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path = Path(str(path) + ".rejected")
        digest = self.population()["vgosdb"]["vlbi.tgz"]
        path.write_text(json.dumps({
            "url": "https://example.invalid/vlbi.tgz",
            "http_status": 200,
            "size_bytes": 12,
            "sha256": "f" * 64,
            "expected_sha256": digest,
            "retrieved_utc": "2026-08-27T10:00:01+00:00",
            "retrieval_validation": "content_rejected",
            "rejected_reason": "content-shape validation failed",
            "n_pinned": 0,
            "n_failed": 1,
            "failures": [{"url": "https://example.invalid/vlbi.tgz",
                          "reason": "see rejected_reason"}],
        }), encoding="utf-8")
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, _, _ = C9.provider_report_evidence(
                "2026-08-27T10:00:00+00:00", self.population(),
            )
        rows = [row for row in attempts if row.get("source_group") == "vgosdb"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["artifact"], "vlbi.tgz")
        self.assertEqual(rows[0]["reason"], "content-shape validation failed")
        self.assertEqual(rows[0]["failure_class"], "content_validation_failure")
        self.assertEqual(rows[0]["reachability_stage"], "bytes_received")

    def test_current_rejected_report_without_embedded_timestamp_uses_file_freshness(self):
        path = self.root / C9.PIN_REPORTS["ppta"]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path = Path(str(path) + ".rejected")
        path.write_text(json.dumps({
            "pins": [], "failures": [{"name": "ppta.dat", "error": "timed out"}],
            "n_failed": 1, "retrieval_validation": "content_validation_incomplete",
        }), encoding="utf-8")
        started = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=1)).isoformat()
        with mock.patch.object(C9, "ROOT", self.root):
            attempts, records, _ = C9.provider_report_evidence(started, self.population())
        ppta_record = next(row for row in records if row["section"] == "ppta")
        ppta_attempt = next(row for row in attempts if row.get("source_group") == "ppta")
        self.assertTrue(ppta_record["fresh"])
        self.assertEqual(ppta_attempt["failure_class"], "transport_failure")


class TestC9ProductionProof(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ftro-c9-output-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_removed_deterministic_output_must_be_recreated_byte_identically(self):
        relative = "phase0/reports/four-domain-intersection.json"
        target = self.root / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b"expected\n")
        expected = {relative: b"expected\n"}
        with mock.patch.object(C9, "ROOT", self.root):
            prepared = C9.prepare_regenerated_outputs(5, expected)
            missing = C9.verify_regenerated_outputs(5, expected)
            target.write_bytes(b"wrong\n")
            wrong = C9.verify_regenerated_outputs(5, expected)
            target.write_bytes(b"expected\n")
            right = C9.verify_regenerated_outputs(5, expected)
        self.assertEqual([row["path"] for row in prepared], [relative])
        self.assertFalse(missing[0]["recreated"])
        self.assertFalse(wrong[0]["match"])
        self.assertTrue(right[0]["match"])

    def test_optical_summary_is_byte_deterministic_not_existence_only(self):
        relative = "phase0/reports/optical-inventory-summary.json"
        target = self.root / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(b'{"expected": true}\n')
        expected = {relative: target.read_bytes()}
        with mock.patch.object(C9, "ROOT", self.root):
            C9.prepare_regenerated_outputs(3, expected)
            target.write_bytes(b'{"wrong": true}\n')
            wrong = C9.verify_regenerated_outputs(3, expected)
            target.write_bytes(expected[relative])
            right = C9.verify_regenerated_outputs(3, expected)
        self.assertFalse(wrong[0]["match"])
        self.assertTrue(right[0]["match"])
        self.assertIn("step3_optical_summary", C9.DETERMINISTIC)

    def test_optical_identity_never_infers_public_access(self):
        optical = {
            "md5_match": True,
            "http_status": 200,
            "effective_url": "https://example.invalid/archive.zip",
            "content_type": "application/zip",
            "size_bytes": 10,
            "expected_md5": "a" * 32,
            "md5": "a" * 32,
            "sha256": "b" * 64,
        }
        attempt = C9.optical_attempt(optical, [3])
        self.assertEqual(attempt["failure_class"], "success")
        self.assertEqual(attempt["access_class_conclusion"], "not_established")
        self.assertEqual(attempt["access_evidence"], "anonymous_request_succeeded")
        self.assertEqual(attempt["source_group"], "optical")

    def test_transport_has_priority_over_prior_checksum_text(self):
        failure, reachability = C9.classify_failure(
            4, "checksum_match: true\nCould not resolve host: provider.invalid",
        )
        self.assertEqual(failure, "transport_failure")
        self.assertEqual(reachability, "dns_failed")

    def test_curl_http_marker_is_single_and_machine_readable(self):
        record = {
            "stdout_text": (
                "FTRO_CURL_HTTP 200 https://example.invalid/a.zip "
                "application/zip 140736196\n"
            )
        }
        parsed = C9.optical_http_evidence(record)
        self.assertEqual(parsed["http_status"], 200)
        self.assertEqual(parsed["curl_size_download"], 140736196)

    def test_timeout_terminates_process_group_before_it_can_write_late_bytes(self):
        marker = self.root / "late-provider-byte"
        script = f"(sleep 0.5; printf late > {shlex.quote(str(marker))}) & sleep 60"
        environment = {"PATH": os.environ["PATH"], "LC_ALL": "C"}
        with mock.patch.object(C9, "ROOT", self.root):
            result = C9.run_step(
                {"step": 4, "script": script}, environment,
                timeout_s=0.1, termination_grace_s=0.2,
            )
        time.sleep(0.7)
        self.assertIsNone(result["exit_code"])
        self.assertTrue(result["process_group"]["isolated"])
        termination = result["process_group"]["timeout_termination"]
        self.assertTrue(termination["reaped"])
        self.assertIsNone(termination["error"])
        self.assertFalse(marker.exists())

    def test_toolchain_records_the_exact_pipeline_shell(self):
        with mock.patch.dict(os.environ, {"PATH": os.environ["PATH"]}, clear=True):
            evidence = C9.toolchain_evidence()
        shell = next(row for row in evidence["tools"] if row["name"] == "shell")
        self.assertEqual(shell["invocation_path"], C9.PIPELINE_SHELL)
        self.assertEqual(shell["probe_output"], "FTRO_C9_SHELL_PROBE")
        self.assertEqual(shell["sha256"], C9.digest_file(Path(C9.PIPELINE_SHELL).resolve()))


class TestVolatileCrateSizes(unittest.TestCase):
    def test_live_pin_reports_omit_unstable_content_size(self):
        crate = json.loads((REPO / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        graph = {row["@id"]: row for row in crate["@graph"]}
        self.assertEqual(REFRESH_CRATE.VOLATILE_CONTENT_SIZE, C9.PIN_REPORT_PATHS)
        for path in REFRESH_CRATE.VOLATILE_CONTENT_SIZE:
            self.assertNotIn("contentSize", graph[path])

    def test_refresh_check_ignores_live_report_length_drift(self):
        relative = "phase0/reports/igs-artifact-pins.json"
        with tempfile.TemporaryDirectory(prefix="ftro-crate-volatile-test-") as temporary:
            root = Path(temporary)
            target = root / relative
            target.parent.mkdir(parents=True)
            target.write_text("{}", encoding="utf-8")
            (root / "ro-crate-metadata.json").write_text(json.dumps({
                "@graph": [{"@id": relative, "@type": "File"}],
            }), encoding="utf-8")
            for body in ("{}", '{"retrieved_utc":"a much longer live value"}'):
                target.write_text(body, encoding="utf-8")
                completed = subprocess.run(
                    [sys.executable, str(REPO / "src/ftro/refresh_crate.py"), "--check"],
                    cwd=root, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


class TestControllerStartup(unittest.TestCase):
    def test_entrypoints_do_not_create_ignored_bytecode_before_preflight(self):
        with tempfile.TemporaryDirectory(prefix="ftro-controller-startup-") as temporary:
            root = Path(temporary)
            audit = root / "phase0" / "audit"
            audit.mkdir(parents=True)
            for name in ("run_c9.py", "run.py", "check_qualification.py", "c9_contract.py"):
                shutil.copy2(REPO / "phase0" / "audit" / name, audit / name)
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            for name in ("run_c9.py", "run.py", "check_qualification.py"):
                completed = subprocess.run(
                    [sys.executable, str(audit / name), "--help"], cwd=root,
                    capture_output=True, text=True, env=environment,
                )
                self.assertEqual(completed.returncode, 0,
                                 completed.stdout + completed.stderr)
                self.assertEqual(list(root.rglob("__pycache__")), [])
                self.assertEqual(list(root.rglob("*.pyc")), [])


class TestQualificationPair(unittest.TestCase):
    def test_copying_one_pass_twice_cannot_count_as_two(self):
        calibration = {
            "ended_utc": "2026-08-27T10:00:00+00:00",
            "subject": {"checkout_realpath": "/tmp/calibration"},
        }
        one = {
            "sha256": "a" * 64,
            "run_id": "qualifying-1",
            "checkout_realpath": "/tmp/q1",
            "started_utc": "2026-08-27T10:01:00+00:00",
        }
        errors = QUALIFICATION.pair_invariants(
            calibration, [one, dict(one)],
            checker_subject={"checkout_realpath": "/tmp/checker"},
            c9_document={"subject": {"checkout_realpath": "/tmp/c9"}},
        )
        self.assertIn("qualifying report byte digests are not distinct", errors)
        self.assertIn("qualifying run IDs are not distinct", errors)
        self.assertIn("qualifying checkout identities are not distinct", errors)

    def test_two_later_distinct_checkouts_satisfy_pair_invariants(self):
        calibration = {
            "ended_utc": "2026-08-27T10:00:00+00:00",
            "subject": {"checkout_realpath": "/tmp/calibration"},
        }
        rows = [
            {"sha256": "a" * 64, "run_id": "q1", "checkout_realpath": "/tmp/q1",
             "started_utc": "2026-08-27T10:01:00+00:00"},
            {"sha256": "b" * 64, "run_id": "q2", "checkout_realpath": "/tmp/q2",
             "started_utc": "2026-08-27T10:02:00+00:00"},
        ]
        self.assertEqual(QUALIFICATION.pair_invariants(
            calibration, rows,
            checker_subject={"checkout_realpath": "/tmp/checker"},
            c9_document={"subject": {"checkout_realpath": "/tmp/c9"}},
        ), [])

    def test_final_checker_must_be_a_fifth_distinct_checkout(self):
        calibration = {
            "ended_utc": "2026-08-27T10:00:00+00:00",
            "subject": {"checkout_realpath": "/tmp/calibration"},
        }
        rows = [
            {"sha256": "a" * 64, "run_id": "q1", "checkout_realpath": "/tmp/q1",
             "started_utc": "2026-08-27T10:01:00+00:00"},
            {"sha256": "b" * 64, "run_id": "q2", "checkout_realpath": "/tmp/q2",
             "started_utc": "2026-08-27T10:02:00+00:00"},
        ]
        for reused in ("/tmp/c9", "/tmp/calibration", "/tmp/q1", "/tmp/q2"):
            with self.subTest(reused=reused):
                errors = QUALIFICATION.pair_invariants(
                    calibration, rows,
                    checker_subject={"checkout_realpath": reused},
                    c9_document={"subject": {"checkout_realpath": "/tmp/c9"}},
                )
                self.assertIn("qualification checker did not use a distinct checkout", errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
