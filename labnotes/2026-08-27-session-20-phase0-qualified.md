# Session 20 — Phase 0 qualified and closed

**Date:** 2026-08-27
**Branch:** `phase0-closure`
**Qualified carrier:** `8ddcbfacef2468b8988c331c30100d72f0912eb8`
**Carrier tree:** `c3e05bddcdb59c578cd406d28da8247d243c5c59`
**Status:** **Phase 0 complete; bounded audits 2/2**
**Licence:** CC BY 4.0

> **Append-only.** This note follows session 19. The evidence-publication commit is a descendant
> describing the named carrier; it is not silently substituted as the audited subject.

## 00 — The carrier passed the no-Git boundary

Commit `8ddcbfa` was exported with literal `git archive` into
`/tmp/ftro-archive-8ddcbfa.mwfEj6`. With no repository metadata present, the network-free suite
ran **185 tests with zero failures or skips**. `refresh_crate.py --check` reported 0 stale and 0
missing. This demonstrates acceptance condition 1 for the carrier rather than for its preparation
worktree.

## 01 — C9 passed once, live, without intervention

`c9-8ddcbfa-1` ran from a fresh detached checkout between 14:50:08 and 14:53:09 UTC. All README
steps 0–7 completed. The report records:

| Evidence | Result |
| --- | --- |
| Provider attempts | 66 recorded / 66 successful |
| Population | 57 IGS, 4 PPTA, 3 evidence repositories, 1 vgosDB, 1 optical archive |
| IGS route | SIO/SOPAC GARNER; 57 HTTP 200; no redirect |
| Manual intervention / route substitution | 0 / 0 |
| Deterministic outputs | 5 / 5 byte-identical |
| Provider bytes retained | 0 |
| Report SHA-256 | `8d018fa9dfcaadfef0e08451632cda3860aaacca2986f1d9206e640af83d1452` |

The report binds carrier commit `8ddcbfa`, tree `c3e05bdd`, the eight-step README command block,
97 bound inputs, all 65 registry pins plus the optical archive, toolchain evidence and cleanup.

One dead end is retained. After C9 passed, I invoked `run_c9.py --check-report`; that interface
does not exist, so argparse rejected the command because `--run-id` and `--out` were absent. It
changed no repository or evidence byte. The strict C9 consumer is `phase0/audit/run.py`, which
validated the report before calibration and again before each qualifying run.

## 02 — Calibration separated instrument debugging from qualification

The frozen manifest ran once in a second clean checkout as `calibration-8ddcbfa-1`. It passed:

```text
overall=pass detected=21 not_detected=4 not_executed=0
```

Every one of the 25 mutations changed its target digest and produced a diff digest; every case
reset to the carrier fingerprint. The four non-detections are the registered M6, M7, M8 and M12c
outcomes, not recipes that failed to execute. Calibration SHA-256:
`e909238182963024a3a33db1bd527261d249531474abe472c6424524839884dc`.

## 03 — Two qualifying runs reproduced the frozen result

Only after calibration completed did two further detached checkouts run the unchanged manifest:

| Run | Observation counts | Reset proofs | SHA-256 |
| --- | --- | --- | --- |
| `qualifying-8ddcbfa-1` | 21 detected / 4 not detected / 0 not executed | 25/25 | `acc0ef4d18da8e76cdf540aa6baae3771ccba0166f7e0e397e5af3be2afe719c` |
| `qualifying-8ddcbfa-2` | 21 detected / 4 not detected / 0 not executed | 25/25 | `43c61b44eb054b6f585cd7290bf0b740b5b5455f5d400d53b44e99fcca484a96` |

Both reports bind the same carrier and frozen manifest, but have distinct run IDs, bytes and
checkout identities. Neither produced a failed case or a new high-severity current defect.

## 04 — The fifth checkout closed the tuple

A fifth clean checkout ran `check_qualification.py` over C9, calibration and both qualifiers. It
deeply revalidated all reports and returned:

```text
Phase-0 qualification evidence: PASS (2/2)
```

The final report records distinct report digests, run IDs, checkout identities, a distinct
checker checkout and calibration-before-qualification chronology. SHA-256:
`db0d5a81537d30eed89440ee7ae5dc49f15925a26917c883b517ed45126c0618`.

## 05 — Exit decision

All five conditions in acceptance contract v1.3.0 hold for carrier `8ddcbfa`. Phase 0 is complete.
The descendant publication keeps the carrier-bound contract, manifest, root README, runner and
mutation targets unchanged and adds only evidence, this append-only note, and a status evaluation.

Open provider incompleteness remains the scientific deliverable: the VLBI downstream analysis
product and IERS EOP series, four depositor question groups and the IPTA upstream report. Phase 1
can resume without reopening Phase 0 unless a finding meets the contract's explicit blocking
predicate.
