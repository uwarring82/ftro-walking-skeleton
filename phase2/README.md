# Phase 2 — reference-ancestry graph

Branch `phase2`, from `main` @ `e123a81` (Phase 0 closed, Phase 1 Gate 1 passed).

| Work package | Status |
| --- | --- |
| **2A — Representation Identity Trial** | **pre-registered**; step 1 of 6 complete |
| 2B+ — profile amendment, ancestry materialisation, query fixtures | not started; held behind 2A |

## WP2A in one paragraph

`FTRO-P1-DEF-010` records that snapshot identity does not distinguish encoded retrieval bytes from
decoded product bytes: three IGS products serve different container bytes at SIO than at BKG while
decoding identically. WP2A compares exactly two representations of that fork against exactly two
product families, using neutral questions fixed before either mapping exists. It reports which, if
either, a registered requirement separates — and reports **equivalence** rather than choosing
aesthetically when both pass.

> **Read [`REGISTRATION-STATUS.md`](wp2a/REGISTRATION-STATUS.md) first.** Versions **1.0.0 and
> 1.1.0 were both rejected before Step 2** and are retained byte-unchanged; **1.2.0 is current**.
> No step of the trial has been executed under any version.

- [`contract-v1.2.md`](wp2a/contract-v1.2.md) — scope, corrected states, oracle, decision tables; §0 tabulates the eight v1.1 defects
- [`source-facts-v1.2.json`](wp2a/source-facts-v1.2.json) — **generated** by [`build_source_facts.py`](wp2a/build_source_facts.py); literal source content only
- [`interpretations-v1.2.json`](wp2a/interpretations-v1.2.json) — every curated judgement, with a stated basis
- [`queries-v1.2.json`](wp2a/queries-v1.2.json) — 11 queries, declared cardinality, split-family rule
- [`mutation-cases-v1.2.json`](wp2a/mutation-cases-v1.2.json) — **134 enumerated cases** with exact target identities, plus R11
- [`step2-schema-v1.2.json`](wp2a/step2-schema-v1.2.json) — four outcomes, exhaustive targets, trusted base, all 256 digest bits

## What v1.2 changed

v1.1 claimed expected facts came from "a committed generator" — **none existed** — and the
predicates, temporal semantics, consumption claims and execution states it presented as source
derivation are not derivable from those sources at all. v1.2 splits **generated source facts** from
**registered interpretations**, and commits the generator with `--check` and tests.

Three corrections are substantive, not editorial: BKG containers and the optical member are
`opaque` (identified but not inspectable), not `unresolved`; the optical support key is the **MJD
token inside the member content**, not the filename date; and Q9 no longer makes
`assertion_only_supported` unreachable by construction.

## Two things the contract records that were not obvious

**The two families are consumed at different layers.** Decoded IGS bytes are consumed by
`pin_igs.py` for *content validation*; the scientific intersection derives GNSS support from
*authenticated filenames* and never reads decoded content. The optical `.dat` member is a genuine
scientific input. Treating both as analysis-consumed would have baked a false premise into the
trial. Query Q5 tests exactly this asymmetry.

**The optical member digest is not authenticated here.** The member *path* is
(`optical-inventory-summary.json`: 16,106 samples, `mjd_first` 59631.788542 — the corpus-wide
earliest optical sample, which sets the published 31.17 h gap). No per-member digest or size exists
anywhere in the repository, so `780,292 B / 00cc90d8…` is registered as a **prediction** for step 2
to confirm or refute, not as an expected fact.

## Execution order

1. **Freeze contract, source facts, interpretations, queries, decision tables, mutation cases, Step-2 schema** ✅ *(v1.2; v1.0 and v1.1 rejected)*
2. Write and freeze `run_step2.py`; run Step 2 once from a clean published commit
3. Hand-author four fixtures — 2 models × 2 families
4. One explicitly **non-qualifying** calibration
5. Freeze any repairs in a new candidate
6. One qualifying comparison from a clean checkout, then **stop**

The mutation freeze is two-stage on purpose: the population is frozen now, the executable per-case
recipes after step 3 and before step 4 — because recipes chosen after inspecting the fixtures would
be post-hoc, which is what disqualified the 2026-08-26 exercises.

## Out of scope

No profile amendment, Gate-1 rerun, full ancestry graph, RO-Crate conformance claim, BKG
re-verification, resolver or browser. Any scope change after results are seen creates a new contract
version and restarts the trial under it.
