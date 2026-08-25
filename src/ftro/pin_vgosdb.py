#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# FTRO Phase-1 VLBI vgosDB pinner.
#
# Retrieves an IVS vgosDB session archive from OPAR (Observatoire de Paris), an IVS data
# centre reachable anonymously, and records an FTRO snapshot identity with full digests.
#
# Content-shape validation is mandatory here (FTRO-DEF-018): the first attempt at this
# leg used CDDIS, which returns an Earthdata login page with HTTP 200. Status and
# checksum alone would have pinned that login page as if it were the session data.

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import urllib.request

GZIP_MAGIC = b"\x1f\x8b"
HTML_MARKERS = (b"<!DOCTYPE html", b"<!doctype html", b"<html", b"<HTML")


def main():
    """Return 0 only if the retrieval is content-valid AND matches any expected digest."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://ivsopar.obspm.fr/vlbi/ivsdata/vgosdb/2022/20220228-r11040.tgz")
    ap.add_argument("--session", default="R11040")
    ap.add_argument("--cache", default="data/raw/vlbi")
    ap.add_argument("--out", default="phase0/reports/vlbi-vgosdb-pin.json")
    ap.add_argument("--expect-sha256", default=None)
    args = ap.parse_args()

    os.makedirs(args.cache, exist_ok=True)
    dest = os.path.join(args.cache, os.path.basename(args.url))
    retrieved = datetime.datetime.now(datetime.timezone.utc).isoformat()

    req = urllib.request.Request(args.url, headers={"User-Agent": "FTRO-walking-skeleton/0.1"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        headers, body, status = dict(resp.headers), resp.read(), resp.status

    sha256 = hashlib.sha256(body).hexdigest()
    md5 = hashlib.md5(body).hexdigest()

    # --- content-shape validation, not status-and-checksum ---
    checks, members, wrappers = {}, [], []
    checks["gzip_magic"] = body[:2] == GZIP_MAGIC
    checks["not_html"] = not any(m in body[:2048] for m in HTML_MARKERS)
    try:
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tf:
            members = tf.getnames()
        checks["tar_readable"] = True
    except Exception as exc:                                     # noqa: BLE001
        checks["tar_readable"] = False
        checks["tar_error"] = f"{type(exc).__name__}: {exc}"
    # vgosDB wrapper files are named <session>_V<nnn>_i<CENTRE>_<band>.wrp -- the version
    # token is embedded, not a filename prefix.
    #
    # Filenames overstate distinct states: the same wrapper bytes are republished under a
    # different Institution designator. Key on the member digest, never the filename.
    wrapper_paths = sorted(m for m in members if m.endswith(".wrp"))
    wrappers = [os.path.basename(m) for m in wrapper_paths]
    wrapper_records, by_digest = [], {}
    try:
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tf:
            for mp in wrapper_paths:
                data = tf.extractfile(mp).read()
                dig = hashlib.sha256(data).hexdigest()
                run_tags = re.findall(rb"RunTimeTag\s+([0-9/]+\s+[0-9:]+\s*\w*)", data)
                inputs = re.findall(rb"InputWrapper\s+(\S+)", data)
                wrapper_records.append({
                    "path": mp, "name": os.path.basename(mp), "size_bytes": len(data),
                    "sha256": dig,
                    "run_time_tags": [t.decode(errors="replace").strip() for t in run_tags],
                    "input_wrappers": sorted({i.decode(errors="replace") for i in inputs}),
                })
                by_digest.setdefault(dig, []).append(os.path.basename(mp))
    except Exception as exc:                                     # noqa: BLE001
        checks["wrappers_readable"] = False
        checks["wrapper_error"] = f"{type(exc).__name__}: {exc}"

    versions = sorted({mm.group(1) for w in wrappers if (mm := re.search(r"_V(\d{3})_", w))})
    centres = sorted({mm.group(1) for w in wrappers
                      if (mm := re.search(r"_V\d{3}_i([A-Za-z]+)_", w))})
    # Centres that actually produced DISTINCT wrapper bytes, as opposed to a redesignation.
    producing_centres = sorted({re.search(r"_V\d{3}_i([A-Za-z]+)_", names[0]).group(1)
                                for names in by_digest.values()
                                if re.search(r"_V\d{3}_i([A-Za-z]+)_", names[0])})
    duplicate_groups = {d: n for d, n in by_digest.items() if len(n) > 1}
    checks["has_wrappers"] = bool(wrappers)
    checks["has_versioned_wrappers"] = bool(versions)
    checks["session_in_paths"] = any(args.session.lower() in m.lower() for m in members)
    ok = all(v for k, v in checks.items() if isinstance(v, bool))

    # Tri-state: None means "not checked", never a silent pass.
    checksum_match = None if args.expect_sha256 is None else (sha256 == args.expect_sha256)
    verified = ok and (checksum_match is not False)

    # Rejected bytes must never occupy the product filename in the cache.
    if verified:
        tmp = dest + ".part"
        with open(tmp, "wb") as fh:
            fh.write(body)
        os.replace(tmp, dest)

    pin = {
        "generator": "src/ftro/pin_vgosdb.py",
        "session": args.session,
        "url": args.url,
        "data_centre": "OPAR (Observatoire de Paris) IVS data centre, anonymous HTTPS",
        "http_status": status,
        "content_type": headers.get("Content-Type"),
        "last_modified": headers.get("Last-Modified"),
        "etag": headers.get("ETag"),
        "retrieved_utc": retrieved,
        "retrieval_procedure": f"GET {args.url}",
        "size_bytes": len(body),
        "sha256": sha256,
        "md5": md5,
        "expected_sha256": args.expect_sha256,
        "checksum_match": checksum_match,
        "retrieval_validation": "content_validated" if verified else "content_rejected",
        "content_checks": checks,
        "content_valid": ok,
        "n_members": len(members),
        "wrappers": wrappers,
        "wrapper_records": wrapper_records,
        "n_wrapper_filenames": len(wrappers),
        "n_distinct_wrapper_digests": len(by_digest),
        "duplicate_wrapper_groups": duplicate_groups,
        "internal_versions": versions,
        "institution_designators": centres,
        "producing_centres": producing_centres,
        "internal_version_note": (
            f"This archive carries {len(wrappers)} wrapper FILENAMES but only "
            f"{len(by_digest)} DISTINCT wrapper byte sequences: "
            + "; ".join(f"{' == '.join(n)}" for n in duplicate_groups.values())
            + f". Institution designators present are {', '.join(centres)}, but only "
            f"{', '.join(producing_centres)} produced distinct wrapper bytes -- the others are "
            "redesignations of identical content. A chain consuming 'the R11040 vgosDB' must "
            "name the wrapper MEMBER it used, keyed by member SHA-256 rather than filename; the "
            "archive checksum alone does not pin that choice. The wrapper format's own "
            "InputWrapper keyword records wrapper-to-wrapper derivation."),
        "concept_id": f"ftro:concept:ivs/session/{args.session}",
        "snapshot_id": f"ftro:snapshot:ivs/vgosdb/{os.path.basename(args.url)}@sha256:{sha256}",
        "snapshot_kind": "ftro_composed",
        "snapshot_note": ("OPAR supplies no immutable per-version PID for this archive, so task "
                          "card §10 requires an FTRO identity composed from concept id, "
                          "retrieval time, byte checksum and retrieval procedure."),
        # Profile §5.1: an ftro_composed identity must record what was checked and found absent.
        "composition_precondition_checked": [
            "OPAR directory listing - no per-file PID",
            "IVS session listing - no DOI or handle for the vgosDB",
            "HTTP ETag / Last-Modified - mutable, and this archive is a re-release",
        ],
        "composition_justification": ("No IVS data centre mints an immutable per-version PID for a "
                                      "vgosDB archive, so task card §10 composition applies."),
        "volatility_warning": (
            "This archive is a RE-RELEASE, not a frozen 2022 artifact. The internal anchor is the "
            "latest wrapper's RunTimeTag (see wrapper_records), which post-dates the session by "
            "years; the HTTP Last-Modified is secondary and dates mirror publication rather than "
            "the reprocessing act. The bytes may change again; the checksum pins THIS retrieval."),
    }
    # An unverified retrieval does not get to mint an identity.
    if not verified:
        for k in ("snapshot_id", "snapshot_kind", "snapshot_note",
                  "composition_precondition_checked", "composition_justification"):
            pin.pop(k, None)
        pin["rejected_reason"] = ("expected-checksum mismatch" if checksum_match is False
                                  else "content-shape validation failed")
        pin["bytes_written_to_cache"] = False
    else:
        pin["bytes_written_to_cache"] = True

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(pin, open(args.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: pin[k] for k in
                      ("size_bytes", "sha256", "checksum_match", "content_valid",
                       "last_modified", "n_members", "n_wrapper_filenames",
                       "n_distinct_wrapper_digests", "internal_versions",
                       "producing_centres")}, indent=2))
    print(f"wrote {args.out}")
    if not verified:
        print(f"REJECTED: {pin['rejected_reason']}", file=sys.stderr)
    return 0 if verified else 1


if __name__ == "__main__":
    sys.exit(main())
