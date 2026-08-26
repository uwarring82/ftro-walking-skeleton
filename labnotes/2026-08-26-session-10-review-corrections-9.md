# Session 10 — Ninth external review: an oracle that measured the wrong thing

**Date:** 2026-08-26 · **Reviews:** commit [`5f0244f`](https://github.com/uwarring82/ftro-walking-skeleton/commit/5f0244f3fa41c25fe6b79082c1fff8c1513009dc)
**Outcome:** null intact; five new self-directed entries; 86 → 94 tests.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[09](2026-08-26-session-09-review-corrections-8.md)
> are left unedited.

---

## 00 — The oracle checked topology, not extent

Session 09's headline was an "independent" oracle. Both of its routes call the same
`analyse_optical.contiguous_runs()`. It was one implementation invoked twice.

And the manifest recorded four **run counts**. So the reviewer halved every run's span while
preserving topology:

| | Before | After halving |
| --- | ---: | ---: |
| optical support | 133.1119 h | **81.6907 h** |
| optical ∩ VLBI | 82.0134 h | **52.194 h** |
| run counts | 7,398 / 7,398 / 7,139 / 4,826 | *unchanged* |
| tests | 86 pass | **86 pass** |

A 40% change in the quantity the whole analysis rests on, invisible. I had written a check that
constrained the *shape* of the answer and not its *size*, and then called it an oracle.

The fix is what "independent" should have meant: a segmenter written from the specification **in the
test file**, calling nothing in `src/`. Plus a manifest of full run **tuples** — comparison, file,
`tick_start`, `tick_end`, `n_samples` — and total spans. Four things now have to agree: the
independent segmenter, the production segmenter, both sensitivity routes, and the recorded manifest.

Span-halving now fails **12 tests**. → [`FTRO-DEF-048`](../ledgers/deficiency-log.md#ftro-def-048),
D-066.

---

## 01 — A compensating control that measured the wrong property

Session 09 excluded generated files from version tracking and added a **freshness** check as the
compensating control. Freshness proves output matches *current* input. It says nothing about whether
*changed* output was re-versioned — which was the actual `DEF-045` complaint.

So editing the optical summary and regenerating produced different content still declaring v0.2.0,
and every gate passed. The scenario `DEF-045` records as fixed reproduced exactly.

The test had a second defect worth naming on its own: it rendered **into the tracked checkout**. A
stale file was overwritten by the first failing run, so the second run passed. A test that repairs
the condition it inspects reports success on its second invocation forever.

Generated documents now carry their content digest under `__generated__` alongside their declared
version; changed content under an unchanged version fails `--check` and is refused by `--update`.
The freshness test renders into a copy. → [`FTRO-DEF-049`](../ledgers/deficiency-log.md#ftro-def-049),
D-067.

---

## 02 — `DEF-034` again, one level further down

The consumer gate explicitly permitted a **pin** with no `retrieval_validation`, while the profile
requires it on every record. That is the absent-field failure for the third time: report level
(`DEF-034`), report level again with `false` (`DEF-043`), now pin level — each time inside the gate
written after the previous one.

Also accepted: `n_pinned` absent entirely; `57.0` for a 57-pin report (float equals int); `true` for
a single-pin report (True equals 1); and a non-empty `failures` list beside `n_failed: 0`.

None of the branches added for `DEF-043` had a test. That is the actual lesson —
D-068: **every branch of a conformance predicate needs its own mutation test, or it is untested
code.** → [`FTRO-DEF-050`](../ledgers/deficiency-log.md#ftro-def-050).

---

## 03 — A precondition enforced on one input path

`--expect-sha256 abc` fetched and parsed the archive before rejecting it: the explicit argument was
validated only after retrieval, so it was not a precondition at all. Registry-derived expectations
were preflighted; the command-line one was not.

And `valid_digest()` used `re.match` with a trailing `$`, which in Python **also accepts a trailing
newline** — so a digest read straight from a file validated, and the consumer accepted a report
whose actual and expected digests both carried the suffix. `fullmatch` now.
→ [`FTRO-DEF-051`](../ledgers/deficiency-log.md#ftro-def-051), D-069.

---

## 04 — A capability list is a claim

`TRACKED_SUFFIXES` advertised `.yaml`, `.yml` and `.cff`; `VERSION_RE` parsed only Markdown and
JSON. A versioned YAML file produced `check 0 → register 0 new → check 0`. The completeness claim
covered file types the scanner could not read.

→ [`FTRO-DEF-052`](../ledgers/deficiency-log.md#ftro-def-052), D-070: a capability list needs a test
per entry.

---

## 05 — Ledger

| | S07 | S08 | S09 | S10 |
| --- | --- | --- | --- | --- |
| Entries | 36 | 41 | 47 | **52** |
| Resolved | 12 | 17 | 23 | **28** |
| Self-directed | 12 | 17 | 23 | **28** |

`execution` **26** · `source_evidence` 19 · `schema` 4 · `rights` 2 · `policy` 1

---

## 06 — The pattern, stated honestly

Six rounds ago the failures were claims outrunning evidence. They are now, without exception,
**controls that do not measure what they are named for**:

| Round | The control | What it actually measured |
| --- | --- | --- |
| 07 | version gate | a string against a copy of itself |
| 08 | regression test | that the committed output was self-consistent |
| 09 | freshness check | that output matched *current* input |
| 10 | segmentation oracle | topology, while the result depends on extent |

Each was built in response to the previous round, and each substituted a property that was easy to
check for the property that mattered. That substitution is the thing to watch for, and I have not
yet caught one myself before a review did.

---

## 07 — Method notes to self

- **Constrain the quantity the result depends on.** Counts are not spans. If the downstream number
  is hours, the oracle must pin hours.
- **"Independent" means it does not call the code under test.** Two entry points into one function
  are one implementation.
- **A compensating control must measure the property the original gate measured**, not a nearby one
  that is easier to implement.
- **A test must never write into the tree it inspects.** It repairs the fault and then reports
  success forever.
- **Every branch of a predicate needs a mutation test**, or the branch is untested code that looks
  like coverage.
- **A capability list is a claim.** `.yml` in a suffix tuple is a promise the regex has to keep.

---

## 08 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

Scope of what is actually guarded, stated plainly: there is now an **extent-constraining oracle for
segmentation only**. The four-domain intersection, the alignment arithmetic and the three credit
bases still have no independent implementation and no manifest constraining their magnitudes — the
same defect this round found in the segmentation oracle, still unaddressed for every other
computation.

Most of the profile's normative clauses still have no executable check. Thirty-one do now.
