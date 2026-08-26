#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""One declarative schema for FTRO JSON artifacts.

Replaces hand-written field checks scattered across producers, consumers and tests.

Eight separate ledger entries -- FTRO-DEF-034, -038, -043, -047, -050, -056 and two
relatives -- were the same defect: absence accepted as success. Each was fixed by adding
another `if field not in doc` at a new site. Declaring the contract ONCE, and validating
the same declaration in the producer before promotion and in the consumer before use,
retires the family rather than its instances.

Rules the hand-written versions kept getting wrong, encoded here once:
  * absence is a failure, never a default;
  * bool is a subclass of int in Python, so an int check must exclude it;
  * a type guard must FAIL on the wrong type, not skip;
  * a count field must agree with the list it counts.
"""

import re

SHA256 = re.compile(r"[0-9a-f]{64}")


def _typename(v):
    return type(v).__name__


def _check_field(name, value, spec, problems):
    kind = spec.get("type")
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            problems.append(f"{name}={value!r} is {_typename(value)}, expected int")
            return
    elif kind == "str":
        if not isinstance(value, str):
            problems.append(f"{name}={value!r} is {_typename(value)}, expected str")
            return
    elif kind == "list":
        if not isinstance(value, list):
            problems.append(f"{name} is {_typename(value)}, expected list")
            return
    elif kind == "digest":
        if not (isinstance(value, str) and SHA256.fullmatch(value)):
            problems.append(f"{name}={value!r} is not a 64-character hex digest")
            return
    if "enum" in spec and value not in spec["enum"]:
        problems.append(f"{name}={value!r}, expected one of {tuple(spec['enum'])}")
    if "const" in spec and value != spec["const"]:
        problems.append(f"{name}={value!r}, expected {spec['const']!r}")


def validate(doc, spec, prefix=""):
    """Return a list of problems. Empty means conforming."""
    problems = []
    for name, fspec in spec.get("required", {}).items():
        if name not in doc:
            problems.append(f"{prefix}{name} absent (absence is not evidence of success)")
            continue
        _check_field(prefix + name, doc[name], fspec, problems)

    for counter, listname in spec.get("count_of", {}).items():
        if counter in doc and listname in doc and isinstance(doc[listname], list) \
                and isinstance(doc[counter], int) and not isinstance(doc[counter], bool):
            if doc[counter] != len(doc[listname]):
                problems.append(f"{prefix}{counter}={doc[counter]} but {listname} has "
                                f"{len(doc[listname])} entries")

    items = spec.get("items")
    if items:
        listname = items["in"]
        seq = doc.get(listname)
        if isinstance(seq, list):
            for i, item in enumerate(seq):
                if not isinstance(item, dict):
                    problems.append(f"{prefix}{listname}[{i}] is {_typename(item)}, "
                                    f"expected object")
                    continue
                problems += validate(item, items["spec"], prefix=f"{prefix}{listname}[{i}].")
    return problems


# ---------------------------------------------------------------------------
# The contracts. Declared once; used by producers and consumers alike.
# ---------------------------------------------------------------------------

PIN = {
    "required": {
        "sha256": {"type": "digest"},
        "expected_sha256": {"type": "digest"},
        "checksum_match": {"const": True},
        "retrieval_validation": {"type": "str", "const": "content_validated"},
        "retrieved_utc": {"type": "str"},
        "retrieval_procedure": {"type": "str"},
    },
}

PIN_REPORT = {
    "required": {
        "generator": {"type": "str"},
        "retrieval_validation": {"type": "str", "const": "content_validated"},
        "n_pinned": {"type": "int"},
        "n_failed": {"type": "int", "const": 0},
        "n_without_expected_digest": {"type": "int", "const": 0},
        "pins": {"type": "list"},
        "failures": {"type": "list"},
        "uncovered_by_registry": {"type": "list"},
    },
    "count_of": {"n_pinned": "pins", "n_failed": "failures",
                 "n_without_expected_digest": "uncovered_by_registry"},
    "items": {"in": "pins", "spec": PIN},
}
