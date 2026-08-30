# Session 26 — WP2A v1.1 rejected; v1.2 separates generated facts from registered judgement

**Date:** 2026-08-30 · **Branch:** `phase2`
**Outcome:** second registration rejected before step 2. Still nothing executed.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 24–25 unedited; both registrations retained byte-unchanged.

---

## 00 — The defect under the other seven

v1.1's contract said expected facts were *"derived from these four sources by a committed
generator, not hand-transcribed."* **No generator existed.** I wrote the facts inline in a shell
heredoc and described the result as generated.

The second half is worse than the first. Even with a generator, those four sources **cannot**
produce what v1.1 attributed to them. No pin report states a predicate. No inventory states an
evidence state. Nothing in `identities.json` says which line of production code reads which byte
layer, or what a temporal bound means. Those are judgements. Presenting them as source derivation
is [[projection-only-verification]] one level up: the *provenance* of the facts was fabricated,
not the facts themselves.

v1.2 splits them. `build_source_facts.py` emits only values copied verbatim from a digest-pinned
source, has `--check`, and is tested. `interpretations-v1.2.json` holds every judgement with a
`basis` of `profile_term`, `code_reading` or `registered_convention`.

While authoring it, the generator refused a digest tail I had typed by hand for the inventory
source. That is the behaviour worth having.

## 01 — Three corrections that are scientific, not editorial

**`opaque`, not `unresolved`.** Profile v0.0.3:212 reserves `unresolved` for *no specific evidence
artifact has been identified*. BKG's containers are identified **exactly** — name, digest, size,
route, retrieval time, all at `a806bba`. Identified-but-inaccessible is `opaque`. And the
*historical report about* the BKG container is itself `resolvable`, which is a third thing again.
v1.1 collapsed all of it and froze the false contrast into Q8 — the discriminating query.

**The optical support key is not the filename.** v1.1 answered Q5b as "the member-path date
component". `analyse_optical.py` uses the filename only to select `*.dat` and to label a row; it
never parses the date. Every temporal fact comes from the MJD token in the row content, retained as
a decimal string so tick quantisation avoids a float round-trip. I had read that code twice this
week and still wrote the wrong thing into a frozen registration.

**Q9 could not be failed in one direction.** M2 forbids an output entity by construction. v1.1's Q9
required the output state to *be* an RDF subject or object. So `assertion_only_supported` was
unreachable **by definition** — the trial could not return one of its own outcomes. v1.2 asks for
an identifier *denoting* the output byte-state, which M2 may mint on the assertion node.

## 02 — Freezing counts is not freezing targets

v1.1 froze 76 cases and called target selection exhaustive. It froze **counts**. `R8` said "one
case per output" while the oracle held six Family-A assertions each with four temporal bounds and
an evidence state — so the recipe author, writing *after* seeing the fixtures, still chose which.

v1.2 enumerates **134 cases**, each naming its exact `target_id` and `target_field`. `R8` alone is
70. `R11` cannot be enumerated yet (entity counts need fixtures), so the rule is frozen instead:
one case per entity, with the recipe checker asserting that count equals the fixture's declared
count — F-REQ-5 exists to make that checkable.

Twice now the fix for post-hoc selection has itself been post-hoc-able one level down.

## 03 — Publication defects the widened discovery exposed

`FTRO-P1-DEF-014` extended crate discovery to the phase trees and shipped with **no test**
(`-019`). It also declared every discovered file as CC BY Markdown — fine for `labnotes/`, wrong
for trees holding `.py` (`-017`). Latent only because the two existing Python files had been
declared by hand; the next auto-declared one would have been published as a CC BY Markdown
document. And the root crate advertised `dateModified: 2026-08-28` across commits that changed its
content (`-018`).

Fixed with a per-suffix declaration table that **raises** on an unknown suffix rather than
defaulting, `dateModified` advanced on write, and ten tests over depth, suffixes, exclusions,
declaration rules and undeclared-file count. Verified by `build_source_facts.py` being
auto-declared as Apache-2.0 `SoftwareSourceCode`.

## 04 — Step 2 is authentication, not prediction

v1.1 called the member digest a prospective prediction. It is not: the value was supplied from a
prior diagnostic before registration. Confirming it reproduces and authenticates a known
observation — real evidential weight, but not the weight of a successful blind prediction. v1.2
says so, and registers all 256 digest bits instead of the 60 v1.1 froze.

`step2-schema-v1.2.json` also adds the outcome v1.1 could not express: **two extractors that
execute and disagree with each other**. v1.1 would have had to pick a winner. That is
`evidence_assurance_failed`, and no digest is adopted from a disagreeing pair.

## 05 — Method note to self

**Ask what would have to be true for each registered fact to come from where I say it comes from.**
Every one of these eight was findable by reading v1.1 against its own sources and against the
profile — no execution required, no fixtures needed. Both rejected registrations passed every
mechanical check I applied. Mechanical validity keeps measuring the wrong thing.

## 06 — Next

Step 2 under v1.2: write and freeze `run_step2.py` against the frozen schema, then run it once from
a clean published commit.
