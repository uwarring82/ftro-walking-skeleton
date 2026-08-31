# Session 30 — WP2A v1.3.2: the input that made its clean carrier dirty

**Date:** 2026-08-31 · **Branch:** `phase2` · **Task:** Step-2 acquisition readiness
**Outcome:** v1.3.1 superseded before execution; clean-compatible v1.3.2 prepared
**Licence:** CC BY 4.0

---

## 00 — Readiness check, not a Step-2 run

After publishing v1.3.1 at `1b9e056`, a read-only readiness check confirmed a clean branch and no
official or rejected Step-2 report. The three IGS inputs existed at their registered ignored paths.
The optical ZIP did not exist at the registered repository-root path, but the authenticated local
copy existed at:

`data/raw/zenodo-17107693/ROCIT campaign results.zip`

The Step-2 `run` command was not invoked. No registered decoder or extractor ran, and no evidence
report was minted.

One dead end in that readiness command is recorded because the lab-note rule requires it: a zsh
loop variable named `path` overwrote zsh's special `$path` array, so three `stat` invocations
reported `command not found`. The subsequent `rg --files -uu` path enumeration did not reuse that
name and established the four file locations. This shell mistake changed no file and was not an
instrument execution.

---

## 01 — The registered preconditions contradicted each other

v1.3.1 required both of the following before any provider input opened:

1. `clean_published_subject()` must observe an empty
   `git status --porcelain=v1 --untracked-files=all`; and
2. `ROCIT campaign results.zip` must already exist at repository root.

The root filename is neither tracked nor ignored. Supplying it therefore makes condition 1 false.
The only way to execute v1.3.1 would have been unregistered local state such as `.git/info/exclude`,
or a dirty-tree exception. Neither was used. The carrier was internally unexecutable even though
its target digest, methods and report semantics were sound.

Evidence: `phase2/wp2a/step2-schema-v1.3.json#/x-ftro-registration/input_policy/population/3` at
carrier `1b9e056`; `phase2/wp2a/run_step2_v1_3.py#clean_published_subject`; `.gitignore`;
`FTRO-P1-DEF-022`.

---

## 02 — v1.3.2 removes the contradiction

The registered optical input path now names the existing ignored location under
`data/raw/zenodo-17107693/`. The outer SHA-256, size, route, member selector, imported member
expectation, extraction methods, interpretation bound and outcome precedence are unchanged.

A committed test now enumerates all four registered provider-input paths and asks Git's own ignore
engine whether each is ignored. This is the property the clean-subject gate relies on. A future
input-path edit that recreates the v1.3.1 contradiction fails before publication.

Because no Step-2 execution began, v1.3.2 is another pre-execution patch amendment. v1.3.1 remains
inspectable at `1b9e056` and is explicitly marked superseded rather than silently rewritten.

---

## 03 — Pre-publication verification

- main suite: 252 tests, zero failures and zero skips;
- Phase-1 suite: 48 tests, zero failures and zero skips;
- all five v1.3 generators and the Step-2 registration checker: PASS;
- Gate-1 structural/source and SIO report freshness/content: PASS;
- version gate: three changed versioned artifacts, zero stale;
- root crate: zero stale, zero missing;
- `git diff -- phase0/`: empty; and
- v1.3.2 registration-manifest SHA-256:
  `703b655078d0ff55c71462c7c931b20369bc01e0eba380818487f4265375868c`.

Step 2 remains unexecuted until this exact carrier is committed and published.
