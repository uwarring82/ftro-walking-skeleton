#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Refresh ro-crate-metadata.json contentSize values against disk.
#
# Session 03 claimed this refresh "is now a script" while no script was committed --
# the same class of unbacked claim as FTRO-DEF-027. This is that script.
#
# Hand-maintained size metadata drifts silently: a review reported one stale value and
# fifteen existed. Enumerate, never patch the reported one.

import datetime as dt
import hashlib
import json
import os
import stat
import sys
import tempfile

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

# These are living, bounded flat populations.  Checking only entities already in the graph
# made a newly added ledger snapshot, lab note or test invisible while `--check` reported
# "0 missing" (FTRO-P1-DEF-012).  Discovery is deliberately narrow: it does not turn the
# crate into an indiscriminate repository dump.
DISCOVERED_DOCUMENTS = {
    "labnotes": {".md"},
    "ledgers": {".json", ".md"},
    "tests": {".py"},
}

# Some bounded populations are also represented by an explicit collection entity.  Root
# membership alone is insufficient for those collections: adding a test must update both
# the Dataset and tests/ hasPart populations, or the two views drift.
DISCOVERED_COLLECTIONS = {
    "tests": "tests/",
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
# Maximum path-component count below a phase root, INCLUDING the file name.  Thus
# phase1/manifests/optical/ro-crate-metadata.json is exactly depth 3 and is included;
# phase1/a/b/c/file.json is depth 4 and is outside the bounded population.
MAX_DISCOVERY_DEPTH = 3
EXCLUDED_DIRECTORY_NAMES = {"__pycache__", ".ipynb_checkpoints"}
UNKNOWN_PHASE_SUFFIX_POLICY = "error"

PUBLICATION_CONTROL_ID = "#ftro-root-crate-publication-control"
PUBLICATION_FINGERPRINT_PREFIX = "sha256:"
CRATE_DATE_ENV = "FTRO_CRATE_DATE"


class DiscoveryPolicyError(ValueError):
    pass


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
    """Walk one bounded phase tree under an explicit, fail-closed file policy."""
    if UNKNOWN_PHASE_SUFFIX_POLICY != "error":
        raise DiscoveryPolicyError(
            f"unsupported phase suffix policy {UNKNOWN_PHASE_SUFFIX_POLICY!r}"
        )
    paths = []
    if not os.path.isdir(root):
        return paths
    for current, directories, names in os.walk(root):
        directories[:] = sorted(
            name for name in directories if name not in EXCLUDED_DIRECTORY_NAMES
        )
        directory_depth = (
            len(os.path.relpath(current, root).split(os.sep)) if current != root else 0
        )
        # Files in this directory are one component deeper than the directory.  Prune
        # children once files in the current directory are at the inclusive boundary.
        if directory_depth >= MAX_DISCOVERY_DEPTH - 1:
            directories[:] = []
        for name in sorted(names):
            suffix = os.path.splitext(name)[1]
            if suffix not in suffixes:
                path = os.path.join(current, name).replace(os.sep, "/")
                raise DiscoveryPolicyError(
                    f"unsupported file suffix {suffix!r} in bounded phase tree: {path}"
                )
            if directory_depth + 1 > MAX_DISCOVERY_DEPTH:
                continue
            path = os.path.join(current, name).replace(os.sep, "/")
            paths.append(path)
    return paths


CC_BY = "https://creativecommons.org/licenses/by/4.0/"
APACHE = "https://www.apache.org/licenses/LICENSE-2.0"

# Discovery originally declared every file as Markdown under CC BY, because it only ever ran
# over labnotes/ and ledgers/.  Extending it to the phase trees made that wrong: those trees
# hold .py, which is code under Apache-2.0, not a CC BY document (FTRO-P1-DEF-017).  A default
# that was merely narrow became a mislabelling as soon as the population widened.
SUFFIX_DECLARATION = {
    ".md": {"encodingFormat": "text/markdown", "license": CC_BY, "types": ["File"]},
    ".json": {"encodingFormat": "application/json", "license": CC_BY, "types": ["File"]},
    ".py": {"encodingFormat": "text/x-python", "license": APACHE,
            "types": ["File", "SoftwareSourceCode"]},
}


def document_entity(path):
    suffix = os.path.splitext(path)[1]
    if suffix not in SUFFIX_DECLARATION:
        raise ValueError(f"no declaration rule for suffix {suffix!r} ({path})")
    rule = SUFFIX_DECLARATION[suffix]
    entity = {
        "@id": path,
        "@type": rule["types"] if len(rule["types"]) > 1 else rule["types"][0],
        "name": os.path.basename(path),
        "encodingFormat": rule["encodingFormat"],
        "license": {"@id": rule["license"]},
    }
    if suffix == ".py":
        entity["programmingLanguage"] = {"@id": "#python-3.13"}
    return entity


def current_date():
    """Return the publication date, with a deterministic override for controlled runs."""
    value = os.environ.get(CRATE_DATE_ENV)
    if value is None:
        return dt.datetime.now(dt.timezone.utc).date().isoformat()
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{CRATE_DATE_ENV} must be YYYY-MM-DD, got {value!r}") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{CRATE_DATE_ENV} must be canonical YYYY-MM-DD, got {value!r}")
    return value


