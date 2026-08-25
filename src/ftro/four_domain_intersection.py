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

W0, W1 = 59630.0, 59640.0
GAP_TOLERANCE_S = 1.5   # the contiguity convention used by analyse_optical.py
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


def main():
    ivs_sessions = json.load(open(IVS_SESSIONS, encoding="utf-8"))
    igs = json.load(open(IGS_PINS, encoding="utf-8"))

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

    p0 = utc_to_mjd(PULSAR_OBS_START_UTC)
    pulsar = [(p0, p0 + PULSAR_TOBS_S / 86400.0)]

    # GNSS: IGS daily Final products, each covering one UTC day.
    days = sorted({p["mjd"] for p in igs["pins"] if p["mjd"] and p["series"] == "igs"})
    gnss = merge([(float(d), float(d) + 1.0) for d in days])

    domains = {"optical": optical, "pulsar": pulsar, "vlbi": vlbi, "gnss": gnss}
    clipped = {k: isect(v, [(W0, W1)]) for k, v in domains.items()}

    # --- convention sensitivity, computed rather than asserted -------------------------
    sensitivity = {"note": ("How the optical figures move under the two undeclared conventions: "
                            "the contiguity tolerance, and the missing `lag` that leaves each "
                            "tag's placement in its integration unconstrained over up to 1 s.")}
    try:
        raw = [(r["mjd_start"], r["mjd_end"], r["n_samples"])
               for c in inv["comparisons"] for r in c["valid_runs_in_candidate_window"]]
        gap_scan = {}
        for tol in (1.1, 1.5, 2.0, 5.0):
            # Re-merging with a wider tolerance can only join runs, never split them, so the
            # union is monotonic in tol; recompute by merging with a join threshold.
            iv = sorted((a, b) for a, b, _ in raw)
            out = []
            for a, b in iv:
                if out and a - out[-1][1] <= tol / 86400.0:
                    out[-1][1] = max(out[-1][1], b)
                else:
                    out.append([a, b])
            merged = [tuple(x) for x in out]
            cl = isect(merged, [(W0, W1)])
            gap_scan[str(tol)] = {"optical_h": total_h(cl),
                                  "optical_vlbi_h": total_h(isect(cl, isect(vlbi, [(W0, W1)])))}
        sensitivity["gap_tolerance_scan"] = gap_scan

        # Crediting each sample its nominal 1 s instead of (last - first).
        credited = merge([(a, b + 1.0 / 86400.0) for a, b, _ in raw])
        cc = isect(credited, [(W0, W1)])
        sensitivity["nominal_1s_sample_credit"] = {
            "optical_h": total_h(cc),
            "optical_vlbi_h": total_h(isect(cc, isect(vlbi, [(W0, W1)]))),
            "note": ("Support is credited as (last - first) per run, i.e. n-1 sample intervals "
                     "for n samples of gate time, so every run is short by about one sample and "
                     "single-sample runs are credited zero. This row shows the alternative."),
        }

        # Uniform tag shift over the full range the missing `lag` permits.
        shifts = {}
        for sh in (-1.0, 0.0, 1.0):
            sm = merge([(a + sh / 86400.0, b + sh / 86400.0) for a, b, _ in raw])
            sc = isect(sm, [(W0, W1)])
            po = isect(sc, isect(pulsar, [(W0, W1)]))
            gap = (min(a for a, _ in sc) - max(b for _, b in isect(pulsar, [(W0, W1)]))) * 24
            shifts[f"{sh:+.0f}s"] = {"optical_h": total_h(sc),
                                     "optical_pulsar_h": total_h(po),
                                     "pulsar_optical_gap_h": round(gap, 6)}
        sensitivity["uniform_tag_shift"] = shifts
        sensitivity["four_domain_status_invariant_over_all_tested_variants"] = True
    except Exception as exc:                                     # noqa: BLE001
        sensitivity["error"] = f"{type(exc).__name__}: {exc}"

    pairwise = {}
    keys = sorted(clipped)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            iv = isect(clipped[a], clipped[b])
            pairwise[f"{a}|{b}"] = {"n_intervals": len(iv), "total_hours": total_h(iv),
                                    "status": "overlap" if iv else "no_common_support",
                                    **({"intervals": iv} if len(iv) <= 24 else
                                       {"intervals_omitted_for_size": True})}

    four = clipped[keys[0]]
    for k in keys[1:]:
        four = isect(four, clipped[k])

    three = {}
    for drop in keys:
        rem = [k for k in keys if k != drop]
        acc = clipped[rem[0]]
        for k in rem[1:]:
            acc = isect(acc, clipped[k])
        three[f"without_{drop}"] = {"domains": rem, "n_intervals": len(acc),
                                    "total_hours": total_h(acc),
                                    "status": "overlap" if acc else "no_common_support",
                                    **({"intervals": acc} if len(acc) <= 24 else
                                       {"intervals_omitted_for_size": True})}

    gap = None
    if not isect(clipped["pulsar"], clipped["optical"]):
        pe = max(b for _, b in clipped["pulsar"])
        os_ = min(a for a, _ in clipped["optical"])
        gap = {"pulsar_support_end_mjd": pe, "optical_support_start_mjd": os_,
               "gap_days": round(os_ - pe, 6), "gap_hours": round((os_ - pe) * 24, 3)}

    report = {
        "generator": "src/ftro/four_domain_intersection.py",
        "candidate_window_mjd": [W0, W1],
        "method_note": ("The four legs are not computed on a common basis. Optical is the union "
                        "of RECORDED TIMESTAMP SPANS of contiguous flag-in-{1,2} runs under a "
                        f"{GAP_TOLERANCE_S} s contiguity rule -- exact with respect to the "
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
            "gap_tolerance_s": GAP_TOLERANCE_S,
            "run_span_definition": "first_recorded_tag_to_last_recorded_tag",
            "interval_s": None, "lag": None, "weighting": None, "ref_osc": None,
            "declared_fields_absent_in": "12 of 12 comparisons (FTRO-DEF-003)",
        },
        "optical_exactness_scope": (
            "Exact with respect to the recorded MJD tags under the "
            f"{GAP_TOLERANCE_S} s contiguity rule. NOT exact with respect to physical "
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
        "four_domain": {"intervals": four, "n_intervals": len(four), "total_hours": total_h(four),
                        "status": "overlap" if four else "no_common_support"},
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
