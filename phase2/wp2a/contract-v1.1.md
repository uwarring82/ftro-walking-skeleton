# Phase 2 · Work Package 2A — Representation Identity Trial

**Document ID:** FTRO-P2-WP2A-001 · **Version:** 1.1.0 · **Date:** 2026-08-29
**Status:** **Pre-registered.** Frozen before any fixture or evaluator exists.
**Supersedes:** [`contract-v1.0.md`](contract-v1.0.md) — **rejected pre-registration**, retained
unchanged. See [`REGISTRATION-STATUS.md`](REGISTRATION-STATUS.md).
**Branch:** `phase2` · **Licence:** CC BY 4.0

Opened against `FTRO-P1-DEF-010`. This is a **trial**, not a Gate-1 audit.

---

## 0. Why v1.0 was rejected

v1.0 was mechanically sound — valid JSON, 40 cases recomputing exactly, the optical values
correctly labelled a prediction — and **still could not execute or answer its own requirements**.
Ten defects, all structural. The registration was rejected before Step 2 rather than repaired
mid-flight, because a registration amended after execution begins is not a registration.

| # | Defect in v1.0 | v1.1 |
| --- | --- | --- |
| 1 | `evidence_state` conflated accessibility, verification and execution; Q7 required temporal bounds the oracle never supplied | §2 three axes; §3 explicit bound values **and** bound states |
| 2 | Q1's oracle lacked BKG sizes/routes/times/procedures and the optical container's retrieval identity | §4 four pinned sources |
| 3 | Q5 conflated three distinct IGS consumption facts | Q5a/Q5b/Q5c |
| 4 | The identity question was untested: M2 could return a digest literal and pass Q1–Q8 | **Q9** addressability |
| 5 | An executed R1–R10 that went undetected, or a detected R11, matched no outcome | `assurance_failed` |
| 6 | "Applies to fixture" let recipes pick the easiest of 3 products / 6 occurrences / 3 outputs | exhaustive targets, **76** cases |
| 7 | R11 mutated a display name fixtures were not required to have | **F-REQ-4** mandatory |
| 8 | Query applicability was prose; model-pass aggregation undefined | machine-readable applicability, cardinality, pass rule |
| 9 | A refuted optical prediction halted the trial with no typed outcome | `prediction_refuted` |
| 10 | Seven Phase-1 reports undeclared while `refresh_crate --check` reported green | bounded recursive discovery |

---

## 1. Frozen scope

Unchanged from v1.0 §2 and restated here so this document is self-contained.

**Family A — IGS container variants.** One family: three products (`igs21982.clk.Z`,
`igs21983.clk.Z`, `igr21991.clk.Z`), **six** retrieval occurrences (SIO and BKG per product),
**three** decoded outputs.

**Family B — ROCIT ZIP plus exactly one member.** One container, one retrieval occurrence, one
member: `PTB_Yb_CombKnoten-INRIM_ITYb1/2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat` — the
corpus-wide earliest optical sample, which sets the published 31.17 h pulsar→optical gap.

**Two representations.** M1 explicit container → transformation → output node. M2 per-container
transformation assertion carrying output byte identity, **no output entity**. M2 still requires a
named assertion node: bitemporal and evidence attributes cannot live on a plain RDF property
(`FTRO-P1-DEF-002`). A bare-property mapping is `not_executed`, not a failure of M2.

Four fixtures: **M1×A, M2×A, M1×B, M2×B**.

---

## 2. Three axes, never one

v1.0's single `evidence_state` mixed a profile term with two states that are not profile terms.

| Axis | Enum | Means | Authority |
| --- | --- | --- | --- |
| `evidence_state` | `resolvable` \| `opaque` \| `unresolved` | can the evidence artifact be retrieved and inspected | profile v0.0.3 line 207 |
| `verification_result` | `supports` \| `contradicts` \| `indeterminate` | what the evidence does to the assertion | profile |
| `execution_status` | `reproduced` \| `historical_recorded_not_reexecuted` \| `not_attempted` | did **this package** re-execute the check | WP2A-local, **not** a profile term |

BKG is `evidence_state: unresolved` (refused all connections from this environment, session 19)
**and** `execution_status: historical_recorded_not_reexecuted`. Those are different statements and
**Q8 cannot be answered without separating them.** This trial never upgrades BKG to `reproduced`.

---

## 3. Temporal facts are values plus bound states

Every assertion carries `valid_from`, `valid_to`, `known_from`, `known_to`, each as an explicit
`{value, bound_state}` with `bound_state ∈ {exact, open, unknown}`. A null value with
`bound_state: open` is a *stated* open bound; a null with no bound state is a missing fact and
fails Q7. JSON-LD null disappears at RDF expansion (`FTRO-P1-DEF-002` v2.0.0), so silence cannot
be a bound.

---

## 4. The oracle is four pinned sources

