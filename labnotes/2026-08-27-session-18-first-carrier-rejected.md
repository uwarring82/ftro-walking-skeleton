# Session 18 — first closure carrier rejected by its clean-archive gate

**Date:** 2026-08-27  
**Branch:** `phase0-closure`  
**Rejected carrier:** `fdd2f6a`  
**Status:** C9 not started; calibration not run; qualifying audits **0/2**  
**Licence:** CC BY 4.0

> **Append-only.** This note starts after session 17 and does not rewrite its successful
> preparation-tree result. The distinction between that result and the committed archive result
> is the finding.

## 00 — The carrier existed, so condition 1 could finally be tested literally

The preparation tree passed 175 tests, the version gate, root-crate freshness and the whitespace
check. It was committed as `fdd2f6a` and immediately exported with:

```text
archive_dir=$(mktemp -d /tmp/ftro-archive-check.XXXXXX)
git archive HEAD | tar -x -C "$archive_dir"
cd "$archive_dir"
python3 -m unittest discover -s tests
```

Result: **175 run, 5 errors**. Every error came from
`tests/test_phase0_c9_contract.py:carrier_context()`, which invoked `git rev-parse HEAD` against the
archive. The other 170 tests completed successfully. This is `FTRO-DEF-073`.

The failure is not a technicality. Acceptance condition 1 names a clean `git archive` precisely so
the network-free suite cannot borrow state from the source checkout. Five tests for the strict C9
contract did exactly that. A source-tree PASS was therefore insufficient evidence, and `fdd2f6a`
is rejected as the closure carrier.

## 01 — The repair removes the hidden dependency

The strict-contract tests now build a minimal temporary Git repository from exported files. It
contains the README, acceptance contract, live runner, expected-digest registry and four committed
pin reports used by the validator. The fixture is committed with isolated Git identity and config;
all commit/tree, population and dirty-worktree assertions execute against it. Nothing is written
into the source tree, and the test no longer depends on a parent `.git` directory.

This is a test-environment repair, not a weakening of C9. Production C9 still requires a clean
detached checkout and binds the complete carrier tree. The temporary repository exists only so
the network-free contract tests can exercise Git-scoped validation from their declared archive
environment.

The executable manifest advances from 1.0.0 to **1.0.1** because recording this committed defect
changes the root README digest targeted by M12c and M13. The 16 operators, 25 concrete cases,
mutations, detectors and expected outcomes are unchanged. Rebinding a changed target without a
manifest version advance would itself violate C10.

## 02 — Consequence for sequencing

No provider request, C9 report, calibration or qualifying report was made against `fdd2f6a`.
Therefore nothing needs rebinding or invalidating beyond the carrier itself. The required sequence
remains:

1. freeze the repaired descendant;
2. pass the complete suite from that commit's literal archive;
3. run live C9 from a fresh detached clone;
4. run one non-qualifying calibration; and
5. run two qualifying audits and the final checker in three further distinct clones.
