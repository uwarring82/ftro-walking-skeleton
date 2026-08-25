# ApplicabilityAssessment AA-PPTA-TIMINGMODEL-001

**Version:** 1.0.0 · **Date:** 2026-08-25 · **Licence:** CC BY 4.0
**Task card:** FTRO-WS-001 v0.3 §5.2 ("timing-model applicability is not a manifest fact"), §22.4

## Question

> Is the shipped timing model `toas_and_parameters/all/J0437-4715.par` applicable to the
> shipped TOA set `toas_and_parameters/all/J0437-4715.tim`, and to the selected
> observation at MJD 59630.4675 in particular?

## Subject

| Field | Value |
| --- | --- |
| Timing model | `J0437-4715.par`, 4,402 B, SHA-256 `cfbd0db49a66d8a1…` |
| TOA set | `J0437-4715.tim`, 4,464,619 B, SHA-256 `ee6a2dec40b4dc6f…` |
| Selected observation | `uwl_220220_104059_b4`, UWL / Medusa, `-tobs 3843.1` s |
| Applicable interval under test | MJD 59630.445127 – 59630.489608 |
| Assessor | FTRO Phase-0, manual inspection with scripted counting |

## Findings

### 1. Interval coverage — **supports**

| Model term | Value | TOA set |
| --- | --- | --- |
| `START` | 52741.358093 | first TOA 54297.85253 |
| `FINISH` | 59645.403173* | last TOA 59645.40317 |

*`FINISH 59645.403172955089218` matches the final TOA epoch exactly. The selected
observation at MJD 59630.4675 lies well inside `[START, FINISH]`.

The model's reference epochs (`PEPOCH`, `POSEPOCH`, `DMEPOCH` = 55486; `TZRMJD` = 56192.66)
all precede the selected observation by 11–4 years, so the applied solution is a
long extrapolation in spin and astrometric phase from its reference epoch — normal for
pulsar timing, but a material fact for uncertainty accounting.

### 2. Fit metadata does not match the co-located TOA set — **contradicts**

| Quantity | Model states | TOA file contains |
| --- | --- | --- |
| Number of TOAs | `NTOA 20836` | **11,637** TOA lines |
| Degrees of freedom | `CHI2R 23.8024 20780` | consistent with 20,836, not 11,637 |

The `.tim` contains **no** `INCLUDE`, `JUMP`, `EFAC` or `EQUAD` directives that could
reconcile the difference. The 20,780 d.o.f. is consistent with 20,836 TOAs less ~56
fitted parameters, so the model was fitted against a set roughly 79% larger than the
one shipped alongside it — plausibly a combined narrowband-plus-wideband set.

A cold reproducer loading this `.par` with this `.tim` **cannot** reproduce the quoted
χ²_r = 23.80. Recorded as
[`FTRO-DEF-013`](../../ledgers/deficiency-log.md#ftro-def-013).

### 3. Declared dependencies — mixed

| Term | Value | `evidence_state` |
| --- | --- | --- |
| `EPHEM` | `DE436` | `unresolved` — no ephemeris artifact ships with the release |
| `CLK` | `TT(BIPM2020)` | **contested** — see [AA-PPTA-CLKREALISATION-001](AA-PPTA-CLKREALISATION-001.md) |
| `UNITS` | `TCB` | `resolvable` — declared |
| `TIMEEPH` | `IF99` | `unresolved` — no artifact |
| `T2CMETHOD` | `IAU2000B` | `unresolved` — no artifact |
| `CORRECT_TROPOSPHERE` | `Y` | `unresolved` — no model artifact or met data identified |
| Earth orientation | **not declared at all** | **`unresolved`** — [`FTRO-DEF-012`](../../ledgers/deficiency-log.md#ftro-def-012) |

`J0437-4715.par` contains **zero** occurrences of `EOP`, `UT1`, `IERS`, `C04` or polar
motion. Barycentring nevertheless requires an Earth-orientation series; the dependency
is satisfied implicitly by an unshipped, unversioned TEMPO2 runtime.

This **confirms the card's pre-registered expectation** (§15.1) that the PPTA→C04 chain
would be opaque — in a stronger form: the artifact is not merely opaque, it is
**unidentified**.

### 4. Chi-squared magnitude

`CHI2R 23.8024` indicates the model does not describe its TOA set within the quoted
uncertainties — expected for J0437−4715, whose timing residuals are dominated by
red noise handled separately in `noisefiles/`. The `all/` directory ships both a
"basic" `.par` and a `_singlePsrNoise_fit.par`; the **basic** file assessed here is
described by the release README as one whose "timing model parameters should be
considered less reliable."

## Outcome

| Field | Value |
| --- | --- |
| **`evidence_state`** | `resolvable` for both artifacts; `unresolved` for 5 of 7 declared dependencies |
| **`VerificationActivity.result`** | `indeterminate` overall — `supports` on interval coverage, `contradicts` on fit metadata |
| **`contestation_state`** | `open` (inherited from AA-PPTA-CLKREALISATION-001) |
| **Assessment outcome** | **`partial`** — the model covers the selected epoch, but its fit metadata does not correspond to the co-located TOA set and most of its declared ancestry is unresolved |

The model is **applicable in interval** to the selected observation. It is **not
verifiable** against the shipped TOAs, and its ancestry is largely unresolved. This is
recorded as a versioned assessment with assessor, method, evidence, interval and
outcome, per card §5.2 — not as a bare manifest statement.

## Action

1. Ask the PPTA team which TOA set produced `NTOA 20836` / `CHI2R 23.8024`.
2. Request the TEMPO2 runtime revision and the `eopc04` and `DE436` artifacts present at
   production time.
3. Re-assess against `J0437-4715_singlePsrNoise_fit.par` in Phase 2 and compare outcomes.
