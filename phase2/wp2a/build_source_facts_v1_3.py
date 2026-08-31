#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build WP2A v1.3 source facts without presenting constructed keys as source facts.

Only values below ``source_projection`` are copied from the four authenticated JSON
sources.  Trial selection and join keys are emitted in separately labelled sections;
neither is represented as provider/source content.

  python3 phase2/wp2a/build_source_facts_v1_3.py
  python3 phase2/wp2a/build_source_facts_v1_3.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "phase2/wp2a/source-facts-v1.3.json"

SOURCES = {
    "igs_sio": {
        "path": "phase0/reports/igs-artifact-pins.json",
        "git_commit": None,
        "sha256": "d97b05d23ae1adc01e62765a5f7aff41e67e539d32c015057a60418d93ad9b7c",
    },
    "igs_bkg": {
        "path": "phase0/reports/igs-artifact-pins.json",
        "git_commit": "a806bbaa573d28f1460d18110f7974189ca19213",
        "sha256": "467d699ebfc4ac5088cb519bb5379eb5c273dc680a1cd9db053d50f26e2d6201",
    },
    "identities": {
        "path": "phase0/evidence/identities.json",
        "git_commit": None,
        "sha256": "a4a27e7e6dd0fd3ae75fd36acd9cfb9dfde51576724b8fecd21cae66cae3ac45",
    },
    "optical_inventory": {
        "path": "phase0/reports/optical-inventory-summary.json",
        "git_commit": None,
        "sha256": "f2f8b482dedb245eaac8b56f5ed56397073a64cea448dac845bf5599df3644ea",
    },
}

VARIANT_NAMES = ("igs21982.clk.Z", "igs21983.clk.Z", "igr21991.clk.Z")
OPTICAL_SNAPSHOT = "https://doi.org/10.5281/zenodo.17107693"
COMPARISON = "PTB_Yb_CombKnoten-INRIM_ITYb1"
MEMBER_FILE = "2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat"


class SourceFactsError(RuntimeError):
    """A pinned input or its required population is invalid."""


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def json_pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def source_bytes(key: str) -> bytes:
    spec = SOURCES[key]
    if spec["git_commit"] is None:
        try:
            body = (ROOT / spec["path"]).read_bytes()
        except OSError as exc:
            raise SourceFactsError(f"{key}: cannot read {spec['path']}: {exc}") from exc
    else:
        command = [
            "git", "--no-replace-objects", "-C", str(ROOT), "show",
            f"{spec['git_commit']}:{spec['path']}",
        ]
        done = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if done.returncode != 0:
            raise SourceFactsError(
                f"{key}: git show failed: {done.stderr.decode(errors='replace')}"
            )
        body = done.stdout
    observed = sha256_bytes(body)
    if observed != spec["sha256"]:
        raise SourceFactsError(
            f"{key}: authenticated source mismatch: expected {spec['sha256']}, observed {observed}"
        )
    return body


def load_sources() -> tuple[dict[str, Any], dict[str, bytes]]:
    documents: dict[str, Any] = {}
    bodies: dict[str, bytes] = {}
    for key in SOURCES:
        body = source_bytes(key)
        try:
            document = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SourceFactsError(f"{key}: authenticated bytes are not JSON: {exc}") from exc
        if not isinstance(document, dict):
            raise SourceFactsError(f"{key}: top-level JSON value is not an object")
        documents[key] = document
        bodies[key] = body
    return documents, bodies


def unique_index(rows: Any, field: str, *, source: str) -> tuple[dict[str, Any], dict[str, int]]:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise SourceFactsError(f"{source}: expected an array of objects")
    index: dict[str, Any] = {}
    positions: dict[str, int] = {}
    for position, row in enumerate(rows):
        value = row.get(field)
        if not isinstance(value, str) or not value:
            raise SourceFactsError(f"{source}[{position}].{field}: missing non-empty string")
        if value in index:
            raise SourceFactsError(f"{source}: duplicate {field} {value!r}")
        index[value] = row
        positions[value] = position
    return index, positions


def find_unique(rows: Any, field: str, value: str, *, source: str) -> tuple[dict[str, Any], int]:
    """Find one selected row without claiming every source row carries the selector field."""
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise SourceFactsError(f"{source}: expected an array of objects")
    matches = [(position, row) for position, row in enumerate(rows) if row.get(field) == value]
    if len(matches) != 1:
        raise SourceFactsError(
            f"{source}: expected exactly one {field}={value!r}, observed {len(matches)}"
        )
    position, row = matches[0]
    return row, position


def copied(source_key: str, pointer: str, values: dict[str, Any]) -> dict[str, Any]:
    """Label an exact projection. ``values`` must contain only copied source values."""
    return {"source_key": source_key, "source_pointer": pointer, "values": values}


