# WP2A registration status

Read this before reading any other WP2A document.

| Version | Status | Files |
| --- | --- | --- |
| **1.0.0** | **REJECTED pre-registration — never executed** | `contract-v1.0.md`, `expected-facts-v1.0.json`, `queries-v1.0.json`, `mutation-population-v1.0.json` |
| **1.1.0** | **CURRENT** | `contract-v1.1.md`, `expected-facts-v1.1.json`, `queries-v1.1.json`, `mutation-population-v1.1.json` |

## v1.0 is retained unchanged, and is not live

The v1.0 files are **byte-identical to their registration at `100b0e8`**. They are kept so the
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
