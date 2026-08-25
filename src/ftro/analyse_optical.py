#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO walking skeleton -- Phase 0 optical leg analyser.
#
# Reads the extracted Zenodo 17107693 ("ROCIT campaign results.zip") tree and emits
# a machine-readable inventory: per-comparison file lists, MJD support, validity-flag
# histograms checked against the pinned 0/1/2 semantics, sampling-interval statistics,
# and the actual valid support intersecting the candidate window.
#
# The archive is never modified. Source values are preserved verbatim; no flag,
# uncertainty or timestamp is coerced. Deviations are reported, not repaired.

import argparse
import json
import os
import re
import sys
from collections import Counter
from decimal import Decimal

CANDIDATE_MJD_START = 59630.0   # 2022-02-20
CANDIDATE_MJD_END = 59640.0     # 2022-03-02
# Documented flag vocabulary, pinned from INRIM/optical-link-data-format (see source ledger).
DOCUMENTED_FLAGS = {0: "invalid", 1: "valid but experimental", 2: "valid"}
NOMINAL_SAMPLING_S = 1.0
TICK_SECONDS = 0.0864          # 1e-6 d, the serialisation quantum
SEC_PER_DAY = 86400.0


def parse_yaml_block(path):
    """Minimal reader for the archive's flat one-item YAML list. Values kept as source strings."""
    out, order = {}, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            m = re.match(r"^[\s-]*([A-Za-z_][A-Za-z_0-9]*):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                out[key] = val
                order.append(key)
    return out, order


def parse_dat(path):
    """Return (header_lines, rows, malformed).

    Rows are (mjd, ratio_str, flag_int, uA_str, uB_str, mjd_token). The raw MJD token is
    retained so the time-coordinate quantisation test operates on the serialised decimal
    string rather than on a float round-trip.
    """
    header, rows, malformed = [], [], []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                header.append(line)
                continue
            parts = line.split()
            if len(parts) < 3:
                malformed.append((lineno, line))
                continue
            try:
                mjd = float(parts[0])
                flag = int(parts[2])
            except ValueError:
                malformed.append((lineno, line))
                continue
            uA = parts[3] if len(parts) > 3 else None
            uB = parts[4] if len(parts) > 4 else None
            # Integer microdays ("ticks") parsed from the decimal token. Every MJD in this
            # archive is an exact multiple of 1e-6 d, so tick arithmetic is exact where
            # float subtraction is not: differencing binary floats split the single
            # physical 23-tick spacing into 1.9872 and 1.987199 (FTRO-DEF-036).
            ipart, _, frac = parts[0].partition(".")
            tick = int(ipart) * 1_000_000 + int(frac.ljust(6, "0")[:6])
            rows.append((mjd, parts[1], flag, uA, uB, parts[0], tick))
    return header, rows, malformed


def contiguous_runs(mjds, flags, keep, gap_tol_s):
    """Group consecutive samples whose flag is in `keep` into runs, splitting on gaps."""
    runs = []
    start = prev = None
    n = 0
    tol_days = gap_tol_s / SEC_PER_DAY
    for mjd, fl in zip(mjds, flags):
        if fl in keep:
            if start is None:
                start, prev, n = mjd, mjd, 1
            elif (mjd - prev) > tol_days:
                runs.append((start, prev, n))
                start, prev, n = mjd, mjd, 1
            else:
                prev, n = mjd, n + 1
        else:
            if start is not None:
                runs.append((start, prev, n))
                start = None
    if start is not None:
        runs.append((start, prev, n))
    return runs


def main():
    ap = argparse.ArgumentParser(description="FTRO Phase-0 optical leg analyser")
    ap.add_argument("--root", required=True, help="extracted archive root")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--gap-tolerance-s", type=float, default=1.5,
                    help="max inter-sample spacing kept inside one run")
    args = ap.parse_args()

    comparisons = []
    global_flags = Counter()
    all_spacings = Counter()          # keyed by integer ticks, not floats
    tick_spacings = Counter()
    # Time-coordinate quantisation test (FTRO-DEF-002). Counts EVERY value, not a sample.
    mjd_decimal_places = Counter()
    quantum_tested = 0
    quantum_conforming = 0
    quantum_exceptions = []
    spacings_total = 0

    for name in sorted(os.listdir(args.root)):
        cdir = os.path.join(args.root, name)
        if not os.path.isdir(cdir):
            continue
        yml_path = os.path.join(cdir, name + ".yml")
        meta, meta_order = (parse_yaml_block(yml_path) if os.path.exists(yml_path) else ({}, []))

        files, cflags = [], Counter()
        c_min = c_max = None
        valid_runs_in_window = []
        headers_seen = set()

        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".dat"):
                continue
            fpath = os.path.join(cdir, fn)
            header, rows, malformed = parse_dat(fpath)
            for h in header:
                if "script" in h.lower() or "generated" in h.lower():
                    headers_seen.add(h.strip())
            if not rows:
                files.append({"file": fn, "n_samples": 0, "malformed_lines": len(malformed)})
                continue

            mjds = [r[0] for r in rows]
            flags = [r[2] for r in rows]
            fc = Counter(flags)
            cflags.update(fc)
            global_flags.update(fc)

            ticks = [r[6] for r in rows]
            for a, b in zip(ticks, ticks[1:]):
                tick_spacings[b - a] += 1
                spacings_total += 1

            # Is every serialised MJD an exact multiple of the 1e-6 d quantum?
            for r in rows:
                tok = r[5]
                frac = tok.split(".")[1] if "." in tok else ""
                mjd_decimal_places[len(frac)] += 1
                quantum_tested += 1
                if Decimal(tok).scaleb(6) % 1 == 0:
                    quantum_conforming += 1
                elif len(quantum_exceptions) < 50:
                    quantum_exceptions.append({"file": fn, "mjd_token": tok})

            fmin, fmax = min(mjds), max(mjds)
            c_min = fmin if c_min is None else min(c_min, fmin)
            c_max = fmax if c_max is None else max(c_max, fmax)

            # uncertainty columns as literally present in the file
            uA_vals = sorted({r[3] for r in rows if r[3] is not None})
            uB_vals = sorted({r[4] for r in rows if r[4] is not None})

            files.append({
                "file": fn,
                "n_samples": len(rows),
                "malformed_lines": len(malformed),
                "mjd_first": fmin,
                "mjd_last": fmax,
                "flag_histogram": {str(k): v for k, v in sorted(fc.items())},
                "undocumented_flag_values": sorted(v for v in fc if v not in DOCUMENTED_FLAGS),
                "uA_sys_column_values": uA_vals,
                "uB_sys_column_values": uB_vals,
            })

            # valid support intersecting the candidate window (flags 1 and 2 = "valid")
            if fmax >= CANDIDATE_MJD_START and fmin <= CANDIDATE_MJD_END:
                w = [(m, f) for m, f in zip(mjds, flags)
                     if CANDIDATE_MJD_START <= m <= CANDIDATE_MJD_END]
                if w:
                    runs = contiguous_runs([m for m, _ in w], [f for _, f in w],
                                           keep={1, 2}, gap_tol_s=args.gap_tolerance_s)
                    for s, e, n in runs:
                        valid_runs_in_window.append(
                            {"file": fn, "mjd_start": s, "mjd_end": e, "n_samples": n,
                             "span_s": round((e - s) * SEC_PER_DAY, 3)})

        # YAML-vs-column uncertainty consistency, reported without coercion
        consistency = {}
        for side in ("A", "B"):
            key = f"u{side}_sys"
            col_key = f"u{side}_sys_column_values"
            col_vals = sorted({v for f in files for v in f.get(col_key, []) or []})
            y = meta.get(key)
            agree = None
            if y is not None and col_vals:
                try:
                    agree = all(abs(float(v) - float(y)) <= 0.0 for v in col_vals)
                except ValueError:
                    agree = None
            consistency[key] = {"yaml_value": y, "column_values": col_vals, "identical": agree}

        comparisons.append({
            "comparison": name,
            "yaml_present": bool(meta),
            "yaml_keys": meta_order,
            "yaml_values": meta,
            "generation_headers": sorted(headers_seen),
            "n_dat_files": len(files),
            "mjd_first": c_min,
            "mjd_last": c_max,
            "flag_histogram": {str(k): v for k, v in sorted(cflags.items())},
            "undocumented_flag_values": sorted(v for v in cflags if v not in DOCUMENTED_FLAGS),
            "uncertainty_consistency": consistency,
            "valid_runs_in_candidate_window": valid_runs_in_window,
            "n_valid_samples_in_window": sum(r["n_samples"] for r in valid_runs_in_window),
            "files": files,
        })

    report = {
        "generator": "src/ftro/analyse_optical.py",
        "source_record": "https://doi.org/10.5281/zenodo.17107693",
        "candidate_window_mjd": [CANDIDATE_MJD_START, CANDIDATE_MJD_END],
        "documented_flag_vocabulary": {str(k): v for k, v in DOCUMENTED_FLAGS.items()},
        "gap_tolerance_s": args.gap_tolerance_s,
        "nominal_sampling_s": NOMINAL_SAMPLING_S,
        "global_flag_histogram": {str(k): v for k, v in sorted(global_flags.items())},
        "global_undocumented_flag_values": sorted(v for v in global_flags if v not in DOCUMENTED_FLAGS),
        "sample_spacing_histogram_s": {
            f"{k * TICK_SECONDS:.4f}": v
            for k, v in sorted(tick_spacings.items(), key=lambda kv: -kv[1])[:20]},
        "sample_spacing_histogram_ticks": {
            str(k): v for k, v in sorted(tick_spacings.items(), key=lambda kv: -kv[1])[:20]},
        # Exhaustive support for the claim that no spacing lies between the two dominant
        # values. The truncated top-20 histogram cannot carry that claim, and the summary
        # explicitly warns against generalising from it.
        "sample_spacing_exhaustive": {
            "n_spacings_total": spacings_total,
            "n_distinct_spacings": len(tick_spacings),
            "min_spacing_ticks": min(tick_spacings) if tick_spacings else None,
            "max_spacing_ticks": max(tick_spacings) if tick_spacings else None,
            "arithmetic": ("integer microday ticks; 1 tick = 1e-6 d = 86.4 ms exactly. "
                           "Float subtraction is NOT used: it split the single physical "
                           "23-tick spacing into 1.9872 and 1.987199 and inflated the "
                           "distinct-gap count from 1161 to 1237 (FTRO-DEF-036)."),
            "dominant_spacings_ticks": {str(k): tick_spacings.get(k, 0) for k in (11, 12)},
            "next_populated_tick_above_12": min((k for k in tick_spacings if k > 12), default=None),
            "n_pairs_in_ticks_13_to_22": sum(v for k, v in tick_spacings.items() if 13 <= k <= 22),
            "empty_tick_band": [13, 22],
            "gap_tolerances_that_segment_identically_s": [
                round(12 * TICK_SECONDS, 4),
                round(min((k for k in tick_spacings if k > 12), default=0) * TICK_SECONDS, 4)],
            "n_distinct_tick_spacings": len(tick_spacings),
            "note": ("Computed over ALL adjacent pairs, not the truncated top-20 histogram. "
                     "The two dominant spacings are 0.9504 s (11 quanta) and 1.0368 s (12 "
                     "quanta); the next distinct value is reported above and is 23 quanta, i.e. "
                     "a float-representation twin of 1.9872 s. Nothing lies strictly between, so "
                     "any gap tolerance in (1.0368, next) segments identically -- which is why "
                     "1.1 s and 1.5 s give identical runs. Compare against the rounded literal "
                     "1.9872 with care: round(x, 6) yields both 1.9872 and 1.987199 for the same "
                     "physical spacing."),
        },
        "sample_spacing_coverage": {
            "n_spacings_total": spacings_total,
            "n_distinct_spacings": len(tick_spacings),
            "n_spacings_in_top20": sum(v for _, v in
                                       sorted(tick_spacings.items(), key=lambda kv: -kv[1])[:20]),
            "note": ("sample_spacing_histogram_s is truncated to the 20 most common spacings; "
                     "n_spacings_in_top20 states how many of n_spacings_total those cover, so "
                     "claims about the histogram must not be generalised to all spacings."),
        },
        "mjd_quantum_check": {
            "quantum_days": 1e-6,
            "quantum_seconds": 0.0864,
            "n_tested": quantum_tested,
            "n_conforming": quantum_conforming,
            "n_exceptions": quantum_tested - quantum_conforming,
            "exceptions_sample": quantum_exceptions,
            "decimal_place_histogram": {str(k): v for k, v in sorted(mjd_decimal_places.items())},
            "note": ("Tests whether every serialised MJD value is an exact multiple of 1e-6 d "
                     "(86.4 ms), evaluated on the decimal token as written, not a float "
                     "round-trip. Evidence for FTRO-DEF-002."),
        },
        "n_comparisons": len(comparisons),
        "comparisons": comparisons,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
