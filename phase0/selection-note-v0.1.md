# Phase-0 Selection Note v0.1

**Document ID:** FTRO-SEL-001
**Version:** 0.1.0
**Date:** 2026-08-25
**Task card:** FTRO-WS-001 v0.3, §21 Phase 0 and §22
**Status:** Gate 0 candidate
**Licence:** CC BY 4.0

This note records the four concrete product selections, the pre-registered
cold-reproduction targets and tolerances, and the computed temporal support that
Gate 0 requires. It is a pre-registration: §16 states that a target or tolerance
changed after the first result is inspected is labelled post hoc and cannot satisfy
the original acceptance test.

---

## 1. Candidate window

**MJD 59630.0 – 59640.0** (2022-02-20T00:00 – 2022-03-02T00:00 UTC), as specified in
task card §6, retained as a *test* interval with no guarantee of overlap.

GPS weeks spanned: 2198 day 0 through 2199 day 3.

---

## 2. Four product selections

### 2.1 Optical clocks — SELECTED

| Field | Value |
| --- | --- |
| Concept PID | <https://doi.org/10.5281/zenodo.17107693> |
| Snapshot identity | `ftro:snapshot:zenodo/17107693/ROCIT-campaign-results.zip@md5:4ae290f559c90b462991286c933a1147` |
| MD5 | `4ae290f559c90b462991286c933a1147` — **verified, matches card §5.1** |
| SHA-256 | `6168e24a0c29ce0929e9651460f11ea77f151176e1ba3d0fe3428e1e08bd56bd` (newly recorded) |
| Size | 83,530,540 B |
| Licence | CC BY 4.0 (Zenodo record metadata) |
| Retrieved | 2026-08-25T13:45Z |

**Selected records:** the 7 comparisons whose valid support intersects the selected
VLBI session (§2.3), led by `PTB_Yb1E2_CombYb-PTB_Yb_CombKnoten` (20.331 h of
overlapping support) and `PTB_Yb_CombKnoten-PTB_Sr3_CombKnoten` (18.758 h).

**Actual archive contents:** 12 comparison directories, 252 `.dat` files, 12 `.yml`
files, 9,018,290 samples. No code, README or licence file is present.

