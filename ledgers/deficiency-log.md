# FTRO Classified Deficiency Log

> **Generated file — do not edit.** Source of truth is [`deficiency-log.json`](deficiency-log.json); regenerate with `python3 src/ftro/render_deficiencies.py`.

**Version:** 0.1.0  
**Opened:** 2026-08-25  
**Phase:** Phase 0  
**Task card:** FTRO-WS-001 v0.3

## Summary

**By class:** execution (2), policy (1), rights (2), schema (3), source_evidence (15)  
**By severity:** critical (2), high (8), low (3), medium (10)  
**By domain:** cross-domain (2), gnss (2), optical (11), pulsar (7), vlbi (1)  
**By disposition:** open (23)  

**Total entries:** 23

| ID | Class | Sev. | Domain | Title |
| --- | --- | --- | --- | --- |
| [`FTRO-DEF-003`](#ftro-def-003) | source_evidence | critical | optical | ref_osc, interval, lag and weighting are absent from every comparison, leaving the time-tag realisation unresolved |
| [`FTRO-DEF-004`](#ftro-def-004) | source_evidence | critical | optical | Comparator output is formally ambiguous between two documented physical interpretations |
| [`FTRO-DEF-001`](#ftro-def-001) | source_evidence | high | optical | Validity-flag vocabulary is documented but degenerate: every sample carries flag=1 |
| [`FTRO-DEF-002`](#ftro-def-002) | source_evidence | high | optical | Published MJD time tags are quantised to 86.4 ms, coarser than the 1 s sampling they represent |
| [`FTRO-DEF-007`](#ftro-def-007) | execution | high | optical | Named generating scripts are not present in the archive and no environment specification is supplied |
| [`FTRO-DEF-011`](#ftro-def-011) | source_evidence | high | pulsar | Timing model requests TT(BIPM2020) but the release ships a TT(BIPM2021) clock file |
| [`FTRO-DEF-012`](#ftro-def-012) | source_evidence | high | pulsar | No Earth-orientation artifact is identified anywhere in the release |
| [`FTRO-DEF-014`](#ftro-def-014) | rights | high | pulsar | PPTA DR3 is CC BY-SA 4.0, incompatible with the CC BY 4.0 assigned to FTRO metadata outputs |
| [`FTRO-DEF-018`](#ftro-def-018) | rights | high | vlbi | CDDIS returns an Earthdata login page with HTTP 200 instead of an authentication error |
| [`FTRO-DEF-023`](#ftro-def-023) | policy | high | cross-domain | Candidate window contains no four-domain simultaneous support |
| [`FTRO-DEF-005`](#ftro-def-005) | schema | medium | optical | A semantically significant second systematic uncertainty is carried in a column the format declares ignorable |
| [`FTRO-DEF-006`](#ftro-def-006) | source_evidence | medium | optical | YAML scalar uncertainties disagree with the per-sample uncertainty columns |
| [`FTRO-DEF-008`](#ftro-def-008) | source_evidence | medium | optical | One comparison was produced by a different pipeline at a different epoch |
| [`FTRO-DEF-013`](#ftro-def-013) | source_evidence | medium | pulsar | Timing model's fit metadata does not correspond to the co-located TOA file |
| [`FTRO-DEF-015`](#ftro-def-015) | source_evidence | medium | pulsar | One data release, two DOIs, ~42% duplicated content and no manifest of the split |
| [`FTRO-DEF-016`](#ftro-def-016) | source_evidence | medium | pulsar | Pinned gps2utc.clk contains 64 duplicate MJD abscissae with differing ordinates |
| [`FTRO-DEF-017`](#ftro-def-017) | source_evidence | medium | pulsar | TT(BIPM2021) values at the candidate epoch are extrapolated, not published BIPM values |
| [`FTRO-DEF-019`](#ftro-def-019) | source_evidence | medium | gnss | Product availability time is mirror-derived, not provider-declared |
| [`FTRO-DEF-021`](#ftro-def-021) | schema | medium | cross-domain | No vocabulary yet exists for a quantised time coordinate whose precision is coarser than its sampling interval |
| [`FTRO-DEF-022`](#ftro-def-022) | execution | medium | optical | Pinned processing-evidence commit post-dates the data it is cited to explain by 19 months |
| [`FTRO-DEF-009`](#ftro-def-009) | source_evidence | low | optical | Declared coverage begins 1.8 days before the first actual sample |
| [`FTRO-DEF-010`](#ftro-def-010) | schema | low | optical | Arbitrary-precision nominal ratios carry float64 round-trip artifacts |
| [`FTRO-DEF-020`](#ftro-def-020) | source_evidence | low | gnss | High-rate 30 s clock products are absent from the mirror used |

## Entries

### FTRO-DEF-001

**Validity-flag vocabulary is documented but degenerate: every sample carries flag=1**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Computing an actual validity mask from the archive's flag column.

**Known fact or required evidence.** The pinned format (INRIM/optical-link-data-format@689bda77, README.md line 77) defines column 3 as '0 = invalid, 1 = valid but experimental, 2 = valid'.

**Observed.** All 9,018,290 samples across all 12 comparisons carry flag=1. Values 0 and 2 never occur.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#global_flag_histogram`
- `data/raw/evidence/olf-README.md`

**Impact.** The flag column carries zero discriminating information. Validity intervals must be derived from sample presence/absence, not from the mask. Every published sample is formally only 'valid but experimental'; no sample is declared fully 'valid'.

**Workaround.** Derive support from contiguous runs of present samples; treat the entire archive as flag-state 1.

**Proposed response.** Ask the provider whether invalid samples were removed before publication rather than flagged, and whether flag=2 was ever intended for this release.

---

### FTRO-DEF-002

**Published MJD time tags are quantised to 86.4 ms, coarser than the 1 s sampling they represent**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Establishing the achieved timestamp resolution of the optical records for the alignment certificate.

**Known fact or required evidence.** The archive is described as one-second fractional-frequency ratios with MJD time tags.

**Observed.** Every MJD value in the sampled files is written with exactly 6 decimal places and is an exact multiple of 1e-6 d = 86.4 ms (1,564,882/1,564,882 sampled). The nominal 1 s grid appears as a dither between 0.9504 s (11 quanta) and 1.0368 s (12 quanta) in ratio 1.347775, against 1.347826 required for a mean of exactly 1 s; implied mean spacing 0.999999199 s.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#sample_spacing_histogram_s`

**Impact.** Maximum timestamp error from quantisation is +/-43.2 ms, i.e. 4.3% of the sampling interval. Any cross-domain alignment involving these records is bounded at ~43 ms, roughly eight orders of magnitude coarser than the fractional-frequency precision of the comparisons themselves. A consumer taking the MJD column at face value will mis-state the achieved resolution.

**Workaround.** Reconstruct the underlying 1 s grid by index rather than by reading the MJD column; record the quantisation as a floor in the alignment certificate.

**Proposed response.** Request time tags at a precision commensurate with the sampling interval, or an explicit statement of the intended time-tag epoch and its uncertainty.

---

### FTRO-DEF-003

**ref_osc, interval, lag and weighting are absent from every comparison, leaving the time-tag realisation unresolved**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | critical |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Task card section 5.1 required action: 'Extract the declared ref_osc, interval, lag and weighting fields.'

**Known fact or required evidence.** The pinned format defines all four as OPTIONAL YAML fields: ref_osc = 'Local reference oscillator'; interval = 'Duration of each measurement, in seconds'; lag = 'Fractional timetag location wrt the interval (1=end of the interval)'; weighting = 'Weighting function of the frequency counter'.

**Observed.** None of the four keys appears in any of the 12 YAML files. Observed keys are exactly: denrhoBA, grsA, grsB, name, nu0A, nu0B, numrhoBA, sB, uA_sys, uB_sys.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].yaml_keys`
- `data/raw/evidence/olf-README.md`

**Impact.** The omission is spec-conformant (the fields are optional) but evidentially fatal for the pilot's headline question. Without `lag` the time tag cannot be placed within its own integration interval; without `interval` the integration duration is unknown; without `weighting` the counter response is unknown; without `ref_osc` the local reference oscillator is unnamed. The optical time-tag ancestry chain therefore terminates at evidence_state=unresolved inside the archive boundary.

**Workaround.** None available from the archive. See phase0/optical-timetag-ancestry-note.md.

**Proposed response.** Request the four optional fields from the depositors; propose to the format maintainers that ref_osc, interval and lag become REQUIRED when the file is published as a citable archive.

---

### FTRO-DEF-004

**Comparator output is formally ambiguous between two documented physical interpretations**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | critical |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Assigning a single physical interpretation to the published comparator output.

**Known fact or required evidence.** The pinned format's 'Examples of comparator outputs' table lists two rows with identical rho0 = nu0B/nu0A and sB = nu0B, distinguished ONLY by the reference oscillator: Ref = A gives Delta = rho-tilde(B,A) ('Frequency of B referenced to A, relative units'); Ref = local RF gives Delta = rho-tilde(B,x) - rho-tilde(A,x) ('Difference of reduced frequency ratios, using an external reference x').

**Observed.** All 12 comparisons use rho0 = nu0B/nu0A and sB = nu0B (numrhoBA equals nu0B and denrhoBA equals nu0A to within float64 round-trip artifacts). `ref_osc` is absent in all 12.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].yaml_values`
- `data/raw/evidence/olf-README.md`

**Impact.** The archive cannot, from its own contents, distinguish which of two documented interpretations applies. The two have different reference oscillators and therefore different time-tag ancestry. This is a direct consequence of FTRO-DEF-003 and is the reason the optical leg cannot be resolved to a station time scale.

**Workaround.** Record both candidate interpretations as competing assertions rather than selecting one.

**Proposed response.** Request ref_osc from the depositors.

---

### FTRO-DEF-005

**A semantically significant second systematic uncertainty is carried in a column the format declares ignorable**

| Field | Value |
| --- | --- |
| Class | `schema` |
| Severity | medium |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Expressing both clocks' systematic uncertainties within the pinned format.

**Known fact or required evidence.** The pinned format defines column 4 as 'time-varying systematic uncertainty (optional, for accurate clocks only)' and column >4 as 'custom information. Not used in automatic data analysis scripts.'

**Observed.** All 252 data files carry five columns. The header names column 5 `uB_sys`, and it holds the B-side systematic uncertainty. Under the pinned specification a conforming consumer would discard it.

**Evidence.**

- `data/raw/evidence/olf-README.md`
- `phase0/reports/optical-inventory-summary.json#comparisons[].uncertainty_consistency`

**Impact.** The format cannot express two per-sample systematic uncertainties. A spec-conforming reader silently drops half the uncertainty budget. This is a schema limitation of the pinned format, not a mistake by the depositors.

**Workaround.** Read column 5 explicitly, documenting the departure from the pinned specification.

**Proposed response.** Propose a uB_sys column to the format maintainers.

---

### FTRO-DEF-006

**YAML scalar uncertainties disagree with the per-sample uncertainty columns**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Selecting a single systematic-uncertainty value per comparison side.

**Known fact or required evidence.** The pinned format defines YAML `uA_sys`/`uB_sys` as 'fractional uncertainty of the oscillator (optional)' and column 4 as the time-varying systematic uncertainty.

**Observed.** For 4 of 12 comparisons the YAML scalar differs from every value in the corresponding column, e.g. INRIM_ITYb1-SYRTE_Sr2 declares uB_sys = 2.2e-17 while the column takes 5 distinct values spanning 2.1e-17 to 2.3e-17. Elsewhere the YAML key is absent while the column is populated, and vice versa.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].uncertainty_consistency`

**Impact.** Uncertainty propagation into an alignment certificate is ambiguous: the scalar and the series are both plausible authorities and the format does not say which prevails.

**Workaround.** Prefer the per-sample column where present; record the scalar as a separate provider assertion.

**Proposed response.** Ask the format maintainers to state precedence when both are supplied.

---

### FTRO-DEF-007

**Named generating scripts are not present in the archive and no environment specification is supplied**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Instantiating the recorded software environment for a cold reproduction (task card section 16 step 4).

**Known fact or required evidence.** Task card section 5.1 states the record contents include 'processing code'.

**Observed.** The archive contains exactly 252 .dat and 12 .yml files; no code, README, licence or environment file. Data-file headers name two generating scripts, `06-procclocks-v3.py` (11 comparisons, generated 2025-01-20) and `convert-to-rocit.py` (NPL-Yb+(E3)-NPL-Sr1 only, generated 2024-04-22). Neither script is in the archive.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].generation_headers`

**Impact.** The optical processing step cannot be re-executed. The card's section 5.1 description of the record contents is not supported by the bytes.

**Workaround.** Treat the .dat files as the earliest reproducible artifact; the transformation that produced them is opaque.

**Proposed response.** Request the two scripts and an environment lock; correct the card's section 5.1 description in v0.4.

---

### FTRO-DEF-008

**One comparison was produced by a different pipeline at a different epoch**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Treating the archive as a single homogeneous product.

**Known fact or required evidence.** The archive is published as one Zenodo record with one DOI.

**Observed.** NPL-Yb+(E3)-NPL-Sr1 was generated by `convert-to-rocit.py` on 2024-04-22T14:53:18+02:00; the other 11 comparisons by `06-procclocks-v3.py` on 2025-01-20 between 17:01:50 and 17:04:07 +01:00. NPL-Yb+(E3)-NPL-Sr1 is also the only comparison with no support inside the candidate window (it begins at MJD 59647.73).

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].generation_headers`

**Impact.** The archive is two provenance branches under one identifier. Snapshot identity at record level conceals a heterogeneous derivation history.

**Workaround.** Model the NPL comparison as a separate derivation branch in the ancestry graph.

**Proposed response.** Record two generating activities in the manifest rather than one.

---

### FTRO-DEF-009

**Declared coverage begins 1.8 days before the first actual sample**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | low |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Computing actual support (task card section 6: no inference from campaign boundaries).

**Known fact or required evidence.** The Zenodo record and task card section 5.1 state coverage MJD 59630-59675.

**Observed.** The earliest sample in the archive is MJD 59631.78854 (PTB_Yb_CombKnoten-INRIM_ITYb1); the latest is MJD 59675.00000.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].mjd_first`

**Impact.** Declared coverage overstates support at the lower bound by 1.789 days. This directly affects the four-domain intersection test, in which the pulsar observation falls in exactly that unsupported region.

**Workaround.** Use computed support; ignore the declared range.

**Proposed response.** Correct the coverage statement in card v0.4.

---

### FTRO-DEF-010

**Arbitrary-precision nominal ratios carry float64 round-trip artifacts**

| Field | Value |
| --- | --- |
| Class | `schema` |
| Severity | low |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Consuming numrhoBA/denrhoBA at the precision the format promises.

**Known fact or required evidence.** The pinned format types numrhoBA and denrhoBA as 'Arbitrary precision floating point', explicitly so the nominal ratio is exact.

**Observed.** 7 of 12 numrhoBA values differ from the corresponding nu0B by ~1e-13 Hz, e.g. '518295836590863.6000000000002' against '518295836590863.6' (relative 3.9e-28). sB is additionally truncated to double precision, e.g. 642121496772645.1 against nu0B 642121496772645.12.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#comparisons[].yaml_values`

**Impact.** Physically negligible at 1e-28 relative, but it defeats the arbitrary-precision intent of the field and shows the value passed through a float64. A downstream consumer chaining many comparisons cannot rely on exactness.

**Workaround.** Round to the declared nominal frequency when the intent is unambiguous, recording the correction.

**Proposed response.** Serialise these fields as exact decimal strings without a float round-trip.

---

### FTRO-DEF-011

**Timing model requests TT(BIPM2020) but the release ships a TT(BIPM2021) clock file**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Assembling a self-consistent clock chain from artifacts inside one data release.

**Known fact or required evidence.** `toas_and_parameters/all/J0437-4715.par` declares `CLK TT(BIPM2020)`.

**Observed.** The only TAI-to-TT artifact in `toas_and_parameters/clock/` is `tai2tt_bipm2021.clk`, whose header reads '# TAI TT(BIPM2021)'. No TT(BIPM2020) artifact is present in the release.

**Evidence.**

- `data/raw/ppta/J0437-4715.par`
- `data/raw/ppta/tai2tt_bipm2021.clk`
- `phase0/applicability/AA-PPTA-CLKREALISATION-001.md`

**Impact.** Two artifacts in the same release specify different realisations of terrestrial time. A reproducer cannot satisfy the .par's declared CLK from the release contents alone. The discrepancy is recorded as an ApplicabilityAssessment with an indeterminate outcome, not silently resolved.

**Workaround.** None applied. Both assertions are retained; no substitution is made.

**Proposed response.** Ask the PPTA team which realisation was actually applied during production of the shipped TOAs.

---

### FTRO-DEF-012

**No Earth-orientation artifact is identified anywhere in the release**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Recovering the exact EOP artifact consumed by the PPTA timing solution (task card section 15.1).

**Known fact or required evidence.** Barycentring a pulsar TOA requires an Earth-orientation series. The card pre-registered the expectation that this node 'may terminate at a bundled or regenerated artifact whose ancestry to a particular IERS C04 snapshot is opaque.'

**Observed.** `J0437-4715.par` contains zero occurrences of EOP, UT1, IERS, C04 or polar-motion terms. The release's `clock/` directory contains only pks2gps.clk and tai2tt_bipm2021.clk. The EOP dependency is satisfied implicitly by the TEMPO2 runtime, which is not shipped or versioned in the release.

**Evidence.**

- `data/raw/ppta/J0437-4715.par`
- `data/raw/ppta/dr3-part1-files.json`

**Impact.** PRE-REGISTERED EXPECTATION CONFIRMED, and in a stronger form than anticipated: the artifact is not merely opaque, it is unidentified. evidence_state = unresolved. This removes the most likely IVS-to-pulsar shared-ancestry path, because the pulsar side of that path cannot be evidenced at all.

**Workaround.** None. No modern C04 snapshot is substituted, per task card section 20.

**Proposed response.** Ask the PPTA team for the TEMPO2 runtime revision and the eopc04 file actually present at production time.

---

### FTRO-DEF-013

**Timing model's fit metadata does not correspond to the co-located TOA file**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Verifying that the shipped .par was fitted to the shipped .tim.

**Known fact or required evidence.** `toas_and_parameters/all/` is described by the release README as 'the .tim and .par files for the full data set'.

**Observed.** `J0437-4715.par` records `NTOA 20836` and `CHI2R 23.8024 20780`, implying a fit against 20,836 TOAs. `J0437-4715.tim` contains 11,637 TOA lines and no INCLUDE, JUMP, EFAC or EQUAD directives that could reconcile the difference. START and FINISH in the .par do match the .tim's first and last TOA epochs.

**Evidence.**

- `data/raw/ppta/J0437-4715.par`
- `data/raw/ppta/J0437-4715.tim`

**Impact.** A cold reproducer loading this .par with this .tim cannot reproduce the quoted chi-squared. The .par may have been fitted against a different (e.g. combined narrowband-plus-wideband) TOA set. Recorded as an observation requiring assessment, not as a proven error.

**Workaround.** None. Recorded as an open ApplicabilityAssessment.

**Proposed response.** Ask the PPTA team which TOA set produced the shipped fit metadata.

---

### FTRO-DEF-014

**PPTA DR3 is CC BY-SA 4.0, incompatible with the CC BY 4.0 assigned to FTRO metadata outputs**

| Field | Value |
| --- | --- |
| Class | `rights` |
| Severity | high |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Assigning a redistribution mode for pulsar-leg content under task card section 7A.

**Known fact or required evidence.** Task card section 7A assigns CC BY 4.0 to FTRO-authored manifests, graph metadata, certificates, ledgers and documentation, and states that provider content retains its own licence and is never relicensed by inclusion.

**Observed.** Both PPTA DR3 collections declare 'Creative Commons Attribution-ShareAlike 4.0 International Licence' together with the rights statement 'All Rights (including copyright) CSIRO 2023.' ShareAlike is a copyleft term; CC BY-SA 4.0 content cannot be incorporated into a CC BY 4.0 work.

**Evidence.**

- `ledgers/rights-ledger.md`
- `https://data.csiro.au/collection/csiro:59374`

**Impact.** Any FTRO output that incorporated PPTA descriptive content would inherit ShareAlike, contradicting section 7A. Factual pins (checksums, filenames, epochs) are not affected, but quoted description text is.

**Workaround.** redistribution_mode = link_only for PPTA content; FTRO records facts and pointers only and quotes provider prose only under fair dealing with attribution.

**Proposed response.** State the CC BY / CC BY-SA boundary explicitly in Access Charter v0.1.

---

### FTRO-DEF-015

**One data release, two DOIs, ~42% duplicated content and no manifest of the split**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Establishing a single concept identity and a single snapshot identity for 'PPTA DR3'.

**Known fact or required evidence.** Task card section 5.2 treats PPTA DR3 as one dataset.

**Observed.** DR3 is published as two separately-DOI'd DAP collections: csiro:59374 (10.25919/j4xr-wp05, 109,298 files, 1.426 TB) and csiro:59381 (10.25919/axvw-qa43, 106,393 files, 1.348 TB). They share 90,884 identical file paths, including the entire dr2/profiles tree and the entire toas_and_parameters tree; only 18,414 and 15,509 files respectively are unique. Both are dataVersionNumber 2. Neither collection states which files are unique to it.

**Evidence.**

- `data/raw/ppta/dr3-part1-files.json`
- `data/raw/ppta/dr3-part2-files.json`

**Impact.** 'PPTA DR3' has no single provider PID. Citing either DOI alone is incomplete; citing both implies 2.77 TB when the union is smaller. Concept identity requires an FTRO-composed identifier over the pair.

**Workaround.** Define an FTRO concept identity spanning both DOIs and record the computed part overlap.

**Proposed response.** Ask CSIRO for a parent collection or an explicit split manifest.

---

### FTRO-DEF-016

**Pinned gps2utc.clk contains 64 duplicate MJD abscissae with differing ordinates**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | pulsar |
| Dataset | `IPTA/pulsar-clock-corrections` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Interpolating the GPS-to-UTC correction deterministically.

**Known fact or required evidence.** The artifact is a two-column table of MJD against correction in seconds, consumed by TEMPO2 as an interpolable series.

**Observed.** Verification procedure VP-GPS2UTC-001 v1.0.0 found 64 repeated MJD values, 45 of them carrying two different ordinates, with a maximum difference of 1.0e-09 s. One of them, MJD 55559.0, is the C0-to-C0' regime boundary itself, where the two entries differ by 3.0e-10 s. Rows are otherwise non-decreasing in MJD.

**Evidence.**

- `phase0/evidence/VA-GPS2UTC-001.json`

**Impact.** Interpolation at a duplicated abscissa is implementation-dependent; two conforming readers may differ by up to 1 ns. No duplicate falls inside the candidate window, so the pilot is unaffected, but the defect is latent for other epochs.

**Workaround.** None needed for this pilot; the candidate window is clean.

**Proposed response.** Report upstream to the IPTA repository maintainers.

---

### FTRO-DEF-017

**TT(BIPM2021) values at the candidate epoch are extrapolated, not published BIPM values**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Evidencing the terrestrial-time realisation applied at the TOA epoch.

**Known fact or required evidence.** TT(BIPM20xx) is an annually published BIPM realisation.

**Observed.** `tai2tt_bipm2021.clk` header states: 'BIPM extrapolation using the formula: 32.184 + 27667.5ns - 0.01(MJD - 59579.0)ns'. The candidate epoch MJD 59630.4675 lies 51.5 days after the extrapolation reference epoch MJD 59579. The tabulated values at MJD 59629 and 59639 reproduce the formula exactly, confirming extrapolation rather than measurement. The table extends to MJD 99999.

**Evidence.**

- `data/raw/ppta/tai2tt_bipm2021.clk`

**Impact.** The terrestrial-time leg at the candidate epoch is a linear extrapolation with no stated uncertainty, superseded by every later BIPM realisation. Bitemporally this is a living series consumed at an a-priori state, and it must not be displayed as a measured BIPM value.

**Workaround.** Record the extrapolation formula and its reference epoch as the evidence, not a BIPM publication.

**Proposed response.** Compare against the published TT(BIPM2022+) values for the same epoch and quantify the divergence in Phase 3.

---

### FTRO-DEF-018

**CDDIS returns an Earthdata login page with HTTP 200 instead of an authentication error**

| Field | Value |
| --- | --- |
| Class | `rights` |
| Severity | high |
| Domain | vlbi |
| Dataset | `CDDIS IVS archive` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Anonymous retrieval of the IVS master schedule from CDDIS.

**Known fact or required evidence.** A retrieval that requires authentication should signal it, conventionally with HTTP 401 or 403.

**Observed.** GET https://cddis.nasa.gov/archive/vlbi/ivsdata/master/2022/master2022.txt returned HTTP 200 with 10,980 bytes of Earthdata Login HTML, whose <title> is 'Earthdata Login'. The bytes checksum cleanly and would pass a naive size-and-checksum retrieval test.

**Evidence.**

- `labnotes/2026-08-25-session-01-phase0.md`

**Impact.** A federation retrieval procedure that validates only status code and checksum will silently pin a login page as if it were data, then propagate that checksum as evidence. This affects FTRO's own tooling: src/ftro/pin_igs.py has the same weakness and is recorded here as a known limitation.

**Workaround.** IVS session metadata was obtained from https://ivscc.gsfc.nasa.gov/sessions/2022/ instead. Retrieval procedures must add content-type and content-shape validation.

**Proposed response.** Add a soft-auth-wall detector to all FTRO retrieval procedures before Phase 1; record CDDIS as access_class = registered.

---

### FTRO-DEF-019

**Product availability time is mirror-derived, not provider-declared**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | gnss |
| Dataset | `IGS operational products` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Recording a provider-authoritative first-availability time for the bitemporal resolver.

**Known fact or required evidence.** Task card section 10 requires release time and first availability time as distinct primitives; section 13.3 requires resolver fixtures keyed on knowledge date.

**Observed.** The pinned artifacts carry only the BKG mirror's HTTP Last-Modified header, e.g. igr21980 at 2022-02-21T17:30:12Z and igs21980 at 2022-03-13T11:46:51Z. These are mirror file times, which approximate but are not identical to IGS release times. No IGS-declared release timestamp was located for these artifacts.

**Evidence.**

- `phase0/reports/igs-artifact-pins.json`

**Impact.** The bitemporal resolver fixtures are keyed on an approximation. The Rapid-to-Final ordering (about 1 day against about 21 days) is robust, but a knowledge date within hours of a boundary is not decidable from this evidence.

**Workaround.** Record availability as mirror-derived with evidence_state = resolvable and an explicit provenance note.

**Proposed response.** Seek an IGS-authoritative product release log for GPS weeks 2198-2199.

---

### FTRO-DEF-020

**High-rate 30 s clock products are absent from the mirror used**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | low |
| Domain | gnss |
| Dataset | `IGS operational products` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Pinning the clock artifact at the cadence a sub-daily alignment would require.

**Known fact or required evidence.** IGS Final clock products are published at 5-minute cadence (.clk) and, for many weeks, 30-second cadence (.clk_30s).

**Observed.** The BKG mirror listing for GPS weeks 2198 and 2199 contains .sp3, .clk and .erp only. No .clk_30s and no .sum summary files are present.

**Evidence.**

- `phase0/reports/igs-artifact-pins.json`

**Impact.** Sub-5-minute GNSS clock interpolation cannot be evidenced from this data centre. Given that the optical leg's own time tags are quantised at 86.4 ms (FTRO-DEF-002), this is not currently the binding constraint.

**Workaround.** Use the 5-minute Final clocks; record the cadence limit in the alignment certificate.

**Proposed response.** Locate a mirror carrying .clk_30s for these weeks if sub-5-minute alignment is later required.

---

### FTRO-DEF-021

**No vocabulary yet exists for a quantised time coordinate whose precision is coarser than its sampling interval**

| Field | Value |
| --- | --- |
| Class | `schema` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO profile v0.0.1` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Expressing FTRO-DEF-002 in the minimum record fields of task card section 10.

**Known fact or required evidence.** Section 10 requires 'sampling interval, integration interval, estimator window and validity mask as distinct fields' and 'coordinate-time scale, timestamp format and physical realisation of the timestamp'.

**Observed.** There is no field for the numerical resolution of the recorded time coordinate as serialised, which is distinct from the sampling interval and from the timestamp realisation. The optical leg needs all three: 1 s sampling, 86.4 ms serialisation quantum, unresolved physical realisation.

**Evidence.**

- `profile/ftro-graph-profile-v0.0.1.md`

**Impact.** Without this field the achieved-resolution figure in an alignment certificate cannot be traced to its cause.

**Workaround.** Profile v0.0.1 adds `time_coordinate_quantum` and `time_coordinate_quantum_evidence` as a candidate FTRO extension.

**Proposed response.** Retain through Phase 6 and decide whether to freeze.

---

### FTRO-DEF-022

**Pinned processing-evidence commit post-dates the data it is cited to explain by 19 months**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | optical |
| Dataset | `INRIM/tintervals` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Treating the pinned tintervals commit as the software that produced the archive.

**Known fact or required evidence.** Task card section 5.1 lists INRIM/tintervals at commit 2064db12777df78bc87f68f7710a47176192c2e1 as 'Processing evidence'.

**Observed.** That commit is dated 2026-08-16T16:00:18Z with message 'Prepare documentation for 0.3.0'. The archive's data files were generated on 2025-01-20 and 2024-04-22. The pinned commit therefore cannot be the software that produced them.

**Evidence.**

- `phase0/evidence/identities.json`

**Impact.** The pin is valid as a snapshot of a related tool but must not be presented as the generating software. Its role is contextual, not causal.

**Workaround.** Record tintervals with edge type `contextualized_by`, not `generated_by`.

**Proposed response.** Ask the depositors which tintervals revision was used; correct the card's section 5.1 wording in v0.4.

---

### FTRO-DEF-023

**Candidate window contains no four-domain simultaneous support**

| Field | Value |
| --- | --- |
| Class | `policy` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `pilot window MJD 59630-59640` |
| Disposition | `open` |
| Version | 1.0.0 |

**Failed step.** Task card section 2: constructing a four-domain walking skeleton for a common interval.

**Known fact or required evidence.** The card proposes MJD 59630-59640 as a candidate, explicitly 'retained as test interval, not guaranteed overlap'.

**Observed.** Computed supports inside the window: GNSS 240.000 h (continuous), optical 197.075 h (upper bound), VLBI 123.500 h, pulsar 1.067 h (one observation, MJD 59630.445127-59630.489608). The pulsar support is disjoint from both optical (gap 31.174 h) and VLBI. Four-domain intersection is empty; optical+VLBI+GNSS intersect over 118.575 h.

**Evidence.**

- `phase0/reports/four-domain-intersection.json`

**Impact.** Simultaneity across four domains is NOT DEMONSTRATED for this window. Per sections 6 and 20 the interval is not widened and no substitute dataset is introduced. The object continues as an ancestry and federation skeleton, and the alignment certificate will carry status no_common_support.

**Workaround.** None applied by design.

**Proposed response.** Record as a pilot outcome. Any future window change is a new, versioned selection decision, not an amendment to this one.

---
