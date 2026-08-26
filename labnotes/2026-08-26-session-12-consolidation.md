# Session 12 — Consolidation: bounding Phase 0 so it can be finished

**Date:** 2026-08-26 · **Reviews:** commit [`3e6face`](https://github.com/uwarring82/ftro-walking-skeleton/commit/3e6face8afdac3799358936b95baf90a8926b0e0)
**Outcome:** five findings closed **by construction**; the codebase shrank; Phase 0 given a finite exit condition.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[11](2026-08-26-session-11-review-corrections-10.md)
> are left unedited.

---

## 00 — Why this session is different

The reviewer asked why the process would not converge, and answered it better than I had. The
diagnosis, which I accept in full:

1. **Verifier regress.** Every gate is code and needs verifying. Without a declared trusted base,
   "who verifies the verifier?" recurses. At `3e6face` the repository was **73% verification code**
   — 3,311 lines against 1,188 of analysis.
2. **Five finding types entering one ledger with equal weight.** "The result is wrong", "a producer
   emits what its consumer rejects", "I can invent a mutation the tests miss", "a clause has no
   check" and "the provider published no evidence" are not the same thing. Treating them alike made
   progress unreadable and made me report latent mutation gaps with the rhetoric of live defects.
3. **An append-only count can only rise**, so ledger totals could never show convergence. "Execution
   is now the largest class" partly just reflected building more machinery to inspect.
4. **"Proper functionality" was never bounded.** Each round searched further outward — another input
   shape, hidden precondition, maintenance flag or hypothetical mutation — with **no state in which
   the answer could be "done"**.

My own contribution to the loop: I fixed instances rather than classes, and built the fence
precisely around the last hole each time. The absent-field defect appears **eight times** in this
ledger. Every fix was another hand-written `if field not in doc`.

---

## 01 — Consolidation, not more guards

| Change | Effect |
| --- | --- |
| One declarative `schema.py`, applied by producer and consumer | Retires the 8-entry absent-field family at class level |
| `promote()` validates the same declaration the consumer applies | Producer/consumer mismatch **impossible by construction** |
| `series`/`mjd` derived from authenticated filenames | The relabel mutation now has **no effect at all** |
| Domain supports built once and passed in; `build_sensitivity` raises if omitted | Main/sensitivity divergence **impossible**, not policed |
| `per_sample_nominal_credit` sorts its own input | Removing the caller's sort has **no effect** |
| Version state machine → git | **275 → 101 lines**; registry file, `--update`, `--register` and every laundering branch deleted |
| `compute_overlap.py`, `support-intersection.json` deleted | Dead code |

Four of the five findings are now closed by *removal of the possibility* rather than by a check.
That is the difference between this round and the previous nine.

### A consequence worth recording

Deleting files breaks links in append-only notes. Two historical references now dangle:

| Note | Link | Status |
| --- | --- | --- |
| [session 01](2026-08-25-session-01-phase0.md) §09 | `src/ftro/compute_overlap.py` | deleted session 12; superseded by `four_domain_intersection.py` |
| [session 07](2026-08-26-session-07-review-corrections-6.md) §03 | `phase0/evidence/versioned-artifacts.json` | deleted session 12 with the version state machine it served |

The notes are **not** edited: they record what existed at that knowledge time, and that is the
point of the policy. The tombstone above is the reconciliation, and the deletions are recorded in
the decision ledger. A reader following a dead link should land here.

**Net: the codebase got smaller.** −275 lines of state machine, −72 of dead code, −1 registry file,
+112 of schema.

---

## 02 — A convergence measure that can reach zero

Every ledger entry now carries two axes:

- `finding_type` ∈ `current_defect` · `latent_regression` · `assurance_gap` ·
  `external_evidence_gap` · `recorded_outcome`
- `affects` ∈ `changes_result` · `blocks_workflow` · `maintenance_only` · `no_present_effect`

The measure is: **open entries that bear on the Phase-0 result and are software defects** — not
external evidence gaps, not the recorded null.

> **Currently: 0.**

Every remaining result-bearing entry is a provider evidence gap — `ref_osc` absent, no EOP
artifact, `TT(BIPM2020)` versus 2021 — which is the *deliverable*, not a failure. Plus `DEF-023`,
the null itself, now typed `recorded_outcome` because there is nothing to fix.

Retriage totals: 22 `latent_regression`, 17 `external_evidence_gap`, 16 `current_defect`,
7 `assurance_gap`, 1 `recorded_outcome`. Reading that table, the last ten rounds were overwhelmingly
about **faults outside the test contract**, not about the committed result being wrong.

---

## 03 — A finite exit condition

[`phase0/acceptance-contract-v1.0.md`](../phase0/acceptance-contract-v1.0.md) freezes twelve
contracts and, as importantly, states what is **out of scope**: proof that every normative clause
has a check, exhaustive mutation coverage of maintenance commands, independent oracles for
computations other than segmentation, and resistance to arbitrary hand-edits by someone with commit
access.

Those are real. Listing them is what makes Phase 0 finite.

Exit requires: C1–C8 and C10–C12 green from a clean export; C9 executed live once; the convergence
measure at zero; the declared mutation suite detecting its pre-registered fault model; and **two
bounded audits producing no new high-severity current defect**. A latent-regression finding is
filed and deferred — it does not reopen Phase 0.

**Status: 1, 3 and 4 hold. C9 outstanding. One further audit needed.**

---

## 04 — The audit, pre-registered and executed once

[`audit-fault-model-v1.0.md`](../phase0/audit-fault-model-v1.0.md) enumerates thirteen mutation
operators *before* execution, precisely because the previous protocol had an implicit "find five"
stopping rule that cannot terminate.

Result: **13 of 13 behaved as pre-registered. No new findings.**
([`audit-2026-08-26.md`](../phase0/reports/audit-2026-08-26.md).)

Two are recorded as *no effect* or *impossible* rather than *detected*, and that distinction is
deliberate: the defect was removed rather than caught. A mutation that now propagates coherently is
a legitimate parameter change.

**Then the process found something itself.** Running `check_versions.py --check --base HEAD~1`
immediately after committing surfaced `FTRO-DEF-064`: a document that *gains* a version hit an
unguarded branch and raised `AttributeError`. My M12 had enumerated the three cases that came to
mind, not the state machine's transitions.

That is the first finding located by our own pre-registered process rather than by review, and the
first exercise of the amend-then-rerun rule — the fault model is now v1.1.0 with M12a–M12c
enumerated. It is also a small vindication of the reset: a bounded checklist, run and then amended,
caught a real defect and stopped.

One honest caveat, filed rather than claimed: `PULSAR_OBS_START_UTC` is still a hand-written
literal. Single-sourced, but not derived from the pinned `.tim`. Detecting an unauthorised edit to
it is a code-review concern, and the "derive, don't store" treatment is Phase-1 work.

---

## 05 — Method notes to self

- **Fix classes, not instances.** Eight rounds of `if field not in doc` were one missing schema.
- **Prefer removing the possibility to checking for it.** Four of five findings closed by
  construction; those cannot recur.
- **Declare a trusted base or recurse forever.** Deleting the version machine removed four defect
  classes and 174 lines at once.
- **Separate finding types before counting them.** Conflating them made a converging project look
  divergent.
- **Bound the scope, then test the bound.** An unbounded acceptance condition has no "done" state,
  however good the work is.
- **A count that only rises cannot measure progress.**

---

## 06 — Carried forward

Unchanged and genuinely open — and these are the actual remaining Phase-0 work, not verification:

- the downstream VLBI analysis-centre product and IERS EOP series (`unresolved`);
- four depositor question groups and the IPTA upstream report, all unsent;
- **C9**: the documented pipeline has never been run end to end against live providers in one pass.

Phase 1 (four RO-Crate 1.3 manifests) remains unstarted. It has been unstarted for eleven sessions
while the scientific content — same null, same 82.0134 h — did not change. That is the clearest
measure of how far the verification work drifted from the deliverable, and the reason for stopping
it here.
