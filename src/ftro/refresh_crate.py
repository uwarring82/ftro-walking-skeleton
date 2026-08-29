#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Refresh ro-crate-metadata.json contentSize values against disk.
#
# Session 03 claimed this refresh "is now a script" while no script was committed --
# the same class of unbacked claim as FTRO-DEF-027. This is that script.
#
# Hand-maintained size metadata drifts silently: a review reported one stale value and
# fifteen existed. Enumerate, never patch the reported one.

import json
import os
import sys

CRATE = "ro-crate-metadata.json"

# These reports are deliberately regenerated against live providers.  Retrieval times
# and HTTP metadata can change their JSON byte length even when every pinned payload is
# identical.  RO-Crate 1.3 makes contentSize optional; omitting it prevents the final
# `--check` command from turning benign live metadata-length drift into a C9 failure.
VOLATILE_CONTENT_SIZE = {
    "phase0/reports/evidence-repo-pins.json",
    "phase0/reports/igs-artifact-pins.json",
    "phase0/reports/ppta-artifact-pins.json",
    "phase0/reports/vlbi-vgosdb-pin.json",
}

# These are living, bounded document populations.  Checking only entities already in the
# graph made a newly added ledger snapshot and lab note invisible while `--check` reported
# "0 missing" (FTRO-P1-DEF-012).  Discovery is deliberately narrow: it does not turn the
# crate into an indiscriminate repository dump.
DISCOVERED_DOCUMENTS = {
    "labnotes": {".md"},
    "ledgers": {".json", ".md"},
}

# The phase working trees are living populations too, but nested: phase1/reports/,
# phase1/manifests/<domain>/, phase2/wp2a/.  Flat discovery could not see them, so seven
# Phase-1 reports stayed undeclared while `--check` reported "0 missing", and Phase 2 was
# complete only because entities were added by hand (FTRO-P1-DEF-014).  A rule nothing
# enforces is not a rule.  Recursion is bounded by an explicit suffix set and a fixed
# depth so the crate does not become an indiscriminate repository dump.
DISCOVERED_TREES = {
    "phase1": {".md", ".json", ".py"},
    "phase2": {".md", ".json", ".py"},
}
MAX_DISCOVERY_DEPTH = 3
EXCLUDED_DIRECTORY_NAMES = {"__pycache__", ".ipynb_checkpoints"}


def discovered_documents():
    paths = []
    for directory, suffixes in DISCOVERED_DOCUMENTS.items():
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path) and os.path.splitext(name)[1] in suffixes:
                paths.append(path)
    for directory, suffixes in DISCOVERED_TREES.items():
        paths.extend(discovered_tree(directory, suffixes))
    return sorted(set(paths))


def discovered_tree(root, suffixes):
    """Walk one bounded phase tree.  Depth and suffixes are both explicit limits."""
    paths = []
    if not os.path.isdir(root):
        return paths
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            name for name in directories if name not in EXCLUDED_DIRECTORY_NAMES
        )
        depth = len(os.path.relpath(current, root).split(os.sep)) if current != root else 0
        if depth >= MAX_DISCOVERY_DEPTH:
            directories[:] = []
        for name in sorted(names):
            if os.path.splitext(name)[1] not in suffixes:
                continue
            path = os.path.join(current, name).replace(os.sep, "/")
            paths.append(path)
    return paths


def document_entity(path):
    suffix = os.path.splitext(path)[1]
    return {
        "@id": path,
        "@type": "File",
        "name": os.path.basename(path),
        "encodingFormat": "application/json" if suffix == ".json" else "text/markdown",
        "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"},
    }


def main():
    check_only = "--check" in sys.argv
    crate = json.load(open(CRATE, encoding="utf-8"))
    stale, missing, undeclared, added = [], [], [], []
    graph = {row.get("@id"): row for row in crate["@graph"]}
    discovered = discovered_documents()
    root = graph.get("./")
    root_parts = {row.get("@id") for row in root.get("hasPart", [])} if root else set()
    for path in discovered:
        if path not in graph:
            if check_only:
                undeclared.append(f"graph entity {path}")
            else:
                entity = document_entity(path)
                crate["@graph"].append(entity)
                graph[path] = entity
                added.append(f"graph entity {path}")
        if root is None:
            undeclared.append(f"root Dataset for discovered document {path}")
        elif path not in root_parts:
            if check_only:
                undeclared.append(f"root hasPart {path}")
            else:
                root.setdefault("hasPart", []).append({"@id": path})
                root_parts.add(path)
                added.append(f"root hasPart {path}")

    for e in crate["@graph"]:
        i = e.get("@id", "")
        if i.startswith(("http", "#")) or i.endswith("/") or i == "./":
            continue
        if "name" not in e:
            e["name"] = os.path.basename(i)
        if i == CRATE:
            e.pop("contentSize", None)      # self-referential: never settles
            continue
        if i in VOLATILE_CONTENT_SIZE:
            if "contentSize" in e:
                stale.append((i, e.pop("contentSize"), "omitted (volatile live report)"))
            continue
        if not os.path.exists(i):
            missing.append(i)
            continue
        actual = str(os.path.getsize(i))
        if e.get("contentSize") != actual:
            stale.append((i, e.get("contentSize"), actual))
            e["contentSize"] = actual

    for i, was, now in stale:
        print(f"{'STALE' if check_only else 'updated'}: {i} {was} -> {now}")
    for i in missing:
        print(f"MISSING FILE for graph entity: {i}", file=sys.stderr)
    for item in undeclared:
        print(f"UNDECLARED BOUNDED DOCUMENT: {item}", file=sys.stderr)
    for item in added:
        print(f"added: {item}")

    if check_only:
        print(f"{len(stale)} stale, {len(missing) + len(undeclared)} missing")
        return 1 if (stale or missing or undeclared) else 0

    json.dump(crate, open(CRATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"refreshed {len(stale)} contentSize values; {len(added)} declarations added; "
          f"{len(missing) + len(undeclared)} missing")
    return 1 if (missing or undeclared) else 0


if __name__ == "__main__":
    sys.exit(main())
