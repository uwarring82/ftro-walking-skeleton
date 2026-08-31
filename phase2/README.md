# Phase 2 — reference-ancestry graph

Branch `phase2`, from `main` @ `e123a81` (Phase 0 closed, Phase 1 Gate 1 passed).

| Work package | Status |
| --- | --- |
| **2A — Representation Identity Trial** | **v1.3.2 Step 2 `supports` at carrier `1d4bc31`; evaluator not frozen** |
| 2B+ — profile amendment, ancestry materialisation, query fixtures | not started; held behind 2A |

## WP2A in one paragraph

`FTRO-P1-DEF-010` records that snapshot identity does not distinguish encoded retrieval bytes from
decoded product bytes: three IGS products serve different container bytes at SIO than at BKG while
decoding identically. WP2A compares exactly two representations of that fork against exactly two
product families, using neutral questions fixed before either mapping exists. It reports which, if
either, a registered requirement separates — and reports **equivalence** rather than choosing
aesthetically when both pass.

> **Read [`REGISTRATION-STATUS.md`](wp2a/REGISTRATION-STATUS.md) first.** Versions **1.0.0–1.2.0
> were rejected before Step 2** and remain byte-unchanged; **1.3.2 is current**. Its instrument is
> bound, and its single Step-2 execution supports all four registered targets. No mapping,
> evaluator or mutation run has occurred.

- [`contract-v1.3.md`](wp2a/contract-v1.3.md) — scope, model semantics, total decision function and execution order
- [`source-facts-v1.3.json`](wp2a/source-facts-v1.3.json) — authenticated source projection; constructed join keys are explicitly separate
- [`prior-observation-v1.3.json`](wp2a/prior-observation-v1.3.json) — imported optical digest/size claim, without an immutable external locator
- [`interpretations-v1.3.json`](wp2a/interpretations-v1.3.json) — curated states, transformations, assertions, temporal bounds and code readings
- [`queries-v1.3.json`](wp2a/queries-v1.3.json) — 11 queries, direct answer pointers and a model-relation-aware decision function
- [`expected-answers-v1.3.json`](wp2a/expected-answers-v1.3.json) — exact normalized records generated before fixtures, with only two bound Step-2 time tokens unresolved
- [`mutation-cases-v1.3.json`](wp2a/mutation-cases-v1.3.json) — **168 enumerated pre-fixture cases**, exact fields, plus exact-set R11
- [`step2-schema-v1.3.json`](wp2a/step2-schema-v1.3.json) — executed report schema, four authenticated byte snapshots, postflight pathname-mutation evidence and ordered outcomes
- [`registration-manifest-v1.3.json`](wp2a/registration-manifest-v1.3.json) — immutable digest binding for the registration, checker and runner
- [`step2-input-evidence-v1.3.json`](wp2a/reports/step2-input-evidence-v1.3.json) — immutable supporting report bound to carrier `1d4bc31` and manifest SHA-256 `703b6550…5868c`

## Why v1.3 exists

v1.2 passed its mechanical checks but still left the future runner to supply scientific and
assurance choices. It registered only 60 digest bits for the optical member, called an already
parsed member `opaque`, dated knowledge before verification, described M2 in a way Q9 could not
satisfy honestly, omitted complete transformation records, and left mutation and outcome choices
in prose. Its “verbatim” generator also minted identities and conclusions that were not source
values.

v1.3 makes those boundaries executable. Literal source values carry exact pointers; constructed
keys and curated interpretations identify themselves. The optical member is `resolvable` while its
verification remains `indeterminate` and the new procedure `not_attempted`. The complete imported
digest claim is a reproduction target—not provider attestation or an independently timestamped
external record—and observed bytes can never populate an expected field. Exact normalized answers
are frozen before any fixture; fixtures may contain only raw graph data.

## Two things the contract records that were not obvious

**The two families are consumed at different layers.** Decoded IGS bytes are consumed by
`pin_igs.py` for *content validation*; the scientific intersection derives GNSS support from
*authenticated filenames* and never reads decoded content. The optical `.dat` member is a genuine
scientific input. Treating both as analysis-consumed would have baked a false premise into the
trial. Query Q5 tests exactly this asymmetry.

**The optical member digest is an imported claim, not provider-authenticated evidence here.** The
path is authenticated by the inventory (16,106 samples, `mjd_first` 59631.788542). A complete
earlier claim—780,292 bytes and full SHA-256—is now durably registered inside Git as an
authentication/reproduction target. The external exchange has no immutable locator or signature,
so its earlier chronology cannot be independently audited. Step 2 may support or contradict the
value; a match is not provider attestation. The same member was already present at a gitignored
path when v1.3.1 was registered. Repository evidence does not bind the present copy to its original
extraction; the qualified C9 independently extracted the same selector in an isolated checkout and
then deleted it. Every Step-2 report therefore carries an explicit bound: support proves
cross-extractor byte agreement and reproduction, not an independent origin for the expected digest
or size.

The single Step-2 execution authenticated all four outer inputs, observed no post-authentication
path change, and returned four supporting target rows. For the optical member, Python `zipfile` and
system `unzip -p` agreed byte-for-byte and reproduced `00cc90d8…5363c067`, 780,292 bytes. The report
itself carries the limitation above; `step2_supports` is not a stronger provenance claim.

## Execution order

1. Freeze the v1.3 scientific and execution registration ✅
2. Write, test and bind `run_step2_v1_3.py` without opening provider payloads ✅
3. Publish the bound candidate; run Step 2 once from that clean published commit ✅ (`supports`)
4. Freeze the evaluator before any fixture exists **next**
5. Hand-author four fixtures — 2 models × 2 families
6. Freeze exact mutation recipes; run one explicitly **non-qualifying** calibration
7. Freeze any repairs as a new candidate/version where required
8. One qualifying comparison from a clean checkout, then **stop**

The mutation freeze is two-stage on purpose: the population is frozen now, the executable per-case
recipes after step 3 and before step 4 — because recipes chosen after inspecting the fixtures would
be post-hoc, which is what disqualified the 2026-08-26 exercises.

## Out of scope

No profile amendment, Gate-1 rerun, full ancestry graph, RO-Crate conformance claim, BKG
re-verification, resolver or browser. Any scope change after results are seen creates a new contract
version and restarts the trial under it.
