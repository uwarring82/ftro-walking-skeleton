# Session 19 — first live C9 rejected; provider containers separated from decoded content

**Date:** 2026-08-27
**Branch:** `phase0-closure`
**Rejected carrier:** `354868a08bf99e401907f47ac42c8b5636548ba7`
**Carrier tree:** `b9a685b9c6637b298665dcd99b6c561b728070a2`
**Status:** C9 FAIL; calibration not run; qualifying audits **0/2**
**Licence:** CC BY 4.0

> **Append-only.** This note follows session 18. It does not convert the failed live run into
> evidence for another carrier, and it does not count route-development trials as C9.

## 00 — The second carrier passed the boundary the first one failed

A literal `git archive` of `354868a` ran **175 tests with zero failures or skips**, followed by
`check_versions.py --check`, `refresh_crate.py --check` and `git diff --check`. The archive had no
Git database. This closes the specific hidden-Git dependency recorded as `FTRO-DEF-073` and
demonstrates acceptance condition 1 for this carrier.

One orchestration command then cloned the carrier but invoked the runner from the controller's
working directory because the requested child working directory did not exist at process start.
Python failed with `can't open file /Users/uwarring/phase0/audit/run_c9.py`. No provider request and
no C9 report resulted. This is a recorded dead end, not a C9 execution.

## 01 — The first actual live execution failed at provider reachability

The runner was then invoked inside a fresh detached clone as `c9-354868a-1`. Its immutable report
is retained outside the tracked carrier at:

```text
/tmp/ftro-closure-354868a-20260827/c9.json
sha256:6e497683b1287eb4dd8ae2c2ebf0bac9457bfd2ddd04a4448ad0953ca3a8e325
```

Observed execution:

| Evidence | Result |
| --- | --- |
| Regression suite | 175 passed |
| Completed README steps | 0, 1, 2, 3 |
| Optical archive | HTTP 200; 83,530,540 B; MD5 matched |
| Provider attempts recorded | 61 |
| Successful attempts | 4 |
| BKG IGS attempts | 57 transport failures |
| Failure stage | TCP connection refused; no HTTP response or bytes |
| Access-class conclusion | not established |
| Manual intervention / route substitution | 0 / 0 |

Step 4 stopped under `zsh -e` after `pin_igs.py` rejected all 57 requests and preserved its
failed report as `.rejected`; vgosDB and PPTA were therefore not attempted in this run. Steps 5–7
did not run. The strict report says `status: fail`, `qualifying: false`. Calibration was not
started, as required.

Three direct probes at 07:54 UTC reproduced immediate refusal on BKG port 443. This establishes
reachability failure from this environment at those knowledge times, not restriction or general
unavailability.

## 02 — The report named the last failure as the first

The report's `provider_attempts` retain the true order: the first IGS rejection was
`igs21980.sp3.Z` at 07:41:27.482440 UTC and the last was `igs21997.erp.Z` at
07:42:17.736870 UTC. `first_failure` nevertheless named the latter because the recorder selected
`failed_attempts[-1]`. This is `FTRO-DEF-074`.

The defect did not alter FAIL, the transport classification or the access-class conclusion. It
did make a named evidence field false, so `354868a` is rejected as the closure carrier. The repair
orders failed attempts by pipeline step and then retrieval timestamp, with original position only
as a tie-breaker. Its regression fixture deliberately assembles rows out of chronological order.

## 03 — Alternative official mirrors expose representation-level identity

The IGS data-centre list names SIO/SOPAC, IGN and WHU. Live probes established:

- SIO/GARNER anonymous HTTPS retrieved and content-validated **57/57** registered artifacts;
- WHU anonymous FTP validated 53 on the first sequential pass, with one transient FTP 425 that
  succeeded on retry;
- IGN anonymous FTP requires explicit anonymous credentials; and
- SIO, IGN and WHU agree on the three containers that differ from the prior BKG retrieval.

Comparing the complete SIO population with the locally pinned BKG population gave:

```text
checked=57 missing=0 outer_mismatches=3 inner_mismatches=0
```

