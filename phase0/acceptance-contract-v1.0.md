# Phase-0 Acceptance Contract v1.0

**Document ID:** FTRO-ACC-001 · **Version:** 1.3.0 · **Date:** 2026-08-27 · **Licence:** CC BY 4.0
**Status:** Frozen functional scope; execution qualification pending. Anything not listed here is
Phase 1 or robustness work.

---

## Why this exists

Ten review rounds produced 33 self-directed findings without the discovery rate falling. The
diagnosis is not that the repository is wrong; it is that **"proper functionality" was never
bounded**, so each round searched further outward — another input shape, maintenance flag or
hypothetical mutation — and there was no state in which the answer could be "done".

Three structural causes, recorded so they are not repeated:

1. **Verifier regress.** Every gate is code, and code needs verification. Without a declared
   trusted base the question "who verifies the verifier?" recurses indefinitely. At its peak the
   repository was 73% verification code.
2. **Conflated finding types.** "The result is wrong", "a producer emits what its consumer
   rejects", "I can invent a mutation the tests miss", "a clause has no check" and "the provider
   published no evidence" all entered one ledger with equal rhetorical weight.
3. **Append-only totals cannot show convergence.** The count only rises.

## Trusted computing base

Assumed correct and **not** verified by this repository: the Python standard library, `git`, the
operating system, the shell plus `curl`/`md5`/`unzip` used by the documented live pipeline, and the
providers' own published bytes. C9 and the bounded audit record resolved executable bytes and tool
probes; controller Git is selected from fixed system paths and run with replacement refs disabled.
That is provenance and isolation, not independent verification of the tools. Everything else in
`src/` is in scope for the contracts below.

The version state machine was deleted in favour of `git` for exactly this reason: 275 lines of
bespoke state produced four defects of its own, none of which existed in the thing it replaced.

---

## The contracts

A contract is *satisfied* when the stated command produces the stated outcome from its declared
clean environment. C1–C8 and C10–C12 are exercised by the network-free suite from a clean
`git archive`; C9 uses a clean detached Git checkout because its documented version gate
deliberately fails closed without Git metadata.

| # | Contract | Verified by |
| --- | --- | --- |
| C1 | In its default mode, every pinner refuses to fetch any artifact whose digest is not recorded in `phase0/evidence/expected-digests.json`, and refuses any malformed digest in **all** modes. `--allow-unpinned` is an explicit first-pin escape and is out of C1's scope by construction | `pinning.preflight`; `TestPreflightDigestValidation` |
| C2 | A retrieval that fails validation or digest promotes no report, mints no identity and caches no bytes | `pinning.promote`; `TestPinnerEndToEnd` |
| C3 | Every committed pin report satisfies one declared schema, checked by the producer before promotion and by the consumer before use | `schema.PIN_REPORT`; `TestConsumerGate` |
| C4 | The four-domain computation refuses any report that is not a clean success, and binds pins to the registry by name and digest | `pinning.assert_report_usable`; `TestConsumerGate` |
| C5 | Scientific meaning is derived from authenticated names, never read from unbound report fields | `igs_day_from_name`; relabel mutation has no effect |
| C6 | The **non-optical** domain supports (pulsar, VLBI, GNSS) have one construction, passed from the main computation into the sensitivity scan, which raises if they are omitted. Optical support is constructed per variant by design — varying it *is* the scan. Main and sensitivity are reconciled two-sidedly at the shipped convention for every domain, pair, triple, four-way result and gap | `main_vs_sensitivity_reconciliation`; run fails on disagreement |
| C7 | Optical segmentation agrees with an implementation that shares no code with it, tuple for tuple, at every tolerance and at each threshold T and T+1 | `independent_runs`; `TestSegmentationOracle` |
| C8 | Step 2, the tracked optical summary produced within step 3, and steps 5–6 reproduce their committed outputs byte-for-byte from the same pinned inputs. The pin reports produced by retrieval steps 1 and 4 are **not** byte-deterministic — they stamp `retrieved_utc` — and are covered by C1 and C2 instead | README steps 2, 3, 5–6; determinism check |
| C9 | Every documented command in the README runs to completion, in order and without intervention, from a clean detached Git checkout against live providers | recorded live run, per release |
| C10 | A changed versioned artifact declares a new, forward version, and the gate **fails closed** when no git context is available rather than reporting success | `check_versions.py --check`; `TestVersionGate` |
| C11 | Every deficiency carries a machine-readable finding type and impact axis | `deficiency-log.json`; renderer |
| C12 | No entry is simultaneously open, `affects == changes_result` and `finding_type == current_defect` | the convergence measure derived from the merged machine ledger |

