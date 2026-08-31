# Session 28 — WP2A v1.3 frozen and reconciled before Step 2

**Date:** 2026-08-31 · **Branch:** `phase2`

**Starting commit:** `734ba0f` · **Outcome:** the executable v1.3 registration is frozen; its
committed Phase-1 supplement is reconciled into the canonical ledger; Step 2 remains unexecuted.

**Licence:** CC BY 4.0

> **Append-only.** Session 27 and registration versions 1.0–1.2 remain unchanged. This note records
> the descendant bookkeeping performed only after the v1.3 carrier existed.

---

## 00 — Frozen subject

Commit `734ba0f` binds the v1.3 scientific registration, exact expected answers, 168 pre-fixture
mutation cases, executable Step-2 schema, checker and runner. Before that commit, the final
instrument audit closed two execution boundaries: a configured upstream must resolve to a
remote-tracking ref before any input access, and both methods consume only anonymous seekable
descriptors populated from the exact authenticated input snapshot. The later pathname rehash is
mutation evidence only.

The runner also exercises the descriptor transport with an FTRO-synthetic sentinel before any
provider pathname opens. Snapshot allocation and method-start failures become typed non-execution
rows. Provider-free tests exercised both decoder pairs and a change-after-capture path mutation.

No Step-2 command, mapping, evaluator or mutation run occurred, and no WP2A provider payload was
opened.

The first full test run after freezing exposed a test-only publication assumption: a synthetic
shape fixture used local `HEAD` while asserting containment in `origin/phase2`. Production rejected
that now-unpushed commit correctly. The fixture now names the actual upstream commit; the
production predicate remains unchanged.

## 01 — Committed-snapshot reconciliation

The committed `phase1/deficiency-log-phase1.json` at `734ba0f` is copied byte-for-byte to
`ledgers/phase1-deficiency-log-at-734ba0f.json`:

- supplement version: 0.10.0;
- entries: 21 (15 resolved, 6 open, all self-directed);
- SHA-256: `3ae9ec050bb8196a4117123bf550a377bf98444d32d1dbb063165d1077ea8472`.

Canonical ledger v0.25.0 replaces each earlier Phase-1 projection with that committed body, adds
`FTRO-P1-DEF-020` and `FTRO-P1-DEF-021`, and retains all six immutable reconciliation sources.
The resulting totals are 97 entries, 68 resolved, 29 open and 72 self-directed. The convergence
predicate remains zero.

This changes no Phase-0 carrier, Gate-1 subject or WP2A trial evidence. It is a descendant record
about the frozen candidate.

## 02 — Stop

The next operation is publication of this descendant on `phase2`, followed by the single registered
Step-2 run from a clean published commit. Fixture and evaluator work remains prohibited unless
Step 2 supports all four registered targets.
