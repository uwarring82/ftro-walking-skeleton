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
import re
import sys

SHA256_RE = re.compile(r"[0-9a-f]{64}")


def valid_digest(value):
    """A digest is EXACTLY 64 lowercase hex characters.

    fullmatch, not match: `re.match` with a trailing `$` also accepts a trailing newline,
    so a digest read from a file with its newline intact validated (FTRO-DEF-051).
    """
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


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
    """Refuse to fetch anything unless every target has a WELL-FORMED expected digest.

    Key membership is not enough: a registry entry of null, "" or a truncated string is
    not an expectation. Checking membership alone let {"x.tgz": null} through preflight,
    after which the pinner cached bytes, promoted its report and minted an identity
    carrying expected_sha256: null (FTRO-DEF-042).

    Returns the list of uncovered names (empty unless allow_unpinned).
    """
    missing = [n for n in names if n not in expected]
    malformed = [n for n in names if n in expected and not valid_digest(expected[n])]

    if malformed:
        # A malformed expectation is always fatal: --allow-unpinned means "no expectation
        # recorded yet", not "an expectation that is not a digest".
        raise PreflightError(
            f"preflight: {len(malformed)} {what} expectation(s) are not 64-character hex "
            f"digests: "
            + ", ".join(f"{n}={expected[n]!r}" for n in malformed[:5])
            + f"{' ...' if len(malformed) > 5 else ''}. Nothing was fetched.")

    if missing and not allow_unpinned:
        raise PreflightError(
            f"preflight: {len(missing)} of {len(names)} {what}s have no expected digest "
            f"in the registry: {missing[:5]}{'...' if len(missing) > 5 else ''}. "
            f"Nothing was fetched. Add them to the registry, or pass --allow-unpinned to "
            f"establish a first pin.")
    return missing


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


# Fields a report MUST declare for a consumer to trust it, with their required values.
# Absence is a failure, not a zero: the first version used `.get()` truthiness, so a
# report that simply omitted n_failed or retrieval_validation was accepted (FTRO-DEF-038).
REQUIRED_REPORT_STATE = {
    "retrieval_validation": ("content_validated",),
    "n_failed": (0,),
    "n_without_expected_digest": (0,),
}


def _registry_digests(registry_path, section):
    try:
        with open(registry_path, encoding="utf-8") as fh:
            sect = json.load(fh).get(section) or {}
    except (OSError, json.JSONDecodeError):
        return None
    return {k: (v["sha256"] if isinstance(v, dict) else v) for k, v in sect.items()}


