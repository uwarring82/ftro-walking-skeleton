# FTRO Source Ledger

**Version:** 0.1.0 · **Opened:** 2026-08-25 · **Licence:** CC BY 4.0

Every artifact pinned in Phase 0, with its concept identity, snapshot identity, checksum
and evidence state. Machine-readable companion:
[`phase0/evidence/identities.json`](../phase0/evidence/identities.json).

`evidence_state ∈ {resolvable, opaque, unresolved}`

---

## Optical

| Artifact | Snapshot identity | Checksum | State |
| --- | --- | --- | --- |
| ROCIT campaign results.zip | `ftro:snapshot:zenodo/17107693/…@md5:4ae290f5…` | MD5 `4ae290f559c90b462991286c933a1147` ✅ matches card<br>SHA-256 `6168e24a0c29ce0929e9651460f11ea77f151176e1ba3d0fe3428e1e08bd56bd` | `resolvable` |
| optical-link-data-format | `git:INRIM/optical-link-data-format@689bda77000fec52c401bc0c9c3664d1dd534ecb` | README SHA-256 `cf93ae7a…fcee98` ✅ matches card | `resolvable` |
| tintervals | `git:INRIM/tintervals@2064db12777df78bc87f68f7710a47176192c2e1` | commit dated 2026-08-16 ⚠️ **19 months after the data** | `resolvable`, edge `contextualized_by` |
| Local reference oscillator | — | — | **`unresolved`** |
| Station time scale / UTC(k) | — | — | **`unresolved`** |
| Generating scripts | `06-procclocks-v3.py`, `convert-to-rocit.py` | named in headers, **absent from archive** | **`unresolved`** |

Size 83,530,540 B · 12 comparisons · 252 `.dat` · 12 `.yml` · 9,018,290 samples
Actual coverage **MJD 59631.78854 – 59675.00000** (declared 59630–59675)

## Pulsar

| Artifact | Snapshot identity | Size / checksum | State |
| --- | --- | --- | --- |
| PPTA DR3 (concept) | `ftro:concept:ppta/dr3` over DOIs `10.25919/j4xr-wp05` + `10.25919/axvw-qa43` | 90,884 shared paths; 18,414 / 15,509 unique | `resolvable` |
| `J0437-4715.tim` | `…@sha256:ee6a2dec40b4dc6f` | 4,464,619 B ✅ matches manifest | `resolvable` |
| `J0437-4715.par` | `…@sha256:cfbd0db49a66d8a1` | 4,402 B ✅ | `resolvable` |
| `pks2gps.clk` | `…@sha256:c8131f51e17eef40` | 1,742,710 B ✅ | `resolvable` (own upstream `opaque`) |
| `tai2tt_bipm2021.clk` | `…@sha256:047c2a19b13f6923` | 48,871 B ✅ | `resolvable`, **contested** |
| `gps2utc.clk` | `git:ipta/pulsar-clock-corrections@36dc139a…` | SHA-256 `7a1dcb60…669a0a` ✅ matches card | `resolvable`, **verified** `VA-GPS2UTC-001` |
| `DE436` ephemeris | declared in `.par` | no artifact ships | **`unresolved`** |
| Earth-orientation series | **not declared at all** | — | **`unresolved`** |
| `IF99` time ephemeris | declared in `.par` | no artifact | **`unresolved`** |
| `IAU2000B` T2C method | declared in `.par` | no artifact | **`unresolved`** |
| Troposphere correction | `CORRECT_TROPOSPHERE Y` | no model or met data identified | **`unresolved`** |

Selected observation `uwl_220220_104059_b4` · support **MJD 59630.445127 – 59630.489608**
· 10 TOAs · 979.709–2545.197 MHz

## VLBI

| Artifact | Identity | State |
| --- | --- | --- |
| Session R11040 (IVS-R1) | `ftro:concept:ivs/session/R11040` | metadata `resolvable` |
| vgosDB snapshot | — | **`unresolved`** |
| Analysis-centre product | — | **`unresolved`** |
| Downstream IERS EOP series | — | **`unresolved`** |

Support **MJD 59638.708333 – 59639.708333** · DB `XA` · correlator BONN · analysis NASA ·
status Released · `access_class = registered` (CDDIS Earthdata,
[`FTRO-DEF-018`](deficiency-log.md#ftro-def-018))

## GNSS

**57 artifacts pinned** with SHA-256, MD5, size and mirror `Last-Modified`; full detail in
[`phase0/reports/igs-artifact-pins.json`](../phase0/reports/igs-artifact-pins.json).

| Line | Files | Availability for MJD 59630 |
| --- | --- | --- |
| `igs` Final orbit / clock / ERP | 24 | 2022-03-13T11:46:51Z |
| `igr` Rapid orbit / clock / ERP | 33 | 2022-02-21T17:30:12Z |

GPS weeks 2198–2199 · frame **IGb14** · data centre BKG, anonymous HTTP ·
`availability_time_source = mirror_derived`

## Verification activities

| ID | Procedure | Subject | Result |
| --- | --- | --- | --- |
| `VA-GPS2UTC-001` | `VP-GPS2UTC-001` v1.0.0 | `gps2utc.clk` supplies C0′ over MJD 59630–59640 | **`supports`** |

## Applicability assessments

| ID | Question | Outcome |
| --- | --- | --- |
| [`AA-PARKES-C0C0PRIME-001`](../phase0/applicability/AA-PARKES-C0C0PRIME-001.md) | Did the Parkes receiver track C0 or C0′? | **`indeterminate`** |
| [`AA-PPTA-CLKREALISATION-001`](../phase0/applicability/AA-PPTA-CLKREALISATION-001.md) | TT(BIPM2020) or TT(BIPM2021)? | **`indeterminate`**, contestation `open` |
| [`AA-PPTA-TIMINGMODEL-001`](../phase0/applicability/AA-PPTA-TIMINGMODEL-001.md) | Is the `.par` applicable to the `.tim` and the selected epoch? | **`partial`** |
