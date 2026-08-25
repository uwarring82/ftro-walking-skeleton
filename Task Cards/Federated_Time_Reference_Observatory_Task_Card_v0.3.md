# Task Card — Federated Time-Reference Observatory: Walking Skeleton

**Card ID:** FTRO-WS-001  
**Version:** 0.3  
**Date:** 2026-08-25  
**Status:** Ready to pick up; no domain schema frozen  
**Decision authority:** U. Warring  
**Implementation owner:** Unassigned  
**Estimated effort:** 10–17 focused working days for one technically experienced researcher, excluding domain-review latency; Phase 5 timeboxes apply whether reproductions succeed or fail  
**Supersedes:** FTRO-WS-001 v0.2

## 1. Mission

Build a small, working federation that lets an external researcher discover and retrieve public time-referenced measurements and reconstruct their reference-clock ancestry across scientific domains, without transferring custody to a central archive or requiring providers to adopt a common analysis framework.

The differentiating product is a **machine-readable, bitemporal reference-ancestry graph with a human-readable browser**. Dataset discovery, adapters and staging are necessary infrastructure, but are not by themselves the scientific contribution.

In plain language, the observatory should let a user answer:

1. What was measured, where and when?
2. Which oscillator, clock, transfer link, time scale, correction model and software made that timestamp meaningful?
3. Which parts of that chain are supported, inaccessible, unknown or disputed?
4. Can two selected records legitimately be placed on a common time axis, and with what achieved resolution?

## 2. Immediate objective

Construct a four-domain walking skeleton for a candidate common interval in early 2022:

1. pulsar timing — Parkes Pulsar Timing Array Data Release 3 (PPTA DR3);
2. VLBI — one public IVS session and its downstream Earth-orientation dependencies;
3. GNSS — the relevant IGS operational products;
4. optical clocks — the public ROCIT European-fibre subset.

For at least one selected record per domain, expose the complete reference and correction ancestry as far as public evidence permits. Every missing or disputed dependency must remain visible and typed.

The pilot tests federation, provenance, temporal alignment and reproducibility. It does not test a new physical hypothesis.

## 3. Fixed design commitments

- **Federation over migration.** Providers retain custody. The observatory stores identifiers, manifests, evidence, provenance, access instructions and optional compute-near-data hooks.
- **Reference ancestry first.** The pilot must attempt cross-domain ancestry reconstruction, not merely common search and download.
- **Stable primitives below, derived vocabulary above.** Providers contribute epochs, intervals, time scales, timestamp realisations, correction dependencies, availability dates and evidence. Framework-specific quantities such as causal loading or descriptive delay ratios are optional computed views.
- **No universal meaning of “raw.”** Processing levels are provider-declared advisory annotations. Transformations and their evidence are authoritative.
- **Typed incompleteness is data.** Missing, inaccessible, disputed or only asserted ancestry is retained and quantified.
- **Bitemporality is part of the graph core.** Both physical validity and federation knowledge history are queryable.
- **Human and machine views share one source of truth.** The browser is generated from the same graph and resolver outputs used by software; it is not a separately curated narrative.
- **The analysis layer remains separate.** The observatory provides discoverability, provenance, alignment certificates, validation and reproducible access. Searches for physical signatures, anomaly detection, cross-correlations, parameter inference and model comparison live in separately versioned analysis projects.
- **Nulls require reasons.** Empty overlap, missing evidence, incommensurability and failed resolution are distinct outcomes, not one undifferentiated null.
- **Nothing freezes before failure against real data.** Source, schema, execution, policy and rights deficiencies are citable pilot outputs.
- **Expansion is governed by scientific role.** A timestamp alone does not make a dataset an observatory collection.

## 4. Scope, data roles and admission

### 4.1 Four data roles

Every linked object must have one primary role in the use under consideration:

| Role | Meaning | Examples |
| --- | --- | --- |
| **Core measurement** | Precise timing is constitutive of the physical observable | optical-clock ratio, pulsar TOA, VLBI delay, GNSS clock product, seismic waveform |
| **Ancestry or correction artifact** | Used to create, time-reference, calibrate or correct a core measurement | clock-correction file, EOP series, ephemeris, tidal-loading model, leap-second table |
| **Contextual sensor** | Independent observation that may explain or challenge a core record but was not used to produce it | local weather, magnetometer, earthquake waveform, tide gauge, solar-wind record |
| **Analysis-only input** | Introduced by a separate scientific study to test a hypothesis | financial series, social data, a selected model prediction, unrelated contextual archive |

The same dataset may occupy different roles in different documented uses. A tidal model applied during VLBI processing is an ancestry artifact; a tide-gauge record added later to investigate a residual is a contextual sensor.

### 4.2 Relationship semantics

The graph and browser must distinguish at least:

- **time_referenced_to** — part of the timing ancestry;
- **calibrated_by** or **corrected_by** — applied in producing the record;
- **contextualized_by** — contemporaneous information with no causal claim;
- **analysed_with** — combined only by a separately versioned analysis.

Temporal or spatial proximity must never be displayed as evidence of causation.

### 4.3 Admission test

A future collection is eligible only if it supplies or explicitly lacks all of the following:

1. an observable with a defined measurement epoch or support interval;
2. a scientific reason why timing or time-dependent provenance matters;
3. a declared time-coordinate convention and timestamp realisation;
4. a versioned data product or resolvable custody endpoint;
5. a reconstructible or explicitly incomplete chain to local oscillators, transfer links, reference time scales, ephemerides and corrections as applicable;
6. evidence and rights metadata sufficient for a third party to assess reuse;
7. scientific utility independent of any particular observatory-hosted analysis.

Passing the test makes a collection eligible; it does not require ingestion. Expansion remains a governed prioritisation decision.

### 4.4 Expansion horizon

The pilot remains restricted to the four domains in §2. The following register guides later selection:

