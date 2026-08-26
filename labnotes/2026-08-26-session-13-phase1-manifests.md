# Session 13 — Phase 1: four hand-authored manifests

**Date:** 2026-08-26 · **Branch:** `phase1` · **Phase-0 baseline:** `main` frozen at [`a806bba`](https://github.com/uwarring82/ftro-walking-skeleton/commit/a806bbaa573d28f1460d18110f7974189ca19213)
**Outcome:** four manifests written; five Phase-1 findings, two of them defects in the profile itself.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 01–12 are left unedited.

---

## 00 — Isolation

Phase 1 runs on a branch. `main` stays at the Phase-0 candidate baseline so C9 and the second
bounded audit run against artifacts this work cannot have touched — including `ledgers/`, whose
contents feed C11 and C12, and `profile/`, which Gate 1 forbids freezing.

Phase 1's own findings go in `phase1/deficiency-log-phase1.json`. The two ledgers merge when
Phase 0 closes.

| Track | Runs on | Status |
| --- | --- | --- |
| Phase 0 closure | `main` @ `a806bba` | C9 outstanding; 1 of 2 clean audits |
| Phase 1 | `phase1` | four manifests written |

---

## 01 — What writing a manifest found that reading a profile did not

**The profile has a normative clause no conforming manifest can satisfy.**

§4 requires **every edge** to carry `valid_from`, `valid_to`, `known_from`, `known_to`. §9.1 pins
RO-Crate 1.3 — JSON-LD. In JSON-LD an edge is a *property*, and **a property cannot carry
attributes**.

So writing the optical manifest forced a reified `ftro:Edge` node with `edge_class`, `subject` and
`object` — a class the profile does not declare. Both affected manifests are therefore
non-conforming against §4 as literally worded.

This is the argument for Gate 1's "nothing is frozen" in one concrete instance. Eleven sessions of
review found no such thing, because it is invisible until you try to serialise a bitemporal edge.

Two smaller cases of the same kind: §9.1 *mandates* a conformance report and declares no node class
for it, and `TIMEEPH IF99` in the PPTA `.par` is neither an ephemeris nor a reference frame, so it
needed an edge the profile has not got.
→ [`FTRO-P1-DEF-002`](../phase1/deficiency-log-phase1.json), `-003`.

---

## 02 — Conformance is asserted and unverified

§9.1 requires the exact validator and version in every conformance report. **No RO-Crate validator
is obtainable here** — `rocrate-validator` is not installable in this environment and the
repository takes no third-party dependencies.

So all four manifests carry `validator: null`, `validation_result: "not_run"`, and the reason
stated in the report itself. On §9.1's own definition — *"RO-Crate-compatible means the crate
validates against the pinned base"* — these manifests are **not yet demonstrated to be RO-Crate
1.3**. Recorded as [`FTRO-P1-DEF-001`](../phase1/deficiency-log-phase1.json) rather than presented
as conformance.

A structural self-check (descriptor `about`, root `conformsTo`, required root properties, no
dangling `hasPart`) passes on all four. That is weaker evidence and is labelled so.

---

## 03 — The comparison

Two thirds of the declared vocabulary has never been used:

| | Declared | Used | Unexercised |
| --- | ---: | ---: | ---: |
| edge classes | 21 | 8 | **13** |
| node classes | 41 | 13 | **28** |

The distinction that matters is *why* a term is unused. `contributes_to` and `uses_tide_model` are
unused because the **provider evidence is unresolved** — those terms are needed. `analysed_with`
and `ContextualSensorSeries` are unused because these four legs have no instance. The profile gives
no way to tell them apart, which is exactly what "nothing is frozen" needs to be actionable.
→ `FTRO-P1-DEF-004`.

**21 fields appear in all four** manifests and are required-field candidates; 86 appear in exactly
one and are correctly domain-specific.

**And the legs are not alike:**

| Domain | Fields | Edges |
| --- | ---: | ---: |
| pulsar | 67 | 5 |
| optical | 64 | 4 |
| vlbi | 53 | 1 |
| gnss | 46 | **0** |

GNSS uses **no ancestry edges at all**. In this pilot it is a *dependency* of other chains, not a
chain. §10 states one minimum record for every dataset; a leg whose role is to be consumed
plausibly needs a different one. → `FTRO-P1-DEF-005`.

---

## 04 — Gate 1

> *no FTRO term is frozen; all four manifests can locate source bytes or report the access failure.*

**Nothing frozen.** The amendment is drafted in
[`vocabulary-pressure-v1.0.md`](../phase1/reports/vocabulary-pressure-v1.0.md) §6 and deliberately
**not applied** — four manifests over four domains in one window is not enough evidence to fix a
vocabulary.

**Bytes located or failure reported**, per leg:

| Leg | Outcome |
| --- | --- |
| optical | located; `time_referenced_to` terminates `unresolved`, comparator has two retained readings |
| pulsar | located; `uses_eop` has **no object** — the release identifies no EOP artifact; TT realisation contested `open` |
| VLBI | vgosDB located from OPAR; `contributes_to` downstream EOP **unresolved**; wrapper member not pinned by the container digest |
| GNSS | located; 57 digests enforced; the reprocessing policy returns an **explained null** |

No gap is repaired, substituted or hidden. Both ends of card §15.1's leading shared-ancestry path
are independently unresolved, and the manifests say so in the graph rather than in prose.

---

## 05 — Method notes to self

- **Write the artifact before fixing the vocabulary.** §4's unsatisfiability survived eleven review
  rounds and fell out of the first serialisation attempt.
- **A mandated record needs a declared class.** §9.1 requires a conformance report the vocabulary
  cannot type.
- **"Unused" is two different findings.** Unused-because-unresolved is a provider gap;
  unused-because-inapplicable is untested vocabulary. Conflating them hides both.
- **Not all legs are chains.** A uniform minimum record assumes a uniform role.

---

## 06 — Next

Phase 1 remaining: retrieval test from a clean environment (§21), then the profile amendment to
v0.0.4 once the comparison is settled.

Phase 0 closure, untouched by this branch: **C9** — the live end-to-end run — and a second bounded
audit against the unchanged checklist.
