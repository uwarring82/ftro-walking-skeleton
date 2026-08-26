# Session 14 — Boundaries executed: C9 fails, Gate 1 source location passes

**Date:** 2026-08-26 · **Branch:** `phase1` · **Phase-1 parent:** `028c317ff1db27577617b8c3d2ff105da77b6739`  
**Phase-0 baseline:** `main` remains at `a806bbaa573d28f1460d18110f7974189ca19213`  
**Outcome:** the exact Phase-0 cold path fails; the second audit is not executable as pre-registered; the bounded Gate-1 source clause passes 69/69; RO-Crate 1.3 conformance remains unverified.  
**Licence:** CC BY 4.0

> **Append-only correction.** Session 13 is not edited. Its claims that no validator was obtainable,
> that profile §4 was literally unsatisfiable, and that the four manifests passed a sufficient
> structural self-check were wrong or too strong. This session preserves and corrects them.

---

## 00 — Isolation held

Phase-0 closure ran in an isolated clone of `main` at `a806bba`. Gate-1 work stayed under
`phase1/` plus this append-only note. The shared `main`, `src/`, `tests/`, `phase0/`, `ledgers/`
and `profile/` trees were not edited.

The append-only note/index is the declared exception to “everything under `phase1/`”. Consequently
`refresh_crate.py --check` on the Phase-1 branch reports the root crate's
`labnotes/README.md` size as stale (`3333 → 3615`). Refreshing the root crate would modify a
Phase-0 artifact, so the stale branch-local size is recorded and deferred; the isolated `main`
baseline used for C9 reported zero stale and zero missing entries.

The current branch still points to `028c317`; the work in this session is an uncommitted candidate.
The retrieval report therefore calls its source state an **isolated export**, not a committed clean
checkout.

---

## 01 — C9 was finally executed, and failed

Execution window: `2026-08-26T13:26:55Z`–`13:31:02Z`; Darwin arm64; Python 3.13.7;
locale C.UTF-8. The exact record is
[`phase0-c9-attempt-2026-08-26.json`](../phase1/reports/phase0-c9-attempt-2026-08-26.json).

| README step | Result |
| --- | --- |
| 0 | 97 tests, exit 0, zero skips |
| 1 | evidence repositories 3 pinned / 0 failed / 0 uncovered |
| 2 | GPS→UTC verification exit 0; committed evidence reproduced byte-for-byte |
| 3 retrieve/hash | Zenodo archive matched MD5 `4ae290f559c90b462991286c933a1147` and SHA-256 `6168e24a…56bd` |
| 3 unzip | **exit 2** |
| 3 after manual `mkdir` | unzip, optical analysis and summary exit 0 |
| 4 | IGS 57/0/0; vgosDB 1/0/0; PPTA 4/0/0; every checksum match exactly true |
| 5 | `no_common_support`; zero four-domain intervals; pulsar→optical gap 31.174 h |
| 6 | both renderers exit 0 |
| 7 | zero stale versions; zero stale or missing crate records |

The failing documented command was:

```text
unzip -d data/raw/zenodo-17107693/extracted "ROCIT campaign results.zip"
checkdir: cannot create extraction directory: data/raw/zenodo-17107693/extracted
No such file or directory
exit 2
```

No earlier command creates `data/raw/zenodo-17107693`. Adding
`mkdir -p data/raw/zenodo-17107693` proved the remainder of the pipeline, but C9 says every
documented command runs from a clean export. The diagnostic continuation is not a qualified pass.

The four timestamp-bearing fresh reports equal the baseline after recursively removing only
`retrieved_utc`. Deterministic outputs remained byte-identical:

| Artifact | SHA-256 |
| --- | --- |
| `phase0/evidence/VA-GPS2UTC-001.json` | `151de33f2b395b9739ef78a1a34e92250cb59417758ed31989a336790e9b899d` |
| `phase0/reports/four-domain-intersection.json` | `f5b6ab85e8be01a7b26d50f18ebaa8aff9c9256c0359ded4996aa8797a40d2de` |
| `ledgers/deficiency-log.md` | `ff043710e63e4f4e4c13cdb3b6e07a1bb8c91109b6ea73ca0eb12cac6168ab56` |
| `phase0/optical-validity-intervals.md` | `bf45394d173767f43f17d1a58f36b9f8161b9ddea4107212ecf02ca389029029` |

