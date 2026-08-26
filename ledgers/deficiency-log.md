# FTRO Classified Deficiency Log

> **Generated file — do not edit.** Source of truth is [`deficiency-log.json`](deficiency-log.json); regenerate with `python3 src/ftro/render_deficiencies.py`.

**Version:** 0.14.0  
**Opened:** 2026-08-25  
**Phase:** Phase 0  
**Task card:** FTRO-WS-001 v0.3

## Summary

**By class:** execution (38), policy (1), rights (2), schema (4), source_evidence (19)  
**By severity:** critical (2), high (35), low (3), medium (24)  
**By domain:** cross-domain (25), gnss (5), optical (20), pulsar (8), vlbi (6)  
**By disposition:** open (24), resolved (40)  
**By responsible party:** ftro (40), provider (24)  
**By finding type:** assurance_gap (7), current_defect (17), external_evidence_gap (17), latent_regression (22), recorded_outcome (1)  
**By affects:** blocks_workflow (11), changes_result (12), maintenance_only (9), no_present_effect (32)  

**Total entries:** 64 · **self-directed:** 40

> **Convergence measure.** An append-only count can only rise, so totals cannot show progress. The measure is: **open entries that could change the Phase-0 result and are not external evidence gaps.**
>
> Currently: **0** — the remaining result-bearing entries are provider evidence gaps and the recorded null itself, which are the deliverable rather than software failures.

