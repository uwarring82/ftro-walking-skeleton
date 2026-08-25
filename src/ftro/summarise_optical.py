#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Reduce the full optical inventory to a committable summary.
# The full inventory (data/work/optical-inventory.json, ~12 MB) is regenerable from the
# archive via analyse_optical.py and is therefore not tracked; this summary is.

import json
import sys

src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))

comps = []
for c in d["comparisons"]:
    runs = c["valid_runs_in_candidate_window"]
    comps.append({
        "comparison": c["comparison"],
        "yaml_keys": c["yaml_keys"],
        "yaml_values": c["yaml_values"],
        "generation_headers": c["generation_headers"],
        "n_dat_files": c["n_dat_files"],
        "mjd_first": c["mjd_first"],
        "mjd_last": c["mjd_last"],
        "flag_histogram": c["flag_histogram"],
        "undocumented_flag_values": c["undocumented_flag_values"],
        "uncertainty_consistency": {
            k: {"yaml_value": v["yaml_value"],
                "n_distinct_column_values": len(v["column_values"]),
                "column_value_min": min(v["column_values"], key=float) if v["column_values"] else None,
                "column_value_max": max(v["column_values"], key=float) if v["column_values"] else None,
                "identical_to_yaml": v["identical"]}
            for k, v in c["uncertainty_consistency"].items()},
        "n_valid_runs_in_candidate_window": len(runs),
        "n_valid_samples_in_window": c["n_valid_samples_in_window"],
        "valid_support_seconds_in_window": round(sum(r["span_s"] for r in runs), 3),
        "window_support_envelope_mjd": ([min(r["mjd_start"] for r in runs),
                                         max(r["mjd_end"] for r in runs)] if runs else None),
        "files": [{"file": f["file"], "n_samples": f["n_samples"],
                   "mjd_first": f.get("mjd_first"), "mjd_last": f.get("mjd_last"),
                   "flag_histogram": f.get("flag_histogram")} for f in c["files"]],
    })

out = {k: d[k] for k in ("generator", "source_record", "candidate_window_mjd",
                         "documented_flag_vocabulary", "gap_tolerance_s", "nominal_sampling_s",
                         "global_flag_histogram", "global_undocumented_flag_values",
                         "sample_spacing_histogram_s", "sample_spacing_coverage",
                         "sample_spacing_exhaustive",
                         "mjd_quantum_check", "n_comparisons")}
out["note"] = ("Summary of the full inventory; per-sample uncertainty-column value sets and "
               "individual run boundaries are omitted. Regenerate the full inventory with "
               "src/ftro/analyse_optical.py.")
out["comparisons"] = comps
json.dump(out, open(dst, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"wrote {dst}")
