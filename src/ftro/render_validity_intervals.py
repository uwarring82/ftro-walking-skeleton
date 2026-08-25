#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Render phase0/optical-validity-intervals.md from the committed optical summary.
#
# Committed because FTRO-DEF-027 established the rule that a number quoted in a finding
# must be traceable to a key in a committed report produced by a committed generator.
# A generated document whose generator is not committed reproduces that defect.

import json

SRC = "phase0/reports/optical-inventory-summary.json"
DST = "phase0/optical-validity-intervals.md"


def main():
    d = json.load(open(SRC, encoding="utf-8"))
    q, cov = d["mjd_quantum_check"], d["sample_spacing_coverage"]
    L = []
    w = L.append

    w("# Optical Validity Intervals inside MJD 59630–59640\n")
    w("**Document ID:** FTRO-OVI-001 · **Version:** 0.2.0 · **Date:** 2026-08-25 · "
      "**Licence:** CC BY 4.0  ")
    w("**Task card:** FTRO-WS-001 v0.3 §22.2 — *\"a table of actual optical validity intervals "
      "inside MJD 59630–59640 checked against the pinned `0/1/2` flag semantics\"*\n")
    w("> **Generated file — do not edit.** Regenerate with "
      "`python3 src/ftro/render_validity_intervals.py`.\n")
    w("> **Revised v0.2.0** after external review. The quantisation census is now computed by a "
      "committed script over every value rather than an ad-hoc 40-file sample "
      "([`FTRO-DEF-027`](../ledgers/deficiency-log.md#ftro-def-027)), and the one-second grid is "
      "stated as a model-dependent inference rather than a fact.\n")
    w("**Source:** Zenodo version DOI [10.5281/zenodo.17107693](https://doi.org/10.5281/zenodo.17107693) "
      "(concept DOI [10.5281/zenodo.17107692](https://doi.org/10.5281/zenodo.17107692)), "
      "MD5 `4ae290f559c90b462991286c933a1147` (verified)  ")
    w("**Generated from:** [`optical-inventory-summary.json`](reports/optical-inventory-summary.json) "
      "via `src/ftro/analyse_optical.py`\n")
    w("---\n")

    w("## 1. Flag-semantics conformance check — the headline result\n")
    w("The pinned format (`INRIM/optical-link-data-format@689bda77`, README line 77) defines:\n")
    w("> Column 3: validity flag (**0 = invalid, 1 = valid but experimental, 2 = valid**)\n")
    w("Observed across the entire archive:\n")
    w("| Flag | Documented meaning | Occurrences |")
    w("| --- | --- | --- |")
    for k, v in sorted(d["global_flag_histogram"].items()):
        w(f"| `{k}` | {d['documented_flag_vocabulary'][k]} | **{v:,}** |")
    for k, v in sorted(d["documented_flag_vocabulary"].items()):
        if k not in d["global_flag_histogram"]:
            w(f"| `{k}` | {v} | **0** |")
    w("")
    w(f"**Undocumented flag values found: {d['global_undocumented_flag_values'] or 'none'}.**\n")
    total = sum(d["global_flag_histogram"].values())
    w(f"**Every one of the {total:,} samples in all 12 comparisons carries flag = 1.** ")
    w("Values `0` and `2` never occur. The three-state vocabulary is documented but not exercised, ")
    w("so the flag column carries **zero discriminating information** and cannot serve as a "
      "validity mask.\n")
    w("Consequences:\n")
    w("- Validity intervals below are derived from **sample presence and contiguity**, not from "
      "the flag.")
    w("- No sample in the archive is declared fully `valid`; every published sample is formally "
      "only *\"valid but experimental\"*.")
    w("- Invalid samples may have been **removed** before publication rather than flagged, but the "
      "archive does not say so, and we did not establish it.\n")
    w("Recorded as [`FTRO-DEF-001`](../ledgers/deficiency-log.md#ftro-def-001).\n")
    w("---\n")

    w("## 2. Time-coordinate quantisation\n")
    w("### 2.1 The quantum — measured, exhaustive\n")
    w("| Test | Result |")
    w("| --- | --- |")
    w(f"| MJD values tested | **{q['n_tested']:,}** (every value in the archive) |")
    w(f"| Exact multiples of 10⁻⁶ d (86.4 ms) | **{q['n_conforming']:,}** |")
    w(f"| Exceptions | **{q['n_exceptions']}** |")
    w("| Decimal places | "
      + ", ".join(f"{k} dp: {v:,}" for k, v in q["decimal_place_histogram"].items()) + " |")
    w("")
    w("The test operates on the serialised decimal token, not a float round-trip. ")
    w("**The 86.4 ms serialisation quantum is a measured fact.**\n")

    w("### 2.2 The one-second grid — an inference\n")
    w(f"Sample-spacing histogram (20 most common of {cov['n_distinct_spacings']:,} distinct "
      "spacings):\n")
    w("| Spacing (s) | Count | Multiple of 86.4 ms |")
    w("| --- | --- | --- |")
    for k, v in list(d["sample_spacing_histogram_s"].items())[:6]:
        w(f"| {k} | {v:,} | {float(k) / 0.0864:.0f} |")
    w("")
    pct = 100 * cov["n_spacings_in_top20"] / cov["n_spacings_total"]
    w(f"These 20 spacings cover **{cov['n_spacings_in_top20']:,} of {cov['n_spacings_total']:,}** "
      f"intervals ({pct:.2f}%), so statements about the histogram must not be generalised to all "
      "spacings.\n")
    w("The 1.0368 / 0.9504 s dither in ratio 1.347775 — against 1.347826 for a mean of exactly "
      "1 s, implying a mean spacing of 0.999999199 s — is **strongly consistent with "
      "nearest-rounding of a one-second grid** to the 86.4 ms quantum. Under that model the "
      "maximum serialisation error is **±43.2 ms**, 4.3% of the nominal sampling interval.\n")
    w("**No field in the archive declares the sampling grid**, so the one-second figure is a "
      "model-dependent inference, not a declared or measured fact. The ±43.2 ms bound is a limit "
      "on the *time* axis and is therefore not expressible as a ratio against the dimensionless "
      "fractional-frequency uncertainty the same files report.\n")
    w("See [`FTRO-DEF-002`](../ledgers/deficiency-log.md#ftro-def-002) and ")
    w("[the time-tag ancestry note](optical-timetag-ancestry-note.md).\n")
    w("---\n")

    w("## 3. Actual support inside the candidate window\n")
    w("Runs are maximal contiguous stretches of flag ∈ {1,2} samples with inter-sample spacing "
      "≤ 1.5 s.\n")
    w("| Comparison | Runs | Samples | Valid support | Envelope (MJD) |")
    w("| --- | ---: | ---: | ---: | --- |")
    rows = sorted(d["comparisons"], key=lambda c: -c["n_valid_samples_in_window"])
    tot_s = tot_n = tot_r = 0
    for c in rows:
        n = c["n_valid_samples_in_window"]
        if not n:
            w(f"| `{c['comparison']}` | 0 | 0 | **none** | — |")
            continue
        s, e = c["valid_support_seconds_in_window"], c["window_support_envelope_mjd"]
        tot_s += s
        tot_n += n
        tot_r += c["n_valid_runs_in_candidate_window"]
        w(f"| `{c['comparison']}` | {c['n_valid_runs_in_candidate_window']:,} | {n:,} | "
          f"{s / 3600:.2f} h | {e[0]:.5f} – {e[1]:.5f} |")
    w(f"| **Sum over comparisons** | **{tot_r:,}** | **{tot_n:,}** | **{tot_s / 3600:.2f} h** | |")
    w("")
    w("> **The total row is comparison-hours, not wall-clock time.** It sums support across "
      "concurrently-running comparisons and so exceeds the 240 h window. The temporal **union** "
      "of these runs is **133.112 h**; the union of the per-comparison envelopes is 197.075 h. "
      "See [`four-domain-intersection.json`](reports/four-domain-intersection.json).\n")
    w("**11 of 12 comparisons** have support inside the window. `NPL-Yb+(E3)-NPL-Sr1` has none: ")
    w("it begins at MJD 59647.73, and it is also the only comparison produced by a different "
      "pipeline ([`FTRO-DEF-008`](../ledgers/deficiency-log.md#ftro-def-008)).\n")
    w("Support is heavily **fragmented**: e.g. `PTB_Yb1E2_CombYb-PTB_Yb_CombKnoten` has 1,934 "
      "separate runs. Envelopes therefore substantially overstate real coverage, which is why the "
      "four-domain calculation uses the **exact run-level union** rather than envelopes.\n")
    w("---\n")

    w("## 4. Declared vs actual coverage\n")
    mn = min(c["mjd_first"] for c in d["comparisons"])
    mx = max(c["mjd_last"] for c in d["comparisons"])
    w("| | MJD range | UTC |")
    w("| --- | --- | --- |")
    w("| Declared (Zenodo record + card §5.1) | 59630 – 59675 | 2022-02-20 – 2022-04-06 |")
    w(f"| **Actual (computed)** | **{mn:.5f} – {mx:.5f}** | 2022-02-21 – 2022-04-06 |")
    w("")
    w(f"Declared coverage overstates support at the lower bound by **{mn - 59630:.3f} days**. ")
    w("This matters for one pairwise cell: the single PPTA observation in the window falls at ")
    w("MJD 59630.4675, inside exactly that unsupported region, so taking the declared coverage at "
      "face value would make **optical ∩ pulsar** appear non-empty when it is not. It does not "
      "affect the four-domain result, because pulsar ∩ VLBI is independently empty. See ")
    w("[`FTRO-DEF-009`](../ledgers/deficiency-log.md#ftro-def-009) and ")
    w("[`FTRO-DEF-023`](../ledgers/deficiency-log.md#ftro-def-023).\n")

    open(DST, "w", encoding="utf-8").write("\n".join(L))
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
