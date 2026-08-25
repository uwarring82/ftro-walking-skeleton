# Federated Time-Reference Observatory — Walking Skeleton

[![Licence: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![Licence: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSES/Apache-2.0.txt)
[![Phase](https://img.shields.io/badge/phase-0%20complete%20%28EOP%20open%29-green.svg)](phase0/selection-note-v0.1.md)

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

**1. The four domains have no common support.** The pulsar leg is the binding constraint: it
overlaps GNSS, but neither optical nor VLBI. The legs are *not* computed on a common basis —
optical is the exact union of contiguous valid sample runs; VLBI uses scheduled session intervals
and GNSS daily product validity, both upper bounds; pulsar uses scan start plus `-tobs`:

| Combination | Result |
| --- | --- |
| GNSS ∩ optical ∩ VLBI | **≤ 82.013 h** (upper bound — VLBI/GNSS legs are envelopes) |
| GNSS ∩ pulsar | 1.067 h — the scan lies wholly inside GNSS product validity |
| optical ∩ pulsar | `no_common_support` |
| pulsar ∩ VLBI | `no_common_support` |
| **all four** | **`no_common_support`** |

Only those two pairs, and every three- and four-domain combination containing the pulsar, are
empty. `GNSS ∩ pulsar` is not.

The single pulsar observation in the window ends at MJD 59630.489608; the earliest optical
sample is MJD 59631.788542 — a **31.17 hour gap**. Because the VLBI and GNSS legs are deliberate
upper bounds, refining them into exact per-observation support can only *remove* overlap: this is
a **robust `no_common_support` under conservative envelopes**. Per card §6 and §20 the interval
was **not** widened and no substitute dataset was introduced.

**2. Both leading shared-ancestry paths are blocked** — in different domains, for
different reasons:

| Candidate path | Blocked by |
| --- | --- |
| IVS session → IERS EOP → pulsar barycentring | The PPTA release identifies **no EOP artifact at all**. The card's §15.1 expectation was an *opaque* artifact; the observed outcome is different and more severe — `unresolved` — so the expectation is **not strictly confirmed**. |
| optical time tags → station time scale → UTC(k)/BIPM | `ref_osc` is **absent from all 12 comparisons**. The pinned format also states that time transfer is *out of scope*, so the gap is **structurally permitted by the format**. |

`shared_ancestry_demonstration = indeterminate` (provisional).

**3. The optical time tags are quantised at 86.4 ms** — every serialised MJD is an exact multiple
of 10⁻⁶ d, on a census of **9,018,290 of 9,018,290** values with **0 exceptions**. The
1.0368/0.9504 s dither, in ratio 1.347775 against the 1.347826 predicted for a one-second grid, is
**strongly consistent with nearest-rounding of a one-second grid**, implying **at most ±43.2 ms
serialisation error under that model**. The archive declares no sampling grid, so the 1 s figure is
an inference. These files report fractional frequency at the 10⁻¹⁷ level; the two figures are not
commensurable — a time quantum against a dimensionless ratio — but ±43.2 ms is the binding limit on
placing these records on any shared time axis.

**4. 27 classified deficiencies** across all five classes — 2 critical, 11 high, 4 resolved.
Three are **self-directed**, against FTRO's own tooling and evidence discipline.

**5. Platform conformance is separate from scientific demonstration.** The platform worked as far
as it was exercised: each gap it encountered was located, typed and — where the bytes were
reachable — pinned and verified. The downstream VLBI analysis product and IERS EOP series were
neither pinned nor verified; those remain `unresolved` rather than closed. Card §15.2 is explicit
that failing to demonstrate shared ancestry is a valid scientific result, not a platform failure.

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

# 3. Pin the IGS artifacts for the window (content-validated)
python3 src/ftro/pin_igs.py

# 4. Pin the R11040 vgosDB from OPAR (content-validated)
python3 src/ftro/pin_vgosdb.py \
  --expect-sha256 0211948678aebfbcfdcf0f8d1ab8777bfd940605668073b8deb99aba1ff2ba54

# 5. Compute the four-domain intersection (needs step 1's full inventory)
python3 src/ftro/four_domain_intersection.py

# 6. Regenerate the derived Markdown from its JSON sources of truth
python3 src/ftro/render_deficiencies.py
python3 src/ftro/render_validity_intervals.py
```

**Reproducibility scope.** Steps 1, 2, 5 and 6 are deterministic: over the same pinned local
inputs they reproduce their committed outputs byte-for-byte. Steps 3 and 4 are network
retrievals that stamp a fresh `retrieved_utc`, so their outputs differ on each run by
construction — the *pinned digests* they record are what must match, and they are asserted in
[`identities.json`](phase0/evidence/identities.json).

**Retrieval validation.** `pin_igs.py` and `pin_vgosdb.py` validate content *shape*, not just
HTTP status and checksum — a status-and-checksum retrieval will happily pin an authentication
interstitial as data, which is how CDDIS returns its Earthdata login page. That weakness was
logged against our own tooling as
[`FTRO-DEF-018`](ledgers/deficiency-log.md#ftro-def-018) and is now closed, with a regression
test against the live CDDIS URL.

---

## Pilot sources

| Domain | Source | Licence | Redistribution |
| --- | --- | --- | --- |
| Optical | [Zenodo 17107693](https://doi.org/10.5281/zenodo.17107693) — ROCIT European fibre subset | CC BY 4.0 | `copy_permitted` |
| Pulsar | PPTA DR3 — [part 1](https://doi.org/10.25919/j4xr-wp05), [part 2](https://doi.org/10.25919/axvw-qa43) | **CC BY-SA 4.0** | `link_only` |
| VLBI | IVS session R11040 (IVS-R1, 2022-02-28) — vgosDB pinned from OPAR | not established | `link_only` |
| GNSS | IGS Final & Rapid, GPS weeks 2198–2199, frame IGb14 | not established | `link_only` |

**Only one of four legs may be redistributed.** Two (IGS, IVS) have rights not established at all;
a third (PPTA) has clearly established rights that are copyleft and therefore incompatible with
CC BY 4.0 FTRO output. That is itself a Phase-0 finding about federation readiness.

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

## Revision history

| Commit | Change |
| --- | --- |
| `fdbf2b9` | Phase 0 as first published |
| this | Corrections after external review — see [session 02 lab notes](labnotes/2026-08-26-session-02-review-corrections.md). The four-domain result is unchanged and now holds at exact run level; nine claims that outran their evidence were corrected, and three self-directed deficiencies were filed. |

## Next — Phase 1

Hand-author four RO-Crate 1.3 manifests declaring conformance to the pinned base and the
FTRO profile. Blocking items are listed in
[lab notes §14](labnotes/2026-08-25-session-01-phase0.md#14--carried-into-phase-1); the VLBI
downstream analysis product and IERS EOP series remain the open leg.
