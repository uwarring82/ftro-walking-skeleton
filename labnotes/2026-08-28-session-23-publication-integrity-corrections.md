# Session 23 — authenticating the carrier evidence and its publication views

**Date:** 2026-08-28 · **Branch:** `phase1`
**Phase-0 carrier:** `8ddcbfa` (qualified, untouched) · **Gate-1 candidate:** `d0f9e37` (unchanged)
**Outcome at this checkpoint:** three publication defects corrected in the Phase-1 supplement;
canonical reconciliation deliberately follows in a second commit.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 01–22 are unedited. This note corrects their later interpretation and
> records a checkpoint-before-reconciliation sequence explicitly.

---

## 00 — chronology correction for session 22

Session 22 was added by checkpoint commit `f1837d4`. Its prose described the reconciliation and
87-entry totals as complete, but the canonical fold, immutable supplement snapshot and
qualification-status editorial update landed only in the following commit, `bb76154`.

The final two-commit outcome was correct; the narrative was one commit early. This note records the
actual order rather than editing session 22:

1. `f1837d4` froze the supplement and the note that described the intended fold;
2. `bb76154` copied that exact committed supplement with `git show`, reconciled the canonical
   ledger and published the resulting views.

This session follows the order literally. The commit containing this note is the new supplement
checkpoint. A later commit will snapshot and reconcile it; no claim in this note depends on that
later commit already existing.

## 01 — the carrier-relative test trusted an unauthenticated projection

The first `FTRO-P1-DEF-011` repair stopped comparing frozen target digests with descendant
working-tree bytes. It then read the carrier's calibration and two qualifying reports and checked
selected fields — but never authenticated the report files themselves.

A same-size mutation of an unchecked calibration field could therefore keep the selected
projection unchanged while changing the qualified report digest. The focused audit tests and
crate-size check could remain green. The version-policy gate rejects an unbumped dirty edit, but a
permitted forward version declaration can satisfy that policy without authenticating immutable
bytes. The published qualification table already carried the necessary five SHA-256 values; no
executable test consumed them.

`FTRO-P1-DEF-011` is corrected at v2.0.0. The test now:

- pins the exact C9, calibration, two qualifying and final qualification JSON byte digests;
- authenticates the final qualification JSON before trusting its embedded evidence hashes;
- cross-checks the five-value mapping against the qualification-status Markdown table;
- parses carrier fields and mutation tuples only after the byte check; and
- includes a same-size run-id mutation that must fail the digest binding.

No file under `phase0/audit/` changed.

## 02 — `refresh_crate --check` could not discover an omission

The root crate omitted the new reconciliation snapshot and session-22 note while reporting
`0 stale, 0 missing`. The checker iterated only graph entities already present, so a new file absent
from the graph was outside its observable population. This is `FTRO-P1-DEF-012`.

The bounded discovery rule is now executable for two authored-document populations:

- every `labnotes/*.md` file;
- every `ledgers/*.json` and `ledgers/*.md` file.

Each must be both a graph entity and a root Dataset `hasPart`. The refresh command can add missing
declarations deterministically; an independent test enumerates the same filesystem populations.
This also brings the previously isolated Phase-1 sessions 13–16 into the integrated root crate.

## 03 — the Gate-1 live command implied the wrong checkout

The SIO report and surrounding prose correctly bind Gate 1 to candidate `d0f9e37`, but the command
block said only to run from a clean checkout "after publication". Current branch head `bb76154` is
correctly ineligible: descendant status, test, qualification and ledger changes lie outside the
candidate's publication allowlist.

`FTRO-P1-DEF-013` records the documentation defect. The live command now requires a detached
checkout of full commit `d0f9e3728e26fff423237b896e9b8ce79feca5bd`. Report freshness may still
be checked from the descendant; live reproduction and historical report verification are separate
operations.

## 04 — scope and next boundary

These corrections change neither the Phase-0 result nor either immutable subject. They require no
live provider retrieval and no Phase-0 requalification. After this checkpoint is committed, the
supplement will be snapshotted and folded into the canonical ledger under the standing two-commit
rule.

The next scientific/model task remains unchanged: compare alternative encoded/decoded assertion
models against another packaged provider product, then establish normative RO-Crate 1.3 validation
before amending profile §5. Phase 2 remains held.
