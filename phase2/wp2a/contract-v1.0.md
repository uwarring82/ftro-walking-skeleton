# Phase 2 · Work Package 2A — Representation Identity Trial

**Document ID:** FTRO-P2-WP2A-001 · **Version:** 1.0.0 · **Date:** 2026-08-28
**Status:** **Pre-registered.** Frozen before either mapping is authored.
**Branch:** `phase2` · **Integration parent:** `e123a81`
**Licence:** CC BY 4.0

This is a **trial**, not a Gate-1 audit. It compares two ways of representing the same
encoded/decoded identity fork and reports which, if either, a registered requirement separates.
It does not amend the profile and does not re-open Phase 0 or Gate 1.

Opened against [`FTRO-P1-DEF-010`](../../ledgers/deficiency-log.json) — *snapshot identity does not
distinguish encoded retrieval bytes from decoded product bytes*.

---

## 1. Two premise corrections, recorded before they can bias the trial

### 1.1 The two families are consumed at different layers — this is the point, not a defect

A trial that treated both decoded payloads as analysis-consumed would bake in a false premise.
Verified against the implementation at `e123a81`:

| | IGS `.clk.Z` | ROCIT `.dat` member |
| --- | --- | --- |
| Who decodes | [`pin_igs.py:143`](../../src/ftro/pin_igs.py#L143) `unixz.decompress` | README step 3 `unzip` |
| Why | **content validation** — `decoded_variant_evidence()` executes a decoded-content expectation | **scientific analysis** |
| Scientific consumer | [`four_domain_intersection.py:101`](../../src/ftro/four_domain_intersection.py#L101) — GNSS support from **authenticated filenames** via `IGS_FINAL_NAME` | [`analyse_optical.py:155`](../../src/ftro/analyse_optical.py#L155) — reads `.dat` bytes |
| Decoded bytes reach the science? | **No** | **Yes** |

So the `Consumption` fact family must record *different* consumers, purposes and consumed layers
per family. Any representation that cannot express that asymmetry fails, and that failure is a
result, not an execution error.

### 1.2 The optical member digest is NOT authenticated in this repository

The member **path** is authenticated: `phase0/reports/optical-inventory-summary.json` records
`2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat` under comparison `PTB_Yb_CombKnoten-INRIM_ITYb1`,
16,106 samples, `mjd_first` **59631.788542** — the corpus-wide earliest optical sample, and
therefore the boundary that sets the published 31.17 h pulsar→optical gap. That is why this member
and not another.

**No per-member digest or size exists anywhere in the repository.** The values below are therefore
registered as **predictions**, not as authenticated expected facts. Step 2 confirms or refutes them.
A mismatch is a trial-halting finding to be reported, never a silent update.

---

## 2. Frozen scope

### 2.1 Exactly two product families

**Family A — IGS container variants (one family, three artifacts).** Authenticated in
`phase0/reports/igs-artifact-pins.json` (`d97b05d2…`):

| Artifact | SIO outer | BKG outer | Decoded |
| --- | --- | --- | --- |
| `igs21982.clk.Z` | `7bd05cce…` 1,594,709 B | `da4b4c4b…` 1,593,885 B | `b3145e51…` 6,037,296 B |
| `igs21983.clk.Z` | `9280fcd3…` 1,603,895 B | `898d8029…` 1,604,221 B | `8ac65974…` 6,071,695 B |
| `igr21991.clk.Z` | `2ead2464…` 1,044,279 B | `fa3ff944…` 1,044,897 B | `aa5e471c…` 4,000,804 B |

**Family B — ROCIT ZIP plus exactly one scientific member.**
Container: Zenodo record `10.5281/zenodo.17107693`, `ROCIT campaign results.zip`.
Member: `PTB_Yb_CombKnoten-INRIM_ITYb1/2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat`.
**Predicted** 780,292 B, SHA-256 `00cc90d8…363c067` — see §1.2.

Nothing else enters the trial. No third family, no additional member, no window change.

### 2.2 Exactly two representations

| | Model |
| --- | --- |
| **M1 explicit-node** | container entity → transformation activity → decoded/member entity |
| **M2 assertion-only** | per-container transformation assertion carrying the output byte identity, with **no** decoded/member entity |

**M2 still requires a named assertion/activity node.** Bitemporal and evidence attributes cannot
live on a plain RDF property — established by `FTRO-P1-DEF-002`. "Assertion-only" means *no output
entity*, never *no node*. A mapping that puts the quartet on a bare property is `not_executed`,
not a failure of M2.

Four fixtures: **M1×A, M2×A, M1×B, M2×B**.

### 2.3 Four neutral fact families both models must reproduce

| Family | Required facts |
| --- | --- |
| Retrieval | concept, occurrence, route, time, procedure, **outer** digest and size |
| Transformation | source retrieval, decoder/extractor, member selector, **output** digest and size |
| Consumption | consumer, purpose, **exact consumed byte layer** |
| Assertion | predicate, evidence artifact and state, verification result, temporal bounds |

The questions are neutral between M1 and M2 and are fixed before either mapping exists.

### 2.4 The current GNSS assertion is not the oracle

Expected facts come from independently authenticated evidence — the pin report, the optical
inventory, and step 2's input-evidence report — never from the provisional representation already
in `phase1/manifests/gnss/`. That manifest is an input under test, not a reference.

### 2.5 Evidence strength stays explicit

| Claim | State |
| --- | --- |
| SIO decoding | `reproduced` |
| BKG decoded equality | `historical_recorded_not_reexecuted` |
| Optical member extraction and scientific consumption | `reproduced` |

BKG is unreachable from this environment (session 19). Its decoded equality is a retained
historical record and is **never** upgraded by this trial.

---

## 3. Decision table

| Observation | Outcome |
| --- | --- |
| Only M1 passes | `encoded_decoded_supported` |
| Only M2 passes | `assertion_only_supported` |
| Both pass | `equivalent_for_registered_queries` |
| Both execute and fail | `neither_supported` |
| Required evidence insufficient | `indeterminate_evidence` |
| Mutation, evaluator or reset did not execute | `not_executed` |

**Stopping rule.** The trial stops when the fixed population is exhausted. There is no "look for
one more query" step.

`FTRO-P1-DEF-010` closes **only** when exactly one model is separated by a pre-registered Task Card
requirement. If both pass, the reported result is `equivalent_for_registered_queries` and the entry
stays open. **A model is never chosen aesthetically.**

---

## 4. Trusted computing base

Trusted, not re-verified by this package: Python 3.13 standard library; `git`; the Phase-0 pin
reports and optical inventory at `e123a81`; `src/ftro/unixz.py`, already verified byte-identical to
`gzip -dc` on a real container. Everything else this package asserts is executed.

---

## 5. Execution order

1. **Freeze this contract, the expected facts, the queries, the decision table and the mutation
   population** — before either mapping. *(this commit)*
2. Generate a durable **input-evidence report**, including independent `zipfile` and `unzip -p`
   cross-checks and an independent Unix-compress cross-check.
3. Hand-author the **four fixtures**.
4. Run **one explicitly non-qualifying calibration**.
5. Freeze any repairs in a **new candidate**.
6. Run **one qualifying comparison** from a clean checkout, and stop.

### 5.1 Two-stage mutation freeze — stated, not discovered later

The mutation **population, applicability matrix, expected observations and exact case count** are
frozen now (§6). The **executable per-case recipes** — concrete target, mutation value, detecting
command, reset boundary, destination — cannot be frozen before the fixtures exist, and are frozen
in a second pre-registration artifact after step 3 and **before** step 4.

Neither artifact may change after any result is observed. This is the Phase-0 lesson applied
in advance: a manifest that names operators without executable recipes cannot qualify
(`FTRO-P1-DEF-009`), and selecting recipes after inspecting the implementation is post-hoc.

---

## 6. Mutation population

Every case carries an expected observation. `R11` expects **no effect** — a registered
non-detection, so a recipe that silently fails to apply is distinguishable from a correct pass.

| # | Operator | Applies to | Expected |
| --- | --- | --- | --- |
| R1 | route drift | all 4 | detected |
| R2 | outer-digest drift | all 4 | detected |
| R3 | output-digest drift | all 4 | detected |
| R4 | wrong member selector | B only (2) | detected |
| R5 | wrong consumed layer | all 4 | detected |
| R6 | collapsed container identities | A only (2) | detected |
| R7 | missing transformation provenance | all 4 | detected |
| R8 | missing evidence/time state | all 4 | detected |
| R9 | dropped fixture | all 4 | detected |
| R10 | forged result | all 4 | detected |
| R11 | display-name-only change | all 4 | **not_detected** |

**Exactly 40 cases**: nine operators × 4 fixtures, plus R4 × 2 and R6 × 2.

---

## 7. Out of scope

No profile amendment. No Gate-1 rerun. No full ancestry graph. No RO-Crate conformance claim. No
BKG re-verification. No resolver. No browser. No third product family.

**Any scope change after results are seen creates a new contract version**, and the trial restarts
under it.
