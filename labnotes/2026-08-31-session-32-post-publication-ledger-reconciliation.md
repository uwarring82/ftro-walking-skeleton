# Session 32 — closing the post-publication ledger interval

**Date:** 2026-08-31 · **Branch:** `phase2` · **Task:** reconcile the committed Phase-1 supplement
**Outcome:** `FTRO-P1-DEF-023` folded into the canonical ledger
**Licence:** CC BY 4.0

---

## 00 — Why this reconciliation was required

Commit `29782674079de4e650bd4b035152ee72c8b71c37` published the immutable WP2A Step-2 report and
added resolved entry `FTRO-P1-DEF-023` to the Phase-1 working supplement. The same commit retained
the canonical ledger at its preceding `1d4bc31` snapshot. That left the supplement at 23 Phase-1
entries while the canonical ledger carried 22.

No open defect was hidden, and the Step-2 result was unaffected, but the state violated the
supplement's standing rule: each committed interval is snapshotted and folded into the canonical
ledger, while earlier snapshots remain immutable.

## 01 — Committed-source snapshot

The exact bytes of `phase1/deficiency-log-phase1.json` at `2978267` are retained as
`ledgers/phase1-deficiency-log-at-2978267.json`:

- source commit: `29782674079de4e650bd4b035152ee72c8b71c37`;
- supplement version: `0.13.0`;
- entries: 23; and
- SHA-256: `6ce142a7012d1821af2d6b2e7b16d3c28236a2feeab86b0798c0d3965d0a4a0d`.

The snapshot is byte-identical to `git show
29782674079de4e650bd4b035152ee72c8b71c37:phase1/deficiency-log-phase1.json`. Every Phase-1 body
in the canonical ledger matches that source after removing only the canonical `source_ledger`
binding.

## 02 — Canonical state

Unified ledger v0.27.0 now carries:

| Measure | Value |
| --- | ---: |
| all entries | 99 |
| resolved | 70 |
| open | 29 |
| self-directed | 74 |
| result-bearing open software defects | **0** |
| retained Phase-1 merge sources | 8 |

`FTRO-P1-DEF-023` remains resolved. It records that three runner tests depended on the official
report being absent; after publication, one errored and two passed against the wrong guard because
they asserted only a broad exception type. The repair gave each branch test an isolated output path
and a branch-specific diagnostic, plus a separate immutable-output test.

## 03 — Evidence boundary

This is descendant ledger publication only. It does not rebind or rerun Step 2:

- Step-2 subject remains `1d4bc31c6e73bec9e1717e64d5c09e526b75b64b`;
- report SHA-256 remains
  `67111c699372237192588771332ff14704279a6dd8fbaf0f60ee356f63bf725c`;
- registration-manifest SHA-256 remains
  `703b655078d0ff55c71462c7c931b20369bc01e0eba380818487f4265375868c`;
- all four targets remain `support`; and
- no provider input or manifest-bound instrument file changed.

## 04 — Next boundary

WP2A contract §9 step 4 remains next: freeze and synthetic-test the evaluator before any real
fixture exists. Its pre-fixture tests must demonstrate rejection of each registered wrong-answer,
malformed-evidence and assurance-failure branch; a green baseline alone cannot establish that the
evaluator exercises the branch named by a test.

The self-test population, expected branch diagnostics and pass rule must therefore be frozen in a
machine-readable binding before the evaluator is implemented. Otherwise step 4 would still permit
post-hoc selection of whichever synthetic cases the implementation already passes.

## 05 — Verification and one read-only command error

The publication gate passed with 253 main tests and 48 Phase-1 tests, all five v1.3 generators,
both Step-2 checkers, Gate-1 structure and report freshness, the version gate and root-crate
completeness.

An initial immutable-diff command included the Step-2 report in a comparison against `1d4bc31`,
where that not-yet-published file correctly did not exist. Git displayed the complete report as an
addition and exited non-zero. The command was read-only. The corrected checks use separate
baselines: manifest-bound instrument bytes against `1d4bc31`, the report and live supplement
against `2978267`, and `phase0/` against `2978267`.
