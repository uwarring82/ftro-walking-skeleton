#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO Phase-0 four-domain support-intersection calculator.
#
# Computes a support envelope for each pilot domain inside the candidate window and the
# pairwise / three- / four-way intersections.
#
# The four legs are NOT computed on a common basis, and the report says so:
#   optical - union of RECORDED TIMESTAMP SPANS of contiguous flag-in-{1,2} runs, under a
#             chosen contiguity rule. Exact with respect to the recorded tags; NOT exact with
#             respect to physical measurement support, because interval/lag/weighting are
#             absent from all 12 comparisons (FTRO-DEF-003), so a tag's placement within its
#             own integration is unconstrained over up to 1 s.
#   vlbi    - scheduled session intervals, NOT per-observation support (UPPER BOUND)
#   gnss    - IGS Final daily product validity, NOT per-epoch support (UPPER BOUND)
#   pulsar  - scan start from the file-name UTC stamp plus the header -tobs
# Card §6's ideal is met fully only by the optical leg. Because two legs are upper
# bounds, any reported overlap is an upper bound, and refining them can only remove
# support - which is what makes an empty intersection robust.
#
# Section 20 forbids widening the interval when the intersection is empty; this tool
# reports the empty result instead.

import datetime
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinning  # noqa: E402
from optical_sensitivity import build_sensitivity  # noqa: E402

W0, W1 = 59630.0, 59640.0
GPS_EPOCH_MJD = 44244

# igsWWWWD.ext.Z -- Final product, GPS week WWWW, day-of-week D (7 = weekly summary).
IGS_FINAL_NAME = re.compile(r"^igs(\d{4})(\d)\.(sp3|clk|erp)\.Z$")


def igs_day_from_name(name):
    """MJD covered by an IGS FINAL daily product, or None. Derived, never trusted."""
    m = IGS_FINAL_NAME.match(name or "")
    if not m:
        return None
    week, dow = int(m.group(1)), int(m.group(2))
    if dow > 6:                      # day 7 is the weekly ERP summary, not a daily product
        return None
    return GPS_EPOCH_MJD + week * 7 + dow
ARCHIVE_ROOT = "data/raw/zenodo-17107693/extracted"
OPTICAL_INVENTORY = "data/work/optical-inventory.json"
OPTICAL_SUMMARY = "phase0/reports/optical-inventory-summary.json"
IVS_SESSIONS = "phase0/reports/ivs-sessions-candidate-window.json"
IGS_PINS = "phase0/reports/igs-artifact-pins.json"
OUT = "phase0/reports/four-domain-intersection.json"

# Pulsar: PPTA DR3 J0437-4715, single observation epoch inside the window.
# Support = scan start (from the file-name UTC stamp) + integration time -tobs.
PULSAR_OBS_START_UTC = "2022-02-20T10:40:59"
PULSAR_TOBS_S = 3843.1
PULSAR_TOA_MJD = [59630.467530701, 59630.467530762]


def utc_to_mjd(s):
    dt = datetime.datetime.fromisoformat(s)
    return (dt - datetime.datetime(1858, 11, 17)).total_seconds() / 86400.0


def merge(ivs):
    ivs = sorted(ivs)
    out = []
    for a, b in ivs:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def isect(A, B):
    out = []
    for a0, a1 in A:
        for b0, b1 in B:
            lo, hi = max(a0, b0), min(a1, b1)
            if hi > lo:
                out.append((lo, hi))
    return merge(out)


def total_h(ivs):
    return round(sum(b - a for a, b in ivs) * 24, 4)


def gnss_support_from_pins(pins):
    """Build the production GNSS support from authenticated artifact names.

    The report's ``series`` and ``mjd`` fields are depositor/tool projections and are
    deliberately ignored.  Both the science pipeline and the M6 audit probe call this
    function so the probe cannot drift into a second implementation of C5.
    """
    days = sorted({day for day in (igs_day_from_name(pin.get("name")) for pin in pins)
                   if day is not None})
    return merge([(float(day), float(day) + 1.0) for day in days])


def pulsar_support():
    """Return the sole production construction of the selected pulsar scan support."""
    start = utc_to_mjd(PULSAR_OBS_START_UTC)
    return [(start, start + PULSAR_TOBS_S / 86400.0)]


