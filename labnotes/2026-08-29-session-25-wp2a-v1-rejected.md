# Session 25 — WP2A v1.0 rejected before step 2; v1.1 issued

**Date:** 2026-08-29 · **Branch:** `phase2`
**Outcome:** a mechanically sound registration found structurally unable to run. Nothing executed under it.
**Licence:** CC BY 4.0

> **Append-only.** Session 24 is unedited. Its registration is retained byte-unchanged and marked rejected.

---

## 00 — Sound is not the same as executable

`100b0e8` passed every mechanical check: valid JSON, 11 operators and 40 cases recomputing exactly,
the optical values correctly labelled a partial-digest prediction, clean branch, exact commit.

It still could not answer or execute its own requirements. Ten defects, every one structural.

The decisive one: **no query tested addressability.** M2 could return an output digest as a
literal, satisfy every retrieval, transformation, consumption and assertion query, and never give
the consumed state an addressable identity — *the question the trial exists to answer.* A trial
that cannot fail its own hypothesis is not a trial. `Q9` now asks it directly, and if M2 fails only
Q9 that is a substantive finding, not a malformed fixture.

## 01 — The other nine

| # | Defect | Repair |
| --- | --- | --- |
| 1 | `evidence_state` carried three axes at once; Q7 wanted temporal bounds the oracle lacked | three axes; `{value, bound_state}` per bound |
| 2 | Oracle had no BKG route/size/time/procedure and no optical container identity | four pinned sources |
| 3 | Q5 asked one question with three answers | Q5a / Q5b / Q5c |
| 5 | Undetected registered fault matched no outcome | `assurance_failed` |
| 6 | "Applies to fixture" let recipes pick the easiest target | exhaustive, 76 cases |
| 7 | R11 mutated a field fixtures needn't have | F-REQ-4 mandatory |
| 8 | Applicability prose-only; aggregation undefined | machine-readable |
| 9 | Refuted prediction halted with no type | `prediction_refuted` |
| 10 | Seven Phase-1 reports undeclared behind a green check | bounded recursive discovery |

Two deserve their own paragraph.

**#2 is why an oracle must be pinned, not described.** v1.0 named the current pin report as the
IGS source. That report retains only `previous_retrieval_sha256` — the BKG **route, size, retrieval
time and procedure do not exist in it.** They exist only at `a806bba:phase0/reports/igs-artifact-pins.json`
(`467d699e…6201`). Q1 was unanswerable for three of Family A's six retrieval occurrences and the
registration did not know it. Likewise the optical container's retrieval identity lives in
`identities.json` (`a4a27e7e…3ac45`), which v1.0 never cited.

**#6 is post-hoc selection wearing a different hat.** Each Family-A fixture holds three products,
six retrieval occurrences and three outputs. "R1 applies to M1×A" would have let the recipe author,
writing *after* seeing the fixtures, mutate whichever single occurrence was easiest and record the
operator as covered. Targets are now exhaustive over counted populations — 76 cases, no remaining
choice. The two-stage freeze was supposed to prevent exactly this and did not, because it bounded
the *stage* and not the *selection*.

## 02 — The rule this establishes

**A registration is amended only before execution begins.** After step 2 starts, a defect in the
registration produces a new version and a restarted trial, never an edit to the live one.

v1.0 is kept byte-identical with an explicit
[`REGISTRATION-STATUS.md`](../phase2/wp2a/REGISTRATION-STATUS.md). Nothing about it is in force,
and nothing was executed under it — which is the only reason v1.1 is a fresh registration rather
than a contaminated one.

## 03 — The crate gap was the same shape

`refresh_crate --check` reported **0 stale, 0 missing** while seven Phase-1 reports were undeclared,
because discovery was flat and the phase trees are nested. Phase 2 looked complete only because its
five entities were added by hand last session. A Step-2 report could have been omitted with the
gate still green.

Bounded recursive discovery now walks `phase1/` and `phase2/` under an explicit suffix set, a fixed
depth and an excluded-directory set. Before the fix the check named all fourteen missing
declarations; after it, both trees report zero undeclared. `FTRO-P1-DEF-014`.

## 04 — Method note to self

**Check whether a registration can answer its own questions from its own oracle, before freezing
it.** Every one of these ten was findable by reading v1.0 against itself — no execution required.
Mechanical validity measured the wrong thing: the JSON was well-formed and the arithmetic was
right, and neither had anything to do with whether the trial could run.

## 05 — Next

Step 2 under v1.1: the durable input-evidence report, with independent `zipfile`, `unzip -p` and
Unix-compress cross-checks, which also settles the member-digest prediction as
`prediction_confirmed` or `prediction_refuted`.
