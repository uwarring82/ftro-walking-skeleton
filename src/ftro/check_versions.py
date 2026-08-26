#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Assert that every changed versioned artifact declares a new version.

REPLACES a 280-line bespoke state machine with a registry file, --update and --register
flags, stored content digests and a special case for generated files. That machine
produced four separate defects of its own -- FTRO-DEF-039, -044, -055 and the
missing-entry laundering path -- each a way for the maintenance command to satisfy the
gate it maintained.

The trusted base is now git, which already records what changed and what the previous
content was. There is no registry to fall out of date, no flag that can weaken a check,
and no separate code path for generated documents.

    python3 src/ftro/check_versions.py            # report
    python3 src/ftro/check_versions.py --check    # non-zero if any artifact is stale
    python3 src/ftro/check_versions.py --base REF # compare against REF instead of HEAD
"""

import re
import subprocess
import sys

VERSION_RE = re.compile(
    r'(?:\*\*Version:\*\*|"version"\s*:|^\s*version\s*:)\s*["\']?([0-9]+\.[0-9]+\.[0-9]+)',
    re.MULTILINE)

# Documents whose version is set elsewhere, with the reason. Anything else that declares
# a version is checked; there is no opt-in list to fall behind.
EXCLUSIONS = {
    "Task Cards/Federated_Time_Reference_Observatory_Task_Card_v0.3.md":
        "the specification being implemented; versioned by its author",
    "CITATION.cff": "versioned by release; validated by cffconvert",
}
SKIP_PREFIXES = ("data/", "tests/", "LICENSES/", ".git/")


def _git(*args, ok=(0,)):
    r = subprocess.run(["git", *args], capture_output=True, text=True, timeout=120)
    if r.returncode not in ok:
        return None
    return r.stdout


def declared_version(text):
    m = VERSION_RE.search(text[:4096]) if text else None
    return m.group(1) if m else None


def main():
    check = "--check" in sys.argv
    base = "HEAD"
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1]

    changed = _git("diff", "--name-only", base)
    if changed is None:
        print("not a git repository, or the base ref is unknown; nothing to compare",
              file=sys.stderr)
        return 0

    problems, checked = [], 0
    for path in sorted(set(changed.split())):
        if path in EXCLUSIONS or path.startswith(SKIP_PREFIXES):
            continue
        if not path.endswith((".md", ".json", ".cff", ".yaml", ".yml")):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                now = fh.read(4096)
        except OSError:
            continue                       # deleted; nothing to version
        was = _git("show", f"{base}:{path}", ok=(0, 128))
        if was is None:
            continue                       # newly added; no previous version to advance
        v_now, v_was = declared_version(now), declared_version(was)
        if v_now is None and v_was is None:
            continue                       # unversioned document; not in scope
        checked += 1
        if v_now is None:
            problems.append((path, f"declared version {v_was} was removed"))
        elif v_was is None:
            # The document gained a version. Nothing to advance from; not a fault.
            print(f"ok   {path} (none) -> {v_now}")
        elif v_now == v_was:
            problems.append((path, f"content changed but version is still {v_now}"))
        else:
            try:
                if tuple(map(int, v_now.split("."))) < tuple(map(int, v_was.split("."))):
                    problems.append((path, f"version went backwards: {v_was} -> {v_now}"))
                    continue
            except ValueError:
                problems.append((path, f"unparseable version {v_now!r}"))
                continue
            print(f"ok   {path} {v_was} -> {v_now}")

    for path, why in problems:
        print(f"STALE {path}: {why}", file=sys.stderr)
    print(f"{checked} versioned artifact(s) changed since {base}; {len(problems)} stale")
    return 1 if (check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())