| Artifact | Earlier BKG container SHA-256 | SIO/IGN/WHU container SHA-256 | Decoded SHA-256 |
| --- | --- | --- | --- |
| `igs21982.clk.Z` | `da4b4c4b…8233eea1` | `7bd05cce…eada33b5` | `b3145e51…a1137ba` |
| `igs21983.clk.Z` | `898d8029…e6d2eb40` | `9280fcd3…e75975e6` | `8ac65974…777e3ab` |
| `igr21991.clk.Z` | `fa3ff944…5206f8ec1c` | `2ead2464…c51f34` | `aa5e471c…f89a01` |

The decoded digest in each row is identical on both sides. Fifty-four outer containers are also
identical. No reachable official route reproducing the three BKG-specific containers was
established. Therefore this is not recorded as a URL-only substitution: the next registry keeps
the previous retrieval digest and decoded digest while selecting the SIO outer digest as a new
snapshot. The GNSS support and scientific conclusion are unchanged. This is `FTRO-DEF-075`.

The same SIO listings also falsified the dataset-level wording of `FTRO-DEF-020`: each week has
seven `igs*.clk_30s.Z` files and 96 `*.sum.Z` files. Their absence was a BKG-route observation,
not an IGS-holdings observation. `FTRO-DEF-020` is corrected to v2.0.0 and resolved. The files
remain outside the frozen 57-artifact Phase-0 target population.

## 04 — The alternate-route trial caught one more provenance projection

`pin_igs.py --base https://garner.ucsd.edu/pub/products` emitted SIO URLs but still labelled the
report as BKG and described every Last-Modified value as a BKG mirror time. The locator was
configurable; its provenance text was not. This is `FTRO-DEF-076`.

The next carrier names SIO/GARNER as its default. Any operator-supplied override is instead
labelled `data centre not established`; it cannot inherit the default provider identity. Direct
tests cover both paths.

The first registry repair repeated the same failure one layer down: it stored `decoded_sha256`
and `previous_retrieval_sha256`, but `pin_igs.py` projected each structured record back to its
outer `sha256` and never executed the decoded expectation. A correct-looking evidence field that
cannot reject wrong bytes is inert. `FTRO-DEF-076` is therefore corrected to v2.0.0. The pinner
now validates the structured record before any request, decompresses each representation variant,
rejects a decoded mismatch, and emits the expected and observed decoded digests plus their match
result. A malformed structured expectation makes zero requests.

A final route review found one remaining attribution hole: successful `urlopen()` calls discarded
`resp.geturl()`, so a future redirect could still be labelled as SIO solely because SIO was the
requested base. `FTRO-DEF-076` is corrected again to v3.0.0. The pinner now records the effective
URL and rejects any unexpected redirect before cache or promotion. It also distinguishes a
decoded-checksum rejection from content-shape rejection in the failure note.

The final preparation pinner pass retrieved and promoted **57/57**, recorded an effective URL on
all 57 pins, and found **0 redirects**; all three decoded expectations matched. This remains route
preparation, not a C9 run.

Review of the failure path also found that `urllib.error.HTTPError` was falling through the broad
transport-exception branch. That discarded an HTTP response's status, headers and body evidence,
so C9 could not distinguish a reached provider returning 4xx/5xx from failure before HTTP. This
extends `FTRO-DEF-072` to v2.0.0. HTTP errors now preserve status, effective URL, selected headers,
body size and digest in the rejected report, while caching no response bytes; C9 consumes the same
fields and classifies the attempt as `http_failure`.

A current-view ledger audit then found six resolved version-gate entries still describing the
registry, `--update`, `--register` and generated-file special case deleted in session 12. Their
historical observations remain unchanged, but their resolution fields now describe the actual
read-only Git comparison and its two explicit file exclusions. This changes no disposition or
convergence count; it prevents the structured ledger from presenting retired machinery as the
current control.

## 05 — Consequence for the exit sequence

Carrier `354868a` is historical failed evidence. Its clean-archive result is retained, but no C9,
calibration or qualifying count transfers to its descendant. The next sequence remains exact:

1. commit and clean-archive-test the SIO-bound repaired carrier;
2. execute C9 from a fresh detached clone with no route substitution;
3. run one non-qualifying calibration;
4. run the unchanged manifest twice in two further clean clones; and
5. validate the tuple in a fifth clone.

The ledger now has 85 entries, 56 resolved and 60 self-directed. The imported unzip deficiency is
resolved because the live run completed the repaired extraction step. The convergence predicate remains
zero: the new current defects affected workflow/evidence provenance, not the scientific result.
