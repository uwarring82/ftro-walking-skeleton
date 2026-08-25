# Session 02 — External review: corrections and self-directed deficiencies

**Date:** 2026-08-25 · **Reviews:** commit [`fdbf2b9`](https://github.com/uwarring82/ftro-walking-skeleton/commit/fdbf2b9b4564e7e489e75a2d638faeedf1b79e5e)
**Outcome:** central result upheld; nine corrections applied; four new deficiencies, three self-directed.
**Licence:** CC BY 4.0

> **Append-only.** [Session 01](2026-08-25-session-01-phase0.md) is left **unedited**, including
> the passages corrected below. It records what was believed at that knowledge time, and that is
> itself data — the same bitemporal rule the project applies to provider evidence. Every correction
> below back-links to the session-01 passage it supersedes.

---

## 00 — What the review did and did not overturn

The four-domain `no_common_support` conclusion **survives**, and survives more strongly than it was
originally argued: it now holds at **exact run level**, not merely under a generous upper bound.

What did not survive: several claims that outran their evidence, one identity model that was simply
wrong, and one access conclusion drawn from a single data centre. Three of those became
self-directed deficiency entries.

The uncomfortable pattern: **every one of my errors was an over-claim in the direction of a more
impressive result.** Not one was a hedge that turned out too cautious.

---

## 01 — The error I most want on the record

Session 01 §01 reasoned:

> "**Note on `metadata.version`: it is `null`.** Zenodo's concept DOI resolves to the latest
> version, so concept and snapshot identity are not separable from provider metadata alone. An FTRO
> composed snapshot identity is required — the first live instance of the card's §10 rule."

Every step of that is wrong.

1. `metadata.version` is not null — **the key does not exist**. The only `null` values in the record
   are creators' `affiliation` fields.
2. A human-readable version *string* has no bearing on PID separability anyway.
3. Zenodo asserts the concept/version distinction in **four independent fields**: `conceptdoi`
   (`10.5281/zenodo.17107692`), `conceptrecid`, `links.parent_doi` versus `links.self_doi`, and
   `metadata.relations.version[0].parent.pid_value`.
4. Card §10 composition is **conditional**: it applies "when a provider supplies no immutable
   snapshot identifier". Zenodo supplies one. The precondition was never met.

So in the very leg used to *demonstrate* the two-level identity model, I invented an identity where
the provider had already supplied one. The string `17107692` appeared **nowhere** in the repository
— while sitting in the cached record my own pipeline had read and re-read all session.

This is the mirror image of the failure the project exists to catch. Not missing evidence:
**available evidence not read.** Filed as
[`FTRO-DEF-024`](../ledgers/deficiency-log.md#ftro-def-024).

Corrected: `concept_id` is the concept DOI, `snapshot_id` the version DOI, `snapshot_kind`
`provider_immutable`. The md5-composed string survives as a `file_identity`, which is what it always
was.

A related subtlety the correction surfaced: the version DOI pins the **files** immutably but not the
**metadata**. `revision: 6` records six metadata edits on 2025-09-12 between 16:09:41Z and 16:22:22Z,
none of which minted a new DOI. A metadata snapshot needs `revision` + `updated` as well.

Profile consequence: an `ftro_composed` identity must now record
`composition_precondition_checked[]` — which provider fields were inspected and found absent. An
identity composed without that record is non-conforming.

---

## 02 — 118.575 h was an upper bound presented as a measurement

Session 01 §11 reported the three-domain overlap as **118.575 h**. That figure came from
per-comparison optical **envelopes**, and the reviewer's independent run-level calculation gave
~82.013 h.

Reimplemented `four_domain_intersection.py` to take the exact union of all valid runs:

```
optical basis: run_level_union (7398 runs -> 1384 disjoint intervals)
optical  support  133.112 h   (was 197.075 h as envelopes)
optical|vlbi       82.013 h   (was 118.575 h)
FOUR-DOMAIN: no_common_support (0 h)
```

**82.013 h** — matching the reviewer's independent figure. The four-domain null is unchanged.

The important change is not the number, it is what can now be claimed. Optical support is **exact**.
But VLBI still uses *scheduled session intervals* and GNSS *daily product validity* — both upper
bounds — so any overlap involving them remains an upper bound, and the report now says so per-leg
via a `bound` field.

Which also corrects a sloppier claim. Session 01 §11 said "relaxing the computation cannot
manufacture an overlap". That is backwards: *relaxing* to declared coverage is precisely what would
manufacture one. The defensible direction is **refinement** — refining generous envelopes into exact
support can only *remove* overlap. "Robust `no_common_support` under conservative envelopes" is both
accurate and less prone to being read as a statistical claim, which "strong null" invited.

---

## 03 — "Every combination including the pulsar is empty"

I wrote that in the hand-off summary. My own committed
[`four-domain-intersection.json`](../phase0/reports/four-domain-intersection.json) records
`gnss|pulsar` as `overlap`, 1.067 h.

The machine-readable layer and the selection note were both correct throughout. The error lived
only in the two narrative summaries — README and lab note — which listed every empty pulsar
combination and silently omitted the one non-empty one, under a heading reading "The four domains
do not overlap".

Corrected to: only the two pairs optical∩pulsar and VLBI∩pulsar, and every three- and four-domain
combination containing the pulsar, are empty. `GNSS ∩ pulsar` is not.

Worth naming the mechanism, because it will recur: **the summary tables were curated to support the
headline rather than to report the computation.** No individual cell was false. The omission did
the work.

---

## 04 — A census that was actually a 0.44% sample

Session 01 §03b reported the quantisation as "verified on 1,564,882 of 1,564,882 sampled values",
in five documents.

That number came from an ad-hoc interactive command reading the **first 40 `.dat` files**. No
committed script performed a decimal-place or 1e-6-multiple test at all, and the evidence pointer I
cited (`sample_spacing_histogram_s`) does not contain it. It read as an exhaustive census of a
9-million-sample corpus; it was 0.44% of it, from an uncommitted command.

Fixed by implementing the test rather than restating the number.
`analyse_optical.py` now emits `mjd_quantum_check`:

```
n_tested = 9,018,290   n_conforming = 9,018,290   n_exceptions = 0
decimal_place_histogram = {"6": 9018290}
```

The finding survives intact — and is now *stronger*, because it is exhaustive and reproducible. But
the evidence discipline failed, in exactly the class this ledger exists to record.
[`FTRO-DEF-027`](../ledgers/deficiency-log.md#ftro-def-027).

The same pass caught a second evidence-pointer problem: `sample_spacing_histogram_s` is truncated to
the 20 most common spacings, covering 8,999,974 of 9,018,038 intervals. It could never have
supported an exceptionless claim about all spacings. There is now a `sample_spacing_coverage` key
that states the shortfall.

Rule adopted (D-023): **a number quoted in a finding must be traceable to a key in a committed
report, and the evidence pointer must name that key.**

---

## 05 — Eight orders of magnitude between quantities that cannot be divided

Six documents compared the 86.4 ms time quantum against 10⁻¹⁷ fractional-frequency uncertainty and
called it "roughly eight orders of magnitude apart".

Seconds and a dimensionless ratio are different kinds of quantity. The ratio is not merely
imprecise, it is undefined — and I could not reconstruct where the "eight" came from. No arithmetic
in the repo yields it.

Deleted rather than recalculated (D-027). The substantive point needs no ratio: **±43.2 ms is the
binding limit on placing these records on any shared time axis**, whatever the frequency data's
precision.

The related over-claim: I stated the 1 s grid as fact. The 86.4 ms quantum *is* measured — every
value, no exceptions. The 1 s grid is an **inference** from the dither ratio (1.347775 observed
against 1.347826 predicted), and nothing in the archive declares a sampling grid. Now stated as
"strongly consistent with nearest-rounding of a one-second grid, implying at most ±43.2 ms
serialisation error under that model."

---

## 06 — The EOP finding was not a confirmation

Session 01 §10 called the EOP result "the pre-registered EOP prediction, confirmed… in a stronger
form than written."

Card §15.1 predicted an **opaque** artifact — one identified but not sufficiently inspectable. What
we found is an **unidentified** one: `unresolved`, a different state in the profile's own
vocabulary.

A different outcome is not a confirmation, even when it is more severe. Treating "worse than
predicted" as "prediction confirmed" is how pre-registration gets quietly hollowed out — and the
whole point of §15.1 was to make that impossible. Corrected everywhere (D-028).

Two adjacent scope fixes:
- DEF-012's title claimed "no EOP artifact **anywhere in the release**". The evidence is a grep of
  one `.par` plus the part-1 listing; ~2.77 TB and the part-2 listing were never searched. Retitled
  to what was actually checked.
- "The dependency is satisfied implicitly by an unshipped TEMPO2 runtime" is an *inference* about
  production, never evidenced. What is supported: the release identifies no EOP artifact;
  barycentring requires one; TEMPO2 is the likely but unverified supplier.

---

## 07 — "Unresolved" that meant "I only tried one data centre"

Session 01 §09 hit the CDDIS Earthdata wall and recorded `evidence_state = unresolved` for the VLBI
products, reporting that credentials or a non-CDDIS route were needed.

I never tried OPAR. It serves the same archive anonymously:

```
https://ivsopar.obspm.fr/vlbi/ivsdata/vgosdb/2022/20220228-r11040.tgz
19,610,760 bytes   sha256 0211948678aebfbcfdcf0f8d1ab8777bfd940605668073b8deb99aba1ff2ba54
```

An access-class conclusion drawn from a single channel. "Unresolved" asserted an unavailability that
was never established — which is precisely the unsupported null that typed incompleteness exists to
prevent. [`FTRO-DEF-025`](../ledgers/deficiency-log.md#ftro-def-025).

Rule adopted (D-025): `access_class` may only be recorded after enumerating the provider's listed
distribution channels, **and the enumeration must be recorded**.

Pinning it produced a finding worth more than the pin. The archive contains **seven wrapper files
across five internal versions** from three analysis centres:

```
V001_iMPI   V002_iGSFC   V003_iGSFC   V004_iGSFC   V004_iIVS   V005_iGSFC   V005_iIVS
```

The byte checksum pins the *container*, not the wrapper version a downstream analysis consumed. Two
chains citing the same checksum may have used different versions from different centres. The
profile's two-level identity is insufficient here — a **third, intra-archive level** is needed
([`FTRO-DEF-026`](../ledgers/deficiency-log.md#ftro-def-026)).

And `Last-Modified` is **2025-12-15**, so this is a re-release, not a frozen 2022 artifact. The
checksum pins *this retrieval*.

---

## 08 — Closing DEF-018 against ourselves

Session 01 logged DEF-018 against our own tooling — `pin_igs.py` validated status and checksum but
not content shape — and then did nothing about it. A self-directed deficiency that is never closed
is decoration.

Both retrieval scripts now validate content shape. The regression test runs against the live CDDIS
URL:

```
CDDIS: HTTP 200, 10980 bytes, Content-Type=text/html
  validate_content -> False | response is HTML, not a product file;
                             authentication markers present: ['Earthdata Login','oauth','login','password']
genuine igs21980.sp3.Z -> True | ok
```

DEF-018 moves to `resolved` for FTRO tooling. CDDIS's own behaviour is unchanged and remains
reportable upstream, and the PPTA leg is still pinned at `status_and_checksum` only — recorded
rather than glossed.

---

## 09 — Smaller corrections

| Fix | Was | Now |
| --- | --- | --- |
| Truncated digests | `@sha256:` + 16 hex, in the identity itself | full 64 chars; short forms only in named `sha256_short` fields or visible head…tail prose |
| `pin_igs.py:96` | `[:16]` slice, reproducing the defect for all 57 pins | full digest emitted |
| CFF 1.2 | `role:` invalid on author; references lacked required `authors` | validates; 131 author entries, **all 67 ORCIDs verified against provider metadata** |
| RO-Crate 1.3 | external DOIs reachable only via `mentions`; `src/ftro` lacked trailing slash | DOIs in `hasPart` + `isBasedOn`; `src/ftro/` as directory Dataset with per-script File entities |
| Cadence | "~3-week cadence confirmed: a 16.0-day gap" | 1.07 d before, 14.94 d after — irregular; neither confirms nor contradicts |
| Validity-table total | "Total: 282.37 h" in a 240 h window | "Sum over comparisons" — comparison-hours, not wall-clock; union is 133.112 h |
| Rights summary | "three of four legs carry rights not established" | one of four is redistributable; PPTA's rights *are* established, they are copyleft |
| "not a depositor error" | an unevidenced judgement about depositors | "structurally permitted by the format" |
| Selection note status | "Gate 0 candidate" | "Gate 0 passed" — §6 already said so |

---

## 10 — Ledger state

| | Session 01 | Session 02 |
| --- | --- | --- |
| Entries | 23 | **27** |
| Resolved | 0 | **4** |
| Self-directed | 1 (DEF-018, unfixed) | **4** (018 closed; 024, 025, 027 new) |

`source_evidence` 17 · `schema` 4 · `execution` 3 · `rights` 2 · `policy` 1

---

## 11 — Method notes to self

- **My errors were not random.** Nine corrections, and every one made the result look better than
  the evidence supported. A review that only checks arithmetic will not catch this class; it needs
  someone asking "does the claim exceed the evidence?" of each sentence.
- **A curated table can lie while every cell is true.** §03 is the cleanest example: the omission
  did the work, not any false entry.
- **Read the metadata you already fetched.** §01 was not a hard problem. The concept DOI sat in a
  file I had open all session, and I reasoned instead from a field that did not exist.
- **"Unresolved" is a claim, and it needs evidence too.** §07 — I recorded an unavailability I had
  not established. Typed incompleteness is only honest if the types are earned.
- **Fix your own deficiencies or stop filing them.** DEF-018 sat open for a session while I cited it
  as evidence of good practice.
- **Verification before correction pays.** Every reviewer claim was checked independently; the
  Zenodo one turned out *worse* than reported (absent, not null) and the run-level figure landed on
  82.013 h from a separate implementation. Accepting the corrections unverified would have missed
  both.

---

## 12 — Carried forward, unchanged from session 01 §14

The downstream VLBI analysis-centre product and IERS EOP series remain **unresolved** — that leg is
half-closed, not closed. The four depositor question groups and the IPTA upstream report are
untouched by this session and still need to be sent.
