#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Corrected optical-convention sensitivity scan for the FTRO four-domain report.

Replaces the gap_tolerance_scan / nominal_1s_sample_credit block of
src/ftro/four_domain_intersection.py.

Why the replacement is needed
-----------------------------
The committed block re-merged the runs of an inventory that analyse_optical.py had
ALREADY segmented at its own --gap-tolerance-s (1.5 s), pooling them across every
comparison and every .dat file. That construction is wrong twice over:

  * it can never SPLIT a run, so no tolerance below the inventory's own can be
    probed -- 1.1 s is structurally forced to equal 1.5 s rather than found equal;
  * it JOINS runs belonging to different comparisons and different files, inventing
    support in a hole that no single measurement series covered.

The correct probe re-segments from the 9,018,290 raw records at each tolerance,
using analyse_optical's own contiguous_runs() so the convention under test is
literally the shipped one, and then rebuilds the union and every intersection.

Arithmetic
----------
Times are integer MICROSECONDS since MJD 0. Every MJD token in the archive carries
exactly six decimals and is an exact multiple of 1e-6 d (9018290/9018290 conforming,
FTRO-DEF-002), 1e-6 d == 86400 us exactly, and the 1 s nominal gate == 1000000 us
exactly. Nothing here rounds.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys

US_PER_DAY = 86_400_000_000
US_PER_S = 1_000_000
W0_MJD, W1_MJD = 59630.0, 59640.0
W0, W1 = int(W0_MJD) * US_PER_DAY, int(W1_MJD) * US_PER_DAY
WINDOW = [(W0, W1)]

GAP_TOLERANCES_S = (1.1, 1.5, 2.0, 5.0)
TAG_SHIFTS_S = (-1.0, 0.0, 1.0)

PULSAR_OBS_START_UTC = "2022-02-20T10:40:59"
PULSAR_TOBS_S = 3843.1


# --------------------------------------------------------------------------- exact interval algebra
def to_us(mjd: float) -> int:
    """Exact us from a 1e-6 d-quantised MJD float (float error ~1 us << 43200 us)."""
    return round(mjd * 1e6) * 86400


def merge(ivs, join_us: int = 0):
    """Union; `join_us` bridges gaps up to that width (0 = touch-or-overlap only)."""
    out = []
    for a, b in sorted(ivs):
        if out and a - out[-1][1] <= join_us:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def isect(A, B):
    """Sweep intersection of two sorted, disjoint interval lists. O(n+m)."""
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if hi > lo:
            out.append((lo, hi))
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


def isect_all(lists):
    acc = lists[0]
    for nxt in lists[1:]:
        acc = isect(acc, nxt)
    return acc


def hours(ivs) -> float:
    return sum(b - a for a, b in ivs) / 3_600_000_000


def h6(ivs) -> float:
    return round(hours(ivs), 6)


