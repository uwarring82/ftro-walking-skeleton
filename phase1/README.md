# Phase 1 — Reality-first manifests

**Branch:** `phase1` · **Qualified Phase-0 evidence carrier:** [`8ddcbfa`](https://github.com/uwarring82/ftro-walking-skeleton/commit/8ddcbfacef2468b8988c331c30100d72f0912eb8)

## Integration boundary

Phase 0 is closed for immutable carrier `8ddcbfa`; its qualification evidence is published by
`264cf1a`. The historical Phase-1 work was merged with that baseline at `12b119a`, then Gate 1 was
rebaselined in a separate six-file candidate `d0f9e37`. Neither merge nor rebaseline rewrites the
qualified Phase-0 subject or the two historical Gate-1 witnesses.

The current Gate-1 source witness is defined by the integration parent, the exact six candidate
files and a fingerprint of four carrier evidence inputs. Publication-only changes may follow under
`phase1/reports/`, `labnotes/`, the Phase-1 README and ledger, and the root RO-Crate metadata. The
checker still rejects executable or scientific-input drift outside that bounded set.

**Ledger reconciliation is complete through snapshot
[`phase1-deficiency-log-at-7585135.json`](../ledgers/phase1-deficiency-log-at-7585135.json).**
[`ledgers/deficiency-log.json`](../ledgers/deficiency-log.json) v0.23.0 is canonical and now
carries all fifteen Phase-1 entries — 91 entries, 62 resolved, 29 open, 66 self-directed,
convergence predicate **0**. It no longer reports an open audit blocker for a phase published as
closed.

The unified ledger retains **all four** reconciliation sources under `merged_sources`: the
immutable nine-entry snapshot at `1c9bc56`, merged before qualification; then eleven at `f1837d4`,
thirteen at `6e03702`, and fifteen at `7585135`. Earlier snapshots are never rewritten.

`phase1/deficiency-log-phase1.json` continues as the Phase-1 working supplement under the standing
rule stated in its own `note`: new entries open here, each reconciliation snapshots the committed
state and folds it in, and a body that diverges under an unchanged version label is itself a
defect — as `FTRO-P1-DEF-008` was, at v2.0.0 in two files with different bodies.

At this checkpoint the supplement is v0.7.0 with thirteen entries: `FTRO-P1-DEF-011` is corrected
at v2.0.0 and new resolved entries `-012` and `-013` record the crate-discovery and Gate-1
instruction defects. That exact committed supplement is snapshotted and folded into the canonical
ledger; future Phase-1 entries begin the next supplement interval under the same standing rule.

This is descendant bookkeeping. The qualified carrier `8ddcbfa` is not rebound, no Phase-0
requalification is required, and Gate 1 remains bound to candidate `d0f9e37`.

| Track | Runs on | Status |
| --- | --- | --- |
| Phase 0 closure | carrier `8ddcbfa` | **complete**: C9 pass, calibration pass, qualifying audits **2/2** |
| Phase 1 manifests | candidate `d0f9e37` | **Gate 1 source-location clause passed against SIO**; normative RO-Crate 1.3 conformance remains `not_run` |

## What Phase 1 is

Card §21: four hand-authored RO-Crate 1.3 manifests, one per domain, declaring conformance to the
pinned base and the FTRO profile, with every field and real-world transition that does not fit
cleanly recorded.

**Gate 1:** no FTRO term is frozen; all four manifests can locate source bytes **or report the
access failure**. Unresolved provider evidence does not block — it is represented.

## Gate-1 evidence

The bounded checker consumes one captured snapshot of the four manifests and the frozen Phase-0
evidence. It compares the **exact** source identity set, not only counts; reconciles the selected
PPTA, GNSS and VLBI projections; and fingerprints every input used by retrieval. A clean run also
proves its source state before making a request. Two witnesses are accepted for the same candidate
identity `(Phase-1 parent, ten-input fingerprint)`: the exact six input files overlaid on the parent,
or a clean descendant commit containing those six paths plus only the explicit non-executable
publication outputs named above. Both require no `data/` directory; changes under `src/`, `tests/`,
`phase0/`, `profile/`, `ledgers/` or arbitrary additional `phase1/` code are rejected.

```bash
python3 -m unittest discover -s phase1/tests -v
python3 phase1/check_gate1.py
python3 phase1/check_gate1.py \
  --check-report phase1/reports/gate1-clean-retrieval-sio-d0f9e37.json
# Live reproduction must use the exact candidate, not the publication descendant at branch HEAD:
git switch --detach d0f9e3728e26fff423237b896e9b8ce79feca5bd
# Run from that clean, data-free checkout; write outside the tree to preserve cleanliness:
python3 phase1/check_gate1.py --retrieve --source-state committed_checkout \
  --out /tmp/gate1-clean-retrieval.json
```

The current clean committed-checkout run matched **69/69** targets: 66 provider artifacts and three
FTRO pin reports fetched at qualified carrier `8ddcbfa`. Those catalogs are FTRO publication
evidence, not third-party provider artifacts. Fifty-seven provider sources are catalog-backed GNSS
entries at SIO/GARNER, of which five are graph exemplars. The report records candidate `d0f9e37`,
the exact six changed paths and four frozen carrier inputs; no provider bytes were retained. See the
[`SIO rebaseline report`](reports/gate1-clean-retrieval-sio-d0f9e37.json).

The two earlier 69/69 reports remain truthful historical witnesses for the BKG-bound `a806bba`
fingerprint: [`committed checkout`](reports/gate1-clean-retrieval-committed-d31a70c.json) and
[`parent overlay`](reports/gate1-clean-retrieval-v1.0.json). They do not transfer to the SIO
population: three GNSS `.Z` containers have new outer digests and snapshot identifiers even though
their decoded payloads are equal. Equal counts and filenames do not establish population identity.

Do not confuse Gate 1's 66 provider sources with C9's equal headline count. Gate 1 uses 3 optical,
5 pulsar, 1 VLBI and 57 GNSS provider sources. C9 uses 1 optical archive, 4 PPTA artifacts, 1
vgosDB, 3 evidence-repository files and 57 GNSS artifacts. The totals coincide; the populations do
not.

This is deliberately not a general RO-Crate or FTRO-profile validator. `roc-validator` 0.11.3 is
obtainable but supports bases 1.1 and 1.2, not the normative 1.3 target. The exact validation status
and non-normative 1.2 result are in
[`ro-crate-validation-v1.0.json`](reports/ro-crate-validation-v1.0.json).

## Phase-0 boundary discovered and closed

The first Phase-1 boundary run correctly remains a failure: README step 3 lacked its parent
directory, and neither historical audit was pre-registered. Carrier `8ddcbfa` later executed the
repaired eight-step pipeline against live providers, then one calibration and two qualifying runs
of the frozen manifest passed. The historical failure is retained in
[`phase0-c9-attempt-2026-08-26.json`](reports/phase0-c9-attempt-2026-08-26.json); the closure verdict
is [`phase0/phase0-qualification-v1.0.md`](../phase0/phase0-qualification-v1.0.md).

The profile amendment remains deferred for a different reason: the representation-level identity
fork and the RDF assertion model must be exercised before §5 is changed, and normative RO-Crate
1.3 validation remains unavailable. Current guidance is
[`vocabulary-pressure-v1.2.md`](reports/vocabulary-pressure-v1.2.md); v1.0 and v1.1 remain historical.

## Deliberate non-goals for this phase

- **No generation machinery.** The manifests are hand-authored. Building a generator before four
  real manifests exist would encode a vocabulary nobody has tested against real products — the
  mistake the profile's own §5.0 warns about.
- **No profile amendment from one representation fork.** The four manifests and SIO rebaseline
  expose the pressure; at least one alternative mapping and another packaged product must test it
  before §5 is frozen.
- **No resolution of Phase-0 evidence gaps.** `ref_osc`, the PPTA EOP artifact and the VLBI
  downstream products stay unresolved and are represented as typed incompleteness.
