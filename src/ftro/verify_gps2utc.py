#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO verification procedure VP-GPS2UTC-001 (v1.0.0).
#
# Named, versioned procedure evaluating the pinned IPTA T2runtime/clock/gps2utc.clk
# artifact. Emits a VerificationActivity record with result in
# {supports, contradicts, indeterminate}, per FTRO profile section 11.4.
#
# Subject of verification:
#   "For the interval [mjd_start, mjd_end], gps2utc.clk supplies GPS->UTC corrections
#    derived from the BIPM C0' (almanac-steered) realisation rather than C0
#    (GPS Combined Clock)."
#
# The procedure inspects the artifact's own regime-marker comments and the byte
# checksum. It does NOT assess whether any particular receiver tracked C0 or C0';
# that is a separate ApplicabilityAssessment, because the artifact itself states
# "This may or may not resemble what your GPS receiver system uses."

import argparse
import hashlib
import json
import re
import sys

PROCEDURE_ID = "VP-GPS2UTC-001"
PROCEDURE_VERSION = "1.0.0"
C0_PRIME_MARKER = re.compile(r"based on\s+C0'\s+values", re.I)
C0_MARKER = re.compile(r"based on\s+C0\s+values", re.I)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    """Return (regimes, rows). regimes: list of (line_no, regime). rows: (line_no, mjd, value)."""
    regimes, rows = [], []
    current = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if C0_PRIME_MARKER.search(s):
                    current = "C0'"
                    regimes.append((lineno, current))
                elif C0_MARKER.search(s):
                    current = "C0"
                    regimes.append((lineno, current))
                continue
            parts = s.split()
            if len(parts) < 2:
                continue
            try:
                rows.append((lineno, float(parts[0]), float(parts[1]), current))
            except ValueError:
                continue
    return regimes, rows


def main():
    ap = argparse.ArgumentParser(description=f"{PROCEDURE_ID} v{PROCEDURE_VERSION}")
    ap.add_argument("--file", required=True)
    ap.add_argument("--mjd-start", type=float, required=True)
    ap.add_argument("--mjd-end", type=float, required=True)
    ap.add_argument("--expect-sha256", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    digest = sha256(args.file)
    checksum_ok = (args.expect_sha256 is None) or (digest == args.expect_sha256)

    regimes, rows = load(args.file)
    window = [r for r in rows if args.mjd_start <= r[1] <= args.mjd_end]
    regimes_in_window = sorted({r[3] for r in window if r[3] is not None})

    # Data-integrity checks on the artifact itself.
    seen, duplicates = {}, []
    prev_mjd, non_monotonic = None, []
    for lineno, mjd, val, reg in rows:
        if mjd in seen:
            duplicates.append({"mjd": mjd, "lines": [seen[mjd][0], lineno],
                               "values": [seen[mjd][1], val],
                               "regimes": [seen[mjd][2], reg],
                               "value_difference_s": val - seen[mjd][1]})
        else:
            seen[mjd] = (lineno, val, reg)
        if prev_mjd is not None and mjd < prev_mjd:
            non_monotonic.append({"line": lineno, "mjd": mjd, "previous_mjd": prev_mjd})
        prev_mjd = mjd

    gaps = []
    wm = sorted(r[1] for r in window)
    for a, b in zip(wm, wm[1:]):
        if b - a > 1.0:
            gaps.append({"after_mjd": a, "before_mjd": b, "gap_days": round(b - a, 6)})

    if not checksum_ok:
        result, reason = "indeterminate", "artifact checksum does not match the pinned value"
    elif not window:
        result, reason = "indeterminate", "no samples inside the requested interval"
    elif regimes_in_window == ["C0'"]:
        result, reason = "supports", "every sample in the interval lies inside a C0' regime block"
    elif regimes_in_window == ["C0"]:
        result, reason = "contradicts", "every sample in the interval lies inside a C0 regime block"
    else:
        result, reason = "indeterminate", f"interval spans mixed or unmarked regimes: {regimes_in_window}"

    activity = {
        "@type": "VerificationActivity",
        "procedure_id": PROCEDURE_ID,
        "procedure_version": PROCEDURE_VERSION,
        "subject": ("gps2utc.clk supplies C0'-derived GPS->UTC corrections over "
                    f"MJD [{args.mjd_start}, {args.mjd_end}]"),
        "artifact": args.file,
        "artifact_sha256": digest,
        "expected_sha256": args.expect_sha256,
        "checksum_match": checksum_ok,
        "result": result,
        "reason": reason,
        "interval_mjd": [args.mjd_start, args.mjd_end],
        "n_samples_in_interval": len(window),
        "regimes_in_interval": regimes_in_window,
        "regime_markers": [{"line": ln, "regime": rg} for ln, rg in regimes],
        "artifact_mjd_first": min((r[1] for r in rows), default=None),
        "artifact_mjd_last": max((r[1] for r in rows), default=None),
        "n_rows_total": len(rows),
        "duplicate_abscissae": duplicates,
        "non_monotonic_rows": non_monotonic,
        "gaps_in_interval_days": gaps,
        "sampling_note": "artifact is tabulated at 1-day cadence; sub-daily use requires interpolation",
    }
    out = json.dumps(activity, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
