#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Focused tests that keep the M6/M7/M8 audit probes on production paths."""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src" / "ftro"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROBES = load_module("ftro_audit_probes_hardened", REPO / "phase0" / "audit" / "probes.py")
import four_domain_intersection as FDI  # noqa: E402
import optical_sensitivity as SENSITIVITY  # noqa: E402


def matching_sensitivity_row(surface):
    """Project a production main surface into the sensitivity row's public shape."""
    return {
        "domain_h": {name: FDI.total_h(intervals)
                     for name, intervals in surface["clipped"].items()},
        "pairwise_h": {name: row["total_hours"]
                       for name, row in surface["pairwise"].items()},
        "three_domain_h": {name: row["total_hours"]
                           for name, row in surface["three_domain"].items()},
        "four_domain_h": surface["four_domain"]["total_hours"],
        "four_domain_n_intervals": surface["four_domain"]["n_intervals"],
        "four_domain_status": surface["four_domain"]["status"],
        **({"pulsar_optical_gap_h": surface["pulsar_optical_gap"]["gap_hours"]}
           if surface["pulsar_optical_gap"] else {}),
    }


class TestM6ProductionSupport(unittest.TestCase):
    def run_probe(self, report):
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as handle:
            json.dump(report, handle)
            handle.flush()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = PROBES.igs_support(SimpleNamespace(report=handle.name))
        return code, output.getvalue()

    def test_probe_calls_the_production_gnss_support_builder(self):
        report = {"pins": [
            {"name": "igs21980.sp3.Z", "series": "igs", "mjd": 59630},
            {"name": "igs21981.sp3.Z", "series": "igs", "mjd": 59631},
        ]}
        with mock.patch.object(FDI, "gnss_support_from_pins",
                               wraps=FDI.gnss_support_from_pins) as production:
            code, output = self.run_probe(report)
        self.assertEqual(code, 0)
        production.assert_called_once_with(report["pins"])
        self.assertIn('"n_days":2', output)
        self.assertIn('"support_hours":48.0', output)

    def test_relabelling_unbound_fields_cannot_change_probe_output(self):
        report = {"pins": [
            {"name": "igs21980.sp3.Z", "series": "igs", "mjd": 59630},
            {"name": "igs21981.clk.Z", "series": "igs", "mjd": 59631},
        ]}
        changed = copy.deepcopy(report)
        for pin in changed["pins"]:
            pin["series"], pin["mjd"] = "igr", 0
        self.assertEqual(self.run_probe(report), self.run_probe(changed))


class TestM7ProductionReconciliation(unittest.TestCase):
    def setUp(self):
        domains = {
            "optical": [(59631.0, 59633.0)],
            "pulsar": [(59630.5, 59631.5)],
            "vlbi": [(59630.0, 59634.0)],
            "gnss": [(59630.0, 59640.0)],
        }
        self.surface = FDI.overlap_surface(domains)
        self.row = matching_sensitivity_row(self.surface)

    def test_pulsar_constants_have_exactly_one_production_home(self):
        homes = PROBES.constant_assignment_homes(
            ("PULSAR_OBS_START_UTC", "PULSAR_TOBS_S"))
        expected = ["src/ftro/four_domain_intersection.py"]
        self.assertEqual(homes, {
            "PULSAR_OBS_START_UTC": expected,
            "PULSAR_TOBS_S": expected,
        })

    def test_reconciliation_checks_the_complete_available_surface(self):
        result = FDI.reconcile_surface(self.surface, self.row, 1.5)
        self.assertEqual(result["disagreements"], [])
        self.assertEqual(len(result["checked_quantities"]), 18)
        self.assertEqual(set(result["checked_quantities"]), {
            "domain gnss", "domain optical", "domain pulsar", "domain vlbi",
            "pairwise gnss|optical", "pairwise gnss|pulsar", "pairwise gnss|vlbi",
            "pairwise optical|pulsar", "pairwise optical|vlbi", "pairwise pulsar|vlbi",
            "three-domain without_gnss", "three-domain without_optical",
            "three-domain without_pulsar", "three-domain without_vlbi",
            "four_domain hours", "four_domain n_intervals", "four_domain status",
            "pulsar_optical_gap",
        })

    def test_each_reconciliation_family_can_disagree(self):
        mutations = {
            "domain pulsar": lambda row: row["domain_h"].__setitem__("pulsar", 999),
            "pairwise optical|pulsar":
                lambda row: row["pairwise_h"].__setitem__("optical|pulsar", 999),
            "three-domain without_vlbi":
                lambda row: row["three_domain_h"].__setitem__("without_vlbi", 999),
            "four_domain hours": lambda row: row.__setitem__("four_domain_h", 999),
            "four_domain n_intervals":
                lambda row: row.__setitem__("four_domain_n_intervals", 999),
            "four_domain status": lambda row: row.__setitem__("four_domain_status", "wrong"),
            "pulsar_optical_gap":
                lambda row: row.__setitem__("pulsar_optical_gap_h", 999),
        }
        for expected, mutation in mutations.items():
            with self.subTest(quantity=expected):
                row = copy.deepcopy(self.row)
                mutation(row)
                result = FDI.reconcile_surface(self.surface, row, 1.5)
                self.assertIn(expected, result["disagreements"])

    def test_missing_or_extra_projection_keys_are_disagreements(self):
        for family, label in (("domain_h", "domain key population"),
                              ("pairwise_h", "pairwise key population"),
                              ("three_domain_h", "three-domain key population")):
            with self.subTest(family=family):
                row = copy.deepcopy(self.row)
                row[family]["rogue"] = 0
                result = FDI.reconcile_surface(self.surface, row, 1.5)
                self.assertIn(label, result["disagreements"])

    def test_probe_calls_production_reconciliation(self):
        args = SimpleNamespace(archive_root=str(REPO / "tests" / "fixtures" / "mini-archive"))
        output = io.StringIO()
        with mock.patch.object(FDI, "reconcile_surface",
                               wraps=FDI.reconcile_surface) as production:
            with contextlib.redirect_stdout(output):
                code = PROBES.m7_coherence(args)
        self.assertEqual(code, 0, output.getvalue())
        production.assert_called_once()
        payload = json.loads(output.getvalue().split("FTRO_M7_COHERENCE ", 1)[1])
        self.assertTrue(payload["one_home"])
        self.assertTrue(payload["coherent"])
        self.assertEqual(len(payload["checked_quantities"]), 18)


class TestM8CalleeOwnedSort(unittest.TestCase):
    def test_production_credit_is_identical_for_deliberately_unsorted_input(self):
        start = SENSITIVITY.W0 + 10 * SENSITIVITY.US_PER_S
        ordered = [start, start + 500_000, start + 2_000_000, start + 2_500_000]
        unsorted = [ordered[2], ordered[0], ordered[3], ordered[1]]
        self.assertNotEqual(unsorted, sorted(unsorted))
        self.assertEqual(SENSITIVITY.per_sample_nominal_credit(unsorted),
                         SENSITIVITY.per_sample_nominal_credit(ordered))

    def test_probe_constructs_disorder_and_reports_the_sorted_oracle_match(self):
        args = SimpleNamespace(archive_root=str(REPO / "tests" / "fixtures" / "mini-archive"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = PROBES.sample_credit(args)
        self.assertEqual(code, 0, output.getvalue())
        payload = json.loads(output.getvalue().split("FTRO_SAMPLE_CREDIT ", 1)[1])
        self.assertTrue(payload["input_was_unsorted"])
        self.assertGreater(payload["input_inversions"], 0)
        self.assertTrue(payload["matches_sorted_oracle"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
