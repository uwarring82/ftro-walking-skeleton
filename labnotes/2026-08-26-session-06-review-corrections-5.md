# Session 06 — Fifth external review: the fix reproduced the defect inside the fix

**Date:** 2026-08-26 · **Reviews:** commit [`11ea11c`](https://github.com/uwarring82/ftro-walking-skeleton/commit/11ea11c5c229d2da50060c2403a81eac0398368f)
**Outcome:** scientific null untouched; three deficiencies reopened, one new; all self-directed.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[05](2026-08-25-session-05-review-corrections-4.md)
> are left unedited, including the statements corrected in §04 below.

---

## 00 — Projection-only verification, inside the machinery built to eliminate it

Session 05 named the failure mode and built the fix. The fix had the failure mode.

- The digest registry was committed, correct, and **not connected**. `pin_igs.py` loaded the
  sectioned file but looked names up at its root, so all 57 IGS artifacts pinned with
  `expected_sha256: null` — while the report still read as enforced. A full local rerun: **57/57
  null**.
- `pin_evidence_repos.py` hard-coded the `tintervals` expectation as `None` even after its digest
  was committed, so the documented command rejected it and exited 1.
- `pin_igs.py` wrote to `data/work/igs-pins.json` while the intersection consumed the committed
  report — the two could diverge silently.
- The test named *"cover every pinned artifact"* checked **4 of 65**.
- The reconciliation test read **stored reports**, skipped concepts absent from the manifest instead
  of failing, and compared a field only when both copies already carried it.

That last one is the sharpest. I wrote a test to catch generator/manifest drift, and it could not
detect drift: removing a `snapshot_id`, adding a rogue concept, or deleting the generated §5.1
fields all left the suite green. I verified it this session by injecting exactly those mutations.

The registry values were right. The enforcement was not connected. **A correct artifact that
nothing consumes is the same defect as an incorrect one** — it just fails silently in the other
direction.

---

## 01 — Reconciliation that can actually fail

Rebuilt so every edge rejects **MISSING**, **UNKNOWN** and **MISMATCHED**:

- `GENERATOR_REPORTS` declares which generator is authoritative for which concept, so a concept no
  generator produces cannot escape reconciliation, and a report entry naming an unknown concept
  cannot be skipped.
- Reconciled fields must be present on **both** sides — absence on either is a failure, not an
  exemption.
- `TestDigestRegistryChain` asserts registry and reports agree on *which artifacts exist* across all
  four sections, that the count is exactly **65**, and that every pin records its expectation as
  **enforced** rather than merely equal.
- No curated `content_validated` record may claim generated provenance without a report entry.

Then I tested the tests, which is what was missing:

| Injected mutation | Result |
| --- | --- |
| remove a `snapshot_id` | **FAILED** (1) |
| add a rogue concept | **FAILED** (1) |
| drop the generated §5.1 fields | **FAILED** (1) |
| delete a whole pin | **FAILED** (7) |
| corrupt a digest | **FAILED** (2) |
| *(unmutated baseline)* | OK |

39 tests, zero skips. `pin_igs.py` now takes `--expect-section` and `--require-expectations`, fails
on an absent or empty section, and writes where its consumers read. `pin_evidence_repos.py` reads
the registry instead of literals — `tintervals` now pins and matches.

→ [`FTRO-DEF-031`](../ledgers/deficiency-log.md#ftro-def-031) **v3.0.0**,
[`FTRO-DEF-035`](../ledgers/deficiency-log.md#ftro-def-035) **v2.0.0**.

---

## 02 — 1.987199 s was never real

The reviewer caught something I had published as evidence: the spacing analysis differenced
**binary floats**, from session 01 onward.

Recomputed in exact integer microday ticks:

| | Float | Exact |
| --- | ---: | ---: |
| distinct spacings | 1,237 | **1,161** |
| next value above 12 ticks | 1.987199 s *and* 1.9872 s | **23 ticks = 1.9872 s** |
| occurrences | 528 + 6,235 | **6,763** |

Float subtraction had split one physical spacing into two apparent ones, and session 05's
"exhaustive evidence key" then reported the artefact as the boundary — with a note explaining the
rounding, which made it *look* considered. It was still an artefact.

Worse, `n_strictly_between` was **tautologically zero**: its upper endpoint was defined as the next
observed value, so nothing could ever lie between. A key that cannot fail is not evidence.

The exact form is a better finding: ticks **13–22 are empty** — 0 of 9,018,038 adjacent pairs — and
the next populated value is 23 ticks. So any tolerance strictly between 12 and 23 ticks segments
identically. That is a falsifiable statement about an empty band, not a restatement of "the next
value is the next value". The 1.1/1.5 equality and the four-domain null are unaffected.

→ [`FTRO-DEF-036`](../ledgers/deficiency-log.md#ftro-def-036), D-047: where a serialised quantity is
exactly representable in integers, compute in integers.

---

## 03 — D-039a lasted one commit

Session 05 adopted D-039a — the version-bump rule binds *every* versioned artifact — and the same
commit changed both ledgers without bumping either.

A rule stated and broken in its own commit is now the third occurrence
([`FTRO-DEF-029`](../ledgers/deficiency-log.md#ftro-def-029), the §5.0 gate, and this). So it is no
longer a rule: `src/ftro/check_versions.py` holds a registry of versioned artifacts and their
declared versions, `--check` exits non-zero on drift, and it prints a note for any versioned file
modified since HEAD. Both ledgers are bumped, and the source ledger now records the `tintervals`
`pyproject.toml` digest it had omitted.

→ [`FTRO-DEF-033`](../ledgers/deficiency-log.md#ftro-def-033) **v3.0.0**.

---

## 04 — Corrections that had only reached session 05

Session 05 corrected several statements in its own lab note and nowhere else. Now propagated to the
formal documents:

| Statement | Was in | Corrected |
| --- | --- | --- |
| "re-segmentation from all 9,018,290 records at each tolerance" | selection note, `optical_sensitivity.py`, DEF-030 | parses once, caches and re-segments the 1,023,950 in-window records |
| "26 tests pass" | DEF-031 | 39, zero skips |
| "the profile is now v0.0.2" | DEF-033 | v0.0.3 |
| "all five composed identities" | profile §5.0 | seven |

A lab note is a record of what was believed; it is not where a correction lands. Recording a fix in
the narrative and leaving the specification wrong is its own small instance of the same failure.

---

## 05 — Ledger

| | S01 | S02 | S03 | S04 | S05 | S06 |
| --- | --- | --- | --- | --- | --- | --- |
| Entries | 23 | 27 | 29 | 33 | 35 | **36** |
| Resolved | 0 | 4 | 5 | 9 | 11 | **13** |
| Self-directed | 1 | 4 | 5 | 9 | 11 | **12** |
| Reopened | — | — | — | — | 2 | **3** |

`source_evidence` 19 · `execution` 10 · `schema` 4 · `rights` 2 · `policy` 1

`execution` has grown from 2 to 10 across six sessions. Every one of those is the same shape: the
thing was expressible and was simply not done, and nothing checked.

---

## 06 — Method notes to self

- **Test the test.** Five injected mutations took ten minutes and proved more than three sessions of
  assertions. If a check has never been seen to fail, it has not been verified.
- **A correct artifact nothing consumes is a broken artifact.** The registry was right and inert for
  a full commit.
- **A key that cannot fail is not evidence.** `n_strictly_between` was structurally zero.
- **Compute in integers where the data is integral.** Floats invented a spacing that then survived
  into a published evidence key, wearing a note about rounding.
- **Land the correction in the specification, not only the narrative.**

---

## 07 — Carried forward

Genuinely open and unchanged: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

Still true, and worth repeating rather than quietly dropping: **most of the profile's normative
clauses have no executable check.** Nine do now. The reviewer's chain — expected registry → freshly
executed pinners → validated pin reports → derived identities → crate and human views — is right,
and only the first three edges are enforced. Deriving `identities.json` from the reports is Phase-1
work; until then two hand-maintained views are reconciled by test rather than by construction.
