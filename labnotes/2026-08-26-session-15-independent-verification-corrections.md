# Session 15 — Independent verification corrections: audit reset and durable Gate-1 witnesses

**Date:** 2026-08-26 · **Branch:** `phase1` · **Phase-1 parent:** `028c317ff1db27577617b8c3d2ff105da77b6739`  
**Phase-0 baseline:** `main` remains at `a806bbaa573d28f1460d18110f7974189ca19213`  
**Outcome:** the qualifying Phase-0 audit count is corrected from 1/2 to **0/2**; Gate-1 retrieval is now runnable from both an exact parent overlay and a clean descendant commit; all quoted retrieval counters are derived and checked.  
**Licence:** CC BY 4.0

> **Append-only correction.** Session 14 is not edited. This note supersedes its §02 and §07
> statements that one clean audit had been achieved, and its 36-test count. The incorrect belief
> remains visible at its knowledge time.

---

## 00 — Independent verification, not summary acceptance

The external review recomputed all 69 retrieval results, all aggregate counts, the byte total, ten
input hashes, the report digest and both test suites. Those claims reproduced exactly. It also
reproduced the C9 `unzip` failure and established why a clean export lacks `data/`: the directory is
gitignored and Info-ZIP 6.00 does not recursively create the missing destination parents.

Three review findings remained:

1. the audit counted as the first clean run was itself selected retrospectively;
2. Gate-1 preflight accepted only an uncommitted overlay and rejected a clean published carrier;
3. three quoted report counters were correct but not verified.

`FTRO-P1-DEF-007` is revised to v3.0.0 and resolved. `FTRO-P1-DEF-009` is revised to v2.0.0 and
remains open.

---

## 01 — Neither historical audit qualifies

The previous 1/2 arithmetic cannot survive the concrete pre-registration standard already stated
in `FTRO-P1-DEF-009`.

The Git chronology is dispositive:

- `f767457` introduced the semantic fault model and completed run-1 report in the same commit;
- `97553a2` amended the model and report together after M12c was found;
- `a806bba` introduced the corrected acceptance scope, the fixes, the complete run-2 result and
  the claim that run 2 was the first clean audit in the same commit.

Run 2 also contains M1b and M1c, neither of which appears in any fault-model version, and chooses
the explicit-digest route for M11 after run 1 exposed that route. The model still says only “any
pinner” and supplies no exact file/field, mutation value, detecting command, reset boundary or
report destination.

Both runs remain useful retrospective diagnostics. Neither is a pre-registered audit. Therefore:

- exit condition 4 is **not demonstrated**;
- exit condition 5 stands at **0/2**;
- one executable audit manifest must be frozen before execution; and
- that unchanged manifest must then produce two separately recorded clean runs.

The Phase-0 contract, fault model and historical audit report remain untouched under the isolation
rule. The corrected current state is recorded in
[`FTRO-P1-DEF-009`](../phase1/deficiency-log-phase1.json) and the amended
[`phase0-c9-attempt-2026-08-26.json`](../phase1/reports/phase0-c9-attempt-2026-08-26.json).

---

## 02 — Candidate identity is not checkout form

The prior preflight accepted only this transient state:

```text
HEAD = Phase-1 parent + six modified/untracked Gate-1 files
```

A clean commit containing exactly those bytes had no worktree overlay and a different HEAD, so it
was rejected. The purported clean procedure therefore became unrunnable as soon as its code was
committed.

The stable candidate identity is now:

```text
(Phase-1 parent commit, SHA-256 fingerprint of the ten captured Gate-1 inputs)
```

Checkout form is a separately recorded execution witness:

| Witness | Required evidence before any request |
| --- | --- |
| `parent_overlay` | no `data/`; HEAD is `028c317`; changed/untracked paths equal the six candidate input files |
| `committed_checkout` | no `data/`; clean worktree; HEAD descends from `028c317`; all six candidate paths differ from the parent |