def build() -> dict[str, Any]:
    documents, bodies = load_sources()
    sio, sio_pos = unique_index(documents["igs_sio"].get("pins"), "name", source="igs_sio/pins")
    bkg, bkg_pos = unique_index(documents["igs_bkg"].get("pins"), "name", source="igs_bkg/pins")
    optical, optical_position = find_unique(
        documents["identities"].get("artifacts"), "snapshot_id", OPTICAL_SNAPSHOT,
        source="identities/artifacts",
    )
    comparison, comparison_position = find_unique(
        documents["optical_inventory"].get("comparisons"), "comparison", COMPARISON,
        source="optical_inventory/comparisons",
    )

    products = []
    occurrence_keys = []
    for name in VARIANT_NAMES:
        if name not in sio or name not in bkg:
            raise SourceFactsError(f"{name}: absent from one or both authenticated IGS reports")
        s = sio[name]
        b = bkg[name]
        if b.get("sha256") != s.get("previous_retrieval_sha256"):
            raise SourceFactsError(f"{name}: current report does not link the historical outer digest")
        if b.get("concept_id") != s.get("concept_id"):
            raise SourceFactsError(f"{name}: SIO and BKG concept_id values differ")
        sio_pointer = f"/pins/{sio_pos[name]}"
        bkg_pointer = f"/pins/{bkg_pos[name]}"
        products.append({
            "registered_selector": name,
            "sio_occurrence_source": copied("igs_sio", sio_pointer, {
                key: s[key] for key in (
                    "name", "concept_id", "url", "effective_url", "retrieval_procedure",
                    "retrieved_utc", "sha256", "size_bytes", "retrieval_validation",
                    "decoded_sha256", "decoded_size_bytes", "expected_decoded_sha256",
                    "decoded_checksum_match", "previous_retrieval_sha256", "snapshot_change_basis",
                )
            }),
            "bkg_occurrence_source": copied("igs_bkg", bkg_pointer, {
                key: b[key] for key in (
                    "name", "concept_id", "url", "retrieval_procedure", "retrieved_utc",
                    "sha256", "size_bytes", "retrieval_validation",
                )
            }),
        })
        for source_key, suffix, pointer in (
            ("igs_sio", "SIO", sio_pointer), ("igs_bkg", "BKG", bkg_pointer)
        ):
            occurrence_keys.append({
                "kind": "constructed_join_key",
                "value": f"{name}@{suffix}",
                "construction": "registered product filename + '@' + registered source label",
                "inputs": [{"source_key": source_key, "source_pointer": f"{pointer}/name"}],
                "not_a_source_value": True,
            })

    optical_pointer = f"/artifacts/{optical_position}"
    members, member_pos = unique_index(
        comparison.get("files"), "file", source=f"optical_inventory/comparisons/{COMPARISON}/files"
    )
    if MEMBER_FILE not in members:
        raise SourceFactsError(f"optical inventory: missing registered member {MEMBER_FILE}")
    member = members[MEMBER_FILE]
    comparison_pointer = f"/comparisons/{comparison_position}"
    member_pointer = f"{comparison_pointer}/files/{member_pos[MEMBER_FILE]}"
    member_selector = f"{comparison['comparison']}/{member['file']}"

    generator_digest = sha256_bytes(Path(__file__).read_bytes())
    return {
        "document": "FTRO WP2A authenticated source projection",
        "version": "1.3.0",
        "generator": {
            "path": "phase2/wp2a/build_source_facts_v1_3.py",
            "sha256": generator_digest,
        },
        "boundary": {
            "source_projection": "Only values nested under a `values` object are copied from an authenticated source at the adjacent JSON pointer.",
            "registered_selection": "Selectors choose the bounded WP2A population; they are trial registration, not provider facts.",
            "constructed_join_keys": "Every constructed key is explicitly labelled and is not evidence of a provider identity.",
            "scientific_output_identity": "No transformation-output identity is minted in this source projection.",
        },
        "authenticated_sources": {
            key: {
                "path": spec["path"],
                "git_commit": spec["git_commit"],
                "sha256": sha256_bytes(bodies[key]),
            }
            for key, spec in SOURCES.items()
        },
        "registered_selection": {
            "family_A_product_names": list(VARIANT_NAMES),
            "family_B_snapshot": OPTICAL_SNAPSHOT,
            "family_B_comparison": COMPARISON,
            "family_B_member_file": MEMBER_FILE,
            "basis": "WP2A v1.3 bounded trial selection; not copied from a source",
        },
        "source_projection": {
            "family_A": {"products": products},
            "family_B": {
                "container_occurrence_source": copied("identities", optical_pointer, {
                    key: optical[key] for key in (
                        "concept_id", "snapshot_id", "retrieval_procedure", "retrieved_utc",
                        "sha256", "size_bytes", "evidence_state", "retrieval_validation",
                        "content_validation",
                    )
                }),
                "member_inventory_source": copied("optical_inventory", member_pointer, {
                    key: member[key] for key in ("file", "n_samples", "mjd_first", "mjd_last")
                }),
                "comparison_name_source": copied(
                    "optical_inventory", comparison_pointer,
                    {"comparison": comparison["comparison"]},
                ),
            },
        },
        "constructed_join_keys": {
            "retrieval_occurrences": occurrence_keys,
            "optical_member_selector": {
                "kind": "constructed_join_key",
                "value": member_selector,
                "construction": "comparison + '/' + file",
                "inputs": [
                    {"source_key": "optical_inventory", "source_pointer": f"{comparison_pointer}/comparison"},
                    {"source_key": "optical_inventory", "source_pointer": f"{member_pointer}/file"},
                ],
                "not_a_source_value": True,
            },
        },
        "declared_counts": {
            "family_A_products": 3,
            "family_A_retrieval_occurrences": 6,
            "family_A_decoded_byte_observations": 3,
            "family_B_retrieval_occurrences": 1,
            "family_B_member_inventory_records": 1,
            "basis": "count of the explicitly registered selection and projection above",
        },
    }


def serialise(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        rendered = serialise(build())
    except (SourceFactsError, KeyError, TypeError) as exc:
        print(f"FAIL WP2A v1.3 source facts: {exc}", file=sys.stderr)
        return 1
    if args.check:
        try:
            committed = OUT.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"FAIL WP2A v1.3 source facts: cannot read {OUT}: {exc}", file=sys.stderr)
            return 1
        if committed != rendered:
            print("FAIL WP2A v1.3 source facts: committed output differs", file=sys.stderr)
            return 1
        print("WP2A v1.3 source facts: PASS")
        return 0
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
