# ApplicabilityAssessment AA-PPTA-CLKREALISATION-001

**Version:** 1.0.0 · **Date:** 2026-08-25 · **Licence:** CC BY 4.0
**Task card:** FTRO-WS-001 v0.3 §14.1, §20 ("Timing-model applicability requires judgment")

## Question

> Which realisation of terrestrial time was applied in producing the PPTA DR3
> J0437−4715 TOAs: `TT(BIPM2020)` as the timing model declares, or `TT(BIPM2021)` as the
> shipped clock file supplies?

## Evidence

| Artifact | Declares |
| --- | --- |
| `toas_and_parameters/all/J0437-4715.par` (SHA-256 `cfbd0db49a66d8a1…`) | `CLK            TT(BIPM2020)` |
| `toas_and_parameters/clock/tai2tt_bipm2021.clk` (SHA-256 `047c2a19b13f6923…`) | `# TAI TT(BIPM2021)` |

**No `TT(BIPM2020)` artifact exists anywhere in either DR3 collection.** The `clock/`
directory contains exactly two files: `pks2gps.clk` and `tai2tt_bipm2021.clk`.

The two artifacts are co-located in the same release, at
`toas_and_parameters/all/` and `toas_and_parameters/clock/` respectively, and the
release README describes `clock/` as containing "the TEMPO2 clock correction files used
in the production of this dataset."

## Additional finding: the shipped values are extrapolated

`tai2tt_bipm2021.clk`'s header states:

> "BIPM extrapolation using the formula: `32.184 + 27667.5ns - 0.01(MJD - 59579.0)ns`"

Verified against the table: the formula yields 32.1840276670 s at the candidate epoch,
matching the tabulated MJD 59629 value exactly, and 32.1840276669 at MJD 59639.

The candidate epoch MJD 59630.4675 lies **51.5 days after** the extrapolation reference
epoch MJD 59579. The table extends to MJD 99999.

So the TT realisation applied at the candidate epoch is a **linear extrapolation with
no stated uncertainty**, not a BIPM-published measured value. Recorded as
[`FTRO-DEF-017`](../../ledgers/deficiency-log.md#ftro-def-017).

## Outcome

| Field | Value |
| --- | --- |
| **`evidence_state`** | `resolvable` — both artifacts retrieved and inspected |
| **`VerificationActivity.result`** | `contradicts` — for the claim "the release's clock artifacts satisfy the timing model's declared `CLK`" |
| **`contestation_state`** | **`open`** — two artifacts in one release assert incompatible realisations |
| **Assessment outcome** | **`indeterminate`** |

Both assertions are retained with their evidence. Neither is silently corrected, and
no TT(BIPM2020) artifact is fetched from elsewhere to "repair" the release
(card §20: *"Mark evidence opaque or unresolved; do not substitute a modern product"*).

Recorded as [`FTRO-DEF-011`](../../ledgers/deficiency-log.md#ftro-def-011).

## Impact on the pre-registered reproduction

`REPRO-PSR-001` deliberately targets only the **observatory-to-UTC** leg
(`pks2gps.clk` + `gps2utc.clk`), which is fully evidenced, and stops before the
TAI→TT step, precisely because that step is contested here.

## Action

Ask the PPTA team which TT realisation was applied during production, and whether the
`CLK TT(BIPM2020)` line in the shipped `.par` is a stale carry-over from an earlier
processing round.
