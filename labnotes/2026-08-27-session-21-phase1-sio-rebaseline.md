# Session 21 — Phase 1 rebased to the qualified SIO carrier

**Date:** 2026-08-27
**Branch:** `phase1-rebaseline`
**Phase-0 carrier:** `8ddcbfacef2468b8988c331c30100d72f0912eb8`
**Integration parent:** `12b119ae5b03cad707a968ed3fdf3e6424966853`
**Gate-1 candidate:** `d0f9e3728e26fff423237b896e9b8ce79feca5bd`
**Status:** **Gate 1 source-location clause passed against the current SIO evidence**
**Licence:** CC BY 4.0

> **Append-only.** This note corrects the current state without editing sessions 13–20 or either
> historical Gate-1 report.

## 00 — Publication and integration

`phase0-closure` was pushed first, making the qualified carrier fetchable. `main` then
fast-forwarded from `a806bba` to qualification publication `264cf1a`. Historical Phase-1 commit
`1c9bc56` was not rebased: `main` was merged into it explicitly at `12b119a`.

The merge had one textual conflict, `labnotes/README.md`. The two sides added disjoint chronological
ranges, sessions 13–16 and 17–20. Resolution was the ordered union; no note body was edited.

## 01 — The old witness failed closed

Running the old checker after integration produced ten failures:

- `identities.json` differed for optical, pulsar and VLBI;
- the GNSS catalog differed from its frozen digest and manifest entity; and
- all five GNSS exemplars still named the BKG retrieval procedure.

That is the expected result. The earlier 69/69 reports remain true for their `a806bba` fingerprints
but cannot witness carrier `8ddcbfa`.

## 02 — Rebaseline choices were made before retrieval

The bounded candidate changes exactly six paths: the checker, its test file and four manifests.
The choices are:

1. `BASELINE_COMMIT` is audited carrier `8ddcbfa`, not publication commit `264cf1a` and not the old
   `a806bba` baseline.
2. All three FTRO catalog URLs use `8ddcbfa`. PPTA and VLBI bytes are unchanged; the IGS catalog is
   the SIO-bound snapshot `d97b05d2…3ad9b7c`.
3. `PHASE1_PARENT_COMMIT` is integration checkpoint `12b119a`; the carrier alone is not the parent
   of the historical Phase-1 manifests.
4. All 57 GNSS provider routes are SIO/GARNER. The five graph exemplars carry the carrier's route,
   availability and retrieval evidence.
5. The two old Gate-1 reports are retained verbatim. A new report is required.

The structural checker passed all four manifests. Phase-1 tests increased 44 → 48 and all passed;
the 185-test source-tree suite also passed. The four new checks bind the carrier/SIO population,
constrain the representation-variant magnitudes, and reject a missing or corrupted assertion.

## 03 — The representation fork is a federation finding

Three clock products have different BKG and SIO `.Z` container digests but equal decoded payload
digests. Therefore a filename plus “the product checksum” is not a complete federated identity:
the checksum depends on whether it names retrieval bytes or decoded state and on which data centre
served the container.

The GNSS manifest now records three provisional decoded-equivalence assertions. Current and
historical outer snapshots remain distinct. No assertion uses `owl:sameAs`; each is scoped to the
decoded payload and records algorithm, decoding implementation, evidence artifact and bitemporal
bounds. The checker derives their expected values from the SIO pin report. This is an exercised
candidate model, not a profile amendment. `FTRO-P1-DEF-010` keeps the normative question open.

The current run rechecked SIO. It did not re-fetch BKG; the BKG side remains the historical evidence
recorded during Phase 0.

## 04 — Same counts, different populations

Gate 1's 69 is 66 provider sources plus three FTRO catalogs. The 66 providers are 3 optical, 5
pulsar, 1 VLBI and 57 GNSS sources. C9's equal headline 66 is 1 optical archive, 4 PPTA artifacts,
1 vgosDB, 3 evidence-repository files and 57 GNSS artifacts. Neither equal count implies equal set.

Even Gate 1's old and new 69 differ: three GNSS container identities and the IGS catalog snapshot
changed. Exact source keys and the ten-input fingerprint—not totals—carry the claim.

## 05 — Clean committed-checkout result

The shared development checkout contains an ignored `data/` directory. A direct source-state probe
there correctly refused to qualify; no user data was removed. A fresh detached clone of candidate
`d0f9e37` had no `data/` directory and ran the live retrieval instead:

```text
Gate 1 structural/source check: PASS (4 manifests)
Gate 1 clean retrieval: 69/69 matched; 0 failed
Gate 1 report freshness/content: PASS
```

The report records 66 provider sources, 3 source catalogs, 69 matched, 0 failed, a verified clean
committed checkout and exactly the six candidate paths since parent `12b119a`. Provider bytes were
streamed to SHA-256 and not retained.

Report: `phase1/reports/gate1-clean-retrieval-sio-d0f9e37.json`

SHA-256: `10890685d8edff405a88a6d310c13dfd9317f74dfe66eaa31f61f10e8d790691`

## 06 — Boundary after Gate 1

Gate 1 source location is current again. It does not demonstrate normative RO-Crate 1.3 or profile
conformance. The next work is the previously deferred hand-authored comparison of relation,
unresolved-state and representation-identity models, followed by a bounded profile amendment—not
generation machinery and not Phase 2.