# --------------------------------------------------------------------------- re-segmentation
def _load_analyse_optical(src="src/ftro/analyse_optical.py"):
    """Import the shipped analyser as a module so the convention under test IS the shipped one."""
    spec = importlib.util.spec_from_file_location("ftro_analyse_optical", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Resegmenter:
    """Re-segments the raw archive at any tolerance.

    Default path imports analyse_optical and calls its own parse_dat/contiguous_runs,
    reading the 446 MB tree ONCE and caching the in-window (mjd, flag) samples, so a
    four-point scan costs one pass rather than four. `subprocess_runs()` is the
    independent cross-check: it shells out to analyse_optical.py exactly as an
    operator would and reads the resulting inventory back.
    """

    def __init__(self, root, src="src/ftro/analyse_optical.py"):
        self.root = root
        self.src = src
        self.ao = _load_analyse_optical(src)
        self._cache = None

    def _window_samples(self):
        """[(comparison, file, [mjd...], [flag...])] for files touching the window."""
        if self._cache is not None:
            return self._cache
        cache = []
        for name in sorted(os.listdir(self.root)):
            cdir = os.path.join(self.root, name)
            if not os.path.isdir(cdir):
                continue
            for fn in sorted(os.listdir(cdir)):
                if not fn.endswith(".dat"):
                    continue
                _hdr, rows, _bad = self.ao.parse_dat(os.path.join(cdir, fn))
                if not rows:
                    continue
                mjds = [r[0] for r in rows]
                if not (max(mjds) >= W0_MJD and min(mjds) <= W1_MJD):
                    continue
                w = [(m, r[2]) for m, r in zip(mjds, rows) if W0_MJD <= m <= W1_MJD]
                if w:
                    cache.append((name, fn, [m for m, _ in w], [f for _, f in w]))
        self._cache = cache
        return cache

    def runs(self, gap_tol_s):
        """[(start_us, end_us, n_samples, comparison, file)] segmented at gap_tol_s."""
        out = []
        for comp, fn, mjds, flags in self._window_samples():
            for s, e, n in self.ao.contiguous_runs(mjds, flags, keep={1, 2},
                                                   gap_tol_s=gap_tol_s):
                out.append((to_us(s), to_us(e), n, comp, fn))
        return out

    def subprocess_runs(self, gap_tol_s, out_json):
        """Cross-check path: shell out to analyse_optical.py, then read its inventory."""
        subprocess.run([sys.executable, self.src, "--root", self.root,
                        "--out", out_json, "--gap-tolerance-s", str(gap_tol_s)],
                       check=True)
        inv = json.load(open(out_json, encoding="utf-8"))
        return [(to_us(r["mjd_start"]), to_us(r["mjd_end"]), r["n_samples"],
                 c["comparison"], r["file"])
                for c in inv["comparisons"] for r in c["valid_runs_in_candidate_window"]]

    def window_stamps_us(self):
        """Every valid in-window tag, as exact us. Segmentation-independent."""
        out = []
        for _c, _f, mjds, flags in self._window_samples():
            out.extend(to_us(m) for m, fl in zip(mjds, flags) if fl in {1, 2})
        out.sort()
        return out


# --------------------------------------------------------------------------- optical bases
def span_union(runs):
    """Recorded first-tag..last-tag spans, unioned. The report's primary basis."""
    return isect(merge([(a, b) for a, b, *_ in runs]), WINDOW)


def run_span_plus_trailing_gate(runs):
    """Each RUN extended 1 s past its last tag. What the committed row actually computed."""
    return isect(merge([(a, b + US_PER_S) for a, b, *_ in runs]), WINDOW)


def per_run_nominal_block(runs):
    """Each run repacked as n contiguous nominal gates from its first tag."""
    return isect(merge([(a, a + n * US_PER_S) for a, _b, n, *_ in runs]), WINDOW)


def per_sample_nominal_credit(stamps_us):
    """Union of [t, t+1 s) over EVERY valid tag. Independent of the contiguity rule."""
    out = []
    for m in stamps_us:
        if out and m <= out[-1][1]:
            out[-1][1] = max(out[-1][1], m + US_PER_S)
        else:
            out.append([m, m + US_PER_S])
    return isect([(a, b) for a, b in out], WINDOW)


# --------------------------------------------------------------------------- four-domain, per variant
def four_domain(optical, vlbi, gnss, pulsar):
    """Every leg, every pairwise, three- and four-way overlap. COMPUTED, never asserted."""
    dom = {"optical": optical, "pulsar": pulsar, "vlbi": vlbi, "gnss": gnss}
    keys = sorted(dom)
    pairwise = {f"{a}|{b}": h6(isect(dom[a], dom[b]))
                for i, a in enumerate(keys) for b in keys[i + 1:]}
    three = {f"without_{d}": h6(isect_all([dom[k] for k in keys if k != d])) for d in keys}
    four = isect_all([dom[k] for k in keys])
    res = {
        "domain_h": {k: h6(v) for k, v in dom.items()},
        "pairwise_h": pairwise,
        "three_domain_h": three,
        "four_domain_h": h6(four),
        "four_domain_n_intervals": len(four),
        "four_domain_status": "overlap" if four else "no_common_support",
    }
    if not isect(pulsar, optical) and pulsar and optical:
        res["pulsar_optical_gap_h"] = round(
            (min(a for a, _ in optical) - max(b for _, b in pulsar)) / 3_600_000_000, 6)
    return res


def build_sensitivity(root, ivs_sessions, igs_pins, src="src/ftro/analyse_optical.py",
                      cross_check_dir=None):
    seg = Resegmenter(root, src)

    vlbi = isect(merge([(to_us(s["mjd_start"]), to_us(s["mjd_end"])) for s in ivs_sessions]),
                 WINDOW)
    days = sorted({p["mjd"] for p in igs_pins["pins"] if p["mjd"] and p["series"] == "igs"})
    gnss = isect(merge([(int(d) * US_PER_DAY, (int(d) + 1) * US_PER_DAY) for d in days]), WINDOW)
    dt = __import__("datetime").datetime.fromisoformat(PULSAR_OBS_START_UTC)
    p0 = round((dt - __import__("datetime").datetime(1858, 11, 17)).total_seconds() * US_PER_S)
    pulsar = isect([(p0, p0 + round(PULSAR_TOBS_S * US_PER_S))], WINDOW)

    def variant(optical, **extra):
        return {**four_domain(optical, vlbi, gnss, pulsar),
                "optical_n_intervals": len(optical), **extra}

    stamps = seg.window_stamps_us()
    scan, spans = {}, {}
    for tol in GAP_TOLERANCES_S:
        runs = seg.runs(tol)
        spans[tol] = span_union(runs)
        scan[f"{tol}"] = variant(spans[tol], n_runs=len(runs),
                                 n_samples=sum(n for _a, _b, n, *_ in runs))

    base = seg.runs(1.5)
    credit = {
        "run_span_plus_trailing_gate": variant(
            run_span_plus_trailing_gate(base),
            note="Each RUN extended 1 s past its last tag -- what the previous "
                 "'nominal_1s_sample_credit' row computed. Credits one gate per RUN, "
                 "not per SAMPLE, and inherits the contiguity rule."),
        "per_run_nominal_block": variant(
            per_run_nominal_block(base),
            note="Each run repacked as n contiguous 1 s gates from its first tag. "
                 "Totals n x 1 s per run but relocates tags, so it is a bookkeeping "
                 "figure, not a support claim."),
        "per_sample_nominal_1s_credit": variant(
            per_sample_nominal_credit(stamps),
            n_samples=len(stamps),
            naive_sum_h=round(len(stamps) * US_PER_S / 3_600_000_000, 6),
            note="Union of [t, t+1 s) over every valid tag. The only credit basis that "
                 "is independent of the contiguity rule, and the only one that never "
                 "attributes support to an instant no comparison sampled."),
    }

    shifts = {}
    for sh in TAG_SHIFTS_S:
        d = round(sh * US_PER_S)
        shifts[f"{sh:+.0f}s"] = variant(
            isect(merge([(a + d, b + d) for a, b, *_ in base]), WINDOW))

    statuses = {v["four_domain_status"]
                for group in (scan, credit, shifts) for v in group.values()}
    out = {
        "method": ("Each gap tolerance is a full re-segmentation from the raw records via "
                   "analyse_optical.contiguous_runs(); the previous implementation re-merged "
                   "an inventory already segmented at 1.5 s and bridged gaps across "
                   "comparisons and files, so it could not split runs and did join series "
                   "that never overlapped."),
        "arithmetic": "exact integer microseconds; 1e-6 d = 86400 us, 1 s = 1000000 us",
        "gap_tolerance_scan": scan,
        "sample_credit": credit,
        "uniform_tag_shift": shifts,
        "four_domain_status_over_all_variants": sorted(statuses),
        "four_domain_status_invariant": len(statuses) == 1,
    }
    if cross_check_dir:
        os.makedirs(cross_check_dir, exist_ok=True)
        xc = {}
        for tol in GAP_TOLERANCES_S:
            r = seg.subprocess_runs(tol, os.path.join(cross_check_dir, f"inv-{tol}.json"))
            xc[f"{tol}"] = {"optical_h": h6(span_union(r)),
                            "matches_in_process": h6(span_union(r)) == scan[f"{tol}"]["domain_h"]["optical"]}
        out["subprocess_cross_check"] = xc
    return out


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(repo)
    s = build_sensitivity(
        "data/raw/zenodo-17107693/extracted",
        json.load(open("phase0/reports/ivs-sessions-candidate-window.json", encoding="utf-8")),
        json.load(open("phase0/reports/igs-artifact-pins.json", encoding="utf-8")),
    )
    json.dump(s, open("/tmp/ftro-gapscan/sensitivity-corrected.json", "w"), indent=2)
    print("gap tolerance scan")
    for k, v in s["gap_tolerance_scan"].items():
        print(f"  tol={k:<4} runs={v['n_runs']:<5} optical {v['domain_h']['optical']:.6f} h"
              f"  n vlbi {v['pairwise_h']['optical|vlbi']:.6f} h"
              f"  n pulsar {v['pairwise_h']['optical|pulsar']:.6f} h"
              f"  n gnss {v['pairwise_h']['gnss|optical']:.6f} h"
              f"  4D {v['four_domain_h']:.6f} h [{v['four_domain_status']}]")
    print("sample credit")
    for k, v in s["sample_credit"].items():
        print(f"  {k:<30} optical {v['domain_h']['optical']:.6f} h"
              f"  n vlbi {v['pairwise_h']['optical|vlbi']:.6f} h"
              f"  4D {v['four_domain_h']:.6f} h [{v['four_domain_status']}]")
    print("uniform tag shift")
    for k, v in s["uniform_tag_shift"].items():
        print(f"  {k:<6} optical {v['domain_h']['optical']:.6f} h"
              f"  n pulsar {v['pairwise_h']['optical|pulsar']:.6f} h"
              f"  gap {v.get('pulsar_optical_gap_h')} h"
              f"  4D [{v['four_domain_status']}]")
    print("four-domain status over all variants:", s["four_domain_status_over_all_variants"],
          "invariant:", s["four_domain_status_invariant"])
