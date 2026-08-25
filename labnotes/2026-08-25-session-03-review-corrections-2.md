# Session 03 — Second external review: a rule written and broken in the same commit

**Date:** 2026-08-25 · **Reviews:** commit [`2c31279`](https://github.com/uwarring82/ftro-walking-skeleton/commit/2c3127933b2bfe1a3b950fe89affea6a600b64b0)
**Outcome:** result unchanged and now shown invariant over every convention tested; five corrections; two new deficiencies, one self-directed.
**Licence:** CC BY 4.0

> **Append-only.** [Session 01](2026-08-25-session-01-phase0.md) and
> [Session 02](2026-08-25-session-02-review-corrections.md) are left unedited.

---

## 00 — The finding that matters most

Session 02 added a conformance rule to the profile:

> "An `ftro_composed` identity without this record is not conforming."

**All five composed identities in the same commit violated it** — the four PPTA members and the
vgosDB identity that commit itself introduced. 5 of 5.

That is not a slip. It is the same shape as `DEF-018` in session 01: file a rule, cite it as
evidence of rigour, don't apply it. Session 02's own method note said *"fix your own deficiencies
or stop filing them"* — and then shipped a new unenforced rule in the same breath.

The gap was invisible for one reason: **nothing checked**. So the fix is not the five patches. It
is [`FTRO-DEF-029`](../ledgers/deficiency-log.md#ftro-def-029) and the rule now at the top of
profile §5.0:

> No MUST-clause is landed in this profile until an executable check enforces it against the
> reference manifest.

`tests/test_retrieval_validation.py::TestComposedIdentityConformance` now asserts it. When I first
ran the suite it failed on all five, naming each — which is what a test is for.

---

## 01 — `--expect-sha256` was decoration

The reviewer ran `pin_vgosdb.py` with an all-zero expected digest. It wrote the identity and
exited 0, recording `checksum_match: false` as a *field*.

Reproduced exactly. Worse on inspection: the script wrote the retrieved bytes to the product
filename **before** validating them, so a login page could have been left sitting in
`data/raw/vlbi/20220228-r11040.tgz` — the precise failure `DEF-018` exists to prevent, in the tool
written to fix `DEF-018`.

All three tools now fail closed:

| | Mismatched digest | Correct digest |
| --- | --- | --- |
| `pin_vgosdb.py` | exit 1, no identity minted, no bytes cached | exit 0 |
| `verify_gps2utc.py` | exit 3 | exit 0 |
| `pin_igs.py` | exit 1 if any artifact fails validation | exit 0 |

`checksum_match` is now tri-state: `null` means *not checked* and can never read as a pass. Bytes
are written to `.part` and `os.replace`d only after validation.

And the "regression test" session 02 claimed was never committed — only the validator was. That is
`DEF-027`'s failure mode again: a claim with no committed artifact behind it. There is now a real
suite: 15 tests, standard-library `unittest`, with deterministic fixtures for the login page, a
genuine `.Z`, a wrong-magic `.Z`, a minimal vgosDB and a non-vgosDB tarball.

---

## 02 — Seven filenames, five states

Session 02 reported the vgosDB as carrying "five internal wrapper versions from three analysis
centres". Extracting and hashing the wrappers:

| Wrapper | SHA-256 | Latest RunTimeTag |
| --- | --- | --- |
| `V001_iMPI` | `32c3ef8e…` | 2022/03/10 19:50:56 UTC |
| `V002_iGSFC` | `c9616dd1…` | 2022/03/10 19:59:10 UTC |
| `V003_iGSFC` | `25a19892…` | 2022/03/10 19:59:22 UTC |
| `V004_iGSFC` | `3c52b94f…` | 2022/03/10 22:28:49 UTC |
| `V004_iIVS` | `3c52b94f…` | *identical bytes* |
| `V005_iGSFC` | `310c5815…` | 2025/12/12 21:18:49 UTC |
| `V005_iIVS` | `310c5815…` | *identical bytes* |

**Seven filenames, five distinct byte sequences.** The `iIVS` files are redesignations of identical
content under a different Institution field. Only **MPI and GSFC** produced distinct wrapper bytes —
"three analysis centres" was an artefact of counting filenames.

The lesson generalises, so it is now a decision (D-034): **key on the member digest, never the
filename.** Filename keying invented two states that do not exist and attributed bytes to a centre
that produced none. The pin script now computes all of this rather than my asserting it.

### And the "third identity level" was wrong

`DEF-026` concluded the profile needed a third identity tier. Reading the vgosDB manual §7.1–§7.2
settles it the other way: a wrapper is *"an ASCII file that contains pointers to the files in a
vgosDB"* — an **ordinary archive member**. So the selection needs nothing new:

- which state was consumed → a member `File` entity keyed by **member SHA-256**;
- that a chain used it → a consumption edge;
- wrapper-to-wrapper derivation → `derived_from`, which the format itself already records as
  `InputWrapper` (every wrapper from V002 on points back to `V001_iMPI`).

Profile §5.2 is **retracted**, not amended — the honest record is that the section was wrong.
`DEF-026` is rewritten to v2.0.0 and reclassified from `schema` to `source_evidence`: the schema
was adequate; the *recording* was missing.

### The re-release anchor

Session 02 called the archive a re-release from its HTTP `Last-Modified` (2025-12-15). The internal
evidence is better: V005 carries a sixth Process block, `nuSolve 0.8.3`,
**RunTimeTag 2025/12/12 21:18:49 UTC**, absent from V004, and repoints 24 members to `_V001`
variants whose tar mtimes are also 2025-12-12. The HTTP header is three days later and dates
*mirror publication*, not the reprocessing act.

Nothing in the filename, URL or session listing signals that a 2022 session archive now contains
2025 reprocessing → [`FTRO-DEF-028`](../ledgers/deficiency-log.md#ftro-def-028).

---

## 03 — "Exact" was still doing too much work

Session 02 replaced the envelope figure with a run-level union and called optical support **exact**.
It is exact *over the recorded MJD tags, under a chosen 1.5 s contiguity rule*. It is not exact as
physical measurement support, because `interval`, `lag` and `weighting` are absent from all 12
comparisons — the repository's own ancestry note says a tag's placement in its integration is
unconstrained over up to a full second.

Two undeclared conventions, so the script now computes the sensitivity instead of my asserting
robustness:

| Variant | Optical | optical ∩ VLBI | Four-domain |
| --- | --- | --- | --- |
| gap tolerance 1.1–1.5 s | 133.11 h | 82.02 h | `no_common_support` |
| gap tolerance 2.0 s | 133.12 h | 82.02 h | `no_common_support` |
| gap tolerance 5.0 s | 133.57 h | 82.24 h | `no_common_support` |
| each sample credited 1 s | 133.50 h | 82.18 h | `no_common_support` |
| uniform tag shift ±1 s | 133.11 h | — | `no_common_support` (gap 31.1741–31.1747 h) |

**Invariant over every convention tested.** That is a stronger statement than "exact" ever was, and
unlike "exact" it is true.

`optical_support_basis` is now `recorded_timestamp_span_union` and `bound.optical` is `derived`.

### The count that was two counts

7,398 runs merge into **1,384** intervals, of which **31** have zero recorded span — single-sample
runs, where first tag equals last tag — leaving **1,353** with positive duration after the window
clip. Session 02 printed 1,353 as though it were the merge output.

This also surfaced a systematic undercount: crediting `(last − first)` gives each run *n−1* sample
intervals for *n* samples of gate time, and single-sample runs get zero. Crediting each sample its
nominal 1 s raises optical to 133.50 h (+0.29%). Disclosed rather than silently switched, since
the 1 s figure is itself the inferred grid.

---

## 04 — ±43.2 ms is not a floor

I had written that ±43.2 ms is "the binding limit on placing these records on any shared time axis".
It is a **per-tag rounding bound under the inferred nearest-rounding model**, and it is neither:

- **not necessarily dominant** — the missing `interval`/`lag`/`weighting` allow up to **1 s** of
  placement freedom, over twenty times larger;
- **not irreducible** — if the grid model holds, reconstructing epochs by sample index recovers
  much of the quantisation loss.

Calling the smaller, reducible term the "binding limit" while a larger irreducible one sits in the
same document is exactly the drift session 02 said it had caught.

---

## 05 — The access rule was aimed at the wrong field

Session 02 adopted: *"`access_class` may only be recorded after enumerating the provider's listed
distribution channels."* That contradicts the profile's own definition — `access_class` is a
property of a **retrieval path**, so one content-validated anonymous retrieval settles it for that
path regardless of any other channel.

Restated so positives and negatives are scoped differently:

> **Positives are per-path; negatives are per-dataset.** One successful content-validated
> retrieval establishes `access_class = public` for that path. No single failed path may establish
> a dataset-level negative: `evidence_state = unresolved` requires that every provider-listed
> channel has been attempted, recorded as `routes_tried[]`.

Our own enumeration was also incomplete — the IVS page lists **three** centres and we recorded two:

| Channel | Outcome |
| --- | --- |
| CDDIS | `auth_required` — Earthdata login as HTTP 200 |
| **BKG** | `unreachable` — no TCP on 443 from two independent networks; class **not established** |
| OPAR | `retrieved` — anonymous, content-validated |

`unreachable` establishes nothing about access class. Recording BKG does not change the OPAR pin —
which is what the corrected scoping predicts, and a small check that the rule is right.

---

## 06 — Smaller fixes

| Fix | Was | Now |
| --- | --- | --- |
| Self-directed count | "three" | **five**, with machine-readable `responsible_party` and `self_directed` on every entry |
| VLBI `concept_note` | "the vgosDB … are NOT yet pinned", one field above the pin | current |
| RO-Crate `contentSize` | one stale value flagged; **15** were stale | refreshed from disk by script, not by hand |
| Session-02 filename | `2026-08-26-…` against a 2026-08-25 date | renamed; 4 referring files updated |
| `tests/` | absent | in the RO-Crate as a directory Dataset |

The 15-vs-1 stale sizes are the point in miniature: hand-maintained metadata drifts silently, so
the refresh is now a script.

---

## 07 — Ledger

| | S01 | S02 | S03 |
| --- | --- | --- | --- |
| Entries | 23 | 27 | **29** |
| Resolved | 0 | 4 | **5** |
| Self-directed | 1 | 4 | **5** |

`source_evidence` 19 · `schema` 4 · `execution` 3 · `rights` 2 · `policy` 1

---

## 08 — Method notes to self

- **A rule without a check is a wish.** Two sessions running, I filed a rule and did not enforce
  it. The difference this time is `tests/`, which failed on all five and named them.
- **Count states, not names.** Seven wrapper filenames, five wrapper states. Anything keyed on a
  human-assigned label will over-count.
- **Prefer internal anchors to transport metadata.** `RunTimeTag` beats HTTP `Last-Modified`: one
  records the act, the other records a mirror's copy of it.
- **"Exact" needs a scope.** Exact over *what*, under *which* convention. Twice now the word has
  been the thing that outran the evidence.
- **Compute the sensitivity instead of asserting robustness.** "Invariant over every convention
  tested" is checkable; "robust" is not.
- **When a review flags one instance, count them all.** One stale `contentSize` was reported; 15
  existed. The reviewer sampled; the fix has to enumerate.

---

## 09 — Carried forward

Unchanged: the downstream VLBI analysis-centre product and IERS EOP series remain **unresolved**;
the four depositor question groups and the IPTA upstream report are still unsent. New: the PPTA leg
is still pinned at `status_and_checksum` only, and `DEF-028` adds a question to IVS about version
tokens for reprocessed session archives.