def overlap_surface(domains):
    """Compute the main report's complete overlap surface from four domain supports."""
    clipped = {name: isect(intervals, [(W0, W1)])
               for name, intervals in domains.items()}
    keys = sorted(clipped)

    pairwise = {}
    for index, left in enumerate(keys):
        for right in keys[index + 1:]:
            intervals = isect(clipped[left], clipped[right])
            pairwise[f"{left}|{right}"] = {
                "n_intervals": len(intervals),
                "total_hours": total_h(intervals),
                "status": "overlap" if intervals else "no_common_support",
                **({"intervals": intervals} if len(intervals) <= 24 else
                   {"intervals_omitted_for_size": True}),
            }

    three = {}
    for dropped in keys:
        remaining = [name for name in keys if name != dropped]
        intervals = clipped[remaining[0]]
        for name in remaining[1:]:
            intervals = isect(intervals, clipped[name])
        three[f"without_{dropped}"] = {
            "domains": remaining,
            "n_intervals": len(intervals),
            "total_hours": total_h(intervals),
            "status": "overlap" if intervals else "no_common_support",
            **({"intervals": intervals} if len(intervals) <= 24 else
               {"intervals_omitted_for_size": True}),
        }

    four = clipped[keys[0]]
    for name in keys[1:]:
        four = isect(four, clipped[name])

    gap = None
    if clipped["pulsar"] and clipped["optical"] \
            and not isect(clipped["pulsar"], clipped["optical"]):
        pulsar_end = max(end for _, end in clipped["pulsar"])
        optical_start = min(start for start, _ in clipped["optical"])
        gap = {
            "pulsar_support_end_mjd": pulsar_end,
            "optical_support_start_mjd": optical_start,
            "gap_days": round(optical_start - pulsar_end, 6),
            "gap_hours": round((optical_start - pulsar_end) * 24, 3),
        }

    return {
        "clipped": clipped,
        "pairwise": pairwise,
        "three_domain": three,
        "four_domain": {
            "intervals": four,
            "n_intervals": len(four),
            "total_hours": total_h(four),
            "status": "overlap" if four else "no_common_support",
        },
        "pulsar_optical_gap": gap,
    }


def reconcile_surface(surface, sensitivity_row, tolerance, tolerance_h=5e-4):
    """Reconcile every sensitivity quantity that has a main-report counterpart.

    Returning the checked quantity names makes the scope inspectable.  Missing or extra
    keys are disagreements rather than silently reducing the comparison surface.
    """
    disagreements = []
    checked = []

    def compare_number(label, main_value, sensitivity_value):
        checked.append(label)
        if not isinstance(main_value, (int, float)) \
                or not isinstance(sensitivity_value, (int, float)) \
                or isinstance(main_value, bool) or isinstance(sensitivity_value, bool) \
                or abs(main_value - sensitivity_value) > tolerance_h:
            disagreements.append(label)

    expected_domains = set(surface["clipped"])
    observed_domains = set(sensitivity_row.get("domain_h", {}))
    if observed_domains != expected_domains:
        disagreements.append("domain key population")
    for name in sorted(expected_domains):
        compare_number(f"domain {name}", total_h(surface["clipped"][name]),
                       sensitivity_row.get("domain_h", {}).get(name))

    expected_pairs = set(surface["pairwise"])
    observed_pairs = set(sensitivity_row.get("pairwise_h", {}))
    if observed_pairs != expected_pairs:
        disagreements.append("pairwise key population")
    for name in sorted(expected_pairs):
        compare_number(f"pairwise {name}", surface["pairwise"][name]["total_hours"],
                       sensitivity_row.get("pairwise_h", {}).get(name))

    expected_three = set(surface["three_domain"])
    observed_three = set(sensitivity_row.get("three_domain_h", {}))
    if observed_three != expected_three:
        disagreements.append("three-domain key population")
    for name in sorted(expected_three):
        compare_number(f"three-domain {name}",
                       surface["three_domain"][name]["total_hours"],
                       sensitivity_row.get("three_domain_h", {}).get(name))

    four = surface["four_domain"]
    compare_number("four_domain hours", four["total_hours"],
                   sensitivity_row.get("four_domain_h"))
    checked.extend(("four_domain n_intervals", "four_domain status"))
    if sensitivity_row.get("four_domain_n_intervals") != four["n_intervals"]:
        disagreements.append("four_domain n_intervals")
    if sensitivity_row.get("four_domain_status") != four["status"]:
        disagreements.append("four_domain status")

    gap = surface["pulsar_optical_gap"]
    sensitivity_gap = sensitivity_row.get("pulsar_optical_gap_h")
    checked.append("pulsar_optical_gap")
    if gap is None and sensitivity_gap is not None:
        disagreements.append("pulsar_optical_gap")
    elif gap is not None:
        if sensitivity_gap is None or abs(gap["gap_hours"] - sensitivity_gap) > tolerance_h:
            disagreements.append("pulsar_optical_gap")

    return {
        "checked": True,
        "tolerance": tolerance,
        "checked_quantities": checked,
        "disagreements": disagreements,
    }


