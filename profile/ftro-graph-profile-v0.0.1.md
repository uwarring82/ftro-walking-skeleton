# FTRO Reference-Ancestry Graph Profile v0.0.1

**Document ID:** FTRO-PRF-001 · **Version:** 0.0.1 · **Date:** 2026-08-25
**Status:** Draft — **no term is frozen** (task card Gate 1) · **Licence:** CC BY 4.0
**Normative base:** [RO-Crate Metadata Specification 1.3](https://w3id.org/ro/crate/1.3)

> **Freeze status.** Task card §21 Gate 1: *"no FTRO term is frozen."* Every term below
> is provisional and will be reviewed at Phase 6 against the full deficiency ledger.
> Terms marked **[P0]** were added or changed because Phase-0 evidence demanded it.

---

## 1. Conformance

A conforming manifest declares conformance to **both**:

1. the pinned base, RO-Crate Metadata Specification 1.3 (Recommendation, 2026-06-22); and
2. this profile, by version.

"RO-Crate-compatible" means the crate **validates against the pinned base** and
satisfies this profile's constraints. Similar JSON-LD conventions are insufficient.

**The validator and its version must be recorded in every conformance report.** An
RO-Crate 1.2 export may be produced for tool-compatibility testing; it is not a second
normative base.

A schema limitation encountered while expressing a term is **logged**, not concealed.

## 2. Node classes

| Group | Classes |
| --- | --- |
| Identity & granularity | `SeriesConcept`, `ImmutableSnapshot`, `Collection`, `Release`, `Dataset`, `File`, `Segment`, `Record`, `Observation` |
| Instrumentation & time | `Station`, `Instrument`, `Oscillator`, `Clock`, `TimeScaleRealisation` |
| Transfer & correction | `TransferLink`, `Comparison`, `CalibrationArtifact`, `CorrectionArtifact` |
| Models & frames | `Ephemeris`, `EarthOrientationSeries`, `TideLoadingModel`, `ReferenceFrame`, `CoordinateConvention` |
| Context | `ContextualSensorSeries` |
| Execution | `Software`, `Configuration`, `Model`, `Template`, `Workflow`, `EnvironmentLock`, `Execution` |
| Epistemic | `Publication`, `EvidenceArtifact`, `Assertion`, `VerificationActivity`, `ApplicabilityAssessment`, `Contestation` |
| Governance | `Policy`, `ResolverExecution`, `AlignmentCertificate`, `DeficiencyEntry` |

**Graph roots need not be UTC(k).** A chain may legitimately terminate at a free-running
local oscillator, a direct optical ratio, a proper-time model, an institutional
assertion, or an unresolved or opaque dependency.

**Evidence artifacts have ancestry too.** Phase 0 confirmed this concretely: `pks2gps.clk`
is a merge of three sources across different eras, described only narratively; and
`tai2tt_bipm2021.clk` is a linear *extrapolation*, not a measured BIPM series. Neither is
a terminal simply because it comes from an authoritative repository.

## 3. Edge classes

`derived_from` · `snapshot_of` · `contributes_to` · `generated_by` · `observed_by` ·
`time_referenced_to` · `transferred_via` · `calibrated_by` · `corrected_by` ·
`contextualized_by` · `analysed_with` · `uses_ephemeris` · `uses_eop` ·
`uses_tide_model` · `uses_reference_frame` · `supersedes` · `evidenced_by` ·
`evaluated_by` · `selected_by_policy` · `contests`

**[P0] `conforms_to`** — added. Phase 0 needed to relate the optical archive to its
format specification (`optical-link-data-format@689bda77`), which is neither
`generated_by` nor `derived_from`.

**[P0] Edge-direction caution.** The optical format names comparison directories
`INSTITUTEB_OSCB-INSTITUTEA_OSCA`, so the **first** token is oscillator **B** and the
second is **A**. Verified against the YAML: in `INRIM_ITYb1-SYRTE_Sr2`,
`nu0A` = 429 228 004 229 873 Hz (Sr, SYRTE) and `nu0B` = 518 295 836 590 863.6 Hz
(Yb, INRIM). Manifest authors must not infer direction from directory-name order.

## 4. Bitemporal core

Every mutable node assertion and **every** edge carries:

| Field | Meaning |
| --- | --- |
| `valid_from`, `valid_to` | when the relation applied to the physical record or product |
| `known_from`, `known_to` | when the federation held that assertion |

`release_time`, `file_availability_time` and `observation_time` remain **separate
primitives**.

**For a fixed knowledge date, the materialised derivation subgraph must be acyclic.**
Bitemporality represents revisions; it does not legitimise circular derivation.
Acyclicity is evaluated at **snapshot** granularity: an IVS session may contribute to a
later EOP snapshot while a VLBI analysis consumes an earlier a-priori snapshot. Those
are distinct directed relations, not a cycle.

### 4.1 [P0] Availability-time provenance

`file_availability_time` must record **how it was obtained**. Phase 0's IGS pins derive
availability from a mirror's HTTP `Last-Modified`, which approximates but is not
identical to the provider's release time
([`FTRO-DEF-019`](../ledgers/deficiency-log.md#ftro-def-019)).

Required sub-field: `availability_time_source ∈ {provider_declared, mirror_derived, inferred, unknown}`.

## 5. Two-level identity

| Level | Meaning |
| --- | --- |
| **concept identity** | the continuing series or product line |
| **snapshot identity** | the immutable state actually consumed |

Snapshot identity uses a provider version or PID where available; otherwise an FTRO
identity composed from **concept identifier + retrieval time + byte checksum + recorded
retrieval procedure**.

Derivation and acyclicity are evaluated at snapshot granularity. A concept match shows
two chains depend on the same continuing resource; it **cannot** establish that they
consumed the same state.

**Every living artifact used in a reproduction must be materialised and pinned before
execution.**

### 5.1 [P0] Composite concept identity

Phase 0 found a case where even the concept identity had to be composed: PPTA DR3 is
published as two DOIs with 90,884 shared file paths and no manifest of the split
([`FTRO-DEF-015`](../ledgers/deficiency-log.md#ftro-def-015)).

`SeriesConcept` therefore admits `member_pids[]` and a computed `part_overlap` report.

## 6. Evidence, verification and contestation

These are **three orthogonal primitives**, never one status list:

```
evidence_state        ∈ {resolvable, opaque, unresolved}
VerificationActivity.result ∈ {supports, contradicts, indeterminate}
contestation_state    ∈ {none, open, resolved}
```

- **resolvable** — an identified evidence artifact can be retrieved and inspected under
  the recorded access conditions
- **opaque** — an artifact is identified but cannot be inspected sufficiently
- **unresolved** — no specific evidence artifact has been identified

"Asserted", "verified", "contested" are **derived display labels**. Lineage completeness
is computed by traversal, never stored.

Display-as-verified requires all four conditions in [Charter §6](../charter/access-charter-v0.1.md).

### 6.1 Phase-0 worked examples

| Situation | `evidence_state` | Verification | Contestation |
| --- | --- | --- | --- |
| `gps2utc.clk` pinned, checksum verified, C0′ regime confirmed by `VP-GPS2UTC-001` | resolvable | **supports** | none |
| Parkes receiver C0 vs C0′ configuration | **unresolved** | none | none |
| `.par` says `TT(BIPM2020)`; release ships `TT(BIPM2021)` | resolvable (both) | **contradicts** | **open** |
| PPTA Earth-orientation artifact | **unresolved** | none | none |
| Optical `ref_osc` / time-tag realisation | **unresolved** | none | none |
| `pks2gps.clk` own upstream provenance (narrative merge) | **opaque** | none | none |

## 7. Granularity and query semantics

- **Bulk samples stay in provider formats.** No node per one-second optical sample.
  Phase 0's optical leg has 9,018,290 samples and generates **12** comparison nodes.
- `Segment` nodes are introduced only where ancestry, calibration, validity, access or
  evidence **changes**.
- JSON-LD is the exchange representation — not a commitment to SPARQL or any database.
- Canonical valid-time and "as known on date" query fixtures are **normative**.
- Pilot acceptance requires **deterministic** query results on the pilot graph, not a
  scalability benchmark.

## 8. Time-coordinate fields

Task card §10 requires `sampling_interval`, `integration_interval`, `estimator_window`
and `validity_mask` as **distinct** fields, plus `coordinate_time_scale`,
`timestamp_format` and `timestamp_physical_realisation`.

### 8.1 [P0] `time_coordinate_quantum` — new

Phase 0 found no way to express a defect it measured: the optical archive's serialised
MJD is quantised at **86.4 ms** while its sampling interval is **1 s**
([`FTRO-DEF-002`](../ledgers/deficiency-log.md#ftro-def-002)). That is neither the
sampling interval nor the physical realisation.

| Field | Meaning |
| --- | --- |
| `time_coordinate_quantum` | numerical resolution of the recorded time coordinate **as serialised** |
| `time_coordinate_quantum_evidence` | how it was determined (declared, or measured — and by what procedure) |

An `AlignmentCertificate` must propagate this as a **floor** on achieved resolution.
For the optical leg that floor is ±43.2 ms, roughly eight orders of magnitude coarser
than the fractional-frequency precision the same files report.

Recorded as [`FTRO-DEF-021`](../ledgers/deficiency-log.md#ftro-def-021). **Not frozen.**

### 8.2 [P0] `validity_mask_informativeness` — new

Phase 0 found a documented three-state validity vocabulary in which **only one state
ever occurs** across 9,018,290 samples
([`FTRO-DEF-001`](../ledgers/deficiency-log.md#ftro-def-001)). A mask that never varies
is not a mask, and a manifest that merely records "validity flags present" would mislead.

| Field | Values |
| --- | --- |
| `validity_mask_informativeness` | `discriminating`, `degenerate`, `absent` |
| `validity_mask_observed_values` | the value set actually present |

Source values are **preserved and never coerced** (task card §20).

## 9. Rights fields

`data_rights` · `metadata_rights` · `evidence_retention_rights` ·
`redistribution_mode ∈ {copy_permitted, metadata_only, link_only, restricted, conflicting, unknown}`

Unknown or conflicting rights default to **pointer-only** registration.

### 9.1 [P0] `licence_compatibility`

Phase 0 found a copyleft source (PPTA DR3, CC BY-SA 4.0) alongside a permissive one
(Zenodo 17107693, CC BY 4.0). A field is required stating whether provider rights permit
incorporation into a CC BY 4.0 FTRO output:
`licence_compatibility ∈ {compatible, copyleft_restricted, incompatible, undetermined}`.

### 9.2 [P0] `access_class` and soft auth walls

`access_class ∈ {public, registered, mediated, restricted}` is a property of the
**retrieval path**, not the dataset.

A conforming retrieval procedure must validate **content shape**, not merely HTTP status
and checksum, because CDDIS returns an authentication interstitial with HTTP 200
([`FTRO-DEF-018`](../ledgers/deficiency-log.md#ftro-def-018)).

Required: `retrieval_validation ∈ {status_only, status_and_checksum, content_validated}`.
Only `content_validated` may support `evidence_state = resolvable`.

## 10. Policy objects and resolver

### 10.1 Resolver contract

```text
resolve(subject, valid_interval, as_of, policy_pid)
  -> selected_artifact_pid | null
     + reason_code
     + evidence
     + policy_pid
     + resolver_version
```

### 10.2 Policy requirements

Every policy is a first-class citable object with: PID and immutable version; issuer and
publication date; validity and knowledge intervals; human-readable rule; executable rule
or implementation hash; eligible product classes and tie-breaking rules; supersession
relation; and tests demonstrating positive selection, competing selection and null
behaviour.

**Provider recommendations are never mutable labels.** A changed recommendation produces
a new policy version.

### 10.3 [P0] Phase-0 resolver fixture material

The IGS pins supply real bitemporal fixture data. For epoch MJD 59630 (2022-02-20):

| Product | Artifact | Mirror availability |
| --- | --- | --- |
| Rapid | `igr21980.sp3.Z` | 2022-02-21T17:30:12Z |
| **Final** | `igs21980.sp3.Z` | **2022-03-13T11:46:51Z** |

So `resolve(epoch=59630, as_of=2022-02-25)` must return the **Rapid** product and
`resolve(epoch=59630, as_of=2022-03-20)` the **Final** — same policy, same epoch,
different knowledge date, and the historical answer is never overwritten.

`repro3` covers 1994–2020, so the homogeneous-reprocessing policy must return an
explained **null** for this interval.

## 11. Alignment certificate

Exactly one primary status:

| Status | Meaning |
| --- | --- |
| `computed` | a common representation and achieved resolution were calculated |
| `partial` | only a declared subset could be aligned |
| `no_common_support` | the actual temporal-support intersection is empty |
| `indeterminate` | alignment may be possible, but required evidence or corrections are missing or opaque |
| `unrepresentable` | no defensible common coordinate or uncertainty representation has been defined |

Only `computed`, and where meaningful `partial`, carry a numerical achieved resolution.
**A null value always carries its status and reason.**

Support is computed from **actual** records and validity masks, never from campaign
boundaries. Phase 0's certificate-precursor emits `no_common_support`
([`four-domain-intersection.json`](../phase0/reports/four-domain-intersection.json)).

## 12. Deficiency entries

`deficiency_class ∈ {source_evidence, schema, execution, policy, rights}`
`disposition ∈ {open, accepted, rejected, deferred, resolved}`

Each entry carries a stable identifier and version, dataset and domain, the failed step,
the known real-world fact or required evidence, evidence, severity and downstream
impact, any temporary workaround, a proposed response, and links to the manifest,
profile, policy and software versions in which the issue occurred.

**The ledger is distinct from incomplete ancestry.** The former records a limitation
encountered *by the federation*; the latter records incomplete knowledge about a
physical or documentary chain.

Classification follows the card's worked examples: an out-of-vocabulary or degenerate
archive flag begins as `source_evidence`, not automatically `schema`; inability to
*represent* a resolved fact is `schema`; missing executable environment information is
`execution`; ambiguous "provider-recommended" selection is `policy`; incompatible
metadata and data licences are `rights`.

## 13. Open profile questions for Phase 6

1. Should `time_coordinate_quantum` be required for every time-series node, or only where measured?
2. Is `validity_mask_informativeness` a profile field or a derived view?
3. Does `conforms_to` belong in the edge vocabulary or in RO-Crate's native conformance mechanism?
4. How should a composite `SeriesConcept` over several provider PIDs be identified stably?
5. Can RO-Crate 1.3 express bitemporal edge properties without a custom extension, and at what tooling cost?

**No term is frozen until these are answered against the full deficiency ledger.**