### Reproduction dead end retained

The first attempt to reproduce only the unzip failure cloned a new tree and copied the verified
archive, but accidentally invoked `unzip` from the source checkout. It exited 9 because that
working directory had no archive. Re-running from the new clone, whose `data/` directory was
absent, reproduced the original exit 2 exactly. The exit-9 attempt is not folded away.

Filed as [`FTRO-P1-DEF-008`](../phase1/deficiency-log-phase1.json).

---

## 02 — The second audit was not started

The fault model pre-registers semantic operators M1–M13, but not one exact execution recipe for
each: target file/field, replacement value, choice among “or” alternatives, detecting command,
reset boundary and report destination are missing. Selecting those details after inspecting the
implementation would be a post-hoc audit.

The fail-closed action was to stop. Before run 3, freeze a finite execution manifest, execute it
once in isolated copies, report every result and stop. Phase-0 exit condition 5 remains at one
clean audit of two. Filed as `FTRO-P1-DEF-009`.

---

## 03 — Three session-13 corrections

### 03.1 A validator is obtainable

`roc-validator` 0.11.3 installs in a temporary virtual environment. It provides RO-Crate 1.1 and
1.2 profiles, not the pinned 1.3 base. The correct statement is **normative validation not run**, not
“no validator obtainable”. RDFLib 7.6.0 parses all four JSON-LD files, but parsing is not RO-Crate
conformance. `FTRO-P1-DEF-001` is revised to v2.0.0.

### 03.2 §4 is under-specified, not impossible

JSON-LD can represent a relation with attributes by reifying it as a node. The defect is that the
profile says every edge carries four times while declaring no relation-assertion class,
subject/predicate/object cardinality, direct-triple policy or RDF-level unresolved/open-bound
semantics. The provisional `ftro:Edge` proves one encoding, not the encoding. Also, JSON-LD null
disappears at RDF expansion, so “required and nullable distinguishes silence” was wrong.
`FTRO-P1-DEF-002` is revised to v2.0.0.

### 03.3 Frequency was not semantic coverage

The 13/21 edge and 28/41 node figures counted names across whole files. They do not establish that
a term was exercised, why an unused term is absent, which entity kind owns a common field or that
four occurrences warrant a MUST. The proposed `exercised` flags and 21 universal required fields
are withdrawn. `FTRO-P1-DEF-004` is revised to v2.0.0.

The corrected assessment is
[`vocabulary-pressure-v1.1.md`](../phase1/reports/vocabulary-pressure-v1.1.md). Version 1.0 remains
as the historical first assessment.

---

## 04 — The first manifests and first Gate-1 checker did not support their PASS

The four initial manifests contained 13 anonymous nested records despite RO-Crate’s flattened
form, omitted a typed Profile entity in every crate, mixed base/profile conformance declarations,
and linked the same VLBI V004 wrapper twice while omitting V005. The original self-check did not
test those properties. Filed and resolved as `FTRO-P1-DEF-006`.

The first replacement checker then repeated projection-only verification:

- it constrained source **counts**, so a digest-correct README could replace `gps2utc` and pass;
- it accepted JSON `false` as integer zero;
- it did not reconcile VLBI wrapper digest, member path or size;
- it validated source reports and reopened them later for retrieval; and
- it did not fingerprint the inputs behind a PASS report.

The concrete `gps2utc → README` substitution and a corrupted wrapper both passed before repair.
Filed and resolved as `FTRO-P1-DEF-007`.

The bounded checker now:

1. captures the checker, its mutation tests, four manifests, identities and three frozen reports
   once;
2. binds their path/digest map to one input fingerprint;
3. compares the exact `(domain, role, identifier, URL, SHA-256)` source set;
4. reconciles the four PPTA members, five VLBI wrapper states/seven paths, six GNSS product-line
   counts and represented exemplars;
5. constrains the exact JSON-LD context and minimum root/report/assertion structure;
6. makes report freshness and result population executable; and
7. proves the clean-export state from the absence of `data/`, the exact Git parent and the exact
   six-file overlay before any network request.

