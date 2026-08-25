# Session 01 — Phase 0: evidence lock, bootstrap ledger and selection

**Date:** 2026-08-25 · **Task card:** FTRO-WS-001 v0.3 §21 Phase 0, §22
**Outcome:** Gate 0 passed, with the VLBI product leg carried as an open item.
**Licence:** CC BY 4.0

---

## 00 — Setup

Repository initialised at `/Users/uwarring/Documents/GitHub/observatory`, published as
`uwarring82/ftro-walking-skeleton`. Public, per the card's §7A commitment to a public
walking skeleton preceding any consortium engagement.

Dual licensing established up front: Apache-2.0 for `src/**`, CC BY 4.0 for everything
else authored here. `data/raw/` gitignored — the federation records identifiers and
checksums, not provider bytes.

---

## 01 — Optical leg: retrieval and checksum

Fetched the Zenodo REST record first, before any bytes.

```
GET https://zenodo.org/api/records/17107693
  → title matches card §5.1
  → license.id = "cc-by-4.0"
  → 1 file: "ROCIT campaign results.zip", 83,530,540 B, md5:4ae290f559c90b462991286c933a1147
```

Every fact the card asserts about the record checks out. Downloaded and verified:

| | Value |
| --- | --- |
| MD5 | `4ae290f559c90b462991286c933a1147` — **matches card §5.1** |
| SHA-256 | `6168e24a0c29ce0929e9651460f11ea77f151176e1ba3d0fe3428e1e08bd56bd` — newly recorded |
| Size | 83,530,540 B |

**Note on `metadata.version`: it is `null`.** Zenodo's concept DOI resolves to the
latest version, so concept and snapshot identity are not separable from provider
metadata alone. An FTRO composed snapshot identity is required — the first live instance
of the card's §10 rule, encountered within the first ten minutes.

---

## 02 — Optical leg: first look, and the first surprise

Extracted: **12 comparison directories, 252 `.dat`, 12 `.yml`. Nothing else.**

