# PPTA DR3 Observation List for MJD 59630–59640 (PSR J0437−4715)

**Document ID:** FTRO-PSR-001 · **Version:** 0.1.0 · **Date:** 2026-08-25 · **Licence:** CC BY 4.0
**Task card:** FTRO-WS-001 v0.3 §5.2, §22.3

---

## 1. Result

**Exactly one observation** of PSR J0437−4715 falls inside the candidate window, yielding
**10 sub-banded TOAs**.

| Field | Value |
| --- | --- |
| Observation | `uwl_220220_104059_b4` |
| Scan start (from filename stamp) | 2022-02-20T10:40:59 UTC = MJD 59630.445127 |
| Integration `-tobs` | 3843.1 s (1.0675 h) |
| **Support interval** | **MJD 59630.445127 – 59630.489608** |
| Front end / back end | UWL / Medusa |
| Site code | `pks` |
| Bandwidth `-bw` | 832 MHz |
| Sub-band groups | `sbD2`, `sbF2` (`uwl_20CM`), `sbG2` (`uwl_10CM`) |
| TOAs | 10 |
| TOA epoch range | MJD 59630.467530701 – 59630.467530762 |
| Frequency range | 979.709 – 2545.197 MHz |
| Uncertainty range | 0.034 – 0.446 µs |

The 10 TOA epochs span 6.1 × 10⁻⁸ d ≈ 5.3 ms: they are sub-band TOAs of the same
integration, not independent epochs.

## 2. TOA detail

| # | Frequency (MHz) | TOA (MJD) | σ (µs) | Sub-band | `-group` | `-B` |
| ---: | ---: | --- | ---: | --- | --- | --- |
| 1 |  979.709 | 59630.467530741 | 0.356 | sbD2 | `UWL_sbD` | `uwl_20CM` |
| 2 | 1136.196 | 59630.467530707 | 0.435 | sbD2 | `UWL_sbD` | `uwl_20CM` |
| 3 | 1217.760 | 59630.467530761 | 0.446 | sbD2 | `UWL_sbD` | `uwl_20CM` |
| 4 | 1570.612 | 59630.467530727 | 0.034 | sbF2 | `UWL_sbF` | `uwl_20CM` |
| 5 | 1704.193 | 59630.467530719 | 0.047 | sbF2 | `UWL_sbF` | `uwl_20CM` |
| 6 | 1848.022 | 59630.467530713 | 0.058 | sbF2 | `UWL_sbF` | `uwl_20CM` |
| 7 | 1980.251 | 59630.467530708 | 0.067 | sbF2 | `UWL_sbF` | `uwl_20CM` |
| 8 | 2103.693 | 59630.467530704 | 0.084 | sbG2 | `UWL_sbG` | `uwl_10CM` |
| 9 | 2243.084 | 59630.467530701 | 0.113 | sbG2 | `UWL_sbG` | `uwl_10CM` |
| 10 | 2545.197 | 59630.467530762 | 0.146 | sbG2 | `UWL_sbG` | `uwl_10CM` |

Sorted by frequency. The TOA epochs are **not** monotonic in frequency: the highest
(2545.197 MHz) and one of the lowest (1217.760 MHz) carry the two latest epochs, so the
sub-band ordering is not a simple dispersion sweep.

## 3. Cadence context — the card's "terminal edge" concern

| | Epoch | Δ from selected |
| --- | --- | --- |
| Previous observation | MJD 59629.394670 (`uwl_220219_085623`) | −1.07 d |
| **Selected observation** | **MJD 59630.467531** | — |
| Next observation | MJD 59645.403173 (`uwl_220307_090825`) | **+14.94 d** |
| Last TOA in DR3 | MJD 59645.403173 | — |

The observed local cadence is irregular — 1.07 d before and 14.94 d after the selected scan — so
card §5.2's ~3-week figure is neither confirmed nor contradicted by this window; a cadence claim
would need the full DR3 epoch series. Critically, the **next** observation is 5.4 days *past the
end of the candidate window*, so the selected scan is the sole pulsar record available for it.

DR3's declared coverage ends 2022-03-07 (MJD 59645), i.e. 5 days after the window closes.
The candidate window is therefore genuinely at the release's terminal edge, but the
window itself **is** covered.

## 4. Ancestry chain, as far as evidence permits

```
J0437−4715 TOA @ MJD 59630.467530701           [resolvable]
  │
  ├── observed_by ──► Parkes "Murriyang" 64 m, UWL front end + Medusa backend
  │
  ├── time_referenced_to ──► pks2gps.clk            [resolvable]
  │        Parkes clock → GPS.  ~1-day cadence.
  │        Bracketing samples (59630.37155, −90.041 ns), (59631.37502, −94.252 ns)
  │        Interpolated at TOA epoch: −90.444 ns   (slope −4.196 ns/day)
  │        └── own ancestry: narratively described merge of three eras; no per-epoch
  │            receiver metadata                    [opaque]
  │
  ├── time_referenced_to ──► gps2utc.clk            [resolvable, VERIFIED VA-GPS2UTC-001]
  │        GPS → UTC.  C0′ regime throughout the window.
  │        Value at MJD 59630: +2.800 ns
  │        └── receiver tracked C0 or C0′?           [UNRESOLVED — AA-PARKES-C0C0PRIME-001]
  │
  ├── time_referenced_to ──► tai2tt_bipm2021.clk    [resolvable but CONTESTED]
  │        TAI → TT(BIPM2021), 10-day cadence
  │        Value at epoch 32.1840276670 s — EXTRAPOLATED via
  │        32.184 + 27667.5ns − 0.01(MJD − 59579.0)ns
  │        └── .par declares CLK TT(BIPM2020); no such artifact ships
  │                                                  [OPEN CONTESTATION — FTRO-DEF-011]
  │
  ├── uses_ephemeris ──► DE436                       [UNRESOLVED — declared, no artifact]
  │
  ├── uses_eop ──► ???                               [UNRESOLVED — NOT DECLARED AT ALL]
  │        No EOP/UT1/IERS/C04/polar-motion term anywhere in J0437-4715.par.
  │        Release identifies no EOP artifact; the source of the series is not
  │        evidenced (an unshipped TEMPO2 runtime is the likely but unverified supplier).
  │                                                  [FTRO-DEF-012]
  │
  └── evaluated_by ──► J0437-4715.par                [PARTIAL — AA-PPTA-TIMINGMODEL-001]
           NTOA 20836 vs 11,637 TOA lines shipped     [FTRO-DEF-013]
```

**Fully evidenced sub-chain:** observatory clock → GPS → UTC. Total correction at the
selected TOA epoch: **−90.444 + 2.800 = −87.644 ns**. This is what `REPRO-PSR-001`
pre-registers.

**Everything above UTC is contested or unresolved.**

## 5. Bearing on the shared-ancestry criterion

The card's leading candidate path is *IVS session → IERS EOP series → pulsar barycentring*.
The pulsar end of that path **cannot be evidenced**: no EOP artifact is identified in the
release ([`FTRO-DEF-012`](../ledgers/deficiency-log.md#ftro-def-012)).

The card (§15.1) anticipated an **opaque** EOP artifact. The observed outcome is different and
more severe: **`unresolved`** — no artifact is identified at all — so the expectation is not
strictly confirmed. No modern C04 snapshot is substituted (§20).

## 6. Rights

PPTA DR3 is **CC BY-SA 4.0**. `redistribution_mode = link_only`. This document records
identifiers, epochs, sizes, checksums and declared parameter values — facts, not
provider prose. See [`FTRO-DEF-014`](../ledgers/deficiency-log.md#ftro-def-014).
