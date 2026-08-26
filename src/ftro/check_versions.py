#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assert that no versioned artifact has changed since its version was last set.

The first version of this gate stored `set_at: "HEAD"` and never used it: it compared each
document's declared version against a hard-coded copy of the same string, so the two agreed
by construction. Changing a document's content without bumping its version passed. A
working-tree change produced only a non-failing note, and no test invoked the checker at
all (FTRO-DEF-033 v4.0.0).

This version stores a CONTENT DIGEST taken when the version was set. Any content change
without a version bump is then detectable, because the digest no longer matches.

    python3 src/ftro/check_versions.py --check    # non-zero if any artifact is stale
    python3 src/ftro/check_versions.py --update   # re-record digests after a deliberate bump
"""

import hashlib
import json
import os
import re
import sys

REGISTRY = "phase0/evidence/versioned-artifacts.json"
VERSION_RE = re.compile(r'(?:\*\*Version:\*\*|"version"\s*:)\s*"?([0-9]+\.[0-9]+\.[0-9]+)')


def declared_version(path):
    """The version the document declares in its own header."""
    try:
        with open(path, encoding="utf-8") as fh:
            head = fh.read(4096)
    except OSError:
        return None
    m = VERSION_RE.search(head)
    return m.group(1) if m else None


def content_digest(path):
    """Digest of the whole file, so any substantive change is visible."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# Documents deliberately excluded from version tracking, with the reason. Anything that
# declares a version and is not here MUST be registered: a manual list with no
# completeness check tracked twelve files while three applicability assessments declared
# versions and were silently unwatched (FTRO-DEF-040).
EXCLUSIONS = {
    "Task Cards/Federated_Time_Reference_Observatory_Task_Card_v0.3.md":
        "the specification being implemented; versioned by its author, not by this repo",
    "CITATION.cff": "versioned by release, validated by cffconvert instead",
    "ledgers/deficiency-log.md":
        "generated from deficiency-log.json, which IS tracked; regenerating it is not a "
        "content change requiring a bump",
    "phase0/optical-validity-intervals.md":
        "generated from optical-inventory-summary.json by render_validity_intervals.py",
    "phase0/evidence/versioned-artifacts.json":
        "this registry itself; its version field is a false positive from the versions it "
        "records, and tracking it would be self-referential",
}
SEARCH_ROOTS = ("phase0", "ledgers", "profile", "charter")


def discover_versioned(roots=SEARCH_ROOTS):
    """Every tracked-directory document that declares a version in its first 4 KB."""
    found = {}
    for root in roots:
        for dirpath, _dirs, files in os.walk(root):
            for fn in sorted(files):
                if not fn.endswith((".md", ".json")):
                    continue
                path = os.path.join(dirpath, fn)
                v = declared_version(path)
                if v:
                    found[path] = v
    return found


def audit(registry):
    """Return (problems, current) without mutating anything."""
    problems, current = [], {}
    for path, rec in sorted(registry.items()):
        if not os.path.exists(path):
            problems.append((path, "registered but missing from the working tree"))
            continue
        got_v, got_d = declared_version(path), content_digest(path)
        current[path] = {"version": got_v, "sha256": got_d}
        if got_v is None:
            problems.append((path, "no version declared in the first 4 KB"))
            continue
        if got_v != rec["version"]:
            problems.append((path, f"declares {got_v}, registry recorded {rec['version']}; "
                                   f"run --update after a deliberate bump"))
        elif got_d != rec["sha256"]:
            problems.append((path, f"content changed but version is still {got_v}: "
                                   f"recorded {rec['sha256'][:12]}, now {got_d[:12]}"))
    return problems, current


def main():
    check = "--check" in sys.argv
    update = "--update" in sys.argv
    # Initial registration is a separate, explicit path -- not a side effect of --update.
    register_new = "--register" in sys.argv
    if not os.path.exists(REGISTRY):
        print(f"no registry at {REGISTRY}; run --update to create it", file=sys.stderr)
        return 2
    with open(REGISTRY, encoding="utf-8") as fh:
        registry = json.load(fh)["artifacts"]

    problems, current = audit(registry)

    # Completeness: a document that declares a version must be tracked.
    for path, v in sorted(discover_versioned().items()):
        if path in registry or path in EXCLUSIONS:
            continue
        problems.append((path, f"declares version {v} but is not in the registry; "
                               f"add it or record an explicit exclusion"))

    if update:
        # --update re-records a DELIBERATE bump. It must not be usable to launder a
        # content change made under the same version: the first version replaced both
        # fields unconditionally, so `--check` then passed on unbumped drift
        # (FTRO-DEF-039).
        laundered = []
        for path, cur in current.items():
            rec = registry.get(path)
            if rec and cur["version"] == rec["version"] and cur["sha256"] != rec["sha256"]:
                laundered.append(path)
        if laundered and not register_new:
            for path in laundered:
                print(f"REFUSED {path}: content changed but version is still "
                      f"{current[path]['version']}. Bump the version, then --update.",
                      file=sys.stderr)
            return 1
        for path, cur in current.items():
            registry[path] = {"version": cur["version"], "sha256": cur["sha256"]}
        with open(REGISTRY, encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["artifacts"] = registry
        with open(REGISTRY, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        print(f"re-recorded {len(registry)} artifacts")
        return 0

    for path, rec in sorted(registry.items()):
        if not any(p == path for p, _ in problems):
            print(f"ok   {path} v{rec['version']}")
    for path, why in problems:
        print(f"STALE {path}: {why}", file=sys.stderr)
    if problems:
        print(f"{len(problems)} versioned artifact(s) stale", file=sys.stderr)
    return 1 if (check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
