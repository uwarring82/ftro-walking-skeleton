# Session 04 — Third external review: checks that said more than they executed

**Date:** 2026-08-25 · **Reviews:** commit [`0b41929`](https://github.com/uwarring82/ftro-walking-skeleton/commit/0b41929cc77d0c727754e61e6fa4246c9ad9fd27)
**Outcome:** four-domain null unchanged and now computed per variant; four new self-directed deficiencies; profile bumped to v0.0.2.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md),
> [02](2026-08-25-session-02-review-corrections.md) and
> [03](2026-08-25-session-03-review-corrections-2.md) are left unedited.

---

## 00 — A correction owed from session 03

Session 03's method notes claimed the determinism check passed. It did not, on first run: the
shell loop mis-quoted its file list, `shasum` received one long filename, and `diff` compared two
**identical error messages** and reported success. I caught it, re-ran correctly, and the outputs
were genuinely byte-identical — but I reported only the corrected result and left the false pass
out of the note.

Under this repository's own append-only/dead-end rule that was the wrong call: *"Dead ends are
recorded. A retrieval that failed, a hypothesis that collapsed and a wrong turn are all findings."*
A verification that passed for the wrong reason is exactly such a finding, and it belonged in
session 03 rather than in a summary that no reader of the repository will see.

Recorded here, late, where the repository can see it.

---

## 01 — The sensitivity scan could not do what it reported

Session 03's headline improvement was replacing an asserted robustness claim with a computed one.
The computation was wrong.

`analyse_optical.py --gap-tolerance-s` bounds inter-sample spacing **inside one file's** run. My
scan started from an inventory *already segmented at 1.5 s* and re-merged it. Two defects, and the
code's own comment concedes the first:

> `# Re-merging with a wider tolerance can only join runs, never split them`

- **It cannot split.** So the 1.1 s row was structurally forced to equal 1.5 s. The scan's
  most-quoted result was an artefact of its input.
- **It joins across series.** It flattened runs from every comparison and every `.dat` file into
  one sorted list, so a run of `INRIM_ITYb1-SYRTE_Sr2` and a run of `NPL-Yb+(E3)-NPL-Sr1` a second
  apart were welded together — crediting support to an instant no single measurement covered.

**All eight reported cells were wrong, always high.** Correct values, from re-segmenting all
9,018,290 records at each tolerance:

| Tolerance | Runs | Optical | optical ∩ VLBI |
| --- | ---: | ---: | ---: |
| 1.1 s | 7,398 | 133.111920 h | 82.013424 h |
| 1.5 s | 7,398 | 133.111920 h | 82.013424 h |
| 2.0 s | 7,139 | 133.116888 h | 82.016184 h |
| 5.0 s | 4,826 | 133.567344 h | 82.232760 h |

And two lines below the scan:

```python
sensitivity["four_domain_status_invariant_over_all_tested_variants"] = True
```

A literal. In the same commit whose lab note said *"compute the sensitivity instead of asserting
robustness."* The fix was one line away from the error.

### What the broken scan concealed

Redone properly, two real findings appear that the artefact had hidden:

**1.1 s genuinely equals 1.5 s** — and now for a reason. No inter-sample spacing exists *anywhere*
in that interval: the spacings jump from 1.0368 s straight to 1.9872 s. That is a property of the
data, established by actually splitting at 1.1 s.

**The per-sample credit is 2.43 h *below* the span basis**, not above it:

| Basis | Optical | ∩ VLBI |
| --- | ---: | ---: |
| recorded tag spans (shipped) | 133.111920 h | 82.013424 h |
| run span + trailing 1 s gate | 133.496073 h | 82.182577 h |
| per-run *n* × 1 s block | 133.496567 h | 82.182929 h |
| **per-sample 1 s credit** | **130.684083 h** | **80.450043 h** |

My note had asserted the correction "can only ADD support". Crediting each tag its own second
exposes the ~36.8 ms holes the span basis silently fills at ~276,000 sample boundaries. It
subtracts. And it is the only basis independent of the contiguity rule, because it never segments.

