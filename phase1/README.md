# Phase 1 — Reality-first manifests

**Branch:** `phase1` · **Baseline:** `main` frozen at [`a806bba`](https://github.com/uwarring82/ftro-walking-skeleton/commit/a806bbaa573d28f1460d18110f7974189ca19213)

## Isolation rule

Phase 1 **must not modify** any Phase-0 candidate output before C9 and the second bounded audit
have run. That includes `src/`, `tests/`, `phase0/`, `ledgers/` and `profile/` — the ledger
because its contents feed C11 and C12, and the profile because Gate 1 forbids freezing terms
before the manifests exist.

Everything Phase 1 produces lives under `phase1/`, including its own deficiency ledger. When
Phase 0 closes, the two ledgers merge.

| Track | Runs on | Status |
| --- | --- | --- |
| Phase 0 closure | `main` @ `a806bba` | C9 outstanding; one clean audit of two |
| Phase 1 manifests | `phase1` branch | in progress |

## What Phase 1 is

Card §21: four hand-authored RO-Crate 1.3 manifests, one per domain, declaring conformance to the
pinned base and the FTRO profile, with every field and real-world transition that does not fit
cleanly recorded.

**Gate 1:** no FTRO term is frozen; all four manifests can locate source bytes **or report the
access failure**. Unresolved provider evidence does not block — it is represented.

## Deliberate non-goals for this phase

- **No generation machinery.** The manifests are hand-authored. Building a generator before four
  real manifests exist would encode a vocabulary nobody has tested against real products — the
  mistake the profile's own §5.0 warns about.
- **No profile amendment until all four are written and compared.** Vocabulary pressure is
  discovered by writing the manifests, not predicted.
- **No resolution of Phase-0 evidence gaps.** `ref_osc`, the PPTA EOP artifact and the VLBI
  downstream products stay unresolved and are represented as typed incompleteness.
