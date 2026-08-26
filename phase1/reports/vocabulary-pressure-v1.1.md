# Vocabulary pressure from four hand-authored manifests — corrected assessment

**Document ID:** FTRO-VOC-001 · **Version:** 1.1.0 · **Date:** 2026-08-26 · **Licence:** CC BY 4.0  
**Supersedes:** `vocabulary-pressure-v1.0.md` as current guidance; v1.0 remains as the historical first assessment.  
**Inputs:** the four manifests under `phase1/manifests/`, profile v0.0.3, RO-Crate 1.3, the frozen Phase-0 source reports, and the bounded Gate-1 checks.

Gate 1 still means **nothing is frozen**. This correction narrows what the first comparison actually established.

---

## 1. The edge finding is real, but v1.0 stated it too strongly

JSON-LD can represent a relation with attributes by reifying it as a node. Therefore profile §4 is
not literally impossible to serialise. The actual defect is that the profile requires the
bitemporal quartet on “every edge” while specifying none of the choices needed to make that
requirement interoperable:

- the relation-assertion class and its subject, predicate and object cardinalities;
- whether a direct RDF triple is also materialised;
- whether the quartet describes the assertion, the subject state, or both;
- how an identified-but-unresolved object differs from an absent object; and
- how open temporal bounds survive RDF conversion.

The provisional `ftro:Edge` / `ftro:Assertion` nodes prove one possible authoring pattern, not the
normative one. A v0.0.4 amendment should define a relation assertion explicitly and scope §4 to
those assertion nodes. It should not claim that every ordinary JSON-LD property is itself
bitemporal.

## 2. JSON null is not typed incompleteness

The v1.0 proposal made `validator` and `validator_version` “required and nullable” so null could
distinguish silence. That does not work at the RDF layer: JSON-LD null-valued properties disappear.
The same warning applies to unresolved edge objects and open time bounds.

The manifests now pair provisional null authoring markers with explicit state and reason fields,
and the Gate-1 checker requires a subject, relation, explicit object/literal state and reason on an
unresolved assertion. The amendment still needs a durable RDF-level representation—for example an
explicit resolution-state individual or controlled literal. Null alone must not carry meaning.

## 3. Conformance report and `TIMEEPH`

Profile §1 requires validator identity and version **in every conformance report** but does not
quite require that a report exist. All four manifests nevertheless need one to state the honest
`not_run` result, so `ConformanceReport` is a strong candidate, not a logically forced class.

`TIMEEPH IF99` is a declared timing-model parameter. The first manifests treated it as a new edge
because it fits neither `uses_ephemeris` nor `uses_reference_frame`. That is evidence for a
parameter-declaration representation; it is not yet evidence that `uses_time_ephemeris` should be
an ancestry edge. Do not freeze that edge from one `.par` file.

## 4. The frequency comparison was descriptive, not a required-field oracle

The original counts—13 of 21 edge classes and 28 of 41 node classes unused, plus 21 fields present
in all four manifests—came from whole-document key frequency. They do not establish:

- that a term is semantically exercised rather than merely named;
- that absence means inapplicable rather than provider evidence missing;
- that a field belongs on the same kind of entity in each domain; or
- that four occurrences justify a universal MUST.

The counts remain a historical inventory in `vocabulary-usage.json`; they are not a normative
coverage result. Do not promote the 21 fields wholesale and do not add an `exercised` boolean to
the profile yet. A future coverage report should classify each term use as instantiated,
unresolved-but-required, inapplicable to these legs, or untested.

## 5. What Gate 1 actually demonstrated

The exact frozen source population is now executable:

| Domain | Provider sources | FTRO source catalogs | Representation |
| --- | ---: | ---: | --- |
| optical | 3 | 0 | three graph entities reconciled to `identities.json` |
| pulsar | 5 | 1 | five graph entities; four-member PPTA concept reconciled to its pin report |
| VLBI | 1 | 1 | container plus five digest-keyed internal wrapper states reconciled to seven members |
| GNSS | 57 | 1 | six product-line concepts, five checked exemplars, and the frozen 57-entry source catalog |

An isolated export with no `data/` directory retrieved and matched all **66 provider sources** and
all **3 commit-pinned catalogs**. The report fingerprints the checker, manifests and frozen evidence
inputs and passes its freshness/content check. This demonstrates Gate 1’s source-location clause;
it is not general RO-Crate or profile validation.

Unresolved evidence remains unresolved: optical time-tag realisation, PPTA EOP identity, VLBI
downstream analysis/EOP contribution, and TT(BIPM2020) versus the shipped 2021 correction.

## 6. Conformance status

`roc-validator` 0.11.3 is obtainable, correcting v1.0’s contrary claim, but it supports RO-Crate
1.1 and 1.2 rather than the pinned 1.3 base. RDFLib parses all four JSON-LD documents. A temporary
non-normative 1.2 export fails. None of those facts demonstrates 1.3 conformance; the exact record
is `ro-crate-validation-v1.0.json`.

## 7. Amendment boundary

Do not apply v0.0.4 yet. Before amendment:

1. close Phase-0 C9’s documented-path defect;
2. freeze one executable audit manifest and obtain two qualifying clean runs from it;
3. decide the RDF-level unresolved/bitemporal assertion model; and
4. obtain a 1.3 validator or record an explicit, reviewed substitute conformance method.

The smallest defensible future amendment is the relation-assertion and explicit-state model plus a
profile context. Role-conditioned minimum records and vocabulary-coverage markers need more than
these four legs and should remain provisional.
