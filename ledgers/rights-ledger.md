# FTRO Rights Ledger

**Version:** 0.2.0 · **Opened:** 2026-08-25 · **Revised:** 2026-08-27 · **Licence of this document:** CC BY 4.0

Task card §11.6 requires `data_rights`, `metadata_rights`, `evidence_retention_rights`
and `redistribution_mode` to be tracked **separately**. Unknown or conflicting rights
default to pointer-only registration pending provider-specific review.

`redistribution_mode ∈ {copy_permitted, metadata_only, link_only, restricted, conflicting, unknown}`

---

## FTRO-authored outputs

| Output class | Licence | Basis |
| --- | --- | --- |
| Software (`src/**`) | Apache-2.0 | card §7A |
| Metadata, manifests, graph metadata, certificates, ledgers, lab notes, documentation | CC BY 4.0 | card §7A |

**Federation does not imply a right to redistribute source bytes or provider metadata.**
Retrieved provider bytes live under `data/raw/` and are excluded from version control.

---

## Provider sources

### Optical — Zenodo 17107693

| Field | Value |
| --- | --- |
| `data_rights` | **CC BY 4.0** |
| `metadata_rights` | **CC BY 4.0** (Zenodo record metadata) |
| `evidence_retention_rights` | Permitted — CC BY 4.0 allows retention and redistribution with attribution |
| `redistribution_mode` | `copy_permitted` |
| Evidence | `metadata.license.id = "cc-by-4.0"` in the Zenodo REST record, retrieved 2026-08-25 |

**Caveat.** The licence is declared only in the Zenodo *record metadata*. The archive
bytes contain no licence file, so a consumer who obtains the ZIP without the record
metadata has no in-band rights statement.

### Pulsar — PPTA DR3 (both DOIs)

| Field | Value |
| --- | --- |
| `data_rights` | **CC BY-SA 4.0** |
| `metadata_rights` | **CC BY-SA 4.0**, alongside the statement "All Rights (including copyright) CSIRO 2023." |
| `evidence_retention_rights` | Retention permitted; **redistribution triggers ShareAlike** |
| `redistribution_mode` | **`link_only`** |
| Evidence | `licence` field of DAP collections `csiro:59374` and `csiro:59381`, retrieved 2026-08-25 |

**Conflict — [`FTRO-DEF-014`](deficiency-log.md#ftro-def-014).** CC BY-SA 4.0 is
copyleft. Incorporating PPTA descriptive content into an FTRO output would force that
output to ShareAlike, contradicting card §7A. FTRO therefore records **facts and
pointers only** — identifiers, paths, sizes, checksums, epochs, declared parameter
values — which are not subject to copyright in the relevant sense, and quotes provider
prose only briefly with attribution.

Note also the tension between an open CC BY-SA grant and a blanket "All Rights
(including copyright) CSIRO 2023" reservation appearing on the same record.

### GNSS — IGS operational products

| Field | Value |
| --- | --- |
| `data_rights` | **Not established.** No machine-readable licence accompanies the pinned artifacts |
| `metadata_rights` | Not established |
| `evidence_retention_rights` | Assumed permitted for verification; not evidenced |
| `redistribution_mode` | **`link_only`** (default for unknown rights, per card §11.6) |
| Evidence | No licence file or machine-readable licence is exposed with the pinned products in the SIO/SOPAC GARNER listings for GPS weeks 2198–2199 |

IGS products are conventionally understood to be freely available, but *convention is
not evidence*. Recorded as `unknown` pending a provider-specific statement.

### VLBI — IVS session R11040 products

| Field | Value |
| --- | --- |
| `data_rights` | **Not established** |
| `metadata_rights` | **Not established** |
| Metadata access | Session listing is publicly readable at <https://ivscc.gsfc.nasa.gov/sessions/2022/>; readability is not a reuse grant |
| `evidence_retention_rights` | Not established |
| `redistribution_mode` | **`link_only`** |
| Access class | Route-specific: **`public`** at OPAR; **`registered`** at CDDIS; BKG not established |

OPAR serves the pinned vgosDB anonymously. See
[`FTRO-DEF-018`](deficiency-log.md#ftro-def-018): the separate CDDIS route returns the login page
with HTTP 200 rather than 401/403, so an automated agent cannot detect that route's wall from the
status code alone.

### Evidence artifacts

| Artifact | `data_rights` | `redistribution_mode` |
| --- | --- | --- |
| `INRIM/optical-link-data-format` @ `689bda77` | Repository licence not examined in Phase 0 | `link_only` |
| `INRIM/tintervals` @ `2064db12` | Repository licence not examined in Phase 0 | `link_only` |
| `ipta/pulsar-clock-corrections` @ `36dc139a` | Repository licence not examined in Phase 0 | `link_only` |

Recorded as an open Phase-1 action: examine and record the licence of each evidence
repository before any manifest declares redistribution rights over its contents.

---

## Summary

| Source | data_rights | redistribution_mode | Compatible with CC BY 4.0 FTRO output? |
| --- | --- | --- | --- |
| Zenodo 17107693 | CC BY 4.0 | `copy_permitted` | Yes |
| PPTA DR3 | CC BY-SA 4.0 | `link_only` | **No — copyleft** |
| IGS products | unknown | `link_only` | Undetermined |
| IVS / CDDIS | unknown | `link_only` | Undetermined |

Three of four pilot legs carry rights that are **not** established well enough to
permit redistribution. This is itself a Phase-0 finding about the state of federation
readiness in these communities.