| Candidate family | Potential value | Default role | Provisional priority |
| --- | --- | --- | --- |
| UTC(k), GNSS clock estimates, fibre-link phase, TWSTFT, PTP/NTP and clock-operation logs | Reconstructs the reference backbone and identifies clock swaps, steers and dissemination faults | ancestry/core | highest |
| Satellite and lunar laser ranging; DORIS | Earth geometry, station motion, Earth rotation, gravity and solar-system dynamics | core | high |
| Superconducting/absolute gravimeters, strainmeters and tiltmeters | Gravitational potential, tides, loading, hydrology and crustal deformation | core/context | high |
| Seismic waveforms and distributed acoustic sensing | Propagating ground motion and mechanically induced sensor/link disturbances | core/context | high |
| Solid-Earth, ocean-loading and pole-tide models | Direct processing dependencies for geodesy and clock work | ancestry | immediate where used |
| Tide gauges, ocean-bottom pressure, hydrology and ocean observatories | Independent mass-loading and sea-level information | core/context | medium-high |
| Local meteorology and atmospheric products | Oscillator environment, atmospheric delay and loading | ancestry when applied; otherwise context | high |
| Geomagnetic, ionospheric, solar-wind and radiation monitors | GNSS/radio propagation, electromagnetic disturbance and electronics diagnostics | context | high |
| Gravitational-wave strain | Independent precisely timed transient channel | core | medium |
| Neutrino, gamma-ray, fast-radio-burst and cosmic-ray events | Multi-messenger coincidence tests | core/event context | medium |
| X-ray pulsars, eclipsing binaries, exoplanet transits, stellar oscillations and occultations | Independent astronomical timers and timing-model tests | core | medium |
| Planetary ranging, spacecraft Doppler and ephemerides | Solar-system dynamics and terrestrial-to-planetary timing | core/ancestry | medium |
| Power-grid frequency and phase | Continental network of coupled engineered oscillators | core candidate | exploratory; access risk |
| Telecom phase, data-centre timing and fibre sensing | Distributed-clock and propagation behaviour | core candidate | exploratory; access risk |
| Laboratory cavities, combs, atom interferometers, magnetometers and quantum gravimeters | Complementary sensitivities to fields, constants and local environment | core | scientifically high; release risk |
| Financial, traffic, biological or social time series | Possible external controls or timestamp-infrastructure studies | analysis-only by default | excluded from collection scope unless separately justified |

