#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WP2A source facts from the four pinned oracle sources.

v1.1 claimed expected facts were "derived from the four pinned oracle sources by a committed
generator".  No generator was committed, and the claim was false in a second way: predicates,
temporal interpretations, code-consumption claims and WP2A execution states are NOT in those
sources at all.  They are curated semantics, and presenting them as source derivation is the
projection-only pattern one level up (FTRO-P1-DEF-016).

This generator emits ONLY what the sources literally contain.  Everything requiring judgement
lives in interpretations-v1.2.json, separately, with a stated basis per item.

  python3 phase2/wp2a/build_source_facts.py            # write source-facts-v1.2.json
  python3 phase2/wp2a/build_source_facts.py --check     # fail if the committed file has drifted
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "phase2", "wp2a", "source-facts-v1.2.json")

# Pinned by digest.  A source whose bytes differ is a hard failure, never a silent re-derive.
SOURCES = {
    "igs_sio": {
        "path": "phase0/reports/igs-artifact-pins.json", "git_rev": None,
        "sha256": "d97b05d23ae1adc01e62765a5f7aff41e67e539d32c015057a60418d93ad9b7c",
        "role": "IGS SIO retrieval occurrences and decoded outputs"},
    "igs_bkg": {
        "path": "phase0/reports/igs-artifact-pins.json", "git_rev": "a806bba",
        "sha256": "467d699ebfc4ac5088cb519bb5379eb5c273dc680a1cd9db053d50f26e2d6201",
        "role": "IGS BKG retrieval occurrences: route, size, retrieval time, procedure"},
    "identities": {
        "path": "phase0/evidence/identities.json", "git_rev": None,
        "sha256": "a4a27e7e6dd0fd3ae75fd36acd9cfb9dfde51576724b8fecd21cae66cae3ac45",
        "role": "optical container complete retrieval identity"},
    "optical_inventory": {
        "path": "phase0/reports/optical-inventory-summary.json", "git_rev": None,
        "sha256": "f2f8b482dedb245eaac8b56f5ed56397073a64cea448dac845bf5599df3644ea",
        "role": "optical member path, sample count and MJD extent"},
}

VARIANT_NAMES = ("igs21982.clk.Z", "igs21983.clk.Z", "igr21991.clk.Z")
OPTICAL_SNAPSHOT = "https://doi.org/10.5281/zenodo.17107693"
COMPARISON = "PTB_Yb_CombKnoten-INRIM_ITYb1"
MEMBER_FILE = "2022-02-21_PTB_Yb_CombKnoten-INRIM_ITYb1.dat"


class SourceError(RuntimeError):
    pass


