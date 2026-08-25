# FTRO Access Charter v0.1

**Document ID:** FTRO-CHT-001 · **Version:** 0.1.0 · **Date:** 2026-08-25
**Status:** Draft, informed by Phase-0 evidence · **Licence:** CC BY 4.0
**Task card:** FTRO-WS-001 v0.3 §7A

> **Status note.** This charter is written *after* Phase 0, not before it, so that every
> clause is grounded in something actually encountered. Where Phase 0 produced evidence
> bearing on a clause, the clause cites it.

---

## 1. Mission

The Federated Time-Reference Observatory exposes, in machine-readable and
human-readable form, the **reference-clock ancestry of public time-referenced
scientific measurements across domains**, so that an external researcher can determine
what was measured, what made its timestamp meaningful, which parts of that chain are
supported or missing, and whether two records may legitimately share a time axis.

The differentiating product is the **bitemporal reference-ancestry graph with a
human-readable browser**. Discovery, adapters and staging are necessary infrastructure,
not the scientific contribution.

## 2. Federation and custody

- **Providers retain custody.** FTRO stores identifiers, manifests, evidence,
  provenance, access instructions, checksums and optional compute-near-data hooks.
- **FTRO is not an archive.** It does not accept deposits and does not guarantee
  preservation of provider bytes.
- **Inclusion is not endorsement**, and it is not a claim of rights.
- Retrieved bytes held for verification are working copies, excluded from publication.

## 3. Rights

### 3.1 FTRO-authored outputs

| Output | Licence |
| --- | --- |
| Manifests, graph metadata, certificates, ledgers, lab notes, documentation | **CC BY 4.0** |
| Browser and resolver software, analysis scripts | **Apache-2.0** |

### 3.2 Provider content

**Provider content retains its own licence and is never relicensed by inclusion.**

FTRO tracks four rights fields *separately*: `data_rights`, `metadata_rights`,
`evidence_retention_rights`, and
`redistribution_mode ∈ {copy_permitted, metadata_only, link_only, restricted, conflicting, unknown}`.

**Unknown or conflicting rights default to `link_only`** pending provider-specific
review.

### 3.3 The copyleft boundary — evidence-driven clause

Phase 0 found that the four pilot legs carry **three different rights situations**
([`rights-ledger.md`](../ledgers/rights-ledger.md)):

| Source | `data_rights` | Compatible with CC BY 4.0 FTRO output? |
| --- | --- | --- |
| Zenodo 17107693 | CC BY 4.0 | Yes |
| PPTA DR3 | **CC BY-SA 4.0** | **No — copyleft** |
| IGS products | not established | Undetermined |
| IVS / CDDIS | not established | Undetermined |

Therefore: **FTRO records facts and pointers, not provider prose.** Identifiers, paths,
sizes, checksums, epochs, declared parameter values and computed measurements over
provider data are recorded freely. Provider descriptive text is quoted only briefly,
with attribution, and never bulk-incorporated.

