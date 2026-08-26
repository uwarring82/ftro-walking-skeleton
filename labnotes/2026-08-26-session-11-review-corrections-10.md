# Session 11 — Tenth external review: a fixture that could not see the boundary

**Date:** 2026-08-26 · **Reviews:** commit [`aaeae6f`](https://github.com/uwarring82/ftro-walking-skeleton/commit/aaeae6fcbc48169373ece3f8eae1ab7839f9ce1e)
**Outcome:** null intact; five new self-directed entries; 94 → 99 tests.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[10](2026-08-26-session-10-review-corrections-9.md)
> are left unedited.

---

## 00 — An oracle constrains only what its fixture exercises

Session 10 fixed the oracle to constrain extent, not just topology. It still could not see a
threshold.

5.0 s **floors** to 57 ticks and **rounds** to 58. The mini-archive had no 58-tick gap, so
replacing `int()` with `round()` in `contiguous_runs()` left all 94 tests green — while the real
archive has **3,143 gaps of exactly 58 ticks**, and the published 5 s row would have become:

| | Published | With `round()` |
| --- | ---: | ---: |
| runs | 4,826 | **2,943** |
| optical | 133.567344 h | **134.533680 h** |
| optical ∩ VLBI | 82.232760 h | **82.536504 h** |

The regenerated report passed the tests, the version gate and the crate gate.

The fixture now embeds gaps at each tolerance's threshold **T and T+1** — 12/13, 17/18, 23/24,
57/58 — with tests asserting that a T gap merges and a T+1 gap splits at every tolerance.

| Injected | Result |
| --- | --- |
| `int()` → `round()` | **6 failures** |
| `>` → `>=` | **12 failures** |

→ [`FTRO-DEF-053`](../ledgers/deficiency-log.md#ftro-def-053), D-071.

---

## 01 — The runtime gate read the report's own account of itself

`assert_report_usable()` consulted nothing external. So:

- truncating the IGS report from 57 pins to **one**, with `n_pinned: 1` — accepted;
- rewriting a pin's **actual and expected** digest to the same fabricated value — accepted.

And `four_domain_intersection.py` consumed those pins directly. A stored-report test *did* check
registry equality, but the documented workflow runs the tests **before** retrieval, so it protects
the repository, not a run.

The gate is now bound to the expected-digest registry and rejects missing, unknown and duplicate
pins, and any digest disagreeing with the registry. Both mutations exit 1.
→ [`FTRO-DEF-054`](../ledgers/deficiency-log.md#ftro-def-054), D-072.

---

## 02 — A special case that quietly weakened the state machine

The generated-content check rejected changed content only when the declared version **equalled** the
recorded one — and `--register` disabled the refusal outright. Three laundering paths, all verified:

| | Before |
| --- | --- |
| same v0.2.0 output | `check 1 → register 0 → check 0`, 94 tests pass |
| v0.2.0 → v0.1.0 | check, update, check and all tests pass |
| version removed | `--update` recorded `"version": null` |

I had given generated files a *weakened copy* of the state machine instead of the machine. They now
run the same one: version required and valid, exact registry agreement on `--check`, forward-only
updates, and `--register` may only add a missing entry. All three now end in exit 1.
→ [`FTRO-DEF-055`](../ledgers/deficiency-log.md#ftro-def-055), D-073.

---

## 03 — A guard that skips is not a guard

The failure/uncovered coherence check ran only when the field was **already a list**. So
`failures: {}` passed, `uncovered_by_registry: "ghost"` passed, and `pins: {}` added to a valid
single-pin report was ignored entirely. My tests exercised non-empty valid lists only — the shapes
that were never in question.

Type is now checked before invariant, and six container-shape mutations are tested.
→ [`FTRO-DEF-056`](../ledgers/deficiency-log.md#ftro-def-056), D-074.

---

## 04 — Measuring the side effect instead of the act

The test named "nothing was fetched" observed the diagnostic and an empty cache directory. Bytes
are not cached until verification, so moving retrieval **above** the preflight error — same message,
same empty cache — kept all 94 tests green.

It now spies on `urllib.request.urlopen` and asserts **zero calls**. Injecting a fetch before the
preflight fails.

The production-consumer mutation test was also still writing into the tracked checkout, against
this project's own D-067 from one session earlier. It now runs in a copied tree and asserts the
tracked report is untouched. → [`FTRO-DEF-057`](../ledgers/deficiency-log.md#ftro-def-057), D-075.

---

## 05 — Ledger

| | S08 | S09 | S10 | S11 |
| --- | --- | --- | --- | --- |
| Entries | 41 | 47 | 52 | **57** |
| Resolved | 17 | 23 | 28 | **33** |
| Self-directed | 17 | 23 | 28 | **33** |

`execution` **31** · `source_evidence` 19 · `schema` 4 · `rights` 2 · `policy` 1

---

## 06 — The pattern, one level finer

Session 10 named the pattern as *controls that do not measure what they are named for*. This round
sharpens it: every finding is a control whose **scope** is narrower than its name.

| Control | Name implies | Actual scope |
| --- | --- | --- |
| segmentation oracle | the segmenter is correct | correct on inputs the fixture happens to contain |
| consumer gate | the report is usable | the report agrees with itself |
| generated-version check | generated content is versioned | versioned when the version is unchanged |
| container coherence | the report is well shaped | well shaped when already the right type |
| "nothing fetched" | no request was issued | no bytes were cached |

Each is true as far as it goes. The defect is that "as far as it goes" was never stated, and I read
each as the full claim. What I have not yet done is write down, for each gate, the inputs it does
**not** constrain — which would have made all five of these visible without a review.

---

## 07 — Method notes to self

- **A fixture bounds an oracle's claim.** No 58-tick gap meant no statement about 58-tick gaps.
- **Exercise thresholds at T and T+1.** Off-by-one is the failure mode boundaries exist to catch.
- **A runtime gate must consult something external.** Self-description is not verification.
- **A special case must obey the general state machine**, not a simplified copy of it.
- **Check the type before the invariant.** `isinstance` guards skip; they do not fail.
- **Assert the act you forbid, not a side effect that usually accompanies it.**
- **State each gate's scope explicitly**, including what it does not cover.

---

## 08 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

Scope of what is guarded, stated plainly: an extent- and boundary-constraining oracle exists for
**segmentation only**. The four-domain intersection, the alignment arithmetic and the three credit
bases still have no independent implementation, no manifest constraining their magnitudes, and no
fixture exercising their boundaries — the three defects this round and the last found in the
segmentation oracle, still unaddressed for every other computation. That is now the largest known
gap in the verification story, and it is not shrinking.

Most of the profile's normative clauses still have no executable check. Thirty-six do now.