Representative public infrastructures include the [International Laser Ranging Service](https://ilrs.gsfc.nasa.gov/), [IGETS gravimetry archive](https://isdc.gfz.de/igets-data-base/), [FDSN seismic sources](https://ds.iris.edu/data/sources.htm), [PSMSL sea-level archive](https://psmsl.org/), [INTERMAGNET](https://intermagnet.org/), [NASA OMNI](https://omniweb.gsfc.nasa.gov/), [ESA Swarm](https://earth.esa.int/eogateway/missions/swarm/data), the [Gravitational Wave Open Science Center](https://gwosc.org/), [NASA GCN](https://gcn.nasa.gov/) and the [NICER archive](https://heasarc.gsfc.nasa.gov/docs/nicer/nicer_archive.html).

## 5. Pilot datasets and current evidence

### 5.1 Optical clocks

- **Dataset:** *Dataset for “Coordinated international comparisons between optical clocks connected via fiber and satellite links”*, Zenodo record 17107693, v1.
- **DOI:** <https://doi.org/10.5281/zenodo.17107693>
- **Actual archive scope:** European fibre comparisons only; eight optical clocks in four countries. The associated publication covers the larger ten-clock, six-country fibre-and-satellite campaign and must not be conflated with this archive.
- **Coverage:** MJD 59630–59675, corresponding to 2022-02-20 through 2022-04-06.
- **Archive:** ROCIT campaign results.zip, 83.5 MB.
- **Recorded MD5:** 4ae290f559c90b462991286c933a1147.
- **Source-data licence:** CC BY 4.0, as declared by the Zenodo record.
- **Record contents:** one-second fractional-frequency ratios, MJD time tags, validity flags, YAML metadata and processing code.
- **Format evidence:** [`INRIM/optical-link-data-format`](https://github.com/INRIM/optical-link-data-format) at commit `689bda77000fec52c401bc0c9c3664d1dd534ecb`; pinned `README.md` SHA-256 `cf93ae7a8f934944230e8555941d9d1e1afac9fa59d3a6d15bacd7befbfcee98`.
- **Processing evidence:** [`INRIM/tintervals`](https://github.com/INRIM/tintervals) at commit `2064db12777df78bc87f68f7710a47176192c2e1`.
- **Documented validity flags:** `0 = invalid`, `1 = valid but experimental`, `2 = valid`. The archive must be checked for conformance; an undeclared value or inconsistent use becomes a source-evidence deficiency.
- **Timestamp-ancestry question:** identify what physically realises the one-second MJD time tags. Extract the declared `ref_osc`, `interval`, `lag` and `weighting` fields; then seek the station time scale, maser or other clock and any UTC(k)/BIPM relationship supporting those tags. The fibre ratio chain alone does not answer this question.
- **Required action:** retrieve the archive, verify its checksum and licence, enumerate every comparison and its actual validity mask, and select one or more records that intersect the candidate window.

References: <https://zenodo.org/records/17107693> and associated publication <https://doi.org/10.1364/OPTICA.561754>

### 5.2 Pulsar timing

- **Dataset:** PPTA DR3.
- **Coverage:** MJD 53040–59640.
- **Public products:** calibrated pulse profiles, flux-density dynamic spectra, times of arrival and initial timing models for 32 pulsars.
- **Cadence:** typically about three weeks; campaign-range overlap therefore does not imply an observation in a short window.
- **Nominated anchor:** PSR J0437−4715, subject to inspection of its actual records within the candidate interval.
- **Known limitation:** the candidate interval lies at the release’s terminal edge.
- **Required action:** pin the exact DR3 files, timing model, observatory clock-correction files, ephemeris and Earth-orientation inputs used for the selected observation.
- **Assessment requirement:** timing-model applicability is not a manifest fact. Record it as a versioned ApplicabilityAssessment with assessor or software, method, evidence, applicable interval and outcome.

Reference: <https://www.cambridge.org/core/journals/publications-of-the-astronomical-society-of-australia/article/parkes-pulsar-timing-array-third-data-release/0871479709CE59FD647EF794AFCF3960>

### 5.3 GNSS

- **Target:** IGS products applicable to the candidate interval.
- **Policy test A — contemporaneous operational product:** expected to select an IGb14-era final product for February 2022; the exact artifact remains to be pinned.
- **Policy test B — latest homogeneous reprocessing:** expected to return null because repro3 covers 1994–2020 and does not cover the candidate interval.
- **Lineage ledger item:** IGS20 became operational at GPS week 2238, beginning 2022-11-27.
- **Required action:** identify the exact clock, orbit, bias, attitude and related artifacts required by the selected chains, with product identifiers, availability dates, checksums and reference-frame metadata.

References: <https://igs.org/news/igs20/> and <https://lists.igs.org/pipermail/igsmail/2022/008244.html>

### 5.4 VLBI

- **Target:** one publicly retrievable IVS session whose measurement support intersects, or is maximally relevant to, the candidate interval and whose contribution to an IERS Earth-orientation product can be evidenced.
- **Current state:** exact session, vgosDB version, analysis-centre product and downstream EOP series not yet selected.
- **Required action:** choose and pin these objects before the manifest vocabulary is frozen.

## 6. Candidate temporal window and fallback rule

- **Candidate range:** MJD 59630–59640, corresponding to 2022-02-20 through 2022-03-02.
- **Actual support:** must be computed from per-record observation epochs, integration/support intervals, optical validity masks and product validity intervals.
- **No inference from campaign boundaries:** a source belongs to the common window only when its actual data support intersects it.
- **Fallback:** if no four-domain observational intersection exists, do not widen the interval silently and do not substitute the March 2023 optical dataset. Continue the object as an ancestry and federation skeleton while reporting simultaneity as not demonstrated.

## 7. Required top-level deliverables

### A. Access Charter v0.1

The charter must define:

- mission centred on exposing cross-domain reference ancestry;
- federation and custody principles;
- provider and user rights;
- licences for FTRO-authored outputs: CC BY 4.0 for manifests, graph metadata, certificates, ledgers and documentation; Apache-2.0 for browser and resolver software; provider content retains its own licence and is never relicensed by inclusion;
- public, registered, mediated and restricted access modes;
- citation flow, provider credit, service credit and reduced support burden as participation incentives;
- separation between observatory services and scientific analysis;
- advisory status of provider processing levels;
- versioning, supersession, withdrawal, correction and contestation rules;
- rights-conflict and pointer-only states;
- independent reporting of platform conformance and scientific demonstration outcomes;
- language stating that insufficient public evidence is a valid result but does not count as a demonstrated shared dependency;
- governance sequence: public walking skeleton first; engagement with GGOS, IERS, BIPM and providers after a working object exists.

### B. FTRO Reference-Ancestry Graph Profile v0.0.1

The profile must define the minimum record, node and edge vocabulary, bitemporal semantics, evidence model, verification activities, contestation, policy objects, alignment outcomes, rights fields and resolver contract.

### C. Walking Skeleton v0.1

The skeleton must contain the seven outputs specified in §8 and execute against the four public pilot legs.

## 8. Seven walking-skeleton outputs

1. **Four hand-authored manifests.** One RO-Crate 1.3 manifest conforming to the FTRO profile per domain, based on real source products rather than an abstract ontology exercise.
2. **Pinned retrieval and validation procedures.** Fetch instructions or scripts, identifiers, rights, sizes and checksums; no hidden local files or undocumented manual steps.
3. **Bitemporal provenance graph with a read-only human browser.** Machine-readable JSON-LD plus a static visual interface generated from the same graph, with restorable URL-fragment state.
4. **Versioned policy objects and resolver.** Executable or declarative policies with reproducible fixtures, including the IGS operational-selection and honest-null cases.
5. **Cold-reproduction reports.** An outsider reproduces one published or provider-documented result per domain using only manifests and cited evidence. These are conformance tests, not a general analysis service.
6. **Alignment certificate.** A typed report of source time scales, transformations, correction versions, support intersection, uncertainty or achieved resolution and unresolved limitations.
7. **Classified deficiency log.** A versioned, citable account of source-evidence, schema, execution, policy and rights failures encountered from Phase 0 onward.

## 9. Standards and serialization

### 9.1 Normative base

- **Base specification:** [RO-Crate Metadata Specification 1.3](https://w3id.org/ro/crate/1.3), Recommendation published 2026-06-22.
- **Domain profile:** FTRO Reference-Ancestry Graph Profile v0.0.1.
- Each manifest must declare conformance to both the pinned base and the FTRO profile.
- “RO-Crate-compatible” means that the crate validates against the pinned base specification and satisfies the FTRO profile constraints. Merely using similar JSON-LD conventions is insufficient.

### 9.2 Extensions and compatibility

- Bitemporal, evidence, contestation and domain terms may be explicit FTRO profile extensions.
- A schema limitation encountered while expressing these terms is logged rather than concealed.
- An RO-Crate 1.2 export may be tested for tool compatibility because 1.3 is recent, but it is not a second normative base.
- The exact validator and its version must be recorded in every conformance report.

## 10. Minimum record fields

Each dataset, product or evidence manifest must record, where applicable:

- concept-level persistent identifier for a continuing series or product line, plus title, provider, custody endpoint and access class;
- snapshot-level persistent identifier where supplied, immutable version, generation time, release time, first availability time, checksum and supersession relation;
- when a provider supplies no immutable snapshot identifier, an FTRO snapshot identity composed from the concept identifier, retrieval time, byte checksum and recorded retrieval procedure;
- data rights, metadata rights, evidence-retention rights and redistribution mode;
- observation epoch and support interval;
- sampling interval, integration interval, estimator window and validity mask as distinct fields;
- coordinate-time scale, timestamp format and physical realisation of the timestamp;
- station, instrument, oscillator, clock and reference-scale identifiers;
- transfer channel and calibration/correction artifacts;
- ephemeris, Earth-orientation product, tide/loading model and reference-frame identifiers and versions;
- processing software, configuration, template/model and execution environment;
- uncertainty representation and quality flags as supplied by the provider;
- evidence artifact for every asserted dependency;
- valid-time interval and knowledge-time interval;
- provider-declared processing level, if any, marked advisory;
- evidence accessibility, verification activities and open contestation;
- relevant deficiency entries and applicability assessments.

No contributor is required to supply Lambda, delta or any physics interpretation.

## 11. Graph profile

### 11.1 Candidate node classes

- series concept, immutable snapshot, collection, release, dataset, file, segment, record and observation;
- station, instrument, oscillator, clock and time-scale realisation;
- transfer link, comparison, calibration and correction artifact;
- ephemeris, Earth-orientation series, tide/loading model, reference frame and coordinate convention;
- environmental or contextual sensor series;
- software, configuration, model, template, workflow, environment lock and execution;
- publication, evidence artifact, assertion, verification activity, applicability assessment and contestation;
- policy, resolver execution, alignment certificate and deficiency entry.

Graph roots need not be UTC(k). A chain may legitimately terminate at a free-running local oscillator, a direct optical ratio, a proper-time model, an institutional assertion, or an unresolved or opaque dependency.

Evidence artifacts have ancestry too. A TEMPO2 correction file, ephemeris or provider manifest is not treated as an unquestioned terminal simply because it comes from an authoritative repository.

### 11.2 Candidate edge classes

- derived_from
- snapshot_of
- contributes_to
- generated_by
- observed_by
- time_referenced_to
- transferred_via
- calibrated_by
- corrected_by
- contextualized_by
- analysed_with
- uses_ephemeris
- uses_eop
- uses_tide_model
- uses_reference_frame
- supersedes
- evidenced_by
- evaluated_by
- selected_by_policy
- contests

### 11.3 Bitemporal requirements

Every mutable node assertion and every edge carries:

- **valid_from, valid_to:** when the relation applied to the physical record or product;
- **known_from, known_to:** when the federation held that assertion.

Release time, file availability time and observation time remain separate primitives. For a fixed knowledge date, the materialised derivation subgraph must be acyclic; bitemporality represents revisions but does not legitimise circular derivation.

Living series use two-level identity:

- **concept identity** names the continuing series or product line;
- **snapshot identity** names the immutable state actually consumed, using a provider version or PID where available and otherwise an FTRO retrieval-time-plus-checksum identity.

Derivation and acyclicity are evaluated at snapshot granularity. A series-concept match can show that two chains depend on the same continuing resource, but it cannot establish that they consumed the same state. For products such as IERS C04, an IVS session may contribute to a later snapshot while a VLBI analysis consumes an earlier a-priori snapshot; those are distinct directed relations, not a cycle. Every living artifact used in a reproduction must therefore be materialised and pinned before execution.

### 11.4 Evidence, verification and contestation

Do not encode “asserted,” “verified,” “contested,” “opaque” and “unresolved” as one mutually exclusive status list.

Primitive fields are:

- **evidence_state ∈ {resolvable, opaque, unresolved}**
  - resolvable: an identified evidence artifact can be retrieved and inspected under the recorded access conditions;
  - opaque: an artifact is identified but cannot be inspected sufficiently;
  - unresolved: no specific evidence artifact has been identified.
- **VerificationActivity.result ∈ {supports, contradicts, indeterminate}**
- **contestation_state ∈ {none, open, resolved}**

Human-readable labels such as “asserted,” “verified” and “contested” are derived views. Lineage completeness is calculated by traversal and is not another stored state.

An assertion is displayed as verified only if:

1. its evidence is resolvable and pinned by identifier, version and checksum where available;
2. a named, versioned verification procedure evaluates the relation;
3. that activity records a supporting result, execution time, agent or software and output;
4. the verification activity is itself resolvable within the federation.

A supported claim may still be openly contested by a different assertion.

**Worked example.**

| Situation | Evidence state | Verification | Contestation |
| --- | --- | --- | --- |
| Exact Parkes clock file pinned but not inspected | resolvable | none | none |
| Versioned procedure parses the file and supports the stated correction | resolvable | supports | none |
| Named file exists but access or content is insufficient | opaque | indeterminate or none | none |
| No exact correction file can be identified | unresolved | none | none |
| Two evidence artifacts imply incompatible corrections | resolvable or opaque per artifact | recorded separately | open |

**Pilot contestation fixture.** The associated campaign publication reports that March 2022 GNSS-derived ratios involving INRIM Yb disagreed with the optical-link result by approximately `4 × 10^-16`; the authors judged the INRIM GNSS ratios unreliable and left the cause unidentified. Represent this as separately evidenced measurement assertions plus an open `contests` relation to the publication node. The fibre-only Zenodo archive does not itself evidence the GNSS branch, so the graph must cross the archive boundary explicitly rather than manufacture a GNSS node inside that dataset.

### 11.5 Granularity and query semantics

- Bulk samples remain in provider formats. The graph does not create a node for every one-second optical sample, seismogram datum or market tick.
- Graph segments are introduced when ancestry, calibration, validity, access or evidence changes.
- Canonical valid-time and “as known on date” query fixtures are normative.
- JSON-LD is the exchange representation, not a commitment to SPARQL or any particular database.
- Pilot acceptance requires deterministic query results on the pilot graph, not a general scalability benchmark.

### 11.6 Rights model

Track separately:

- data_rights;
- metadata_rights;
- evidence_retention_rights;
- redistribution_mode ∈ {copy_permitted, metadata_only, link_only, restricted, conflicting, unknown}.

Unknown or conflicting rights default to pointer-only registration pending provider-specific review. Federation does not imply a right to redistribute source bytes or provider metadata.

## 12. Human-browser demonstrator

The pilot includes a small, read-only browser rather than a full production portal. Its implementation posture is a **static site generated from the versioned graph JSON and resolver fixtures**. No pilot backend, live graph service or provider-side query translator is required.

### 12.1 Required views

1. **Discovery view:** search and filter by interval, domain, station, instrument, signal type, access and evidence state.
2. **Timeline and map:** show actual support intervals and locations, not merely campaign boundaries.
3. **Ancestry explorer:** follow a record through oscillators, transfer links, time scales, corrections, models, software and evidence.
4. **Comparison view:** compare two records, distinguish snapshot identity from series-concept identity with quantified snapshot divergence, and show whether their supports overlap.
5. **Knowledge-time view:** an “as known on this date” control that materialises the bitemporal graph under the selected date and policy.
6. **Alignment view:** show transformations and one typed alignment outcome from §14.
7. **Deficiency view:** expose unresolved, opaque, contradicted and contested dependencies without hiding them behind a completeness score.

### 12.2 Visual semantics

- Supported connection: solid line plus text label.
- Assertion not yet checked: dashed line plus label.
- Opaque evidence: lock marker.
- Unresolved evidence: visibly open endpoint.
- Open contestation: branching warning with access to the competing assertions.

Colour may supplement but never carry status alone. Dense paths must use progressive disclosure rather than a single “spaghetti graph.”

### 12.3 Reproducibility

- Every browser state has a stable, shareable query reference encoded as a URL fragment over non-sensitive state; opening the URL must reconstruct the same view against the cited graph and policy versions.
- Every view can export the underlying graph fragment and policy version.
- No manually authored browser statement may contradict or supplement the graph invisibly.
- An outsider must be able to answer without reading JSON:
  1. what records exist for an interval;
  2. what each record depends on;
  3. what is supported, missing, inaccessible or disputed.

## 13. Policy objects and resolver

### 13.1 Resolver contract

~~~text
resolve(subject, valid_interval, as_of, policy_pid)
  -> selected_artifact_pid | null
     + reason_code
     + evidence
     + policy_pid
     + resolver_version
~~~

### 13.2 Policy requirements

Every policy P is a first-class, citable graph object with:

- persistent identifier and immutable version;
- issuer and publication date;
- validity and knowledge intervals;
- human-readable rule;
- executable rule or implementation hash when applicable;
- eligible product classes and tie-breaking rules;
- supersession relation;
- tests demonstrating positive selection, competing selection and null behaviour.

Provider recommendations are never mutable labels. A changed recommendation produces a new policy version.

### 13.3 Mandatory resolver fixtures

- “Best operational product for epoch t as known on date d.”
- “Latest homogeneous reprocessing covering interval I as known on date d.”
- A null caused by absent temporal coverage.
- Two successive policies returning different products for the same epoch without altering historical results.
- A product superseded after the original analysis date.

## 14. Time alignment work package

### 14.1 Required work

- Extract each source’s native time coordinate and timestamp realisation.
- Preserve primitive epochs and support intervals before conversion.
- Pin all transformations, leap-second tables, station-clock corrections, ephemerides, EOP series, reference-frame products, tide/loading models and software versions.
- Ingest existing TEMPO2/IPTA clock-correction files as evidence artifacts; do not transcribe their content into unsupported prose. Pin the [`IPTA/pulsar-clock-corrections`](https://github.com/ipta/pulsar-clock-corrections) repository at commit `36dc139a150efde056aa32fa13deac856a7a679d` and `T2runtime/clock/gps2utc.clk` at SHA-256 `7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a`. Its rendered page is useful discovery metadata but is a living view, not a reproducible identity. Parkes-specific and TT(BIPM) legs remain separate until their exact artifacts are pinned.
- Create an ApplicabilityAssessment for whether the Parkes receiver configuration tracked the GPS Combined Clock (`C0`) or the almanac-steered realisation (`C0′`) during the selected interval. The correction choice depends on receiver configuration and evidence; it is not inferable from the correction filename alone.
- Compute overlap from actual supports and masks.
- Produce an alignment certificate containing transformations, uncertainty contributions, achieved resolution when calculable, excluded records, gaps and unresolved dependencies.
- Do not promise nanosecond alignment or any fixed resolution before the certificate is calculated.

### 14.2 Typed certificate outcomes

Every certificate emits exactly one primary status:

| Status | Meaning |
| --- | --- |
| **computed** | A common representation and achieved resolution were calculated |
| **partial** | Only a declared subset could be aligned |
| **no_common_support** | The actual temporal-support intersection is empty |
| **indeterminate** | Alignment may be possible, but required evidence or corrections are missing or opaque |
| **unrepresentable** | No defensible common coordinate or uncertainty representation has been defined |

Only computed, and where meaningful partial, carries a numerical achieved resolution. A null value must always be accompanied by its status and reason.

## 15. Shared ancestry and outcome accounting

### 15.1 Shared-node test

The differentiating scientific test seeks a shared dependency in two independently constructed domain ancestries. Because the likeliest dependencies are living series, report two grades rather than collapsing identity:

1. **Snapshot-level demonstration (stronger):** both chains evidence the same immutable snapshot PID/version and checksum.
2. **Series-level demonstration:** both chains evidence the same concept PID but consumed different or incompletely identified snapshots. Quantify snapshot divergence using retrieval or generation time, coverage, version, checksum and any material parameter or content differences. Never display this grade as snapshot identity.

Candidate paths include:

- IVS session → IERS EOP series → pulsar barycentring;
- IGS product → GNSS chain and, only if archived evidence supports it, an optical-comparison chain;
- BIPM time-scale realisation → more than one domain.

No candidate is credited in advance. The public ROCIT record is fibre-only, so an IGS node must not be inserted merely because the wider campaign included GNSS comparisons. Its relevant cross-domain ancestry question is instead the time-tag chain: which local oscillator or station time scale realises the one-second MJD tags, and whether that chain reaches an evidenced UTC(k) or BIPM-related node.

The exact EOP artifact used by PPTA must be recovered from timing configurations. **Pre-registered expectation:** this node may terminate at a bundled or regenerated artifact whose ancestry to a particular IERS C04 snapshot is opaque. If so, report the opacity as observed; do not silently substitute a current C04 snapshot. The two-level identity and bitemporal rules in §11.3 distinguish an IVS session contributing to a later C04 state from an analysis consuming an earlier a-priori state.

### 15.2 Separate outcome axes

Report independently:

- **platform_conformance ∈ {pass, partial, fail}**
- **shared_ancestry_demonstration ∈ {snapshot_demonstrated, series_demonstrated_with_divergence, not_demonstrated, indeterminate, contradicted}**

Evidence opacity may therefore yield platform conformance pass or partial while shared ancestry remains indeterminate. A series-level match is a successful but weaker result and must carry its divergence report. No match, or inability to evidence one, remains a valid scientific result of the skeleton rather than a platform failure.

## 16. Cold-reproduction protocol

Before any reproduction is executed, the Phase-0 selection note must pre-register one target value and a numerical or categorical acceptance tolerance for each domain. A changed target or tolerance requires a versioned amendment; if changed after the first result is inspected, it is labelled post hoc and cannot satisfy the original acceptance test.

For each domain:

1. nominate one modest published or provider-documented result;
2. start in an ephemeral clean environment with no unlisted local domain knowledge or files;
3. discover and retrieve all inputs solely through the manifest;
4. instantiate the recorded software environment;
5. execute the pinned procedure;
6. compare the output against the nominated value with a declared tolerance;
7. record missing steps, manual interventions, ambiguities and failures;
8. emit a signed or checksummed reproduction report.

Each reproduction must include a machine-readable environment lock: an OCI image digest, Nix or Conda lock, or equivalent, plus architecture, operating system, locale, time zone, source revision and build options where relevant. A container is recommended but not mandatory where licensing or architecture makes it unsuitable.

The first cold run is timeboxed to one focused working day per domain. At the boundary, a complete failure report—target, tolerance, environment, last successful step, blocker, evidence and remaining work—is a valid Phase-5 exit. Success is not assumed by the 10–17-day estimate. Targets should test ancestry and reproducibility, not maximise scientific novelty.

## 17. Classified deficiency log

The ledger opens in Phase 0, before the FTRO domain profile is frozen.

Each entry contains:

- stable entry identifier and version;
- deficiency_class ∈ {source_evidence, schema, execution, policy, rights};
- dataset and domain;
- failed representation, query, retrieval, interpretation or reproduction step;
- known real-world fact or required evidence;
- evidence;
- severity and downstream impact;
- temporary workaround, if any;
- proposed response;
- disposition ∈ {open, accepted, rejected, deferred, resolved};
- links to the manifest, profile, policy and software versions in which the issue occurred.

Examples:

- an archive flag outside the pinned optical format’s documented `0/1/2` vocabulary, or inconsistent use of those flags, begins as source_evidence rather than automatically schema;
- inability to express a resolved flag transition is schema;
- missing executable environment information is execution;
- ambiguous “provider-recommended” selection is policy;
- inability to identify the immutable snapshot of a living series is source_evidence, while inability to represent concept/snapshot identity is schema;
- incompatible metadata and data licences are rights.

The ledger is distinct from incomplete ancestry. The former records a limitation encountered by the federation; the latter records incomplete knowledge about a physical or documentary chain.

## 18. Acceptance criteria

### 18.1 Platform conformance

- [ ] All four public source legs have pinned identifiers, versions, rights, access routes and checksums where available.
- [ ] FTRO-authored metadata/documents and software declare the licences in §7A without overriding provider rights.
- [ ] Four RO-Crate 1.3 manifests conform to the pinned FTRO profile or emit explicit conformance failures.
- [ ] Every dependency assertion has valid time, knowledge time and evidence state.
- [ ] Every displayed verification points to a resolvable VerificationActivity.
- [ ] Open contestation remains representable alongside supporting evidence.
- [ ] The resolver reproduces historical decisions under a cited policy version.
- [ ] The IGS operational policy returns an appropriate 2022 product.
- [ ] The homogeneous-reprocessing policy returns an explained null for the same interval.
- [ ] Actual temporal support is computed from records and validity masks.
- [ ] The alignment certificate emits a typed status and, where calculable, achieved resolution.
- [ ] One cold reproduction per domain succeeds or emits a complete failure report.
- [ ] Four targets and tolerances were pre-registered before execution, with any post-result amendment visibly labelled post hoc.
- [ ] Each reproduction has a machine-readable environment specification.
- [ ] The static human browser answers the three questions in §12.3 from the graph alone and restores a cited view from its URL fragment.
- [ ] No required step depends on an undocumented local file, credential or manual convention.
- [ ] Every encountered deficiency appears in the classified ledger.
- [ ] No physics-search or anomaly-detection claim is presented as an observatory result.

### 18.2 Differentiating scientific criterion

- [ ] At least one shared ancestry dependency is evidenced in two independently constructed domains and graded as either snapshot_demonstrated or series_demonstrated_with_divergence.
- [ ] Any series-level result includes the two consumed snapshot identities and a quantified divergence report.

If neither grade is met, report not_demonstrated, indeterminate or contradicted as appropriate. Do not convert concept-level similarity, evidence opacity or a current-series substitution into snapshot identity.

## 19. Non-goals for this card

- Building a central data lake.
- Building a production-scale portal.
- Defining a universal raw-data hierarchy.
- Establishing a new physical signature or cross-domain correlation.
- Providing real-time steering or two-way clock verification.
- Standardising provider-internal formats.
- Promising a universal timing precision.
- Forming a consortium before the public skeleton exists.
- Admitting additional collections during the four-domain pilot.
- Treating every timestamped dataset as observatory material.
- Ingesting financial or other social time series absent a separately justified timestamp-science question.

## 20. Risks and prescribed responses

| Risk | Response |
| --- | --- |
| No true four-domain temporal intersection | Emit no_common_support; retain the ancestry skeleton; do not widen silently |
| Domains have no defensible common uncertainty representation | Emit unrepresentable rather than a numerical or generic null |
| Optical archive flags conflict with the pinned `0/1/2` format semantics | Open a Phase-0 source_evidence deficiency; preserve source values and do not coerce them |
| Sparse PPTA sampling yields no observation in the interval | Record failure; retain the terminal-edge test; assess a different collection only through a new selection decision |
| Timing-model applicability requires judgment | Create an evidenced ApplicabilityAssessment rather than a bare manifest statement |
| Exact EOP, ephemeris or correction version cannot be recovered | Mark evidence opaque or unresolved; do not substitute a modern product |
| Shared living series but non-identical or unknown snapshots | Report series_demonstrated_with_divergence only when the common concept identity is evidenced; otherwise indeterminate or not demonstrated |
| Provider “best product” changes | Resolve under the cited historical policy; never overwrite the policy object |
| Processing-level dispute | Preserve provider annotation and explicit transformations; do not adjudicate a universal level |
| Apparent provenance cycle | Materialise at snapshot granularity and a fixed knowledge date; distinguish consumed a-priori states from later contributed states and reject genuine circular derivation |
| Public artifact disappears or changes | Retain PID, retrieval time, checksum, custody status and typed evidence state |
| Rights are unknown or conflicting | Use pointer-only registration pending review |
| RO-Crate 1.3 tooling lags | Record validator versions and test a non-normative 1.2 export without weakening the 1.3 target |
| Browser implies certainty or causality | Use explicit labels, non-colour cues and distinct ancestry/context/analysis edges |
| Bitemporal graph becomes large | Keep samples external and segment only where provenance or validity changes |
| Evidence artifact has undocumented ancestry | Continue graph traversal or terminate explicitly as opaque/unresolved |
| Cold reproduction exceeds its timebox | Stop cleanly and publish the complete failure report; do not extend silently or redefine the tolerance |

## 21. Suggested execution sequence

### Phase 0 — Evidence lock, bootstrap ledger and selection (1–2 days)

- [ ] Open decision, source and classified deficiency ledgers.
- [ ] Retrieve Zenodo 17107693 and verify the recorded checksum.
- [ ] Record the Zenodo CC BY 4.0 declaration and pin the optical format and `tintervals` commits listed in §5.1.
- [ ] Parse optical metadata and flags against the documented `0/1/2` semantics; record any deviation before interpreting it.
- [ ] Start the optical time-tag ancestry trace from `ref_osc`, `interval`, `lag` and `weighting` toward the actual station time-scale realisation.
- [ ] Pin exact PPTA files and inspect J0437−4715 support near MJD 59630–59640.
- [ ] Create a provisional PPTA ApplicabilityAssessment rather than an unattributed model-validity judgment.
- [ ] Pin the IPTA correction repository and `gps2utc.clk` snapshot in §14; create the separate `C0`/`C0′` receiver ApplicabilityAssessment.
- [ ] Choose one IVS session and downstream EOP product.
- [ ] Choose exact IGS operational artifacts for the interval.
- [ ] Pre-register one cold-reproduction target and tolerance per domain in the selection note.
- [ ] Record the expectation that the PPTA EOP chain may be opaque at exact C04-snapshot granularity; treat it as a prediction to test, not a supplied fact.
- [ ] Record rights separately for source data, metadata and retained evidence.
- [ ] Apply CC BY 4.0 to FTRO-authored metadata/documents and Apache-2.0 to FTRO software while preserving all provider licences.

**Gate 0:** four concrete product sets selected or explicitly missing; four reproduction targets and tolerances locked; source and FTRO rights recorded; first deficiency entries classified.

### Phase 1 — Reality-first manifests (2–3 days)

- [ ] Hand-author one RO-Crate 1.3 manifest per domain.
- [ ] Declare the FTRO profile and validator version.
- [ ] Test retrieval in a clean environment.
- [ ] Record every field and real-world transition that does not fit cleanly.

**Gate 1:** no FTRO term is frozen; all four manifests can locate source bytes or report the access failure.

### Phase 2 — Graph profile and ancestry extraction (2–3 days)

- [ ] Implement the minimum node and edge vocabulary.
- [ ] Add valid and knowledge times.
- [ ] Materialise concept and snapshot identities for every living series used by a chain.
- [ ] Assign evidence_state to every dependency assertion.
- [ ] Represent verification activities and contestation separately.
- [ ] Instantiate the March 2022 INRIM fibre/GNSS discrepancy as the real open-contestation fixture, with the publication as evidence for the GNSS-side assertion.
- [ ] Ingest clock-correction, ephemeris, EOP, tide/loading and product-lineage evidence.
- [ ] Materialise four segmented ancestry chains.
- [ ] Create canonical valid-time and knowledge-time query fixtures.

**Gate 2:** every dependency has an evidence state; every verification and contest is explicit; no dependency is silently completed.

### Phase 3 — Policy resolver and support intersection (1–2 days)

- [ ] Create and version the two IGS policy objects.
- [ ] Implement the resolver contract and fixtures.
- [ ] Compute the actual candidate-window intersection.
- [ ] Generate a provisional typed alignment certificate.

**Gate 3:** resolver outputs are reproducible, including reasoned nulls; simultaneity and alignment status are known.

### Phase 4 — Human-browser demonstrator (1–2 days)

- [ ] Generate a static site from the versioned graph JSON and resolver fixtures.
- [ ] Implement discovery, timeline/map, ancestry and comparison views.
- [ ] Add the knowledge-date control and policy display.
- [ ] Encode evidence and contestation accessibly.
- [ ] Export the underlying graph fragment from every view.
- [ ] Encode non-sensitive view state in URL fragments and test deterministic restoration.

**Gate 4:** an outsider can answer the three questions in §12.3 without reading JSON.

### Phase 5 — Cold reproduction and deficiency consolidation (2–4 days)

- [ ] Load, without changing, the Phase-0 target and tolerance per domain.
- [ ] Define and lock each execution environment.
- [ ] Run all four from clean environments, timeboxed to one focused working day per domain.
- [ ] At each timebox, record success or emit the complete failure report defined in §16.
- [ ] Complete the alignment certificate.
- [ ] Consolidate the classified deficiency log.
- [ ] Test the shared-node criterion.
- [ ] Report platform conformance separately from shared-ancestry demonstration.

**Gate 5:** an uninvolved reader can reproduce the successes and understand every timeboxed failure from the published package alone; no exit depends on all four runs succeeding.

### Phase 6 — Freeze decision (0.5–1 day)

- [ ] Review all deficiency classes before accepting any FTRO profile field as stable.
- [ ] Revise the Access Charter and Graph Profile.
- [ ] Decide whether evidence supports a v0.1 public walking skeleton.
- [ ] Only then prepare engagement material for GGOS, IERS, BIPM and data providers.

## 22. Restart instructions

When this card is picked up again, begin with Phase 0 rather than revisiting the observatory’s broad scientific motivation or expansion catalogue.

The first work session should produce:

1. a locally verified copy or documented retrieval of Zenodo 17107693;
2. a table of actual optical validity intervals inside MJD 59630–59640 checked against the pinned `0/1/2` flag semantics;
3. the PPTA observation list for the same interval, especially J0437−4715;
4. a provisional PPTA timing-model ApplicabilityAssessment and a separate `C0`/`C0′` receiver ApplicabilityAssessment;
5. a selection note naming the exact IVS session and IGS artifacts and pre-registering one reproduction target and tolerance per domain;
6. a timestamp-ancestry note for the optical MJD tags, beginning with the YAML timing and `ref_osc` fields;
7. concept and snapshot identities for the pinned optical-format, `tintervals` and `gps2utc.clk` evidence artifacts;
8. the first classified deficiency and rights entries, including the FTRO output licences.

Do not begin consortium formation, production portal development, additional-domain ingestion or physics analysis until these outputs exist.

## 23. Decision log

| Decision | v0.3 status |
| --- | --- |
| Federation over central migration | retained |
| Reference-clock ancestry as headline deliverable | retained |
| Analysis layer separate from observatory | retained |
| Human browser generated from the graph | adopted |
| Pilot browser implemented as a static graph-generated site with URL-fragment state | adopted |
| Bitemporality in graph core | retained |
| Policy P as versioned, citable object | retained |
| Processing levels advisory and provider-declared | retained |
| Typed incompleteness as scientific output | retained and decomposed into primitive fields |
| Verification requires evidence plus recorded validation | adopted |
| Contestation independent of verification | adopted |
| Lineage completeness derived rather than stored | adopted |
| Typed alignment outcomes including unrepresentable | adopted |
| Deficiency ledger begins in Phase 0 and is classified | adopted |
| RO-Crate 1.3 plus FTRO profile as normative serialization | adopted |
| Environment lock required for cold reproduction | adopted |
| Data, metadata and evidence rights separated | adopted |
| FTRO metadata/documents CC BY 4.0; FTRO software Apache-2.0; provider rights preserved | adopted |
| Candidate interval MJD 59630–59640 | retained as test interval, not guaranteed overlap |
| Optical leg restricted to Zenodo 17107693 fibre subset | retained |
| Optical format and processing evidence pinned; three-state validity semantics adopted from source specification | adopted |
| Optical cross-domain ancestry starts from the MJD time-tag realisation, not an assumed GNSS ratio chain | adopted |
| Simultaneity failure reported, never repaired silently | retained |
| Platform conformance separated from shared-ancestry demonstration | adopted |
| Shared-node requirement | refined into snapshot-level and series-level-with-divergence grades |
| Living series use separate concept and immutable snapshot identities | adopted |
| Acyclicity evaluated at snapshot granularity | adopted |
| PPTA-to-C04 snapshot opacity recorded as a pre-registered expectation | adopted as test prediction, not fact |
| Four cold-reproduction targets and tolerances locked in Phase 0 | adopted |
| Timeboxed complete failure report is a valid Phase-5 exit | adopted |
| March 2022 INRIM fibre/GNSS discrepancy used as the contestation fixture | adopted |
| `gps2utc.clk` pinned by commit/checksum and `C0`/`C0′` applicability assessed separately | adopted |
| Additional sources assigned core, ancestry, context or analysis roles | adopted |
| Tidal models enter ancestry when applied; observed tides remain independent data | adopted |
| Seismic waveforms eligible; earthquake catalogues remain derived products | adopted |
| Weather and space weather admitted as ancestry or context according to use | adopted |
| Financial and generic social data analysis-only by default | adopted |
| Consortium engagement after walking skeleton | retained |

## 24. Version history

| Version | Date | Summary |
| --- | --- | --- |
| 0.1 | 2026-08-25 | Initial four-domain walking-skeleton task card |
| 0.2 | 2026-08-25 | Integrated structural review and scope discussion: state model decomposed; typed alignment outcomes; classified Phase-0 deficiencies; applicability assessments; platform/scientific outcomes separated; RO-Crate 1.3 pinned; rights and environment locks added; read-only human browser included; graph granularity and query semantics clarified; governed expansion register added for geodetic, geophysical, environmental, astronomical and engineered sensor sources |
| **0.3** | **2026-08-25** | **Verified and pinned the optical archive’s CC BY 4.0 rights, format specification, processing package and three-state flag semantics; made the optical MJD-tag chain an explicit ancestry question; pinned the living IPTA `gps2utc` artifact and added `C0`/`C0′` applicability; introduced concept/snapshot identity and graded shared-series evidence; bound acyclicity to snapshots; pre-registered the likely PPTA EOP-opacity outcome; replaced the synthetic contestation exemplar with the documented INRIM fibre/GNSS discrepancy; fixed FTRO output licences; specified a static graph-generated browser with shareable URL state; and required Phase-0 reproduction targets/tolerances plus timeboxed failure reports** |

---

**Next action:** execute Phase 0 from §21 and update this card to v0.4 with the four exact product selections, pre-registered reproduction targets and tolerances, two PPTA applicability assessments, actual optical validity intervals, the optical time-tag ancestry trace and the first classified deficiency entries.
