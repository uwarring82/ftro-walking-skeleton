# Vocabulary pressure from four hand-authored manifests

**Document ID:** FTRO-VOC-001 · **Version:** 1.0.0 · **Date:** 2026-08-26 · **Licence:** CC BY 4.0
**Inputs:** the four manifests under `phase1/manifests/`, compared against profile v0.0.3.

Card Gate 1: *no FTRO term is frozen.* This document is the evidence for the profile amendment
that follows it — written **after** the manifests, not predicted before them.

---

## 1. Terms the manifests needed and the profile does not have

### 1.1 Edges cannot carry bitemporal fields — an `Edge` class is forced

The profile (§4) requires **every edge** to carry `valid_from`, `valid_to`, `known_from`,
`known_to`. In JSON-LD an edge is a *property*, and a property cannot carry attributes. Writing the
optical and pulsar manifests forced a reified `ftro:Edge` node with `edge_class`, `subject` and
`object` — a class the profile does not declare.

This is the clearest thing Phase 1 found. It is not a naming gap: **§4 as written cannot be
satisfied in the serialisation §9.1 mandates.** Either the profile declares the reified form, or
§4 must be relaxed to "every edge that carries bitemporal state", which changes its meaning.

### 1.2 `ConformanceReport` has no class, though §9.1 requires the record

§9.1: *"The exact validator and its version must be recorded in every conformance report."* The
profile mandates the artifact and declares no node class for it. All four manifests invented
`ftro:ConformanceReport`.

### 1.3 `time_ephemeris` has no edge

`J0437-4715.par` declares `TIMEEPH IF99`. That is not an ephemeris (`uses_ephemeris` is DE436) and
not a reference frame. Used as `ftro:time_ephemeris`; the profile has no term.

---

## 2. Terms the profile has and no manifest needed

**13 of 21 edge classes unused:** `derived_from`, `snapshot_of`, `contributes_to` *(needed but
unresolved — see §4)*, `observed_by`, `transferred_via`, `calibrated_by`, `corrected_by`,
`analysed_with`, `uses_tide_model`, `supersedes`, `evidenced_by`, `evaluated_by`,
`selected_by_policy`, `contests`.

**28 of 41 node classes unused.**

Two different situations, and the distinction matters:

| Reason unused | Examples | Action |
| --- | --- | --- |
| The evidence is unresolved, so the edge has no object | `contributes_to` (VLBI→EOP), `uses_tide_model` | **Keep.** The term is needed; the provider evidence is missing. |
| Phase 0's four legs simply do not exercise it | `analysed_with`, `transferred_via`, `ContextualSensorSeries` | **Keep but mark untested.** A term no manifest has used is unvalidated vocabulary. |

The profile should say which of its terms have been exercised against a real product. Two thirds
have not.

---

## 3. Fields used by all four — required-field candidates

Twenty-one fields appear in every manifest:

`access_class` · `base_specification` · `concept_kind` · `conformance_report` · `data_rights` ·
`data_role` · `domain` · `evidence_state` · `known_from` · `known_to` · `licence_compatibility` ·
`note` · `profile` · `redistribution_mode` · `retrieval_validation` · `sha256` · `valid_from` ·
`valid_to` · `validation_result` · `validator` · `validator_version`

Against 86 fields used by exactly one manifest, which are correctly domain-specific and should stay
optional.

---

## 4. What the manifests could not express, and why

| Gap | Cause | Recorded as |
| --- | --- | --- |
| Optical `time_referenced_to` has no object | `ref_osc` absent from all 12 comparisons | `FTRO-DEF-003`, evidence_state `unresolved` |
| Optical comparator has two readings | `ref_osc` discriminates them | `FTRO-DEF-004`, both retained |
| Pulsar `uses_eop` has no object | The release identifies no EOP artifact | `FTRO-DEF-012` |
| VLBI `contributes_to` has no object | Downstream product not pinned | open |
| TT realisation contested | `.par` says BIPM2020, release ships BIPM2021 | `FTRO-DEF-011`, contestation `open` |
| Wrapper member not pinned by container digest | 7 filenames, 5 digests | `FTRO-DEF-026` |

**Gate 1 is satisfied on this axis:** each manifest either locates its source bytes or reports the
access failure. None of these gaps is repaired, substituted or hidden.

---

## 5. Asymmetry worth noting

| Domain | Fields | Edges | FTRO node classes |
| --- | ---: | ---: | ---: |
| pulsar | 67 | 5 | 12 |
| optical | 64 | 4 | 7 |
| vlbi | 53 | 1 | 5 |
| gnss | 46 | **0** | 4 |

GNSS uses **no ancestry edges at all**. Its content is pinned artifacts plus two policy objects —
it is a *dependency* of other chains rather than a chain itself. The profile treats all domains
alike; a leg whose role is to be consumed may need a different minimum record than one that
consumes.

---

## 6. Proposed amendment (v0.0.4) — not yet applied

1. **Declare `ftro:Edge`** as a reified relation carrying `edge_class`, `subject`, `object` and the
   bitemporal quartet; restate §4 in terms of it.
2. **Declare `ConformanceReport`**, with `validator` and `validator_version` **required and
   nullable** — a null with a stated reason is conformant, silence is not.
3. **Add `uses_time_ephemeris`**, or fold `TIMEEPH` into `uses_ephemeris` with a qualifier. Prefer
   the separate edge: they are different artifacts with different provenance.
4. **Mark every term `exercised: true|false`** against these four manifests. Two thirds are `false`.
5. **Promote the 21 universal fields to required**; leave the 86 singletons optional.
6. **Do not freeze anything.** Four manifests over four domains in one window is not enough
   evidence to fix a vocabulary, and Gate 1 does not ask for it.
