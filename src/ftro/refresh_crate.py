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


def main():
    check_only = "--check" in sys.argv
    crate = json.load(open(CRATE, encoding="utf-8"))
    stale, missing = [], []
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

    if check_only:
        print(f"{len(stale)} stale, {len(missing)} missing")
        return 1 if (stale or missing) else 0

    json.dump(crate, open(CRATE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"refreshed {len(stale)} contentSize values; {len(missing)} missing files")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
