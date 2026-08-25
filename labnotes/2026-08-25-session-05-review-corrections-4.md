# Session 05 — Fourth external review: projection-only verification

**Date:** 2026-08-25 · **Reviews:** commit [`1b77a72`](https://github.com/uwarring82/ftro-walking-skeleton/commit/1b77a7267f63124587d82298b9dd4b92914ec2a4)
**Outcome:** scientific result untouched; two deficiencies reopened, two new, both self-directed; profile v0.0.3.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[04](2026-08-25-session-04-review-corrections-3.md)
> are left unedited, including the session-04 statements corrected in §05 below.

---

## 00 — The failure mode finally has a name

The reviewer named it: **projection-only verification**. Tests validated a manually corrected
downstream manifest, while the generators, expected-digest inputs and other human views stayed
unreconciled.

That is the single description covering four sessions of findings. Each round I fixed the
*projection* the check happened to look at, and each round the next review found the same defect
one layer back:

| Session | Fixed | Left drifting |
| --- | --- | --- |
| 02 | claims | the rules behind them |
| 03 | rules | the checks meant to enforce them |
| 04 | checks | the generators feeding what the checks read |
| 05 | generators | *(reconciliation now tested; manifest derivation deferred)* |

Recorded as [`FTRO-DEF-035`](../ledgers/deficiency-log.md#ftro-def-035), because a failure mode
that recurs at every layer deserves an entry of its own rather than four separate ones.

---

## 01 — The §9.2 check exempted everything that omitted the field

```python
if es == "resolvable" and rv is not None and rv != "content_validated":
```

`rv is not None`. Every record that simply *omitted* `retrieval_validation` was skipped rather than
failed. All 11 manifest artifacts assert `resolvable`; only 5 declared `content_validated`; **6
omitted the field entirely**. The test passed.

This is the unsupported-null failure — the thing this project exists to catch — committed inside
the check written to enforce the clause that forbids it. Session 02's own note said *"'Unresolved'
is a claim, and it needs evidence too."* An absent value is not evidence of validation.

Fixed by doing the work rather than widening the clause:

- **`src/ftro/pin_evidence_repos.py`** retrieves and content-validates the three git-hosted
  evidence artifacts. One of them, `tintervals`, had asserted `resolvable` with **no checksummed
  file at all** — the record rested on commit metadata alone. It now pins `pyproject.toml` at
  `c1054d63…`, and the pinner refuses to run without an expected digest unless `--allow-unpinned`
  is passed to establish a first pin.
- The Zenodo record is `content_validated` on the strongest evidence in the repo: the archive is
  expanded and fully parsed, 9,018,290 records read.
- The two genuinely concept-level records get an explicit `not_applicable`, itself guarded by a
  test that refuses it for anything carrying a `snapshot_id`.

Profile §9.2 now states that `retrieval_validation` is **required**, that a check must fail closed
on absence, and that `not_applicable` is an enumerated state for non-retrievals — not a hole.
→ [`FTRO-DEF-034`](../ledgers/deficiency-log.md#ftro-def-034), D-042.

---

## 02 — The pinner and the manifest were split-brain

`pin_ppta.py` was added in session 04 to close the §9.2 contradiction. It emitted:

```
ftro:snapshot:ppta/dr3/J0437-4715.par@sha256:…
```

The canonical manifest holds:

```
ftro:snapshot:ppta/dr3/all/J0437-4715.par@sha256:…
```

**All four differed.** It also emitted no `concept_id` and none of the §5.1 composition fields, so
every identity it produced was non-conforming against the rule session 03 had introduced.

So `DEF-029` was closed *only in the hand-curated manifest*. The tool built to support that
manifest emitted four different, non-conforming identities — and nothing compared them, because
every test read the manifest.

Fixed structurally, not by editing four strings:

- the generator **declares** its canonical `concept_id` and snapshot stem in its target table,
  rather than deriving one ad hoc;
- it emits the §5.1 composition fields, so regenerated output stays conforming;
- three reconciliation tests assert generator output equals the manifest for every pinned artifact,
  across the PPTA, evidence-repo and vgosDB reports;
- one test checks that a **freshly generated** identity is §5.1-conforming, not only the stored one.

Profile §9.3 now requires this generally. The stronger fix — deriving the manifest *from* the pin
reports instead of maintaining both — is the right long-term answer and is deferred to Phase 1
rather than claimed here. → [`FTRO-DEF-035`](../ledgers/deficiency-log.md#ftro-def-035), D-043.

---

## 03 — "Nothing skips" was false

A clean export of `1b77a72` still reported:

```
Ran 26 tests
OK (skipped=3)
```

Three provider-dependent tests remained skippable, and **no test invoked any pinner end-to-end**.
Session 04 stated "nothing skips" and "26 tests, all passing on a clean clone". Both false.

Removed the three skippable tests — they duplicated coverage the local-fixture tests already gave —
and replaced them with six **end-to-end** pinner tests that run `pin_vgosdb.py` as a subprocess over
`file://` URLs against committed fixtures:

| Test | Asserts |
| --- | --- |
| valid vgosDB | exit 0, identity minted, bytes cached |
| tarball with no wrappers | exit 1, **no identity**, no bytes cached |
| HTML served as an archive | exit 1, no identity |
| digest mismatch | exit 1, `checksum_match: false`, no identity, no bytes |
| matching digest | exit 0, `checksum_match: true` |
| generated identity | §5.1-conforming as emitted |

**34 tests, zero skips**, verified on a clean `git archive` export.

The cold path was unenforced too, in four separate ways the reviewer enumerated: both
expected-digest manifests lived in gitignored `data/work/`, the documented IGS command passed no
manifest, `pin_ppta.py` treated an absent expectation file as an empty map while still recording
`checksum_match`, and `pin_igs.py` wrote to `data/work/` while the intersection read
`phase0/reports/`. Expected digests are now committed to
[`phase0/evidence/expected-digests.json`](../phase0/evidence/expected-digests.json) — 4 PPTA, 57
IGS, 1 vgosDB, 3 evidence repos — the README command passes it, the pinners refuse to run without
it, and a test asserts it covers every pinned artifact.
→ [`FTRO-DEF-031`](../ledgers/deficiency-log.md#ftro-def-031) **v2.0.0**, D-044, D-045.

---

## 04 — DEF-033 fixed half its own scope

The entry names both the profile *and* `identities.json`. I bumped the profile and marked it
resolved. `identities.json` had **four byte-distinct states** across `fdbf2b9`, `2c31279`,
`0b41929` and `1b77a72` while remaining `"version": "0.1.0"` throughout.

Closing a deficiency against half the artifacts it names is a smaller version of the same
projection error: I checked the part I had just touched. `identities.json` is now v0.2.0 with a
`version_history` array recording its prior drift, and D-039 is extended to bind every versioned
artifact. → [`FTRO-DEF-033`](../ledgers/deficiency-log.md#ftro-def-033) **v2.0.0**.

---

## 05 — Session 04 evidence statements, corrected

| Session 04 said | Actually |
| --- | --- |
| "re-segmenting from all 9,018,290 records at each tolerance" | the implementation parses the archive **once** and caches the **1,023,950 in-window** records, re-segmenting those. The 9,018,290 figure belongs to the quantum census, not the scan. |
| "twelve variants" | **ten**: 4 gap tolerances + 3 credit bases + 3 tag shifts. |
| "no spacing exists between 1.0368 s and 1.9872 s" | true, but supported only by a top-20 histogram the summary itself warns against generalising from. |

The last one is now backed by an exhaustive key. Computing it exposed a wrinkle worth keeping: the
next distinct spacing above 1.0368 s is **1.987199 s**, not 1.9872 — `round(x, 6)` yields both for
the same physical spacing of 23 quanta. The claim holds (`n_strictly_between: 0` over all 9,018,038
adjacent pairs), but stated against a literal I had rounded by hand it would have looked false.
`sample_spacing_exhaustive` now reports the bound **from the data**.

Two further claims that outran the code, both now corrected: the source ledger and decision D-024
still described a "live CDDIS regression test" that has never existed as committed code, and
`DEF-018`'s own response asserted it. The live check was run interactively, once, and never
committed.

---

## 06 — Ledger

| | S01 | S02 | S03 | S04 | S05 |
| --- | --- | --- | --- | --- | --- |
| Entries | 23 | 27 | 29 | 33 | **35** |
| Resolved | 0 | 4 | 5 | 9 | **11** |
| Self-directed | 1 | 4 | 5 | 9 | **11** |
| Reopened | — | — | — | — | **2** |

`source_evidence` 19 · `execution` 9 · `schema` 4 · `rights` 2 · `policy` 1

Two entries reopened at v2.0.0 after their first fixes proved partial. That the ledger can record a
closure as premature is the point of it.

---

## 07 — Method notes to self

- **Fix the generator, not the projection.** Four rounds of correcting whatever the check happened
  to read. The check reads one view; the defect lives in whatever produces it.
- **`is not None` in a conformance test is a hole.** An exemption must be an enumerated state you
  can grep for, never an absence.
- **Close a deficiency against every artifact it names**, not the one you just edited.
- **Bound a claim with the value the data reports**, not a literal you rounded — 1.987199, not
  1.9872.
- **Verify in the directory you think you are in.** Two patches this session landed in `/tmp/ce`
  because a prior `cd` persisted; the repo copies were untouched and only a follow-up grep caught
  it. Same family as session 03's determinism false pass.

---

## 08 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; the
four depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

Newly explicit: **most of the profile's normative clauses still have no executable check.** Six do.
Section §5.0 claims the gate; the gate is not yet general, and saying so is more useful than
another layer of assertion. Deriving `identities.json` from the pin reports — rather than
reconciling two hand-maintained views — is the Phase-1 fix that would retire this whole class.