**Actual coverage:** MJD 59631.78854 – 59675.00000, not the declared 59630 – 59675
([`FTRO-DEF-009`](../ledgers/deficiency-log.md#ftro-def-009)).

### 2.2 Pulsar timing — SELECTED

| Field | Value |
| --- | --- |
| Concept identity | `ftro:concept:ppta/dr3` (FTRO-composed; no single provider PID — [`FTRO-DEF-015`](../ledgers/deficiency-log.md#ftro-def-015)) |
| Member PIDs | <https://doi.org/10.25919/j4xr-wp05>, <https://doi.org/10.25919/axvw-qa43> |
| Licence | **CC BY-SA 4.0** — copyleft ([`FTRO-DEF-014`](../ledgers/deficiency-log.md#ftro-def-014)) |
| Redistribution mode | `link_only` |
| Coverage | 2004-02-05 – 2022-03-07 (MJD 53040 – 59645) |

**Selected record:** PSR J0437−4715, observation `uwl_220220_104059_b4`, UWL receiver
with Medusa backend, `-tobs 3843.1` s.

- Scan start 2022-02-20T10:40:59 UTC = MJD 59630.445127
- Support interval MJD **59630.445127 – 59630.489608**
- **10 TOAs**, sub-banded 979.709 – 2545.197 MHz, uncertainties 0.034 – 0.446 µs
- Nearest neighbouring epochs: MJD 59629.394670 (before) and MJD 59645.403173 (after)

This is the **only** J0437−4715 observation inside the candidate window. The ~3-week
cadence noted in card §5.2 is confirmed: a 16.0-day gap follows this observation.

**Pinned ancestry artifacts** (all retrieved 2026-08-25, sizes match the DAP manifest):

| Artifact | Path | Size | SHA-256 (16) |
| --- | --- | --- | --- |
| Timing model | `toas_and_parameters/all/J0437-4715.par` | 4,402 B | `cfbd0db49a66d8a1` |
| TOAs | `toas_and_parameters/all/J0437-4715.tim` | 4,464,619 B | `ee6a2dec40b4dc6f` |
| Parkes→GPS clock | `toas_and_parameters/clock/pks2gps.clk` | 1,742,710 B | `c8131f51e17eef40` |
| TAI→TT | `toas_and_parameters/clock/tai2tt_bipm2021.clk` | 48,871 B | `047c2a19b13f6923` |

### 2.3 VLBI — SELECTED (session), NOT YET PINNED (products)

**Session: IVS-R1 `R11040`.**

| Field | Value |
| --- | --- |
| Start | 2022-02-28T17:00 UTC |
| Duration | 24 h |
| Support | MJD 59638.708333 – 59639.708333 |
| DB code | XA |
| Ops centre | NASA |
| Correlator | BONN |
| Analysis centre | NASA |
| Status | Released |

**Selection rationale.** Seven IVS sessions intersect the candidate window. R11040
overlaps **7 of 11** in-window optical comparisons with 91.95 h of cumulative
optical-comparison overlap, against 26.38 h for the next-best (AUA085). It is also an
IVS-R1 session, the operational series that feeds IVS combined Earth-orientation
products.

| Session | Type | Support (MJD) | Optical comparisons | Cumulative overlap |
| --- | --- | --- | --- | --- |
| **R11040** | **IVS-R1** | **59638.7083–59639.7083** | **7** | **91.95 h** |
| AUA085 | AUSTRAL | 59632.7292–59633.7292 | 3 | 26.38 h |
| AOV068 | AOV | 59633.7500–59634.7500 | 2 | 24.46 h |
| R11039 | IVS-R1 | 59631.7083–59632.7083 | 2 | 13.26 h |
| UH007R | USNO-CRF | 59631.5833–59632.5833 | 2 | 10.66 h |
| R41039 | IVS-R4 | 59634.7708–59635.7708 | 1 | 16.51 h |
| VO2055 | VGOS-OPS | 59634.7500–59635.7500 | 1 | 16.12 h |

**Not yet pinned, and blocking:** the vgosDB snapshot, the analysis-centre product and
the downstream IERS EOP series. CDDIS, the primary archive, returns an Earthdata login
page with HTTP 200 ([`FTRO-DEF-018`](../ledgers/deficiency-log.md#ftro-def-018)).
Session metadata was obtained from the IVS session listing instead.
`evidence_state = unresolved` for the VLBI data products.

### 2.4 GNSS — SELECTED

**57 artifacts pinned** with SHA-256, MD5, size and mirror `Last-Modified`, from the
BKG IGS mirror over anonymous HTTP. See
[`phase0/reports/igs-artifact-pins.json`](reports/igs-artifact-pins.json).

| Product line | Files | Total |
| --- | --- | --- |
| `igs` Final orbit (`.sp3.Z`) | 11 | 1.07 MB |
| `igs` Final clock (`.clk.Z`, 5-minute) | 11 | 17.39 MB |
| `igs` Final ERP (`.erp.Z`, weekly) | 2 | — |
| `igr` Rapid orbit / clock / ERP | 33 | 12.44 MB |

Reference frame for the interval: **IGb14**. IGS20 became operational at GPS week 2238
(2022-11-27), after the candidate window, consistent with card §5.3.

`.clk_30s` high-rate clocks and `.sum` summaries are absent from this mirror
([`FTRO-DEF-020`](../ledgers/deficiency-log.md#ftro-def-020)).

---

## 3. Computed temporal support and the four-domain intersection

Support is computed from actual records and validity masks, never from campaign
boundaries (card §6). Full output:
[`phase0/reports/four-domain-intersection.json`](reports/four-domain-intersection.json).

| Domain | Support inside window | Basis |
| --- | --- | --- |
| GNSS | 240.000 h (continuous) | IGS Final daily product validity |
| Optical | 197.075 h (**upper bound**) | union of per-comparison valid-run envelopes |
| VLBI | 123.500 h | scheduled session intervals |
| Pulsar | 1.067 h | one scan, start + `-tobs` |

| Combination | Result | Overlap |
| --- | --- | --- |
| gnss ∩ optical | overlap | 197.075 h |
| gnss ∩ vlbi | overlap | 123.500 h |
| optical ∩ vlbi | overlap | 118.575 h |
| gnss ∩ pulsar | overlap | 1.067 h |
| **optical ∩ pulsar** | **no_common_support** | 0 h |
| **pulsar ∩ vlbi** | **no_common_support** | 0 h |
| optical ∩ vlbi ∩ gnss | overlap | 118.575 h |
| **all four** | **no_common_support** | **0 h** |

**Result: `no_common_support`.** The pulsar observation ends at MJD 59630.489608; the
earliest optical sample is MJD 59631.788542. The gap is **31.174 hours**.

The optical figure is an upper bound — real optical support is fragmented into
hundreds of short runs — so the null is a *strong* null: relaxing the optical
computation cannot create an intersection.

Per card §6 and §20 the interval is **not widened**, the March 2023 optical dataset is
**not substituted**, and the object continues as an ancestry and federation skeleton
with simultaneity reported as not demonstrated
([`FTRO-DEF-023`](../ledgers/deficiency-log.md#ftro-def-023)).

---

## 4. Pre-registered cold-reproduction targets and tolerances

Locked before any reproduction is executed, per card §16. Each target is chosen to
test ancestry and reproducibility rather than scientific novelty. Timebox: one focused
working day per domain; at the boundary a complete failure report is a valid exit.

### 4.1 Optical — `REPRO-OPT-001`

> **Target.** Recompute the mean comparator output ⟨Δ_{A→B}⟩ over all flag ∈ {1,2}
> samples of `PTB_Yb1E2_CombYb-PTB_Yb_CombKnoten` within MJD 59638.708333 – 59639.708333
> (the R11040 support), reading the `.dat` column 2 and applying the pinned format's
> definition with the YAML `numrhoBA`, `denrhoBA` and `sB` constants.
>
> **Acceptance.** The recomputed mean must agree with a value computed independently by
> a second implementation of the pinned format specification to within
> **1 × 10⁻¹⁸ fractional**, and the sample count must match exactly.
>
> **Rationale.** This tests whether the pinned format alone is sufficient to consume the
> archive. It deliberately does *not* test the physical frequency ratio, because
> [`FTRO-DEF-004`](../ledgers/deficiency-log.md#ftro-def-004) shows the physical
> interpretation is ambiguous without `ref_osc`.

### 4.2 Pulsar — `REPRO-PSR-001`

> **Target.** Apply the pinned clock chain to the first TOA of observation
> `uwl_220220_104059_b4` (raw topocentric MJD 59630.467530701) and recover the total
> observatory-clock correction: interpolate `pks2gps.clk` at that epoch and add the
> `gps2utc.clk` C0′ value for MJD 59630.
>
> **Pre-registered value.** `pks2gps` interpolates to **−90.44 ns** between the
> bracketing samples (59630.37155, −90.041 ns) and (59631.37502, −94.252 ns);
> `gps2utc` at MJD 59630 is **+2.80 ns**. Total ≈ **−87.64 ns**.
>
> **Acceptance.** An independent implementation must reproduce the total to within
> **±1 ns**, using linear interpolation, and must independently identify the same two
> bracketing samples.
>
> **Rationale.** This tests the one leg of the pulsar chain that *is* fully evidenced.
> It deliberately stops short of barycentring, because
> [`FTRO-DEF-012`](../ledgers/deficiency-log.md#ftro-def-012) shows the EOP artifact is
> unresolved and [`FTRO-DEF-011`](../ledgers/deficiency-log.md#ftro-def-011) shows the
> TT realisation is contested within the release.

### 4.3 VLBI — `REPRO-VLBI-001`

> **Target.** Retrieve the R11040 vgosDB from a publicly accessible archive and report
> the number of observations (scans × baselines) it contains, together with the session
> start and end epochs as recorded inside the database.
>
> **Acceptance.** Session start must match 2022-02-28T17:00 UTC to within **±5 minutes**,
> and the retrieved file must checksum-match a second independent retrieval.
>
> **Rationale.** Deliberately modest. Given
> [`FTRO-DEF-018`](../ledgers/deficiency-log.md#ftro-def-018), the *primary* question is
> whether an outsider can obtain the bytes at all without credentials. A credentialed-only
> outcome is itself the result.

### 4.4 GNSS — `REPRO-GNSS-001`

> **Target.** From `igs21991.sp3.Z` (GPS week 2199 day 1, MJD 59638, 2022-02-28), extract
> the ECEF position of PRN G01 at epoch 2022-02-28T12:00:00 UTC.
>
> **Acceptance.** An independent implementation must recover the same three coordinates
> to within **±0.1 mm** (i.e. exact agreement at the file's stated 0.1 mm precision), and
> must independently confirm the header's declared reference frame as **IGb14**.
>
> **Rationale.** SP3-c is a well-specified format; a failure here indicates a retrieval or
> decompression problem rather than a scientific one, which is precisely the platform
> property under test.

**Amendment rule.** Any change to a target or tolerance above requires a versioned
amendment to this note. If made after the corresponding result is inspected, the
amendment must be labelled post hoc and cannot satisfy the original acceptance test.

---

## 5. Rights recorded separately

See [`ledgers/rights-ledger.md`](../ledgers/rights-ledger.md). Summary:

| Source | data_rights | metadata_rights | redistribution_mode |
| --- | --- | --- | --- |
| Zenodo 17107693 | CC BY 4.0 | CC BY 4.0 | `copy_permitted` |
| PPTA DR3 | CC BY-SA 4.0 | CC BY-SA 4.0 | `link_only` |
| IGS products | no explicit machine-readable licence located | — | `link_only` |
| IVS / CDDIS | not established (auth wall) | — | `link_only` |

FTRO-authored outputs: **CC BY 4.0** for metadata and documents, **Apache-2.0** for
software. No provider content is relicensed by inclusion.

---

## 6. Gate 0 assessment

| Gate 0 requirement | Status |
| --- | --- |
| Four concrete product sets selected or explicitly missing | **Met** — optical, pulsar and GNSS pinned with checksums; VLBI session selected, products explicitly unresolved |
| Four reproduction targets and tolerances locked | **Met** — §4 above, pre-registered before execution |
| Source and FTRO rights recorded | **Met** — data, metadata and evidence rights recorded separately |
| First deficiency entries classified | **Met** — 23 entries across all five classes |

**Gate 0: passed, with the VLBI product leg carried forward as an explicit open item.**
