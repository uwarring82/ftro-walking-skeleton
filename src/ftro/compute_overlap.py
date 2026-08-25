#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO Phase-0 support-intersection calculator.
#
# Intersects the ACTUAL optical valid runs (not campaign envelopes) with candidate
# VLBI session supports, per task card section 6: "a source belongs to the common
# window only when its actual data support intersects it."

import argparse
import json


def intersect(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if hi > lo else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--optical", default="data/work/optical-inventory.json")
    ap.add_argument("--sessions", required=True, help="JSON list of VLBI sessions")
    ap.add_argument("--out", default="data/work/overlap.json")
    args = ap.parse_args()

    opt = json.load(open(args.optical, encoding="utf-8"))
    sessions = json.load(open(args.sessions, encoding="utf-8"))

    results = []
    for s in sessions:
        sup = (s["mjd_start"], s["mjd_end"])
        per_comp = []
        for c in opt["comparisons"]:
            runs = c["valid_runs_in_candidate_window"]
            hits = [(r, iv) for r in runs if (iv := intersect((r["mjd_start"], r["mjd_end"]), sup))]
            if not hits:
                continue
            total_s = sum((iv[1] - iv[0]) * 86400 for _, iv in hits)
            per_comp.append({
                "comparison": c["comparison"],
                "n_runs_overlapping": len(hits),
                "overlap_seconds": round(total_s, 3),
                "overlap_hours": round(total_s / 3600, 3),
                "first_overlap_mjd": min(iv[0] for _, iv in hits),
                "last_overlap_mjd": max(iv[1] for _, iv in hits),
            })
        per_comp.sort(key=lambda x: -x["overlap_seconds"])
        results.append({
            "session": s["code"], "type": s["type"], "start_utc": s["start_utc"],
            "mjd_start": sup[0], "mjd_end": sup[1],
            "n_optical_comparisons_overlapping": len(per_comp),
            "total_optical_overlap_hours": round(sum(p["overlap_hours"] for p in per_comp), 3),
            "per_comparison": per_comp,
        })

    results.sort(key=lambda x: (-x["n_optical_comparisons_overlapping"],
                                -x["total_optical_overlap_hours"]))
    out = {"generator": "src/ftro/compute_overlap.py",
           "note": ("Optical support is the union of contiguous flag-in-{1,2} runs computed from "
                    "actual samples; VLBI support is the scheduled session interval from the IVS "
                    "session listing, not a per-observation support."),
           "sessions": results}
    json.dump(out, open(args.out, "w", encoding="utf-8"), indent=2)
    print(f"wrote {args.out}")
    for r in results:
        print(f"{r['session']:<8} {r['type']:<10} MJD {r['mjd_start']:.4f}-{r['mjd_end']:.4f}  "
              f"comparisons={r['n_optical_comparisons_overlapping']:<3} "
              f"optical-overlap={r['total_optical_overlap_hours']:.2f} h")


if __name__ == "__main__":
    main()
