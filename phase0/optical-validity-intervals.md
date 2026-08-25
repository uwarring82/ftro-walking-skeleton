# Optical Validity Intervals inside MJD 59630–59640

**Document ID:** FTRO-OVI-001 · **Version:** 0.2.0 · **Date:** 2026-08-25 · **Licence:** CC BY 4.0  
**Task card:** FTRO-WS-001 v0.3 §22.2 — *"a table of actual optical validity intervals inside MJD 59630–59640 checked against the pinned `0/1/2` flag semantics"*

> **Generated file — do not edit.** Regenerate with `python3 src/ftro/render_validity_intervals.py`.

> **Revised v0.2.0** after external review. The quantisation census is now computed by a committed script over every value rather than an ad-hoc 40-file sample ([`FTRO-DEF-027`](../ledgers/deficiency-log.md#ftro-def-027)), and the one-second grid is stated as a model-dependent inference rather than a fact.

**Source:** Zenodo version DOI [10.5281/zenodo.17107693](https://doi.org/10.5281/zenodo.17107693) (concept DOI [10.5281/zenodo.17107692](https://doi.org/10.5281/zenodo.17107692)), MD5 `4ae290f559c90b462991286c933a1147` (verified)  
**Generated from:** [`optical-inventory-summary.json`](reports/optical-inventory-summary.json) via `src/ftro/analyse_optical.py`

---

## 1. Flag-semantics conformance check — the headline result

The pinned format (`INRIM/optical-link-data-format@689bda77`, README line 77) defines:

> Column 3: validity flag (**0 = invalid, 1 = valid but experimental, 2 = valid**)

Observed across the entire archive:

| Flag | Documented meaning | Occurrences |
| --- | --- | --- |
| `1` | valid but experimental | **9,018,290** |
| `0` | invalid | **0** |
| `2` | valid | **0** |

**Undocumented flag values found: none.**

**Every one of the 9,018,290 samples in all 12 comparisons carries flag = 1.** 
Values `0` and `2` never occur. The three-state vocabulary is documented but not exercised, 
so the flag column carries **zero discriminating information** and cannot serve as a validity mask.

Consequences:

- Validity intervals below are derived from **sample presence and contiguity**, not from the flag.
- No sample in the archive is declared fully `valid`; every published sample is formally only *"valid but experimental"*.
- Invalid samples may have been **removed** before publication rather than flagged, but the archive does not say so, and we did not establish it.

Recorded as [`FTRO-DEF-001`](../ledgers/deficiency-log.md#ftro-def-001).

---

## 2. Time-coordinate quantisation

### 2.1 The quantum — measured, exhaustive

| Test | Result |
| --- | --- |
| MJD values tested | **9,018,290** (every value in the archive) |
| Exact multiples of 10⁻⁶ d (86.4 ms) | **9,018,290** |
| Exceptions | **0** |
| Decimal places | 6 dp: 9,018,290 |

The test operates on the serialised decimal token, not a float round-trip. 
**The 86.4 ms serialisation quantum is a measured fact.**

### 2.2 The one-second grid — an inference

Sample-spacing histogram (20 most common of 1,237 distinct spacings):

| Spacing (s) | Count | Multiple of 86.4 ms |
| --- | --- | --- |
| 1.0368 | 5,139,806 | 12 |
| 0.9504 | 3,813,549 | 11 |
| 3.024 | 7,274 | 35 |
| 1.9872 | 6,235 | 23 |
| 8.9856 | 4,263 | 104 |
| 6.9984 | 3,865 | 81 |

These 20 spacings cover **8,999,974 of 9,018,038** intervals (99.80%), so statements about the histogram must not be generalised to all spacings.

The 1.0368 / 0.9504 s dither in ratio 1.347775 — against 1.347826 for a mean of exactly 1 s, implying a mean spacing of 0.999999199 s — is **strongly consistent with nearest-rounding of a one-second grid** to the 86.4 ms quantum. Under that model the **per-tag rounding bound is ±43.2 ms**, 4.3% of the nominal sampling interval.

That bound is neither universal nor irreducible. The absent `interval`, `lag` and `weighting` leave a tag's placement within its own integration unconstrained over up to **1 s** — a larger term — and if the grid model is accepted, reconstructing epochs by sample index could recover much of the quantisation loss.

**No field in the archive declares the sampling grid**, so the one-second figure is a model-dependent inference, not a declared or measured fact. The ±43.2 ms bound is a limit on the *time* axis and is therefore not expressible as a ratio against the dimensionless fractional-frequency uncertainty the same files report.

See [`FTRO-DEF-002`](../ledgers/deficiency-log.md#ftro-def-002) and 
[the time-tag ancestry note](optical-timetag-ancestry-note.md).

---

## 3. Actual support inside the candidate window

Runs are maximal contiguous stretches of flag ∈ {1,2} samples with inter-sample spacing ≤ 1.5 s.

| Comparison | Runs | Samples | Valid support | Envelope (MJD) |
| --- | ---: | ---: | ---: | --- |
| `PTB_Yb1E2_CombYb-PTB_Yb_CombKnoten` | 1,934 | 446,524 | 123.50 h | 59632.37187 – 59640.00000 |
| `PTB_Yb_CombKnoten-INRIM_ITYb1` | 811 | 116,633 | 32.17 h | 59631.78854 – 59639.97589 |
| `PTB_Yb_CombKnoten-PTB_Sr3_CombKnoten` | 58 | 112,441 | 31.22 h | 59638.33537 – 59640.00000 |
| `INRIM_ITYb1-SYRTE_Sr2` | 1,686 | 72,526 | 19.68 h | 59638.80139 – 59640.00000 |
| `PTB_In_CombKnoten-PTB_Yb_CombKnoten` | 16 | 60,820 | 16.89 h | 59633.72199 – 59640.00000 |
| `INRIM_ITYb1-PTB_Sr3_CombKnoten` | 552 | 55,186 | 15.18 h | 59638.80139 – 59639.97589 |
| `PTB_Yb_CombKnoten-SYRTE_Sr2` | 982 | 54,478 | 14.86 h | 59638.54016 – 59639.97589 |
| `PTB_Sr3_CombKnoten-SYRTE_Sr2` | 970 | 53,671 | 14.64 h | 59638.54016 – 59639.97589 |
| `PTB_In_CombKnoten-PTB_Sr3_CombKnoten` | 9 | 21,703 | 6.03 h | 59639.73743 – 59640.00000 |
| `PTB_In_CombKnoten-INRIM_ITYb1` | 123 | 15,976 | 4.40 h | 59639.73743 – 59639.97589 |
| `PTB_In_CombKnoten-SYRTE_Sr2` | 257 | 13,992 | 3.82 h | 59639.73743 – 59639.97589 |
| `NPL-Yb+(E3)-NPL-Sr1` | 0 | 0 | **none** | — |
| **Sum over comparisons** | **7,398** | **1,023,950** | **282.37 h** | |

> **The total row is comparison-hours, not wall-clock time.** It sums support across concurrently-running comparisons and so exceeds the 240 h window. The temporal **union** of these runs is **133.112 h** (7,398 runs merge to 1,384 intervals, of which 31 have zero recorded span because they are single-sample runs, leaving 1,353 with positive duration in the window); the union of the per-comparison envelopes is 197.075 h. See [`four-domain-intersection.json`](reports/four-domain-intersection.json).

**11 of 12 comparisons** have support inside the window. `NPL-Yb+(E3)-NPL-Sr1` has none: 
it begins at MJD 59647.73, and it is also the only comparison produced by a different pipeline ([`FTRO-DEF-008`](../ledgers/deficiency-log.md#ftro-def-008)).

Support is heavily **fragmented**: e.g. `PTB_Yb1E2_CombYb-PTB_Yb_CombKnoten` has 1,934 separate runs. Envelopes therefore substantially overstate real coverage, which is why the four-domain calculation uses the **exact run-level union** rather than envelopes.

---

## 4. Declared vs actual coverage

| | MJD range | UTC |
| --- | --- | --- |
| Declared (Zenodo record + card §5.1) | 59630 – 59675 | 2022-02-20 – 2022-04-06 |
| **Actual (computed)** | **59631.78854 – 59674.99999** | 2022-02-21 – 2022-04-06 |

Declared coverage overstates support at the lower bound by **1.789 days**. 
This matters for one pairwise cell: the single PPTA observation in the window falls at 
MJD 59630.4675, inside exactly that unsupported region, so taking the declared coverage at face value would make **optical ∩ pulsar** appear non-empty when it is not. It does not affect the four-domain result, because pulsar ∩ VLBI is independently empty. See 
[`FTRO-DEF-009`](../ledgers/deficiency-log.md#ftro-def-009) and 
[`FTRO-DEF-023`](../ledgers/deficiency-log.md#ftro-def-023).