def direct_references(entity, key):
    value = entity.get(key, [])
    if isinstance(value, dict):
        value = [value]
    return [row.get("@id") for row in value if isinstance(row, dict) and row.get("@id")]


def add_reference(entity, key, target):
    value = entity.get(key)
    reference = {"@id": target}
    if value is None:
        entity[key] = reference
    elif isinstance(value, list):
        value.append(reference)
    else:
        entity[key] = [value, reference]


def publication_control_entity(date_modified, fingerprint="0" * 64):
    return {
        "@id": PUBLICATION_CONTROL_ID,
        "@type": "CreativeWork",
        "name": "FTRO root-crate publication control",
        "description": (
            "Deterministic SHA-256 over the root-crate graph (excluding only this node's "
            "self-referential identifier field) and every non-volatile local file entity. "
            "It detects same-size content drift and semantic edits to ro-crate-metadata.json."
        ),
        "identifier": PUBLICATION_FINGERPRINT_PREFIX + fingerprint,
        "dateModified": date_modified,
    }


def local_fingerprint_paths(crate):
    paths = []
    for entity in crate.get("@graph", []):
        path = entity.get("@id", "")
        if (not path or path == CRATE or path in VOLATILE_CONTENT_SIZE
                or path.startswith(("http://", "https://", "#"))
                or path == "./" or path.endswith("/")):
            continue
        if os.path.isfile(path):
            paths.append(path)
    return sorted(set(paths))


