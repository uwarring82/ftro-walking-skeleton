# WP2A registration status

Read this before reading any other WP2A document.

| Version | Status | Files |
| --- | --- | --- |
| **1.0.0** | **REJECTED pre-registration — never executed** | `contract-v1.0.md`, `expected-facts-v1.0.json`, `queries-v1.0.json`, `mutation-population-v1.0.json` |
| **1.1.0** | **REJECTED pre-registration — never executed** | `contract-v1.1.md`, `expected-facts-v1.1.json`, `queries-v1.1.json`, `mutation-population-v1.1.json` |
| **1.2.0** | **REJECTED pre-registration — never executed** | `contract-v1.2.md`, `source-facts-v1.2.json` + `build_source_facts.py`, `interpretations-v1.2.json`, `queries-v1.2.json`, `mutation-cases-v1.2.json`, `step2-schema-v1.2.json` |
| **1.3.0** | **CURRENT — instrument bound, Step 2 not executed** | `contract-v1.3.md`, `source-facts-v1.3.json`, `prior-observation-v1.3.json`, `interpretations-v1.3.json`, `queries-v1.3.json`, `expected-answers-v1.3.json`, `mutation-cases-v1.3.json`, `step2-schema-v1.3.json`, `registration-manifest-v1.3.json`, generators, checker and runner |

## v1.2 is rejected and retained unchanged

v1.2 separated generated facts from interpretations, but its generator still constructed
occurrence and output identities, roles, counts and a repository-wide absence claim while calling
the result verbatim source content. More decisively, the registered optical expectation contained
only 60 of 256 digest bits, so a runner would have had to invent the remaining bits or copy its
observation into the expected field.

The registration also called an already parsed optical member `opaque`, dated knowledge at a
pre-fetch timestamp, made M2's Q9 condition semantically contradictory, omitted complete Q3
transformation records, left the decision table overlapping, and froze mutation counts whose
operators and exact fields remained partly selectable. Its Step-2 “schema” was a prose field list
without input authentication, outcome precedence, atomic publication or a durable result binding.

v1.3 registers the full imported claim without presenting it as provider authentication or an
independently timestamped external record, separates literal projections from constructed join
keys, supplies three independent state axes
and bounded knowledge time, gives Q9 an explicit RDF distinction, enumerates **168** exact
pre-fixture mutation cases plus an exact-set R11 rule, and binds an executed schema, checker and
runner in one immutable manifest. Exact normalized answers are generated before any fixture, and
M1's superset relation is an assurance invariant rather than a result a fixture can violate
substantively. No provider payload was read while issuing or testing v1.3.

## v1.1 is also rejected, and also retained unchanged

v1.1 repaired v1.0's ten defects and introduced or left eight more. The decisive one: it claimed
expected facts were produced by a committed generator, and **no generator existed** — while the
predicates, temporal semantics, code-consumption claims and execution states it presented as
"derived from the four pinned sources" are not derivable from those sources at all. Curated
semantics presented as source derivation.

It also labelled the BKG containers and the optical member `unresolved` when the profile reserves
that for *no identified artifact*; the identified but uninspected BKG artifacts are `opaque`, while
the already parsed optical member is `resolvable`. It answered the optical
support key as the filename date when production reads MJD tokens from the member content, scored
Q7 against the wrong cardinality, froze mutation counts rather than target identities, and posed Q9
so that `assertion_only_supported` was unreachable by definition.

`contract-v1.2.md` §0 tabulates all eight.

## v1.0–v1.2 are retained unchanged, and none is live

The v1.0 files are **byte-identical to their registration at `100b0e8`**, the v1.1 files to theirs
at `7585135`, and the v1.2 files to theirs at `ccd1534`. They are kept so each rejected
registration stays inspectable, not because any part is in force. **No Step-2 extraction, mapping,
evaluation or mutation run occurred under any rejected version.**

v1.0 was mechanically sound and structurally unable to answer or execute its own requirements:
three conflated axes under one `evidence_state`, an oracle missing every BKG route/size/time and
the optical container's retrieval identity, one consumption question standing for three distinct
facts, no query testing addressability at all, no outcome for a registered fault going undetected,
target selection loose enough for recipes to pick the easiest of six occurrences, a mutation
against a field fixtures were not required to have, prose-only query applicability leaving
model-pass aggregation undefined, and an untyped halt for a refuted prediction.

`contract-v1.1.md` §0 tabulates all ten against their repairs.

## Rule

A registration is amended only *before* execution begins. After Step 2 starts, a defect in the
registration produces a **new version and a restarted trial**, never an edit to the live one.
