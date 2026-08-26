# Phase-0 Acceptance Contract v1.0

**Document ID:** FTRO-ACC-001 · **Version:** 1.0.0 · **Date:** 2026-08-26 · **Licence:** CC BY 4.0
**Status:** Frozen scope for Phase 0. Anything not listed here is Phase 1 or robustness work.

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

Assumed correct and **not** verified by this repository: the Python standard library, `git`,
the operating system, and the providers' own published bytes. Everything else in `src/` is in
scope for the contracts below.

The version state machine was deleted in favour of `git` for exactly this reason: 275 lines of
bespoke state produced four defects of its own, none of which existed in the thing it replaced.

---

## The contracts

A contract is *satisfied* when the stated command produces the stated outcome from a clean
export. Each is executable.

| # | Contract | Verified by |
| --- | --- | --- |
| C1 | Every pilot artifact is pinned by a digest recorded in `phase0/evidence/expected-digests.json`, and each pinner refuses to fetch anything not covered there | `pinning.preflight`; `TestPreflightDigestValidation` |
| C2 | A retrieval that fails validation or digest promotes no report, mints no identity and caches no bytes | `pinning.promote`; `TestPinnerEndToEnd` |
| C3 | Every committed pin report satisfies one declared schema, checked by the producer before promotion and by the consumer before use | `schema.PIN_REPORT`; `TestConsumerGate` |
| C4 | The four-domain computation refuses any report that is not a clean success, and binds pins to the registry by name and digest | `pinning.assert_report_usable`; `TestConsumerGate` |
| C5 | Scientific meaning is derived from authenticated names, never read from unbound report fields | `igs_day_from_name`; relabel mutation has no effect |
| C6 | Main and sensitivity computations share one construction of every domain support, and are reconciled at the shipped convention for every domain, pair, triple, four-way result and gap | `main_vs_sensitivity_reconciliation`; run fails on disagreement |
| C7 | Optical segmentation agrees with an implementation that shares no code with it, tuple for tuple, at every tolerance and at each threshold T and T+1 | `independent_runs`; `TestSegmentationOracle` |
| C8 | The deterministic stages reproduce their committed outputs byte-for-byte from the same inputs | README step 6; determinism check |
| C9 | Every documented command in the README runs to completion from a clean export | manual, per release |
| C10 | A changed versioned artifact declares a new, forward version | `check_versions.py --check` |
| C11 | Every deficiency carries a machine-readable finding type and impact axis | `deficiency-log.json`; renderer |
| C12 | No open entry that could change the Phase-0 scientific conclusion is a software defect | the convergence measure in the rendered ledger |

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
4. **The declared mutation suite detects its pre-registered fault model** (see
   [`phase0/audit-fault-model-v1.0.md`](audit-fault-model-v1.0.md)).
5. **Two bounded audits against this frozen scope produce no new high-severity current defect.**
   A latent-regression finding does not reopen Phase 0; it is filed and deferred.

Status at v1.0: 1, 3 and 4 hold. 2 is outstanding. 5 requires one further audit.

---

## What a finding means from here

| Finding type | Effect on Phase 0 |
| --- | --- |
| `current_defect` bearing on the result | **Blocks.** Fix before exit. |
| `current_defect` blocking a documented workflow | **Blocks.** Fix before exit. |
| `current_defect`, maintenance only | Filed; fix if cheap, otherwise defer. |
| `latent_regression` | **Does not block.** Filed against the fault model for Phase 1. |
| `assurance_gap` | **Does not block.** Listed as out of scope above. |
| `external_evidence_gap` | **Never blocks.** This is the deliverable. |
| `recorded_outcome` | Not a defect. |

This is the change that makes the process terminable: a mutation nobody has performed against
committed code is a Phase-1 concern, not a Phase-0 failure.