def publication_fingerprint(crate):
    """Hash crate semantics and declared local bytes without self-reference.

    The descriptor file's bytes cannot be hashed into a digest stored inside itself.  Its
    parsed graph, including root dateModified and the control node, is canonicalised instead;
    only the control node's self-referential identifier field is excluded.  All non-volatile
    local entities contribute their exact bytes, so equal-size edits remain observable.
    """
    projected = {
        key: value for key, value in crate.items() if key != "@graph"
    }
    projected_graph = []
    for entity in crate.get("@graph", []):
        if entity.get("@id") == PUBLICATION_CONTROL_ID:
            projected_graph.append({
                key: value for key, value in entity.items() if key != "identifier"
            })
        else:
            projected_graph.append(entity)
    projected["@graph"] = projected_graph
    canonical = json.dumps(
        projected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(b"FTRO root-crate publication fingerprint v1\0")
    digest.update(canonical)
    for path in local_fingerprint_paths(crate):
        digest.update(b"\0path\0")
        digest.update(path.encode("utf-8"))
        digest.update(b"\0sha256\0")
        with open(path, "rb") as handle:
            file_digest = hashlib.sha256()
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                file_digest.update(block)
        digest.update(file_digest.digest())
    return digest.hexdigest()


def write_crate_atomic(crate):
    """Publish a complete descriptor with no partial-write or overwrite window."""
    try:
        publication_mode = stat.S_IMODE(os.stat(CRATE).st_mode)
    except FileNotFoundError:
        publication_mode = 0o644
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".ro-crate-metadata.", suffix=".candidate", dir="."
    )
    temporary = os.path.abspath(temporary_name)
    try:
        os.fchmod(descriptor, publication_mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(crate, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, CRATE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check_only = "--check" in argv
    crate = json.load(open(CRATE, encoding="utf-8"))
    stale, missing, undeclared, added = [], [], [], []
    graph = {row.get("@id"): row for row in crate["@graph"]}
    try:
        discovered = discovered_documents()
        today = current_date()
    except (DiscoveryPolicyError, ValueError) as exc:
        print(f"PUBLICATION POLICY ERROR: {exc}", file=sys.stderr)
        return 1
    root = graph.get("./")
    root_parts = {row.get("@id") for row in root.get("hasPart", [])} if root else set()
    collection_parts = {}
    for directory, collection_id in DISCOVERED_COLLECTIONS.items():
        collection = graph.get(collection_id)
        collection_parts[directory] = (
            {row.get("@id") for row in collection.get("hasPart", [])}
            if collection else None
        )
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
        directory = path.split("/", 1)[0]
        if directory in DISCOVERED_COLLECTIONS:
            collection_id = DISCOVERED_COLLECTIONS[directory]
            members = collection_parts[directory]
            if members is None:
                undeclared.append(f"collection entity {collection_id} for {path}")
            elif path not in members:
                if check_only:
                    undeclared.append(f"{collection_id} hasPart {path}")
                else:
                    graph[collection_id].setdefault("hasPart", []).append({"@id": path})
                    members.add(path)
                    added.append(f"{collection_id} hasPart {path}")

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

    control = graph.get(PUBLICATION_CONTROL_ID)
    # The control describes a root Dataset publication.  Small unit fixtures that inspect
    # an isolated report without a root Dataset retain their historical, narrower scope.
    if root is not None and control is None:
        if check_only:
            undeclared.append(f"graph entity {PUBLICATION_CONTROL_ID}")
        else:
            initial_date = root.get("dateModified", today) if root else today
            control = publication_control_entity(initial_date)
            crate["@graph"].append(control)
            graph[PUBLICATION_CONTROL_ID] = control
            added.append(f"graph entity {PUBLICATION_CONTROL_ID}")
    if root is not None and PUBLICATION_CONTROL_ID not in direct_references(root, "subjectOf"):
        if check_only:
            undeclared.append(f"root subjectOf {PUBLICATION_CONTROL_ID}")
        else:
            add_reference(root, "subjectOf", PUBLICATION_CONTROL_ID)
            added.append(f"root subjectOf {PUBLICATION_CONTROL_ID}")

    if root is not None and control is not None:
        canonical_control = publication_control_entity(
            control.get("dateModified", root.get("dateModified", today))
        )
        static_control_fields = ("@id", "@type", "name", "description")
        for field in static_control_fields:
            expected_value = canonical_control[field]
            if control.get(field) != expected_value:
                stale.append((
                    f"{PUBLICATION_CONTROL_ID} {field}",
                    control.get(field),
                    expected_value,
                ))
                if not check_only:
                    control[field] = expected_value
        extra_control_fields = sorted(set(control) - set(canonical_control))
        if extra_control_fields:
            stale.append((
                f"{PUBLICATION_CONTROL_ID} extra fields",
                ", ".join(extra_control_fields),
                "none",
            ))
            if not check_only:
                for field in extra_control_fields:
                    del control[field]

        observed = publication_fingerprint(crate)
        expected_identifier = PUBLICATION_FINGERPRINT_PREFIX + observed
        stored_identifier = control.get("identifier")
        dates_agree = control.get("dateModified") == root.get("dateModified")
        fingerprint_changed = stored_identifier != expected_identifier
        if check_only:
            if fingerprint_changed:
                stale.append((
                    f"{PUBLICATION_CONTROL_ID} identifier",
                    stored_identifier,
                    expected_identifier,
                ))
            if not dates_agree:
                stale.append((
                    f"{PUBLICATION_CONTROL_ID} dateModified",
                    control.get("dateModified"),
                    root.get("dateModified"),
                ))
            if fingerprint_changed and root.get("dateModified") != today:
                stale.append((
                    "./ dateModified", root.get("dateModified"), f"{today} (on next write)"
                ))
        elif fingerprint_changed or not dates_agree:
            previous_date = root.get("dateModified")
            root["dateModified"] = today
            control["dateModified"] = today
            control["identifier"] = (
                PUBLICATION_FINGERPRINT_PREFIX + publication_fingerprint(crate)
            )
            if previous_date != today:
                stale.append(("./ dateModified", previous_date, today))

    write_blocked = bool(missing or undeclared)
    for i, was, now in stale:
        action = "STALE" if check_only else "not written" if write_blocked else "updated"
        print(f"{action}: {i} {was} -> {now}")
    for i in missing:
        print(f"MISSING FILE for graph entity: {i}", file=sys.stderr)
    for item in undeclared:
        print(f"UNDECLARED BOUNDED DOCUMENT: {item}", file=sys.stderr)
    for item in added:
        print(f"added: {item}")

    if check_only:
        print(f"{len(stale)} stale, {len(missing) + len(undeclared)} missing")
        return 1 if (stale or missing or undeclared) else 0

    # Publication is transactional at the descriptor boundary.  All mutations above are
    # in-memory; a failed completeness check must leave the official crate byte-identical.
    if write_blocked:
        print("publication rejected; ro-crate-metadata.json left unchanged", file=sys.stderr)
        return 1

    try:
        write_crate_atomic(crate)
    except OSError as exc:
        print(f"publication failed; ro-crate-metadata.json left unchanged: {exc}", file=sys.stderr)
        return 1
    print(f"refreshed {len(stale)} metadata values; {len(added)} declarations added; "
          f"{len(missing) + len(undeclared)} missing")
    return 1 if (missing or undeclared) else 0


if __name__ == "__main__":
    sys.exit(main())
