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

def _identities():
    path = os.path.join(REPO, "phase0", "evidence", "identities.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["artifacts"]


def _composed(artifacts):
    """Every artifact asserting ftro_composed, at EITHER identity level.

    The first version of this helper filtered on snapshot_kind alone. Profile §5.1 is
    unqualified, so the real denominator includes concept_kind too -- the earlier test
    passed while 2 of 7 records were non-conforming, because it encoded the same wrong
    denominator the finding had used (FTRO-DEF-029 v2.0.0).
    """
    return [a for a in artifacts
            if "ftro_composed" in (a.get("snapshot_kind"), a.get("concept_kind"))]


class TestPinnerEndToEnd(unittest.TestCase):
    """Run the pinners as subprocesses over local file:// URLs.

    FTRO-DEF-031 v2.0.0: the earlier suite exercised validate_content in-process but never
    ran a pinner, and its three fail-closed tests skipped on a clean clone because they
    needed a gitignored provider artifact. These need nothing but committed fixtures.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ftro-e2e-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _pin_vgosdb(self, fixture_name, expect=None):
        url = "file://" + os.path.join(FIXTURES, fixture_name)
        out = os.path.join(self.tmp, "pin.json")
        args = [sys.executable, "src/ftro/pin_vgosdb.py", "--url", url, "--session", "R11040",
                "--cache", os.path.join(self.tmp, "cache"), "--out", out]
        if expect:
            args += ["--expect-sha256", expect]
        r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=120)
        rec = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else None
        return r, rec

    def test_pins_a_valid_vgosdb_end_to_end(self):
        r, rec = self._pin_vgosdb("vgosdb_min.tgz")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(rec["content_valid"])
        self.assertIn("snapshot_id", rec)
        self.assertTrue(rec["bytes_written_to_cache"])
        self.assertEqual(rec["internal_versions"], ["001"])

    def test_rejects_a_tarball_that_is_not_a_vgosdb(self):
        r, rec = self._pin_vgosdb("not_vgosdb.tgz")
        self.assertEqual(r.returncode, 1, "a tarball with no wrappers must fail closed")
        self.assertFalse(rec["content_valid"])
        self.assertNotIn("snapshot_id", rec, "a rejected retrieval must mint no identity")
        self.assertFalse(rec["bytes_written_to_cache"])

    def test_rejects_html_served_as_an_archive(self):
        r, rec = self._pin_vgosdb("login_page.html")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("snapshot_id", rec)

    def test_fails_closed_on_digest_mismatch_end_to_end(self):
        r, rec = self._pin_vgosdb("vgosdb_min.tgz", expect="0" * 64)
        self.assertEqual(r.returncode, 1, "digest mismatch must be fatal")
        self.assertIs(rec["checksum_match"], False)
        self.assertNotIn("snapshot_id", rec)
        self.assertFalse(rec["bytes_written_to_cache"],
                         "unverified bytes must not occupy the product filename")

    def test_succeeds_on_matching_digest_end_to_end(self):
        import hashlib
        digest = hashlib.sha256(fixture("vgosdb_min.tgz")).hexdigest()
        r, rec = self._pin_vgosdb("vgosdb_min.tgz", expect=digest)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIs(rec["checksum_match"], True)
        self.assertIn("snapshot_id", rec)

    def test_composed_identity_emitted_by_the_generator_is_conforming(self):
        """Profile §5.1 must hold for freshly generated output, not only for the manifest."""
        _, rec = self._pin_vgosdb("vgosdb_min.tgz")
        self.assertEqual(rec["snapshot_kind"], "ftro_composed")
        self.assertTrue(rec["composition_precondition_checked"])
        self.assertGreater(len(rec["composition_justification"].strip()), 20)


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
        """Profile §9.2: only content_validated may support evidence_state = resolvable.

        Fails CLOSED on a missing value. The earlier version carried `rv is not None`,
        which exempted six of eleven records that simply omitted the field -- the
        unsupported-null failure this project exists to catch (FTRO-DEF-034).
        """
        offenders = []
        for a in _identities():
            rv, es = a.get("retrieval_validation"), a.get("evidence_state")
            if es != "resolvable":
                continue
            if rv not in ("content_validated", "not_applicable"):
                offenders.append((a.get("concept_id"), rv))
        self.assertEqual(offenders, [],
                         f"evidence_state=resolvable without content_validated: {offenders}")

    def test_not_applicable_only_for_records_without_a_snapshot(self):
        """`not_applicable` is for concept-level records, not an escape hatch for retrievals."""
        for a in _identities():
            if a.get("retrieval_validation") == "not_applicable":
                with self.subTest(concept=a.get("concept_id")):
                    self.assertFalse(a.get("snapshot_id"),
                                     "a record with a snapshot_id IS a retrieval")

    def test_every_record_declares_retrieval_validation(self):
        """No record may leave the field absent: absence is not evidence of validation."""
        for a in _identities():
            with self.subTest(concept=a.get("concept_id")):
                self.assertIn("retrieval_validation", a)


class TestGeneratorManifestReconciliation(unittest.TestCase):
    """The generators and the curated manifest must agree.

    FTRO-DEF-035: tests validated a hand-corrected manifest while the generators that
    feed it drifted. pin_ppta.py emitted four snapshot identities that differed from the
    canonical ones and nothing noticed, because nothing compared them.
    """

    REPORTS = [
        ("phase0/reports/ppta-artifact-pins.json", "pins"),
        ("phase0/reports/evidence-repo-pins.json", "pins"),
    ]

    def _canonical(self):
        return {a["concept_id"]: a for a in _identities() if a.get("concept_id")}

    def test_generated_identities_match_the_manifest(self):
        canon = self._canonical()
        checked = 0
        for path, key in self.REPORTS:
            full = os.path.join(REPO, path)
            if not os.path.exists(full):
                self.fail(f"{path} missing; regenerate it before running the suite")
            with open(full, encoding="utf-8") as fh:
                report = json.load(fh)
            for pin in report[key]:
                cid = pin.get("concept_id")
                if cid not in canon:
                    continue
                with self.subTest(report=path, concept=cid):
                    rec = canon[cid]
                    for field in ("snapshot_id", "sha256"):
                        if pin.get(field) and rec.get(field):
                            self.assertEqual(pin[field], rec[field],
                                             f"{field} disagrees between generator and manifest")
                    checked += 1
        self.assertGreater(checked, 0, "no generated identity was reconciled")

    def test_vgosdb_pin_matches_the_manifest(self):
        full = os.path.join(REPO, "phase0", "reports", "vlbi-vgosdb-pin.json")
        if not os.path.exists(full):
            self.fail("vlbi-vgosdb-pin.json missing; regenerate it")
        with open(full, encoding="utf-8") as fh:
            pin = json.load(fh)
        rec = self._canonical()[pin["concept_id"]]
        self.assertEqual(pin["snapshot_id"], rec["snapshot_id"])
        self.assertEqual(pin["sha256"], rec["sha256"])

    def test_expected_digests_cover_every_pinned_artifact(self):
        """The committed expectation file must actually enforce the committed pins."""
        exp_path = os.path.join(REPO, "phase0", "evidence", "expected-digests.json")
        self.assertTrue(os.path.exists(exp_path),
                        "expected-digests.json must be committed, not left in gitignored data/work")
        with open(exp_path, encoding="utf-8") as fh:
            exp = json.load(fh)
        with open(os.path.join(REPO, "phase0", "reports", "ppta-artifact-pins.json"),
                  encoding="utf-8") as fh:
            for pin in json.load(fh)["pins"]:
                with self.subTest(name=pin["name"]):
                    self.assertEqual(exp["ppta"].get(pin["name"]), pin["sha256"])

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
