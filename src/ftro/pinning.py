#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Shared retrieval contract for the FTRO pinners.

Three rules, each of which was violated by at least one pinner before this module:

1. PREFLIGHT. Registry coverage is checked BEFORE any byte is fetched. pin_igs.py used to
   check coverage after caching all 57 files and constructing their pins, so an uncovered
   expectation still cached bytes and emitted a snapshot with null expectation fields.
2. ATOMIC PROMOTION. The report is written to a temporary path and promoted to the
   official path only on COMPLETE success. A failed run used to overwrite the official
   report, which a scientific consumer then read as normal input.
3. NO EXPECTATION, NO IDENTITY. A missing expectation is a failure, not a null field.
   Only an explicit --allow-unpinned establishes a first pin, and it is recorded.

See FTRO-DEF-031 v4.0.0 and D-045.
"""

import json
import os
import sys


class PreflightError(SystemExit):
    """Raised before any retrieval when the digest registry cannot cover the targets."""


def load_section(registry_path, section, required=True):
    """Return {key: sha256} for one section of the sectioned digest registry."""
    if not os.path.exists(registry_path):
        if required:
            raise PreflightError(
                f"preflight: no digest registry at {registry_path}; "
                f"pass --allow-unpinned only to establish a first pin")
        return {}
    with open(registry_path, encoding="utf-8") as fh:
        registry = json.load(fh)
    sect = registry.get(section)
    if sect is None:
        available = sorted(k for k, v in registry.items() if isinstance(v, dict))
        raise PreflightError(f"preflight: registry has no section {section!r}; "
                             f"sections present: {available}")
    if not sect and required:
        raise PreflightError(f"preflight: section {section!r} is empty")
    return {k: (v["sha256"] if isinstance(v, dict) else v) for k, v in sect.items()}


def preflight(expected, names, allow_unpinned=False, what="artifact"):
    """Refuse to fetch anything unless every target has an expected digest.

    Returns the list of uncovered names (empty unless allow_unpinned).
    """
    uncovered = [n for n in names if n not in expected]
    if uncovered and not allow_unpinned:
        raise PreflightError(
            f"preflight: {len(uncovered)} of {len(names)} {what}s have no expected digest "
            f"in the registry: {uncovered[:5]}{'...' if len(uncovered) > 5 else ''}. "
            f"Nothing was fetched. Add them to the registry, or pass --allow-unpinned to "
            f"establish a first pin.")
    return uncovered


def promote(report, out_path, ok):
    """Write the report atomically, promoting to out_path only on complete success.

    On failure the report is written beside the official path with a .rejected suffix so
    the evidence survives, and the official path is left untouched.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if not ok:
        rejected = out_path + ".rejected"
        with open(rejected, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"NOT PROMOTED: {out_path} left unchanged; rejected report at {rejected}",
              file=sys.stderr)
        return False
    tmp = out_path + ".part"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    os.replace(tmp, out_path)
    return True


def assert_report_usable(path, what="report"):
    """Consumer-side gate: refuse to build science on a report that is not a clean success.

    four_domain_intersection.py consumed the IGS report without checking any of this, so a
    failed run produced normal GNSS support.
    """
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    problems = []
    if doc.get("n_failed"):
        problems.append(f"n_failed={doc['n_failed']}")
    if doc.get("n_without_expected_digest"):
        problems.append(f"n_without_expected_digest={doc['n_without_expected_digest']}")
    rv = doc.get("retrieval_validation")
    if rv is not None and rv != "content_validated":
        problems.append(f"retrieval_validation={rv!r}")
    pins = doc.get("pins") if isinstance(doc.get("pins"), list) else [doc]
    bad = [p.get("name") or p.get("key") or p.get("session")
           for p in pins if p.get("checksum_match") is not True]
    if bad:
        problems.append(f"{len(bad)} pins without checksum_match=True: {bad[:5]}")
    if problems:
        raise SystemExit(f"{what} at {path} is not a clean success: {'; '.join(problems)}. "
                         f"Regenerate it before deriving results from it.")
    return doc
