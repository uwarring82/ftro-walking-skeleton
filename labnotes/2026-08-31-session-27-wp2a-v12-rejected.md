# Session 27 — WP2A v1.2 rejected; the runner's choices moved into v1.3

**Date:** 2026-08-31 · **Branch:** `phase2`
**Starting commit:** `cdfb553` · **Outcome:** v1.2 rejected before execution; v1.3 registered and
instrumented; Step 2 not run.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 01–26 are unedited. The v1.0, v1.1 and v1.2 registration artifacts
> remain byte-identical to their publication commits. This note corrects session 26.

---

## 00 — Boundary observed

The next planned file was `run_step2.py`. Reading v1.2 as a runner specification showed that the
runner would still have had to choose evidence and semantics after registration. The decisive
example was mechanical: `step2-schema-v1.2.json` required a 64-hex expected digest, while
`interpretations-v1.2.json` contained only the eight-character prefix and seven-character suffix
of the optical observation. The claimed “all 256 bits” registered a format, not a value.

No WP2A decoder or extractor was invoked on provider bytes while finding or repairing this. The
three local IGS containers and optical archive are provider inputs for a later clean run; the v1.3
tests use metadata, synthetic report rows and FTRO-synthesised archive bytes only.

## 01 — Scientific corrections

- The selected ROCIT member is `resolvable`: Phase 0 expanded the authenticated container and
  parsed every `.dat` member. Its independent byte verification is `indeterminate`, and the WP2A
  procedure is `not_attempted`. Accessibility, verification and execution are different axes.
- Retrieval start is not an exact knowledge time. Durable assertions now carry intervals bounded
  by their latest prerequisite and first cited carrier. Cross-origin equality cannot predate the
  SIO object. The optical exact-byte assertion remains a pending Step-2 interval.
- Q3 is per transformation: six Family-A transformations and one Family-B transformation.
- M2 permits an RDF identifier for the output byte state but supplies no separate description or
  `ftro:TransformationOutput` type for it. Q9 tests that distinction and rejects assertion-ID
  reuse, digest literals, presentation-only occurrences and self-loop padding.
- The model decision function first enforces the M1-superset relation, then applies a complete,
  disjoint nine-row table over the relation-consistent tuples. The evaluator must be bound before
  any fixture exists.

Evidence: `contract-v1.3.md`, `interpretations-v1.3.json`, `queries-v1.3.json`.

## 02 — Source projection, not source mythology

`build_source_facts.py` existed in v1.2, but its output still constructed occurrence/output IDs,
roles, counts, a member path and a repository-wide absence assertion while calling every value
verbatim source content. Its regression test searched only Family A for a short word list.

`build_source_facts_v1_3.py` now places copied values only under source-pointer-bearing `values`
objects. Registered selection and constructed join keys are separately labelled. No scientific
output identity is minted there. The complete optical observation is instead recorded in
`prior-observation-v1.3.json` as an externally supplied, non-provider-authenticated reproduction
target; v1.3 did not recompute it. The external review exchange has no immutable locator or
signature, so this is an imported claim whose pre-registration chronology becomes independently
auditable only when this file is committed. Expected values are loaded before provider inputs and
can never be populated from observed Step-2 output.

## 03 — Executable Step-2 boundary

The v1.3 schema fixes four exact local inputs, their outer digests and sizes, four output targets,
two methods per target, tool and command evidence, direct byte equality, full digest and size
comparison, and ordered target/run outcomes. Network acquisition is outside the Step-2 run.

`check_step2_v1_3.py` re-derives populations, input outcomes, method consequences, counters and
the overall outcome. It executes the complete JSON-Schema subset used by the report and
authenticates the fixed registration population and schema from the subject commit.
`run_step2_v1_3.py` requires a clean commit contained in its configured remote-tracking published
ref. It reads each input path once, authenticates and retains that exact byte snapshot, and gives
both methods only anonymous seekable descriptors populated from the snapshot. A later pathname
rehash is mutation evidence only; it cannot validate or alter the bytes consumed. Publication is
only through create-without-overwrite:
support to the official path; every other complete candidate to a run-specific `.rejected` path.
The descriptor transport is itself exercised with an FTRO-synthetic sentinel before any provider
pathname opens. Snapshot allocation and method-start failures become typed non-execution rows in a
preserved candidate.

`registration-manifest-v1.3.json` binds every registration/instrument file except itself. A report
binds the manifest by full SHA-256, avoiding the v1.2 instruction to edit a frozen contract after
the result.

## 03a — The instrument was audited before it was frozen

