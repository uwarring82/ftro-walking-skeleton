# ApplicabilityAssessment AA-PARKES-C0C0PRIME-001

**Version:** 1.0.0 · **Date:** 2026-08-25 · **Licence:** CC BY 4.0
**Task card:** FTRO-WS-001 v0.3 §14.1, §22.4

## Question

> Did the Parkes receiver configuration track the GPS Combined Clock (`C0`) or the
> almanac-steered realisation (`C0′`) during MJD 59630–59640?

Card §14.1: *"The correction choice depends on receiver configuration and evidence; it
is not inferable from the correction filename alone."*

## Subject

| Field | Value |
| --- | --- |
| Assessed artifact | `T2runtime/clock/gps2utc.clk` |
| Snapshot | `git:ipta/pulsar-clock-corrections@36dc139a150efde056aa32fa13deac856a7a679d` |
| SHA-256 | `7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a` — **verified** |
| Applicable interval | MJD 59630.0 – 59640.0 |
| Assessor | FTRO Phase-0, procedure `VP-GPS2UTC-001` v1.0.0 |
| Method | Automated regime-marker inspection + checksum verification |
| Output | [`phase0/evidence/VA-GPS2UTC-001.json`](../evidence/VA-GPS2UTC-001.json) |

## Findings

### 1. What the artifact supplies — **determined**

The file is internally partitioned by regime-marker comments:

| Lines | Regime | Source |
| --- | --- | --- |
| 25 – 6651 | `C0` | BIPM yearly summary tables (`utcgpsYY.ar`, `utcgpsgloYY.ar`) |
| 6654 – end | **`C0′`** | `https://webtai.bipm.org/ftp/pub/tai/other-products/utcgnss/utc-gps`, updated monthly |

The `C0′` block begins at **MJD 55559.0 (2010-12-29)**. The candidate window lies at
lines 10725–10735, **wholly inside the `C0′` block**.

`VP-GPS2UTC-001` result: **`supports`** — "every sample in the interval lies inside a
C0′ regime block." 11 samples, no gaps, daily cadence.

### 2. What the receiver tracked — **NOT determined**

The artifact **explicitly disclaims** applicability to any particular receiver. Its
header, verbatim:

> "The BIPM publishes these values as "C0'", from about 2011 to the present. […] This
> file contains both: when available, we use C0', before that we use C0.
> **This may or may not resemble what your GPS receiver system uses.**"

No evidence of the Parkes receiver configuration during MJD 59630–59640 was located.
`J0437-4715.par` contains no receiver-timing configuration term. PPTA DR3's
`clock/` directory contains only `pks2gps.clk` and `tai2tt_bipm2021.clk`.

Note further that the Parkes chain reaches GPS through `pks2gps.clk` ("Tie of Parkes
clock to GPS time standard"), and it is *that* tie whose receiver configuration matters.
`pks2gps.clk`'s own header describes a merge of three sources across different eras,
with post-MJD-58269.72743 values "taken from the Parkes observatory calibration page" —
a narrative provenance with no per-epoch receiver metadata.

### 3. Internal defect of the assessed artifact

`VP-GPS2UTC-001` also found **64 duplicate MJD abscissae**, 45 carrying two different
ordinates (max difference 1.0 ns). One is the `C0`→`C0′` boundary itself at MJD 55559.0,
where the two entries differ by 0.3 ns. **No duplicate falls inside the candidate
window**, so this pilot is unaffected. Recorded as
[`FTRO-DEF-016`](../../ledgers/deficiency-log.md#ftro-def-016).

## Outcome

| Field | Value |
| --- | --- |
| **`evidence_state`** | `resolvable` (for the artifact) / **`unresolved`** (for the receiver configuration) |
| **`VerificationActivity.result`** | `supports` — for the narrow claim "the artifact supplies C0′ over this interval" |
| **`contestation_state`** | `none` |
| **Assessment outcome** | **`indeterminate`** |

**The two claims must not be conflated.** It is *determined* that `gps2utc.clk` supplies
C0′-derived corrections for the candidate window. It is *undetermined* whether the
Parkes receiver tracked C0 or C0′, and the artifact itself warns that it may not match.

Per card §20, no substitution or assumption is made. The assessment stands at
`indeterminate` until receiver-configuration evidence is obtained.

## Action

Request from the PPTA / Parkes operations team the receiver timing-system configuration
in force during 2022-02, specifically whether the observatory 1 PPS was derived from a
Combined-Clock or almanac-steered GPS realisation.