| Role | Source | SHA-256 |
| --- | --- | --- |
| IGS SIO occurrences and decoded outputs | `phase0/reports/igs-artifact-pins.json` | `d97b05d2…` |
| **IGS BKG route, size, time, procedure** | `a806bba:phase0/reports/igs-artifact-pins.json` | `467d699e…6201` |
| Optical container retrieval identity | `phase0/evidence/identities.json` | `a4a27e7e…3ac45` |
| Optical member path and selection basis | `phase0/reports/optical-inventory-summary.json` | `f2f8b482…` |

The current pin report retains only `previous_retrieval_sha256`; **BKG route, size, retrieval time
and procedure exist only at `a806bba`.** Without that source Q1 is unanswerable for half of
Family A's occurrences.

`phase1/manifests/gnss/ro-crate-metadata.json` is an input **under test** and is never an oracle.

`expected-facts-v1.1.json` is **derived** from these four sources by a committed generator, not
hand-transcribed.

---

## 5. Consumption is three facts, not one

For Family A they have three different answers, and a model that returns one answer fails:

| Fact | Family A | Family B |
| --- | --- | --- |
| Direct scientific input | the authenticated pin-report JSON | the extracted `.dat` member |
| Logical support key | the `name` field, via `IGS_FINAL_NAME` | the member path date component |
| **Provider payload bytes consumed by science** | **none** | the member bytes |

Decoded IGS bytes are consumed by `pin_igs.py` for **content validation**; they never reach
`four_domain_intersection.py`, which reads authenticated filenames. Q5a/Q5b/Q5c ask separately.

---

## 6. Q9 — the query that actually tests the identity question

M2 can return an output digest as a literal and satisfy every retrieval, transformation,
consumption and assertion query while never giving the consumed state an **addressable identity**.
The trial exists to decide whether that suffices.

**Q9:** does the consumed state have a stable, addressable snapshot identity that can occupy the
subject or object position of a derivation or evidence relation? A bare digest literal is rejected.

If M2 fails **only** Q9, the finding is that assertion-only is insufficient for addressability —
a substantive result, not a malformed fixture.

---

## 7. Decision tables

**Model pass rule.** A model passes a family when every query *applicable to that family* returns
every expected fact at its registered cardinality, with no extra and no missing answer. A query not
applicable to a family is neither pass nor fail for it. A model passes overall only by passing both
families; passing one and failing the other is recorded as such and is not a pass.

**Trial outcome.**

| Observation | Outcome |
| --- | --- |
| Only M1 passes | `encoded_decoded_supported` |
| Only M2 passes | `assertion_only_supported` |
| Both pass | `equivalent_for_registered_queries` |
| Both execute and fail | `neither_supported` |
| Required evidence insufficient | `indeterminate_evidence` |
| Mutation, evaluator or reset did not execute | `not_executed` |
| **A registered fault went undetected, or R11 was detected** | **`mutation_assurance_failed`** |

`mutation_assurance_failed` **blocks any model verdict.** No conclusion may be drawn from a run
whose evaluator does not detect its own registered faults.

**Step 2 outcome:** `prediction_confirmed` \| `prediction_refuted` \| `not_executed`.
`prediction_refuted` halts the trial and is reported as a typed result — the member digest
prediction failing is a finding about the evidence, not an accident.

**Stopping rule.** The trial stops when the fixed population is exhausted. `FTRO-P1-DEF-010` closes
**only** if exactly one model is separated by a pre-registered requirement. If both pass, the
result is `equivalent_for_registered_queries` and the entry stays open. **No model is ever chosen
aesthetically.**

---

## 8. Mutation population: 76 exhaustive cases

Eleven operators over explicitly counted target populations — 6/6/1/1 retrieval occurrences,
3/3/1/1 outputs, 3/3/1/1 products, 4 fixtures. **Target selection is exhaustive**, so the recipe
author has no remaining choice: v1.0's "applies to fixture" would have let a recipe mutate
whichever of six occurrences was easiest and call the operator covered.

`R11` (presentation-only) expects `not_detected`, and **F-REQ-4 makes `ftro:display_name`
mandatory on every entity** so R11 is guaranteed executable.

### 8.1 Two-stage freeze

Population, targets, expected observations and outcome rules are frozen **now**. Executable
per-case recipes — concrete value, detecting command, reset boundary, destination — are frozen in
`mutation-recipes-v1.1.json` after Step 3 and **before** Step 4. Neither may change after any
result is observed.

---

## 9. Execution order

1. Freeze this contract, expected facts, queries, decision tables, mutation population ✅
2. Durable input-evidence report — independent `zipfile`, `unzip -p`, Unix-compress cross-checks;
   settles the member-digest prediction
3. Hand-author four fixtures satisfying F-REQ-1…4
4. Freeze `mutation-recipes-v1.1.json`, then one explicitly **non-qualifying** calibration
5. Freeze any repairs in a new candidate
6. One qualifying comparison from a clean checkout, then **stop**

---

## 10. Out of scope

No profile amendment, Gate-1 rerun, full ancestry graph, RO-Crate conformance claim, BKG
re-verification, resolver, browser, or third family. **Any scope change after results are seen
creates a new contract version and restarts the trial under it.**