Both forms capture and hash the same ten inputs. A committed carrier may also contain output files
such as the report, README, ledger and lab notes; those are not retrieval inputs. No future
publishing hash is embedded in the pre-commit report: including a report's own containing commit
inside that report would create a cryptographic fixed-point problem. The exact execution HEAD is
recorded as witness evidence instead.

Mutation tests now:

- run the production retrieval/report path from a synthetic clean descendant commit;
- verify the parent-overlay report against the same committed bytes;
- reject a clean non-descendant carrying the files;
- reject a dirty committed checkout, wrong parent, extra overlay and present `data/`; and
- reject publication of a new PASS that fails its own consumer.

The current live report is explicitly a `parent_overlay` witness. It binds the checker, test file,
four manifests, identities and three frozen catalogs. It does **not** claim that the whole authoring
worktree was tested: `phase1/README.md`, the Phase-1 ledger and other output documents were at their
parent versions in the retrieval clone and do not affect source retrieval. After publication, a
third party can rerun with `--source-state committed_checkout` from the published clean descendant;
that new witness records its exact HEAD.

---

## 03 — Every quoted aggregate is now a checked projection

The verifier previously checked every row and `n_sources`/`n_failed`, but did not check the three
headline fields quoted in prose. It now recomputes, with exact-integer checks:

- `n_sources` from `len(results)`;
- `n_provider_sources` and `n_source_catalogs` from each row's role;
- `n_retrieved_and_matched` only when outcome, Boolean checksum result and digests all agree;
- `n_failed` as total minus fully matched; and
- `gate1_retrieval_status` from the recomputed success count and clean witness type.

Tests remove, falsify and Boolean-substitute every count; preserve the provider/catalog sum while
making both components wrong; duplicate a result; and turn one row into a coherent failure while
leaving the success headlines unchanged. All are rejected.

---

## 04 — Final bounded rerun

The captured-input change invalidated the previous report as designed, so the live retrieval was
run again from the exact parent overlay:

| Quantity | Recomputed result |
| --- | ---: |
| Provider sources | 66 |
| FTRO catalogs at the frozen baseline | 3 |
| Retrieved and matched | 69/69 |
| Failed | 0 |
| Bytes streamed | 140,736,196 |

All results report HTTP 200, `outcome: retrieved`, `checksum_match: true`, and equality between
observed and expected SHA-256. The three catalogs demonstrate that FTRO's pin reports are published
at immutable baseline URLs; they are not independent provider artifacts. Fifty-seven of the 66
provider sources are catalog-backed GNSS entries, with five GNSS exemplars represented as graph
entities.

- executed: `2026-08-26T16:37:58.272503+00:00`
- input fingerprint: `777f02bf2896a19d4621fc09c445a85ca810f1bf3c00714964e48ee1082e8053`
- report SHA-256: `54102b575d4516a9685d78237025eef5debb9113922caee82c0813c33fdd9688`
- Phase-1 tests: **43**, zero skips
- unchanged Phase-0 tests: **97**, zero skips
- production freshness/content check: **PASS**
- root-crate isolation exception: only `labnotes/README.md` is stale (`3333 → 3804`); zero missing;
  the Phase-0 crate was not refreshed

Durable report:
[`gate1-clean-retrieval-v1.0.json`](../phase1/reports/gate1-clean-retrieval-v1.0.json).

---

## 05 — Corrected boundary

| Claim | Status |
| --- | --- |
| Gate-1 source location for the ten-input candidate | **pass, parent-overlay witness** |
| Clean committed-checkout procedure | **implemented and mutation-tested; live rerun awaits publication** |
| RO-Crate 1.3 conformance | **not demonstrated** |
| Phase-0 C9 | **failed as written** |
| Exit condition 4 | **not demonstrated** |
| Qualifying bounded audits | **0/2** |
| Profile v0.0.4 amendment | **deferred** |

The next Phase-0 boundary is now exact: add the one missing README directory-creation command and
rerun C9; freeze one executable audit manifest and run it twice without changing it. Only after
those operations should the Phase-0 artifacts be amended and the Phase-1 profile amendment applied.
