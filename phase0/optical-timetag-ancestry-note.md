# Optical Time-Tag Ancestry Note

**Document ID:** FTRO-OTA-001 · **Version:** 0.2.0 · **Date:** 2026-08-25
**Task card:** FTRO-WS-001 v0.3 §5.1, §15.1, §22.6 · **Licence:** CC BY 4.0

> **The question.** Card §5.1: *"identify what physically realises the one-second MJD
> time tags. Extract the declared `ref_osc`, `interval`, `lag` and `weighting` fields;
> then seek the station time scale, maser or other clock and any UTC(k)/BIPM
> relationship supporting those tags."*

> **The answer.** The chain terminates at `evidence_state = unresolved`, one step in.
> All four fields are absent from all twelve comparisons. The archive cannot name what
> realises its own time tags, and its own pinned format specification declares time
> transfer out of scope.

---

## 1. What the archive actually carries

Twelve comparison directories, 252 `.dat` files, 12 `.yml` files, 9,018,290 samples.
Each `.dat` row is `MJD  Δ_{A→B}  flag  uA_sys  uB_sys`.

The complete set of YAML keys used anywhere in the archive is:

```
denrhoBA  grsA  grsB  name  nu0A  nu0B  numrhoBA  sB  uA_sys  uB_sys
```