The null holds under all of it — now **computed** per variant, across twelve variants.
→ [`FTRO-DEF-030`](../ledgers/deficiency-log.md#ftro-def-030)

---

## 02 — The test suite skipped the thing it existed to test

A clean `git archive` export ran the suite session 03 had just added:

```
OK (skipped=3)
```

All three fail-closed tests depended on gitignored `gps2utc.clk` and skipped without it. The
behaviour the suite was written to protect was never exercised on a clean clone. Neither pinner
was tested end-to-end at all.

Worse, `tests/fixtures/genuine.sp3.Z` was literal fake payload behind a `1f 9d` prefix. Real
`uncompress` rejects it; my validator accepted it, because it only checked two bytes. So
`content_validated` meant no more than **"non-empty, non-HTML, right first two bytes"** — while
the profile granted it the authority to support `evidence_state = resolvable`.

Fixed properly rather than papered over:

- **`src/ftro/unixz.py`** — a pure-stdlib Unix-compress (LZW) codec. Python has no `.Z` support and
  the repo takes no dependencies, so it had to be written: 3-byte header, variable 9–16 bit codes,
  block-mode `CLEAR` with its code-boundary padding quirk, and the KwKwK case. Verified
  **byte-identical to system `gzip -dc`** on a real 253 KB `igs21980.sp3.Z`.
- `validate_content` now decompresses and checks the inner format.
- Fixtures are real: a genuinely LZW-compressed synthetic SP3 (FTRO-authored, since IGS rights are
  `link_only` and provider bytes must not be redistributed), plus right-magic-won't-decompress and
  valid-LZW-wrong-content negatives.
- Fail-closed tests build a local fixture in a `tempfile.mkdtemp`, so nothing skips and nothing
  reads a stale file from a fixed `/tmp` path.

26 tests, all passing on a clean clone.
→ [`FTRO-DEF-031`](../ledgers/deficiency-log.md#ftro-def-031)

### Signatures written from memory fail twice

Writing the inner-format checks, I guessed the IGS ERP signature from recollection: `VERSION` and
`XPOLE`. It rejected all 11 genuine Final ERP files. I guessed again from the Final file I then
read — `EOP  SOLUTION` — and it rejected all 11 Rapid ERP files, which have a different header
entirely. Only the third attempt, keyed on what the two families actually share (`version`, `MJD`,
`UT1-UTC`), accepts all 57.

Two wrong guesses, each disproved by the bytes within seconds of looking. → D-040.

---

## 03 — The check inherited the error it was written to catch

Session 03 closed `DEF-029` — the rule-violated-in-its-own-commit finding — against **five**
composed identities, and wrote a test asserting the rule.

The denominator was **seven**. §5.1's text is unqualified, but I had counted only
`snapshot_kind == ftro_composed` and then wrote the test with the same filter. So the test passed
while `ftro:concept:ppta/dr3` and `ftro:concept:igs/igs/orbit` — both `concept_kind:
ftro_composed` — carried neither field.

The check was **self-confirming**: it encoded the observation's scoping error, so it could only
ever agree with it. That is worse than no check, because it converts an open question into a green
tick.

`DEF-029` is reopened at v2.0.0 with the corrected denominator, and reclassified `schema` →
`execution`. The reviewer's argument is right and matches the ledger's own precedent: `DEF-026`
v2.0.0 already reasons *"the schema is adequate; what was missing was the recording"*. The fields
were always expressible — the fix added two ordinary JSON keys. Nothing could not be *said*; it
simply was not *done*. → D-036.

---

## 04 — A recorded contradiction is not a resolved one

Profile §9.2 says only `content_validated` may support `evidence_state = resolvable`. The four
PPTA artifacts carried `status_and_checksum` **and** `resolvable` from `2c31279` through
`0b41929` — two commits — with a note on each record explaining the gap.

Annotating a contradiction is not fixing it. Resolved by **validating rather than downgrading**:
`src/ftro/pin_ppta.py` checks each artifact against the inner format it claims — a `PSRJ` line for
`.par`, a TEMPO2 `FORMAT` header for `.tim`, a comment header plus MJD rows for `.clk`. All four
pass, and a test now asserts the coupling for every artifact in the manifest.
→ [`FTRO-DEF-032`](../ledgers/deficiency-log.md#ftro-def-032), D-041.

---

## 05 — A version label that named nothing

`profile v0.0.1` was byte-distinct at all three commits while gaining §5.0, §5.1, §5.2 and the
§9.2 `routes_tried` requirement. Card §9.1 requires conformance to be declared *by version* — so
"conforms to v0.0.1" identified no particular set of constraints, and any conformance assertion
against it was unfalsifiable.

Profile is now **v0.0.2**, carrying a version-history table that records what each commit changed,
including the two unversioned changes. Rule: any normative change bumps the version in the same
commit. → [`FTRO-DEF-033`](../ledgers/deficiency-log.md#ftro-def-033), D-039.

---

## 06 — Claims the code did not support

| Claim | Reality |
| --- | --- |
| D-033: "all three tools fail on digest mismatch" | `pin_igs.py` had **no expected-digest input at all**. It now takes `--expect-sha256-manifest` and fails closed. |
| Session 03: RO-Crate refresh "is now a script" | No script was committed. `src/ftro/refresh_crate.py` now exists, with a `--check` mode. |
| README: regression test runs "against the live CDDIS URL" | The committed test uses a 454-byte synthetic fixture and makes no network call. |

Three claims, three commits apart, none backed by committed code. Each is small; the pattern is
not.

---

## 07 — Ledger

| | S01 | S02 | S03 | S04 |
| --- | --- | --- | --- | --- |
| Entries | 23 | 27 | 29 | **33** |
| Resolved | 0 | 4 | 5 | **9** |
| Self-directed | 1 | 4 | 5 | **9** |

`source_evidence` 19 · `execution` 7 · `schema` 4 · `rights` 2 · `policy` 1

The `execution` class has more than doubled this session. That is the right home for this failure
mode: not "we could not express it" but "we did not do it, and nothing checked."

---

## 08 — Method notes to self

- **A check that inherits the finding's assumptions cannot falsify it.** §03 is the cleanest case:
  the test agreed with me because I wrote it from the same wrong premise.
- **Vary the parameter where it acts.** The scan post-processed the stage it meant to re-run, and
  no amount of care downstream could recover what the segmentation had already decided.
- **A skipped test is a failing test that reports success.** Coverage that evaporates on a clean
  clone is not coverage.
- **A fixture must be a real instance of its format.** Fake payload behind correct magic tested the
  magic check and nothing else — and quietly defined what `content_validated` meant.
- **Read the bytes before writing the signature.** Two ERP guesses, two wrong, both disproved
  immediately by looking.
- **Report the failure you had, not the result you ended with.** §00 — the determinism false pass
  belonged in session 03.

Four sessions, and the failure mode has migrated but not changed: session 02 corrected claims,
session 03 corrected rules, session 04 corrected the *checks that were supposed to enforce the
rules*. Each layer was asserted before it was executed.

---

## 09 — Carried forward

The downstream VLBI analysis-centre product and IERS EOP series remain **unresolved** — the only
substantive Phase-1 blocker. The four depositor question groups and the IPTA upstream report are
still unsent; `DEF-028` adds a question to IVS about version tokens for reprocessed archives.

Profile §5.0 is now *closer* to true — six clauses are enforced by tests — but most of the
profile's normative clauses still have no executable check. That gap is itself unclosed.
