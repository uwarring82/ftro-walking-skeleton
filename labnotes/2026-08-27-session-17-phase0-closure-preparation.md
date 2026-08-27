# Session 17 — Phase-0 closure instrument preparation

**Date:** 2026-08-27  
**Branch:** `phase0-closure`, from `main` at `a806bba`  
**Status:** preparation only; C9 not rerun, calibration not run, qualifying audits **0/2**  
**Licence:** CC BY 4.0

> **Append-only.** Sessions 13–16 live on the isolated `phase1` branch and contain the
> Gate-1 work plus the corrections that established the true Phase-0 boundary. This note
> starts the closure branch without rewriting them.

## 00 — The five constraints carried into the instrument

The closure runner must not reduce an audit result to pass/fail. A false M11 pass had
already shown why: the detector can execute the wrong route and still return the expected
exit. The registered observations are therefore `detected`, `not_detected` and
`not_executed`; the last can never pass. Every case must prove:

1. its mutation changed the target digest;
2. its detector emitted a case-specific execution marker rather than failing to start;
3. its registered semantic/diagnostic oracle matched; and
4. the isolated candidate returned to its baseline fingerprint.

M6, M7, M8 and M12c expect `not_detected`. That observation is accepted only after the
mutation and detector have both been demonstrated; a zero-match recipe is
`not_executed`, not a no-effect result.

The historical status correction covers the acceptance contract, the historical audit report,
the root README and the machine ledger entries whose impact claimed pre-registration. A later
consistency pass found and corrected three more current README projections: the stale
self-directed count, the exclusion-form convergence wording and the omitted calibration run.
Append-only sessions remain unchanged.

The nine-entry Phase-1 source ledger at `1c9bc56` is frozen in `ledgers/` and reconciled into the
canonical ledger before qualification. The exact convergence predicate is positive rather than
exclusion-based:

```text
disposition == open
and affects == changes_result
and finding_type == current_defect
```

This avoids accidentally treating a future finding type as blocking. A focused unit test
places assurance and latent-regression entries beside a real current defect and checks
that only the latter is returned.

The merged ledger contains 81 entries: 50 resolved and 57 self-directed. Its convergence value
remains zero. That is a recorded judgement, not an assumption: Phase-1 DEF-002/003 concern profile
and serialisation work and do not change `no_common_support`; DEF-008/009 are closure-workflow
findings addressed by this sprint; DEF-001/004/005 are assurance gaps. Provider-controlled or
later-phase workflow gaps do not block Phase 0 unless they make one of C1–C12 fail.

One calibration run is mandatory and categorically non-qualifying. The runner, manifest,
subject and input tuple must remain unchanged for two later qualifying runs.

C9 invalidation is predeclared. Any tracked change to the candidate before qualification
requires another live run. The suggested tests-only exemption was rejected after reading
the actual workflow: README step 0 executes `tests/`, so changing them changes C9. A later
descendant may publish immutable evidence *about* the named carrier, but is not rebound or
silently treated as the audited subject.

Provider failure reports carry both a reachability stage and a separate access-class
conclusion. A DNS/TCP/TLS failure establishes only reachability from the execution
environment at that time; an HTTP 200 login page is an authentication interstitial, not
a successful retrieval or a general access classification.

## 01 — Two additional contradictions found while binding the procedure

The C9 contract said “clean export”, while README step 7 invokes a version gate designed
to fail closed without Git metadata. A literal `git archive` can never satisfy both. C9
v1.2 now requires a clean detached Git checkout; the network-free suite remains runnable
from a Git archive.

The root README still said Phase 0 complete and described the historical model as
pre-registered. The main JSON ledger repeated that premise in FTRO-DEF-063, -064 and -066.
Those are mutable current sources, so they are corrected here rather than left for a
count-only closure edit. The historical lab notes and failed C9 report remain untouched.

## 02 — Frozen population

[`phase0/audit/execution-manifest-v1.0.json`](../phase0/audit/execution-manifest-v1.0.json)
contains **16 operators expanded to 25 concrete cases**. Alternatives that were prose in
the semantic model are selected before execution: three required-field removals, three
wrong counter types, two wrong list types, three population mutations, both segmentation
boundary changes, and both vgosDB M11 routes.

Every case names one target and its pre-mutation SHA-256, a typed mutation, an argv-array
detector, execution and infrastructure markers, allowed baseline/mutated exit codes,
required diagnostic text, output relation and expected observation. There is no shell
expression or arbitrary code in the manifest.

The carrier commit supplies the subject identity. Embedding that commit's hash inside a
file in the commit would be self-referential; instead the runner requires a clean checkout,
proves that its own and the manifest's bytes equal their HEAD blobs, and records HEAD
commit/tree plus both digests. Two qualifying reports must bind the same tuple.

## 03 — Tests before calibration

Commands run in the uncommitted preparation tree:

```text
python3 -m unittest -v tests.test_phase0_audit
Ran 17 tests — OK

python3 -m unittest discover -s tests -v
Ran 147 tests — OK, zero skips

python3 src/ftro/render_deficiencies.py
wrote ledgers/deficiency-log.md (78 entries)

python3 src/ftro/check_versions.py --check
4 versioned artifacts changed; 0 stale
```

The runner tests inject the three instrument failures directly: a zero-match mutation, a
detector without its execution marker, and a detector that changes a second tracked file
so reset cannot be proved. All three become `not_executed`. A registered no-effect case
changes its target, runs its detector and returns `not_detected` with a passing verdict.

This is not calibration. Calibration can only run after the preparation is committed,
because an uncommitted runner cannot prove its carrier identity. Per the agreed order, C9
runs first from a fresh detached clone; calibration follows and never counts.

Test totals are rebound only after the final manifest and root-crate hashes are refreshed. These
are preparation tests, not a qualifying execution of the frozen manifest.

