# Session 09 — Eighth external review: a regression test that could not fail

**Date:** 2026-08-26 · **Reviews:** commit [`4a5b80a`](https://github.com/uwarring82/ftro-walking-skeleton/commit/4a5b80a5e9bc49eb171efaa3b7299870d1a4bb2c)
**Outcome:** null intact; six new self-directed entries; 70 → 86 tests.
**Licence:** CC BY 4.0

> **Append-only.** Sessions [01](2026-08-25-session-01-phase0.md)–[08](2026-08-26-session-08-review-corrections-7.md)
> are left unedited.

---

## 00 — A conceptual correction I should record first

I have said in three successive notes that deriving `identities.json` from the pin reports is the
fix that retires this class of failure. The reviewer is right that this is wrong, and it matters
enough to state plainly:

> Deriving `identities.json` from pin reports would **not** have prevented the optical sensitivity
> regression. That edge concerns *identity projections*, not *analysis callers*. Deriving human
> views from a bad report would merely propagate the wrong value and remove the visible
> contradiction that exposed it.

I had generalised a real fix for identity drift into a claimed fix for everything, including a
numerical regression it has no purchase on. Worse, derivation would have *destroyed* the signal
that caught this one: the report contradicting the selection note.

What that class needs is an **independently executed numerical oracle**, or two genuinely
independent computations asserted equal. §02 builds one.

---

## 01 — The regression test could not fail on its regression

Session 08's headline fix was three tests guarding the sensitivity computation. They read the
committed JSON.

- Restore the broken `615afe2` revision of `optical_sensitivity.py` → **70 tests green**.
- Make `Resegmenter.runs()` raise → **70 tests green**.

They protected coherence *after manual regeneration*, not the code. A test that cannot fail on the
defect it names is decoration with a docstring.

The "invariant and computed" test was worse: it asserted two summary booleans, so changing a
variant row to `overlap` passed while the summaries sat untouched. I had named it "computed" while
it read a field labelled computed.

→ [`FTRO-DEF-046`](../ledgers/deficiency-log.md#ftro-def-046).

---

## 02 — An oracle that executes

`tests/fixtures/mini-archive/` is a synthetic archive whose run structure is known **by
construction**: comparison AAA has two groups separated by 23 ticks; CCC has four groups separated
by 23, 40 and 60. Ticks 13–22 are empty exactly as in the real archive.

Expected run counts are derived from tick arithmetic, independently of either implementation, and
cross-checked against a manifest recorded when the fixture was built:

| Tolerance | Ticks | Expected runs |
| --- | ---: | ---: |
| 1.1 s | 12 | 6 |
| 1.5 s | 17 | 6 |
| 2.0 s | 23 | 4 |
| 5.0 s | 57 | 3 |

Both segmentation paths — in-process `Resegmenter.runs()` and the subprocess route an operator
would use — are executed against it, and **asserted equal run-for-run**. That redundancy is the
check that would have caught `FTRO-DEF-037` with no committed report in existence.

Verified by injection:

| Injected | Result |
| --- | --- |
| the exact `615afe2` MJD/tick bug | **9 failures** |
| `runs()` raises | **9 errors** |
| *(neither)* | OK |

Both previously left 70 tests green.

One thing worth recording: my first hand-computed expectation for 5.0 s was wrong, and *both*
implementations disagreed with me while agreeing with each other. That is the redundancy working —
it localised the error to my arithmetic, not the code. I derived the expectations from tick
arithmetic after that rather than guessing again.

---

## 03 — Preflight checked presence, not shape

`preflight()` tested `n not in expected`. With `{"vgosdb_min.tgz": null}` the pinner **exited 0,
cached bytes, promoted the official report and minted an identity carrying
`expected_sha256: null`**. And `pin_vgosdb`/`pin_ppta` treated `checksum_match is None` as success,
so "not checked" read as "verified".

Every expectation is now validated as 64 lowercase hex **before any retrieval**; a malformed entry
is fatal even under `--allow-unpinned` (that flag means "not recorded yet", not "recorded as
garbage"); and an unchecked digest counts as verified only when `--allow-unpinned` was explicitly
passed. A malformed URL also escaped `.rejected`, because `Request()` construction sat outside the
`try`. → [`FTRO-DEF-042`](../ledgers/deficiency-log.md#ftro-def-042), D-059.

---

## 04 — `isinstance(False, int)` is True

The consumer gate type-checked counters with `isinstance(value, int)`. JSON `false` passed as zero.
It also accepted a per-pin `content_rejected`, an absent or contradictory per-pin `sha256`, and
`n_pinned: 56` on a report carrying 57 pins — a report describing something other than itself.

→ [`FTRO-DEF-043`](../ledgers/deficiency-log.md#ftro-def-043), D-060.

---

## 05 — A flag that weakened the gate and could not do its job

`--register` only disabled the laundering refusal:

```
check 1  →  update --register 0  →  check 0
```

And because the update loop iterated only **existing** registry entries, `--register` could not
register anything: it exited 0 while the next check still failed. `--update` also accepted a
version downgrade.

Now `--register` adds only newly discovered artifacts, neither flag can bypass the same-version
refusal, and a backwards version is refused. → [`FTRO-DEF-044`](../ledgers/deficiency-log.md#ftro-def-044), D-061.

---

## 06 — An enumeration that was still partial, and an exclusion without a control

Session 08's discovery walked four directories for two file types, so root `codemeta.json` could
change under an unchanged version unnoticed. It is now a whole-repository walk with an explicit skip
list — which immediately found `codemeta.json`.

And generated files were **excluded** from version tracking with nothing put in their place: editing
the optical summary and regenerating produced a byte-different v0.2.0 document while every gate
passed. There is now a freshness check that regenerates and compares, plus a test asserting that
*every* file excluded as "generated" has one. → [`FTRO-DEF-045`](../ledgers/deficiency-log.md#ftro-def-045), D-062.

---

## 07 — A mutation test the unmutated run also passes

`test_production_consumer_rejects_a_stripped_report` asserted only a non-zero exit. On a clean
archive the unmodified consumer already exits 1 because the raw optical data are absent — so
removing the gate entirely would still have passed. It now asserts the specific diagnostic.
→ [`FTRO-DEF-047`](../ledgers/deficiency-log.md#ftro-def-047), D-064.

---

## 08 — Ledger

| | S06 | S07 | S08 | S09 |
| --- | --- | --- | --- | --- |
| Entries | 36 | 36 | 41 | **47** |
| Resolved | 12 | 12 | 17 | **23** |
| Self-directed | 12 | 12 | 17 | **23** |

`execution` **21** · `source_evidence` 19 · `schema` 4 · `rights` 2 · `policy` 1

`execution` is now the largest class. Every entry in it says the same thing: it was expressible, it
was not done, and nothing checked.

---

## 09 — Method notes to self

- **A regression test must execute the code path.** Reading its committed output tests
  transcription, not computation.
- **Redundancy catches what validity cannot.** A wrongly-computed number is well-formed; only a
  second independent path disagrees with it.
- **Validate the shape of a precondition, not its presence.** A key with a null value is not a
  digest.
- **`isinstance(x, int)` is True for booleans.** Exclude `bool` explicitly.
- **A maintenance flag adds capability; it never removes a check.**
- **Excluding a file from one gate obliges covering it with another**, or the exclusion is a hole.
- **Assert the specific diagnostic.** A bare non-zero exit is satisfied by every unrelated failure.
- **Don't generalise a fix beyond what it fixes.** §00 — I claimed a derivation would solve a class
  it cannot touch, for three notes running.

---

## 10 — Carried forward

Unchanged and genuinely open: the downstream VLBI analysis-centre product and IERS EOP series; four
depositor question groups; the IPTA upstream report; `DEF-028`'s question to IVS.

Deriving `identities.json` from the pin reports remains worth doing for **identity** drift, and is
Phase-1 work — but no longer carries the claim I had attached to it. Numerical regressions need
oracles, and there is now one for segmentation only. The four-domain intersection, the alignment
arithmetic and the credit bases have no independent second implementation.

Most of the profile's normative clauses still have no executable check. Twenty-six do now.
