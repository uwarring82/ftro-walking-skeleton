# Phase-0 closure execution

**Document ID:** FTRO-AUD-EXEC-README-001 · **Version:** 1.1.0 · **Date:** 2026-08-27
**Status:** Replacement carrier in preparation; prior C9 failed, calibration not run, qualifying audits 0/2.

The semantic fault model is historical. The executable pre-registration is
[`execution-manifest-v1.0.json`](execution-manifest-v1.0.json); its controller is
[`run.py`](run.py). The live C9 recorder is [`run_c9.py`](run_c9.py).

Carrier `354868a` passed its literal clean-archive suite, then its first live C9 attempt stopped at
step 4 when BKG refused all 57 IGS connections. The same report exposed `FTRO-DEF-074`: its
`first_failure` projection selected the last rejection. The carrier is rejected; no calibration
or qualifying evidence transfers to this replacement.

## Outcome model

Every mutation case has one of three observations:

- `detected`: the registered detector ran and rejected the applied mutation;
- `not_detected`: the registered detector ran and accepted the applied mutation;
- `not_executed`: application, detector-execution or reset evidence is incomplete.

`not_executed` always fails. M6, M7, M8 and M12c register `not_detected`; they pass only
when the target digest changed, the detector emitted its execution marker, its semantic
oracle matched, and the isolated tree returned to the candidate fingerprint.

Each case starts from a fresh full `git archive` of the candidate, initialized as a local
Git repository. Production source is copied, never symlinked. The baseline detector must
pass before mutation. The report records command exit, output digests, bounded excerpts,
the mutation diff digest and reset proof. Controller Git is selected only from fixed system
paths, checksummed in the report and invoked with replacement refs, user/system configuration
and hooks disabled; inherited PATH cannot substitute the carrier reader.

## Fixed execution order

1. The Phase-1 deficiency source ledger is reconciled. Commit this preparation on
   `phase0-closure` and verify its network-free suite from a clean archive.
2. In a fresh detached clone of that commit, with no ignored residue or `data/`, run C9 first:

   ```bash
   python3 phase0/audit/run_c9.py \
     --run-id c9-1 \
     --out /tmp/ftro-c9-1.json
   ```

3. Run the complete manifest once as calibration. It never counts:

   ```bash
   python3 phase0/audit/run.py \
     --mode calibration \
     --run-id calibration-1 \
     --c9-report /absolute/path/to/c9-1.json \
     --out /tmp/ftro-audit-calibration-1.json
   ```

4. If calibration changes any tracked carrier byte, commit a new candidate, rerun C9 and
   calibrate again. There is no pre-qualification rebinding exception: C9, calibration and
   both qualifying reports must name the same exact carrier commit and tree.
5. From two different fresh detached clones of the same successfully calibrated commit,
   run:

   ```bash
   python3 phase0/audit/run.py \
     --mode qualifying \
     --run-id qualifying-1 \
     --c9-report /absolute/path/to/c9-1.json \
     --calibration-report /absolute/path/to/calibration.json \
     --out /tmp/ftro-audit-qualifying-1.json
   ```

   Repeat as `qualifying-2` in the second clone. A checkout records an attempted
   qualifying run in its Git directory and refuses a second attempt.

6. From a third clean detached clone of the same carrier, validate the whole tuple:

   ```bash
   python3 phase0/audit/check_qualification.py \
     --c9-report /absolute/path/to/c9-1.json \
     --calibration-report /absolute/path/to/calibration.json \
     --qualifying-report /absolute/path/to/qualifying-1.json \
     --qualifying-report /absolute/path/to/qualifying-2.json \
     --out /tmp/ftro-phase0-qualification.json
   ```

   The checker deeply revalidates all 25 case records and requires distinct report bytes,
   run IDs and checkout identities. Copying one PASS twice cannot satisfy 2/2.

The C9 report distinguishes pipeline correctness, reachability stage and access-class
conclusion. A provider failure never becomes a claim of restriction or unavailability
without separate evidence. Retrieved bytes and the optical extraction are removed after
the report evidence is captured. Fresh absolute paths and executable bytes are producer checks;
later consumers verify their recorded provenance without requiring the original path or host.

## Candidate invalidation and evidence publication

C9 and every audit report are bound to the same complete tracked carrier tree. Any tracked
change before qualification completes creates a new candidate and requires a new live run.
After the carrier qualifies, a descendant commit may publish the immutable reports, lab note
and status evaluation *about that named carrier*. That is evidence publication, not rebinding:
the descendant is not silently treated as the audited subject.

The qualifying count resets to 0/2 after any change to the runner, manifest, audited
subject or bound inputs. Historical reports are retained; they are never rewritten into
passes.
