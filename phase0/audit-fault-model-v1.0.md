# Phase-0 Audit Fault Model v1.0

**Document ID:** FTRO-AUD-001 · **Version:** 1.0.0 · **Date:** 2026-08-26 · **Licence:** CC BY 4.0
**Status:** Pre-registered. Run once, report all results including zero findings.

Pre-registered so an audit has a defined end. The previous protocol had an implicit "find five"
stopping rule, which cannot terminate: once familiar branches are covered it moves to another
input shape or hypothetical mutation. This enumerates the faults in scope **before** execution.

## Workflows in scope

W1 clean-export test suite · W2 the README pipeline steps 0–7 · W3 each pinner against its
fixtures · W4 `four_domain_intersection.py` against committed reports · W5 `check_versions.py
--check` after a content edit.

## Mutation operators

Applied to `src/` and to committed artifacts. Each must be **detected** (non-zero exit or a
failing test) or recorded as an accepted gap.

| # | Operator | Target | Expected |
| --- | --- | --- | --- |
| M1 | Delete a required field from a pin report | any report | rejected by C3/C4 |
| M2 | Replace an integer counter with `false`, a float, or a string | any report | rejected |
| M3 | Replace a list-valued field with an object or string | any report | rejected |
| M4 | Truncate, duplicate or add a pin | any report | rejected by C4 |
| M5 | Rewrite actual and expected digest to the same fabricated value | any report | rejected by C4 |
| M6 | Relabel a semantic field (`series`, `mjd`) without changing name or digest | IGS report | **no effect** (C5) |
| M7 | Change a domain constant in one computation only | main or sensitivity | **impossible**: the constant has one home and propagates to both (C6) |
| M8 | Remove a sort, or otherwise break an internal precondition | `optical_sensitivity` | **no effect** (function owns its precondition) |
| M9 | `int` → `round`, or `>` → `>=`, in the segmenter | `analyse_optical` | rejected by C7 |
| M10 | Halve every run's span, preserving topology | `analyse_optical` | rejected by C7 |
| M11 | Move a precondition check after the action it guards | any pinner | rejected by the urlopen spy |
| M12 | Edit a versioned artifact without bumping its version | any | rejected by C10 |
| M13 | Reorder README steps so a step consumes an artifact no prior step produces | README | rejected by W2 |

### A note on M7 and M8

Both are recorded as "no effect" or "impossible" rather than "detected", and the distinction is
deliberate. The defect they represent — two computations disagreeing — has been removed by
construction rather than caught by a check. A mutation that now propagates *coherently* is a
legitimate parameter change, not a fault.

What that does **not** cover: an unauthorised edit to a scientific constant. `PULSAR_OBS_START_UTC`
is still a literal, single-sourced but hand-written. Detecting a change to it is a code-review and
version-gate concern, not a consistency one. Deriving it from the pinned `J0437-4715.tim` — the
"derive, don't store" treatment already applied to `series` and `mjd` — is Phase-1 work and is
recorded as an open assurance gap rather than claimed as closed.

## Out of the fault model

Not tested, and stated so rather than left implicit: adversarial hand-edits by an actor with
commit access beyond the operators above; faults in the trusted computing base; provider-side
byte changes (covered by digests, not by tests); and mutations to the test suite itself.

## Reporting rule

Execute the checklist once. Report every operator's result, including "detected" for all of
them. **Do not continue searching after the list is exhausted.** A fault discovered outside this
model is filed as `latent_regression` against Phase 1 and amends this document for the next
audit; it does not reopen Phase 0.