def assert_report_usable(path, what="report", registry=None, section=None, key=None):
    """Consumer gate. With `registry`/`section` it also checks COMPLETENESS.

    Without them the gate verifies only a report's self-description: truncating the IGS
    report to one pin and setting n_pinned: 1 was accepted, as was rewriting a pin's
    actual AND expected digest to the same fabricated value, because nothing external was
    consulted (FTRO-DEF-054). `key` maps a pin to its registry name.
    """
    """Consumer-side gate: refuse to build science on a report that is not a clean success.

    Every required field must be PRESENT, of the right type, and hold a permitted value.
    four_domain_intersection.py originally consumed the IGS report without checking any of
    this, so a failed run produced normal GNSS support; the first gate then accepted a
    report that omitted the state entirely.
    """
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    problems = []

    for field, allowed in REQUIRED_REPORT_STATE.items():
        if field not in doc:
            problems.append(f"{field} absent (absence is not evidence of success)")
            continue
        value = doc[field]
        exemplar = allowed[0]
        if isinstance(exemplar, int):
            # bool is a subclass of int, so isinstance(False, int) is True and JSON
            # `false` was accepted as zero (FTRO-DEF-043).
            if isinstance(value, bool) or not isinstance(value, int):
                problems.append(f"{field}={value!r} is {type(value).__name__}, expected int")
                continue
        elif isinstance(exemplar, str) and not isinstance(value, str):
            problems.append(f"{field}={value!r} is {type(value).__name__}, expected str")
            continue
        if value not in allowed:
            problems.append(f"{field}={value!r}, expected one of {allowed}")

    # Container shape, explicitly. The coherence checks below previously ran only when a
    # field was ALREADY a list, so failures: {} and uncovered_by_registry: "ghost" both
    # passed, and adding pins: {} to a single-pin report was ignored (FTRO-DEF-056).
    if "pins" in doc:
        if not isinstance(doc["pins"], list):
            problems.append(f"pins is {type(doc['pins']).__name__}, expected list")
            pins = []
        else:
            pins = doc["pins"]
            for i, p in enumerate(pins):
                if not isinstance(p, dict):
                    problems.append(f"pins[{i}] is {type(p).__name__}, expected object")
            pins = [p for p in pins if isinstance(p, dict)]
    elif "sha256" in doc:
        pins = [doc]
    else:
        problems.append("report declares neither a pins list nor a single pin")
        pins = []
    if not pins and "pins" not in doc and "sha256" not in doc:
        pass
    elif not pins:
        problems.append("report contains no usable pins")
    # A declared count that disagrees with the pins is a report describing something
    # other than itself.
    # n_pinned must be PRESENT and a true int. Absence passed; 57.0 == 57 and True == 1
    # both compared equal, so a float or a boolean satisfied the count (FTRO-DEF-050).
    if "n_pinned" not in doc:
        problems.append("n_pinned absent (absence is not evidence of a complete report)")
    elif isinstance(doc["n_pinned"], bool) or not isinstance(doc["n_pinned"], int):
        problems.append(f"n_pinned={doc['n_pinned']!r} is {type(doc['n_pinned']).__name__}, "
                        f"expected int")
    elif doc["n_pinned"] != len(pins):
        problems.append(f"n_pinned={doc['n_pinned']} but the report carries {len(pins)} pins")

    # A zero counter beside a non-empty list is a report contradicting itself.
    for lst, counter in (("failures", "n_failed"),
                         ("uncovered_by_registry", "n_without_expected_digest")):
        if lst not in doc:
            problems.append(f"{lst} absent (its counter {counter} is required, so the list is too)")
        elif not isinstance(doc[lst], list):
            problems.append(f"{lst} is {type(doc[lst]).__name__}, expected list")
        elif len(doc[lst]) != doc.get(counter, 0):
            problems.append(f"{lst} has {len(doc[lst])} entries but {counter}="
                            f"{doc.get(counter)!r}")

    for p in pins:
        label = p.get("name") or p.get("key") or p.get("session") or "<unnamed>"
        if p.get("checksum_match") is not True:
            problems.append(f"pin {label}: checksum_match={p.get('checksum_match')!r}, "
                            f"expected True")
        if not valid_digest(p.get("expected_sha256")):
            problems.append(f"pin {label}: expected_sha256={p.get('expected_sha256')!r} "
                            f"is not a 64-character hex digest")
        if not valid_digest(p.get("sha256")):
            problems.append(f"pin {label}: sha256={p.get('sha256')!r} "
                            f"is not a 64-character hex digest")
        elif valid_digest(p.get("expected_sha256")) and p["sha256"] != p["expected_sha256"]:
            problems.append(f"pin {label}: sha256 disagrees with expected_sha256 while "
                            f"checksum_match claims True")
        # Profile §9.2 requires retrieval_validation on EVERY record. Permitting its
        # absence inside pins repeated the DEF-034 failure one level down.
        if "retrieval_validation" not in p:
            problems.append(f"pin {label}: retrieval_validation absent")
        elif p["retrieval_validation"] != "content_validated":
            problems.append(f"pin {label}: retrieval_validation={p['retrieval_validation']!r}")

    # Completeness against the expected registry: which artifacts must be present, and
    # what their digests must be. A self-consistent report is not necessarily a complete
    # or truthful one.
    if registry and section:
        expected = _registry_digests(registry, section)
        if expected is None:
            problems.append(f"expected-digest registry {registry} is unreadable")
        else:
            keyfn = key or (lambda p: p.get("name"))
            got = [keyfn(p) for p in pins]
            dupes = sorted({n for n in got if got.count(n) > 1})
            missing = sorted(set(expected) - set(got))
            unknown = sorted(set(got) - set(expected))
            if dupes:
                problems.append(f"duplicate pins: {dupes[:5]}")
            if missing:
                problems.append(f"{len(missing)} artifact(s) in the registry are absent "
                                f"from the report: {missing[:5]}")
            if unknown:
                problems.append(f"{len(unknown)} pin(s) are not in the registry: {unknown[:5]}")
            for p in pins:
                n = keyfn(p)
                if n in expected and p.get("sha256") != expected[n]:
                    problems.append(f"pin {n}: sha256 does not match the registry digest")

    if problems:
        raise SystemExit(f"{what} at {path} is not a clean success: {'; '.join(problems[:6])}"
                         f"{' ...' if len(problems) > 6 else ''}. "
                         f"Regenerate it before deriving results from it.")
    return doc
