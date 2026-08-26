# Session 07 — Sixth external review: the boundary, not another layer

**Date:** 2026-08-26 · **Reviews:** commit [`99fe720`](https://github.com/uwarring82/ftro-walking-skeleton/commit/99fe720fb79baefb734994424bf6d1a30705c6be)
**Outcome:** scientific null untouched; three entries reopened again, one revised; 39 → 57 tests.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[06](2026-08-26-session-06-review-corrections-5.md)
> are left unedited.

---

## 00 — The gate I built to enforce versioning could not detect a version problem

`check_versions.py` stored `set_at: "HEAD"` and never used it. It compared each document's
declared version against a **hard-coded copy of the same string** — so the two agreed by
construction, and changing content without bumping passed. A working-tree change produced a
*note*, not a failure. No test invoked it.

The commit that introduced it demonstrated the miss: `identities.json` changed its vgosDB retrieval
time and `optical-validity-intervals.md` changed its spacing evidence, neither bumped, and the
latter was not even registered.

Rebuilt on **content digests** recorded when each version was set, in
[`versioned-artifacts.json`](../phase0/evidence/versioned-artifacts.json). Twelve artifacts
registered; `--update` re-records after a deliberate bump. Both failure modes are now tested
against a copied tree:

```
STALE ledgers/source-ledger.md: content changed but version is still 0.4.0:
      recorded deb254459453, now 2f2821ffcd8c
```

→ [`FTRO-DEF-033`](../ledgers/deficiency-log.md#ftro-def-033) **v4.0.0**, D-051.

---

## 01 — Missing expectations could still reach a scientific result

The worst finding, because it crossed from bookkeeping into the science path.

`pin_igs.py` checked registry coverage **after** `cache()` and pin construction. With an uncovered
expectation it exited 1 — having already cached all 57 files, emitted a snapshot with null
expectation fields, and **written the failed report to the official path**. And
`four_domain_intersection.py` read that report without checking `n_failed`,
`retrieval_validation`, `n_without_expected_digest` or per-pin checksum state. A failed pinning run
produced normal GNSS support.

The other three pinners had matching holes: PPTA accepted a missing individual expectation, vgosDB
succeeded with **no expectation at all**, and the evidence pinner fell back to source-code literals
when a registry key was absent — which is how `tintervals` had appeared to work.

`src/ftro/pinning.py` now holds the contract, and all four pinners use it:

| Rule | |
| --- | --- |
| **Preflight** | registry coverage is checked before any byte is fetched |
| **Atomic promotion** | the report reaches the official path only on complete success; a failure is preserved as `.rejected` and the official path is untouched |
| **No expectation, no identity** | a missing expectation is a failure, not a null field |

Plus `assert_report_usable()` as the consumer gate. Verified:

```
preflight: 1 of 57 IGS artifacts have no expected digest in the registry:
['igs21980.sp3.Z']. Nothing was fetched.
  official report unchanged: YES        stray .part files: 0
four_domain_intersection.py on a report with n_failed=3 → exit 1
```

→ [`FTRO-DEF-031`](../ledgers/deficiency-log.md#ftro-def-031) **v4.0.0**, D-048–D-050.

---

## 02 — My mutation table proved things no test asserted

Session 06 ran five mutations by hand, published the table, and called the reconciliation verified.
A manual table is not a test. The reviewer then found six fail-open branches the table had not
covered, and a **combined vgosDB mutation** — null expectation and checksum state, invalid
retrieval time, changed snapshot kind, deleted §5.1 fields — that passed the entire 39-test suite.

Every branch closed:

| Was | Now |
| --- | --- |
| `retrieved_utc` equality skipped entirely | must parse as ISO-8601 on **both** sides |
| §5.1 checked only if the *report* said `ftro_composed` | `snapshot_kind` must **agree with the manifest** first |
| digest test never compared report ↔ registry | `expected_sha256` must **equal** the registry digest |
| vgosDB enforcement explicitly skipped | vgosDB included |
| missing top-level validation permitted as `None` | must declare `content_validated`, no failures, no uncovered expectations |

And the table itself is now **twelve committed tests** in `TestMutationsAreDetected`, each copying
the committed views into a temporary tree, mutating one, and asserting the suite rejects it —
including the exact combined mutation that used to pass. **57 tests, zero skips.**

→ [`FTRO-DEF-035`](../ledgers/deficiency-log.md#ftro-def-035) **v3.0.0**, D-052.

---

## 03 — Exact census, float segmentation

Session 06 made the spacing *census* exact and left `contiguous_runs()` comparing binary-float MJD
differences. At an exact 1.9872 s tolerance, 231 of the 259 in-window 23-tick gaps evaluate above
the threshold and 28 below — a segmentation boundary decided by representation error.

The published tolerances (1.1, 1.5, 2.0, 5.0 s) all sit far from any populated boundary, so no
published figure moves; `optical ∩ VLBI` is still 82.0134 h and the null still holds. But "we made
the census exact" was not the same as "the arithmetic is exact", and I had written the former while
meaning the latter. Segmentation now uses integer ticks with the tolerance floored once.

The generated evidence also still carried the obsolete *"float-representation twin"* note,
contradicting its own exact representation. Replaced by the empty-band statement.

→ [`FTRO-DEF-036`](../ledgers/deficiency-log.md#ftro-def-036) **v2.0.0**, D-053.

---

## 04 — The documented clean path did not run

README step 2 read `data/raw/evidence/gps2utc.clk`, which no earlier step creates — the evidence
pinner writes `pulsar-clock-corrections--gps2utc.clk`, and ran *afterwards*. The exact command
failed on a clean archive. Reordered so the evidence pinner runs first, with the name it actually
writes.

Also: the crate check was failing (86,566 recorded against 86,939 actual), and README and session 06
said 13 resolved where the machine ledger correctly said 12. `DEF-031` still carried a stale
"26 tests pass".

Small things — but a "documented clean path" that has not been run is a claim, and I had been
making it for three commits.

---

## 05 — Ledger

| | S01 | S02 | S03 | S04 | S05 | S06 | S07 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Entries | 23 | 27 | 29 | 33 | 35 | 36 | **36** |
| Resolved | 0 | 4 | 5 | 9 | 11 | 12 | **12** |
| Self-directed | 1 | 4 | 5 | 9 | 11 | 12 | **12** |
| Reopenings | — | — | — | — | 2 | 3 | **7** |

No new entries this round: every finding was a reopening of one already recorded. That is the first
session where the ledger's shape did not grow, and it is the more useful signal — the problems are
now the *same* problems, being pushed to their boundary rather than replaced by new ones.

`source_evidence` 19 · `execution` 10 · `schema` 4 · `rights` 2 · `policy` 1

---

## 06 — Method notes to self

- **A gate that agrees with itself by construction is not a gate.** `check_versions.py` compared a
  string against a copy of itself and reported ok for three commits.
- **Check the precondition before the action, not after.** Coverage verified after caching is not
  coverage; it is a report about bytes already on disk.
- **A failed run must not be able to publish.** Atomic promotion is the difference between a
  detectable failure and a silently poisoned input.
- **Demonstrating by hand is not testing.** Session 06's table was correct and proved nothing about
  the committed suite.
- **Exactness has to reach every comparison**, not the headline computation.
- **Run the documented path.** Three commits of instructions that fail on a clean checkout.

---

## 07 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

The reviewer's chain is now enforced on its first four edges — expected registry → preflighted
pinners → promoted-only-on-success reports → consumers that reject non-success. The last edge,
**deriving `identities.json` from the reports** rather than reconciling two hand-maintained views,
remains Phase-1 work and remains the fix that would retire this class rather than testing across it.

Most of the profile's normative clauses still have no executable check. Fifteen do now.
