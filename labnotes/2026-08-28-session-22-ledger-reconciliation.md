# Session 22 — one ledger again: reconciling the Phase-1 supplement

**Date:** 2026-08-28 · **Branch:** `phase1`
**Phase-0 carrier:** `8ddcbfa` (qualified, untouched) · **Gate-1 candidate:** `d0f9e37` (unchanged)
**Outcome:** a machine-readable contradiction removed; one integrity test corrected; two entries added.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 01–21 are unedited. This note records what changed and why.

---

## 00 — The contradiction

`ledgers/deficiency-log.json` is linked from the README as *"everything that is broken."* It is the
canonical, machine-readable answer to "what is still wrong here." It said
`FTRO-P1-DEF-009` — *neither historical bounded audit qualifies as pre-registered* — was **open**,
while `phase0/phase0-qualification-v1.0.md` declared Phase 0 closed on the strength of two
qualifying audits.

Both statements were published. A reader querying the ledger got an open blocker for a phase
announced as closed, and no automated consumer could tell which to believe.

The supplement was documented as pending reconciliation, so this was known bookkeeping rather than
drift. It was still a contradiction in the machine layer, and the machine layer is the product.

## 01 — Two bodies, one version label

Reconciling surfaced a second problem. `FTRO-P1-DEF-008` existed as **v2.0.0 in both files with
different bodies**: the unified copy was written while carrier `354868a` was current and still said
exit condition 2 was open; the supplement's copy was written after qualification. Same id, same
version, different claims.

A version label that does not identify a constraint state identifies nothing — the same finding as
`FTRO-DEF-033`, one layer out. Resolved as **v3.0.0**, one canonical body in both files, with the
divergence recorded in the entry rather than smoothed away.

The supplement's `note` is now a **standing rule** instead of a description of one merge: new
Phase-1 entries open in the supplement; each reconciliation snapshots its committed state to
`ledgers/phase1-deficiency-log-at-<commit>.json`, records that snapshot in the unified ledger's
`merged_sources`, and folds the entries in; earlier snapshots are never rewritten; a divergence
under an unchanged version label is itself a defect.

## 02 — `FTRO-P1-DEF-011`

Writing a status note into `README.md` failed two of 185 tests. `README.md` is the pinned target of
the frozen audit cases `M12c.version-gained` and `M13.consume-before-produce`, and
`test_every_target_digest_is_current` hashed the **working tree** and compared it to the carrier's
frozen digest.

That test was wrong after qualification. The manifest describes carrier `8ddcbfa`, and its own
`c9_rebinding_policy` says evidence publication is *"a descendant record about the qualified
carrier, not a rebound candidate"* — descendants are expected. Resolving frozen targets against
descendant bytes reported a manifest defect that did not exist.

Two repairs were considered and rejected:

- **Re-freeze the two digests.** Changes the qualified instrument while preserving the coupling
  that caused the problem — and quietly re-freezing a pre-registered manifest is exactly what made
  the 2026-08-26 exercises non-qualifying.
- **Point M13 at a fixture copy of the README.** Would test the copy, not the documented pipeline.
  Projection-only verification, again.

The correct fix was to the test's scope. Every `(target, before-digest)` tuple is now verified
against the carrier's own calibration and two qualifying reports, which are asserted to bind commit
`8ddcbfa`, tree `c3e05bdd…` and manifest digest `08f5db20…`. The manifest **file** stays frozen by
digest, so the instrument still cannot drift. The bound-document check carried the identical latent
coupling and got the same treatment.

The live README is constrained separately and deliberately against the working tree, by
`run_c9.extract_pipeline()` and the producer-before-consumer oracle `probes.readme_order()`, reading
`README.md` itself — plus a negative case that reorders the pipeline and confirms the oracle
actually rejects it.

**No manifest, runner or qualification evidence was touched. No requalification. No Gate-1 rerun.**

## 03 — Totals

| | Before | After |
| --- | ---: | ---: |
| entries | 85 | **87** |
| resolved | 56 | **58** |
| open | 29 | **29** |
| self-directed | 60 | **62** |
| convergence predicate | 0 | **0** |

Open stays at 29 because `-010` opens as `-009` closes. The predicate holds at zero: both new
entries are `blocks_workflow`, neither is `changes_result`.

The qualification table keeps **85** and now says so explicitly — that is the carrier `8ddcbfa`
state, and the carrier is not rebound by descendant bookkeeping.

## 04 — Method note to self

**A contradiction between two published records is a defect even when both were written honestly.**
The supplement was documented as pending; that documentation did not stop the canonical ledger from
answering the central question wrongly. Reconcile at the moment of publication, not at the next
convenient boundary.

## 05 — Next

Unchanged: compare alternative encoded/decoded assertion models against a second packaged provider
product, then establish RO-Crate 1.3 validation, then amend profile §5. Phase 2 held.
