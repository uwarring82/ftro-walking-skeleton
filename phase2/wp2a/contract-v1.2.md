# Phase 2 · Work Package 2A — Representation Identity Trial

**Document ID:** FTRO-P2-WP2A-001 · **Version:** 1.2.0 · **Date:** 2026-08-30
**Status:** **Pre-registered.** Frozen before any fixture, evaluator or Step-2 run exists.
**Supersedes:** `contract-v1.1.md` (**rejected**), `contract-v1.0.md` (**rejected**). Both retained
byte-unchanged — see [`REGISTRATION-STATUS.md`](REGISTRATION-STATUS.md).
**Branch:** `phase2` · **Licence:** CC BY 4.0

Opened against `FTRO-P1-DEF-010`. A **trial**, not a Gate-1 audit.

---

## 0. Why v1.1 was rejected

v1.1 repaired ten defects in v1.0 and introduced or left eight more. It was rejected before Step 2
for the same reason v1.0 was: **a registration is amended only before execution begins.**

| # | Defect in v1.1 | v1.2 |
| --- | --- | --- |
| 1 | Claimed a committed generator that did not exist; and predicates, temporal semantics, consumption claims and execution states are **not derivable** from the four sources at all | `build_source_facts.py` (committed, `--check`, tested) emits **only** literal source content; all judgement moves to `interpretations-v1.2.json` with a stated basis per item |
| 2 | BKG containers and the optical member labelled `unresolved`; Q8 froze that false contrast | both are **`opaque`** — identified but not inspectable (profile v0.0.3:212). Q8 rewritten as a three-way distinction |
| 3 | Q5b named the member-path date as the optical support key | **the MJD token and flag column inside the member content**; the filename is a selector and label only |
| 4 | Q7 scored `per_output` (A=3) against six Family-A assertions; M2 implies six transformation assertions | `per_assertion`; all cardinalities declared explicitly |
| 5 | 76 cases froze **counts, not target identities** — R8 could still pick among assertions and fields | **134 enumerated cases**, each naming its exact `target_id` and `target_field` |
| 6 | Q9 required the output state to *be* an RDF subject/object, which M2 forbids — `assertion_only_supported` was unreachable by definition | Q9 asks for an **identifier denoting** the output byte-state, explicitly satisfiable without an output entity |
| 7 | Retrieval start used as *exact* `valid_from`; BKG `known_to` closed at the SIO re-pin | `valid_from` `unknown` with `not_later_than`; `known_to` **open** — knowledge did not end when route preference changed |
| 8 | Step 2 had no schema, generator, target population, trusted base, disagreement outcome, and registered only 60 of 256 digest bits | `step2-schema-v1.2.json`: four outcomes incl. `evidence_assurance_failed`, exhaustive targets, trusted base, **all 256 bits** |

Publication defects fixed alongside: recursive discovery had no regression test (`FTRO-P1-DEF-019`);
it declared `.py` as CC BY Markdown (`FTRO-P1-DEF-017`); the root crate's `dateModified` never
advanced (`FTRO-P1-DEF-018`); `phase1/README.md` still reported a superseded supplement version.

---

## 1. Generated facts and registered interpretations are different documents

This is the structural change in v1.2.

| Document | Contains | Produced by |
| --- | --- | --- |
| [`source-facts-v1.2.json`](source-facts-v1.2.json) | **only** values copied verbatim from a pinned source | [`build_source_facts.py`](build_source_facts.py), digest-pinned, `--check`-able, tested |
| [`interpretations-v1.2.json`](interpretations-v1.2.json) | predicates, evidence states, execution states, temporal semantics, code-consumption claims | **hand-curated**, each with `basis ∈ {profile_term, code_reading, registered_convention}` |

No source states a predicate, an evidence state, a temporal semantics, or which line of code
consumes which byte layer. v1.1 presented all of it as "derived from the four pinned sources".
Calling curation derivation is projection-only verification one level up.

The generator pins each source by digest and **fails rather than re-deriving** on drift. During
authoring it rejected a fabricated digest tail on the inventory source — which is the behaviour
that matters.

---

## 2. Scope (unchanged)

**Family A** — three IGS products, **6** retrieval occurrences (SIO + BKG), **3** decoded outputs,
**6** assertions. **Family B** — one ROCIT container, 1 occurrence, 1 member, 1 assertion.
**M1** explicit output node; **M2** per-container transformation assertion with no output entity —
but still a **named assertion node**, since bitemporal attributes cannot sit on a bare property
(`FTRO-P1-DEF-002`). Four fixtures: M1×A, M2×A, M1×B, M2×B.

---

## 3. Evidence state, corrected

Profile v0.0.3:212 — `unresolved` means **no specific evidence artifact has been identified**.

