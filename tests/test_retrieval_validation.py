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
import shutil
import subprocess
import sys
import tarfile
import tempfile
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

    def test_genuine_lzw_sp3_accepted(self):
        """A real LZW stream carrying real SP3 content must pass."""
        ok, _, reason = validate_content("igs21980.sp3.Z", fixture("synthetic_sp3.Z"),
                                         "application/octet-stream")
        self.assertTrue(ok, reason)

    def test_right_magic_but_undecompressable_rejected(self):
        """Magic bytes are necessary, not sufficient (the old fixture passed on magic alone)."""
        ok, _, reason = validate_content("igs21980.sp3.Z", fixture("bad_lzw.sp3.Z"),
                                         "application/octet-stream")
        self.assertFalse(ok, "a .Z that will not decompress must not validate")
        self.assertIn("decompress", reason)

    def test_valid_lzw_but_wrong_inner_format_rejected(self):
        """Decompressing is necessary, not sufficient: the content must be the named product."""
        ok, _, reason = validate_content("igs21980.sp3.Z",
                                         fixture("valid_lzw_wrong_inner.sp3.Z"),
                                         "application/octet-stream")
        self.assertFalse(ok, "valid LZW carrying non-SP3 content must not validate as SP3")
        self.assertIn("SP3", reason)

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