| ID | Class | Sev. | Type | Affects | Party | Title |
| --- | --- | --- | --- | --- | --- | --- |
| [`FTRO-DEF-003`](#ftro-def-003) | source_evidence | critical | external_evidence_gap | changes_result | provider | ref_osc, interval, lag and weighting are absent from every comparison, leaving the time-tag realisation unresolved |
| [`FTRO-DEF-004`](#ftro-def-004) | source_evidence | critical | external_evidence_gap | changes_result | provider | Comparator output is formally ambiguous between two documented physical interpretations |
| [`FTRO-DEF-001`](#ftro-def-001) | source_evidence | high | external_evidence_gap | changes_result | provider | Validity-flag vocabulary is documented but degenerate: every sample carries flag=1 |
| [`FTRO-DEF-002`](#ftro-def-002) | source_evidence | high | external_evidence_gap | changes_result | provider | Published MJD time tags are quantised to 86.4 ms, coarser than the sampling interval they represent |
| [`FTRO-DEF-007`](#ftro-def-007) | execution | high | current_defect | blocks_workflow | provider | Named generating scripts are not present in the archive and no environment specification is supplied |
| [`FTRO-DEF-011`](#ftro-def-011) | source_evidence | high | external_evidence_gap | changes_result | provider | Timing model requests TT(BIPM2020) but the release ships a TT(BIPM2021) clock file |
| [`FTRO-DEF-012`](#ftro-def-012) | source_evidence | high | external_evidence_gap | changes_result | provider | The selected timing model declares no Earth-orientation artifact, and none is identified in the retrieved release inventory |
| [`FTRO-DEF-014`](#ftro-def-014) | rights | high | current_defect | blocks_workflow | provider | PPTA DR3 is CC BY-SA 4.0, incompatible with the CC BY 4.0 assigned to FTRO metadata outputs |
| [`FTRO-DEF-018`](#ftro-def-018) | rights | high | current_defect | blocks_workflow | **self** | CDDIS returns an Earthdata login page with HTTP 200 instead of an authentication error |
| [`FTRO-DEF-023`](#ftro-def-023) | policy | high | recorded_outcome | changes_result | provider | Candidate window contains no four-domain simultaneous support |
| [`FTRO-DEF-024`](#ftro-def-024) | source_evidence | high | current_defect | maintenance_only | **self** | SELF-DIRECTED: FTRO composed a snapshot identity for a leg where the provider supplies one |
| [`FTRO-DEF-025`](#ftro-def-025) | source_evidence | high | current_defect | blocks_workflow | **self** | SELF-DIRECTED: a leg was recorded unresolved without canvassing alternative data centres |
| [`FTRO-DEF-027`](#ftro-def-027) | execution | high | current_defect | blocks_workflow | **self** | SELF-DIRECTED: a headline verification count was not reproducible from any committed script |
| [`FTRO-DEF-029`](#ftro-def-029) | execution | high | assurance_gap | no_present_effect | **self** | SELF-DIRECTED: a conformance rule was introduced and violated in the same commit |
| [`FTRO-DEF-030`](#ftro-def-030) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the convention-sensitivity scan could not perform the reanalysis it reported |
| [`FTRO-DEF-031`](#ftro-def-031) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the committed test suite did not exercise the behaviour it was written to protect |
| [`FTRO-DEF-032`](#ftro-def-032) | execution | high | current_defect | blocks_workflow | **self** | SELF-DIRECTED: four artifacts asserted evidence_state=resolvable under validation the profile forbids |
| [`FTRO-DEF-034`](#ftro-def-034) | execution | high | current_defect | maintenance_only | **self** | SELF-DIRECTED: the §9.2 conformance test exempted every record that omitted the field |
| [`FTRO-DEF-035`](#ftro-def-035) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: projection-only verification -- tests checked a hand-corrected manifest while its generators drifted |
| [`FTRO-DEF-037`](#ftro-def-037) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: a contract change updated one caller of two, and the report published a wrong number |
| [`FTRO-DEF-038`](#ftro-def-038) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the consumer gate and its tests both equated an absent field with success |
| [`FTRO-DEF-042`](#ftro-def-042) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: preflight checked key membership, so a null digest passed as an expectation |
| [`FTRO-DEF-043`](#ftro-def-043) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the consumer gate accepted JSON false as integer zero and ignored per-pin state |
| [`FTRO-DEF-044`](#ftro-def-044) | execution | high | current_defect | maintenance_only | **self** | SELF-DIRECTED: --register was an escape hatch that also could not register anything |
| [`FTRO-DEF-046`](#ftro-def-046) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the tests guarding the sensitivity computation only read its output |
| [`FTRO-DEF-048`](#ftro-def-048) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the segmentation oracle validated topology, not extent |
| [`FTRO-DEF-049`](#ftro-def-049) | execution | high | assurance_gap | no_present_effect | **self** | SELF-DIRECTED: generated-file version enforcement did not exist |
| [`FTRO-DEF-050`](#ftro-def-050) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the consumer permitted absent per-pin state and incoherent counters |
| [`FTRO-DEF-053`](#ftro-def-053) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the oracle fixture contained no gap at a scientifically active tolerance boundary |
| [`FTRO-DEF-054`](#ftro-def-054) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the runtime consumer verified a report's self-description, not its completeness |
| [`FTRO-DEF-055`](#ftro-def-055) | execution | high | assurance_gap | maintenance_only | **self** | SELF-DIRECTED: generated-version enforcement had two laundering paths |
| [`FTRO-DEF-058`](#ftro-def-058) | execution | high | current_defect | blocks_workflow | **self** | SELF-DIRECTED: pin_igs could promote a report its own consumer rejects |
| [`FTRO-DEF-059`](#ftro-def-059) | execution | high | current_defect | blocks_workflow | **self** | SELF-DIRECTED: the committed vgosDB report was rejected by the shared consumer gate |
| [`FTRO-DEF-060`](#ftro-def-060) | execution | high | latent_regression | changes_result | **self** | SELF-DIRECTED: scientific meaning was read from unauthenticated report fields |
| [`FTRO-DEF-061`](#ftro-def-061) | execution | high | latent_regression | changes_result | **self** | SELF-DIRECTED: main and sensitivity computations carried duplicate domain constants |
| [`FTRO-DEF-062`](#ftro-def-062) | execution | high | latent_regression | no_present_effect | **self** | SELF-DIRECTED: a credit function assumed sorted input its caller happened to provide |
| [`FTRO-DEF-063`](#ftro-def-063) | execution | high | assurance_gap | maintenance_only | **self** | SELF-DIRECTED: the review protocol had no terminating condition |
| [`FTRO-DEF-005`](#ftro-def-005) | schema | medium | current_defect | blocks_workflow | provider | A semantically significant second systematic uncertainty is carried in a column the format declares ignorable |
| [`FTRO-DEF-006`](#ftro-def-006) | source_evidence | medium | external_evidence_gap | blocks_workflow | provider | YAML scalar uncertainties disagree with the per-sample uncertainty columns |
| [`FTRO-DEF-008`](#ftro-def-008) | source_evidence | medium | external_evidence_gap | no_present_effect | provider | One comparison was produced by a different pipeline at a different epoch |
| [`FTRO-DEF-013`](#ftro-def-013) | source_evidence | medium | external_evidence_gap | changes_result | provider | Timing model's fit metadata does not correspond to the co-located TOA file |
| [`FTRO-DEF-015`](#ftro-def-015) | source_evidence | medium | external_evidence_gap | blocks_workflow | provider | One data release, two DOIs, ~42% duplicated content and no manifest of the split |
| [`FTRO-DEF-016`](#ftro-def-016) | source_evidence | medium | external_evidence_gap | no_present_effect | provider | Pinned gps2utc.clk contains 64 duplicate MJD abscissae with differing ordinates |
| [`FTRO-DEF-017`](#ftro-def-017) | source_evidence | medium | external_evidence_gap | changes_result | provider | TT(BIPM2021) values at the candidate epoch are extrapolated, not published BIPM values |
| [`FTRO-DEF-019`](#ftro-def-019) | source_evidence | medium | external_evidence_gap | maintenance_only | provider | Product availability time is mirror-derived, not provider-declared |
| [`FTRO-DEF-021`](#ftro-def-021) | schema | medium | current_defect | no_present_effect | provider | No vocabulary yet exists for a quantised time coordinate whose precision is coarser than its sampling interval |
| [`FTRO-DEF-022`](#ftro-def-022) | execution | medium | current_defect | no_present_effect | provider | Pinned processing-evidence commit post-dates the data it is cited to explain by 19 months |
| [`FTRO-DEF-026`](#ftro-def-026) | source_evidence | medium | external_evidence_gap | no_present_effect | provider | A vgosDB archive checksum does not record which wrapper member a chain consumed |
| [`FTRO-DEF-028`](#ftro-def-028) | source_evidence | medium | external_evidence_gap | no_present_effect | provider | The published vgosDB was silently reprocessed in 2025 with no version signal outside its wrappers |
| [`FTRO-DEF-033`](#ftro-def-033) | schema | medium | assurance_gap | maintenance_only | **self** | SELF-DIRECTED: version labels stopped identifying a constraint state |
| [`FTRO-DEF-036`](#ftro-def-036) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the spacing analysis differenced binary floats and invented a distinct spacing |
| [`FTRO-DEF-039`](#ftro-def-039) | execution | medium | current_defect | maintenance_only | **self** | SELF-DIRECTED: --update could legalise an unbumped content change |
| [`FTRO-DEF-040`](#ftro-def-040) | execution | medium | assurance_gap | no_present_effect | **self** | SELF-DIRECTED: 'every versioned artifact' was a manual list with no completeness check |
| [`FTRO-DEF-041`](#ftro-def-041) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: a transport failure produced a traceback instead of a rejected report |
| [`FTRO-DEF-045`](#ftro-def-045) | execution | medium | assurance_gap | no_present_effect | **self** | SELF-DIRECTED: discovery covered four directories, and excluded generated files had no compensating check |
| [`FTRO-DEF-047`](#ftro-def-047) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: a mutation test asserted only a non-zero exit, which the unmutated run also produces |
| [`FTRO-DEF-051`](#ftro-def-051) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: an explicit digest bypassed preflight, and a trailing newline validated |
| [`FTRO-DEF-052`](#ftro-def-052) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the discovery suffix list advertised formats the pattern could not parse |
| [`FTRO-DEF-056`](#ftro-def-056) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: container-shape checks ran only when the container was already the right type |
| [`FTRO-DEF-057`](#ftro-def-057) | execution | medium | latent_regression | no_present_effect | **self** | SELF-DIRECTED: the 'nothing was fetched' test measured 'nothing was cached' |
| [`FTRO-DEF-064`](#ftro-def-064) | execution | medium | current_defect | maintenance_only | **self** | SELF-DIRECTED: the git-based version gate crashed on a document that gains a version |
| [`FTRO-DEF-009`](#ftro-def-009) | source_evidence | low | external_evidence_gap | changes_result | provider | Declared coverage begins 1.8 days before the first actual sample |
| [`FTRO-DEF-010`](#ftro-def-010) | schema | low | current_defect | no_present_effect | provider | Arbitrary-precision nominal ratios carry float64 round-trip artifacts |
| [`FTRO-DEF-020`](#ftro-def-020) | source_evidence | low | external_evidence_gap | no_present_effect | provider | High-rate 30 s clock products are absent from the mirror used |

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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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

**Published MJD time tags are quantised to 86.4 ms, coarser than the sampling interval they represent**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107693` |
| Disposition | `open` |
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
| Version | 1.1.0 |

**Failed step.** Establishing the achieved timestamp resolution of the optical records for the alignment certificate.

**Known fact or required evidence.** The archive is described as one-second fractional-frequency ratios with MJD time tags.

**Observed.** Every MJD value in the archive is written with exactly 6 decimal places and is an exact multiple of 1e-6 d = 86.4 ms: 9,018,290 of 9,018,290 values tested, 0 exceptions (mjd_quantum_check). The nominal 1 s grid appears as a dither between 0.9504 s (11 quanta) and 1.0368 s (12 quanta) in ratio 1.347775, against 1.347826 required for a mean of exactly 1 s; implied mean spacing 0.999999199 s. The archive declares no sampling grid, so the one-second grid is an INFERENCE strongly consistent with the observed dither, not a declared fact.

**Evidence.**

- `phase0/reports/optical-inventory-summary.json#mjd_quantum_check`
- `phase0/reports/optical-inventory-summary.json#sample_spacing_histogram_s`
- `phase0/reports/optical-inventory-summary.json#sample_spacing_coverage`

**Impact.** Under the one-second-grid model the maximum serialisation error is +/-43.2 ms, 4.3% of the nominal sampling interval. Any cross-domain alignment involving these records is bounded at ~43 ms by serialisation alone. That bound is not commensurable with the 1e-17-level fractional-frequency uncertainty the same files report -- a time quantum and a dimensionless ratio are different kinds of quantity, and no ratio between them is meaningful -- but it is the binding limit on placing these records on any shared time axis.

**Workaround.** If the one-second-grid model is accepted, reconstruct epochs by sample index rather than by reading the MJD column, and record the model as a stated assumption.

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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `provider` |
| Version | 1.1.0 |

**Failed step.** Expressing both clocks' systematic uncertainties within the pinned format.

**Known fact or required evidence.** The pinned format defines column 4 as 'time-varying systematic uncertainty (optional, for accurate clocks only)' and column >4 as 'custom information. Not used in automatic data analysis scripts.'

**Observed.** All 252 data files carry five columns. The header names column 5 `uB_sys`, and it holds the B-side systematic uncertainty. Under the pinned specification a conforming consumer would discard it.

**Evidence.**

- `data/raw/evidence/olf-README.md`
- `phase0/reports/optical-inventory-summary.json#comparisons[].uncertainty_consistency`

**Impact.** The format cannot express two per-sample systematic uncertainties. A spec-conforming reader silently drops half the uncertainty budget. This is a schema limitation of the pinned format; the departure is structurally permitted by it.

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
| Finding type | `external_evidence_gap` |
| Affects | `blocks_workflow` |
| Responsible party | `provider` |
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
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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
| Finding type | `current_defect` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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

**The selected timing model declares no Earth-orientation artifact, and none is identified in the retrieved release inventory**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | pulsar |
| Dataset | `doi:10.25919/j4xr-wp05` |
| Disposition | `open` |
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
| Version | 1.1.0 |

**Failed step.** Recovering the exact EOP artifact consumed by the PPTA timing solution (task card section 15.1).

**Known fact or required evidence.** Barycentring a pulsar TOA requires an Earth-orientation series. The card pre-registered the expectation that this node 'may terminate at a bundled or regenerated artifact whose ancestry to a particular IERS C04 snapshot is opaque.'

**Observed.** J0437-4715.par contains zero occurrences of EOP, UT1, IERS, C04 or polar motion. The release's clock/ directory contains only pks2gps.clk and tai2tt_bipm2021.clk. The release identifies no EOP artifact. Barycentring requires an Earth-orientation series, so one must have been supplied by the production environment; the TEMPO2 runtime is the most likely source, but that is an INFERENCE and no runtime is shipped or versioned in the release. SCOPE: verified against J0437-4715.par and the part-1 file listing; the part-2 listing and the remaining ~2.77 TB were not searched.

**Evidence.**

- `data/raw/ppta/J0437-4715.par`
- `data/raw/ppta/dr3-part1-files.json`

**Impact.** PRE-REGISTERED EXPECTATION NOT MET AS WRITTEN: card §15.1 anticipated a bundled or regenerated artifact whose ancestry to a C04 snapshot is OPAQUE. The observed outcome is different and more severe -- the artifact is UNIDENTIFIED, evidence_state = unresolved -- so the expectation is not strictly confirmed. This removes the most likely IVS-to-pulsar shared-ancestry path, because the pulsar side cannot be evidenced at all.

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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `blocks_workflow` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `changes_result` |
| Responsible party | `provider` |
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
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.2.0 |

**Failed step.** Anonymous retrieval of the IVS master schedule from CDDIS.

**Known fact or required evidence.** A retrieval that requires authentication should signal it, conventionally with HTTP 401 or 403.

**Observed.** GET https://cddis.nasa.gov/archive/vlbi/ivsdata/master/2022/master2022.txt returned HTTP 200 with 10,980 bytes of Earthdata Login HTML, whose <title> is 'Earthdata Login'. The bytes checksum cleanly and would pass a naive size-and-checksum retrieval test.

**Evidence.**

- `labnotes/2026-08-25-session-01-phase0.md`

**Impact.** A federation retrieval procedure that validates only status code and checksum will silently pin a login page as if it were data, then propagate that checksum as evidence. This affects FTRO's own tooling: src/ftro/pin_igs.py has the same weakness and is recorded here as a known limitation.

**Workaround.** IVS session metadata was obtained from https://ivscc.gsfc.nasa.gov/sessions/2022/ instead, and the vgosDB itself from OPAR (see FTRO-DEF-025).

**Proposed response.** RESOLVED for FTRO tooling 2026-08-25. All four pinners (pin_igs, pin_vgosdb, pin_ppta, pin_evidence_repos) perform content-shape validation: HTML/auth-marker detection, magic-byte checks, actual decompression via src/ftro/unixz.py for .Z products, inner-format checks, and archive-structure checks for vgosDB. All fail closed on a digest mismatch. Profile §9.2 requires content_validated before evidence_state = resolvable, and 34 committed tests enforce it. CORRECTION (v1.2.0): earlier versions of this entry claimed 'a regression test against the live CDDIS URL'. No such committed test ever existed -- the live check was run interactively once and never committed. The committed suite uses deterministic fixtures and makes NO network call (FTRO-DEF-031 v2.0.0). The CDDIS behaviour itself is unchanged and remains reportable upstream.

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
| Finding type | `external_evidence_gap` |
| Affects | `maintenance_only` |
| Responsible party | `provider` |
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
| Finding type | `external_evidence_gap` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
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
| Finding type | `current_defect` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
| Version | 1.0.0 |

**Failed step.** Expressing FTRO-DEF-002 in the minimum record fields of task card section 10.

**Known fact or required evidence.** Section 10 requires 'sampling interval, integration interval, estimator window and validity mask as distinct fields' and 'coordinate-time scale, timestamp format and physical realisation of the timestamp'.

**Observed.** There is no field for the numerical resolution of the recorded time coordinate as serialised, which is distinct from the sampling interval and from the timestamp realisation. The optical leg needs all three: 1 s sampling, 86.4 ms serialisation quantum, unresolved physical realisation.

**Evidence.**

- `profile/ftro-graph-profile-v0.0.3.md`

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
| Finding type | `current_defect` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
| Version | 1.1.0 |

**Failed step.** Treating the pinned tintervals commit as the software that produced the archive.

**Known fact or required evidence.** Task card section 5.1 lists INRIM/tintervals at commit 2064db12777df78bc87f68f7710a47176192c2e1 as 'Processing evidence'.

**Observed.** That commit is dated 2026-08-16T16:00:18Z with message 'Prepare documentation for 0.3.0'. The archive's data files were generated on 2025-01-20 and 2024-04-22. The pinned revision therefore cannot be the software that produced them; an earlier revision of the same tool is not excluded, and none is pinned.

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
| Finding type | `recorded_outcome` |
| Affects | `changes_result` |
| Responsible party | `provider` |
| Version | 1.1.0 |

**Failed step.** Task card section 2: constructing a four-domain walking skeleton for a common interval.

**Known fact or required evidence.** The card proposes MJD 59630-59640 as a candidate, explicitly 'retained as test interval, not guaranteed overlap'.

**Observed.** Computed supports inside the window: GNSS 240.000 h (daily product validity, upper bound), optical 133.112 h (EXACT union of 7,398 contiguous valid runs merged into 1,353 disjoint intervals), VLBI 123.500 h (scheduled session intervals, upper bound), pulsar 1.067 h (one observation, MJD 59630.445127-59630.489608). The pulsar support is disjoint from optical (gap 31.174 h) and from VLBI, but lies wholly inside GNSS product validity: gnss n pulsar = 1.067 h. Every THREE- and FOUR-domain combination containing the pulsar is therefore empty, as are the two pairs optical n pulsar and VLBI n pulsar. optical n VLBI n GNSS intersect over 82.013 h. CLASSIFICATION: this entry records the pilot's RESULT, not a defect to be fixed. It is retained in the ledger because card §6 requires the empty intersection to be reported rather than repaired, and it is excluded from the convergence measure for the same reason.

**Evidence.**

- `phase0/reports/four-domain-intersection.json`

**Impact.** Simultaneity across four domains is NOT DEMONSTRATED for this window. Per §6 and §20 the interval is not widened and no substitute dataset is introduced. Because the VLBI and GNSS legs are upper bounds, refining them into exact per-observation support can only remove overlap, so the no_common_support result is robust under these conservative envelopes. The object continues as an ancestry and federation skeleton and the alignment certificate carries status no_common_support.

**Workaround.** None applied by design.

**Proposed response.** Record as a pilot outcome. Any future window change is a new, versioned selection decision, not an amendment to this one.

---

### FTRO-DEF-024

**SELF-DIRECTED: FTRO composed a snapshot identity for a leg where the provider supplies one**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | optical |
| Dataset | `doi:10.5281/zenodo.17107692` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Establishing concept and snapshot identity for the optical leg (task card §10, §11.3).

**Known fact or required evidence.** Task card §10 requires an FTRO-composed snapshot identity only 'when a provider supplies no immutable snapshot identifier'. Zenodo supplies a concept DOI (10.5281/zenodo.17107692) and a version DOI (10.5281/zenodo.17107693), asserted in four independent record fields: conceptdoi, conceptrecid, links.parent_doi vs links.self_doi, and metadata.relations.version[0].parent.pid_value.

**Observed.** Phase 0 recorded concept_id as the VERSION DOI, snapshot_kind as 'ftro_composed', and justified this with the note 'The record declares no version string (metadata.version is null), so concept and snapshot are not separable by provider metadata alone.' That reasoning is wrong in three ways: metadata.version is ABSENT rather than null; a human-readable version string has no bearing on PID separability; and the concept DOI was present in the cached record the pipeline had already read. The string '17107692' appeared nowhere in the repository.

**Evidence.**

- `phase0/evidence/identities.json`
- `data/raw/zenodo-17107693/record.json`
- `labnotes/2026-08-25-session-02-review-corrections.md`

**Impact.** A false positive against task card §10's own precondition: FTRO invented an identity where the provider had supplied one, in the very leg used to demonstrate the two-level identity model. Had it stood, any consumer reconciling FTRO's identity against Zenodo's would have found no common identifier. This is the mirror image of the failure the project exists to catch -- not missing evidence, but available evidence not read.

**Workaround.** None needed; corrected in place.

**Proposed response.** Corrected 2026-08-25: concept_id is now the concept DOI, snapshot_id the version DOI, snapshot_kind 'provider_immutable'. Added a rule to the profile: before composing an FTRO identity, record which provider fields were checked and found absent.

---

### FTRO-DEF-025

**SELF-DIRECTED: a leg was recorded unresolved without canvassing alternative data centres**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | high |
| Domain | vlbi |
| Dataset | `IVS session R11040 vgosDB` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.1.0 |

**Failed step.** Establishing whether the R11040 vgosDB is publicly retrievable.

**Known fact or required evidence.** IVS distributes session data through several data centres. CDDIS requires an Earthdata login; OPAR (Observatoire de Paris) serves the same archives anonymously.

**Observed.** Phase 0 tried CDDIS, hit the soft authentication wall (FTRO-DEF-018), and recorded evidence_state = unresolved for the VLBI data products, reporting that credentials or a non-CDDIS route were needed. OPAR was not tried. It serves https://ivsopar.obspm.fr/vlbi/ivsdata/vgosdb/2022/20220228-r11040.tgz anonymously: 19,610,760 bytes, SHA-256 0211948678aebfbcfdcf0f8d1ab8777bfd940605668073b8deb99aba1ff2ba54, validated as a gzip/tar vgosDB with 296 members.

**Evidence.**

- `phase0/reports/vlbi-vgosdb-pin.json`
- `src/ftro/pin_vgosdb.py`

**Impact.** An access-class conclusion was drawn from a single data centre. 'unresolved' asserted unavailability that was not established, which is exactly the kind of unsupported null the typed-incompleteness model is meant to prevent. Corrected: the vgosDB is now pinned and content-validated; the downstream analysis-centre product and IERS EOP series remain unresolved.

**Workaround.** None needed; corrected in place.

**Proposed response.** Corrected 2026-08-25; rule restated after review. The original wording attached route enumeration to access_class, which contradicts profile §9.2: access_class is a property of a single retrieval path, so one content-validated anonymous retrieval establishes access_class = public FOR THAT PATH and needs no canvass. Enumeration gates the dataset-level NEGATIVE instead. Rule adopted (D-025, revised): evidence_state = unresolved, and any dataset-scoped claim of unavailability, may only be recorded after every provider-listed distribution channel has been attempted, with the attempts recorded as a machine-readable routes_tried array. The IVS page lists three centres: CDDIS (registered), BKG (unreachable -- no TCP on 443 from two independent networks, so its class is NOT established) and OPAR (public). BKG was omitted from the original enumeration; recording it does not change the OPAR pin.

---

### FTRO-DEF-026

**A vgosDB archive checksum does not record which wrapper member a chain consumed**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | vlbi |
| Dataset | `IVS session R11040 vgosDB` |
| Disposition | `open` |
| Finding type | `external_evidence_gap` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
| Version | 2.0.0 |

**Failed step.** Recording which internal state of 'the R11040 vgosDB' a downstream chain used.

**Known fact or required evidence.** A snapshot identity must name the immutable state actually consumed (task card §11.3). The vgosDB format manual (vgosDB_format_2021Sep20.pdf §7.1-§7.2) defines a wrapper as 'an ASCII file that contains pointers to the files in a vgosDB', states that 'Wrappers are never over written' and that a new wrapper is created whenever files are added, and provides an InputWrapper keyword recording wrapper-to-wrapper derivation.

**Observed.** The archive contains SEVEN wrapper FILENAMES but only FIVE distinct wrapper byte sequences: 20220228-r11040_V004_iGSFC_kall.wrp and _V004_iIVS_kall.wrp are byte-identical (sha256 3c52b94f...c16a), as are the two V005 files (sha256 310c5815...b67d). Institution designators GSFC, IVS and MPI appear, but only MPI and GSFC produced distinct wrapper bytes; 'iIVS' is a redesignation of identical content, not a third centre's independent product. Every wrapper from V002 onward records InputWrapper 20220228-r11040_V001_iMPI_kall.wrp. The archive byte checksum pins the container and every member, but records nothing about which wrapper a downstream analysis selected.

**Evidence.**

- `phase0/reports/vlbi-vgosdb-pin.json#wrapper_records`
- `phase0/reports/vlbi-vgosdb-pin.json#duplicate_wrapper_groups`
- `phase0/reports/vlbi-vgosdb-pin.json#producing_centres`

**Impact.** Two chains citing the same archive checksum may have consumed different wrapper members. CORRECTION (v2.0.0): the original entry concluded that a THIRD identity level was required. That was wrong. A wrapper is an ordinary archive member and an ASCII pointer file, so the selection is expressible with existing vocabulary -- a member File entity keyed by member SHA-256, plus a consumption edge -- and the format's own InputWrapper keyword already supplies the derived_from relation. Keying on the member digest is also strictly better than keying on the filename, because it collapses 7 names to the 5 real states. The schema is adequate; what was missing was the recording.

**Workaround.** The pin report now records every wrapper member with its digest, RunTimeTag and InputWrapper.

**Proposed response.** Require any VLBI chain to name the wrapper member it consumed (path + SHA-256) via a consumption edge. No profile identity-tier change. Retract profile §5.2 as originally written.

---

### FTRO-DEF-027

**SELF-DIRECTED: a headline verification count was not reproducible from any committed script**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO Phase-0 tooling` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Supporting the FTRO-DEF-002 quantisation claim from committed evidence.

**Known fact or required evidence.** Task card §8.2 requires that no step depend on an undocumented manual convention, and decision D-003 records that retrieval and analysis are implemented as committed scripts.

**Observed.** Phase 0 reported the quantisation as 'verified on 1,564,882 of 1,564,882 sampled values' in five documents. That figure came from an ad-hoc interactive command that read only the first 40 .dat files; no committed script performed a decimal-place or 1e-6-multiple test, and the cited evidence pointer (sample_spacing_histogram_s) does not contain it. Separately, that histogram is truncated to the 20 most common spacings, covering 8,999,974 of 9,018,038 intervals, so it could not support an exceptionless claim either.

**Evidence.**

- `src/ftro/analyse_optical.py#mjd_quantum_check`
- `phase0/reports/optical-inventory-summary.json#sample_spacing_coverage`

**Impact.** A quantitative claim in the strongest optical finding rested on an unrecorded sample of 0.44% of the corpus while reading as an exhaustive census. The underlying finding survives -- the committed test now covers 9,018,290 of 9,018,290 values with 0 exceptions -- but the evidence discipline failed, in the same class of error this ledger exists to record.

**Workaround.** None; the test is now implemented and the counts regenerated.

**Proposed response.** Corrected 2026-08-25: analyse_optical.py emits mjd_quantum_check and sample_spacing_coverage. Rule adopted: a number quoted in a finding must be traceable to a key in a committed report, and evidence pointers must name that key.

---

### FTRO-DEF-028

**The published vgosDB was silently reprocessed in 2025 with no version signal outside its wrappers**

| Field | Value |
| --- | --- |
| Class | `source_evidence` |
| Severity | medium |
| Domain | vlbi |
| Dataset | `IVS session R11040 vgosDB` |
| Disposition | `open` |
| Finding type | `external_evidence_gap` |
| Affects | `no_present_effect` |
| Responsible party | `provider` |
| Version | 1.0.0 |

**Failed step.** Establishing when the retrieved archive's content was produced.

**Known fact or required evidence.** The session was observed 2022-02-28. The vgosDB format states that wrappers are never overwritten and that a new wrapper is created whenever files are added.

**Observed.** The archive's latest wrapper V005 carries RunTimeTag 2025/12/12 21:18:49 UTC in a sixth Process block (SgLib/nuSolve 0.8.3) absent from V004, and repoints 24 members to _V001 variants; those members and History/20220228-r11040_V005_knuSolve.hist carry tar mtime 2025-12-12. The HTTP Last-Modified is 2025-12-15T16:46:58Z, three days later, and dates the mirror publication rather than the reprocessing act. Nothing in the archive FILENAME, the URL or the IVS session listing signals that the 2022 session archive now contains 2025 reprocessing.

**Evidence.**

- `phase0/reports/vlbi-vgosdb-pin.json#wrapper_records`
- `phase0/reports/vlbi-vgosdb-pin.json#volatility_warning`

**Impact.** A consumer retrieving '20220228-r11040.tgz' by that stable-looking name gets different bytes before and after 2025-12. The internal RunTimeTag is the only reliable anchor; the HTTP header is secondary and lags it. Any FTRO snapshot identity for this archive pins the retrieval, not the session as released in 2022.

**Workaround.** Pin by byte checksum and record the latest wrapper RunTimeTag as the content anchor.

**Proposed response.** Ask IVS whether reprocessed session archives can carry a version token in the filename or an accompanying manifest.

---

### FTRO-DEF-029

**SELF-DIRECTED: a conformance rule was introduced and violated in the same commit**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO profile v0.0.1 and phase0/evidence/identities.json` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 2.0.0 |

**Failed step.** Conforming to profile §5.1, introduced by commit 2c31279.

**Known fact or required evidence.** Profile §5.1, added in that commit, states that a manifest asserting `ftro_composed` MUST record `composition_precondition_checked[]` and `composition_justification`, and that 'An ftro_composed identity without this record is not conforming.'

**Observed.** At commit 2c31279 all composed identities in phase0/evidence/identities.json lacked both fields. CORRECTION (v2.0.0): the original count of FIVE was wrong. §5.1's text is unqualified, so the denominator spans BOTH identity levels: seven records assert ftro_composed (five via snapshot_kind, plus ftro:concept:ppta/dr3 and ftro:concept:igs/igs/orbit via concept_kind). At 0b41929, 2 of those 7 were still non-conforming, because the test written to enforce the rule filtered on snapshot_kind alone and so encoded the same wrong denominator the finding had used.

**Evidence.**

- `profile/ftro-graph-profile-v0.0.3.md#51-p0-record-what-was-checked-before-composing-an-identity`
- `tests/test_retrieval_validation.py#TestComposedIdentityConformance`

**Impact.** A profile whose own reference manifest does not satisfy it is not a specification. This repeats FTRO-DEF-018's pattern. Worse, the first fix was self-confirming: the check inherited the error it was written to catch, so it passed while 2 of 7 records violated the rule. CLASSIFICATION (v2.0.0): reclassified schema -> execution. The fields were always expressible with existing vocabulary -- the fix added two ordinary JSON keys, no new node class or identity tier -- so by the card §17 test this is not a schema defect. It is the same shape as FTRO-DEF-027: the committed pipeline did not do what was claimed, and nothing checked.

**Workaround.** None; corrected in place.

**Proposed response.** Corrected across two rounds. 2026-08-25 (round 1): five snapshot-level identities gained both fields. 2026-08-25 (round 2): the denominator was corrected to seven, the two concept-level records gained the fields, and the test helper now selects on either identity level. Additional tests assert §10 identity ingredients, non-empty justifications and the §9.2 content_validated/resolvable coupling. Rule D-032 stands, strengthened by D-036: a check written to enforce a rule must not inherit the finding's own scoping assumptions.

---

### FTRO-DEF-030

**SELF-DIRECTED: the convention-sensitivity scan could not perform the reanalysis it reported**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO Phase-0 tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Testing whether the optical support figure is robust to its undeclared conventions.

**Known fact or required evidence.** analyse_optical.py's --gap-tolerance-s bounds the inter-sample spacing WITHIN one file's flag-in-{1,2} sequence. Probing a different tolerance therefore requires re-segmenting from the raw records.

**Observed.** The scan added in 0b41929 started from an inventory ALREADY segmented at 1.5 s and re-merged it, so (a) it could never SPLIT a run, making the 1.1 s row structurally identical to 1.5 s rather than found equal, and (b) it pooled runs across comparisons and .dat files, joining series that never overlapped and crediting support no measurement covered. All eight reported cells were wrong, always high. Correct values, from re-segmenting the records at each tolerance (the archive is parsed once and the 1,023,950 in-window records are cached; session 04 overstated this as 'all 9,018,290 records at each tolerance'): 1.1 s and 1.5 s give 133.111920 h optical / 82.013424 h optical-VLBI; 2.0 s gives 133.116888 / 82.016184; 5.0 s gives 133.567344 / 82.232760. Separately, four_domain_status_invariant_over_all_tested_variants was assigned the literal True rather than computed, in the same commit whose lab note said 'compute the sensitivity instead of asserting robustness'. And the 'nominal_1s_sample_credit' row extended each RUN end by 1 s rather than crediting each SAMPLE.

**Evidence.**

- `src/ftro/optical_sensitivity.py`
- `phase0/reports/four-domain-intersection.json#optical_support_sensitivity`

**Impact.** A robustness claim that no computation supported. The CONCLUSION survives and is now stronger: re-segmentation confirms no_common_support at every tolerance, and the status is computed per variant rather than asserted. Two substantive findings emerged that the broken scan concealed: 1.1 s equals 1.5 s because NO inter-sample spacing exists anywhere in that interval (ticks 13-22 of the exact tick distribution are empty, the next populated value being 23 ticks = 1.9872 s), which is a real property of the data -- though the boundary was first reported as 1.987199 s, a float artefact corrected in FTRO-DEF-036; and crediting each SAMPLE its nominal 1 s gives 130.684083 h, some 2.43 h BELOW the recorded-span basis, because the span basis silently fills sub-second holes inside runs. The committed note had asserted the credit correction could only ADD support.

**Workaround.** None; the scan is reimplemented in src/ftro/optical_sensitivity.py.

**Proposed response.** Corrected 2026-08-25. Rule adopted (D-037): a sensitivity probe must re-run the pipeline stage whose parameter it varies, never post-process that stage's output.

---

### FTRO-DEF-031

**SELF-DIRECTED: the committed test suite did not exercise the behaviour it was written to protect**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 4.0.0 |

**Failed step.** Regression-testing fail-closed retrieval on a clean clone.

**Known fact or required evidence.** A test that skips is not a test. FTRO-DEF-027 established that a claim must be traceable to committed, runnable code.

**Observed.** On a clean git archive export the suite reported 'OK (skipped=3)': all three fail-closed tests depended on gitignored data/raw/evidence/gps2utc.clk and skipped without it, so the fail-closed behaviour was never exercised. Neither pinner was tested end-to-end. The fixture tests/fixtures/genuine.sp3.Z was literal fake payload behind a 1f9d prefix that real uncompress rejects, and the validator checked only the first two bytes -- so 'content_validated' meant no more than 'non-empty, non-HTML, right first two bytes'. One test ignored the subprocess return code and could read a stale file from a fixed /tmp path. The README meanwhile described a regression test running 'against the live CDDIS URL' that does not exist as committed code. CORRECTION (v2.0.0): the first fix was incomplete. A clean export still reported 'OK (skipped=3)' -- the three provider-dependent tests remained skippable and no test invoked any pinner end-to-end, so session 04's claims 'nothing skips' and '26 tests passing on a clean clone' were false. The cold path was also unenforced: both expected-digest manifests lived in gitignored data/work/, the documented IGS command passed no manifest, and pin_ppta.py treated an absent expectation file as an empty map while still recording checksum_match. CORRECTION (v3.0.0): the second fix was ALSO incomplete. The 65 committed expectations were not enforced: pin_igs.py loaded the sectioned registry but looked names up at its root, so all 57 IGS artifacts pinned with expected_sha256 null while the report still read as enforced; pin_evidence_repos.py hard-coded the tintervals expectation as None even after its digest was committed, so the documented command rejected it and exited 1; pin_igs.py wrote to data/work/igs-pins.json while the intersection consumed the committed report; and the test named 'cover every pinned artifact' checked 4 of 65. CORRECTION (v4.0.0): the third fix was ALSO incomplete, and in a more dangerous way. pin_igs.py checked registry coverage only AFTER cache() and pin construction, so an uncovered expectation still cached all 57 files, emitted a snapshot with null expectation fields, and wrote the FAILED report to the official path -- which four_domain_intersection.py then consumed without checking n_failed, retrieval_validation, n_without_expected_digest or per-pin checksum state, producing normal GNSS support. pin_ppta.py accepted a missing individual expectation; pin_vgosdb.py succeeded with no expectation at all; pin_evidence_repos.py fell back to source-code literals when a registry key was missing.

**Evidence.**

- `tests/test_retrieval_validation.py`
- `src/ftro/unixz.py`
- `tests/fixtures/`

**Impact.** The suite created an appearance of enforcement without the substance, which is worse than no suite. Now: a pure-stdlib Unix-compress decoder verified byte-identical to system gzip on a real 253 KB IGS artifact; validate_content actually decompresses and checks inner format; fail-closed tests use local fixtures and temporary directories so nothing skips or reads stale state; 57 tests pass on a clean clone, with zero skips.

**Workaround.** None.

**Proposed response.** Corrected across four rounds. Round 4 (2026-08-26) introduces src/ftro/pinning.py, a shared contract with three rules: PREFLIGHT (registry coverage checked before any byte is fetched), ATOMIC PROMOTION (the report reaches the official path only on complete success; a failed run is preserved as .rejected and leaves the official path untouched), and NO EXPECTATION NO IDENTITY. All four pinners use it, and pinning.assert_report_usable() gates the scientific consumer. Verified: an uncovered expectation now fetches nothing, caches nothing and leaves the report unchanged; a failed report causes four_domain_intersection.py to exit non-zero.

---

### FTRO-DEF-032

**SELF-DIRECTED: four artifacts asserted evidence_state=resolvable under validation the profile forbids**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | pulsar |
| Dataset | `FTRO profile v0.0.1 and the PPTA leg` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Conforming to profile §9.2.

**Known fact or required evidence.** Profile §9.2: 'Only content_validated may support evidence_state = resolvable.'

**Observed.** The four PPTA artifacts carried retrieval_validation = status_and_checksum AND evidence_state = resolvable simultaneously, from 2c31279 through 0b41929. The contradiction was recorded in a note on each record rather than resolved, and no check tested the coupling.

**Evidence.**

- `phase0/reports/ppta-artifact-pins.json`
- `tests/test_retrieval_validation.py#test_resolvable_requires_content_validated`

**Impact.** An active conformance contradiction in the reference manifest, documented rather than fixed. Resolved by validating rather than downgrading: src/ftro/pin_ppta.py now checks each artifact against the inner format it claims (a PSRJ line for .par, a TEMPO2 FORMAT header for .tim, a comment header plus MJD rows for .clk), all four pass, and a test now asserts the coupling for every artifact.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-25. A recorded contradiction is not a resolved one; if a clause cannot be met, either meet it or change the clause.

---

### FTRO-DEF-033

**SELF-DIRECTED: version labels stopped identifying a constraint state**

| Field | Value |
| --- | --- |
| Class | `schema` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO profile and ledger version labels` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 4.0.0 |

**Failed step.** Declaring conformance 'to the FTRO profile v0.0.1' across three commits.

**Known fact or required evidence.** Task card §9.1 requires each manifest to declare conformance to the pinned base AND the FTRO profile BY VERSION. A version label must therefore identify a unique constraint state.

**Observed.** profile/ftro-graph-profile-v0.0.3.md is byte-distinct at fdbf2b9, 2c31279 and 0b41929 while remaining labelled v0.0.1, and gained normative clauses (§5.0, §5.1, §5.2, the §9.2 routes_tried requirement) between them. phase0/evidence/identities.json likewise stayed v0.1.0 across substantive changes. 'Conforms to v0.0.1' therefore names no particular set of constraints. CORRECTION (v2.0.0): the first fix bumped the profile only. phase0/evidence/identities.json -- named in this entry's own scope -- had four byte-distinct states at fdbf2b9, 2c31279, 0b41929 and 1b77a72 while remaining version 0.1.0 throughout, so the entry was marked resolved while half its own scope was untouched. CORRECTION (v3.0.0): D-039a extended the rule to every versioned artifact and the same commit then changed both ledgers without bumping decision-ledger v0.1.0 or source-ledger v0.2.0. The entry also still described the current profile as v0.0.2 after it had become v0.0.3. CORRECTION (v4.0.0): the gate built in round 3 could not perform the check it existed for. It stored set_at: 'HEAD' and never used it, comparing each document's declared version against a hard-coded copy of the same string -- so the two agreed by construction and a content change without a version bump passed. Working-tree changes produced only a non-failing note, and no test invoked the checker. The same commit demonstrated the miss: identities.json changed its vgosDB retrieval time and optical-validity-intervals.md changed its spacing evidence, both without a bump, and the latter was not even registered.

**Evidence.**

- `profile/ftro-graph-profile-v0.0.3.md`
- `phase0/evidence/identities.json`

**Impact.** Any conformance assertion made against a drifting label is unfalsifiable, which defeats the purpose of §9.1. Corrected: the profile is at v0.0.3 with a version-history table, every versioned artifact carries a version, and src/ftro/check_versions.py enforces the rule.

**Workaround.** Cite the commit hash alongside the version label until the profile freezes.

**Proposed response.** Corrected round 4 (2026-08-26): check_versions.py records a CONTENT DIGEST per artifact in phase0/evidence/versioned-artifacts.json, taken when the version was set, so any change without a bump is detectable. Twelve artifacts registered, --update re-records after a deliberate bump, and TestVersionGate asserts both failure modes -- content drift and an unrecorded bump -- against a copied tree.

---

### FTRO-DEF-034

**SELF-DIRECTED: the §9.2 conformance test exempted every record that omitted the field**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO test suite and profile §9.2` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Enforcing profile §9.2 against the reference manifest.

**Known fact or required evidence.** Profile §9.2: only content_validated may support evidence_state = resolvable. An absent value is not evidence of validation.

**Observed.** The test carried `rv is not None`, so a record omitting retrieval_validation was skipped rather than failed. All 11 manifest artifacts assert resolvable; only 5 declared content_validated and 6 omitted the field entirely. The test passed. This is the unsupported-null failure the project exists to catch, committed inside the check written to prevent it.

**Evidence.**

- `tests/test_retrieval_validation.py#test_resolvable_requires_content_validated`
- `phase0/evidence/identities.json`

**Impact.** A green suite certifying a manifest that did not satisfy the clause. Resolved by doing the work rather than widening the clause: the three git-hosted evidence artifacts are now retrieved and content-validated by src/ftro/pin_evidence_repos.py -- one of them, tintervals, previously asserted resolvable with NO checksummed file at all -- and the two concept-level records carry an explicit not_applicable, itself guarded by a test that refuses it for anything with a snapshot_id.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-25. Rule adopted (D-042): a conformance test must fail closed on a missing value; an exemption must be an explicit enumerated state, never an absence.

---

### FTRO-DEF-035

**SELF-DIRECTED: projection-only verification -- tests checked a hand-corrected manifest while its generators drifted**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO tooling and reference manifest` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 3.0.0 |

**Failed step.** Keeping the generated and curated views of an identity in agreement.

**Known fact or required evidence.** Task card §3: human and machine views share one source of truth. A generator and the manifest it feeds must therefore agree.

**Observed.** src/ftro/pin_ppta.py, added to close FTRO-DEF-032, emitted snapshot identities of the form ftro:snapshot:ppta/dr3/<name>@sha256:... while the canonical manifest used ftro:snapshot:ppta/dr3/<dir>/<name>@sha256:... -- all four differed. It emitted no concept_id and none of the profile §5.1 composition fields, so every identity it produced was non-conforming. DEF-029 was therefore closed only in the manually curated manifest, and no test compared the two views. CORRECTION (v2.0.0): the first fix reproduced the defect inside the fix. The reconciliation test read STORED reports rather than running the generators, skipped concepts absent from the manifest instead of failing, and compared a field only when both copies already carried it. Removing a snapshot_id, adding a rogue concept or deleting the generated §5.1 fields all left the suite green. All six end-to-end tests invoked only pin_vgosdb, whose generated identity itself lacked the profile-required retrieval_procedure. CORRECTION (v3.0.0): the round-2 reconciliation still tested stored projections. All subprocess pinner tests invoked only vgosDB; retrieved_utc equality was explicitly skipped, so 'not-a-timestamp' passed while seven of eight records already disagreed; composition fields were checked only if the REPORT identified itself as ftro_composed, so relabelling its own kind escaped §5.1; the digest test never asserted report.expected_sha256 == registry digest, so zeroing the registry while keeping checksum_match true passed; vgosDB enforcement was explicitly skipped; and a missing top-level retrieval_validation was permitted as None. A combined vgosDB mutation -- null expectation and checksum state, invalid retrieval time, changed snapshot kind, deleted §5.1 fields -- passed the entire 39-test suite.

**Evidence.**

- `src/ftro/pin_ppta.py`
- `tests/test_retrieval_validation.py#TestGeneratorManifestReconciliation`

**Impact.** The general form of four sessions of findings: assertions were verified against a projection that had been corrected by hand, while the machinery producing it was never reconciled. A passing suite meant only 'the curated copy is self-consistent'. Resolved: generators declare the canonical concept_id and snapshot stem explicitly, emit the §5.1 fields, and three reconciliation tests assert generator output equals the manifest for every pinned artifact -- plus a test that a FRESHLY generated identity is §5.1-conforming, not only the stored one.

**Workaround.** None.

**Proposed response.** Corrected round 3 (2026-08-26). Every enumerated fail-open branch is closed: retrieved_utc must parse as ISO-8601 on both sides; snapshot_kind must AGREE with the manifest before §5.1 is evaluated; every pin's expected_sha256 must EQUAL the registry digest, vgosDB included; a committed report must declare content_validated with no failures and no uncovered expectations. The manual mutation table is now twelve committed tests in TestMutationsAreDetected, each copying the committed views into a temporary tree, mutating one, and asserting the suite rejects it -- including the exact combined vgosDB mutation that previously passed. 57 tests, zero skips.

---

### FTRO-DEF-036

**SELF-DIRECTED: the spacing analysis differenced binary floats and invented a distinct spacing**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | optical |
| Dataset | `FTRO Phase-0 tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 2.0.0 |

**Failed step.** Characterising the inter-sample spacing distribution of the optical archive.

**Known fact or required evidence.** Every MJD token in the archive is an exact multiple of 1e-6 d, so spacings are exact integer multiples of one 86.4 ms tick and can be computed without rounding.

**Observed.** analyse_optical.py computed spacings as round((b - a) * 86400, 6) over binary floats, from session 01 through 11ea11c. That split the single physical 23-tick spacing into two apparent values, 1.9872 (6,235 occurrences) and 1.987199 (528), and inflated the distinct-spacing count from 1,161 to 1,237. The exhaustive evidence key added in session 05 then reported 1.987199 as the next spacing above 1.0368 s -- an artefact, not a measurement. Its n_strictly_between was also tautologically zero, because the upper endpoint was defined as the next observed value. CORRECTION (v2.0.0): the census was made exact but contiguous_runs() still compared binary-float MJD differences against a float tolerance. At an exact 1.9872 s tolerance, 231 of the 259 in-window 23-tick gaps evaluated above the threshold and 28 below -- a segmentation boundary decided by representation error. The published tolerances all sit far from any populated boundary, so no published figure changes. The generated evidence also retained an obsolete 'float-representation twin' note contradicting its own exact representation.

**Evidence.**

- `src/ftro/analyse_optical.py`
- `phase0/reports/optical-inventory-summary.json#sample_spacing_exhaustive`

**Impact.** The finding survives and is now exact: the two dominant spacings are 11 and 12 ticks, ticks 13-22 are EMPTY (0 of 9,018,038 pairs), and the next populated value is 23 ticks = 1.9872 s exactly, 6,763 times. So any gap tolerance strictly between 12 and 23 ticks segments identically, which is why 1.1 s and 1.5 s agree. The 1.1/1.5 equality and the four-domain null are unaffected. But a float artefact had been promoted into a published evidence key, and the non-tautological form of the claim -- an EMPTY BAND, not 'nothing before the next value' -- was only visible once the arithmetic was exact.

**Workaround.** None.

**Proposed response.** Corrected round 2 (2026-08-26): contiguous_runs() operates on integer microday ticks with the tolerance converted once by flooring, so segmentation is exact integer arithmetic. The obsolete note is replaced by the empty-band statement. The four-domain result is unchanged at 82.0134 h optical-VLBI and no_common_support.

---

### FTRO-DEF-037

**SELF-DIRECTED: a contract change updated one caller of two, and the report published a wrong number**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO Phase-0 tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Keeping the sensitivity scan consistent with the segmentation it probes.

**Known fact or required evidence.** analyse_optical.contiguous_runs() was changed to take integer microday ticks rather than float MJDs (FTRO-DEF-036 v2.0.0).

**Observed.** Only one of its two callers was updated. optical_sensitivity.Resegmenter continued to pass float MJDs and to convert the returned values as MJDs. With MJD-scale differences compared against a tick-scale tolerance, no gap test could ever be true: every tolerance collapsed to 34 runs -- one per file -- and the committed report published 171.442704 h optical and 117.995208 h optical-VLBI, against the 133.111920 h and 82.013424 h its own main computation produced from the same convention. The report therefore contradicted the selection note, and all 57 committed tests passed.

**Evidence.**

- `src/ftro/optical_sensitivity.py`
- `phase0/reports/four-domain-intersection.json#optical_support_sensitivity`
- `tests/test_retrieval_validation.py#TestSensitivityAgreesWithMainComputation`

**Impact.** A wrong number in a published report, reachable by any reader, surviving every gate. The four-domain null was unaffected -- no_common_support holds under both the broken and the corrected scan -- but the sensitivity table, whose entire purpose is to show the null is convention-independent, was itself wrong. The missing invariant is obvious in hindsight: the scan's shipped-tolerance row and the main computation share a convention, so they must agree, and nothing compared them.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26: the adapter passes ticks. Corrected values reproduce 7,398/7,398/7,139/4,826 runs at 1.1/1.5/2.0/5.0 s. Three tests added: the shipped-tolerance row must equal the main computation, run counts must not be degenerate across tolerances, and the invariance flag must be computed. Rule adopted (D-054): changing a function's contract requires enumerating its callers, and any two computations sharing a convention must be asserted equal.

---

### FTRO-DEF-038

**SELF-DIRECTED: the consumer gate and its tests both equated an absent field with success**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO consumer gate and test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Refusing to derive science from a report that is not a clean success.

**Known fact or required evidence.** Absence is not evidence of success -- the principle already recorded in FTRO-DEF-034 for retrieval_validation.

**Observed.** pinning.assert_report_usable() tested `doc.get(field)` for truthiness, so a report OMITTING retrieval_validation, n_failed or n_without_expected_digest was accepted. Each was removed independently and all three passed. The committed tests carried the same defect via assertFalse(doc.get(...)), so removing both counters from the IGS report left all 57 tests green. The same fail-open pattern, in the gate written to fix the previous one.

**Evidence.**

- `src/ftro/pinning.py#REQUIRED_REPORT_STATE`
- `tests/test_retrieval_validation.py#TestConsumerGate`

**Impact.** A report could reach the scientific path by declaring less rather than more. Fixed by requiring each field to be PRESENT, of the correct type, and to hold a permitted value, and by mutation-testing the production consumer itself rather than only the helper. Single-pin reports now declare the same state as list reports, so no consumer needs a per-shape special case and absence is never ambiguous.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-055): a conformance predicate names its required fields explicitly with types and permitted values; `.get()` truthiness is never a conformance test.

---

### FTRO-DEF-039

**SELF-DIRECTED: --update could legalise an unbumped content change**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Preventing content drift from passing the version gate.

**Known fact or required evidence.** D-051: the version gate compares content digests so unbumped drift is detectable.

**Observed.** check_versions.py --update replaced both the recorded version and the recorded digest unconditionally, including for artifacts the audit had just flagged as same-version drift. In a clean export: --check exited 1, --update exited 0, and --check then passed with the version unchanged. The gate could be silenced by the command documented for maintaining it.

**Evidence.**

- `src/ftro/check_versions.py`
- `tests/test_retrieval_validation.py#test_update_refuses_to_launder_an_unbumped_change`

**Impact.** Any drift could be made invisible in one command. --update now REFUSES when content changed under an unchanged version, and initial registration is a separate explicit --register path rather than a side effect.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-056): the command that maintains a gate must not be able to satisfy it.

---

### FTRO-DEF-040

**SELF-DIRECTED: 'every versioned artifact' was a manual list with no completeness check**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO versioned-artifact registry` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Applying D-039a, which binds every versioned artifact.

**Known fact or required evidence.** A rule quantified over 'every X' needs a way to enumerate X.

**Observed.** The registry was a hand-written twelve-file list. All three ApplicabilityAssessments declare version 1.0.0 and none was registered, so changing one without a bump returned success. Nothing detected the omission because nothing enumerated the population the rule quantifies over.

**Evidence.**

- `src/ftro/check_versions.py#discover_versioned`
- `phase0/evidence/versioned-artifacts.json`

**Impact.** The version rule silently applied to a subset. check_versions.py now DISCOVERS every document under phase0/, ledgers/, profile/ and charter/ that declares a version, and fails if one is neither registered nor listed in an explicit EXCLUSIONS map with a stated reason. Fourteen artifacts are tracked; four generated or externally-versioned documents are excluded on the record. A test asserts a newly added versioned document is detected.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-057): a rule quantified over 'every X' requires an executable enumeration of X and an explicit, stated exclusion policy.

---

### FTRO-DEF-041

**SELF-DIRECTED: a transport failure produced a traceback instead of a rejected report**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | vlbi |
| Dataset | `FTRO retrieval tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Applying the shared retrieval contract to a failed retrieval.

**Known fact or required evidence.** D-049: a report reaches its official path only on complete success, and a failure is preserved as .rejected.

**Observed.** pin_vgosdb.py's urlopen() sat outside any failure-handling path. A preflight-covered but nonexistent file:// URL exited 1 with an unhandled traceback and produced NEITHER the official report NOR a .rejected one -- so a transport failure left no evidence at all, contrary to the contract every other failure mode obeyed. The subprocess suite exercised only content and digest outcomes, never transport.

**Evidence.**

- `src/ftro/pin_vgosdb.py`
- `tests/test_retrieval_validation.py#test_transport_failure_is_preserved_as_rejected`

**Impact.** The one failure mode most likely in practice -- the network -- was the one that left no record. Now caught and promoted as a rejected report with retrieval_validation = content_rejected and a stated reason, with a test asserting no traceback reaches the operator.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-058): every failure mode a contract names must have a test, transport included.

---

### FTRO-DEF-042

**SELF-DIRECTED: preflight checked key membership, so a null digest passed as an expectation**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO retrieval tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Refusing to fetch without a well-formed expected digest.

**Known fact or required evidence.** An expectation is a 64-character hex digest. None, an empty string or a truncated value is not one.

**Observed.** pinning.preflight() tested only `n not in expected`. With {"vgosdb_min.tgz": null} the vgosDB pinner exited 0, cached bytes, promoted the official report and minted an identity carrying expected_sha256: null. pin_vgosdb and pin_ppta additionally treated checksum_match is None as success, so 'not checked' read as 'verified'. IGS and the evidence pinner rejected the same case, but only AFTER fetching -- which is not preflight.

**Evidence.**

- `src/ftro/pinning.py#valid_digest`
- `tests/test_retrieval_validation.py#TestPreflightDigestValidation`

**Impact.** The preflight boundary could be crossed by a registry entry that was present but meaningless, and the resulting identity recorded a null expectation as though verified. Every expectation is now validated as 64 lowercase hex before any retrieval, a malformed entry is fatal even under --allow-unpinned, and an unchecked digest counts as verified only when --allow-unpinned was explicitly passed.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-059): validate the SHAPE of a precondition, not its presence.

---

### FTRO-DEF-043

**SELF-DIRECTED: the consumer gate accepted JSON false as integer zero and ignored per-pin state**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO consumer gate` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Refusing to derive science from a report that is not a clean success.

**Known fact or required evidence.** In Python bool is a subclass of int, so isinstance(False, int) is True.

**Observed.** assert_report_usable() type-checked counters with isinstance(value, int), so n_failed: false was accepted as zero. It also accepted a per-pin retrieval_validation of content_rejected, an absent or contradictory per-pin sha256, and n_pinned: 56 on a report carrying 57 pins.

**Evidence.**

- `src/ftro/pinning.py#assert_report_usable`
- `tests/test_retrieval_validation.py#TestConsumerGate`

**Impact.** A report could pass the gate by declaring false where zero was required, or by contradicting itself internally. The gate now rejects bool for integer fields, requires n_pinned to equal the number of pins, requires both digests to be well formed and mutually consistent, and rejects a per-pin validation state that contradicts the report-level one.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-060): in Python, an int check must exclude bool explicitly.

---

### FTRO-DEF-044

**SELF-DIRECTED: --register was an escape hatch that also could not register anything**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Adding a newly discovered versioned artifact to the registry.

**Known fact or required evidence.** D-056: the command that maintains a gate must not be able to satisfy it.

**Observed.** --register only disabled the same-version laundering refusal, so check 1 -> update --register 0 -> check 0 made drift invisible. And because the update loop iterated only EXISTING registry entries, --register could not add a newly discovered document: it exited 0 while the next check still failed. Ordinary --update also accepted a version downgrade.

**Evidence.**

- `src/ftro/check_versions.py`
- `tests/test_retrieval_validation.py#TestRegisterSemantics`

**Impact.** The maintenance command both weakened the gate and failed at its stated purpose. --register now adds only newly discovered artifacts, neither flag can bypass the same-version refusal, and a version that moves backwards is refused.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-061): a maintenance flag adds capability, never removes a check.

---

### FTRO-DEF-045

**SELF-DIRECTED: discovery covered four directories, and excluded generated files had no compensating check**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO version gate and generated documents` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Applying the version rule to every versioned artifact.

**Known fact or required evidence.** D-057: a rule quantified over 'every X' requires an executable enumeration of X.

**Observed.** discover_versioned() walked only phase0/, ledgers/, profile/ and charter/ for .md and .json, so root codemeta.json could change under an unchanged version unnoticed. Separately, generated documents were excluded from version tracking with no freshness check: editing the optical summary and regenerating produced a byte-different v0.2.0 document while the version check, the crate check and all 70 tests passed.

**Evidence.**

- `src/ftro/check_versions.py#discover_versioned`
- `tests/test_retrieval_validation.py#TestGeneratedFileFreshness`

**Impact.** The enumeration added in the previous round was itself incomplete, and an exclusion had been granted without a compensating control. Discovery now walks the whole repository with an explicit skip list, and a test asserts that every file excluded as 'generated' has a freshness check that regenerates and compares it.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-062): excluding a file from one gate obliges covering it with another.

---

### FTRO-DEF-046

**SELF-DIRECTED: the tests guarding the sensitivity computation only read its output**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Protecting the segmentation computation against regression.

**Known fact or required evidence.** FTRO-DEF-037 was a source regression: a contract change applied to one caller of two.

**Observed.** The tests added to prevent recurrence read only the committed JSON. Restoring the broken 615afe2 revision of optical_sensitivity.py, or making Resegmenter.runs() raise, left all 70 tests green -- they protected coherence after manual regeneration, not the code. The test named 'invariant and computed' also trusted two summary fields, so changing a variant row to overlap passed while the summaries stayed untouched.

**Evidence.**

- `tests/fixtures/mini-archive/`
- `tests/test_retrieval_validation.py#TestSegmentationOracle`

**Impact.** A regression test that cannot fail on the regression it names. Now: a synthetic archive of known construction (one comparison with a 23-tick gap, one with 23, 40 and 60) whose expected run counts are derived from tick arithmetic and cross-checked against a recorded manifest; both the in-process and subprocess segmentation paths are executed against it; and the two are asserted equal run-for-run, which is the redundancy check that would have caught FTRO-DEF-037 with no committed report in existence. Invariance is recomputed from every variant row rather than read from a summary. Verified: reintroducing the 615afe2 bug fails 9 tests; injecting an exception into runs() errors 9.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-063): a regression test must execute the code path, not read its committed output.

---

### FTRO-DEF-047

**SELF-DIRECTED: a mutation test asserted only a non-zero exit, which the unmutated run also produces**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Verifying that the production consumer rejects a malformed report.

**Known fact or required evidence.** A mutation test must distinguish the mutation's effect from every other cause of failure.

**Observed.** test_production_consumer_rejects_a_stripped_report asserted only assertNotEqual(returncode, 0). On a clean archive the unmodified consumer already exits 1 because the raw optical data are absent, so a change that bypassed the gate entirely would still have passed.

**Evidence.**

- `tests/test_retrieval_validation.py`

**Impact.** A self-confirming test: it would have passed with the gate removed. It now asserts the specific diagnostic -- 'is not a clean success' and the named absent field -- so only the intended rejection satisfies it.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-064): assert the specific diagnostic, never a bare non-zero exit.

---

### FTRO-DEF-048

**SELF-DIRECTED: the segmentation oracle validated topology, not extent**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Guarding the segmentation computation against regression.

**Known fact or required evidence.** An oracle must be independent of the code it checks, and must constrain the QUANTITY the downstream result depends on -- here run extent, not merely run count.

**Observed.** Both routes the oracle called 'independent' -- Resegmenter.runs() and subprocess_runs() -- invoke the same analyse_optical.contiguous_runs(). The external manifest recorded four run COUNTS only. Halving every run's span while preserving topology therefore changed optical support from 133.1119 h to 81.6907 h and optical-VLBI from 82.0134 h to 52.194 h, left all four run counts identical, and passed all 86 tests. The variant test separately accepted a renamed 5.0 row and four_domain_n_intervals: 1.

**Evidence.**

- `tests/test_retrieval_validation.py#independent_runs`
- `tests/fixtures/mini-archive/expected-runs.json`

**Impact.** The oracle could detect a broken ADAPTER -- the defect it was written for -- and nothing else. Now: an independent segmenter written from the specification in the test file, a manifest of full run TUPLES (comparison, file, tick_start, tick_end, n_samples) plus total spans, and assertions that the production segmenter, both sensitivity routes and the manifest all agree tuple for tuple. Variant keys are asserted explicitly so a renamed row cannot drop a variant. Verified: the span-halving mutation now fails 12 tests.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-066): an oracle must constrain extent, not only topology, and must not call the implementation it checks.

---

### FTRO-DEF-049

**SELF-DIRECTED: generated-file version enforcement did not exist**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Ensuring a changed generated document receives a new version.

**Known fact or required evidence.** D-062: excluding a file from one gate obliges covering it with another.

**Observed.** The compensating control added last round was a FRESHNESS check: it proves output matches current input, not that changed output was re-versioned. Editing the optical summary and regenerating produced different content still declaring v0.2.0, and the version check, crate check and all tests passed -- exactly the scenario FTRO-DEF-045 claimed to have fixed. The test also rendered into the tracked checkout, so a stale file was overwritten by the first failing run and the second run passed.

**Evidence.**

- `src/ftro/check_versions.py`
- `tests/test_retrieval_validation.py`

**Impact.** A control that measured the wrong property, and a test that repaired the condition it was meant to detect. Generated documents now have their CONTENT registered under __generated__ with their declared version; a content change under an unchanged version fails --check and is refused by --update. The freshness test renders into a copied tree.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-067): a compensating control must measure the property the original gate measured, and a test must never repair the state it inspects.

---

### FTRO-DEF-050

**SELF-DIRECTED: the consumer permitted absent per-pin state and incoherent counters**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO consumer gate` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Refusing a report that is not a clean success.

**Known fact or required evidence.** Profile 9.2 requires retrieval_validation on EVERY record, pins included.

**Observed.** assert_report_usable() explicitly permitted a pin with no retrieval_validation -- the FTRO-DEF-034 failure one level down, in the gate written after it. n_pinned could be absent entirely; 57.0 satisfied a 57-pin report because float equals int, and true satisfied a single-pin report because True equals 1. A non-empty failures or uncovered_by_registry list could coexist with a zero counter. None of the branches added for FTRO-DEF-043 was exercised by a test.

**Evidence.**

- `src/ftro/pinning.py`
- `tests/test_retrieval_validation.py`

**Impact.** The gate could be satisfied by a report that contradicted itself. Per-pin retrieval_validation is now required; n_pinned must be present and a true int matching the pin count; every failure list must agree with its counter. Each branch has a mutation test.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-068): every branch of a conformance predicate needs its own mutation test, or it is untested code.

---

### FTRO-DEF-051

**SELF-DIRECTED: an explicit digest bypassed preflight, and a trailing newline validated**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO retrieval tooling` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Validating a precondition before any retrieval.

**Known fact or required evidence.** D-059: validate the shape of a precondition, not its presence.

**Observed.** pin_vgosdb validated only registry-derived expectations, so --expect-sha256 abc fetched and parsed the archive before rejecting it -- the explicit argument was not a precondition at all. Separately valid_digest() used re.match with a trailing dollar anchor, which in Python also accepts a trailing newline, so a digest read from a file with its newline intact validated and the consumer accepted a report whose actual and expected digests both carried the suffix.

**Evidence.**

- `src/ftro/pin_vgosdb.py`
- `src/ftro/pinning.py`

**Impact.** A precondition enforced on one input path and not the other is not a precondition. The explicit argument is now validated before the request is constructed, and valid_digest uses fullmatch.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-069): validate every input path to a precondition, and prefer fullmatch to match with an anchor.

---

### FTRO-DEF-052

**SELF-DIRECTED: the discovery suffix list advertised formats the pattern could not parse**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Discovering every versioned document.

**Known fact or required evidence.** D-057: a rule over 'every X' requires an executable enumeration of X.

**Observed.** TRACKED_SUFFIXES listed .yaml, .yml and .cff while VERSION_RE matched only Markdown and JSON syntax. A phase0/rogue.yml declaring version 1.0.0 produced check 0, register 0 new, check 0 -- the completeness claim covered file types the scanner could not read.

**Evidence.**

- `src/ftro/check_versions.py`

**Impact.** The enumeration silently under-covered the population it claimed. The pattern now parses YAML and CFF version declarations as well, and a test asserts a versioned YAML file is discovered and registrable.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-070): a capability list is a claim; it needs a test per entry.

---

### FTRO-DEF-053

**SELF-DIRECTED: the oracle fixture contained no gap at a scientifically active tolerance boundary**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Constraining the segmentation threshold against off-by-one error.

**Known fact or required evidence.** 5.0 s floors to 57 ticks and rounds to 58, and the real archive contains 3,143 gaps of exactly 58 ticks.

**Observed.** The mini-archive had no 58-tick gap, so replacing int() with round() in contiguous_runs() left all 94 tests green while changing the published 5 s sensitivity row: runs 4,826 -> 2,943, optical 133.567344 -> 134.533680 h, optical-VLBI 82.232760 -> 82.536504 h. The regenerated report passed the tests, the version gate and the crate gate.

**Evidence.**

- `tests/fixtures/mini-archive/EEE_b-FFF_b/`
- `tests/test_retrieval_validation.py`

**Impact.** An oracle can only constrain behaviour its fixture exercises. The fixture now embeds gaps at each tolerance's floored threshold T and at T+1 (12/13, 17/18, 23/24, 57/58), with tests asserting that a T gap merges and a T+1 gap splits at every tolerance. Verified: int->round now fails 6 tests, and a > to >= flip fails 12.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-071): a fixture must exercise every threshold the production code branches on, at the boundary and one beyond it.

---

### FTRO-DEF-054

**SELF-DIRECTED: the runtime consumer verified a report's self-description, not its completeness**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | gnss |
| Dataset | `FTRO consumer gate` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Refusing an incomplete or fabricated report before deriving science from it.

**Known fact or required evidence.** A report can be internally consistent and still be neither complete nor truthful.

**Observed.** assert_report_usable() consulted nothing external. Truncating the IGS report from 57 pins to one and setting n_pinned: 1 was accepted; so was rewriting a pin's actual AND expected digest to the same fabricated value. four_domain_intersection.py then consumed those pins directly. The stored-report test did check registry equality, but the documented workflow runs the tests BEFORE retrieval, so it does not protect a run.

**Evidence.**

- `src/ftro/pinning.py`
- `src/ftro/four_domain_intersection.py`

**Impact.** The gate is now bound to the expected-digest registry: it rejects pins missing from the registry, pins unknown to it, duplicate pins, and any pin whose digest disagrees with the registry value. Both accepted mutations now exit 1.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-072): a runtime gate must compare against an external expectation, not the artifact's own account of itself.

---

### FTRO-DEF-055

**SELF-DIRECTED: generated-version enforcement had two laundering paths**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Requiring a version advance for changed generated content.

**Known fact or required evidence.** D-067: a compensating control must measure the property the original gate measured.

**Observed.** The generated check rejected changed content only when the declared version EQUALLED the recorded version, and --register disabled the refusal outright. Verified: same version gave check 1 -> register 0 -> check 0 with all 94 tests passing; a v0.2.0 to v0.1.0 downgrade passed check, update and every test; and removing the version entirely let --update record version: null.

**Evidence.**

- `src/ftro/check_versions.py`

**Impact.** Generated entries now run the same state machine as tracked ones: a version is required and must be valid, the registry must agree exactly during --check, updates are permitted only on a strict forward change, and --register may only ADD a missing entry. All three laundering paths now end in exit 1.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-073): a special-cased class of artifact must obey the general state machine, not a weakened copy of it.

---

### FTRO-DEF-056

**SELF-DIRECTED: container-shape checks ran only when the container was already the right type**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO consumer gate` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Validating the structure of a pin report.

**Known fact or required evidence.** A coherence check guarded by isinstance() is skipped, not failed, when the type is wrong.

**Observed.** The failure/uncovered coherence check ran only when each field was ALREADY a list, so failures: {} and uncovered_by_registry: "ghost" both passed, and adding pins: {} to a valid single-pin report was ignored. The tests exercised non-empty valid lists only.

**Evidence.**

- `src/ftro/pinning.py`
- `tests/test_retrieval_validation.py`

**Impact.** Shape is now required explicitly: pins must be a list when present, every entry must be an object, and each count-associated field must be present and a list of the correct type. Six container-shape mutations are tested.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-074): validate the type before the invariant; a guard that skips on the wrong type is a fail-open branch.

---

### FTRO-DEF-057

**SELF-DIRECTED: the 'nothing was fetched' test measured 'nothing was cached'**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO test suite` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Proving that a preflight failure issues no request.

**Known fact or required evidence.** Bytes are not cached until verification, so an empty cache does not imply no retrieval.

**Observed.** The test observed the diagnostic and the cache directory. Moving retrieval ABOVE the preflight error, while keeping the same message and leaving the cache empty, passed all 94 tests. Production ordering was correct, but nothing enforced it.

**Evidence.**

- `tests/test_retrieval_validation.py`

**Impact.** The test now spies on urllib.request.urlopen and asserts zero calls, so the ordering itself is enforced. Verified: injecting a fetch before the preflight now fails. The production-consumer mutation test was also still writing into the tracked checkout, contrary to D-067; it now runs in a copied tree and asserts the tracked report is untouched.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-075): assert the action you mean to forbid, not a side effect that usually accompanies it.

---

### FTRO-DEF-058

**SELF-DIRECTED: pin_igs could promote a report its own consumer rejects**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | gnss |
| Dataset | `FTRO retrieval tooling` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Producing a report that satisfies the consumer contract.

**Known fact or required evidence.** A producer and its consumer must agree on the report contract.

**Observed.** --series accepted duplicates, so `--series igs igr igs` exited 0 and promoted 79 pins of which only 57 were unique -- a report the consumer's duplicate check rejects. The duplicate mutation test was self-confirming: after appending pin 58 it set n_pinned=59, so the count mismatch fired before duplicate detection.

**Evidence.**

- `src/ftro/pin_igs.py`
- `src/ftro/schema.py`

**Impact.** Series are deduped, and promote() now validates the SAME declared schema the consumer applies, so a producer cannot emit something its consumer rejects. That class of mismatch is now impossible by construction rather than caught by review.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26 by consolidation. Rule adopted (D-076): producer and consumer validate one declaration; the producer validates before promotion.

---

### FTRO-DEF-059

**SELF-DIRECTED: the committed vgosDB report was rejected by the shared consumer gate**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | vlbi |
| Dataset | `FTRO retrieval tooling` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `blocks_workflow` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Emitting a report that satisfies the shared contract.

**Known fact or required evidence.** Every committed report must pass the gate every consumer applies.

**Observed.** pin_vgosdb emitted the counters n_failed and n_without_expected_digest but not the failures and uncovered_by_registry lists they count, so the committed report failed the gate introduced one commit earlier. A producer/consumer mismatch shipped in the repository.

**Evidence.**

- `src/ftro/pin_vgosdb.py`
- `src/ftro/schema.py`

**Impact.** The pinner emits both lists; all four committed reports now satisfy the shared schema, and promotion enforces it.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26 by consolidation.

---

### FTRO-DEF-060

**SELF-DIRECTED: scientific meaning was read from unauthenticated report fields**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | gnss |
| Dataset | `FTRO analysis path` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `changes_result` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Binding the meaning of an authenticated artifact, not only its bytes.

**Known fact or required evidence.** The registry binds a pin by name and digest; anything else in the record is unbound.

**Observed.** four_domain_intersection derived GNSS support from report-supplied `series` and `mjd`. Relabelling all 57 pins as `igr`, without changing a name or a digest, passed every gate and all 99 tests while changing GNSS support from 240 h to 0 h and without_pulsar from 82.0134 h to 0.

**Evidence.**

- `src/ftro/four_domain_intersection.py`

**Impact.** series and mjd are now DERIVED from the filename, which the registry binds by digest. A field that is not stored cannot be forged; the relabel mutation now has no effect at all.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-077): derive semantics from authenticated names rather than binding more fields.

---

### FTRO-DEF-061

**SELF-DIRECTED: main and sensitivity computations carried duplicate domain constants**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO analysis path` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `changes_result` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Keeping the main computation and its sensitivity scan consistent.

**Known fact or required evidence.** Two computations of the same quantity must have one source.

**Observed.** The pulsar observation constants were duplicated across four_domain_intersection and optical_sensitivity. Changing only the main start produced a main `overlap` with 13 intervals and 1.0559 h while every embedded sensitivity row still read no_common_support, with all 99 tests and both gates green.

**Evidence.**

- `src/ftro/optical_sensitivity.py`
- `src/ftro/four_domain_intersection.py`

**Impact.** Domain supports are built once and passed in; build_sensitivity now RAISES if a caller omits them. Every domain, pair, triple, four-way result and gap is reconciled at the shipped convention, and the run fails on disagreement. The duplication is removed rather than policed.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-078): remove the duplication rather than reconciling it, where the architecture permits.

---

### FTRO-DEF-062

**SELF-DIRECTED: a credit function assumed sorted input its caller happened to provide**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | optical |
| Dataset | `FTRO analysis path` |
| Disposition | `resolved` |
| Finding type | `latent_regression` |
| Affects | `no_present_effect` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Owning a function's preconditions.

**Known fact or required evidence.** A precondition that lives in the caller is not a precondition.

**Observed.** per_sample_nominal_credit assumed sorted input while window_stamps_us happened to sort. Removing that one sort passed all tests while changing optical credit from 130.684083 h to 15.488280 h and optical-VLBI from 80.450043 h to 10.008253 h.

**Evidence.**

- `src/ftro/optical_sensitivity.py`

**Impact.** The function sorts its own input. Removing the caller's sort now has no effect.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. Rule adopted (D-079): a function owns its preconditions.

---

### FTRO-DEF-063

**SELF-DIRECTED: the review protocol had no terminating condition**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | high |
| Domain | cross-domain |
| Dataset | `FTRO process` |
| Disposition | `resolved` |
| Finding type | `assurance_gap` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Determining when Phase 0 is complete.

**Known fact or required evidence.** An acceptance condition must be finite and stated before it is tested.

**Observed.** Ten rounds produced 33 self-directed findings with a flat discovery rate. Three causes: a verifier regress with no declared trusted base (73% of code was verification); five distinct finding types entering one ledger with equal weight; and an append-only count that can only rise, so totals could not show convergence. 'Proper functionality' was never bounded, so each round searched further outward with no zero-findings outcome available.

**Evidence.**

- `phase0/acceptance-contract-v1.0.md`
- `phase0/audit-fault-model-v1.0.md`

**Impact.** Phase 0 now has a frozen 12-contract scope, a stated trusted computing base, a finite exit condition, a pre-registered fault model executed once, and a convergence measure that can reach zero: open entries bearing on the result that are software defects rather than external evidence gaps. That measure now reads ZERO. The trusted base was shrunk by deleting the 275-line version state machine in favour of git, and the eight-entry absent-field family was retired by one declarative schema.

**Workaround.** None.

**Proposed response.** Adopted 2026-08-26. Rule (D-080): freeze the acceptance scope and pre-register the audit before the next fix round.

---

### FTRO-DEF-064

**SELF-DIRECTED: the git-based version gate crashed on a document that gains a version**

| Field | Value |
| --- | --- |
| Class | `execution` |
| Severity | medium |
| Domain | cross-domain |
| Dataset | `FTRO version gate` |
| Disposition | `resolved` |
| Finding type | `current_defect` |
| Affects | `maintenance_only` |
| Responsible party | `ftro` — **self-directed** |
| Version | 1.0.0 |

**Failed step.** Running check_versions.py --check --base HEAD~1 after the consolidation commit.

**Known fact or required evidence.** A previously unversioned document that gains a version has no prior version to advance from.

**Observed.** The rewritten gate handled content-change, downgrade and removal but fell through to the ordering comparison when the previous version was absent, raising AttributeError on None.split(). Found by running the gate against HEAD~1 immediately after committing it -- the fault model's M12 covered only the three cases I had thought of.

**Evidence.**

- `src/ftro/check_versions.py`
- `phase0/audit-fault-model-v1.0.md`

**Impact.** A maintenance command crashed rather than reporting. No committed artifact was affected. Notable as the first finding located by our own pre-registered process rather than by review, and as the first exercise of the amend-then-rerun rule: the fault model is now v1.1.0 with M12a-M12c enumerated.

**Workaround.** None.

**Proposed response.** Corrected 2026-08-26. The gate accepts a gained version and a test covers it. Rule reinforced: enumerate a state machine's transitions, not the cases that come to mind.

---
