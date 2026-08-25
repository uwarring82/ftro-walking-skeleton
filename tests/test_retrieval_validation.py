#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Deterministic regression tests for FTRO retrieval validation.
#
# These exist because FTRO-DEF-018 (a soft authentication wall returning HTTP 200) and
# FTRO-DEF-027 (a claim not reproducible from committed code) are both failures this
# repository logged against itself. A validator with no committed test is the same
# category of defect as a number with no committed generator.
#
# Standard library only, matching the repo's no-dependency policy.
#     python3 -m unittest discover -s tests -v

import io
import json
import os
import subprocess
import sys
import tarfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(REPO, "tests", "fixtures")
sys.path.insert(0, os.path.join(REPO, "src", "ftro"))

from pin_igs import validate_content  # noqa: E402


def fixture(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        return fh.read()


class TestContentShapeValidation(unittest.TestCase):
    """FTRO-DEF-018: status and checksum are necessary but not sufficient."""

    def test_login_page_is_rejected(self):
        body = fixture("login_page.html")
        ok, level, reason = validate_content("master2022.txt", body, "text/html; charset=utf-8")
        self.assertFalse(ok, "an authentication interstitial must not validate as data")
        self.assertEqual(level, "content_validated")
        self.assertIn("HTML", reason)

    def test_login_page_names_the_auth_markers(self):
        ok, _, reason = validate_content("x.txt", fixture("login_page.html"), None)
        self.assertFalse(ok)
        self.assertIn("Earthdata Login", reason)

    def test_login_page_would_pass_status_and_checksum(self):
        """The point of the finding: the bytes are stable and checksum cleanly."""
        import hashlib
        body = fixture("login_page.html")
        self.assertEqual(len(hashlib.sha256(body).hexdigest()), 64)
        self.assertGreater(len(body), 0)
        self.assertFalse(validate_content("master2022.txt", body, "text/html")[0])

    def test_genuine_compress_archive_accepted(self):
        ok, _, reason = validate_content("igs21980.sp3.Z", fixture("genuine.sp3.Z"),
                                         "application/octet-stream")
        self.assertTrue(ok, reason)

    def test_wrong_magic_for_dot_z_rejected(self):
        ok, _, reason = validate_content("igs21980.sp3.Z", fixture("wrong_magic.sp3.Z"),
                                         "application/octet-stream")
        self.assertFalse(ok)
        self.assertIn("magic", reason)

    def test_empty_body_rejected(self):
        ok, _, reason = validate_content("igs21980.sp3.Z", b"", "application/octet-stream")
        self.assertFalse(ok)
        self.assertIn("empty", reason)

    def test_html_content_type_rejected_even_without_markers(self):
        ok, _, reason = validate_content("data.txt", b"plain text body", "text/html")
        self.assertFalse(ok)
        self.assertIn("Content-Type", reason)


class TestVgosdbShapeValidation(unittest.TestCase):
    """A vgosDB must be a gzip/tar carrying versioned wrapper members."""

    @staticmethod
    def _checks(body):
        checks = {"gzip_magic": body[:2] == b"\x1f\x8b"}
        try:
            with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as tf:
                members = tf.getnames()
            checks["tar_readable"] = True
        except Exception:                                        # noqa: BLE001
            checks["tar_readable"] = False
            members = []
        wrappers = [m for m in members if m.endswith(".wrp")]
        checks["has_wrappers"] = bool(wrappers)
        return checks, members, wrappers

    def test_minimal_vgosdb_accepted(self):
        checks, members, wrappers = self._checks(fixture("vgosdb_min.tgz"))
        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(any("_V001_" in w for w in wrappers))

    def test_tarball_without_wrappers_rejected(self):
        checks, _, wrappers = self._checks(fixture("not_vgosdb.tgz"))
        self.assertTrue(checks["gzip_magic"])
        self.assertTrue(checks["tar_readable"])
        self.assertFalse(checks["has_wrappers"], "a tarball with no .wrp is not a vgosDB")
        self.assertEqual(wrappers, [])

    def test_html_is_not_a_vgosdb(self):
        checks, _, _ = self._checks(fixture("login_page.html"))
        self.assertFalse(checks["gzip_magic"])
        self.assertFalse(checks["tar_readable"])


class TestFailClosed(unittest.TestCase):
    """A checksum mismatch must be fatal, not a recorded field."""

    def _run(self, args):
        return subprocess.run([sys.executable] + args, cwd=REPO,
                              capture_output=True, text=True, timeout=300)

    def test_verify_gps2utc_exits_nonzero_on_digest_mismatch(self):
        clk = os.path.join(REPO, "data", "raw", "evidence", "gps2utc.clk")
        if not os.path.exists(clk):
            self.skipTest("pinned artifact not present; run the retrieval steps in README first")
        out = "/tmp/ftro-test-vg.json"
        r = self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                       "--mjd-start", "59630", "--mjd-end", "59640",
                       "--expect-sha256", "0" * 64, "--out", out])
        self.assertEqual(r.returncode, 3, f"expected exit 3, got {r.returncode}: {r.stderr}")
        with open(out, encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertIs(rec["checksum_match"], False)
        self.assertEqual(rec["result"], "indeterminate")

    def test_verify_gps2utc_exits_zero_on_correct_digest(self):
        clk = os.path.join(REPO, "data", "raw", "evidence", "gps2utc.clk")
        if not os.path.exists(clk):
            self.skipTest("pinned artifact not present")
        r = self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                       "--mjd-start", "59630", "--mjd-end", "59640",
                       "--expect-sha256",
                       "7a1dcb60e4587e7bb9f0ab837ac0b39b54710752fa53062b7e305e5f95669a0a",
                       "--out", "/tmp/ftro-test-vg-ok.json"])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unchecked_digest_is_null_not_true(self):
        """None must mean 'not checked'. A missing check must never read as a pass."""
        clk = os.path.join(REPO, "data", "raw", "evidence", "gps2utc.clk")
        if not os.path.exists(clk):
            self.skipTest("pinned artifact not present")
        out = "/tmp/ftro-test-vg-none.json"
        self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                   "--mjd-start", "59630", "--mjd-end", "59640", "--out", out])
        with open(out, encoding="utf-8") as fh:
            self.assertIsNone(json.load(fh)["checksum_match"])


class TestComposedIdentityConformance(unittest.TestCase):
    """Profile §5.1: an ftro_composed identity must record what was checked."""

    def test_every_composed_identity_records_its_precondition(self):
        path = os.path.join(REPO, "phase0", "evidence", "identities.json")
        with open(path, encoding="utf-8") as fh:
            artifacts = json.load(fh)["artifacts"]
        composed = [a for a in artifacts if a.get("snapshot_kind") == "ftro_composed"]
        self.assertGreater(len(composed), 0, "expected at least one composed identity")
        for a in composed:
            with self.subTest(concept=a.get("concept_id")):
                self.assertIn("composition_precondition_checked", a)
                self.assertIn("composition_justification", a)
                self.assertTrue(a["composition_precondition_checked"])

    def test_no_truncated_digest_inside_an_identity(self):
        import re
        path = os.path.join(REPO, "phase0", "evidence", "identities.json")
        with open(path, encoding="utf-8") as fh:
            blob = fh.read()
        for m in re.finditer(r"@sha256:([0-9a-f]+)", blob):
            with self.subTest(digest=m.group(1)[:12]):
                self.assertEqual(len(m.group(1)), 64,
                                 "a truncated digest inside an identity is a different identity")


if __name__ == "__main__":
    unittest.main(verbosity=2)