class TestUnixCompressCodec(unittest.TestCase):
    """The .Z decoder is load-bearing for content validation, so it is tested directly."""

    def test_round_trip(self):
        import unixz
        for payload in (b"", b"a", b"ab" * 5000, bytes(range(256)) * 40,
                        b"#cP2022  2 20 ORBIT IGb14\n" * 200):
            with self.subTest(n=len(payload)):
                self.assertEqual(unixz.decompress(unixz.compress(payload)), payload)

    def test_rejects_bad_magic(self):
        import unixz
        with self.assertRaises(Exception):
            unixz.decompress(b"\x1f\x8b\x90rest")

    def test_matches_system_gzip_on_our_fixture(self):
        """Cross-check against an independent implementation, not just self-consistency."""
        import shutil
        if not shutil.which("gzip"):
            self.skipTest("system gzip unavailable")
        import unixz
        blob = fixture("synthetic_sp3.Z")
        sysout = subprocess.run(["gzip", "-dc"], input=blob,
                                capture_output=True, timeout=60)
        self.assertEqual(sysout.returncode, 0, sysout.stderr)
        self.assertEqual(unixz.decompress(blob), sysout.stdout)

    def test_max_output_guard(self):
        import unixz
        with self.assertRaises(Exception):
            unixz.decompress(unixz.compress(b"x" * 100000), max_output=10)


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
    """A checksum mismatch must be fatal, not a recorded field.

    These use a LOCAL fixture, not a gitignored provider artifact, so they run on a clean
    clone. The earlier version skipped all three on a fresh checkout, which meant the
    fail-closed behaviour was never actually exercised by the suite.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ftro-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def out(self, name):
        return os.path.join(self.tmp, name)

    def _run(self, args):
        return subprocess.run([sys.executable] + args, cwd=REPO,
                              capture_output=True, text=True, timeout=300)

    def test_verify_gps2utc_fail_closed_on_local_fixture(self):
        """Fail-closed is tested without any gitignored artifact."""
        clk = os.path.join(self.tmp, "tiny.clk")
        with open(clk, "w", encoding="utf-8") as fh:
            fh.write("# UTC(GPS) UTC(USNO)\n# These entries are based on C0' values.\n"
                     "59630.00000 0.000000002800\n59631.00000 0.000000003300\n")
        out = self.out("bad.json")
        r = self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                       "--mjd-start", "59630", "--mjd-end", "59631",
                       "--expect-sha256", "0" * 64, "--out", out])
        self.assertEqual(r.returncode, 3, f"expected exit 3, got {r.returncode}: {r.stderr}")
        with open(out, encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertIs(rec["checksum_match"], False)

    def test_verify_gps2utc_succeeds_on_correct_local_digest(self):
        import hashlib
        clk = os.path.join(self.tmp, "tiny.clk")
        body = ("# UTC(GPS) UTC(USNO)\n# These entries are based on C0' values.\n"
                "59630.00000 0.000000002800\n59631.00000 0.000000003300\n")
        with open(clk, "w", encoding="utf-8") as fh:
            fh.write(body)
        digest = hashlib.sha256(body.encode()).hexdigest()
        r = self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                       "--mjd-start", "59630", "--mjd-end", "59631",
                       "--expect-sha256", digest, "--out", self.out("ok.json")])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_verify_gps2utc_exits_nonzero_on_digest_mismatch(self):
        clk = os.path.join(REPO, "data", "raw", "evidence", "gps2utc.clk")
        if not os.path.exists(clk):
            self.skipTest("pinned artifact not present; run the retrieval steps in README first")
        out = self.out("vg.json")
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
                       "--out", self.out("vg-ok.json")])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_unchecked_digest_is_null_not_true(self):
        """None must mean 'not checked'. A missing check must never read as a pass."""
        clk = os.path.join(REPO, "data", "raw", "evidence", "gps2utc.clk")
        if not os.path.exists(clk):
            self.skipTest("pinned artifact not present")
        out = self.out("vg-none.json")
        r = self._run(["src/ftro/verify_gps2utc.py", "--file", clk,
                       "--mjd-start", "59630", "--mjd-end", "59640", "--out", out])
        self.assertEqual(r.returncode, 0, r.stderr)   # never read a stale file on failure
        with open(out, encoding="utf-8") as fh:
            self.assertIsNone(json.load(fh)["checksum_match"])


def _identities():
    path = os.path.join(REPO, "phase0", "evidence", "identities.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["artifacts"]


def _composed(artifacts):
    """Every artifact asserting ftro_composed, at EITHER identity level.

    The first version of this helper filtered on snapshot_kind alone. Profile §5.1 is
    unqualified, so the real denominator includes concept_kind too -- the earlier test
    passed while 2 of 7 records were non-conforming, because it encoded the same wrong
    denominator the finding had used (FTRO-DEF-031).
    """
    return [a for a in artifacts
            if "ftro_composed" in (a.get("snapshot_kind"), a.get("concept_kind"))]


class TestComposedIdentityConformance(unittest.TestCase):
    """Profile §5.1: an ftro_composed identity must record what was checked."""

    def test_every_composed_identity_records_its_precondition(self):
        composed = _composed(_identities())
        self.assertGreaterEqual(len(composed), 7, "denominator must span both identity levels")
        for a in composed:
            with self.subTest(concept=a.get("concept_id")):
                self.assertIn("composition_precondition_checked", a)
                self.assertIn("composition_justification", a)

    def test_precondition_records_are_substantive(self):
        """A null or empty justification must not satisfy the clause."""
        for a in _composed(_identities()):
            with self.subTest(concept=a.get("concept_id")):
                checked = a.get("composition_precondition_checked")
                why = a.get("composition_justification")
                self.assertIsInstance(checked, list)
                self.assertTrue(checked, "must name at least one field checked and found absent")
                self.assertTrue(all(isinstance(x, str) and x.strip() for x in checked))
                self.assertIsInstance(why, str)
                self.assertGreater(len(why.strip()), 20, "justification must say something")

    def test_section_10_identity_ingredients_present(self):
        """Card §10: a composed identity is concept id + retrieval time + checksum + procedure."""
        for a in _composed(_identities()):
            if not a.get("snapshot_id"):
                continue   # concept-level composition carries no snapshot ingredients
            with self.subTest(concept=a.get("concept_id")):
                self.assertTrue(a.get("concept_id"))
                self.assertTrue(a.get("retrieved_utc"), "§10 requires a retrieval time")
                self.assertTrue(a.get("sha256") or a.get("md5"), "§10 requires a byte checksum")
                self.assertTrue(a.get("retrieval_procedure"),
                                "§10 requires the recorded retrieval procedure")

    def test_resolvable_requires_content_validated(self):
        """Profile §9.2: only content_validated may support evidence_state = resolvable."""
        offenders = []
        for a in _identities():
            rv, es = a.get("retrieval_validation"), a.get("evidence_state")
            if es == "resolvable" and rv is not None and rv != "content_validated":
                offenders.append((a.get("concept_id"), rv))
        self.assertEqual(offenders, [],
                         f"evidence_state=resolvable with weaker validation: {offenders}")

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
