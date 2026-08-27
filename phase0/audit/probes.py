#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Small, explicit detector commands used by the frozen Phase-0 audit recipes.

Each subcommand prints a start marker before touching the property under test.  The
audit runner uses that marker to distinguish a detector that ran from a missing file,
an import failure, or a command that collected no tests.
"""

import argparse
import ast
import json
import os
from pathlib import Path
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "src", "ftro"))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def report_usable(args):
    import pinning

    print("FTRO_PROBE_STARTED report_usable", flush=True)
    try:
        pinning.assert_report_usable(
            args.report,
            what="audit-mutated report",
            registry=args.registry,
            section=args.section,
        )
    except SystemExit as exc:
        print(f"FTRO_REPORT_REJECTED {exc}")
        return 20
    print("FTRO_REPORT_ACCEPTED")
    return 0


def igs_support(args):
    import four_domain_intersection as fdi

    print("FTRO_PROBE_STARTED igs_support", flush=True)
    with open(args.report, encoding="utf-8") as handle:
        report = json.load(handle)
    support = fdi.gnss_support_from_pins(report["pins"])
    clipped = fdi.isect(support, [(fdi.W0, fdi.W1)])
    support_hours = fdi.total_h(clipped)
    result = {
        "intervals": clipped,
        "n_days": round(support_hours / 24),
        "support_hours": support_hours,
    }
    print("FTRO_IGS_SUPPORT " + canonical(result))
    return 0


def constant_assignment_homes(names):
    """Return every assignment home for named production constants."""
    homes = {name: [] for name in names}
    source_root = Path(REPO, "src", "ftro")
    for path in sorted(source_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for statement in ast.walk(tree):
            targets = statement.targets if isinstance(statement, ast.Assign) else \
                [statement.target] if isinstance(statement, ast.AnnAssign) else []
            for target in targets:
                if isinstance(target, ast.Name) and target.id in homes:
                    homes[target.id].append(path.relative_to(REPO).as_posix())
    return homes


def m7_coherence(args):
    import four_domain_intersection as fdi
    import optical_sensitivity as sensitivity

    print("FTRO_PROBE_STARTED m7_coherence", flush=True)
    pulsar = fdi.pulsar_support()
    start = pulsar[0][0]
    vlbi = [(59630.0, 59635.0)]
    gnss = [(59630.0, 59640.0)]

    seg = sensitivity.Resegmenter(args.archive_root)
    optical_us = sensitivity.span_union(seg.runs(1.5))
    optical_mjd = [(a / sensitivity.US_PER_DAY, b / sensitivity.US_PER_DAY)
                   for a, b in optical_us]
    domains = {
        "optical": optical_mjd,
        "pulsar": pulsar,
        "vlbi": vlbi,
        "gnss": gnss,
    }
    surface = fdi.overlap_surface(domains)

    scan = sensitivity.build_sensitivity(
        args.archive_root, [], {}, pulsar_support=pulsar,
        gnss_support=gnss, vlbi_support=vlbi,
    )["gap_tolerance_scan"]["1.5"]
    reconciliation = fdi.reconcile_surface(surface, scan, 1.5)
    homes = constant_assignment_homes(("PULSAR_OBS_START_UTC", "PULSAR_TOBS_S"))
    expected_home = ["src/ftro/four_domain_intersection.py"]
    one_home = all(found == expected_home for found in homes.values())
    main_domain_h = {name: fdi.total_h(intervals)
                     for name, intervals in surface["clipped"].items()}
    main_pairwise_h = {name: row["total_hours"]
                       for name, row in surface["pairwise"].items()}
    main_three_h = {name: row["total_hours"]
                    for name, row in surface["three_domain"].items()}
    coherent = not reconciliation["disagreements"] and one_home
    result = {
        "pulsar_start_utc": fdi.PULSAR_OBS_START_UTC,
        "pulsar_start_mjd": round(start, 9),
        "constant_homes": homes,
        "one_home": one_home,
        "main_surface": {
            "domain_h": main_domain_h,
            "pairwise_h": main_pairwise_h,
            "three_domain_h": main_three_h,
            "four_domain_h": surface["four_domain"]["total_hours"],
            "four_domain_n_intervals": surface["four_domain"]["n_intervals"],
            "four_domain_status": surface["four_domain"]["status"],
            "pulsar_optical_gap_h": (
                surface["pulsar_optical_gap"]["gap_hours"]
                if surface["pulsar_optical_gap"] else None),
        },
        "sensitivity_surface": {
            key: scan.get(key) for key in (
                "domain_h", "pairwise_h", "three_domain_h", "four_domain_h",
                "four_domain_n_intervals", "four_domain_status",
                "pulsar_optical_gap_h")
        },
        "checked_quantities": reconciliation["checked_quantities"],
        "disagreements": reconciliation["disagreements"],
        "coherent": coherent,
    }
    print("FTRO_M7_COHERENCE " + canonical(result))
    return 0 if coherent else 21


def sample_credit(args):
    import optical_sensitivity as sensitivity

    print("FTRO_PROBE_STARTED sample_credit", flush=True)
    seg = sensitivity.Resegmenter(args.archive_root)
    ordered = sorted(seg.window_stamps_us())
    # Construct disorder here rather than hoping file traversal happens to provide it.
    # Sorting `ordered` first makes the probe output independent of the M8 caller-sort
    # mutation; the callee must then recover the same union from this fixed permutation.
    stamps = ordered[1::2] + ordered[::2]
    inversions = sum(left > right for left, right in zip(stamps, stamps[1:]))
    expected = sensitivity.per_sample_nominal_credit(ordered)
    credited = sensitivity.per_sample_nominal_credit(stamps)
    input_was_unsorted = stamps != ordered and inversions > 0
    matches_sorted_oracle = credited == expected
    result = {
        "n_stamps": len(stamps),
        "input_inversions": inversions,
        "input_was_unsorted": input_was_unsorted,
        "matches_sorted_oracle": matches_sorted_oracle,
        "n_intervals": len(credited),
        "total_hours": sensitivity.h6(credited),
        "first": credited[0] if credited else None,
        "last": credited[-1] if credited else None,
    }
    print("FTRO_SAMPLE_CREDIT " + canonical(result))
    return 0 if input_was_unsorted and matches_sorted_oracle else 22


def readme_order(args):
    print("FTRO_PROBE_STARTED readme_order", flush=True)
    with open(args.readme, encoding="utf-8") as handle:
        text = handle.read()

    requirements = [
        ("python3 src/ftro/pin_evidence_repos.py",
         "python3 src/ftro/verify_gps2utc.py"),
        ('curl --fail --show-error --location',
         'md5 "ROCIT campaign results.zip"'),
        ('mkdir -p data/raw/zenodo-17107693',
         'unzip -d data/raw/zenodo-17107693/extracted'),
        ("python3 src/ftro/analyse_optical.py",
         "python3 src/ftro/summarise_optical.py"),
        ("python3 src/ftro/pin_igs.py",
         "python3 src/ftro/four_domain_intersection.py"),
        ("python3 src/ftro/render_deficiencies.py",
         "python3 src/ftro/refresh_crate.py --check"),
    ]
    failures = []
    for producer, consumer in requirements:
        p_at, c_at = text.find(producer), text.find(consumer)
        if p_at < 0 or c_at < 0:
            failures.append({"producer": producer, "consumer": consumer,
                             "reason": "command_missing"})
        elif p_at >= c_at:
            failures.append({"producer": producer, "consumer": consumer,
                             "reason": "consumer_not_after_producer"})
    if failures:
        print("FTRO_README_PIPELINE_OUT_OF_ORDER " + canonical(failures))
        return 20
    print(f"FTRO_README_PIPELINE_OK {len(requirements)}")
    return 0


def parser():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="probe", required=True)

    p = sub.add_parser("report-usable")
    p.add_argument("--report", required=True)
    p.add_argument("--registry", required=True)
    p.add_argument("--section", required=True)
    p.set_defaults(func=report_usable)

    p = sub.add_parser("igs-support")
    p.add_argument("--report", required=True)
    p.set_defaults(func=igs_support)

    p = sub.add_parser("m7-coherence")
    p.add_argument("--archive-root", default="tests/fixtures/mini-archive")
    p.set_defaults(func=m7_coherence)

    p = sub.add_parser("sample-credit")
    p.add_argument("--archive-root", default="tests/fixtures/mini-archive")
    p.set_defaults(func=sample_credit)

    p = sub.add_parser("readme-order")
    p.add_argument("--readme", default="README.md")
    p.set_defaults(func=readme_order)
    return ap


if __name__ == "__main__":
    arguments = parser().parse_args()
    raise SystemExit(arguments.func(arguments))