def main():
    ivs_sessions = json.load(open(IVS_SESSIONS, encoding="utf-8"))
    # Consumer gate: a report that is not a clean success must not become science.
    # This module used to read the IGS report unconditionally, so a failed pinning run
    # produced normal GNSS support (FTRO-DEF-031 v4.0.0).
    igs = pinning.assert_report_usable(
        IGS_PINS, what="IGS pin report",
        registry="phase0/evidence/expected-digests.json", section="igs")

    # Optical: EXACT union of every contiguous valid run across all comparisons.
    # Falls back to per-comparison envelopes (an upper bound) only if the full
    # inventory is absent, and records which basis was used.
    optical_basis = "recorded_timestamp_span_union"
    try:
        inv = json.load(open(OPTICAL_INVENTORY, encoding="utf-8"))
        runs = [(r["mjd_start"], r["mjd_end"])
                for c in inv["comparisons"]
                for r in c["valid_runs_in_candidate_window"]]
        n_runs_input = len(runs)
        optical = merge(runs)
    except FileNotFoundError:
        opt = json.load(open(OPTICAL_SUMMARY, encoding="utf-8"))
        optical_basis = "per_comparison_envelope_UPPER_BOUND"
        n_runs_input = 0
        optical = merge([tuple(c["window_support_envelope_mjd"]) for c in opt["comparisons"]
                         if c["window_support_envelope_mjd"]])

    vlbi = merge([(s["mjd_start"], s["mjd_end"]) for s in ivs_sessions])

    pulsar = pulsar_support()

    # GNSS: IGS daily Final products, each covering one UTC day.
    #
    # series and mjd are DERIVED from the filename, which the registry binds by digest.
    # They were previously read from report fields that nothing authenticated, so
    # relabelling all 57 pins as "igr" -- without touching a name or a digest -- passed
    # every gate and drove GNSS support from 240 h to 0 h (FTRO-DEF-060). A field that is
    # not stored cannot be forged.
    gnss = gnss_support_from_pins(igs["pins"])

    domains = {"optical": optical, "pulsar": pulsar, "vlbi": vlbi, "gnss": gnss}
    surface = overlap_surface(domains)
    clipped = surface["clipped"]

    # Convention sensitivity: RE-SEGMENTS from the raw records at each tolerance.
    # The earlier in-line block re-merged an inventory already segmented at 1.5 s and
    # pooled across comparisons and files, so it could never split a run and could join
    # unrelated series. See FTRO-DEF-030.
    # Domain supports are built ONCE and passed in. Main and sensitivity previously
    # carried separate copies of the pulsar constants, so changing one produced a main
    # `overlap` while every sensitivity row still said no_common_support, with all tests
    # and both gates green (FTRO-DEF-061).
    sensitivity = build_sensitivity(ARCHIVE_ROOT, ivs_sessions, igs,
                                    pulsar_support=pulsar, gnss_support=gnss,
                                    vlbi_support=vlbi)
    pairwise = surface["pairwise"]
    three = surface["three_domain"]
    four_report = surface["four_domain"]
    four = four_report["intervals"]
    gap = surface["pulsar_optical_gap"]

    # Reconcile: the sensitivity row at the SHIPPED convention must reproduce the main
    # computation for every quantity, not just the two that used to be compared.
    shipped = sensitivity["gap_tolerance_scan"].get(str(inv.get("gap_tolerance_s")))
    recon = {"checked": False}
    if shipped:
        full_reconciliation = reconcile_surface(surface, shipped, inv.get("gap_tolerance_s"))
        if full_reconciliation["disagreements"]:
            raise SystemExit("main computation and sensitivity disagree at the shipped "
                             f"convention: {full_reconciliation['disagreements']}. "
                             "One of them is wrong.")
        # Preserve the committed report schema and byte-level deterministic output.  The
        # audit probe consumes ``checked_quantities`` directly from the production helper;
        # the scientific report retains its established public projection.
        recon = {key: full_reconciliation[key]
                 for key in ("checked", "tolerance", "disagreements")}

    report = {
        "generator": "src/ftro/four_domain_intersection.py",
        "main_vs_sensitivity_reconciliation": recon,
        "candidate_window_mjd": [W0, W1],
        "method_note": ("The four legs are not computed on a common basis. Optical is the union "
                        "of RECORDED TIMESTAMP SPANS of contiguous flag-in-{1,2} runs under a "
                        "1.5 s contiguity rule -- exact with respect to the "
                        "recorded tags, not to physical measurement support. VLBI uses scheduled "
                        "session intervals, not per-observation supports, and GNSS uses IGS Final "
                        "daily product validity, not per-epoch support: both are UPPER BOUNDS. "
                        "Pulsar uses scan start from the file-name UTC stamp plus the header "
                        "-tobs. Because two legs are upper bounds, every reported overlap is an "
                        "upper bound; refining them into exact per-observation support can only "
                        "remove overlap. The reported no_common_support is therefore robust under "
                        "these conservative envelopes."),
        "optical_support_basis": optical_basis,
        "optical_runs_merged": {
            "n_input_runs": n_runs_input,
            "n_disjoint_intervals_before_clip": len(optical),
            "n_zero_duration_intervals": sum(1 for a, b in optical if b == a),
            "n_positive_duration_intervals_in_window": len(clipped["optical"]),
            "note": ("merge() emits one interval per run; a run of exactly one sample has "
                     "mjd_end == mjd_start and therefore zero recorded span. isect()'s strict "
                     "hi > lo test drops those at the window clip, which is why the pre-clip "
                     "count exceeds the in-window count."),
        },
        "optical_support_convention": {
            "rule": "maximal runs of flag in {1,2} with inter-sample spacing <= gap_tolerance_s",
            "gap_tolerance_s": inv.get("gap_tolerance_s"),
            "run_span_definition": "first_recorded_tag_to_last_recorded_tag",
            "interval_s": None, "lag": None, "weighting": None, "ref_osc": None,
            "declared_fields_absent_in": "12 of 12 comparisons (FTRO-DEF-003)",
        },
        "optical_exactness_scope": (
            "Exact with respect to the recorded MJD tags under the "
            f"{inv.get('gap_tolerance_s')} s contiguity rule. NOT exact with respect to physical "
            "measurement support: interval, lag and weighting are absent from all 12 "
            "comparisons, so each tag's placement within its own integration is unconstrained "
            "over up to 1 s, and no support is attributed to the trailing integration of any run."),
        "optical_support_sensitivity": sensitivity,
        "bound": {"optical": "derived", "vlbi": "upper", "gnss": "upper", "pulsar": "approximate",
                  "any_intersection_involving_vlbi_or_gnss": "upper",
                  "note": ("optical is 'derived' rather than 'exact': it is exact over recorded "
                           "tags but model-dependent as physical support.")},
        "domain_support": {k: ({"n_intervals": len(v), "total_hours": total_h(v),
                                "envelope_mjd": [min(a for a, _ in v), max(b for _, b in v)],
                                "intervals_omitted_for_size": True}
                               if len(v) > 24 else
                               {"n_intervals": len(v), "intervals": v, "total_hours": total_h(v)})
                           for k, v in clipped.items()},
        "pulsar_toa_mjd_range": PULSAR_TOA_MJD,
        "pairwise": pairwise,
        "three_domain": three,
        "four_domain": four_report,
        "pulsar_optical_gap": gap,
        "alignment_certificate_status": "no_common_support" if not four else "partial",
    }
    json.dump(report, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"wrote {OUT}\n")
    print(f"  optical basis: {optical_basis} ({n_runs_input} runs -> {len(optical)} merged, "
          f"{len(clipped['optical'])} with positive duration in window)")
    for k, v in report["domain_support"].items():
        print(f"  {k:<8} support {v['total_hours']:>8.3f} h  "
              f"({v['n_intervals']} interval(s))")
    print("\n  pairwise:")
    for k, v in pairwise.items():
        print(f"    {k:<20} {v['status']:<18} {v['total_hours']:>8.3f} h")
    print("\n  three-domain:")
    for k, v in three.items():
        print(f"    {k:<20} {v['status']:<18} {v['total_hours']:>8.3f} h")
    print(f"\n  FOUR-DOMAIN: {report['four_domain']['status']} "
          f"({report['four_domain']['total_hours']} h)")
    if gap:
        print(f"  pulsar->optical gap: {gap['gap_hours']} h")


if __name__ == "__main__":
    main()
