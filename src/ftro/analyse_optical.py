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

CANDIDATE_MJD_START = 59630.0   # 2022-02-20
CANDIDATE_MJD_END = 59640.0     # 2022-03-02
# Documented flag vocabulary, pinned from INRIM/optical-link-data-format (see source ledger).
DOCUMENTED_FLAGS = {0: "invalid", 1: "valid but experimental", 2: "valid"}
NOMINAL_SAMPLING_S = 1.0
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
    """Return (header_lines, rows). Rows are (mjd, ratio_str, flag_int, uA_str, uB_str)."""
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
            rows.append((mjd, parts[1], flag, uA, uB))
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
    all_spacings = Counter()

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

            for a, b in zip(mjds, mjds[1:]):
                all_spacings[round((b - a) * SEC_PER_DAY, 6)] += 1

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
        "sample_spacing_histogram_s": {str(k): v for k, v in
                                       sorted(all_spacings.items(), key=lambda kv: -kv[1])[:20]},
        "n_comparisons": len(comparisons),
        "comparisons": comparisons,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(f"wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
