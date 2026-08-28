# Session 24 — Phase 2 opens: WP2A pre-registered before any mapping

**Date:** 2026-08-28 · **Branch:** `phase2` from `main` @ `e123a81`
**Outcome:** contract frozen; two premise corrections recorded; nothing mapped yet.
**Licence:** CC BY 4.0

> **Append-only.** Sessions 01–23 are unedited.

---

## 00 — What is pre-registered

Contract, expected facts, eight neutral queries, the decision table and a 40-case mutation
population — all committed **before** either mapping is authored. Two product families, two
representations, four fixtures.

Phase 0 needed thirteen sessions to learn that an audit whose scope is chosen after seeing results
cannot terminate. This package starts where that ended.

## 01 — Verified, not assumed: the families are consumed at different layers

The correction that shaped the contract. Checked against the implementation rather than accepted:

- `pin_igs.py:143` calls `unixz.decompress`, and `decoded_variant_evidence()` **executes** a
  decoded-content expectation. Decoded IGS bytes are consumed — for content validation.
- `four_domain_intersection.py:101` derives GNSS support from `igs_day_from_name(pin["name"])`
  through the `IGS_FINAL_NAME` regex. **Decoded content never reaches the science.**
- `analyse_optical.py:155` reads `.dat` bytes. The optical member *is* the scientific input.

Had both been modelled as analysis-consumed payloads, the trial would have compared two
representations of a fact that is not true of one family. Query **Q5** now tests the asymmetry
directly, and a model that cannot express it fails.

## 02 — Verified, and it changed the registration: an unauthenticated digest

The member **path** is authenticated in `optical-inventory-summary.json`:
`2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat`, 16,106 samples, `mjd_first` **59631.788542**. That
is the corpus-wide earliest optical sample — the boundary that sets the published 31.17 h
pulsar→optical gap. A good choice of member, and now recorded as *why* this member.

But **no per-member digest or size exists anywhere in the repository.** `780,292 B` and
`00cc90d8…363c067` came from the work-package proposal, not from committed evidence. Freezing them
as expected facts would have been the same premise-baking §01 avoids, one layer out.

They are registered as a **prediction** with `evidence_state: unauthenticated_at_registration`.
Step 2 confirms or refutes it, and a mismatch is a trial-halting finding — never a silent update.
A pre-registered prediction that can fail is stronger than an expected fact that cannot.

## 03 — The mutation freeze is two-stage, and says so

The population — 11 operators, 40 cases, applicability matrix, expected observations, including
`R11` as a registered **non-detection** — is frozen now. The executable per-case recipes cannot be:
the fixtures do not exist yet, and a recipe needs a concrete target, mutation value, detecting
command, reset boundary and destination.

So the contract states the second freeze up front: recipes land after step 3 and **before** step 4
calibration, and neither artifact changes after any result is seen. `FTRO-P1-DEF-009` was filed
because a fault model named operators without executable recipes; this package declares both stages
in advance instead of discovering the gap during execution.

## 04 — The stopping rule has teeth

`FTRO-P1-DEF-010` closes **only** if exactly one model is separated by a pre-registered
requirement. If both pass, the result is `equivalent_for_registered_queries` and the entry stays
open. No model is chosen aesthetically, and "both worked, pick the nicer one" is not an available
outcome.

## 05 — Next

Step 2: the durable input-evidence report, with independent `zipfile`, `unzip -p` and
Unix-compress cross-checks. It also settles the §02 prediction.
