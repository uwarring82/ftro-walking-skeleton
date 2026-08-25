# FTRO Decision Ledger

**Version:** 0.1.0 · **Opened:** 2026-08-25 · **Licence:** CC BY 4.0

Decisions taken during implementation, with their basis. Card-level decisions live in
task card §23; this ledger records choices made *while executing* it.

| # | Decision | Basis | Session |
| --- | --- | --- | --- |
| D-001 | Repository public from Phase 0 | Card §7A: public walking skeleton precedes consortium engagement | 01 |
| D-002 | `data/raw/` excluded from version control | Card §3 federation-over-migration; FTRO stores identifiers and checksums, not provider bytes | 01 |
| D-003 | Retrieval implemented as committed scripts, not interactive commands | Card §8.2: "no hidden local files or undocumented manual steps" | 01 |
| D-004 | Machine-readable ledger is the source of truth; Markdown is generated | Card §3: "human and machine views share one source of truth" | 01 |
| D-005 | Degenerate validity flag classified `source_evidence`, not `schema` | Card §17 worked example: an archive flag problem "begins as source_evidence rather than automatically schema" | 01 |
| D-006 | Missing `ref_osc`/`interval`/`lag`/`weighting` classified `source_evidence`, not `schema` | The pinned format marks all four **optional**, so the format is not at fault; the evidence is | 01 |
| D-007 | Time-varying `uA_sys` **not** filed as a deficiency | The pinned spec documents column 4 as "time-varying systematic uncertainty". Read the spec before classifying | 01 |
| D-008 | Undocumented 5th column classified `schema` | The format *cannot express* a second systematic uncertainty — card §17: "inability to express … is schema" | 01 |
| D-009 | `tintervals` edge is `contextualized_by`, not `generated_by` | Pinned commit post-dates the data by 19 months; that revision cannot be the generating software, and no earlier revision is pinned | 01 |
| D-010 | IVS session R11040 selected over six alternatives | Highest optical overlap (7 comparisons, 91.95 h vs 26.38 h next) and an IVS-R1, the series feeding operational EOP | 01 |
| D-011 | Optical support computed as per-comparison **envelopes** for the intersection test | Deliberate upper bound: refining envelopes into exact runs can only remove support, so a null under envelopes is robust | 01 |
| D-011a | **Superseded 02:** optical support recomputed as the run-level union (133.112 h, not 197.075 h) | External review: the envelope figure was an upper bound presented as support. VLBI and GNSS legs remain upper bounds, so overlaps are still bounded | 02 |
| D-029 | Optical basis relabelled `recorded_timestamp_span_union`, bound `derived` not `exact` | It is exact over recorded tags under a chosen 1.5 s rule, not over physical support: `interval`/`lag`/`weighting` are absent, so tag placement is unconstrained over up to 1 s | 03 |
| D-030 | Convention sensitivity computed by the script, not asserted in prose | Same rule as D-023. The null is now shown invariant over gap tolerance 1.1–5.0 s, 1 s sample crediting and ±1 s tag shift | 03 |
| D-031 | Profile §5.2 ("third identity level") retracted rather than amended | A wrapper is an ordinary archive member and an ASCII pointer file; member digest + consumption edge suffices, and the format's own `InputWrapper` supplies derivation. Retraction is the honest record ([`FTRO-DEF-026`](deficiency-log.md#ftro-def-026) v2.0.0) | 03 |
| D-032 | No profile MUST-clause lands without an executable check against the reference manifest | §5.1 was introduced and violated in the same commit, 5 of 5 identities ([`FTRO-DEF-029`](deficiency-log.md#ftro-def-029)) | 03 |
| D-033 | All three retrieval tools fail closed on a digest mismatch; an unverified retrieval mints no identity and caches no bytes | `--expect-sha256` was recorded as a field, not enforced as a gate; a login page could occupy the product filename | 03 |
| D-033a | **Corrected 04:** `pin_igs.py` had no expected-digest input at all when D-033 was written, so the claim covered two tools, not three. It now takes `--expect-sha256-manifest` and fails closed | A decision that overstates what the code does is the same defect as a finding that does | 04 |
| D-036 | A check written to enforce a rule must not reuse the scoping assumptions of the observation that prompted it | The §5.1 test filtered on `snapshot_kind` alone and so passed while 2 of 7 records violated the clause ([`FTRO-DEF-029`](deficiency-log.md#ftro-def-029) v2.0.0) | 04 |
| D-037 | A sensitivity probe must re-run the pipeline stage whose parameter it varies, never post-process that stage's output | The gap-tolerance scan re-merged an already-segmented inventory: it could not split runs and joined unrelated series ([`FTRO-DEF-030`](deficiency-log.md#ftro-def-030)) | 04 |
| D-038 | A test that can skip must not be the only coverage of a behaviour; a fixture must be a real instance of the format it stands for | A clean clone reported "OK (skipped=3)" with fail-closed untested, and the `.Z` fixture was fake payload behind correct magic ([`FTRO-DEF-031`](deficiency-log.md#ftro-def-031)) | 04 |
| D-039 | Any normative change bumps the profile version in the same commit | v0.0.1 was byte-distinct across three commits while gaining clauses, so "conforms to v0.0.1" named no constraint set ([`FTRO-DEF-033`](deficiency-log.md#ftro-def-033)) | 04 |
| D-040 | Format signatures are derived from the bytes, never from memory | Two successive ERP signatures written from recollection each rejected one of the two genuine ERP families; the third, keyed on what the bytes actually share, accepts all 57 artifacts | 04 |
| D-041 | A recorded contradiction is not a resolved one | The §9.2 `resolvable`/`status_and_checksum` clash was annotated on four records for two commits instead of being fixed ([`FTRO-DEF-032`](deficiency-log.md#ftro-def-032)) | 04 |
| D-034 | Wrapper states keyed by member digest, never filename | 7 filenames collapse to 5 distinct byte sequences; filename keying invents two states and attributes bytes to a centre that produced none | 03 |
| D-035 | Route enumeration gates the dataset-level negative, not `access_class` | `access_class` is a property of a retrieval path, so one content-validated anonymous retrieval settles it for that path. Enumeration is required before asserting `unresolved` | 03 |
| D-012 | Candidate window **not** widened despite the empty intersection | Card §6 and §20 forbid silent widening; §20 forbids substituting the March 2023 dataset | 01 |
| D-013 | `REPRO-PSR-001` targets only the observatory→GPS→UTC leg | The TAI→TT leg is contested (DEF-011) and the EOP leg unresolved (DEF-012); a reproduction target must be evidenced | 01 |
| D-014 | `REPRO-OPT-001` targets format consumption, not the physical frequency ratio | The physical interpretation is ambiguous without `ref_osc` (DEF-004) | 01 |
| D-015 | Own tooling's soft-auth-wall weakness logged against ourselves as DEF-018 | Card §17: the ledger records limitations encountered *by the federation*, including its own | 01 |
| D-016 | BKG chosen as GNSS data centre | Only anonymously accessible mirror of the three tried; CDDIS redirects, AIUB and IGN timed out | 01 |
| D-017 | PPTA `redistribution_mode = link_only` | CC BY-SA 4.0 is copyleft and would propagate to any CC BY 4.0 FTRO output (DEF-014) | 01 |
| D-018 | Charter and profile drafted **after** Phase 0, not before | Every clause is then grounded in evidence actually encountered; Gate 1 requires that no term be frozen | 01 |
| D-019 | Two new profile fields proposed (`time_coordinate_quantum`, `validity_mask_informativeness`) | Phase 0 measured two properties the card's §10 field list cannot express (DEF-021, DEF-001) | 01 |
| D-020 | Fabricated ORCID removed from `CITATION.cff` | An invented persistent identifier is precisely the failure mode this project exists to prevent | 01 |
| D-021 | Corrections applied as a follow-up commit; session-01 lab note left **unedited** | `labnotes/README.md` declares lab notes append-only. A record of what was believed at a knowledge time is itself data — the same bitemporal rule the project applies to provider evidence | 02 |
| D-022 | Optical concept/version identity corrected to the provider's own DOIs | Zenodo asserts the distinction in four fields. Card §10 composition is conditional on the provider supplying no immutable PID; that precondition was never met ([`FTRO-DEF-024`](deficiency-log.md#ftro-def-024)) | 02 |
| D-023 | Quantisation census implemented in `analyse_optical.py` rather than restating the sampled figure | A number quoted in a finding must be traceable to a key in a committed report. The original 1,564,882 came from an uncommitted 40-file sample ([`FTRO-DEF-027`](deficiency-log.md#ftro-def-027)) | 02 |
| D-024 | Content-shape validation added to FTRO retrieval tooling, with a live regression test against CDDIS | DEF-018 was logged against our own tooling in session 01 but not fixed; a self-directed deficiency that is never closed is decoration | 02 |
| D-025 | VLBI leg re-attempted at OPAR and pinned | `unresolved` had asserted unavailability established from a single data centre ([`FTRO-DEF-025`](deficiency-log.md#ftro-def-025)) | 02 |
| D-026 | Full 64-character digests inside every identity; short forms only in named `sha256_short` fields or head…tail prose | A truncated digest inside an identity makes it a different, weaker identity | 02 |
| D-027 | Dimensional comparisons between the time quantum and fractional-frequency uncertainty deleted, not recalculated | Seconds and a dimensionless ratio are different kinds of quantity; no ratio between them is meaningful | 02 |
| D-028 | "Confirmed the pre-registered expectation" downgraded for the EOP finding | The card predicted an *opaque* artifact; we found an *unidentified* one. A different outcome is not a confirmation, even when it is more severe | 02 |