The first runnable draft still had six fail-open edges: its JSON Schema was never executed; an
unknown method ID raised before invalid bytes could be preserved; `published_ref: HEAD` counted as
publication; decoders and extractors reopened named input paths after authentication, so consumed
bytes were not bound to the authenticated capture, and no post-consumption path-mutation check
existed; a historical report was
checked against the descendant working-tree schema; and the global-preflight test never exercised
`build_report()`'s permission fold. The exact imported optical digest and source projections also
lacked independent literal and RFC-6901-pointer reconciliation.

All were repaired before publication. Malformed and non-supporting candidates are preserved,
remote-tracking publication is required before any input access, and the bound subject supplies the
historical schema. Methods now consume only anonymous descriptors populated from captured,
authenticated bytes; a later pathname rehash supplies mutation evidence only, with change as an
ordered run-level assurance failure. Negative tests reach the production folds.
This is `FTRO-P1-DEF-021`; no provider payload was opened while testing it.

## 04 — Mutation freeze, including one correction made during implementation

The first v1.3 draft mechanically expanded R8 to include `verification_result` and
`execution_status`, but retained v1.2 output aliases and still applied R7 per output. That was
inconsistent with the new Q3 cardinality and would have left a later recipe to choose among two
Family-A transformations. It was rejected before the generated population was frozen.

The registered population is **168** pre-fixture cases: R1 14, R2 14, R3 8, R4 2, R5 4, R6 6,
R7 14, R8 98, R9 4 and R10 4. Output, transformation and assertion targets now use the identifiers
in `interpretations-v1.3.json`. Six fixture requirements make semantic target resolution explicit.
R11 remains correctly deferred until entities exist, but requires equality of the graph ID set,
the duplicate-free declared ID set and the recipe target ID set—not equality of two counts.

The next audit found that exact mutation targets did not make the scientific comparison exact.
Broad answer pointers still delegated joins and renames to the future evaluator, Q3 omitted the
assertion identifier named by the contract, and F-REQ-6 required a qualifying fixture to expose the
answers used to judge it. `expected-answers-v1.3.json` now freezes every normalized record before
fixtures; only the successful Step-2 start/end timestamps remain as exact whole-value tokens.
Fixtures contain raw graph data and may not embed an answer cache.

It also made explicit that M1 is M2 plus typed output-node descriptions. An M2 family pass with an
M1 failure is therefore an assurance violation, not a scientific win for M2. Seven such Boolean
tuples are gated out; nine relation-consistent rows remain. Equivalence is a legitimate bounded
result and can close `FTRO-P1-DEF-010` by demonstrating that the registered questions do not
discriminate, while leaving any later serialization preference to a separately registered rule.

## 05 — Publication controls reopened and repaired

The v1.2 crate tests were controls reading their own production scope. Setting discovery depth to
99, emptying the exclusion set or removing Phase 2 left their named tests green. The first
`dateModified` repair ran only after some other size/declaration failure, so a same-size content
change remained invisible.

The replacement tests declare phase1/phase2, suffixes, depth and excluded directories independently;
exercise T and T+1 with real fixtures; and require both graph membership and root `hasPart`.
Unknown in-scope suffixes fail closed. A fingerprint excluding only its self-referential identifier
covers canonical crate semantics and every non-volatile declared local file, so same-size byte changes and
equal-length descriptor edits are detectable and date advancement has an independent trigger.

The replacement itself then needed two boundary corrections: flat-test discovery was compared
only to an already populated crate, and new tests reached the root but not the `tests/` collection.
The final controls compare the producer to an independent `tests/*.py` population and exercise a
new file through graph, root and collection. The publication fingerprint excludes only its own
identifier—not the whole control node—and a failed completeness or atomic-replace operation leaves
the official descriptor byte-identical. The first successful atomic replacement exposed one more
boundary: `mkstemp` changed the descriptor from 0644 to 0600. The publisher now copies the existing
mode to its candidate, and a test constrains it. The final re-audit found that the live control node
still described the old whole-node exclusion; the writer could hash and re-sign that false legacy
description. The control declaration is now canonical: check mode rejects stale or extra fields,
write mode repairs them before fingerprinting, and a test begins from an already re-signed false
declaration.

## 06 — Ledger

`FTRO-P1-DEF-016`, `-018` and `-019` are reopened at v2.0.0 and resolved by the replacements above.
`FTRO-P1-DEF-020` records the scientific-registration defect across v1.2 and the pre-freeze v1.3
drafts; `FTRO-P1-DEF-021` records the distinct Step-2 instrument defect. The Phase-1 supplement
advances to v0.10.0 with 21 entries (15 resolved, 6 open, all self-directed). Reconciliation into
the canonical ledger follows the standing committed-snapshot rule.

## 07 — Stop

The next operation is publication of the bound v1.3 candidate, followed by exactly one Step-2 run
from that clean published commit. No fixture or evaluator is authored unless Step 2 supports. A
non-supporting outcome halts this candidate and remains evidence; it is not repaired into a pass.
