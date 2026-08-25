# Federated Time-Reference Observatory — Walking Skeleton

[![Licence: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![Licence: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSES/Apache-2.0.txt)
[![Phase](https://img.shields.io/badge/phase-0%20complete-green.svg)](phase0/selection-note-v0.1.md)

Implementation of task card **FTRO-WS-001 v0.3**.

A small working federation that lets an external researcher discover public
time-referenced measurements and **reconstruct their reference-clock ancestry** across
scientific domains — without transferring custody to a central archive.

The differentiating product is a **machine-readable, bitemporal reference-ancestry graph
with a human-readable browser**. Discovery and staging are necessary infrastructure, not
the scientific contribution.

The observatory should let a user answer:

1. What was measured, where and when?
2. Which oscillator, clock, transfer link, time scale, correction model and software made that timestamp meaningful?
3. Which parts of that chain are supported, inaccessible, unknown or disputed?
4. Can two records legitimately share a time axis, and at what achieved resolution?

---

## Status — Phase 0 complete, Gate 0 passed

Four pilot domains over the candidate window **MJD 59630–59640** (2022-02-20 → 2022-03-02):
optical clocks, pulsar timing, VLBI and GNSS.

### Headline results

**1. The four domains do not overlap.** Computed from actual records and validity masks,
never from campaign boundaries:

| Combination | Result |
| --- | --- |
| GNSS ∩ optical ∩ VLBI | **118.575 h** |
| optical ∩ pulsar | `no_common_support` |
| pulsar ∩ VLBI | `no_common_support` |
| **all four** | **`no_common_support`** |

The single pulsar observation in the window ends at MJD 59630.489608; the earliest
optical sample is MJD 59631.788542 — a **31.17 hour gap**. Optical support was computed
as a deliberate *upper bound*, so the null is a strong one. Per card §6 and §20 the
interval was **not** widened and no substitute dataset was introduced.

**2. Both leading shared-ancestry paths are blocked** — in different domains, for
different reasons:

| Candidate path | Blocked by |
| --- | --- |
| IVS session → IERS EOP → pulsar barycentring | The PPTA timing model declares **no EOP artifact at all**. This confirms the card's §15.1 pre-registered expectation, in the stronger form of `unresolved` rather than `opaque`. |
| optical time tags → station time scale → UTC(k)/BIPM | `ref_osc` is **absent from all 12 comparisons**. The pinned format also states that time transfer is *out of scope*, so the gap is structural. |

`shared_ancestry_demonstration = indeterminate` (provisional).

**3. The optical time tags are quantised at 86.4 ms** while the sampling interval is 1 s —
verified on 1,564,882 of 1,564,882 sampled values, with a 1.0368/0.9504 s dither in ratio
1.347775 against 1.347826 for an exactly-1 s grid. Maximum time-tag error **±43.2 ms**, in
files reporting fractional frequency at the 10⁻¹⁷ level: roughly **eight orders of
magnitude** apart.

**4. 23 classified deficiencies** across all five classes — 2 critical, 8 high.

**5. Platform conformance is separate from scientific demonstration.** The platform
worked: it located, pinned, verified and *typed* every one of these gaps rather than
papering over them. Card §15.2 is explicit that failing to demonstrate shared ancestry is
a valid scientific result, not a platform failure.

---

## Where to start

| If you want | Read |
| --- | --- |
| The narrative — what was tried, in what order, why | **[Lab notes, session 01](labnotes/2026-08-25-session-01-phase0.md)** |
| The formal Phase-0 output with pre-registered targets | [Selection note v0.1](phase0/selection-note-v0.1.md) |
| Everything that is broken, classified | [Deficiency log](ledgers/deficiency-log.md) · [`.json`](ledgers/deficiency-log.json) |
| Why the optical ancestry chain fails | [Optical time-tag ancestry note](phase0/optical-timetag-ancestry-note.md) |
| What is pinned, and to what checksum | [Source ledger](ledgers/source-ledger.md) · [`identities.json`](phase0/evidence/identities.json) |
| Who may reuse what | [Rights ledger](ledgers/rights-ledger.md) |
| Governance and principles | [Access Charter v0.1](charter/access-charter-v0.1.md) |
| The vocabulary (nothing frozen yet) | [Graph profile v0.0.1](profile/ftro-graph-profile-v0.0.1.md) |

---

## Repository layout

```
charter/     Access Charter v0.1                      (deliverable A)
profile/     Reference-Ancestry Graph Profile v0.0.1  (deliverable B, nothing frozen)
phase0/      Selection note, ancestry notes, applicability assessments, reports
ledgers/     Deficiency, rights, source and decision ledgers
labnotes/    Append-only working record
src/ftro/    Retrieval, analysis and verification tooling (Apache-2.0)
Task Cards/  The specification being implemented
data/        Retrieved provider bytes — gitignored, never redistributed
```

## Reproducing Phase 0

Python 3.13, standard library only — no third-party dependencies.

```bash
# 1. Optical: retrieve, verify, analyse
curl -L -o "ROCIT campaign results.zip" \
  "https://zenodo.org/api/records/17107693/files/ROCIT%20campaign%20results.zip/content"
md5 "ROCIT campaign results.zip"     # 4ae290f559c90b462991286c933a1147
unzip -d data/raw/zenodo-17107693/extracted "ROCIT campaign results.zip"
python3 src/ftro/analyse_optical.py \
  --root data/raw/zenodo-17107693/extracted --out data/work/optical-inventory.json
python3 src/ftro/summarise_optical.py \
  data/work/optical-inventory.json phase0/reports/optical-inventory-summary.json

# 2. Verify the pinned GPS→UTC artifact (procedure VP-GPS2UTC-001)
python3 src/ftro/verify_gps2utc.py --file data/raw/evidence/gps2utc.clk \
  --mjd-start 59630 --mjd-end 59640 \
  --expect-sha256 7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a

# 3. Pin the IGS artifacts for the window
python3 src/ftro/pin_igs.py

# 4. Compute the four-domain intersection
python3 src/ftro/four_domain_intersection.py

# 5. Regenerate the deficiency log Markdown from its JSON source of truth
python3 src/ftro/render_deficiencies.py
```

**Known limitation.** `pin_igs.py` validates HTTP status and checksum but *not* content
shape, so it would pin an authentication interstitial as data. This is logged against
ourselves as [`FTRO-DEF-018`](ledgers/deficiency-log.md#ftro-def-018) and is a Phase-1 fix.

---

## Pilot sources

| Domain | Source | Licence | Redistribution |
| --- | --- | --- | --- |
| Optical | [Zenodo 17107693](https://doi.org/10.5281/zenodo.17107693) — ROCIT European fibre subset | CC BY 4.0 | `copy_permitted` |
| Pulsar | PPTA DR3 — [part 1](https://doi.org/10.25919/j4xr-wp05), [part 2](https://doi.org/10.25919/axvw-qa43) | **CC BY-SA 4.0** | `link_only` |
| VLBI | IVS session R11040 (IVS-R1, 2022-02-28) | not established | `link_only` |
| GNSS | IGS Final & Rapid, GPS weeks 2198–2199, frame IGb14 | not established | `link_only` |

**Three of four legs carry rights not established well enough to permit redistribution.**
That is itself a Phase-0 finding about federation readiness in these communities.

This repository never redistributes provider bytes and never relicenses provider content.
See [LICENSE](LICENSE) and the [rights ledger](ledgers/rights-ledger.md).

## Licensing

| Content | Licence |
| --- | --- |
| Software (`src/**`) | [Apache-2.0](LICENSES/Apache-2.0.txt) |
| Metadata, documents, ledgers, lab notes, reports | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| Provider content | Its own licence, unchanged by inclusion |

## Citation

See [`CITATION.cff`](CITATION.cff). Cite the underlying sources by their own DOIs.

## Next — Phase 1

Hand-author four RO-Crate 1.3 manifests declaring conformance to the pinned base and the
FTRO profile. Blocking items are listed in
[lab notes §14](labnotes/2026-08-25-session-01-phase0.md#14--carried-into-phase-1).
