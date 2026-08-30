# WP2A registration status

Read this before reading any other WP2A document.

| Version | Status | Files |
| --- | --- | --- |
| **1.0.0** | **REJECTED pre-registration — never executed** | `contract-v1.0.md`, `expected-facts-v1.0.json`, `queries-v1.0.json`, `mutation-population-v1.0.json` |
| **1.1.0** | **REJECTED pre-registration — never executed** | `contract-v1.1.md`, `expected-facts-v1.1.json`, `queries-v1.1.json`, `mutation-population-v1.1.json` |
| **1.2.0** | **CURRENT** | `contract-v1.2.md`, `source-facts-v1.2.json` + `build_source_facts.py`, `interpretations-v1.2.json`, `queries-v1.2.json`, `mutation-cases-v1.2.json`, `step2-schema-v1.2.json` |

## v1.1 is also rejected, and also retained unchanged

v1.1 repaired v1.0's ten defects and introduced or left eight more. The decisive one: it claimed
expected facts were produced by a committed generator, and **no generator existed** — while the
predicates, temporal semantics, code-consumption claims and execution states it presented as
"derived from the four pinned sources" are not derivable from those sources at all. Curated
semantics presented as source derivation.

It also labelled the BKG containers and the optical member `unresolved` when the profile reserves
that for *no identified artifact* (both are identified, hence `opaque`), answered the optical
support key as the filename date when production reads MJD tokens from the member content, scored
Q7 against the wrong cardinality, froze mutation counts rather than target identities, and posed Q9
so that `assertion_only_supported` was unreachable by definition.

`contract-v1.2.md` §0 tabulates all eight.

## v1.0 and v1.1 are retained unchanged, and neither is live

The v1.0 files are **byte-identical to their registration at `100b0e8`**, and the v1.1 files to
theirs at `7585135`. They are kept so the
rejected registration stays inspectable, not because any part of it is in force. **No step of the
trial was executed under v1.0** — the defects were found before Step 2, which is why v1.1 is a new
registration rather than an amendment.

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
