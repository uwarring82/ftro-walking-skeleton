# FTRO Phase-0 Qualification Status

**Document ID:** FTRO-P0-QUAL-001
**Version:** 1.1.0
**Date:** 2026-08-27 · **Revised:** 2026-08-28
**Status:** **Phase 0 complete**
**Licence:** CC BY 4.0

> **v1.1.0 is editorial and changes no verdict.** Condition 3's ledger totals are now labelled
> explicitly as the state at carrier `8ddcbfa`. The ledger has since been reconciled forward on a
> descendant (v0.21.0: 87 entries, 58 resolved, 29 open, 62 self-directed, convergence predicate
> still 0). Descendant bookkeeping does not rebind the carrier, and the figures below are left at
> their qualified values on purpose.

## Qualified subject

The qualified subject is the immutable carrier commit
`8ddcbfacef2468b8988c331c30100d72f0912eb8`, tree
`c3e05bddcdb59c578cd406d28da8247d243c5c59`.

This document and the evidence files below are published by a descendant commit. They describe
that named carrier; they do not rebind the qualification to the publication commit. The carrier's
acceptance contract, executable manifest, runner, root README and frozen mutation targets remain
unchanged.

## Exit-condition evaluation

| Condition | Evidence | Result |
| --- | --- | --- |
| 1. Network-free contracts from a literal clean archive | `git archive` of the carrier; 185 tests; root crate 0 stale/0 missing | **pass** |
| 2. C9 against live providers | README steps 0–7; 66/66 provider attempts; 0 interventions; 0 route substitutions | **pass** |
| 3. Convergence predicate | 85 entries; 56 resolved; 60 self-directed; open + `changes_result` + `current_defect` = 0 — **the ledger state at carrier `8ddcbfa`**, deliberately unchanged; later descendant reconciliation does not rebind the carrier | **pass** |
| 4. Frozen manifest behaves as registered | Calibration and both qualifiers: 25/25 cases, 21 detected, 4 registered non-detections, 0 `not_executed`, 25 resets | **pass** |
| 5. Two bounded audits | Two byte-distinct reports from distinct clean checkouts; no failed case or new high-severity current defect | **pass (2/2)** |

The fifth-checkout validator independently revalidated the entire tuple and returned
`Phase-0 qualification evidence: PASS (2/2)`.

## Immutable evidence

| Artifact | SHA-256 |
| --- | --- |
| [`c9-8ddcbfa-1.json`](audit/evidence/c9-8ddcbfa-1.json) | `8d018fa9dfcaadfef0e08451632cda3860aaacca2986f1d9206e640af83d1452` |
| [`calibration-8ddcbfa-1.json`](audit/evidence/calibration-8ddcbfa-1.json) | `e909238182963024a3a33db1bd527261d249531474abe472c6424524839884dc` |
| [`qualifying-8ddcbfa-1.json`](audit/evidence/qualifying-8ddcbfa-1.json) | `acc0ef4d18da8e76cdf540aa6baae3771ccba0166f7e0e397e5af3be2afe719c` |
| [`qualifying-8ddcbfa-2.json`](audit/evidence/qualifying-8ddcbfa-2.json) | `43c61b44eb054b6f585cd7290bf0b740b5b5455f5d400d53b44e99fcca484a96` |
| [`qualification-8ddcbfa.json`](audit/evidence/qualification-8ddcbfa.json) | `db0d5a81537d30eed89440ee7ae5dc49f15925a26917c883b517ed45126c0618` |

## Scope of the claim

This closes the bounded Phase-0 software and evidence-lock scope. It does not turn provider
incompleteness into completeness. The VLBI downstream analysis product, downstream IERS EOP
series, four depositor question groups and IPTA upstream report remain carried into later work.
The scientific result remains `no_common_support` over MJD 59630–59640.

The append-only execution narrative is
[`labnotes/2026-08-27-session-20-phase0-qualified.md`](../labnotes/2026-08-27-session-20-phase0-qualified.md).
