# Session 08 — Seventh external review: a wrong number, published, past every gate

**Date:** 2026-08-26 · **Reviews:** commit [`615afe2`](https://github.com/uwarring82/ftro-walking-skeleton/commit/615afe2cfdadaea46ee7551f8f0ded05c392ed7f)
**Outcome:** four-domain null holds; five new self-directed entries; 57 → 70 tests.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[07](2026-08-26-session-07-review-corrections-6.md)
> are left unedited.

---

## 00 — I broke a contract and updated one caller of two

Session 07 changed `contiguous_runs()` to take integer ticks. It has **two** callers. I updated
one.

`optical_sensitivity.Resegmenter` kept passing float MJDs and converting the results back as MJDs.
MJD-scale differences compared against a tick-scale tolerance means **no gap test can ever be
true** — so every tolerance collapsed to 34 runs, one per file, and the committed report published:

| | Published | Correct |
| --- | ---: | ---: |
| optical | 171.442704 h | 133.111920 h |
| optical ∩ VLBI | 117.995208 h | 82.013424 h |
| runs, all tolerances | 34 | 7,398 / 7,398 / 7,139 / 4,826 |

A wrong number, in a published report, contradicting the selection note *and this report's own main
computation* — and **all 57 committed tests passed**.

The missing invariant is embarrassing in hindsight: the scan's 1.5 s row and the main computation
**share a convention**, so they must agree. Nothing compared them. Three tests now do, including one
asserting the run counts are not degenerate across tolerances — the exact signature of this bug.

The null was never at risk: `no_common_support` holds under both the broken and the corrected scan.
But the sensitivity table exists precisely to show the null is convention-independent, and it was
itself wrong. → [`FTRO-DEF-037`](../ledgers/deficiency-log.md#ftro-def-037), D-054.

---

## 01 — Absence meant success again, in the gate built to stop that

`assert_report_usable()` tested `doc.get(field)` for truthiness. A report that simply **omitted**
`retrieval_validation`, `n_failed` or `n_without_expected_digest` was accepted. Each was removed
independently; all three passed.

And the tests carried the identical defect — `assertFalse(doc.get(...))` — so stripping both
counters from the IGS report left all 57 green.

This is `FTRO-DEF-034` again, in the gate written after `FTRO-DEF-034`. Same principle, same
language construct, one layer down. Every field is now required to be **present, correctly typed,
and hold a permitted value**, the production consumer is mutation-tested rather than only its
helper, and single-pin reports declare the same state as list reports so no consumer needs a
per-shape exemption.
→ [`FTRO-DEF-038`](../ledgers/deficiency-log.md#ftro-def-038), D-055.

---

## 02 — The command that maintains the gate could satisfy it

`check_versions.py --update` replaced both the recorded version and digest unconditionally —
including for artifacts the audit had just flagged as same-version drift.

```
--check  → exit 1     (drift detected)
--update → exit 0     (drift recorded as the new truth)
--check  → exit 0     (drift now invisible, version unchanged)
```

One command silenced the gate. `--update` now refuses when content changed under an unchanged
version, and initial registration is a separate explicit `--register` path rather than a side
effect. → [`FTRO-DEF-039`](../ledgers/deficiency-log.md#ftro-def-039), D-056.

---

## 03 — "Every versioned artifact" was twelve files I happened to list

D-039a binds *every* versioned artifact. The registry was a hand-written list of twelve. All three
ApplicabilityAssessments declare `1.0.0` and none was registered, so changing one without a bump
returned success.

A rule quantified over "every X" needs an executable enumeration of X. `check_versions.py` now
**discovers** every document under `phase0/`, `ledgers/`, `profile/` and `charter/` that declares a
version, and fails if one is neither registered nor in an explicit `EXCLUSIONS` map with a stated
reason. Discovery immediately found five unregistered — the three assessments plus two generated
files that now carry recorded exclusions. Fourteen tracked, four excluded on the record.
→ [`FTRO-DEF-040`](../ledgers/deficiency-log.md#ftro-def-040), D-057.

---

## 04 — The likeliest failure left no evidence

`pin_vgosdb.py`'s `urlopen()` sat outside any failure handling. A preflight-covered but nonexistent
URL exited 1 with a traceback and produced **neither** the official report **nor** a `.rejected`
one — the only failure mode in the whole contract that vanished without a record. And it is the
mode most likely in practice: the network.

The subprocess suite exercised content and digest outcomes and never transport.
→ [`FTRO-DEF-041`](../ledgers/deficiency-log.md#ftro-def-041), D-058: every failure mode a contract
names must have a test.

---

## 05 — Ledger

| | S04 | S05 | S06 | S07 | S08 |
| --- | --- | --- | --- | --- | --- |
| Entries | 33 | 35 | 36 | 36 | **41** |
| Resolved | 9 | 11 | 12 | 12 | **17** |
| Self-directed | 9 | 11 | 12 | 12 | **17** |

`source_evidence` 19 · `execution` **15** · `schema` 4 · `rights` 2 · `policy` 1

The `execution` class is now larger than every other class combined except `source_evidence`. All
fifteen are the same statement: *it was expressible, it was not done, and nothing checked.* Session
07 said the shape of the ledger had stopped growing; that was true for one round.

---

## 06 — What actually went wrong this round

Worth naming plainly, because it is not the same as previous rounds. Sessions 02–07 were about
**claims outrunning evidence**. This round has two of those, but the headline is different: I
**introduced a regression** — a contract changed under a caller I did not check — and it published
a wrong number that every gate accepted.

The gates are now good enough that they caught nothing here, because the failure was upstream of
all of them: a number computed wrongly is still a well-formed number. What catches that is not
another gate but a **redundancy invariant** — two paths that must agree. That is the one class of
check the suite had none of.

---

## 07 — Method notes to self

- **Changing a contract means enumerating its callers.** `grep` would have taken ten seconds.
- **Where two computations share a convention, assert they agree.** Redundancy catches what
  validity checks cannot.
- **`.get()` truthiness is never a conformance test** — twice now, one layer apart.
- **The command that maintains a gate must not be able to satisfy it.**
- **A rule over "every X" needs an enumeration of X**, or it silently means "every X I listed".
- **Test the failure mode you expect in production**, not only the ones convenient to fixture.

---

## 08 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

The reviewer's chain is enforced on its first four edges. The fifth — deriving `identities.json`
from the reports rather than reconciling two hand-maintained views — remains Phase-1 work, and this
round strengthens the case for it: the sensitivity regression is exactly the kind of thing that
derivation removes by construction rather than by assertion.

Most of the profile's normative clauses still have no executable check. Twenty do now.
