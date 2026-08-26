#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Bounded Gate-1 checks for the four hand-authored Phase-1 manifests.

This is deliberately not an RO-Crate validator and does not claim to be one.  It checks
only the two things Gate 1 names: the manifests remain provisional, and each domain can
locate its selected source bytes (or carry a structured access failure).  The optional
network run retrieves every located source in a clean environment and verifies its
committed digest without retaining provider bytes.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import collections
import datetime as dt
import dataclasses
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("optical", "pulsar", "vlbi", "gnss")
BASELINE_COMMIT = "a806bbaa573d28f1460d18110f7974189ca19213"
PHASE1_PARENT_COMMIT = "028c317ff1db27577617b8c3d2ff105da77b6739"
BASE_SPEC = "https://w3id.org/ro/crate/1.3"
PROFILE_PATH = "profile/ftro-graph-profile-v0.0.3.md"
PROFILE_ID = (
    "https://github.com/uwarring82/ftro-walking-skeleton/blob/"
    f"{BASELINE_COMMIT}/{PROFILE_PATH}"
)

# Independent of the manifests: a missing catalog reference must not make the expected
# source population shrink.  Optical has a provider PID and is reconciled against the
# Phase-0 identity record instead of a pinner report.
EXPECTED_CATALOGS = {
    "pulsar": {
        "path": "phase0/reports/ppta-artifact-pins.json",
        "count": 4,
        "sha256": "f758c7cee9a66a1d07e5bd6d2763734a57be5ef9a79f92e98a2aaebba08a9d62",
    },
    "vlbi": {
        "path": "phase0/reports/vlbi-vgosdb-pin.json",
        "count": 1,
        "sha256": "ac808bd43c2da96bcac2065107cbe0b9d16cbdff0ec3ad015313887157cede1a",
    },
    "gnss": {
        "path": "phase0/reports/igs-artifact-pins.json",
        "count": 57,
        "sha256": "467d699ebfc4ac5088cb519bb5379eb5c273dc680a1cd9db053d50f26e2d6201",
    },
}
EXPECTED_IDENTITIES_SHA256 = "531962537358fae0fff488512857888d9fffaad0f7d65a252309e9e6a6f9eecd"
EXPECTED_RETRIEVAL_COUNTS = {"optical": 3, "pulsar": 6, "vlbi": 2, "gnss": 58}
CAPTURED_INPUT_PATHS = (
    "phase1/check_gate1.py",
    "phase1/tests/test_gate1.py",
    "phase0/evidence/identities.json",
    *(item["path"] for item in EXPECTED_CATALOGS.values()),
    *(f"phase1/manifests/{domain}/ro-crate-metadata.json" for domain in DOMAINS),
)


