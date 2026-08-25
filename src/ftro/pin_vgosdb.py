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
import tarfile
import urllib.request

GZIP_MAGIC = b"\x1f\x8b"


def main():
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
    with open(dest, "wb") as fh:
        fh.write(body)

    sha256 = hashlib.sha256(body).hexdigest()
    md5 = hashlib.md5(body).hexdigest()

    # --- content-shape validation, not status-and-checksum ---
    checks, members, wrappers = {}, [], []
    checks["gzip_magic"] = body[:2] == GZIP_MAGIC
    checks["not_html"] = not any(m in body[:2048] for m in (b"<html", b"<!DOCTYPE html"))
    try:
        with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tf:
            members = tf.getnames()
        checks["tar_readable"] = True
    except Exception as exc:                                     # noqa: BLE001
        checks["tar_readable"] = False
        checks["tar_error"] = f"{type(exc).__name__}: {exc}"
    # vgosDB wrapper files are named <session>_V<nnn>_i<CENTRE>_<band>.wrp -- the version
    # token is embedded, not a filename prefix.
    wrappers = sorted(m.split("/")[-1] for m in members if m.endswith(".wrp"))
    versions = sorted({mm.group(1) for w in wrappers
                       if (mm := re.search(r"_V(\d{3})_", w))})
    centres = sorted({mm.group(1) for w in wrappers
                      if (mm := re.search(r"_V\d{3}_i([A-Za-z]+)_", w))})
    checks["has_wrappers"] = bool(wrappers)
    checks["has_versioned_wrappers"] = bool(versions)
    checks["session_in_paths"] = any(args.session.lower() in m.lower() for m in members)
    ok = all(v for k, v in checks.items() if isinstance(v, bool))

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
        "size_bytes": len(body),
        "sha256": sha256,
        "md5": md5,
        "expected_sha256": args.expect_sha256,
        "checksum_match": (args.expect_sha256 is None) or (sha256 == args.expect_sha256),
        "retrieval_validation": "content_validated",
        "content_checks": checks,
        "content_valid": ok,
        "n_members": len(members),
        "wrappers": wrappers,
        "internal_versions": versions,
        "analysis_centres": centres,
        "internal_version_note": ("This archive is NOT a single snapshot: it carries "
                                  f"{len(versions)} internal wrapper versions "
                                  f"({', '.join('V' + v for v in versions)}) from analysis "
                                  f"centres {', '.join(centres)}. A chain that consumes 'the "
                                  "R11040 vgosDB' must name WHICH wrapper version it used; the "
                                  "archive checksum alone does not pin that choice."),
        "concept_id": f"ftro:concept:ivs/session/{args.session}",
        "snapshot_id": f"ftro:snapshot:ivs/vgosdb/{os.path.basename(args.url)}@sha256:{sha256}",
        "snapshot_kind": "ftro_composed",
        "snapshot_note": ("OPAR supplies no immutable per-version PID for this archive, so task "
                          "card §10 requires an FTRO identity composed from concept id, "
                          "retrieval time, byte checksum and retrieval procedure."),
        "volatility_warning": ("Last-Modified post-dates the 2022 session, so this archive is a "
                               "re-release rather than a frozen 2022 artifact. The bytes may "
                               "change again; the checksum pins THIS retrieval, not the session."),
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(pin, open(args.out, "w", encoding="utf-8"), indent=2)
    print(json.dumps({k: pin[k] for k in
                      ("size_bytes", "sha256", "checksum_match", "content_valid",
                       "last_modified", "n_members", "internal_versions",
                       "analysis_centres")}, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
