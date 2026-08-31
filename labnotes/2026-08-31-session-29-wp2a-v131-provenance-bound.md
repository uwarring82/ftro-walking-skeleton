# Session 29 — WP2A v1.3.1: binding the imported claim to its evidential limit

**Date:** 2026-08-31 · **Branch:** `phase2` · **Task:** WP2A Step 2, before execution
**Outcome:** v1.3.0 superseded before execution; v1.3.1 registration prepared
**Licence:** CC BY 4.0

---

## 00 — Why the frozen registration was amended

Independent review confirmed every v1.3.0 implementation claim and found one blocking provenance
overstatement. The optical member whose imported digest and size form the Family-B Step-2 target
already existed at this ignored path when the registration was written:

`data/raw/zenodo-17107693/extracted/PTB_Yb_CombKnoten-INRIM_ITYb1/2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat`

Path presence is environment state, not durable repository evidence. The registration omitted it
and represented three claims about the registration process as bare booleans: that the value was
observed before Step 2, was not derived or recomputed by v1.3, and was registered without reading
provider payload. Git can show that the registration commit precedes any committed Step-2 report;
it cannot establish those earlier actions or omissions. The claims may be true, but their correct
evidence class is `attested_not_repository_checkable`.

Evidence: `phase2/wp2a/prior-observation-v1.3.json`; `git check-ignore -v <member>` resolves to
`.gitignore:10`; no provider payload was opened or hashed during this correction.

---

## 01 — The C9 lineage is narrower than first proposed

The qualifying Phase-0 C9 cannot be the source of the present working-tree copy. It ran in the
separate checkout `/private/tmp/ftro-closure-8ddcbfa.PjM6wU/c9-checkout`, extracted the same relative
selector successfully, then removed `data/` and recorded `provider_bytes_retained: false`.

The durable statements are therefore:

- Session 01 attests that the original Phase-0 work extracted the archive in this repository;
- the committed optical inventory names this exact member and its sample coverage;
- qualifying C9 independently authenticated the container and extracted the same selector in an
  isolated checkout; and
- repository evidence does not bind the present ignored copy to either extraction event.

Evidence: `labnotes/2026-08-25-session-01-phase0.md#02--optical-leg-first-look-and-the-first-surprise`;
`phase0/reports/optical-inventory-summary.json`; and
`phase0/audit/evidence/c9-8ddcbfa-1.json#/subject/checkout_realpath`, `/step_results/3`, `/cleanup`.

---

## 02 — The limitation is part of the report, not commentary beside it

The v1.3.0 report schema had `additionalProperties: false` and no outcome-text field. A later prose
sentence could not be placed in a conforming report, and leaving the bound only in this note would
let the machine-readable outcome travel without it.

v1.3.1 therefore adds one exact, required `outcome_interpretation_bound` object. Its canonical value
lives in `prior-observation-v1.3.json`; the schema embeds it in the frozen registration and as a
JSON-Schema `const`; the runner copies it into every report; and the checker rejects omission or
mutation. A `step2_supports` result now states its own scope:

- it establishes that two registered extractors consumed the same authenticated container bytes,
  agreed byte-for-byte and reproduced the committed expectation;
- it does not establish independent derivation of the expected member digest or size, the external
  timestamp of the prior observation, or provider attestation of that member value.

The target, four-input population, extraction methods, byte-comparison rule, outcome precedence,
queries, expected normalized records and mutation population are unchanged. Because Step 2 had not
executed, this is a pre-execution patch amendment, not a restarted trial.

Evidence: `phase2/wp2a/build_step2_schema_v1_3.py`, `run_step2_v1_3.py`,
`check_step2_v1_3.py`, `step2-schema-v1.3.json`, and `tests/test_wp2a_v13.py`.

---

## 03 — Ledger treatment

`FTRO-P1-DEF-020` is reopened and resolved at v2.0.0 rather than creating a new class of defect.
The omission is another result-bearing registration choice left outside the frozen evidence. The
Phase-1 supplement advances to v0.11.0. Reconciliation into the unified ledger follows the standing
snapshot rule after this supplement state is committed.

No Step-2 provider input was opened in this session before publication of the repaired instrument.

---

## 04 — Pre-publication verification

- main suite: 251 tests, zero failures and zero skips;
- Phase-1 suite: 48 tests, zero failures and zero skips;
- all five v1.3 generators: `--check` PASS;
- Step-2 registration checker: PASS;
- Gate-1 structural/source and SIO report freshness/content: PASS;
- version gate: five changed versioned artifacts, zero stale;
- root crate: zero stale, zero missing;
- `git diff -- phase0/`: empty; and
- v1.3.1 registration-manifest SHA-256:
  `888d7f55c58d1652fa51f16fa2fc59694eba1344082a43e1ff8f8606727267b1`.

These checks use only committed/source-controlled inputs and synthetic fixtures. Step 2 remains
unexecuted until this exact repaired instrument is committed and published.