class Gate1Error(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Gate1Snapshot:
    documents: dict
    sources: tuple[dict, ...]
    input_hashes: dict[str, str]
    input_fingerprint: str


CANDIDATE_OVERLAY_PATHS = {
    "phase1/check_gate1.py",
    "phase1/tests/test_gate1.py",
    *(f"phase1/manifests/{domain}/ro-crate-metadata.json" for domain in DOMAINS),
}
COMMITTED_CARRIER_ALLOWED_EXTRA_PATHS = {
    "phase1/README.md",
    "phase1/deficiency-log-phase1.json",
}
COMMITTED_CARRIER_ALLOWED_EXTRA_PREFIXES = (
    "phase1/reports/",
    "labnotes/",
)


def allowed_committed_output(path: str) -> bool:
    return path in COMMITTED_CARRIER_ALLOWED_EXTRA_PATHS or path.startswith(
        COMMITTED_CARRIER_ALLOWED_EXTRA_PREFIXES
    )


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_inputs(root: Path) -> tuple[dict[str, dict], dict[str, str], str]:
    """Read every Gate-1 input once and bind the set to one fingerprint."""
    captured = {}
    hashes = {}
    fingerprint = hashlib.sha256()
    for relative in CAPTURED_INPUT_PATHS:
        path = root / relative
        raw = path.read_bytes()
        observed = hashlib.sha256(raw).hexdigest()
        payload = None
        if relative.endswith(".json"):
            payload = json.loads(raw.decode("utf-8"))
        captured[relative] = {"payload": payload, "sha256": observed}
        hashes[relative] = observed
        fingerprint.update(relative.encode("utf-8"))
        fingerprint.update(b"\0")
        fingerprint.update(bytes.fromhex(observed))
    return captured, hashes, fingerprint.hexdigest()


def captured_json(root: Path, relative: str, captured: dict | None = None) -> tuple[dict, str]:
    if captured is not None:
        item = captured[relative]
        return item["payload"], item["sha256"]
    path = root / relative
    return load_json(path), sha256_file(path)


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def type_set(entity: dict) -> set[str]:
    return {x for x in as_list(entity.get("@type")) if isinstance(x, str)}


def ref_ids(value):
    """Yield entity references from a flattened JSON-LD value."""
    if isinstance(value, dict):
        if set(value) == {"@id"} and isinstance(value["@id"], str):
            yield value["@id"]
        else:
            for nested in value.values():
                yield from ref_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from ref_ids(nested)


def direct_refs(entity: dict, key: str) -> list[str]:
    return list(ref_ids(entity.get(key)))


def reachable_graph_ids(index: dict, start: str = "./") -> set[str]:
    reached = set()
    pending = [start]
    while pending:
        identifier = pending.pop()
        if identifier in reached or identifier not in index:
            continue
        reached.add(identifier)
        entity = index[identifier]
        for ref in ref_ids({key: value for key, value in entity.items() if key != "@id"}):
            if ref in index and ref not in reached:
                pending.append(ref)
    return reached


def nested_objects(entity: dict):
    """Return property paths containing anonymous objects in an entity.

    RO-Crate metadata is flattened.  Referenced entities are @id-only objects; structured
    records must be promoted to named graph entities rather than hidden blank nodes.
    """
    bad = []

    def walk(value, path):
        if isinstance(value, dict):
            if set(value) == {"@id"}:
                return
            bad.append(path)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    for key, value in entity.items():
        if key not in {"@id", "@type"}:
            walk(value, key)
    return bad


def report_entries(report: dict) -> list[dict]:
    pins = report.get("pins")
    if isinstance(pins, list):
        return pins
    if report.get("generator") == "src/ftro/pin_vgosdb.py":
        return [report]
    raise Gate1Error("source catalog is not a recognised pin report")


def report_is_clean(report: dict, entries: list[dict]) -> list[str]:
    errors = []
    for field in ("n_pinned", "n_failed", "n_without_expected_digest"):
        if type(report.get(field)) is not int:  # bool is deliberately rejected
            errors.append(f"{field} is not an integer")
    if type(report.get("n_pinned")) is int and report["n_pinned"] != len(entries):
        errors.append("n_pinned does not equal the source-entry count")
    if type(report.get("n_failed")) is not int or report["n_failed"] != 0:
        errors.append("n_failed is not zero")
    if type(report.get("n_without_expected_digest")) is not int or report["n_without_expected_digest"] != 0:
        errors.append("n_without_expected_digest is not zero")
    if report.get("failures") != []:
        errors.append("failures is not an empty list")
    if report.get("uncovered_by_registry") != []:
        errors.append("uncovered_by_registry is not an empty list")
    if report.get("retrieval_validation") != "content_validated":
        errors.append("top-level retrieval_validation is not content_validated")
    urls = []
    identifiers = []
    for index, entry in enumerate(entries):
        if entry.get("checksum_match") is not True:
            errors.append(f"entry {index} checksum_match is not true")
        if entry.get("retrieval_validation") != "content_validated":
            errors.append(f"entry {index} is not content_validated")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256", ""))):
            errors.append(f"entry {index} has no valid SHA-256")
        if entry.get("expected_sha256") != entry.get("sha256"):
            errors.append(f"entry {index} expected digest does not equal observed digest")
        url = str(entry.get("url", ""))
        if not url.startswith(("http://", "https://")):
            errors.append(f"entry {index} has no HTTP(S) locator")
        if entry.get("retrieval_procedure") != f"GET {url}":
            errors.append(f"entry {index} retrieval procedure does not bind its URL")
        identifier = entry.get("snapshot_id") or entry.get("ftro_snapshot_id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"entry {index} has no canonical snapshot identifier")
        urls.append(url)
        identifiers.append(identifier)
    if len(urls) != len(set(urls)):
        errors.append("source entries contain duplicate URLs")
    if len(identifiers) != len(set(identifiers)):
        errors.append("source entries contain duplicate snapshot identifiers")
    return errors


def identity_sources(root: Path, domain: str, captured: dict | None = None) -> list[dict]:
    identities, observed = captured_json(
        root, "phase0/evidence/identities.json", captured
    )
    if observed != EXPECTED_IDENTITIES_SHA256:
        raise Gate1Error("Phase-0 identities.json differs from the frozen baseline")
    matches = [
        item for item in identities.get("artifacts", [])
        if item.get("domain") == domain
        and item.get("evidence_state") == "resolvable"
        and re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
        and parse_get(item.get("retrieval_procedure"))
    ]
    expected_count = {"optical": 3, "pulsar": 5, "vlbi": 1}.get(domain)
    if expected_count is None:
        raise Gate1Error(f"no identity-source population is registered for {domain}")
    if len(matches) != expected_count:
        raise Gate1Error(
            f"expected {expected_count} retrievable {domain} identities, found {len(matches)}"
        )
    return matches


def expected_retrieval_sources(root: Path, captured: dict | None = None) -> list[dict]:
    """Build the exact network population from the frozen Phase-0 evidence."""
    sources = []
    for domain in ("optical", "pulsar", "vlbi"):
        for item in identity_sources(root, domain, captured):
            sources.append({
                "domain": domain,
                "role": "provider_source",
                "identifier": item["snapshot_id"],
                "url": parse_get(item["retrieval_procedure"]),
                "expected_sha256": item["sha256"],
            })
    for domain, expectation in EXPECTED_CATALOGS.items():
        path = expectation["path"]
        url = (
            "https://raw.githubusercontent.com/uwarring82/ftro-walking-skeleton/"
            f"{BASELINE_COMMIT}/{path}"
        )
        sources.append({
            "domain": domain,
            "role": "source_catalog",
            "identifier": url,
            "url": url,
            "expected_sha256": expectation["sha256"],
        })
        if domain == "gnss":
            report, _observed = captured_json(root, path, captured)
            for entry in report_entries(report):
                sources.append({
                    "domain": domain,
                    "role": "provider_source",
                    "identifier": entry["ftro_snapshot_id"],
                    "url": entry["url"],
                    "expected_sha256": entry["sha256"],
                })
    return sorted(sources, key=source_key)


def source_key(source: dict):
    return (
        source["domain"], source["role"], source["identifier"],
        source["url"], source["expected_sha256"],
    )


def source_population_errors(
    documents: dict, root: Path, captured: dict | None = None
) -> list[str]:
    observed = sorted(collect_sources(documents, root, captured), key=source_key)
    expected = expected_retrieval_sources(root, captured)
    observed_keys = {source_key(item) for item in observed}
    expected_keys = {source_key(item) for item in expected}
    errors = []
    for missing in sorted(expected_keys - observed_keys):
        errors.append(f"cross-domain: expected retrieval source is absent: {missing!r}")
    for unexpected in sorted(observed_keys - expected_keys):
        errors.append(f"cross-domain: unexpected retrieval source is present: {unexpected!r}")
    if len(observed) != len(observed_keys):
        errors.append("cross-domain: discovered retrieval sources are not unique")
    return errors


def validate_vlbi_wrappers(
    index: dict, root: Path, captured: dict | None = None
) -> list[str]:
    """Reconcile the five digest-keyed wrapper states to the frozen pin report."""
    report, _observed = captured_json(
        root, EXPECTED_CATALOGS["vlbi"]["path"], captured
    )
    records = report.get("wrapper_records")
    if not isinstance(records, list) or len(records) != 7:
        return ["vlbi: frozen source report does not contain seven wrapper records"]

    name_to_digest = {record.get("name"): record.get("sha256") for record in records}
    expected_by_digest = {}
    for record in records:
        digest = record.get("sha256")
        expected_by_digest.setdefault(digest, []).append(record)
    if len(expected_by_digest) != 5:
        return ["vlbi: frozen source report does not contain five wrapper byte states"]

    container = index.get(report.get("snapshot_id"))
    if not container:
        return ["vlbi: pinned container is absent while reconciling wrappers"]
    wrapper_ids = [ref for ref in direct_refs(container, "hasPart") if ref.startswith("#wrapper-")]
    wrapper_nodes = [index.get(identifier) for identifier in wrapper_ids]
    errors = []
    if len(wrapper_ids) != 5 or any(node is None for node in wrapper_nodes):
        errors.append("vlbi: container does not link exactly five wrapper entities")
        return errors
    observed_by_digest = {node.get("ftro:sha256"): node for node in wrapper_nodes}
    if set(observed_by_digest) != set(expected_by_digest):
        errors.append("vlbi: wrapper digest population disagrees with the frozen source report")
        return errors

    for digest, grouped in expected_by_digest.items():
        node = observed_by_digest[digest]
        paths = [record["path"] for record in grouped]
        names = [record["name"] for record in grouped]
        sizes = {record["size_bytes"] for record in grouped}
        time_tags = {tuple(record["run_time_tags"]) for record in grouped}
        inputs = {tuple(record["input_wrappers"]) for record in grouped}
        if as_list(node.get("ftro:member_paths")) != paths:
            errors.append(f"vlbi: wrapper {node['@id']} member paths disagree with the source report")
        if as_list(node.get("ftro:filenames")) != names:
            errors.append(f"vlbi: wrapper {node['@id']} filenames disagree with the source report")
        if len(sizes) != 1 or node.get("contentSize") != str(next(iter(sizes))):
            errors.append(f"vlbi: wrapper {node['@id']} contentSize disagrees with the source report")
        if len(time_tags) != 1 or as_list(node.get("ftro:run_time_tags")) != list(next(iter(time_tags))):
            errors.append(f"vlbi: wrapper {node['@id']} run-time tags disagree with the source report")
        expected_inputs = [name_to_digest[name] for name in next(iter(inputs))]
        observed_inputs = [index[ref].get("ftro:sha256") for ref in direct_refs(node, "ftro:input_wrappers")]
        if len(inputs) != 1 or observed_inputs != expected_inputs:
            errors.append(f"vlbi: wrapper {node['@id']} input-wrapper lineage disagrees with the source report")
    return errors


def validate_ppta_projection(
    index: dict, root: Path, captured: dict | None = None
) -> list[str]:
    report, _observed = captured_json(
        root, EXPECTED_CATALOGS["pulsar"]["path"], captured
    )
    entries = report_entries(report)
    expected_ids = [entry["snapshot_id"] for entry in entries]
    concept = index.get("ftro:concept:ppta/dr3")
    if not concept:
        return ["pulsar: PPTA release concept is absent"]
    errors = []
    if direct_refs(concept, "hasPart") != expected_ids:
        errors.append("pulsar: PPTA concept member set disagrees with the frozen pin report")
    for entry in entries:
        identifier = entry["snapshot_id"]
        node = index.get(identifier)
        if not node:
            errors.append(f"pulsar: frozen source {identifier} is not a graph entity")
            continue
        comparisons = {
            "contentSize": str(entry["size_bytes"]),
            "ftro:sha256": entry["sha256"],
            "ftro:retrieval_procedure": entry["retrieval_procedure"],
            "ftro:retrieval_validation": entry["retrieval_validation"],
        }
        for field, expected in comparisons.items():
            if node.get(field) != expected:
                errors.append(
                    f"pulsar: {identifier} field {field} disagrees with the frozen pin report"
                )
        if entry["name"] not in str(node.get("name", "")):
            errors.append(f"pulsar: {identifier} name does not identify the pinned filename")
        if "File" not in type_set(node):
            errors.append(f"pulsar: frozen source {identifier} is not typed File")
    return errors


def validate_gnss_projection(
    index: dict, root: Path, captured: dict | None = None
) -> list[str]:
    report, _observed = captured_json(
        root, EXPECTED_CATALOGS["gnss"]["path"], captured
    )
    entries = report_entries(report)
    by_id = {entry["ftro_snapshot_id"]: entry for entry in entries}
    counts = collections.Counter(entry["concept_id"] for entry in entries)
    errors = []

    collection = index.get("#igs-source-collection")
    if not collection:
        return ["gnss: source collection is absent"]
    if set(direct_refs(collection, "hasPart")) != set(counts):
        errors.append("gnss: source collection product-line set disagrees with the pin report")
    for concept_id, expected_count in counts.items():
        concept = index.get(concept_id)
        if not concept:
            errors.append(f"gnss: product-line concept {concept_id} is absent")
            continue
        if (
            type(concept.get("ftro:catalog_entry_count")) is not int
            or concept.get("ftro:catalog_entry_count") != expected_count
        ):
            errors.append(f"gnss: product-line count for {concept_id} disagrees with the pin report")
        if not direct_refs(concept, "hasPart") and not direct_refs(concept, "ftro:source_catalog"):
            errors.append(f"gnss: product-line concept {concept_id} has no snapshot or catalog route")

    summary = index.get("#series-counts-igs-igr")
    expected_series = collections.Counter(entry["series"] for entry in entries)
    if not summary:
        errors.append("gnss: series-count summary is absent")
    else:
        for series, expected_count in expected_series.items():
            if (
                type(summary.get(f"ftro:{series}")) is not int
                or summary.get(f"ftro:{series}") != expected_count
            ):
                errors.append(f"gnss: {series} series count disagrees with the pin report")

    exemplars = [
        node for identifier, node in index.items()
        if identifier.startswith("ftro:snapshot:igs/")
    ]
    for node in exemplars:
        identifier = node["@id"]
        entry = by_id.get(identifier)
        if not entry:
            errors.append(f"gnss: exemplar {identifier} is absent from the pin report")
            continue
        comparisons = {
            "name": entry["name"],
            "contentSize": str(entry["size_bytes"]),
            "ftro:sha256": entry["sha256"],
            "ftro:expected_sha256": entry["expected_sha256"],
            "ftro:checksum_match": True,
            "ftro:snapshot_id": identifier,
            "ftro:series": entry["series"],
            "ftro:validity_interval_mjd": [entry["mjd"], entry["mjd"] + 1],
            "ftro:retrieval_procedure": entry["retrieval_procedure"],
            "ftro:retrieval_validation": entry["retrieval_validation"],
        }
        for field, expected in comparisons.items():
            if node.get(field) != expected:
                errors.append(
                    f"gnss: exemplar {identifier} field {field} disagrees with the pin report"
                )
        if direct_refs(node, "ftro:snapshot_of") != [entry["concept_id"]]:
            errors.append(f"gnss: exemplar {identifier} is assigned to the wrong product line")
    return errors


def manifest_path(root: Path, domain: str) -> Path:
    return root / "phase1/manifests" / domain / "ro-crate-metadata.json"


def validate_manifest(
    domain: str,
    document: dict,
    root: Path = REPO_ROOT,
    captured: dict | None = None,
):
    errors = []
    graph = document.get("@graph")
    if not isinstance(graph, list):
        return [f"{domain}: @graph is not a list"], {}

    if any(not isinstance(entity, dict) for entity in graph):
        errors.append(f"{domain}: every @graph member must be an object")
    ids = [entity.get("@id") for entity in graph if isinstance(entity, dict)]
    if any(not isinstance(identifier, str) or not identifier for identifier in ids):
        errors.append(f"{domain}: every graph entity must have a non-empty @id")
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicates:
        errors.append(f"{domain}: duplicate graph @id values: {duplicates}")
    index = {entity["@id"]: entity for entity in graph if isinstance(entity, dict) and isinstance(entity.get("@id"), str)}

    descriptor = index.get("ro-crate-metadata.json")
    crate_root = index.get("./")
    if not descriptor or not crate_root:
        errors.append(f"{domain}: descriptor or root entity is missing")
        return errors, index

    if direct_refs(descriptor, "about") != ["./"]:
        errors.append(f"{domain}: descriptor must be about ./")
    if direct_refs(descriptor, "conformsTo") != [BASE_SPEC]:
        errors.append(f"{domain}: descriptor must declare only the RO-Crate 1.3 base")
    if direct_refs(crate_root, "conformsTo") != [PROFILE_ID]:
        errors.append(f"{domain}: root must declare the commit-pinned FTRO profile")
    profile = index.get(PROFILE_ID)
    if not profile or "Profile" not in type_set(profile):
        errors.append(f"{domain}: commit-pinned profile is not a typed graph entity")

    expected_context = [
        BASE_SPEC + "/context",
        {"ftro": "https://github.com/uwarring82/ftro-walking-skeleton/ns#"},
    ]
    if document.get("@context") != expected_context:
        errors.append(f"{domain}: JSON-LD context is absent, reordered or redefined")
    if crate_root.get("ftro:domain") != domain:
        errors.append(f"{domain}: root domain label does not equal its manifest domain")
    if type_set(descriptor) != {"CreativeWork"}:
        errors.append(f"{domain}: descriptor type is not CreativeWork")
    if "Dataset" not in type_set(crate_root):
        errors.append(f"{domain}: root type does not include Dataset")

    for entity in graph:
        if not isinstance(entity, dict) or not isinstance(entity.get("@id"), str):
            continue
        entity_id = entity["@id"]
        anonymous = nested_objects(entity)
        if anonymous:
            errors.append(f"{domain}: {entity_id} contains unflattened objects at {anonymous}")
        parts = direct_refs(entity, "hasPart")
        if len(parts) != len(set(parts)):
            errors.append(f"{domain}: {entity_id} has duplicate hasPart targets")
        for ref in ref_ids({k: v for k, v in entity.items() if k != "@id"}):
            if (ref.startswith("#") or ref in {"./", "ro-crate-metadata.json"}) and ref not in index:
                errors.append(f"{domain}: {entity_id} has dangling local reference {ref}")

    root_mentions = set(direct_refs(crate_root, "mentions"))
    for entity in graph:
        if not isinstance(entity, dict):
            continue
        if "ftro:Assertion" in type_set(entity) and entity.get("ftro:evidence_state") == "unresolved":
            entity_id = entity["@id"]
            if not direct_refs(entity, "ftro:subject"):
                errors.append(f"{domain}: unresolved assertion {entity_id} has no subject")
            if entity_id not in root_mentions:
                errors.append(f"{domain}: unresolved assertion {entity_id} is not mentioned by the root")
            if not entity.get("ftro:note"):
                errors.append(f"{domain}: unresolved assertion {entity_id} has no reason note")
            if not any(
                entity.get(field)
                for field in ("ftro:edge_class", "ftro:declared_relation", "ftro:relation")
            ):
                errors.append(f"{domain}: unresolved assertion {entity_id} has no declared relation")
            if not any(
                field in entity
                for field in ("ftro:object", "ftro:declared_value", "ftro:competing_readings")
            ):
                errors.append(f"{domain}: unresolved assertion {entity_id} has no explicit object state")

    # Conformance is deliberately not claimed here: Gate 1 keeps the terms provisional.
    report_refs = direct_refs(crate_root, "ftro:conformance_report")
    if len(report_refs) != 1 or report_refs[0] not in index:
        errors.append(f"{domain}: root does not reference exactly one conformance report")
    else:
        report = index[report_refs[0]]
        if "ftro:ConformanceReport" not in type_set(report):
            errors.append(f"{domain}: conformance report is not typed ftro:ConformanceReport")
        if report.get("ftro:normative_validation_result") != "not_run":
            errors.append(f"{domain}: normative RO-Crate 1.3 validation must remain explicitly not_run")
        if not report.get("ftro:normative_validation_reason"):
            errors.append(f"{domain}: not-run normative validation has no reason")

    catalogs = {}
    if domain in EXPECTED_CATALOGS:
        expectation = EXPECTED_CATALOGS[domain]
        expected_path = expectation["path"]
        expected_count = expectation["count"]
        expected_digest = expectation["sha256"]
        refs = direct_refs(crate_root, "ftro:source_catalog")
        if len(refs) != 1 or refs[0] not in index:
            errors.append(f"{domain}: expected source catalog is missing from the root")
        else:
            entity = index[refs[0]]
            if refs[0] not in direct_refs(crate_root, "hasPart"):
                errors.append(f"{domain}: source catalog is not a root data entity")
            if entity.get("ftro:local_path") != expected_path:
                errors.append(f"{domain}: source catalog points to {entity.get('ftro:local_path')!r}, expected {expected_path!r}")
            if entity.get("ftro:sha256") != expected_digest:
                errors.append(f"{domain}: source catalog is not bound to the frozen baseline digest")
            if type(entity.get("ftro:expected_entry_count")) is not int or entity.get("ftro:expected_entry_count") != expected_count:
                errors.append(f"{domain}: source catalog expected-entry count is absent or wrong")
            local = root / expected_path
            if captured is None and not local.is_file():
                errors.append(f"{domain}: local source catalog {expected_path} is absent")
            else:
                try:
                    payload, observed = captured_json(root, expected_path, captured)
                except (OSError, json.JSONDecodeError, KeyError) as exc:
                    errors.append(f"{domain}: cannot read source catalog: {exc}")
                    payload = {}
                    observed = None
                if observed != expected_digest:
                    errors.append(f"{domain}: local source catalog differs from the frozen baseline")
                if entity.get("ftro:sha256") != observed:
                    errors.append(f"{domain}: source catalog digest does not match {expected_path}")
                try:
                    entries = report_entries(payload)
                except Gate1Error as exc:
                    errors.append(f"{domain}: cannot read source catalog: {exc}")
                    entries = []
                    payload = {}
                if len(entries) != expected_count:
                    errors.append(f"{domain}: source catalog has {len(entries)} entries, expected {expected_count}")
                for problem in report_is_clean(payload, entries):
                    errors.append(f"{domain}: source catalog: {problem}")
                catalogs[expected_path] = (entity, entries)
    if domain in {"optical", "pulsar", "vlbi"}:
        try:
            expected_sources = identity_sources(root, domain, captured)
        except Gate1Error as exc:
            errors.append(f"{domain}: {exc}")
        else:
            reachable = reachable_graph_ids(index)
            for expected in expected_sources:
                entity = index.get(expected.get("snapshot_id"))
                if not entity:
                    errors.append(f"{domain}: provider snapshot {expected.get('snapshot_id')} is absent")
                    continue
                if expected.get("snapshot_id") not in reachable:
                    errors.append(f"{domain}: provider snapshot {expected.get('snapshot_id')} is unreachable from the root")
                if entity.get("ftro:sha256") != expected.get("sha256"):
                    errors.append(f"{domain}: provider snapshot {expected.get('snapshot_id')} digest disagrees with identities.json")
                if entity.get("ftro:retrieval_procedure") != expected.get("retrieval_procedure"):
                    errors.append(f"{domain}: provider snapshot {expected.get('snapshot_id')} locator disagrees with identities.json")

    if domain == "vlbi":
        errors.extend(validate_vlbi_wrappers(index, root, captured))
    elif domain == "pulsar":
        errors.extend(validate_ppta_projection(index, root, captured))
    elif domain == "gnss":
        errors.extend(validate_gnss_projection(index, root, captured))

    catalog_digests = {
        entry.get("sha256")
        for _entity, entries in catalogs.values()
        for entry in entries
    }
    parents = {}
    for entity in graph:
        if isinstance(entity, dict) and isinstance(entity.get("@id"), str):
            for child in direct_refs(entity, "hasPart"):
                parents.setdefault(child, []).append(entity)
    for entity in graph:
        if not isinstance(entity, dict) or entity.get("ftro:evidence_state") != "resolvable":
            continue
        digest = entity.get("ftro:sha256")
        if not digest:
            continue
        has_get = str(entity.get("ftro:retrieval_procedure", "")).startswith("GET http")
        in_catalog = digest in catalog_digests
        internal_member = any(str(parent.get("ftro:retrieval_procedure", "")).startswith("GET http") for parent in parents.get(entity.get("@id"), []))
        if not (has_get or in_catalog or internal_member):
            errors.append(f"{domain}: resolvable artifact {entity.get('@id')} has no executable locator")

    return errors, index


def validate_all(root: Path = REPO_ROOT):
    errors, snapshot = build_snapshot(root)
    return errors, snapshot.documents


def parse_get(procedure: str) -> str | None:
    if not isinstance(procedure, str) or not procedure.startswith("GET "):
        return None
    url = procedure[4:].strip()
    return url if url.startswith(("http://", "https://")) else None


def collect_sources(
    documents: dict, root: Path = REPO_ROOT, captured: dict | None = None
):
    sources = {}
    for domain, document in documents.items():
        index = {entity["@id"]: entity for entity in document["@graph"]}
        crate_root = index["./"]
        for ref in direct_refs(crate_root, "ftro:source_catalog"):
            catalog = index[ref]
            url = parse_get(catalog.get("ftro:retrieval_procedure"))
            digest = catalog.get("ftro:sha256")
            if url and digest:
                sources[(domain, url, digest)] = {
                    "domain": domain, "role": "source_catalog", "identifier": ref,
                    "url": url, "expected_sha256": digest,
                }
            report, _observed = captured_json(
                root, catalog["ftro:local_path"], captured
            )
            for entry in report_entries(report):
                entry_url = entry["url"]
                entry_digest = entry["sha256"]
                identifier = entry.get("snapshot_id") or entry.get("ftro_snapshot_id") or entry.get("name") or entry.get("key") or entry_url
                sources[(domain, entry_url, entry_digest)] = {
                    "domain": domain, "role": "provider_source", "identifier": identifier,
                    "url": entry_url, "expected_sha256": entry_digest,
                }
        for entity in document["@graph"]:
            url = parse_get(entity.get("ftro:retrieval_procedure"))
            digest = entity.get("ftro:sha256")
            if url and digest:
                sources.setdefault((domain, url, digest), {
                    "domain": domain, "role": "provider_source", "identifier": entity["@id"],
                    "url": url, "expected_sha256": digest,
                })
    return [sources[key] for key in sorted(sources)]


def build_snapshot(root: Path = REPO_ROOT) -> tuple[list[str], Gate1Snapshot]:
    """Capture once, validate once, and return the exact sources retrieval may use."""
    try:
        captured, input_hashes, fingerprint = capture_inputs(root)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        empty = Gate1Snapshot({}, (), {}, "")
        return [f"cross-domain: cannot capture Gate-1 inputs: {exc}"], empty

    documents = {
        domain: captured[
            f"phase1/manifests/{domain}/ro-crate-metadata.json"
        ]["payload"]
        for domain in DOMAINS
    }
    errors = []
    for domain, document in documents.items():
        domain_errors, _index = validate_manifest(
            domain, document, root, captured
        )
        errors.extend(domain_errors)

    try:
        sources = tuple(collect_sources(documents, root, captured))
    except (Gate1Error, KeyError, TypeError) as exc:
        errors.append(f"cross-domain: cannot construct captured source population: {exc}")
        sources = ()
    if not errors:
        counts = collections.Counter(item["domain"] for item in sources)
        if dict(counts) != EXPECTED_RETRIEVAL_COUNTS:
            errors.append(
                "cross-domain: discovered retrieval population "
                f"{dict(counts)!r}, expected {EXPECTED_RETRIEVAL_COUNTS!r}"
            )
        errors.extend(source_population_errors(documents, root, captured))

    return errors, Gate1Snapshot(
        documents=documents,
        sources=sources,
        input_hashes=input_hashes,
        input_fingerprint=fingerprint,
    )


def retrieve_one(source: dict, timeout: int):
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {**source, "started_utc": started}
    digest = hashlib.sha256()
    size = 0
    try:
        request = urllib.request.Request(
            source["url"], headers={"User-Agent": "FTRO-Gate1-clean-retrieval/1.0"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result["http_status"] = response.status
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                size += len(chunk)
                digest.update(chunk)
        observed = digest.hexdigest()
        result.update({
            "size_bytes": size,
            "observed_sha256": observed,
            "checksum_match": observed == source["expected_sha256"],
            "outcome": "retrieved" if observed == source["expected_sha256"] else "digest_mismatch",
        })
    except Exception as exc:  # noqa: BLE001 - failure is evidence, not a traceback
        result.update({
            "size_bytes": size,
            "observed_sha256": digest.hexdigest() if size else None,
            "checksum_match": False,
            "outcome": "access_failure",
            "error": f"{type(exc).__name__}: {exc}",
        })
    result["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    return result


def _git_output(root: Path, *arguments: str) -> tuple[str | None, str | None]:
    """Return one Git result without allowing a missing/broken checkout to pass."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return None, f"cannot execute git: {exc}"
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return None, f"git {' '.join(arguments)} exited {completed.returncode}: {detail}"
    return completed.stdout.decode("utf-8", errors="strict"), None


def source_state_evidence(root: Path, source_state: str) -> tuple[list[str], dict]:
    """Test, rather than trust, the source-state claim made by a retrieval run."""
    root = root.resolve()
    data_present = (root / "data").exists()
    evidence = {
        "mode": source_state,
        "data_directory_present": data_present,
    }
    if source_state == "working_tree":
        evidence["claim"] = "diagnostic only; no clean-export assertion"
        return [], evidence
    if source_state not in {"parent_overlay", "committed_checkout"}:
        return [f"unsupported source state {source_state!r}"], evidence

    errors = []
    if data_present:
        errors.append("clean source state contains a data/ directory")

    top_level, error = _git_output(root, "rev-parse", "--show-toplevel")
    if error:
        errors.append(error)
    else:
        observed_root = Path(top_level.strip()).resolve()
        evidence["git_top_level"] = str(observed_root)
        if observed_root != root:
            errors.append(
                f"isolated export root {root} is inside Git tree {observed_root}"
            )

    head, error = _git_output(root, "rev-parse", "HEAD")
    observed_head = None
    if error:
        errors.append(error)
    else:
        observed_head = head.strip()
        evidence["git_head"] = observed_head

    changed_raw, error = _git_output(root, "diff", "--name-only", "-z", "HEAD", "--")
    untracked_raw, untracked_error = _git_output(
        root, "ls-files", "--others", "--exclude-standard", "-z"
    )
    if error:
        errors.append(error)
    if untracked_error:
        errors.append(untracked_error)
    if error is None and untracked_error is None:
        changed = {
            item
            for item in (changed_raw + untracked_raw).split("\0")
            if item
        }
        evidence["candidate_paths"] = sorted(changed)
        evidence["required_candidate_paths"] = sorted(CANDIDATE_OVERLAY_PATHS)
        if source_state == "parent_overlay":
            if observed_head is not None and observed_head != PHASE1_PARENT_COMMIT:
                errors.append(
                    "parent overlay HEAD differs from the Phase-1 parent: "
                    f"{observed_head!r} != {PHASE1_PARENT_COMMIT!r}"
                )
            missing = CANDIDATE_OVERLAY_PATHS - changed
            extra = changed - CANDIDATE_OVERLAY_PATHS
            if missing:
                errors.append(
                    "parent overlay is missing candidate paths: "
                    + ", ".join(sorted(missing))
                )
            if extra:
                errors.append(
                    "parent overlay contains changes outside the candidate paths: "
                    + ", ".join(sorted(extra))
                )
        else:
            if changed:
                errors.append(
                    "committed checkout is not clean: " + ", ".join(sorted(changed))
                )
            if observed_head is not None:
                _output, ancestor_error = _git_output(
                    root,
                    "merge-base",
                    "--is-ancestor",
                    PHASE1_PARENT_COMMIT,
                    observed_head,
                )
                parent_is_ancestor = ancestor_error is None
                evidence["phase1_parent_is_ancestor"] = parent_is_ancestor
                if not parent_is_ancestor:
                    errors.append(
                        "committed checkout does not descend from the Phase-1 parent"
                    )
                committed_raw, committed_error = _git_output(
                    root,
                    "diff",
                    "--name-only",
                    "-z",
                    f"{PHASE1_PARENT_COMMIT}..{observed_head}",
                    "--",
                )
                if committed_error:
                    errors.append(committed_error)
                else:
                    committed_paths = {
                        item for item in committed_raw.split("\0") if item
                    }
                    evidence["paths_changed_since_parent"] = sorted(committed_paths)
                    missing = CANDIDATE_OVERLAY_PATHS - committed_paths
                    if missing:
                        errors.append(
                            "committed checkout does not contain all candidate paths: "
                            + ", ".join(sorted(missing))
                        )
                    extra = committed_paths - CANDIDATE_OVERLAY_PATHS
                    evidence["non_input_output_paths"] = sorted(extra)
                    disallowed = {
                        path for path in extra if not allowed_committed_output(path)
                    }
                    if disallowed:
                        errors.append(
                            "committed checkout changes paths outside the candidate and "
                            "publication-output allowlist: "
                            + ", ".join(sorted(disallowed))
                        )

    evidence["verified"] = not errors
    return errors, evidence


def retrieval_report(
    snapshot: Gate1Snapshot,
    workers: int,
    timeout: int,
    root: Path,
    source_state: str,
    source_state_record: dict,
):
    sources = list(snapshot.sources)
    data_directory_present_at_start = (root / "data").exists()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda item: retrieve_one(item, timeout), sources))
    results.sort(key=lambda item: (item["domain"], item["url"]))
    n_ok = sum(
        item.get("outcome") == "retrieved"
        and item.get("checksum_match") is True
        and item.get("observed_sha256") == item.get("expected_sha256")
        for item in results
    )
    return {
        "document": "FTRO Gate-1 clean-environment retrieval report",
        "version": "1.0.0",
        "phase0_baseline": BASELINE_COMMIT,
        "phase1_parent_commit": PHASE1_PARENT_COMMIT,
        "candidate_source_state": source_state,
        "source_state_evidence": source_state_record,
        "input_fingerprint_sha256": snapshot.input_fingerprint,
        "input_sha256": snapshot.input_hashes,
        "executed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "locale": os.environ.get("LC_ALL") or os.environ.get("LANG"),
            "time_zone": os.environ.get("TZ"),
            "data_directory_present_at_start": data_directory_present_at_start,
        },
        "method": "HTTP(S) GET from the exact frozen Phase-0 source population; stream to SHA-256; retain no provider bytes. Content validity follows from equality to the already content-validated frozen digest.",
        "workers": workers,
        "per_source_timeout_seconds": timeout,
        "provider_bytes_retained": False,
        "n_sources": len(results),
        "n_provider_sources": sum(item["role"] == "provider_source" for item in results),
        "n_source_catalogs": sum(item["role"] == "source_catalog" for item in results),
        "n_retrieved_and_matched": n_ok,
        "n_failed": len(results) - n_ok,
        "gate1_retrieval_status": (
            "pass"
            if n_ok == len(results)
            and source_state in {"parent_overlay", "committed_checkout"}
            else "diagnostic_success_not_isolated"
            if n_ok == len(results)
            else "explicit_failure"
        ),
        "results": results,
    }


def retrieval_report_errors(snapshot: Gate1Snapshot, report: dict) -> list[str]:
    errors = []
    if report.get("input_fingerprint_sha256") != snapshot.input_fingerprint:
        errors.append("input fingerprint differs")
    if report.get("input_sha256") != snapshot.input_hashes:
        errors.append("input digest map differs")
    results = report.get("results")
    if not isinstance(results, list):
        return errors + ["results is not a list"]
    expected = {source_key(item): item for item in snapshot.sources}
    observed = {}
    for index, result in enumerate(results):
        try:
            key = source_key(result)
        except (KeyError, TypeError):
            errors.append(f"result {index} has no complete source identity")
            continue
        if key in observed:
            errors.append(f"result {index} duplicates a source identity")
        observed[key] = result
        if result.get("outcome") != "retrieved":
            errors.append(f"result {index} outcome is not retrieved")
        if result.get("checksum_match") is not True:
            errors.append(f"result {index} checksum_match is not true")
        if result.get("observed_sha256") != result.get("expected_sha256"):
            errors.append(f"result {index} observed digest does not match expected digest")
    if set(observed) != set(expected):
        errors.append("report result population differs from the captured source population")
    n_matched = sum(
        result.get("outcome") == "retrieved"
        and result.get("checksum_match") is True
        and result.get("observed_sha256") == result.get("expected_sha256")
        for result in results
        if isinstance(result, dict)
    )
    aggregate_expectations = {
        "n_sources": len(results),
        "n_provider_sources": sum(
            result.get("role") == "provider_source"
            for result in results
            if isinstance(result, dict)
        ),
        "n_source_catalogs": sum(
            result.get("role") == "source_catalog"
            for result in results
            if isinstance(result, dict)
        ),
        "n_retrieved_and_matched": n_matched,
        "n_failed": len(results) - n_matched,
    }
    for field, expected_value in aggregate_expectations.items():
        value = report.get(field)
        if type(value) is not int or value != expected_value:
            errors.append(
                f"{field} is not integer {expected_value} derived from results"
            )
    if len(results) != len(expected):
        errors.append("results count does not equal the captured source population")
    source_state = report.get("candidate_source_state")
    clean_state = source_state in {"parent_overlay", "committed_checkout"}
    if not clean_state:
        errors.append("candidate source state is not a supported clean state")
    expected_status = (
        "pass"
        if n_matched == len(results) and clean_state
        else "diagnostic_success_not_isolated"
        if n_matched == len(results)
        else "explicit_failure"
    )
    if report.get("gate1_retrieval_status") != expected_status:
        errors.append(
            "gate1_retrieval_status is not derived from results and source state"
        )
    if report.get("gate1_retrieval_status") != "pass":
        errors.append("retrieval status is not pass")
    state_evidence = report.get("source_state_evidence")
    if not isinstance(state_evidence, dict):
        errors.append("source-state evidence is absent or not an object")
    else:
        if state_evidence.get("mode") != source_state:
            errors.append("source-state evidence mode disagrees with the report")
        if state_evidence.get("verified") is not True:
            errors.append("source-state evidence is not verified")
        if state_evidence.get("data_directory_present") is not False:
            errors.append("source-state evidence records a data directory")
        if source_state == "parent_overlay":
            if state_evidence.get("git_head") != PHASE1_PARENT_COMMIT:
                errors.append("source-state evidence records the wrong Git parent")
            if state_evidence.get("candidate_paths") != sorted(CANDIDATE_OVERLAY_PATHS):
                errors.append("source-state evidence records the wrong candidate overlay")
        elif source_state == "committed_checkout":
            if state_evidence.get("candidate_paths") != []:
                errors.append("source-state evidence records a dirty committed checkout")
            head = state_evidence.get("git_head")
            if not isinstance(head, str) or re.fullmatch(r"[0-9a-f]{40}", head) is None:
                errors.append("source-state evidence has no full committed Git HEAD")
            if state_evidence.get("phase1_parent_is_ancestor") is not True:
                errors.append("source-state evidence does not establish Phase-1 ancestry")
            committed_paths = state_evidence.get("paths_changed_since_parent")
            if not isinstance(committed_paths, list) or not all(
                isinstance(path, str) for path in committed_paths
            ):
                committed_path_set = set()
                errors.append("source-state evidence has malformed committed paths")
            else:
                committed_path_set = set(committed_paths)
            if not CANDIDATE_OVERLAY_PATHS.issubset(committed_path_set):
                errors.append("source-state evidence omits committed candidate paths")
            disallowed = {
                path
                for path in committed_path_set - CANDIDATE_OVERLAY_PATHS
                if not allowed_committed_output(path)
            }
            if disallowed:
                errors.append(
                    "source-state evidence records disallowed committed paths: "
                    + ", ".join(sorted(disallowed))
                )
    if report.get("environment", {}).get("data_directory_present_at_start") is not False:
        errors.append("data directory was present at retrieval start")
    return errors


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--retrieve", action="store_true", help="retrieve and hash all located sources")
    parser.add_argument("--out", type=Path, help="write the clean retrieval report here")
    parser.add_argument("--check-report", type=Path, help="verify that a retrieval report matches the current Gate-1 inputs")
    parser.add_argument(
        "--source-state",
        choices=("working_tree", "parent_overlay", "committed_checkout"),
        default="working_tree",
        help="identify the source-tree state recorded in a new retrieval report",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)

    errors, snapshot = build_snapshot(args.root)
    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        print(f"Gate 1 structural/source check: {len(errors)} failure(s)", file=sys.stderr)
        return 1
    print("Gate 1 structural/source check: PASS (4 manifests)")

    if args.check_report:
        try:
            prior = load_json(args.check_report)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Gate 1 report freshness: FAIL ({exc})", file=sys.stderr)
            return 1
        report_errors = retrieval_report_errors(snapshot, prior)
        if report_errors:
            for error in report_errors:
                print(f"FAIL Gate 1 retrieval report: {error}", file=sys.stderr)
            print("Gate 1 report freshness/content: FAIL", file=sys.stderr)
            return 1
        print("Gate 1 report freshness/content: PASS")
        if not args.retrieve:
            return 0

    if not args.retrieve:
        return 0
    if not args.out:
        parser.error("--retrieve requires --out")
    state_errors, state_record = source_state_evidence(args.root, args.source_state)
    if state_errors:
        for error in state_errors:
            print(f"FAIL Gate 1 source-state preflight: {error}", file=sys.stderr)
        print("Gate 1 clean retrieval: NOT STARTED", file=sys.stderr)
        return 1
    report = retrieval_report(
        snapshot,
        max(1, args.workers),
        args.timeout,
        args.root,
        args.source_state,
        state_record,
    )
    if report["gate1_retrieval_status"] == "pass":
        report_errors = retrieval_report_errors(snapshot, report)
        if report_errors:
            for error in report_errors:
                print(f"FAIL new Gate 1 retrieval report: {error}", file=sys.stderr)
            print("Gate 1 clean retrieval report: REJECTED before publication", file=sys.stderr)
            return 1
    write_json(args.out, report)
    print(
        f"Gate 1 clean retrieval: {report['n_retrieved_and_matched']}/"
        f"{report['n_sources']} matched; {report['n_failed']} failed -> {args.out}"
    )
    return 0 if report["gate1_retrieval_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
