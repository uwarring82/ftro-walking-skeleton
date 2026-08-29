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

> **Read [`REGISTRATION-STATUS.md`](wp2a/REGISTRATION-STATUS.md) first.** Version **1.0.0 was
> rejected before step 2** and is retained byte-unchanged; **1.1.0 is current**. No step of the
> trial was ever executed under v1.0.

- [`contract-v1.1.md`](wp2a/contract-v1.1.md) — scope, three axes, oracle, decision tables; §0 tabulates all ten v1.0 defects
- [`expected-facts-v1.1.json`](wp2a/expected-facts-v1.1.json) — **derived** from four pinned oracle sources
- [`queries-v1.1.json`](wp2a/queries-v1.1.json) — 11 queries with machine-readable applicability, cardinality and pass rule
- [`mutation-population-v1.1.json`](wp2a/mutation-population-v1.1.json) — 11 operators, **76 exhaustive cases**, 4 fixture requirements

## What v1.1 changed

v1.0 was mechanically sound and structurally unable to run. The decisive one: **no query tested
addressability**, so M2 could return an output digest as a literal and pass every other query
without ever giving the consumed state an addressable identity — the question the trial exists to
answer. **Q9** now asks it directly. The other nine defects and their repairs are tabulated in
[`contract-v1.1.md`](wp2a/contract-v1.1.md) §0 and recorded as `FTRO-P1-DEF-015`.

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

1. **Freeze contract, expected facts, queries, decision tables, mutation population** ✅ *(v1.1; v1.0 rejected)*
2. Durable input-evidence report — independent `zipfile` / `unzip -p` / Unix-compress cross-checks
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