The pinned format ([`INRIM/optical-link-data-format@689bda77`](https://github.com/INRIM/optical-link-data-format/tree/689bda77000fec52c401bc0c9c3664d1dd534ecb),
`README.md` SHA-256 `cf93ae7a…fcee98`, **verified**) defines four further *optional*
keys, none of which appears:

| Key | Specification text | Present? |
| --- | --- | --- |
| `interval` | "Duration of each measurement, in seconds (optional)" | **absent, 12/12** |
| `lag` | "Fractional timetag location wrt the interval (1=end of the interval) (optional)" | **absent, 12/12** |
| `weighting` | "Weighting function of the frequency counter (optional) — 'lambda' or 'pi'" | **absent, 12/12** |
| `ref_osc` | "Local reference oscillator (optional) — String" | **absent, 12/12** |

The omission is **specification-conformant**: all four are optional. It is nonetheless
evidentially fatal. See [`FTRO-DEF-003`](../ledgers/deficiency-log.md#ftro-def-003).

---

## 2. Consequence 1 — the time tag cannot be placed within its own integration

A frequency-counter sample is an average over an interval, not an instant. Locating
its epoch requires all three of `interval`, `lag` and `weighting`:

- without `interval`, the averaging duration is unknown;
- without `lag`, it is unknown whether the tag marks the start, midpoint or end
  (the specification's own example, "1 = end of the interval", shows the range);
- without `weighting`, the counter response — Λ (triangular) or Π (rectangular) — is
  unknown, and these weight the interval differently.

If `lag` were 0 versus 1 with a 1 s `interval`, the true epoch of every sample shifts
by a full second. **Nothing in the archive excludes either.**

---

## 3. Consequence 2 — the comparator output is formally ambiguous

Every one of the 12 comparisons uses ρ⁰_{B,A} = ν̂⁰_B/ν̂⁰_A and s_B = ν̂⁰_B
(`numrhoBA` = `nu0B` and `denrhoBA` = `nu0A`, to within float64 round-trip artifacts —
[`FTRO-DEF-010`](../ledgers/deficiency-log.md#ftro-def-010)).

The specification's "Examples of comparator outputs" table contains **two rows** with
exactly that ρ⁰ and that s_B, differing *only* in the reference oscillator:

| ρ⁰_{B,A} | s_B | **Ref.** | Δ_{A→B} | Physical interpretation |
| --- | --- | --- | --- | --- |
| ν̂⁰_B/ν̂⁰_A | ν̂⁰_B | **A** | ρ̃_{B,A} | Frequency of B, referenced to A, relative units |
| ν̂⁰_B/ν̂⁰_A | ν̂⁰_B | **local RF** | ρ̃_{B,x} − ρ̃_{A,x} | Difference of reduced frequency ratios, using an external reference *x* |

`ref_osc` is the field that would distinguish them, and it is absent. The two readings
have **different reference oscillators and therefore different time-tag ancestry**: one
chains to oscillator A, the other to an unnamed local RF reference *x*.

Both are retained as competing assertions. See
[`FTRO-DEF-004`](../ledgers/deficiency-log.md#ftro-def-004).

---

## 4. Consequence 3 — the recorded time coordinate is quantised at 86.4 ms

Independent of the missing fields, the *serialised* time coordinate has a measurable defect.
Every MJD value carries exactly 6 decimal places and is an exact multiple of 10⁻⁶ d =
**86.4 ms** — a census of **9,018,290 of 9,018,290** values with **0 exceptions**, computed by
`src/ftro/analyse_optical.py` and recorded at
[`optical-inventory-summary.json#mjd_quantum_check`](reports/optical-inventory-summary.json).

The spacing histogram is strongly consistent with an underlying one-second grid:

| Spacing | Count | In quanta |
| --- | --- | --- |
| 1.0368 s | 5,139,806 | 12 |
| 0.9504 s | 3,813,549 | 11 |

- observed ratio 5,139,806 / 3,813,549 = **1.347775**
- ratio required for a mean of exactly 1.000000 s = 0.0496/0.0368 = **1.347826**
- implied mean spacing = **0.999999199 s**

This is strongly consistent with nearest-rounding of a one-second grid to the 86.4 ms quantum,
producing a deterministic 11/12-quantum dither. **Under that model the maximum serialisation
error is ±43.2 ms**, 4.3% of the nominal sampling interval. The model is an inference: no field in
the archive declares the sampling grid. Note also that the spacing histogram is truncated to the
20 most common spacings, covering 8,999,974 of 9,018,038 intervals.

The serialised time coordinate and the reported fractional-frequency uncertainty are quantities of
different kinds — seconds against a dimensionless ratio — so no ratio between them is meaningful.
What follows is nonetheless decisive: any alignment certificate involving these records is floored
at ~43 ms by the serialisation alone, before any question of physical realisation arises. See
[`FTRO-DEF-002`](../ledgers/deficiency-log.md#ftro-def-002).

---

## 5. Why the gap is structurally permitted by the format

The pinned specification's second sentence reads:

> "Clock comparison is understood to mean measuring the ratio of the frequencies of two
> clocks. **Time transfer and time comparison are beyond the scope of this format.**"

The format was designed to carry *frequency ratios*. Its MJD column exists to index
samples, not to assert a time-referenced epoch. The archive is being asked, by this
task card, a question its format explicitly declines to answer.

The gap is therefore **structurally permitted by the format**, and the finding is about the
**federation boundary**: a cross-domain observatory needs time-tag ancestry that domain formats
optimised for frequency ratios were never built to carry. Whether a depositor could nonetheless
have populated the optional fields is a separate question this assessment does not settle.

---

## 6. Chain as far as evidence permits

```
optical comparator output  Δ_{A→B}   [12 comparisons, 9,018,290 samples]
  │
  ├── conforms_to ────► optical-link-data-format @ 689bda77   [resolvable, verified]
  │
  ├── generated_by ───► 06-procclocks-v3.py  (11 comparisons, 2025-01-20)
  │                     convert-to-rocit.py  (NPL only, 2024-04-22)
  │                        └── evidence_state: UNRESOLVED — neither script is in the
  │                            archive  (FTRO-DEF-007, FTRO-DEF-008)
  │
  └── time_referenced_to ──► ??? 
                             └── evidence_state: UNRESOLVED
                                 ref_osc absent (FTRO-DEF-003)
                                 → station time scale: NOT IDENTIFIED
                                 → maser / local oscillator: NOT IDENTIFIED
                                 → UTC(k): NOT REACHED
                                 → BIPM relationship: NOT REACHED
```

**No node is invented to close this chain.** Per card §20, no modern or substitute
artifact is inserted where evidence is missing.

---

## 7. Bearing on the shared-ancestry criterion (§15.1)

Card §15.1 states the optical leg's cross-domain ancestry question is "the time-tag
chain: which local oscillator or station time scale realises the one-second MJD tags,
and whether that chain reaches an evidenced UTC(k) or BIPM-related node."

**It does not.** The chain terminates at `unresolved` before reaching any station time
scale. The optical leg therefore **cannot** contribute a shared-ancestry demonstration
through its time tags on present public evidence.

Combined with [`FTRO-DEF-012`](../ledgers/deficiency-log.md#ftro-def-012) — the PPTA
release identifies no EOP artifact at all — **both** of the card's leading candidate
shared-ancestry paths are blocked by unresolved evidence, in different domains, for
different reasons.

Provisional grading under §15.2: `shared_ancestry_demonstration = indeterminate`,
pending the Phase-2 traversal of the GNSS and VLBI legs, where the IGS product line is
fully pinned and remains the most promising candidate.

---

## 8. Actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Request `ref_osc`, `interval`, `lag`, `weighting` from the depositors for all 12 comparisons | FTRO → INRIM/PTB/SYRTE/NPL |
| 2 | Propose that these fields become **required** when a file is published as a citable archive | FTRO → format maintainers |
| 3 | Request the two generating scripts and an environment lock | FTRO → depositors |
| 4 | Request time tags at a precision commensurate with the sampling interval | FTRO → depositors |
| 5 | Add `time_coordinate_quantum` to the FTRO profile ([`FTRO-DEF-021`](../ledgers/deficiency-log.md#ftro-def-021)) | FTRO |

None of these is a prerequisite for continuing: the unresolved state **is** the
Phase-0 result, and it is recorded as data rather than as a blocker.
