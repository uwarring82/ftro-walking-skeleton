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
| D-009 | `tintervals` edge is `contextualized_by`, not `generated_by` | Pinned commit post-dates the data by 19 months; it cannot be the generating software | 01 |
| D-010 | IVS session R11040 selected over six alternatives | Highest optical overlap (7 comparisons, 91.95 h vs 26.38 h next) and an IVS-R1, the series feeding operational EOP | 01 |
| D-011 | Optical support computed as per-comparison **envelopes** for the intersection test | Deliberate upper bound: a null under an upper bound is a strong null | 01 |
| D-012 | Candidate window **not** widened despite the empty intersection | Card §6 and §20 forbid silent widening; §20 forbids substituting the March 2023 dataset | 01 |
| D-013 | `REPRO-PSR-001` targets only the observatory→GPS→UTC leg | The TAI→TT leg is contested (DEF-011) and the EOP leg unresolved (DEF-012); a reproduction target must be evidenced | 01 |
| D-014 | `REPRO-OPT-001` targets format consumption, not the physical frequency ratio | The physical interpretation is ambiguous without `ref_osc` (DEF-004) | 01 |
| D-015 | Own tooling's soft-auth-wall weakness logged against ourselves as DEF-018 | Card §17: the ledger records limitations encountered *by the federation*, including its own | 01 |
| D-016 | BKG chosen as GNSS data centre | Only anonymously accessible mirror of the three tried; CDDIS redirects, AIUB and IGN timed out | 01 |
| D-017 | PPTA `redistribution_mode = link_only` | CC BY-SA 4.0 is copyleft and would propagate to any CC BY 4.0 FTRO output (DEF-014) | 01 |
| D-018 | Charter and profile drafted **after** Phase 0, not before | Every clause is then grounded in evidence actually encountered; Gate 1 requires that no term be frozen | 01 |
| D-019 | Two new profile fields proposed (`time_coordinate_quantum`, `validity_mask_informativeness`) | Phase 0 measured two properties the card's §10 field list cannot express (DEF-021, DEF-001) | 01 |
| D-020 | Fabricated ORCID removed from `CITATION.cff` | An invented persistent identifier is precisely the failure mode this project exists to prevent | 01 |
