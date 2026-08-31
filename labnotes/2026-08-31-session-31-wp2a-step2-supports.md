# Session 31 — WP2A Step 2 supports, within its registered provenance bound

**Date:** 2026-08-31 · **Branch:** `phase2` · **Task:** WP2A Step 2
**Outcome:** single registered execution returned `step2_supports`
**Licence:** CC BY 4.0

---

## 00 — Subject and execution

The v1.3.2 instrument was committed and published before execution:

- subject commit: `1d4bc31c6e73bec9e1717e64d5c09e526b75b64b`;
- subject tree: `eb1acbddda0e1be2181e97fd5ba7356bd70ee09f`;
- published containment: `origin/phase2`;
- registration-manifest SHA-256:
  `703b655078d0ff55c71462c7c931b20369bc01e0eba380818487f4265375868c`; and
- worktree clean before provider input access.

`python3 phase2/wp2a/run_step2_v1_3.py run` was invoked once. It exited 0 and atomically created
`phase2/wp2a/reports/step2-input-evidence-v1.3.json`. No rejected report was produced.

Run interval: `2026-08-31T12:39:19.985283Z` to `2026-08-31T12:39:22.207392Z`.

---

## 01 — Input and target results

All four outer inputs authenticated against their frozen SHA-256 and size. Every postflight path
still matched the captured snapshot; `n_inputs_changed_during_run` is zero.

| Target | Method agreement | Expected match | Observed decoded/member state |
| --- | --- | --- | --- |
| `decoded:igs21982.clk.Z` | direct byte equality | yes | 6,037,296 B · `b3145e51…a1137ba` |
| `decoded:igs21983.clk.Z` | direct byte equality | yes | 6,071,695 B · `8ac65974…77e3ab` |
| `decoded:igr21991.clk.Z` | direct byte equality | yes | 4,000,804 B · `aa5e471c…f89a01` |
| `member:rocit-zip` | direct byte equality | yes | 780,292 B · `00cc90d8…5363c067` |

Counters: four targets, four supports, zero contradictions, zero evidence-assurance failures, zero
non-executions and zero changed inputs. Overall outcome: `step2_supports`.

---

## 02 — What the optical match does and does not say

The report carries the exact registered `outcome_interpretation_bound`; it is not commentary added
after seeing the result. The optical result establishes that Python `zipfile` and system `unzip -p`
consumed the same authenticated container bytes, agreed byte-for-byte and reproduced the committed
digest and size.

It does **not** establish independent derivation of that expectation, the external timestamp of the
prior observation, or provider attestation of the member value. The expected value's process
provenance remains `attested_not_repository_checkable`, and the present ignored extracted copy's
origin remains unestablished by repository evidence.

This is the evidentially bounded `step2_supports` anticipated in Session 29, not a stronger claim.

---

## 03 — Validation and one command-line dead end

The runner's own `check` command validated the report. An initial standalone-check invocation used
`--check-report` without its required positional value while also supplying `--out`; argparse
exited 2 without reading or changing evidence. Re-running the documented form with the report path
returned PASS.

Report SHA-256:
`67111c699372237192588771332ff14704279a6dd8fbaf0f60ee356f63bf725c`.

The next admissible trial action is contract §9 step 4: bind and synthetic-test the evaluator before
any fixture exists. No mapping, evaluator, fixture or mutation execution occurred in this session.

---

## 04 — The first post-publication suite exposed its own lifecycle assumption

The initial full suite after report creation ran 252 tests and produced one error. A test of the
global input-preflight fold called `build_report()` against the real official path; now that the
immutable report exists, the earlier refuse-overwrite guard correctly stopped it. Two other tests
also reached that guard but passed because they asserted only a broad `CheckError`, making them
false passes for their named unpublished-subject and descriptor-preflight branches.

This is `FTRO-P1-DEF-023`, not a Step-2 finding. Each branch test now uses a temporary synthetic
official path and asserts its specific diagnostic. A separate test asserts that a real existing
official report stops before subject or input access. The immutable report, its carrier and every
instrument byte remain unchanged; Step 2 is not rerun.

---

## 05 — Ledger boundary

Before Step 2, supplement v0.12.0 was committed at `1d4bc31`. Its exact 22-entry bytes are retained
as `ledgers/phase1-deficiency-log-at-1d4bc31.json`, SHA-256
`c3e6b58ef3d75b203ad6a4971f8e6a68e2c9b111aec75ed3fb0d9f735071ffcf`, and reconciled into unified
ledger v0.26.0: 98 entries, 69 resolved, 29 open, 73 self-directed, convergence 0, seven retained
merge sources.

`FTRO-P1-DEF-023` begins the next supplement interval at v0.13.0. It is deliberately not folded
into the earlier snapshot: doing so would rewrite the source chronology the snapshot exists to
preserve.

---

## 06 — Publication gates

After the lifecycle-test repair:

- main suite: 253 tests, zero failures and zero skips;
- Phase-1 suite: 48 tests, zero failures and zero skips;
- all five v1.3 generators: PASS;
- subject-bound Step-2 report checker: PASS;
- Gate-1 structural/source and SIO report freshness/content: PASS;
- version gate: three changed versioned artifacts, zero stale;
- root crate: zero stale, zero missing;
- every manifest-bound instrument artifact and the manifest itself are byte-identical to carrier
  `1d4bc31`; and
- `git diff 1d4bc31 -- phase0/`: empty.

The live supplement is v0.13.0 with 23 entries, 17 resolved, six open and 23 self-directed. Its new
resolved test finding awaits the next standing-rule snapshot; the canonical v0.26.0 totals remain
the committed-snapshot totals stated in §05.
