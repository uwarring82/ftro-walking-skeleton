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
