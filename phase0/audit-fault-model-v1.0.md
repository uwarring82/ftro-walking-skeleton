# Phase-0 Audit Fault Model v1.0

**Document ID:** FTRO-AUD-001 · **Version:** 2.0.0 · **Date:** 2026-08-27 · **Licence:** CC BY 4.0
**Status:** Retrospective semantic fault model. Not itself an executable pre-registration.
The qualifying recipes live separately in
[`audit/execution-manifest-v1.0.json`](audit/execution-manifest-v1.0.json).
**v1.1.0** adds M12a–M12c after M12c was found unguarded by running the gate against `HEAD~1` —
the amend-then-rerun path the reporting rule prescribes.

Finite so an audit can have a defined end. The previous protocol had an implicit "find five"
stopping rule, which cannot terminate: once familiar branches are covered it moves to another
input shape or hypothetical mutation. This enumerates the semantic operators. The 2026-08-26
runs did not freeze concrete targets, mutations, commands, reset rules or report destinations
before execution and therefore do not qualify. A separate executable manifest must select those
details before calibration or audit.

## Workflows in scope

W1 clean-export test suite · W2 the README pipeline steps 0–7 · W3 each pinner against its
fixtures · W4 `four_domain_intersection.py` against committed reports · W5 `check_versions.py
--check` after a content edit.

## Mutation operators

Applied to `src/` and to committed artifacts. The executable manifest must distinguish the
observation `detected`, `not_detected` or `not_executed`. The last is always a run failure.
For M6, M7, M8 and M12c, `not_detected` is the registered observation and passes only when the
mutation was proved applied and the detector was proved to have run.

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
| M11 | Move a precondition check after the action it guards | the registry and explicit-digest routes frozen as separate vgosDB cases | rejected by the `urlopen` spy |
| M12 | Edit a versioned artifact without bumping its version | any | rejected by C10 |
| M12a | Downgrade a version | any | rejected by C10 |
| M12b | Remove a declared version | any | rejected by C10 |
| M12c | Add a version to a previously unversioned document | any | **accepted**: nothing to advance from |
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

First run the frozen executable manifest once as **calibration**. Calibration is categorically
non-qualifying and establishes only that every recipe applies, the detector executes, and the
isolated tree resets. Freeze any correction before qualification begins. Then execute the same
manifest twice in separate clean checkouts, report every result and stop when the fixed list is
exhausted. Any runner, manifest, subject or bound-input change resets the qualifying count to 0/2.
A qualifying run also requires the structured C9 PASS for that exact carrier; the final pair
checker requires two distinct report digests, run IDs and checkout identities.
A finding outside the frozen model is filed under the acceptance contract's finding-type rule;
it does not authorize an unbounded search during a run.
