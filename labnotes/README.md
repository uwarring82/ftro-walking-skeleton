# Lab Notes

Append-only working record of the FTRO walking skeleton.

## Conventions

- **One file per working session**, named `YYYY-MM-DD-session-NN-<topic>.md`.
- **Append-only.** Entries are never rewritten. A conclusion that later proves wrong is
  corrected by a *new* entry that links back, not by editing the original. This mirrors
  the project's own bitemporal rule: the record of what we believed at a knowledge time
  is itself data.
- **Every factual claim carries its evidence** — a command, a file path with a checksum,
  or a generated report. A claim without a route to reproduce it does not belong here.
- **Dead ends are recorded.** A retrieval that failed, a hypothesis that collapsed and a
  wrong turn are all findings; §17 of the task card treats them as citable outputs.
- Lab notes are **CC BY 4.0**, like all FTRO-authored documentation.

## Relationship to the ledgers

Lab notes are *narrative and chronological*: what was tried, in what order, and why.
The ledgers are *structured and current*:

| Want | Read |
| --- | --- |
| What happened, and how we got here | `labnotes/` |
| The classified list of every deficiency found | [`ledgers/deficiency-log.md`](../ledgers/deficiency-log.md) |
| Who may reuse what | [`ledgers/rights-ledger.md`](../ledgers/rights-ledger.md) |
| Which artifacts are pinned, and to what | [`ledgers/source-ledger.md`](../ledgers/source-ledger.md) |
| Why a choice was made | [`ledgers/decision-ledger.md`](../ledgers/decision-ledger.md) |

A finding usually appears **first** in a lab note, then is promoted into a ledger entry
with a stable ID. The lab note keeps the reasoning; the ledger keeps the claim.

## Sessions

| Date | Session | Topic |
| --- | --- | --- |
| 2026-08-25 | 01 | [Phase 0 — evidence lock, bootstrap ledger and selection](2026-08-25-session-01-phase0.md) |
| 2026-08-25 | 02 | [External review — corrections and self-directed deficiencies](2026-08-25-session-02-review-corrections.md) |
| 2026-08-25 | 03 | [Second external review — a rule written and broken in the same commit](2026-08-25-session-03-review-corrections-2.md) |
| 2026-08-25 | 04 | [Third external review — checks that said more than they executed](2026-08-25-session-04-review-corrections-3.md) |
| 2026-08-25 | 05 | [Fourth external review — projection-only verification](2026-08-25-session-05-review-corrections-4.md) |
| 2026-08-26 | 06 | [Fifth external review — the fix reproduced the defect inside the fix](2026-08-26-session-06-review-corrections-5.md) |
| 2026-08-26 | 07 | [Sixth external review — the boundary, not another layer](2026-08-26-session-07-review-corrections-6.md) |
| 2026-08-26 | 08 | [Seventh external review — a wrong number, published, past every gate](2026-08-26-session-08-review-corrections-7.md) |
| 2026-08-26 | 09 | [Eighth external review — a regression test that could not fail](2026-08-26-session-09-review-corrections-8.md) |
| 2026-08-26 | 10 | [Ninth external review — an oracle that measured the wrong thing](2026-08-26-session-10-review-corrections-9.md) |
| 2026-08-26 | 11 | [Tenth external review — a fixture that could not see the boundary](2026-08-26-session-11-review-corrections-10.md) |
| 2026-08-26 | 12 | [Consolidation — bounding Phase 0 so it can be finished](2026-08-26-session-12-consolidation.md) |
| 2026-08-26 | 13 | [Phase 1 — four hand-authored manifests](2026-08-26-session-13-phase1-manifests.md) *(branch `phase1`)* |
| 2026-08-26 | 14 | [Boundaries executed — C9 fails, Gate 1 source location passes](2026-08-26-session-14-boundaries-executed.md) *(branch `phase1`)* |
| 2026-08-26 | 15 | [Independent verification corrections — audit reset and durable Gate-1 witnesses](2026-08-26-session-15-independent-verification-corrections.md) *(branch `phase1`)* |
| 2026-08-26 | 16 | [Published-carrier hardening and committed Gate-1 witness](2026-08-26-session-16-committed-gate1-witness.md) *(branch `phase1`)* |
| 2026-08-27 | 17 | [Phase-0 closure instrument preparation](2026-08-27-session-17-phase0-closure-preparation.md) |
| 2026-08-27 | 18 | [First closure carrier rejected by its clean-archive gate](2026-08-27-session-18-first-carrier-rejected.md) |
| 2026-08-27 | 19 | [First live C9 rejected; provider containers separated from decoded content](2026-08-27-session-19-first-live-c9-rejected.md) |
| 2026-08-27 | 20 | [Phase 0 qualified and closed](2026-08-27-session-20-phase0-qualified.md) |
| 2026-08-27 | 21 | [Phase 1 rebased to the qualified SIO carrier](2026-08-27-session-21-phase1-sio-rebaseline.md) |
| 2026-08-28 | 22 | [One ledger again — reconciling the Phase-1 supplement](2026-08-28-session-22-ledger-reconciliation.md) |
| 2026-08-28 | 23 | [Authenticating carrier evidence and its publication views](2026-08-28-session-23-publication-integrity-corrections.md) |
| 2026-08-28 | 24 | [Phase 2 opens — WP2A pre-registered before any mapping](2026-08-28-session-24-wp2a-preregistration.md) |
| 2026-08-29 | 25 | [WP2A v1.0 rejected before step 2; v1.1 issued](2026-08-29-session-25-wp2a-v1-rejected.md) |
| 2026-08-30 | 26 | [WP2A v1.1 rejected — generated facts split from registered judgement](2026-08-30-session-26-wp2a-v11-rejected.md) |
| 2026-08-31 | 27 | [WP2A v1.2 rejected — the runner's choices moved into v1.3](2026-08-31-session-27-wp2a-v12-rejected.md) |
| 2026-08-31 | 28 | [WP2A v1.3 frozen and reconciled before Step 2](2026-08-31-session-28-wp2a-v13-ledger-reconciliation.md) |
| 2026-08-31 | 29 | [WP2A v1.3.1 — binding the imported claim to its evidential limit](2026-08-31-session-29-wp2a-v131-provenance-bound.md) |
| 2026-08-31 | 30 | [WP2A v1.3.2 — the input that made its clean carrier dirty](2026-08-31-session-30-wp2a-v132-clean-input-path.md) |
| 2026-08-31 | 31 | [WP2A Step 2 supports, within its registered provenance bound](2026-08-31-session-31-wp2a-step2-supports.md) |