## 04 — What remains

1. Refresh the root crate, commit the preparation candidate and verify it from a clean archive.
2. Run C9 once against live providers with `run_c9.py`; retain the structured report.
3. Run the full manifest once as non-qualifying calibration.
4. If the instrument changes, create a new candidate and rerun C9 before recalibration.
5. Run the unchanged manifest twice from separate detached clones, then—and only then—publish the
   closure evaluation. Evidence-only publication does not rewrite a historical report into a pass.

## 05 — The pre-freeze review found the instrument was not ready

The first adversarial review was deliberately run before the carrier commit. It found three
independent false-PASS paths:

- all four pinners ignored a `False` return from the shared promotion boundary, so schema
  rejection could exit zero and leave a stale official report for the science consumer;
- the mutation runner classified accept/reject by consulting the expected observation, so
  changing the expectation could relabel a rejection as `not_detected`; and
- an eight-field JSON with no case records could satisfy the calibration prerequisite.

C9 also compared committed output bytes without proving the producer had rewritten them, silently
skipped absent fresh pin reports, inherited PATH/proxy/Python injection state and inferred public
access from byte identity. M6 and M7 invoked projections rather than the production support paths;
M8's supposedly adversarial input was already sorted. The reset fingerprint omitted file modes,
and no machine check established that two qualifying reports were distinct.

None of these defects reached a frozen candidate. The response removed each permissive route:

- pinner exit now follows the actual promotion result;
- C9 removes generated targets immediately before their producer, requires fresh externally
  registry-checked coverage for all 65 pinned artifacts (including three evidence-repository
  catalog files) plus the optical archive, records
  a resolved/sanitised toolchain, disables child stdin, preserves a provisional witness before
  exception-safe cleanup, and binds the complete tracked tree;
- accept/reject classification is objective and independent of the expected label; calibration
  deeply replays all 25 evidence records, including full output bytes/digests; resets include file
  type and mode; and qualifying runs require the C9 PASS for the same carrier; and
- a final checker requires two distinct report digests, run IDs and checkout identities.

The M6/M7/M8 probes now call production functions. M7 reconciles 18 quantities over every domain,
pair, triple, four-way result and the pulsar-optical gap and verifies the pulsar constants have one
assignment home anywhere in the source AST. M8 constructs a deliberately disordered population.

This is the first point in the closure work where the bounded pre-freeze process prevented known
false evidence from being published. It also changes the next step: hashes and recipes must be
rebound after these corrections, and only then can a carrier be committed.

## 06 — A second pre-freeze pass tested the evidence boundary itself

The first hardening pass still left three current defects in the instrument. They are recorded as
FTRO-DEF-070–072 rather than disappearing into preparation history.

First, the C9 consumer accepted an eight-field synthetic PASS with one retrieval row. That was
another projection: selected counters agreed, but the claimed eight-command procedure, exact
65-pin registry population, optical source and deterministic outputs were absent. Producer and
consumer now invoke the same strict contract. It keys provider attempts by source group and
artifact, rejects duplicate or missing rows, validates command streams and tool digests, and
requires the exact generated-output and deterministic-comparison populations. The carrier rule is
now single-valued: any tracked change before qualification creates a new candidate and requires a
new live run; a later evidence-publication commit reports about the named carrier rather than
rebinding it. The same pass also separated producer-only checks from portable consumption: the
producer must prove its fresh provisional path and current executable bytes, while a later clone
validates those recorded facts without requiring the historical path or identical host binaries.
Stable C9, calibration and qualifying evidence excludes the current report locator: moving the
same bytes into a publication tree cannot change identity or break the next equality check.

Second, the audit runner's subject and tool boundary was narrower than its name. A clean reset was
a self-reported boolean, Git hooks and user configuration could alter the local baseline, PATH
could select a shim, and chronology did not require distinct execution sites. The runner now
fingerprints the export before Git initialisation, the locally committed baseline and every reset;
isolates HOME, Git configuration and hooks; hashes the absolute interpreter; and requires C9,
calibration, both qualifying runs and the checker to use five distinct checkouts in order. A PASS
is deeply revalidated before it is written. A second adversarial pass then replaced the remaining
ambient controller Git lookup with a fixed-path, checksummed executable and disabled replacement
refs for every carrier read. Tests inject both an absolute PATH shim and a local replace ref.

Third, the live runner degraded the producer's most useful failure evidence and omitted parts of
its runtime binding. Rejected reports now preserve structured cause and reachability separately;
each of the 66 live attempts has a source group; timeout handling terminates and reaps the process
group; the exact shell and Git execution environments are recorded; and the optical summary joins
the four analysis products as a freshly reproduced byte comparison. Volatile retrieval reports no
longer claim a self-stabilising root-crate `contentSize`. The last subprocess check caught a
self-invalidating startup path: importing the adjacent contract minted an ignored `__pycache__`
before the runner enumerated ignored residue. All three controller entry points now disable local
bytecode before adjacent imports, with a clean temporary-tree subprocess regression.

No carrier existed while these faults were present. The focused suite's remaining failures at the
end of this pass are deliberately stale freeze bindings: the changed acceptance contract and root
README digests plus the two new shared-contract files not yet enumerated in the root crate. Those
bindings are refreshed only after the ledger and this note stop changing.

After rebinding, the five Phase-0 audit/C9 modules ran **74 tests**, and the complete network-free
suite ran **175 tests**, both with zero failures and zero skips. `check_versions.py --check`
reported four legitimately advanced artifacts and zero stale versions;
`refresh_crate.py --check` reported zero stale and zero missing entities; `git diff --check`
reported no whitespace errors. This is the preparation-tree freeze gate, not condition 1: that
condition is rerun from the committed carrier's clean archive.