**Explicitly out of scope for Phase 0:** proof that every normative profile clause has an
executable check; exhaustive mutation coverage of maintenance commands; independent oracles for
computations other than optical segmentation; resistance to arbitrary hand-edits of committed
artifacts by an actor with write access.

Those are real and some are worth doing. They are Phase 1 or later, and listing them here is what
makes Phase 0 finite.

---

## Exit condition

Phase 0 is complete when all of the following hold, and not before:

1. **C1–C8 and C10–C12 pass** from a clean `git archive` export.
2. **C9** has been executed end to end at least once against live providers, and its result
   recorded.
3. **The convergence measure reads zero**: no open ledger entry both bears on the scientific
   conclusion and is a software defect rather than an external evidence gap or the recorded
   outcome itself.
4. **The frozen executable mutation manifest behaves as registered:** rejected mutations are
   detected; registered no-effect/coherent/accepted mutations are observed without conflating
   them with a recipe that did not execute. See the semantic model in
   [`phase0/audit-fault-model-v1.0.md`](audit-fault-model-v1.0.md) and the frozen recipes in
   [`phase0/audit/execution-manifest-v1.0.json`](audit/execution-manifest-v1.0.json).
5. **Two bounded audits against this frozen scope produce no new high-severity current defect.**
   A latent-regression finding does not reopen Phase 0; it is filed and deferred.

**Status at v1.3** (first live execution, 2026-08-27):

The first retrospective exercise found failures on C3, C8, C10 and M11 and produced two scope
corrections (C1, C6). Those failures were fixed before v1.2, but neither historical exercise
counts toward exit condition 5.

The two 2026-08-26 exercises are retained as retrospective diagnostics. Neither qualifies as a
pre-registered audit: the first fault model and its result were committed together, and run 2
selected cases after observing run 1. The historical claim that condition 4 held and that one of
two audits qualified was therefore false.

Carrier `354868a` demonstrated condition 1 with 175 tests and zero skips from a literal clean
archive. Its live C9 report then exposed a recorder defect (`FTRO-DEF-074`), so it was rejected.
**Condition 1 must be demonstrated again for the replacement carrier**; evidence does not transfer
between carrier trees.
**Condition 3 holds after reconciling all nine entries from the Phase-1 source ledger:** the exact
merged-ledger convergence predicate returns zero.

**2 (C9) is outstanding.** The first actual live attempt completed steps 0–3, then the BKG IGS
route refused all 57 TCP connections in step 4. The report classified reachability without
inferring an access class, and calibration did not start. The replacement carrier adopts the
reachable official SIO/GARNER route as explicit new retrieval snapshots for three byte-distinct,
decoded-identical `.Z` containers (`FTRO-DEF-075`).

**4 is not yet demonstrated.** An executable manifest is prepared but has not yet been calibrated
or executed from its committed carrier.

**5 stands at 0/2.** One non-qualifying calibration run must establish that every frozen recipe
applies, executes and resets; the unchanged manifest must then pass twice in separate clean
checkouts. Calibration never counts.

---

## What a finding means from here

| Finding type | Effect on Phase 0 |
| --- | --- |
| `current_defect` bearing on the result | **Blocks.** Fix before exit. |
| `current_defect` that makes one of C1–C12 fail | **Blocks.** Fix before exit. |
| `current_defect` blocking a provider-controlled or later-phase workflow outside C1–C12 | Filed; it does not block this bounded Phase-0 exit. |
| `current_defect`, maintenance only | Filed; fix if cheap, otherwise defer. |
| `latent_regression` | **Does not block.** Filed against the fault model for Phase 1. |
| `assurance_gap` | **Does not block.** Listed as out of scope above. |
| `external_evidence_gap` | **Never blocks.** This is the deliverable. |
| `recorded_outcome` | Not a defect. |

This is the change that makes the process terminable: a mutation nobody has performed against
committed code is a Phase-1 concern, not a Phase-0 failure.
