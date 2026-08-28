# Federated Time-Reference Observatory — Walking Skeleton

[![Licence: CC BY 4.0](https://img.shields.io/badge/docs-CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![Licence: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSES/Apache-2.0.txt)
[![Phase](https://img.shields.io/badge/Phase%200-closed%3B%20Phase%201%20in%20progress-brightgreen.svg)](phase0/phase0-qualification-v1.0.md)

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

## Status — Phase 0 closed; Phase 1 in progress

**Phase 0 is procedurally closed** for the immutable carrier `8ddcbfa`. Its qualification evidence
was committed separately as the descendant `264cf1a`, so the carrier was never rebound to the
evidence attesting to it. All five conditions of the
[acceptance contract](phase0/acceptance-contract-v1.0.md) hold; the full record is the
[qualification status](phase0/phase0-qualification-v1.0.md).

| Condition | Evidence |
| --- | --- |
| 1. Network-free contracts from a literal clean archive | 185 tests; root crate 0 stale / 0 missing |
| 2. C9 against live providers | README steps 0–7; 66/66 provider attempts; **0** interventions; **0** route substitutions |
| 3. Convergence predicate | 85 ledger entries at carrier `8ddcbfa`; open ∧ `changes_result` ∧ `current_defect` = **0** |
| 4. Frozen manifest behaves as registered | 25/25 cases; 21 detected, 4 registered non-detections, 0 `not_executed`, 25 verified resets |
| 5. Two bounded audits | **2/2** — byte-distinct reports from separate clean checkouts |

Closure cost two rejected carriers, and neither failure was repaired quietly. The first live C9
attempt reached step 4 and failed when the BKG IGS route refused all 57 connections. And the two
2026-08-26 mutation exercises turned out to be *retrospective* rather than pre-registered — the
first fault model was committed together with its own result, and the second added cases after
observing the first — so the qualifying count restarted at **0/2** and both runs were retained as
diagnostics rather than counted. The historical claims to the contrary are retracted by name in the
contract.

**Phase 1** continues on the [`phase1`](https://github.com/uwarring82/ftro-walking-skeleton/tree/phase1)
branch, rebaselined onto the qualified carrier. Four hand-authored RO-Crate 1.3 manifests exist,
and Gate 1's source-location clause **passes for the Gate-1 candidate `d0f9e37`**, from a clean
committed checkout of that commit: 69/69 artifacts located and digest-matched — 66 provider
sources plus 3 catalogs, 140,740,511 bytes, 0 failures. The result is bound to `d0f9e37`, not to
the branch head: the commit that *publishes* the evidence is a descendant record about the
candidate, never itself the Gate-1 subject — the same rule the Phase-0 carrier follows.

Normative RO-Crate 1.3 conformance remains explicitly **`not_run`**: the obtainable validator stops
at 1.2, so these manifests are not yet *demonstrated* to be RO-Crate 1.3. Phase 2 is held.

### One provider finding, not yet in the results below

Three of the 57 IGS products serve **different container bytes** at SIO/GARNER than at BKG while
decoding to byte-identical content (`igs21982.clk.Z`, `igs21983.clk.Z`, `igr21991.clk.Z`). A
snapshot digest for those artifacts is therefore not well defined without naming the data centre —
snapshot identity forks where concept identity holds. The pins retain both digests and the basis
for the change; the modelling question is open as `FTRO-P1-DEF-010`.

Four pilot domains over the candidate window **MJD 59630–59640** (2022-02-20 → 2022-03-02):
optical clocks, pulsar timing, VLBI and GNSS.

### Headline results

**1. The four domains have no common support.** The pulsar leg is the binding constraint: it
overlaps GNSS, but neither optical nor VLBI. The legs are *not* computed on a common basis —
optical is the union of *recorded timestamp spans* of contiguous valid runs under a 1.5 s
contiguity rule — exact over recorded tags, not over physical support; VLBI uses scheduled session
intervals and GNSS daily product validity, both upper bounds; pulsar uses scan start plus `-tobs`:

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
**strongly consistent with nearest-rounding of a one-second grid**, implying a **per-tag rounding
bound of ±43.2 ms under that model**.

That bound is neither universal nor irreducible: the grid is undeclared, the absent `interval`,
`lag` and `weighting` leave a tag's placement within its own integration unconstrained over up to
**1 s** — a larger term — and reconstructing epochs by sample index could recover much of the
quantisation loss. These files report fractional frequency at the 10⁻¹⁷ level, which is not
commensurable with a time quantum.

**4. 85 classified deficiencies**, 56 resolved, 60 self-directed after reconciling the nine-entry
Phase-1 source ledger and rejecting two closure carriers: one at its clean-archive gate and one
after its first live-provider failure report proved to misname the last rejection as the first.
Each carries a `finding_type`
and an `affects` axis, because an append-only count cannot show convergence. The exact measure is:
**entries simultaneously open, `affects == changes_result` and
`finding_type == current_defect` — zero after the merge.** **Sixty are self-directed** —
against FTRO's own tooling,
evidence discipline, test suite and profile conformance. Every entry carries a machine-readable
`responsible_party`. Three (`FTRO-DEF-031`, `-033`, `-035`) have been **reopened repeatedly** as
successive fixes proved partial.

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
| **Scope, contracts and exit condition** | [Phase-0 acceptance contract](phase0/acceptance-contract-v1.0.md) |
| Governance and principles | [Access Charter v0.1](charter/access-charter-v0.1.md) |
| The vocabulary (nothing frozen yet) | [Graph profile v0.0.3](profile/ftro-graph-profile-v0.0.3.md) |

---

## Repository layout

```
charter/     Access Charter v0.1                      (deliverable A)
profile/     Reference-Ancestry Graph Profile v0.0.3  (deliverable B, nothing frozen)
tests/       Regression suite: retrieval validation, fail-closed digests, profile conformance
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
# 0. Regression suite (no network; deterministic fixtures)
python3 -m unittest discover -s tests -v

# 1. Pin the git-hosted evidence artifacts (writes data/raw/evidence/)
python3 src/ftro/pin_evidence_repos.py

# 2. Verify the pinned GPS->UTC artifact (procedure VP-GPS2UTC-001)
python3 src/ftro/verify_gps2utc.py \
  --file data/raw/evidence/pulsar-clock-corrections--gps2utc.clk \
  --mjd-start 59630 --mjd-end 59640 \
  --expect-sha256 7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a

# 3. Optical: retrieve, verify, analyse
curl --fail --show-error --location \
  --output "ROCIT campaign results.zip" \
  --write-out 'FTRO_CURL_HTTP %{http_code} %{url_effective} %{content_type} %{size_download}\n' \
  "https://zenodo.org/api/records/17107693/files/ROCIT%20campaign%20results.zip/content"
md5 "ROCIT campaign results.zip"     # 4ae290f559c90b462991286c933a1147
mkdir -p data/raw/zenodo-17107693
unzip -d data/raw/zenodo-17107693/extracted "ROCIT campaign results.zip"
python3 src/ftro/analyse_optical.py \
  --root data/raw/zenodo-17107693/extracted --out data/work/optical-inventory.json
python3 src/ftro/summarise_optical.py \
  data/work/optical-inventory.json phase0/reports/optical-inventory-summary.json

# 4. Pin the remaining legs. Each PREFLIGHTS the committed digest registry before
#    fetching, and promotes its report only on complete success.
python3 src/ftro/pin_igs.py \
  --expect-sha256-manifest phase0/evidence/expected-digests.json --expect-section igs
python3 src/ftro/pin_vgosdb.py
python3 src/ftro/pin_ppta.py

# 5. Compute the four-domain intersection (refuses a non-clean IGS report)
python3 src/ftro/four_domain_intersection.py

# 6. Regenerate derived Markdown from its JSON sources of truth
python3 src/ftro/render_deficiencies.py
python3 src/ftro/render_validity_intervals.py

# 7. Conformance gates
python3 src/ftro/check_versions.py --check   # changed artifacts declare a new version
python3 src/ftro/refresh_crate.py --check    # RO-Crate sizes match disk
```

**Reproducibility scope.** Step **2**, the tracked optical inventory summary produced within
step **3**, and steps **5 and 6** are byte-deterministic: over the same pinned local inputs they
reproduce their committed outputs byte-for-byte.

The pin reports produced by retrieval steps **1 and 4** stamp a fresh `retrieved_utc` and so
cannot reproduce their committed bytes by construction. The optical archive retrieved in step 3
is digest-pinned, while its derived inventory and summary contain no retrieval timestamp and are
deterministic. Every retrieved artifact must match the *pinned digest*, asserted against
[`expected-digests.json`](phase0/evidence/expected-digests.json). An earlier version of this
paragraph listed step 1 as deterministic, which was false
([`FTRO-DEF-068`](ledgers/deficiency-log.md#ftro-def-068)).

**Step 2** is byte-deterministic and its committed record now names the path step 1 writes, so the
documented command reproduces [`VA-GPS2UTC-001.json`](phase0/evidence/VA-GPS2UTC-001.json) exactly.
It previously recorded a different path, so the documented command produced the same verdict under
a different `artifact` field.

**Retrieval validation.** `pin_igs.py`, `pin_vgosdb.py` and `pin_ppta.py` validate content
*shape*, not just HTTP status and checksum — a status-and-checksum retrieval will happily pin an
authentication interstitial as data, which is how CDDIS returns its Earthdata login page. For a
`.Z` product that means actually decompressing it (via `src/ftro/unixz.py`, a pure-stdlib
Unix-compress decoder verified byte-identical to system `gzip` on a real 253 KB IGS artifact) and
checking the inner format. All three tools fail closed on a digest mismatch: non-zero exit, no
identity minted, no bytes cached. Logged against our own tooling as
[`FTRO-DEF-018`](ledgers/deficiency-log.md#ftro-def-018).

The default IGS route is the official SIO/SOPAC GARNER mirror over anonymous HTTPS. It reproduces
54 of the earlier BKG retrieval containers exactly; three `.Z` containers differ while all 57
decoded products are byte-identical. Those three are explicit new retrieval snapshots, with the
earlier outer digest and common decoded digest retained in the registry
([`FTRO-DEF-075`](ledgers/deficiency-log.md#ftro-def-075)).

The regression tests use committed deterministic fixtures and perform **no network call**; an
earlier README described a live-CDDIS test that did not exist as committed code
([`FTRO-DEF-031`](ledgers/deficiency-log.md#ftro-def-031)).

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
| Software (`src/**`, `tests/**`) | [Apache-2.0](LICENSES/Apache-2.0.txt) |
| Metadata, documents, ledgers, lab notes, reports | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |
| Provider content | Its own licence, unchanged by inclusion |

## Citation

See [`CITATION.cff`](CITATION.cff). Cite the underlying sources by their own DOIs.

## Revision history

| Commit | Change |
| --- | --- |
| `fdbf2b9` | Phase 0 as first published |
| `2c31279` | First external review — see [session 02](labnotes/2026-08-25-session-02-review-corrections.md). Nine claims corrected; optical support recomputed at run level; three self-directed deficiencies filed. |
| `0b41929` | Second external review — see [session 03](labnotes/2026-08-25-session-03-review-corrections-2.md). Conformance rule violated by its own commit (`FTRO-DEF-029`); tools fail closed; profile §5.2 retracted. |
| `1b77a72` | Third external review — see [session 04](labnotes/2026-08-25-session-04-review-corrections-3.md). The sensitivity scan could not perform the reanalysis it reported (`FTRO-DEF-030`) and is reimplemented by re-segmentation; the test suite skipped its own fail-closed coverage on a clean clone (`FTRO-DEF-031`); the §9.2 conformance contradiction is resolved by validating rather than downgrading (`FTRO-DEF-032`); profile bumped because a drifting version label identifies no constraint state (`FTRO-DEF-033`). |
| `11ea11c` | Fourth external review — see [session 05](labnotes/2026-08-25-session-05-review-corrections-4.md). **Projection-only verification** named and fixed: the §9.2 check exempted every record that omitted the field (`FTRO-DEF-034`), and `pin_ppta.py` emitted four identities that differed from the manifest it was built to support (`FTRO-DEF-035`). Generators now declare canonical identities and are reconciled by test; the suite runs with zero skips on a clean export; expected digests are committed. |
| `99fe720` | Fifth external review — see [session 06](labnotes/2026-08-26-session-06-review-corrections-5.md). The digest registry was committed but **not connected** (57/57 IGS pins had `expected_sha256: null`), and the reconciliation test could not detect drift. Now **39 tests**, all 65 digests enforced, and the reconciliation verified by injected mutation. Spacing analysis moved to exact integer ticks: `1.987199 s` was a float artefact (`FTRO-DEF-036`). |
| `615afe2` | Sixth external review — see [session 07](labnotes/2026-08-26-session-07-review-corrections-6.md). Retrieval now **preflights** the digest registry before fetching and **promotes reports only on complete success**; consumers refuse a non-clean report; the version gate checks content digests rather than a hard-coded mirror of the version string; segmentation moved to integer ticks. The manual mutation table is now **12 committed tests**. |
| `4a5b80a` | Seventh external review — see [session 08](labnotes/2026-08-26-session-08-review-corrections-7.md). A contract change updated one caller of two, and the sensitivity scan **published a wrong number past every gate** (`FTRO-DEF-037`); the consumer gate and its tests both accepted an absent field as success (`FTRO-DEF-038`); `--update` could silence the version gate (`FTRO-DEF-039`). |
| `5f0244f` | Eighth external review — see [session 09](labnotes/2026-08-26-session-09-review-corrections-8.md). The tests guarding the sensitivity computation **only read its output**, so restoring the broken revision left all 70 green (`FTRO-DEF-046`). There is now an executing oracle over a synthetic fixture, with both segmentation paths asserted equal run-for-run. Preflight validated presence not shape (`FTRO-DEF-042`); `isinstance(False, int)` let JSON `false` pass as zero (`FTRO-DEF-043`). **86 tests**, zero skips. |
| `aaeae6f` | Ninth external review — see [session 10](labnotes/2026-08-26-session-10-review-corrections-9.md). The oracle constrained **topology, not extent**: halving every run's span changed optical support by 40% and passed all 86 tests (`FTRO-DEF-048`). It now uses a segmenter written independently of `src/`, and a manifest of full run tuples. **94 tests**, zero skips. |
| `3e6face` | Tenth external review — see [session 11](labnotes/2026-08-26-session-11-review-corrections-10.md). The oracle fixture contained **no gap at a live tolerance boundary**, so `int`→`round` passed all 94 tests while changing the 5 s row by 1,883 runs (`FTRO-DEF-053`). The runtime gate read the report's own account of itself (`FTRO-DEF-054`). **99 tests**, zero skips. |
| `a806bba` | **Consolidation.** Ten review rounds had a flat discovery rate because the acceptance scope was unbounded and every gate added unverified surface. This round *shrinks* the codebase: one declarative schema retires the 8-entry absent-field family; `series`/`mjd` are derived from authenticated names; domain supports are built once; the 275-line version state machine is replaced by git (101 lines). Phase 0 now has a [frozen contract](phase0/acceptance-contract-v1.0.md), a finite semantic fault model, and a finite exit condition. The two 2026-08-26 exercises were later shown to be retrospective; neither is a qualifying pre-registered audit. |
| `264cf1a` | **Phase 0 closed** — see [session 20](labnotes/2026-08-27-session-20-phase0-qualified.md). C9 executed end to end against live providers (66/66, zero interventions); the frozen mutation manifest run once as non-qualifying calibration, then twice from separate clean checkouts (2/2). Carrier `8ddcbfa`; evidence committed separately so the carrier was never rebound. The first carrier was rejected when BKG refused all 57 IGS connections ([session 19](labnotes/2026-08-27-session-19-first-live-c9-rejected.md)). |
| `96ba9cb` | **Phase 1 rebaselined** — see [session 21](labnotes/2026-08-27-session-21-phase1-sio-rebaseline.md). Gate 1 re-run against the qualified SIO carrier from a clean committed checkout: 69/69, 140,740,511 bytes. Three IGS products differ in container bytes between data centres while decoding identically (`FTRO-P1-DEF-010`). |

## Next — Phase 1

Phase 0 is closed and its isolation boundary is lifted; work continues on the `phase1` branch.
Next, in order: compare alternative encoded/decoded assertion models against a second packaged
provider product; then establish RO-Crate 1.3 validation; and only then amend profile §5. Phase 2
remains held until the profile is amended from the four real manifests.

The VLBI downstream analysis product, the IERS EOP series, the four depositor question groups and
the IPTA upstream report remain **external evidence gaps** — scientific evidence work, not closure
defects, and typed as such in the ledger rather than repaired.