Where a provider licence is copyleft, `redistribution_mode` is `link_only` regardless of
how convenient copying would be. See
[`FTRO-DEF-014`](../ledgers/deficiency-log.md#ftro-def-014).

## 4. Access modes

| Mode | Meaning |
| --- | --- |
| `public` | Retrievable anonymously over a documented protocol |
| `registered` | Requires a free account or credential |
| `mediated` | Requires a request handled by a person or committee |
| `restricted` | Not available to the general public |

**An access mode is a property of the retrieval path, not of the dataset.** The same
data may be `public` at one mirror and `registered` at another. Phase 0 recorded the
IVS leg as `registered` at CDDIS while its session metadata is `public` at the IVS
session listing.

### 4.1 Soft authentication walls — evidence-driven clause

Phase 0 found that CDDIS returns an **Earthdata login page with HTTP 200**, not 401 or
403 ([`FTRO-DEF-018`](../ledgers/deficiency-log.md#ftro-def-018)). A retrieval procedure
validating only status code and checksum would pin a login page as data.

**Every FTRO retrieval procedure must validate content shape, not merely status and
checksum.** A retrieval that cannot distinguish data from an authentication interstitial
is not a conforming retrieval procedure. This applies to FTRO's own tooling and is
recorded as an open defect against it.

## 5. Typed incompleteness

Missing, inaccessible, disputed and merely-asserted ancestry are **retained and typed**,
never hidden and never averaged into a completeness score.

Primitive, orthogonal fields:

- `evidence_state ∈ {resolvable, opaque, unresolved}`
- `VerificationActivity.result ∈ {supports, contradicts, indeterminate}`
- `contestation_state ∈ {none, open, resolved}`

"Asserted", "verified" and "contested" are **derived display labels**, not stored states.
Lineage completeness is computed by traversal.

**Insufficient public evidence is a valid result.** It is *not* a demonstrated shared
dependency, and it must never be displayed as one.

## 6. Verification

An assertion is displayed as **verified** only if all four hold:

1. its evidence is resolvable and pinned by identifier, version and checksum where available;
2. a **named, versioned verification procedure** evaluates the relation;
3. that activity records a supporting result, execution time, agent or software, and output;
4. the verification activity is itself resolvable within the federation.

Phase 0 established one such procedure, `VP-GPS2UTC-001` v1.0.0, with output
[`VA-GPS2UTC-001.json`](../phase0/evidence/VA-GPS2UTC-001.json).

A supported claim may still be **openly contested** by a different assertion.
Contestation is independent of verification.

## 7. Processing levels

Provider-declared processing levels are **advisory annotations**. FTRO does not
adjudicate a universal notion of "raw". Transformations and their evidence are
authoritative; the level label is not.

## 8. Versioning, supersession, withdrawal, correction and contestation

- Every FTRO document, policy, profile and ledger entry carries an immutable version.
- **Policies are never mutated.** A changed provider recommendation produces a *new
  policy version*; historical resolutions remain reproducible under the cited version.
- Corrections are new versions with a `supersedes` relation, not edits in place.
- Withdrawal removes an assertion from the current view but not from the knowledge-time
  history.
- Any party may lodge a contesting assertion with evidence; the contested claim is not
  removed.

### 8.1 Two-level identity — evidence-driven clause

Living series carry **concept identity** (the continuing product line) and **snapshot
identity** (the immutable state actually consumed). Where a provider supplies no
immutable snapshot PID, FTRO composes one from concept identifier, retrieval time, byte
checksum and recorded retrieval procedure.

Phase 0 found this necessary in three of four legs, and found one case where even the
*concept* identity had to be composed: PPTA DR3 is published as **two DOIs sharing
90,884 identical file paths** ([`FTRO-DEF-015`](../ledgers/deficiency-log.md#ftro-def-015)).

## 9. Separation of observatory from analysis

FTRO provides discoverability, provenance, alignment certificates, validation and
reproducible access. **Searches for physical signatures, anomaly detection,
cross-correlation, parameter inference and model comparison live in separately
versioned analysis projects.**

No physics-search or anomaly-detection claim is ever presented as an observatory result.

Relationship semantics keep this boundary visible in the graph itself:
`time_referenced_to` and `calibrated_by` / `corrected_by` are ancestry;
`contextualized_by` carries no causal claim; `analysed_with` marks a combination made
only by an external analysis. **Temporal or spatial proximity is never displayed as
evidence of causation.**

## 10. Nulls require reasons

Empty overlap, missing evidence, incommensurability and failed resolution are
**distinct outcomes**. A null is always accompanied by its status and reason code.

Alignment certificates emit exactly one primary status from
`{computed, partial, no_common_support, indeterminate, unrepresentable}`. Only
`computed`, and where meaningful `partial`, carry a numerical achieved resolution.

Phase 0's first certificate-precursor emits **`no_common_support`**
([`FTRO-DEF-023`](../ledgers/deficiency-log.md#ftro-def-023)): the pilot's four domains
have no simultaneous support in the candidate window. Per §6 and §20 of the task card
the interval was **not widened** and no substitute dataset was introduced.

## 11. Independent outcome reporting

Two axes are reported **separately and never collapsed**:

- `platform_conformance ∈ {pass, partial, fail}`
- `shared_ancestry_demonstration ∈ {snapshot_demonstrated, series_demonstrated_with_divergence, not_demonstrated, indeterminate, contradicted}`

Evidence opacity may yield platform conformance `pass` while shared ancestry remains
`indeterminate`. **Failure to demonstrate shared ancestry is a valid scientific result
of the skeleton, not a platform failure.**

A series-level match is a successful but *weaker* result and must always carry its
quantified snapshot-divergence report. Concept-level similarity, evidence opacity and
current-series substitution are **never** converted into snapshot identity.

## 12. Participation incentives

Providers who participate receive: citation flow to their own PIDs, explicit provider
credit on every derived view, service credit for federation-visible infrastructure, and
reduced support burden through machine-readable access instructions that answer common
reuse questions without correspondence.

FTRO's deficiency ledger is offered to providers as **actionable feedback**, not as
criticism. Every Phase-0 entry names a concrete proposed response.

## 13. Governance sequence

**A public walking skeleton exists first.** Engagement with GGOS, IERS, BIPM and data
providers follows a working object, not a proposal.

No consortium formation, production portal development, additional-domain ingestion or
physics analysis precedes the outputs listed in task card §22.

## 14. Amendment

This charter is versioned. Amendments are new versions with a `supersedes` relation.
It will be revised at Phase 6 in the light of the full deficiency ledger, and no FTRO
profile field is frozen before that review.
