# Phase 1 — Reality-first manifests

**Branch:** `phase1` · **Baseline:** `main` frozen at [`a806bba`](https://github.com/uwarring82/ftro-walking-skeleton/commit/a806bbaa573d28f1460d18110f7974189ca19213)

## Isolation rule

Phase 1 **must not modify** any Phase-0 candidate output before C9 and two qualifying bounded audits
have run. That includes `src/`, `tests/`, `phase0/`, `ledgers/` and `profile/` — the ledger
because its contents feed C11 and C12, and the profile because Gate 1 forbids freezing terms
before the manifests exist.

Everything Phase 1 produces lives under `phase1/`, including its own deficiency ledger, except the
append-only chronological notes under `labnotes/`. When Phase 0 closes, the two ledgers merge.

That exception deliberately leaves the root crate's recorded `labnotes/README.md` size stale on
this branch. Do not refresh the root crate while the isolation rule holds; `main` at `a806bba`
remains internally current, and the Phase-1 metadata is checked by `phase1/check_gate1.py` instead.

| Track | Runs on | Status |
| --- | --- | --- |
| Phase 0 closure | isolated clone of `main` @ `a806bba` | **C9 failed as written**; qualifying audits **0/2**; executable recipes not frozen |
| Phase 1 manifests | `phase1` branch | **Gate 1 source-location clause passed**; normative RO-Crate 1.3 conformance remains `not_run` |

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
or a clean descendant commit containing those six paths plus only non-executable publication
outputs under `phase1/reports/`, `labnotes/`, the Phase-1 README and the Phase-1 ledger. Both require
no `data/` directory; changes under `src/`, `tests/`, `phase0/`, `profile/`, `ledgers/` or arbitrary
additional `phase1/` code are rejected.

```bash
python3 -m unittest discover -s phase1/tests -v
python3 phase1/check_gate1.py
python3 phase1/check_gate1.py \
  --check-report phase1/reports/gate1-clean-retrieval-v1.0.json
# After publication, from a clean checkout; write outside the tree to preserve cleanliness:
python3 phase1/check_gate1.py --retrieve --source-state committed_checkout \
  --out /tmp/gate1-clean-retrieval.json
```

From the parent-overlay witness with no `data/` directory, the retrieval run matched **69/69**
targets: 66 provider artifacts and three FTRO pin reports fetched at the frozen baseline commit.
Those three demonstrate that the catalogs are published and immutable; they are not third-party
provider artifacts. Fifty-seven provider sources are catalog-backed GNSS entries, of which five are
represented as graph entities. No provider bytes were retained. The report binds the six Gate-1
candidate paths plus four frozen Phase-0 evidence inputs, not unrelated modified documentation in
the authoring worktree. See
[`gate1-clean-retrieval-v1.0.json`](reports/gate1-clean-retrieval-v1.0.json).

This is deliberately not a general RO-Crate or FTRO-profile validator. `roc-validator` 0.11.3 is
obtainable but supports bases 1.1 and 1.2, not the normative 1.3 target. The exact validation status
and non-normative 1.2 result are in
[`ro-crate-validation-v1.0.json`](reports/ro-crate-validation-v1.0.json).

## Phase-0 boundary discovered by the live run

The isolated live-provider run demonstrated that the rest of the pipeline works after one manual
intervention, but C9 itself failed: README step 3 unzips into a parent directory no earlier command
creates. Neither historical audit qualifies as pre-registered: the model and first result landed
together, while run 2 added choices after observing run-1 failures. The qualifying count is 0/2;
one executable manifest must be frozen and then run twice. See
[`phase0-c9-attempt-2026-08-26.json`](reports/phase0-c9-attempt-2026-08-26.json).

The profile amendment is therefore deferred. The corrected vocabulary assessment is
[`vocabulary-pressure-v1.1.md`](reports/vocabulary-pressure-v1.1.md); v1.0 remains as the historical
first assessment.

## Deliberate non-goals for this phase

- **No generation machinery.** The manifests are hand-authored. Building a generator before four
  real manifests exist would encode a vocabulary nobody has tested against real products — the
  mistake the profile's own §5.0 warns about.
- **No profile amendment until all four are written and compared.** Vocabulary pressure is
  discovered by writing the manifests, not predicted.
- **No resolution of Phase-0 evidence gaps.** `ref_osc`, the PPTA EOP artifact and the VLBI
  downstream products stay unresolved and are represented as typed incompleteness.