def raw(key):
    spec = SOURCES[key]
    if spec["git_rev"]:
        done = subprocess.run(["git", "-C", ROOT, "show", f"{spec['git_rev']}:{spec['path']}"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if done.returncode != 0:
            raise SourceError(f"{key}: git show failed: {done.stderr.decode(errors='replace')}")
        body = done.stdout
    else:
        with open(os.path.join(ROOT, spec["path"]), "rb") as handle:
            body = handle.read()
    observed = hashlib.sha256(body).hexdigest()
    if spec["sha256"] and observed != spec["sha256"]:
        raise SourceError(f"{key}: pinned {spec['sha256']}, observed {observed}")
    return body, observed


def build():
    bodies, digests = {}, {}
    for key in SOURCES:
        bodies[key], digests[key] = raw(key)
    sio = {p["name"]: p for p in json.loads(bodies["igs_sio"])["pins"]}
    bkg = {p["name"]: p for p in json.loads(bodies["igs_bkg"])["pins"]}
    identities = json.loads(bodies["identities"])
    inventory = json.loads(bodies["optical_inventory"])

    occurrence_fields = ("url", "retrieval_procedure", "retrieved_utc", "sha256", "size_bytes")
    products = []
    for name in VARIANT_NAMES:
        if name not in sio or name not in bkg:
            raise SourceError(f"{name} absent from a pinned source")
        s, b = sio[name], bkg[name]
        if b["sha256"] != s.get("previous_retrieval_sha256"):
            raise SourceError(f"{name}: BKG digest disagrees with previous_retrieval_sha256")
        products.append({
            "product_name": name,
            "concept_id": s["concept_id"],
            "name_field_value": s["name"],
            "retrieval_occurrences": [
                {"occurrence_id": f"{name}@SIO", "origin": "SIO",
                 "source_key": "igs_sio",
                 **{f: s[f] for f in occurrence_fields}},
                {"occurrence_id": f"{name}@BKG", "origin": "BKG",
                 "source_key": "igs_bkg",
                 **{f: b[f] for f in occurrence_fields}},
            ],
            "decoded_output": {
                "output_id": f"{name}#decoded",
                "sha256": s["decoded_sha256"], "size_bytes": s["decoded_size_bytes"],
                "source_key": "igs_sio",
                "snapshot_change_basis": s["snapshot_change_basis"]},
        })

    optical = next((a for a in identities["artifacts"]
                    if a.get("snapshot_id") == OPTICAL_SNAPSHOT), None)
    if optical is None:
        raise SourceError("optical container absent from identities.json")
    comparison = next((c for c in inventory["comparisons"]
                       if c["comparison"] == COMPARISON), None)
    if comparison is None:
        raise SourceError(f"comparison {COMPARISON} absent from the inventory")
    member = next((f for f in comparison["files"] if f["file"] == MEMBER_FILE), None)
    if member is None:
        raise SourceError(f"member {MEMBER_FILE} absent from {COMPARISON}")

    return {
        "document": "FTRO WP2A source facts",
        "version": "1.2.0",
        "generator": "phase2/wp2a/build_source_facts.py",
        "generated_content_only": (
            "Every value here is copied verbatim from a pinned source. Predicates, evidence "
            "states, execution states, temporal semantics and code-consumption claims are NOT "
            "here -- they are registered interpretations and live in interpretations-v1.2.json."),
        "sources": {k: {**{kk: vv for kk, vv in v.items() if kk != "sha256"},
                        "sha256": digests[k]} for k, v in SOURCES.items()},
        "family_A": {"products": products,
                     "n_products": len(products),
                     "n_retrieval_occurrences": sum(len(p["retrieval_occurrences"]) for p in products),
                     "n_outputs": len(products)},
        "family_B": {
            "container_occurrence": {
                "occurrence_id": "rocit-zip@zenodo", "origin": "Zenodo",
                "source_key": "identities",
                "concept_id": optical["concept_id"], "version_id": optical["snapshot_id"],
                "retrieval_procedure": optical["retrieval_procedure"],
                "retrieved_utc": optical["retrieved_utc"],
                "sha256": optical["sha256"], "size_bytes": optical["size_bytes"],
                "evidence_state_in_source": optical["evidence_state"]},
            "member": {
                "output_id": "rocit-zip#member",
                "source_key": "optical_inventory",
                "comparison": comparison["comparison"], "file": member["file"],
                "member_path": f"{comparison['comparison']}/{member['file']}",
                "n_samples": member["n_samples"],
                "mjd_first": member["mjd_first"], "mjd_last": member["mjd_last"],
                "sha256": None, "size_bytes": None,
                "absent_from_all_sources": (
                    "No per-member digest or size exists in any pinned source, or anywhere in "
                    "the repository. Step 2 establishes them.")},
            "n_retrieval_occurrences": 1, "n_outputs": 1},
    }


def main(argv):
    try:
        built = build()
    except SourceError as exc:
        print(f"FAIL source facts: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(built, indent=2, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if not os.path.exists(OUT):
            print(f"FAIL source facts: {OUT} is absent", file=sys.stderr)
            return 1
        with open(OUT, encoding="utf-8") as handle:
            committed = handle.read()
        if committed != text:
            print("FAIL source facts: committed file differs from freshly generated output",
                  file=sys.stderr)
            return 1
        print("WP2A source facts: PASS (committed output equals regenerated output)")
        return 0
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