| Subject | State | Why |
| --- | --- | --- |
| IGS container @SIO | `resolvable` | retrieved and content-validated here |
| IGS container @BKG | **`opaque`** | identified exactly — name, digest, size, route, time at `a806bba` — but BKG refused all connections (session 19) |
| Historical pin report `a806bba:…` | `resolvable` | the **report** is retrievable even though the container it describes is not |
| ROCIT container | `resolvable` | |
| ROCIT member (pre-Step-2) | **`opaque`** | path authenticated, bytes not yet inspected |

`execution_status ∈ {reproduced, historical_recorded_not_reexecuted, not_attempted}` is a
**registered convention, not a profile term**, and is reported separately.

## 3.1 Temporal bounds, corrected

`valid_from` is `unknown` carrying `not_later_than = retrieved_utc` — our retrieval time bounds
when the bytes existed, not when they became valid. `known_from` is exact at `retrieved_utc`.
**`known_to` is open for every assertion, BKG included**: a change of route preference does not end
knowledge of a decoded-equality assertion.

---

## 4. Oracle

Four pinned sources (`source-facts-v1.2.json` records the digests). A **fifth** — the Step-2
input-evidence report — is added by pin, and only on `step2_supports`.

`phase1/manifests/gnss/ro-crate-metadata.json` is an input **under test**, never an oracle.

---

## 5. Consumption is three facts

| Fact | Family A | Family B |
| --- | --- | --- |
| Direct scientific input | the authenticated pin-report JSON | the extracted `.dat` member bytes |
| Logical support key | the pin record's `name`, via `IGS_FINAL_NAME` | **the MJD token and flag column inside the member content**, via `parse_dat()` |
| Provider payload bytes consumed by science | **none** | the member bytes |

`analyse_optical.py` uses the filename only to select `*.dat` and to label the row. It never parses
the date. v1.1 said otherwise and was simply wrong about the production code.

---

## 6. Decision tables

**Model pass.** Every applicable query returns every expected fact at its **declared** cardinality,
no extra and no missing. Per-family verdicts are always reported.

| Observation | Outcome |
| --- | --- |
| Only M1 passes both families | `encoded_decoded_supported` |
| Only M2 passes both families | `assertion_only_supported` |
| Both pass both families | `equivalent_for_registered_queries` |
| Both execute and fail | `neither_supported` |
| **A model passes one family and fails the other** | **`split_by_family`** |
| Required evidence insufficient | `indeterminate_evidence` |
| Mutation, evaluator or reset did not execute | `not_executed` |
| A registered fault undetected, or R11 detected | `mutation_assurance_failed` |

`mutation_assurance_failed` **blocks every model verdict**. `split_by_family` does **not** close
`FTRO-P1-DEF-010`.

**Step 2:** `supports` \| `contradicts` \| `evidence_assurance_failed` \| `not_executed`.
Two extractors disagreeing with **each other** is `evidence_assurance_failed`: no digest is adopted
from a disagreeing pair. Step 2 is **authentication and reproduction of a prior observation**, not a
blind prediction — the claimed member value was supplied before registration, and a confirmation
carries the weight of an independent reproduction, nothing more.

**Stopping rule.** The trial stops when the enumerated population is exhausted. `FTRO-P1-DEF-010`
closes **only** if exactly one model passes both families. No model is ever chosen aesthetically.

---

## 7. Mutations: 134 enumerated cases, plus R11

Every case names its exact `target_id` and, where the operator has one, its `target_field`.
Freezing counts was not enough: v1.1's R8 could still have chosen among six assertions and four
temporal fields.

R11 (presentation-only, expects `not_detected`) is enumerated at recipe freeze, **one case per
entity**, and the recipe checker must assert that count equals the fixture's declared entity count.
F-REQ-4 makes `ftro:display_name` mandatory; F-REQ-5 makes the entity count declared.

Per-case executable recipes are frozen in `mutation-recipes-v1.2.json` after Step 3 and **before**
Step 4. Neither artifact changes after any result is seen.

---

## 8. Execution order

1. Freeze this contract, source facts, interpretations, queries, decision tables, mutation cases,
   Step-2 schema ✅
2. Write and freeze `run_step2.py`; run Step 2 once from a clean published commit
3. Hand-author four fixtures satisfying F-REQ-1…5
4. Freeze `mutation-recipes-v1.2.json`; one explicitly **non-qualifying** calibration
5. Freeze any repairs in a new candidate
6. One qualifying comparison from a clean checkout, then **stop**

---

## 9. Out of scope

No profile amendment, Gate-1 rerun, full ancestry graph, RO-Crate conformance claim, BKG
re-verification, resolver, browser, third family. **Any scope change after results are seen creates
a new contract version and restarts the trial.**
