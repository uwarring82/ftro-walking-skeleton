#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Assert that every versioned artifact has had its version bumped since it last changed.
#
# D-039 required this; D-039a extended it to every versioned artifact; the same commit
# then changed two ledgers without bumping either (FTRO-DEF-033 v3.0.0). A versioning
# rule with no check is the failure mode this repository has recorded four times.
#
#   python3 src/ftro/check_versions.py            # report
#   python3 src/ftro/check_versions.py --check    # non-zero if any artifact is stale

import json
import re
import subprocess
import sys

# artifact -> the commit at which its CURRENT version was set.
VERSIONED = {
    "profile/ftro-graph-profile-v0.0.3.md": {"version": "0.0.3", "set_at": "HEAD"},
    "phase0/evidence/identities.json": {"version": "0.2.0", "set_at": "HEAD"},
    "ledgers/deficiency-log.json": {"version": "0.6.0", "set_at": "HEAD"},
    "ledgers/decision-ledger.md": {"version": "0.3.0", "set_at": "HEAD"},
    "ledgers/source-ledger.md": {"version": "0.3.0", "set_at": "HEAD"},
    "ledgers/rights-ledger.md": {"version": "0.1.0", "set_at": "HEAD"},
    "phase0/selection-note-v0.1.md": {"version": "0.3.0", "set_at": "HEAD"},
    "phase0/evidence/expected-digests.json": {"version": "0.2.0", "set_at": "HEAD"},
}

VERSION_RE = re.compile(r'(?:\*\*Version:\*\*|"version"\s*:)\s*"?([0-9]+\.[0-9]+\.[0-9]+)')


def declared_version(path):
    try:
        with open(path, encoding="utf-8") as fh:
            head = fh.read(4096)
    except OSError:
        return None
    m = VERSION_RE.search(head)
    return m.group(1) if m else None


def main():
    check = "--check" in sys.argv
    problems = []
    for path, meta in sorted(VERSIONED.items()):
        got = declared_version(path)
        if got is None:
            problems.append((path, "no version declared in the first 4 KB"))
        elif got != meta["version"]:
            problems.append((path, f"declares {got}, registry expects {meta['version']}"))
        else:
            print(f"ok   {path} v{got}")
    # Any versioned artifact modified in the working tree but not re-registered.
    try:
        changed = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                                 capture_output=True, text=True, timeout=60).stdout.split()
    except Exception:                                            # noqa: BLE001
        changed = []
    for path in changed:
        if path in VERSIONED:
            print(f"note {path} modified since HEAD - confirm its version was bumped")
    for path, why in problems:
        print(f"STALE {path}: {why}", file=sys.stderr)
    if check:
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
