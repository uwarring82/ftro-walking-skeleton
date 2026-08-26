# Session 16 — Published-carrier hardening and committed Gate-1 witness

**Date:** 2026-08-26 · **Branch:** `phase1`  
**Candidate commit:** `d31a70c2167d4b548a0026180aa50a38dfaecb5f`  
**Phase-0 baseline:** `main` remains at `a806bbaa573d28f1460d18110f7974189ca19213`  
**Outcome:** the committed carrier now rejects executable extra paths; the exact committed candidate passed a live 69/69 retrieval; DEF-009 links both blocked exit conditions.  
**Licence:** CC BY 4.0

> **Append-only.** Session 15 remains the record of the parent-overlay witness and 0/2 audit
> correction. This session records the final hardening choice, publication commit and second live
> execution form.

---

## 00 — Independent verification result

The 43/97 test counts, live report aggregates, ten input hashes, version gate, root-crate exception,
Phase-0 isolation and both substantive corrections reproduced independently. The review also
confirmed that `committed_checkout` accepted a clean descendant containing the six candidate files.

One deliberate asymmetry remained: the parent overlay allowed exactly six paths, while a committed
carrier allowed any additional committed path. An added `src/ftro/schema.py` therefore passed
preflight. That did not change the digest-pinned 69-source retrieval, but the documentation's phrase
“non-input publication outputs” described a restriction the code did not enforce.

---

## 01 — The stronger witness was chosen

The committed carrier now permits only:

- the six captured candidate paths;
- `phase1/README.md` and `phase1/deficiency-log-phase1.json`;
- files under `phase1/reports/`; and
- files under `labnotes/`.

All other paths are rejected. The producer and report consumer apply the same allowlist. Tests
commit both `src/ftro/schema.py` and an arbitrary `phase1/helper.py` beside the candidate; each is
rejected. A carrier containing the Phase-1 README is accepted. This makes the committed witness
stronger in the relevant dimension: it may carry non-executable evidence outputs, but cannot bundle
unattested Phase-0, profile, ledger, test or executable-code changes.

The Phase-1 suite now contains **44 tests**, zero skips.

The machine-layer omission in `FTRO-P1-DEF-009` was also corrected: `links.contract` is now an array
containing both `exit-condition-4` and `exit-condition-5`.

---

## 02 — Candidate commit

The complete candidate was committed as:

```text
d31a70c2167d4b548a0026180aa50a38dfaecb5f
Phase 1: establish Gate 1 source evidence
```

The commit contains the six candidate inputs and only allowlisted publication outputs beyond them.
It does not modify `src/`, `tests/`, `phase0/`, `ledgers/`, `profile/` or the root README relative to
the Phase-0 baseline.

---

## 03 — Live committed-checkout witness

A fresh local clone checked out `d31a70c` detached. Before any request, the production preflight
established:

- `data/` absent;
- worktree changes: none;
- `028c317` is an ancestor of HEAD;
- all six candidate paths differ from the Phase-1 parent; and
- every additional changed path is an allowlisted publication output.

The live retrieval then reproduced the parent-overlay result:

| Quantity | Result |
| --- | ---: |
| Provider sources | 66 |
| FTRO catalogs at the frozen baseline | 3 |
| Retrieved and matched | 69/69 |
| Failed | 0 |
| Bytes streamed | 140,736,196 |

- executed: `2026-08-26T17:39:27.891192+00:00`
- execution HEAD: `d31a70c2167d4b548a0026180aa50a38dfaecb5f`
- input fingerprint: `b58359d8c8383dcf9e409cc5cc7db07bd8920f391ab35b275d837d402da352e3`
- report SHA-256: `8c65a5e46cd75dbba67d6eadaffb8923d09096330ff994dd70318d9e34a10005`
- freshness/content verification: **PASS**
- Phase-1 tests: **44**, zero skips; unchanged Phase-0 tests: **97**, zero skips
- version gate: zero stale
- root-crate isolation exception: only `labnotes/README.md` is stale (`3333 → 3955`), zero missing

Durable report:
[`gate1-clean-retrieval-committed-d31a70c.json`](../phase1/reports/gate1-clean-retrieval-committed-d31a70c.json).

The parent-overlay report remains separately retained as
[`gate1-clean-retrieval-v1.0.json`](../phase1/reports/gate1-clean-retrieval-v1.0.json). The committed
report is the stronger publication witness. Its containing follow-up commit need not equal the
execution HEAD: the report binds the exact candidate inputs and records the clean commit from which
retrieval ran.

---

## 04 — Remaining boundary

Nothing about Phase-0 closure changed:

- C9 still needs the missing directory-creation command and one clean live rerun;
- exit condition 4 remains undemonstrated;
- qualifying bounded audits remain **0/2**; and
- one executable audit manifest must be frozen and run unchanged twice.

The profile amendment remains deferred until those finite Phase-0 operations complete.