The bounded recheck found one remaining branch in `FTRO-P1-DEF-007`: report creation trusted the
caller's `isolated_export` label and did not run the later report verifier before writing. It could
therefore publish a PASS with `data/` present that its own consumer rejected. The entry was reopened
at v2.0.0 and resolved by preflight plus promotion through the shared verifier. The registered
recheck then passed; no new open-ended search was added.

Thirty-six Phase-1 tests include the demonstrated substitutions, post-validation report
replacement, context redefinition, boolean counter, wrapper, concept-count, reachability and
stale-report mutations, plus wrong-parent, extra-overlay and `data/`-present source states. All
pass. The unchanged Phase-0 suite remains 97/97.

This scope is finite: it is a source-accounting and selected-projection check, **not** a general
RO-Crate or FTRO-profile validator. GNSS’s 57 provider artifacts are catalog-backed; five exemplars
are graph entities. Full 57-node graph materialisation is not claimed.

---

## 05 — Gate-1 retrieval result

The candidate files were overlaid into an isolated local clone of the Phase-1 parent. Before any
request, the checker itself established HEAD `028c317ff1db27577617b8c3d2ff105da77b6739`, no `data/`
directory and exactly the checker, its test file and four manifests as changed paths. The checker
then streamed every target to SHA-256 and retained no provider bytes.

| Domain | Provider sources | FTRO catalogs | Matched |
| --- | ---: | ---: | ---: |
| optical | 3 | 0 | 3 |
| pulsar | 5 | 1 | 6 |
| VLBI | 1 | 1 | 2 |
| GNSS | 57 | 1 | 58 |
| **Total** | **66** | **3** | **69/69** |

The run streamed 140,736,196 bytes. Durable report:
[`gate1-clean-retrieval-v1.0.json`](../phase1/reports/gate1-clean-retrieval-v1.0.json).

- executed: `2026-08-26T14:29:13.721771+00:00`
- input fingerprint: `15ed7126690c3ee3d23563227909da0e1802c23c0d53a609be829ec77b6588eb`
- report SHA-256: `c2d7eb58ff04ede67a07f3dacd999af02f950a4af6f06b9bb58c367793fe183c`
- `python3 phase1/check_gate1.py --check-report ...`: **PASS**

Gate 1’s source-location clause is therefore demonstrated for this candidate. Unresolved provider
evidence stays unresolved; no source was substituted.

---

## 06 — Validation evidence, including dead ends

The first compatibility command used the nonexistent plural option
`--skip-availability-checks`; the CLI exited 2 and suggested singular
`--skip-availability-check`. The next run forced the 1.2 profile directly onto the 1.3 documents;
that predictably included a context-version failure and was not a valid compatibility export.

The retained non-normative export changed only the context URI and descriptor `conformsTo` from
1.3 to 1.2. All four still fail under `roc-validator` 0.11.3:

| Domain | Required issues | Main checks |
| --- | ---: | --- |
| optical | 76 | compact context 70; unresolved software shape 6 |
| pulsar | 81 | compact context 81 |
| VLBI | 73 | compact context 73 |
| GNSS | 64 | compact context 63; URI-string/reference 1 |

This is amendment pressure, not a normative 1.3 verdict. Exact settings and counts:
[`ro-crate-validation-v1.0.json`](../phase1/reports/ro-crate-validation-v1.0.json).

---

## 07 — Status and next boundary

| Claim | Status |
| --- | --- |
| Four hand-authored manifests exist | yes |
| Exact source population can be located from a data-free isolated export | **yes, 69/69** |
| Gate 1 source-location clause | **pass** |
| RO-Crate 1.3 conformance | **not demonstrated** |
| Phase-0 C9 | **fail** |
| Second clean bounded audit | **not run; recipe missing** |
| Profile v0.0.4 amendment | **deferred** |

The Phase-1 ledger now has 9 entries: 2 resolved and 7 open; all are self-directed. The open set
includes assurance/schema questions plus the two Phase-0 workflow blockers. The genuinely external
science gaps are unchanged: VLBI downstream analysis and IERS EOP series, four depositor question
groups, and the IPTA upstream report.

The next correct action is not another open-ended review. It is two finite Phase-0 operations on
the frozen baseline: add the missing README directory-creation step and rerun C9; freeze exact
audit recipes and execute them once. Only then should the profile amendment be applied.
