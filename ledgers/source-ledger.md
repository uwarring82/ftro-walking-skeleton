# FTRO Source Ledger

**Version:** 0.4.0 · **Opened:** 2026-08-25 · **Revised:** 2026-08-26 · **Licence:** CC BY 4.0

> **v0.2.0** corrects the optical identity to the provider's own concept/version DOIs, restores
> full 64-character digests, and pins the VLBI vgosDB. Digests below are abbreviated head…tail for
> display; canonical values are in [`identities.json`](../phase0/evidence/identities.json).

Every artifact pinned in Phase 0, with its concept identity, snapshot identity, checksum
and evidence state. Machine-readable companion:
[`phase0/evidence/identities.json`](../phase0/evidence/identities.json).

`evidence_state ∈ {resolvable, opaque, unresolved}`

---

## Optical

| Artifact | Snapshot identity | Checksum | State |
| --- | --- | --- | --- |
| ROCIT campaign results.zip | **concept** `doi:10.5281/zenodo.17107692`<br>**version** `doi:10.5281/zenodo.17107693` (provider-immutable) | MD5 `4ae290f559c90b462991286c933a1147` ✅ matches card<br>SHA-256 `6168e24a…bd56bd` | `resolvable` |
| optical-link-data-format | `git:INRIM/optical-link-data-format@689bda77000fec52c401bc0c9c3664d1dd534ecb` | README SHA-256 `cf93ae7a…fcee98` ✅ matches card | `resolvable` |
| tintervals | `git:INRIM/tintervals@2064db12777df78bc87f68f7710a47176192c2e1` · pinned file `pyproject.toml` `sha256:c1054d63…` | commit dated 2026-08-16 ⚠️ **19 months after the data**; this revision cannot be the generating software, and no earlier one is pinned. Before 2026-08-25 this record asserted `resolvable` with **no checksummed file at all** ([`FTRO-DEF-034`](deficiency-log.md#ftro-def-034)) | `resolvable`, **content_validated**, edge `contextualized_by` |
| Local reference oscillator | — | — | **`unresolved`** |
| Station time scale / UTC(k) | — | — | **`unresolved`** |
| Generating scripts | `06-procclocks-v3.py`, `convert-to-rocit.py` | named in headers, **absent from archive** | **`unresolved`** |

Size 83,530,540 B · 12 comparisons · 252 `.dat` · 12 `.yml` · 9,018,290 samples
Actual coverage **MJD 59631.78854 – 59675.00000** (declared 59630–59675)

## Pulsar

| Artifact | Snapshot identity (CSIRO file id · digest) | Size / checksum | State |
| --- | --- | --- | --- |
| PPTA DR3 (concept) | `ftro:concept:ppta/dr3` over DOIs `10.25919/j4xr-wp05` + `10.25919/axvw-qa43` | 90,884 shared paths; 18,414 / 15,509 unique | `resolvable` |
| `J0437-4715.tim` | id 65419499 · `sha256:ee6a2dec…541564` | 4,464,619 B ✅ matches manifest | `resolvable` |
| `J0437-4715.par` | id 65419506 · `sha256:cfbd0db4…8aca75` | 4,402 B ✅ | `resolvable` |
| `pks2gps.clk` | id 65419593 · `sha256:c8131f51…f342fa` | 1,742,710 B ✅ | `resolvable` (own upstream `opaque`) |
| `tai2tt_bipm2021.clk` | id 65419592 · `sha256:047c2a19…a23386` | 48,871 B ✅ | `resolvable`, **contested** |
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
| **vgosDB snapshot** | `ftro:snapshot:ivs/vgosdb/20220228-r11040.tgz@sha256:02119486…f2ba54` · 19,610,760 B · OPAR · **content-validated** | **`resolvable`** |
| Analysis-centre product | — | **`unresolved`** |
| Downstream IERS EOP series | — | **`unresolved`** |

Support **MJD 59638.708333 – 59639.708333** · DB `XA` · correlator BONN · analysis NASA ·
status Released · `access_class = **public**` via OPAR (CDDIS is `registered` —
[`FTRO-DEF-018`](deficiency-log.md#ftro-def-018), [`FTRO-DEF-025`](deficiency-log.md#ftro-def-025))

⚠️ The archive carries **5 internal wrapper versions** (V001–V005; centres MPI, GSFC, IVS), so its
checksum does not pin which version a chain consumed
([`FTRO-DEF-026`](deficiency-log.md#ftro-def-026)). `Last-Modified` 2025-12-15 makes it a
re-release, not a frozen 2022 artifact.

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
| — | `src/ftro/pin_vgosdb.py` content checks | R11040 vgosDB is a gzip/tar vgosDB with versioned wrappers | **`supports`** |
| — | `src/ftro/pin_igs.py` `validate_content` | an Earthdata login interstitial is not data; a `.Z` that will not decompress is not a product | **`supports`** — 34 committed tests, deterministic fixtures, **no network call** ([`FTRO-DEF-031`](deficiency-log.md#ftro-def-031) v2.0.0) |
| — | `src/ftro/unixz.py` | pure-stdlib `.Z` decoder matches system `gzip -dc` byte-for-byte on `igs21980.sp3.Z` | **`supports`** |

## Applicability assessments

| ID | Question | Outcome |
| --- | --- | --- |
| [`AA-PARKES-C0C0PRIME-001`](../phase0/applicability/AA-PARKES-C0C0PRIME-001.md) | Did the Parkes receiver track C0 or C0′? | **`indeterminate`** |
| [`AA-PPTA-CLKREALISATION-001`](../phase0/applicability/AA-PPTA-CLKREALISATION-001.md) | TT(BIPM2020) or TT(BIPM2021)? | **`indeterminate`**, contestation `open` |
| [`AA-PPTA-TIMINGMODEL-001`](../phase0/applicability/AA-PPTA-TIMINGMODEL-001.md) | Is the `.par` applicable to the `.tim` and the selected epoch? | **`partial`** |
