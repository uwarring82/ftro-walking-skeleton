# Vocabulary pressure from four hand-authored manifests — representation identity

**Document ID:** FTRO-VOC-001 · **Version:** 1.2.0 · **Date:** 2026-08-27 · **Licence:** CC BY 4.0
**Supersedes:** `vocabulary-pressure-v1.1.md` as current guidance; v1.0 and v1.1 remain historical.
**Inputs:** the four Phase-1 manifests, qualified Phase-0 carrier `8ddcbfa`, the SIO-bound IGS pin
report, and Gate-1 candidate `d0f9e37`.

Gate 1 still means **nothing is frozen**. This revision retains v1.1's relation-assertion,
null-state, conformance-report and coverage findings and adds one identity pressure that became
visible only when the live Phase-0 carrier changed IGS data centre.

---

## 1. One logical product can have distinct retrieval containers

All 57 IGS filenames and decoded payloads are unchanged between the earlier BKG evidence and the
qualified SIO/GARNER carrier. Fifty-four compressed containers are also byte-identical. Three are
not:

| Product | Historical BKG container | Qualified SIO container | Decoded state |
| --- | --- | --- | --- |
| `igs21982.clk.Z` | `da4b4c4b…8233eea1` | `7bd05cce…6ada33b5` | `b3145e51…5a1137ba` |
| `igs21983.clk.Z` | `898d8029…e6d2eb40` | `9280fcd3…e75975e6` | `8ac65974…777e3ab` |
| `igr21991.clk.Z` | `fa3ff944…a6f8ec1c` | `2ead2464…03c51f34` | `aa5e471c…b4f89a01` |

The outer SHA-256 is therefore not “the product checksum” without a named retrieval route. The
BKG and SIO containers are distinct immutable retrieval snapshots. Their decoded payloads are
equal under the recorded Unix-compress procedure. Neither statement cancels the other.

## 2. The profile has no interoperable place for both facts

Profile §5 and the first GNSS crate provide one broad `File` / `ImmutableSnapshot` role. They do
not define whether an encoded container and decoded product state are two nodes, which relation
connects them, which digest identifies the consumed analysis input, or what evidence is required
to assert decoded equality. Merging on filename or decoded hash loses exact-retrieval provenance;
splitting only on the outer hash hides content equality.

This is `FTRO-P1-DEF-010`. It is pressure on the identity model, not evidence for an automatic
third identity tier. Existing `File`, `ImmutableSnapshot`, assertion and derivation concepts may
be sufficient once their roles and cardinalities are made explicit.

## 3. Provisional hand-authored representation

The GNSS manifest now carries three provisional `ftro:RepresentationEquivalenceAssertion` nodes.
Each records:

- distinct current and historical outer snapshot identifiers and SHA-256 values;
- the common decoded SHA-256 and hash algorithm;
- `src/ftro/unixz.py` as the decoding implementation used by the carrier;
- scope `decoded_payload_only`, explicitly excluding `retrieval_container_bytes`;
- the carrier pin report as evidence; and
- valid- and knowledge-time bounds.

The Gate-1 checker derives the three expected assertions from the carrier pin report and rejects a
missing assertion, altered digest, wrong subject/object or wrong evidence artifact. The mapping is
provisional vocabulary evidence. It is not profile conformance and is not `owl:sameAs`: the outer
containers remain byte-distinct entities.

The new Gate-1 live run re-retrieved and checked the SIO side against the qualified digests. It did
not re-fetch BKG. The BKG outer digests and decoded equality remain historical Phase-0 evidence
preserved in the pin report and session 19; this revision does not strengthen that provenance.

## 4. Equal headline counts hid a changed population

The historical and replacement Gate-1 witnesses both say 69/69, but their immutable populations
differ in three GNSS snapshots and one FTRO IGS-catalog snapshot. A count is not an identity check;
the input fingerprint and exact source keys are the evidence.

C9 also reports 66 provider attempts, but it is a different set. Gate 1's 66 are 3 optical, 5
pulsar, 1 VLBI and 57 GNSS sources. C9's 66 are 1 optical archive, 4 PPTA artifacts, 1 vgosDB, 3
evidence-repository files and 57 GNSS artifacts. The same total carries no cross-gate equivalence.

## 5. Gate-1 rebaseline decision

All three FTRO-owned source-catalog URLs are intentionally repinned from `a806bba` to qualified
carrier `8ddcbfa`. The PPTA and VLBI catalog bytes are unchanged; the IGS catalog digest changes to
`d97b05d2…3ad9b7c`. Retaining the old catalog commit would keep the historical witness reproducible
but would make the current Gate attest superseded evidence. The old reports remain immutable for
their own fingerprints instead.

Candidate `d0f9e37`, descended from integration parent `12b119a`, passed 48 Phase-1 tests and the
bounded structural check. A clean committed checkout then retrieved and matched 69/69 current
sources with no provider bytes retained. This demonstrates source location only.

## 6. Amendment boundary

Do not amend profile §5 by copying the provisional class name. Before freezing an identity model:

1. hand-author at least the encoded-node/decoded-node and assertion-only alternatives;
2. state which node is the consumed analysis input and which digest identifies it;
3. define decoding procedure/software provenance and assertion cardinalities;
4. preserve exact container provenance without using `owl:sameAs`; and
5. test the pattern on another compressed or packaged provider product.

The v1.1 relation-assertion and explicit unresolved-state work also remains open, as does normative
RO-Crate 1.3 validation. The smallest defensible amendment must address these together rather than
freezing the first serialisation that happened to pass Gate 1.