No README, no licence file, and — contrary to card §5.1's description of the record
contents — **no processing code**. → [`FTRO-DEF-007`](../ledgers/deficiency-log.md#ftro-def-007).

The first YAML I opened was the surprise:

```yaml
- name: INRIM_ITYb1-SYRTE_Sr2
  numrhoBA: '518295836590863.6000000000002'
  denrhoBA: '429228004229873'
  sB: 518295836590863.6
  nu0A: '429228004229873'
  grsA: 6.086e-15
  uA_sys: 1.7e-17
  nu0B: '518295836590863.6'
  grsB: 0.0
  uB_sys: 2.2e-17
```

**None of `ref_osc`, `interval`, `lag`, `weighting` is present** — and those four are
precisely what card §5.1 instructs us to extract. Checked all 12: absent everywhere.
The complete key set used anywhere in the archive is
`denrhoBA grsA grsB name nu0A nu0B numrhoBA sB uA_sys uB_sys`.

That reframed the session. The card's headline optical question was going to return
`unresolved`, and the work became *establishing that rigorously* rather than answering it.

Also spotted here and pursued later: `numrhoBA` ends `...863.6000000000002` while `nu0B`
ends `...863.6`. A float64 round-trip tail in a field the spec types as arbitrary
precision. → [`FTRO-DEF-010`](../ledgers/deficiency-log.md#ftro-def-010).

---

## 03 — Optical leg: systematic analysis

Wrote [`src/ftro/analyse_optical.py`](../src/ftro/analyse_optical.py) rather than working
interactively, so the numbers below are regenerable. Three results, in increasing order
of how much they surprised me.

### 03a — The validity flag is degenerate

```
GLOBAL flag histogram: {'1': 9018290}
UNDOCUMENTED flag values: []
```

All **9,018,290** samples carry flag = `1`. Values `0` and `2` never appear.

I had expected the card's §20 risk row ("archive flags conflict with the pinned `0/1/2`
semantics") to mean out-of-vocabulary values. It is the opposite failure: the vocabulary
is respected but **never exercised**. A mask that never varies is not a mask.

Two consequences worth stating plainly: validity intervals have to come from sample
*presence*, not from the flag; and every published sample is formally only "valid but
experimental" — the archive never asserts a sample is fully `valid`.

→ [`FTRO-DEF-001`](../ledgers/deficiency-log.md#ftro-def-001), and it drove the new
profile field `validity_mask_informativeness`.

### 03b — The time tags are quantised at 86.4 ms

The spacing histogram was not what a 1 s series should look like:

```
1.0368 s  →  5,139,806
0.9504 s  →  3,813,549
```

Neither is 1 s. Both are multiples of 0.0864 s (12× and 11×), which is 10⁻⁶ day.

Checked directly: every MJD value carries exactly 6 decimal places and is an exact
multiple of 10⁻⁶ d — **1,564,882 of 1,564,882** sampled values, no exceptions.

Then the confirming arithmetic:

| | |
| --- | --- |
| observed ratio 5,139,806 / 3,813,549 | **1.347775** |
| ratio for a mean of exactly 1.000000 s | 0.0496/0.0368 = **1.347826** |
| implied mean spacing | **0.999999199 s** |

So the underlying grid *is* exactly 1 s, and what we see is deterministic rounding to an
86.4 ms quantum. **Maximum time-tag error ±43.2 ms — 4.3% of the sampling interval.**

This is the finding I care most about. The files report fractional frequency at the
10⁻¹⁷ level and time-tag it with a coordinate good to 43 ms: roughly **eight orders of
magnitude** apart. Any cross-domain alignment involving these records is floored at
~43 ms by serialisation alone, before physical realisation is even discussed.

→ [`FTRO-DEF-002`](../ledgers/deficiency-log.md#ftro-def-002), and the new profile field
`time_coordinate_quantum` ([`FTRO-DEF-021`](../ledgers/deficiency-log.md#ftro-def-021)).

### 03c — Heterogeneous YAML and a time-varying "systematic"

Key sets differ across comparisons, and several comparisons carry >20,000 distinct
values in the `uA_sys` column (max 38,662).

I nearly logged the time-varying uncertainty as a defect. **Reading the spec first
prevented that** — it defines column 4 as "time-varying systematic uncertainty (optional,
for accurate clocks only)". Documented behaviour, not a deficiency. Recorded here
because the near-miss is the point: *check the pinned specification before classifying*.

What *is* a finding: the YAML scalar and the column disagree where both exist
(e.g. YAML `uB_sys: 2.2e-17` against column values {2.1, 2.2, 2.3}e-17), and the spec
does not say which prevails →
[`FTRO-DEF-006`](../ledgers/deficiency-log.md#ftro-def-006).

---

## 04 — Reading the pinned format specification

Fetched `INRIM/optical-link-data-format@689bda77`, `README.md`.
SHA-256 `cf93ae7a…fcee98` — **matches the card exactly.**

Commit date **2025-01-20T15:39:52Z**. The archive's data files were generated
2025-01-20T17:01:50+01:00 onward, i.e. **16:01:50Z — 22 minutes later.** Specification and
data were finalised in the same working session. A pleasing provenance detail, and one
that only two pinned timestamps make visible.

Three things in the spec changed my reading of the archive:

**1. The four missing fields are all optional.** So the omission is *conformant*. The
deficiency is `source_evidence`, not `schema` — the format permits the gap; the gap
destroys the ancestry. Classification matters here and I want the reasoning on record.

**2. The comparator output is formally ambiguous.** The spec's examples table has two
rows with *identical* ρ⁰ = ν̂⁰_B/ν̂⁰_A and s_B = ν̂⁰_B, differing only in the reference
oscillator: `Ref = A` gives ρ̃_{B,A}; `Ref = local RF` gives ρ̃_{B,x} − ρ̃_{A,x}.

Verified that **all 12 comparisons** use exactly that ρ⁰ and s_B. And `ref_osc` — the one
field that discriminates them — is absent in all 12. So the archive cannot, from its own
contents, say which of two documented physical interpretations applies, and the two have
different time-tag ancestry. → [`FTRO-DEF-004`](../ledgers/deficiency-log.md#ftro-def-004).

**3. The scope disclaimer.** Second sentence of the spec:

> "Clock comparison is understood to mean measuring the ratio of the frequencies of two
> clocks. **Time transfer and time comparison are beyond the scope of this format.**"

This makes the whole optical result *structural* rather than a depositor error. The
format was built to carry frequency ratios; its MJD column indexes samples, it does not
assert a time-referenced epoch. The card is asking the archive a question its format
explicitly declines to answer. That is a finding about the **federation boundary**, and it
is the honest framing.

Also learned: directory naming is `INSTITUTEB_OSCB-INSTITUTEA_OSCA`, so the **first**
token is B. Verified against frequencies (429.228 THz = Sr = SYRTE = A;
518.296 THz = Yb = INRIM = B). Recorded in the profile as an edge-direction caution —
easy to get backwards.

Wrote up: [`phase0/optical-timetag-ancestry-note.md`](../phase0/optical-timetag-ancestry-note.md).

---

## 05 — Provenance split inside one DOI

Two distinct generating scripts across the archive:

| Script | Comparisons | Generated |
| --- | --- | --- |
| `06-procclocks-v3.py` | 11 | 2025-01-20 |
| `convert-to-rocit.py` | 1 (`NPL-Yb+(E3)-NPL-Sr1`) | 2024-04-22 |

One DOI, two provenance branches, ten months apart. The NPL comparison also turns out to
be the only one with no support in the candidate window. →
[`FTRO-DEF-008`](../ledgers/deficiency-log.md#ftro-def-008).

Also: actual coverage starts **MJD 59631.78854**, not the declared 59630 — the declared
range overstates by 1.79 days. Filed as low severity
([`FTRO-DEF-009`](../ledgers/deficiency-log.md#ftro-def-009)); it later turned out to
decide the session's main result.

---

## 06 — Evidence pins: two hits and one caution

| Artifact | Card's claim | Verified |
| --- | --- | --- |
| `optical-link-data-format@689bda77` README SHA-256 | `cf93ae7a…fcee98` | ✅ exact |
| `gps2utc.clk` @ `36dc139a` SHA-256 | `7a1dcb60…669a0a` | ✅ exact |
| `tintervals@2064db12` | "processing evidence" | ⚠️ see below |

**`tintervals@2064db12` is dated 2026-08-16** — 19 months *after* the archive's data was
generated. It cannot be the software that produced it. The pin is valid as a snapshot of
a related tool, but its edge is `contextualized_by`, not `generated_by`. →
[`FTRO-DEF-022`](../ledgers/deficiency-log.md#ftro-def-022).

The IPTA repo commit is dated **2026-08-24**, one day before this session, with message
"Routine repo update from Github action". A textbook living series — exactly why the card
insists on snapshot identity.

---

## 07 — `gps2utc.clk`, and writing a real verification procedure

The card (§14.1) wants an ApplicabilityAssessment on whether Parkes tracked `C0` or `C0′`.
Rather than eyeball it, wrote
[`src/ftro/verify_gps2utc.py`](../src/ftro/verify_gps2utc.py) — procedure
`VP-GPS2UTC-001` v1.0.0 — so that §11.4's "named, versioned verification procedure"
requirement is met by something that actually exists.

**Result 1 (determined).** The file is partitioned by regime markers. `C0′` begins at
MJD 55559.0 (2010-12-29). The candidate window sits wholly inside it. Verdict `supports`.

**Result 2 (not determined).** The file's own header says:

> "This may or may not resemble what your GPS receiver system uses."

The artifact **disclaims** applicability to any given receiver. No Parkes
receiver-configuration evidence was found. So the assessment is `indeterminate` — and the
two claims must not be conflated: what the *file supplies* is settled; what the *receiver
tracked* is not.

**Result 3 (unexpected).** The procedure also found **64 duplicate MJD abscissae**, 45
carrying two different ordinates, max difference 1.0 ns. One is the `C0`→`C0′` boundary
itself at MJD 55559.0, where the two entries differ by 0.3 ns. Interpolation at a
duplicated abscissa is implementation-dependent.

None falls inside the candidate window, so this pilot is unaffected — but it is a latent
defect in a widely used timing artifact, and worth reporting upstream. →
[`FTRO-DEF-016`](../ledgers/deficiency-log.md#ftro-def-016).

Writing the check as a script rather than a look paid for itself immediately: I was not
looking for duplicates.

---

## 08 — GNSS: 57 artifacts, and a real bitemporal fixture

Candidate window spans GPS weeks 2198 day 0 → 2199 day 3.

CDDIS redirected; AIUB and IGN timed out; **BKG served anonymously.** Pinned 57 artifacts
with SHA-256, MD5, size and `Last-Modified` via
[`src/ftro/pin_igs.py`](../src/ftro/pin_igs.py).

The `Last-Modified` headers turned out to be the valuable part. For epoch MJD 59630:

| Product | Available |
| --- | --- |
| Rapid `igr21980` | 2022-02-21T17:30:12Z (~1 day) |
| **Final `igs21980`** | **2022-03-13T11:46:51Z (~21 days)** |

That is card §13.3's mandatory fixture, with real artifacts: `as_of = 2022-02-25` must
resolve to Rapid, `as_of = 2022-03-20` to Final — same policy, same epoch, different
knowledge date, historical answers never overwritten.

Caveat recorded honestly: these are a *mirror's* file times, not IGS-declared release
times ([`FTRO-DEF-019`](../ledgers/deficiency-log.md#ftro-def-019)). Also no `.clk_30s`
on this mirror ([`FTRO-DEF-020`](../ledgers/deficiency-log.md#ftro-def-020)).

Frame for the interval is **IGb14**; IGS20 starts week 2238 (2022-11-27), after the
window — consistent with card §5.3.

---

## 09 — VLBI: a 200 OK that was not data

Tried CDDIS for the IVS master file:

```
GET https://cddis.nasa.gov/archive/vlbi/ivsdata/master/2022/master2022.txt
  → HTTP 200, 10,980 bytes
  → <title>Earthdata Login</title>
```

**HTTP 200 with an HTML login page.** It checksums cleanly. A retrieval procedure
validating only status code and checksum would have pinned a login page as evidence and
propagated that checksum downstream.

This is the finding with the widest blast radius, because **it implicates our own
tooling**: `pin_igs.py` has exactly this weakness. Logged against ourselves →
[`FTRO-DEF-018`](../ledgers/deficiency-log.md#ftro-def-018), and turned into a profile
requirement (`retrieval_validation`; only `content_validated` may support
`evidence_state = resolvable`).

Fell back to the IVS session listing, which is public. Seven sessions intersect the
window. Computed overlap against the *actual* optical runs with
[`src/ftro/compute_overlap.py`](../src/ftro/compute_overlap.py):

| Session | Type | Optical comparisons | Cumulative overlap |
| --- | --- | --- | --- |
| **R11040** | **IVS-R1** | **7** | **91.95 h** |
| AUA085 | AUSTRAL | 3 | 26.38 h |
| AOV068 | AOV | 2 | 24.46 h |

**R11040 selected** — decisive on overlap, and an IVS-R1, the series that feeds
operational EOP. Its vgosDB and downstream EOP products remain **unpinned** because of
the auth wall; `evidence_state = unresolved` for the VLBI data products.

---

## 10 — Pulsar: the chain that nearly completes

CSIRO DAP search found DR3 published as **two DOIs**. Comparing the file listings:
**90,884 shared paths**, 18,414 and 15,509 unique. The two "parts" duplicate ~42% of each
other, including the entire `toas_and_parameters` tree, and neither says so. There is no
single provider PID for "PPTA DR3". →
[`FTRO-DEF-015`](../ledgers/deficiency-log.md#ftro-def-015).

Licence: **CC BY-SA 4.0** — copyleft, against the CC BY 4.0 the card assigns FTRO outputs.
So `redistribution_mode = link_only` and FTRO records facts, not provider prose. →
[`FTRO-DEF-014`](../ledgers/deficiency-log.md#ftro-def-014).

The listing contained exactly what the card wanted pinned:

```
ppta_dr3/toas_and_parameters/clock/pks2gps.clk          1,742,710 B
ppta_dr3/toas_and_parameters/clock/tai2tt_bipm2021.clk     48,871 B
ppta_dr3/toas_and_parameters/all/J0437-4715.par             4,402 B
ppta_dr3/toas_and_parameters/all/J0437-4715.tim         4,464,619 B
```

Retrieved all four (~6.3 MB out of 2.77 TB). All sizes match the manifest.

### The `.par` is internally inconsistent with its own release

```
CLK            TT(BIPM2020)
EPHEM          DE436
UNITS          TCB
```

But the only TAI→TT artifact shipped is **`tai2tt_bipm2021.clk`**. The timing model asks
for a realisation the release does not contain. Two artifacts, one release, incompatible
assertions. Retained both; substituted neither. →
[`FTRO-DEF-011`](../ledgers/deficiency-log.md#ftro-def-011),
[AA-PPTA-CLKREALISATION-001](../phase0/applicability/AA-PPTA-CLKREALISATION-001.md).

And the shipped TT values at our epoch are **extrapolated**, per the file's own header:
`32.184 + 27667.5ns − 0.01(MJD − 59579.0)ns`. Verified against the table — reproduces
exactly. Our epoch is 51.5 days past the extrapolation reference. Not a measured BIPM
value. → [`FTRO-DEF-017`](../ledgers/deficiency-log.md#ftro-def-017).

### The pre-registered EOP prediction, confirmed

Card §15.1 pre-registered that the PPTA→C04 chain "may terminate at a bundled or
regenerated artifact whose ancestry to a particular IERS C04 snapshot is opaque."

```
grep -icE 'eop|ut1|iers|c04|polar' J0437-4715.par
  → 0
```

**Zero.** Not opaque — *unidentified*. The dependency is satisfied implicitly by an
unshipped, unversioned TEMPO2 runtime. The prediction is confirmed in a stronger form
than written. → [`FTRO-DEF-012`](../ledgers/deficiency-log.md#ftro-def-012).

That kills the card's leading shared-ancestry candidate (IVS → IERS EOP → pulsar
barycentring) from the pulsar end.

### A third inconsistency

`NTOA 20836` and `CHI2R 23.8024 20780` in the `.par`, against **11,637** TOA lines in the
co-located `.tim`, with no `INCLUDE`/`JUMP` to reconcile them. A cold reproducer cannot
reproduce the quoted χ². Recorded as an observation requiring assessment, not a proven
error → [`FTRO-DEF-013`](../ledgers/deficiency-log.md#ftro-def-013),
[AA-PPTA-TIMINGMODEL-001](../phase0/applicability/AA-PPTA-TIMINGMODEL-001.md).

### What *does* work

The observatory→GPS→UTC leg is fully evidenced:

```
pks2gps  interpolated at TOA epoch : −90.444 ns
gps2utc  at MJD 59630              :  +2.800 ns
total                              : −87.644 ns
```

That is the one leg solid enough to pre-register as a reproduction target
(`REPRO-PSR-001`, ±1 ns).

---

## 11 — The result: the window does not close

Ten J0437−4715 TOAs fall inside the window — all from **one** observation,
`uwl_220220_104059_b4`, support **MJD 59630.445127 – 59630.489608**. Next observation is
14.9 days later, past the window.

The optical archive's earliest sample is **MJD 59631.788542**.

```
pulsar support ends    59630.489608
optical support starts 59631.788542
                       ─────────────
gap                     1.298934 d = 31.17 h
```

**They never overlap.** Nor does the pulsar overlap any VLBI session — the earliest
starts 2022-02-21T14:00, a day after the scan.

Wrote [`src/ftro/four_domain_intersection.py`](../src/ftro/four_domain_intersection.py):

| Combination | Result |
| --- | --- |
| gnss ∩ optical ∩ vlbi | **118.575 h** |
| optical ∩ pulsar | `no_common_support` |
| pulsar ∩ vlbi | `no_common_support` |
| **all four** | **`no_common_support`** |

Deliberately used per-comparison **envelopes** for optical support, which *overstates* it
(real support is fragmented into up to 1,934 runs per comparison). The null therefore
holds under an upper bound — relaxing the computation cannot manufacture an overlap.
**A strong null.**

Note the composition of two separately-filed low-severity items: the declared optical
coverage starts at 59630 ([`FTRO-DEF-009`](../ledgers/deficiency-log.md#ftro-def-009)),
and the pulsar scan sits at 59630.47. Taking the *declared* coverage at face value, the
four domains appear to intersect. Taking the *actual* support, they do not. Card §6's
insistence on computing support from records rather than campaign boundaries is doing
real work here — it is the difference between a false positive and the true answer.

Per §6 and §20: interval **not** widened, March 2023 optical dataset **not** substituted.
→ [`FTRO-DEF-023`](../ledgers/deficiency-log.md#ftro-def-023).

---

## 12 — Where that leaves the differentiating criterion

Both of the card's leading shared-ancestry candidates are blocked, in different domains,
for different reasons:

| Candidate path | Blocked by |
| --- | --- |
| IVS session → IERS EOP → pulsar barycentring | pulsar EOP artifact **unidentified** ([DEF-012](../ledgers/deficiency-log.md#ftro-def-012)) |
| optical time tags → station time scale → UTC(k)/BIPM | `ref_osc` **absent** ([DEF-003](../ledgers/deficiency-log.md#ftro-def-003), [DEF-004](../ledgers/deficiency-log.md#ftro-def-004)) |

Provisional: `shared_ancestry_demonstration = indeterminate`. The GNSS leg is the only
one fully pinned, and is the most promising remaining candidate for Phase 2.

Card §15.2 is explicit that this is a valid scientific result of the skeleton, not a
platform failure — and the platform did work: it located, pinned, verified and typed
every one of these gaps rather than papering over them.

---

## 13 — Gate 0

| Requirement | Status |
| --- | --- |
| Four product sets selected or explicitly missing | ✅ optical/pulsar/GNSS pinned; VLBI session selected, products explicitly `unresolved` |
| Four reproduction targets and tolerances locked | ✅ pre-registered in [selection note §4](../phase0/selection-note-v0.1.md) |
| Source and FTRO rights recorded separately | ✅ [rights ledger](../ledgers/rights-ledger.md) |
| First deficiency entries classified | ✅ **23 entries, all five classes** |

**Gate 0 passed.**

## 14 — Carried into Phase 1

1. Pin the R11040 vgosDB and downstream EOP products — needs a non-CDDIS route or credentials.
2. Add content-shape validation to every retrieval procedure, including ours (DEF-018).
3. Examine and record the licence of each evidence repository (currently unexamined).
4. Ask the depositors: `ref_osc` et al.; the two generating scripts; the TT realisation actually applied; the TOA set behind `NTOA 20836`.
5. Report the 64 duplicate abscissae upstream to IPTA.
6. Card v0.4 amendments: §5.1 "processing code" is not in the archive; §5.1 coverage lower bound is 59631.79; `tintervals` pin post-dates the data.

## 15 — Method notes to self

- **Read the pinned spec before classifying anything.** It saved a false `schema` filing
  on the time-varying uncertainty (§03c), and it produced the two strongest findings
  (§04): both came from the spec, not the data.
- **Write the check as a script.** `VP-GPS2UTC-001` found 64 duplicate abscissae I was
  not looking for. Eyeballing would have missed them.
- **Fetch metadata before bytes.** The `metadata.version = null` on Zenodo shaped the
  identity model before a single byte was downloaded.
- **A 200 is not a success.** §09 is the lesson of the session, and it applies to us.
