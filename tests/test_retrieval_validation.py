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
import re
import datetime
import hashlib
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

    def _registry(self, fixture_name, digest="auto"):
        """Write a fixture-scoped digest registry, so preflight has something to enforce."""
        if digest == "auto":
            digest = hashlib.sha256(fixture(fixture_name)).hexdigest()
        path = os.path.join(self.tmp, "registry.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"vgosdb": {fixture_name: digest} if digest else {}}, fh)
        return path

    def _pin_vgosdb(self, fixture_name, expect=None, registry="auto", allow_unpinned=False,
                    out_name="pin.json"):
        url = "file://" + os.path.join(FIXTURES, fixture_name)
        out = os.path.join(self.tmp, out_name)
        args = [sys.executable, "src/ftro/pin_vgosdb.py", "--url", url, "--session", "R11040",
                "--cache", os.path.join(self.tmp, "cache"), "--out", out]
        if registry is not None:
            args += ["--expect", self._registry(fixture_name,
                                                "auto" if registry == "auto" else registry)]
        if expect:
            args += ["--expect-sha256", expect]
        if allow_unpinned:
            args += ["--allow-unpinned"]
        r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=120)
        # On failure the report is NOT promoted to `out`; the evidence is preserved
        # beside it with a .rejected suffix.
        rec = None
        for candidate in (out, out + ".rejected"):
            if os.path.exists(candidate):
                with open(candidate, encoding="utf-8") as fh:
                    rec = json.load(fh)
                break
        return r, rec

    def test_transport_failure_is_preserved_as_rejected(self):
        """A failed retrieval must leave evidence, not a traceback (FTRO-DEF-041)."""
        out = os.path.join(self.tmp, "ghost.json")
        reg = os.path.join(self.tmp, "ghost-registry.json")
        with open(reg, "w", encoding="utf-8") as fh:
            json.dump({"vgosdb": {"ghost.tgz": "0" * 64}}, fh)
        r = subprocess.run(
            [sys.executable, "src/ftro/pin_vgosdb.py",
             "--url", "file:///nonexistent/path/ghost.tgz", "--session", "R11040",
             "--cache", os.path.join(self.tmp, "cache"), "--out", out, "--expect", reg],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr, "a transport failure surfaced as a traceback")
        self.assertFalse(os.path.exists(out), "a failed retrieval must not be promoted")
        self.assertTrue(os.path.exists(out + ".rejected"),
                        "a failed retrieval must be preserved as .rejected")
        with open(out + ".rejected", encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertIn("transport failure", rec["rejected_reason"])
        self.assertEqual(rec["retrieval_validation"], "content_rejected")

    def test_preflight_refuses_an_uncovered_target_and_fetches_nothing(self):
        """Registry coverage is checked BEFORE retrieval, not after caching."""
        r, rec = self._pin_vgosdb("vgosdb_min.tgz", registry=None)
        self.assertEqual(r.returncode, 1)
        self.assertIn("preflight", r.stderr.lower() + r.stdout.lower())
        self.assertIsNone(rec, "a preflight failure must not write a report")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "cache", "vgosdb_min.tgz")),
                         "a preflight failure must not cache bytes")

    def test_failed_run_does_not_overwrite_an_existing_report(self):
        """Atomic promotion: the official path survives a failed run."""
        ok, _ = self._pin_vgosdb("vgosdb_min.tgz", out_name="official.json")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        official = os.path.join(self.tmp, "official.json")
        with open(official, "rb") as fh:
            before = hashlib.sha256(fh.read()).hexdigest()
        bad, _ = self._pin_vgosdb("not_vgosdb.tgz", out_name="official.json", registry=None,
                                  allow_unpinned=True)
        self.assertEqual(bad.returncode, 1)
        with open(official, "rb") as fh:
            after = hashlib.sha256(fh.read()).hexdigest()
        self.assertEqual(before, after, "a failed run overwrote the official report")
        self.assertTrue(os.path.exists(official + ".rejected"),
                        "the rejected report should be preserved beside it")

    def test_pins_a_valid_vgosdb_end_to_end(self):
        r, rec = self._pin_vgosdb("vgosdb_min.tgz")
        self.assertEqual(rec["expected_sha256"], rec["sha256"])
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
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "pin.json")),
                         "a rejected report must not be promoted to the official path")

    def test_rejects_html_served_as_an_archive(self):
        r, rec = self._pin_vgosdb("login_page.html")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("snapshot_id", rec)

    def test_fails_closed_on_digest_mismatch_end_to_end(self):
        r, rec = self._pin_vgosdb("vgosdb_min.tgz", expect="0" * 64, registry="0" * 64)
        self.assertEqual(r.returncode, 1, "digest mismatch must be fatal")
        self.assertIs(rec["checksum_match"], False)
        self.assertNotIn("snapshot_id", rec)
        self.assertFalse(rec["bytes_written_to_cache"],
                         "unverified bytes must not occupy the product filename")

    def test_succeeds_on_matching_digest_end_to_end(self):
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


# Which generator is authoritative for which canonical concept. Declared explicitly so a
# concept that no generator produces cannot silently escape reconciliation, and a report
# entry naming an unknown concept cannot be silently skipped (FTRO-DEF-035 v2.0.0).
GENERATOR_REPORTS = {
    "phase0/reports/ppta-artifact-pins.json": [
        "ftro:concept:ppta/dr3/par/J0437-4715",
        "ftro:concept:ppta/dr3/toas/J0437-4715",
        "ftro:concept:ppta/dr3/clock/pks2gps",
        "ftro:concept:ppta/dr3/clock/tai2tt_bipm2021",
    ],
    "phase0/reports/evidence-repo-pins.json": [
        "https://github.com/INRIM/optical-link-data-format",
        "https://github.com/ipta/pulsar-clock-corrections",
        "https://github.com/INRIM/tintervals",
    ],
    "phase0/reports/vlbi-vgosdb-pin.json": [
        "ftro:concept:ivs/session/R11040",
    ],
}
RECONCILED_FIELDS = ("snapshot_id", "sha256", "retrieved_utc", "retrieval_procedure")


def _report_pins(path):
    """Return {concept_id: pin} for a report, whether it holds a list or a single pin."""
    with open(os.path.join(REPO, path), encoding="utf-8") as fh:
        doc = json.load(fh)
    pins = doc["pins"] if isinstance(doc.get("pins"), list) else [doc]
    return {p["concept_id"]: p for p in pins if p.get("concept_id")}


class TestGeneratorManifestReconciliation(unittest.TestCase):
    """Generated and curated views must agree, and disagreement must be detectable.

    FTRO-DEF-035 v2.0.0: the first version skipped concepts absent from the manifest and
    compared a field only when BOTH copies carried it, so deleting a snapshot_id, adding a
    rogue concept, or dropping the generated composition fields all left the suite green.
    Every edge below rejects MISSING, UNKNOWN and MISMATCHED records.
    """

    def setUp(self):
        self.canon = {a["concept_id"]: a for a in _identities() if a.get("concept_id")}

    def test_every_declared_report_exists(self):
        for path in GENERATOR_REPORTS:
            self.assertTrue(os.path.exists(os.path.join(REPO, path)),
                            f"{path} missing; regenerate before running the suite")

    def test_no_report_entry_is_unknown_to_the_manifest(self):
        """An UNKNOWN concept must fail, not be skipped."""
        for path, expected in GENERATOR_REPORTS.items():
            pins = _report_pins(path)
            for cid in pins:
                with self.subTest(report=path, concept=cid):
                    self.assertIn(cid, self.canon,
                                  "report names a concept absent from identities.json")
                    self.assertIn(cid, expected,
                                  "report names a concept this generator does not declare")

    def test_no_declared_concept_is_missing_from_its_report(self):
        """A MISSING record must fail, not pass vacuously."""
        for path, expected in GENERATOR_REPORTS.items():
            pins = _report_pins(path)
            for cid in expected:
                with self.subTest(report=path, concept=cid):
                    self.assertIn(cid, pins, "declared concept absent from generator output")
                    self.assertIn(cid, self.canon, "declared concept absent from identities.json")

    def test_reconciled_fields_present_on_both_sides_and_equal(self):
        """A field missing from EITHER side is a failure, not an exemption."""
        for path, expected in GENERATOR_REPORTS.items():
            pins = _report_pins(path)
            for cid in expected:
                pin, rec = pins.get(cid, {}), self.canon.get(cid, {})
                for field in RECONCILED_FIELDS:
                    with self.subTest(report=path, concept=cid, field=field):
                        self.assertIn(field, pin, "generator output lacks the field")
                        self.assertIn(field, rec, "manifest record lacks the field")
                        if field == "retrieved_utc":
                            # Not compared for equality -- it differs per run by
                            # construction -- but it must be a real ISO-8601 UTC instant
                            # on BOTH sides. Skipping it entirely let 'not-a-timestamp'
                            # through (FTRO-DEF-035 v3.0.0).
                            for side, val in (("generator", pin[field]), ("manifest", rec[field])):
                                self.assertIsInstance(val, str, side)
                                try:
                                    datetime.datetime.fromisoformat(val)
                                except ValueError:
                                    self.fail(f"{side} retrieved_utc is not ISO-8601: {val!r}")
                            continue
                        self.assertEqual(pin[field], rec[field],
                                         "generator and manifest disagree")

    def test_generated_composition_fields_are_conforming(self):
        """Profile §5.1 must hold for generated output, not only for the stored manifest."""
        for path, expected in GENERATOR_REPORTS.items():
            pins = _report_pins(path)
            for cid in expected:
                pin, rec = pins.get(cid, {}), self.canon.get(cid, {})
                with self.subTest(report=path, concept=cid):
                    # snapshot_kind must AGREE with the manifest, so a report cannot exempt
                    # itself from §5.1 by relabelling its own kind.
                    self.assertEqual(pin.get("snapshot_kind"), rec.get("snapshot_kind"),
                                     "generator and manifest disagree on snapshot_kind")
                    if rec.get("snapshot_kind") != "ftro_composed":
                        continue
                    self.assertTrue(pin.get("composition_precondition_checked"))
                    self.assertGreater(len((pin.get("composition_justification") or "").strip()), 20)

    def test_every_manifest_record_claiming_a_generator_has_one(self):
        """No curated record may claim generated provenance without an entry in a report."""
        produced = {c for v in GENERATOR_REPORTS.values() for c in v}
        for cid, rec in self.canon.items():
            if rec.get("retrieval_validation") != "content_validated":
                continue
            if cid == "https://doi.org/10.5281/zenodo.17107692":
                continue      # validated by full parse in analyse_optical, not by a pinner
            with self.subTest(concept=cid):
                self.assertIn(cid, produced,
                              "content_validated record with no generator reconciling it")


class TestDigestRegistryChain(unittest.TestCase):
    """expected registry -> pin reports -> identities. Every edge rejects missing/extra."""

    REGISTRY = "phase0/evidence/expected-digests.json"
    SECTIONS = {
        "ppta": "phase0/reports/ppta-artifact-pins.json",
        "igs": "phase0/reports/igs-artifact-pins.json",
        "evidence_repos": "phase0/reports/evidence-repo-pins.json",
        "vgosdb": "phase0/reports/vlbi-vgosdb-pin.json",
    }

    def setUp(self):
        with open(os.path.join(REPO, self.REGISTRY), encoding="utf-8") as fh:
            self.registry = json.load(fh)

    @staticmethod
    def _keyed(path, section):
        with open(os.path.join(REPO, path), encoding="utf-8") as fh:
            doc = json.load(fh)
        pins = doc["pins"] if isinstance(doc.get("pins"), list) else [doc]
        if section == "evidence_repos":
            return {p["key"]: p["sha256"] for p in pins}
        if section == "vgosdb":
            return {os.path.basename(p["url"]): p["sha256"] for p in pins}
        return {p["name"]: p["sha256"] for p in pins}

    def test_registry_covers_every_pinned_artifact(self):
        """All 65, not the four that happened to be checked before."""
        total = 0
        for section, path in self.SECTIONS.items():
            got = self._keyed(path, section)
            exp = self.registry.get(section, {})
            with self.subTest(section=section):
                self.assertEqual(sorted(got), sorted(exp),
                                 "registry and report disagree on WHICH artifacts exist")
                for name, digest in got.items():
                    self.assertEqual(exp[name], digest, f"{section}/{name} digest disagrees")
            total += len(got)
        self.assertEqual(total, 65, f"expected 65 pinned artifacts, reconciled {total}")

    def test_reports_record_the_expectation_as_enforced(self):
        """Every pin, vgosDB included, must carry the REGISTRY digest as its expectation."""
        for section, path in self.SECTIONS.items():
            with open(os.path.join(REPO, path), encoding="utf-8") as fh:
                doc = json.load(fh)
            pins = doc["pins"] if isinstance(doc.get("pins"), list) else [doc]
            exp = self.registry.get(section, {})
            for pin in pins:
                if section == "evidence_repos":
                    key = pin["key"]
                elif section == "vgosdb":
                    key = os.path.basename(pin["url"])
                else:
                    key = pin["name"]
                with self.subTest(section=section, name=key):
                    self.assertIsNotNone(pin.get("expected_sha256"),
                                         "pinned without an expected digest: the registry "
                                         "exists but was not applied")
                    # The expectation must BE the registry value, not merely non-null.
                    self.assertEqual(pin["expected_sha256"], exp.get(key),
                                     "report expectation does not match the registry")
                    self.assertIs(pin.get("checksum_match"), True)
                    self.assertEqual(pin.get("sha256"), exp.get(key))

    def test_no_report_declares_incomplete_validation(self):
        for section, path in self.SECTIONS.items():
            with open(os.path.join(REPO, path), encoding="utf-8") as fh:
                doc = json.load(fh)
            with self.subTest(section=section):
                # None was previously permitted, so a report that simply omitted the field
                # passed. Every committed report must declare content_validated.
                # Presence, type and value -- assertFalse(doc.get(...)) equated absence
                # with zero, the same fail-open the production gate had (FTRO-DEF-038).
                self.assertIn("retrieval_validation", doc)
                self.assertEqual(doc["retrieval_validation"], "content_validated",
                                 "a committed report must declare content_validated")
                for counter in ("n_failed", "n_without_expected_digest"):
                    self.assertIn(counter, doc, f"{counter} absent from a committed report")
                    self.assertIsInstance(doc[counter], int)
                    self.assertEqual(doc[counter], 0)


class TestMutationsAreDetected(unittest.TestCase):
    """The suite must FAIL on each of these. Previously verified by hand; now committed.

    A check that has never been seen to fail has not been verified. Session 06 ran these
    mutations manually and reported the table in a lab note; a manual table is not a test
    (FTRO-DEF-035 v3.0.0). Each case copies the repo's committed views into a temporary
    tree, mutates one, and asserts the relevant test class rejects it.
    """

    TARGETS = {
        "ppta": "phase0/reports/ppta-artifact-pins.json",
        "vgosdb": "phase0/reports/vlbi-vgosdb-pin.json",
        "identities": "phase0/evidence/identities.json",
        "registry": "phase0/evidence/expected-digests.json",
    }

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ftro-mut-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for sub in ("phase0/reports", "phase0/evidence", "tests"):
            os.makedirs(os.path.join(self.tmp, sub), exist_ok=True)
        for path in list(self.TARGETS.values()) + [
                "phase0/reports/evidence-repo-pins.json",
                "phase0/reports/igs-artifact-pins.json"]:
            shutil.copy(os.path.join(REPO, path), os.path.join(self.tmp, path))
        shutil.copy(os.path.join(REPO, "tests", "test_retrieval_validation.py"),
                    os.path.join(self.tmp, "tests", "test_retrieval_validation.py"))
        os.symlink(os.path.join(REPO, "src"), os.path.join(self.tmp, "src"))
        os.symlink(os.path.join(FIXTURES), os.path.join(self.tmp, "tests", "fixtures"))

    def _mutate(self, key, fn):
        path = os.path.join(self.tmp, self.TARGETS[key])
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        fn(doc)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)

    def _run_suite(self):
        """Run the reconciliation and chain classes against the mutated tree."""
        r = subprocess.run(
            [sys.executable, "-m", "unittest",
             "tests.test_retrieval_validation.TestGeneratorManifestReconciliation",
             "tests.test_retrieval_validation.TestDigestRegistryChain",
             "tests.test_retrieval_validation.TestComposedIdentityConformance"],
            cwd=self.tmp, capture_output=True, text=True, timeout=300)
        return r

    def test_unmutated_baseline_passes(self):
        r = self._run_suite()
        self.assertEqual(r.returncode, 0,
                         "the copied tree must pass before any mutation is meaningful\n"
                         + r.stderr[-2000:])

    def _assert_detected(self, key, fn, label):
        self._mutate(key, fn)
        r = self._run_suite()
        self.assertNotEqual(r.returncode, 0, f"mutation NOT detected: {label}")

    def test_removing_a_snapshot_id_is_detected(self):
        self._assert_detected("ppta", lambda d: d["pins"][0].pop("snapshot_id"),
                              "removed a snapshot_id")

    def test_a_rogue_concept_is_detected(self):
        self._assert_detected(
            "ppta",
            lambda d: d["pins"].append({**d["pins"][0], "concept_id": "ftro:concept:bogus"}),
            "added a concept no generator declares")

    def test_dropping_generated_composition_fields_is_detected(self):
        def drop(d):
            d["pins"][0].pop("composition_precondition_checked", None)
            d["pins"][0].pop("composition_justification", None)
        self._assert_detected("ppta", drop, "dropped the generated §5.1 fields")

    def test_deleting_a_pin_is_detected(self):
        self._assert_detected("ppta", lambda d: d.__setitem__("pins", d["pins"][1:]),
                              "deleted a whole pin")

    def test_corrupting_a_digest_is_detected(self):
        self._assert_detected("ppta", lambda d: d["pins"][0].__setitem__("sha256", "0" * 64),
                              "corrupted a digest")

    def test_nulling_the_expectation_is_detected(self):
        def null_exp(d):
            d["pins"][0]["expected_sha256"] = None
            d["pins"][0]["checksum_match"] = None
        self._assert_detected("ppta", null_exp, "nulled an expectation while keeping the digest")

    def test_zeroing_the_registry_digest_is_detected(self):
        """Changing the registry while keeping checksum_match: true must fail."""
        def zero(d):
            first = sorted(d["ppta"])[0]
            d["ppta"][first] = "0" * 64
        self._assert_detected("registry", zero, "registry digest no longer matches the report")

    def test_combined_vgosdb_mutation_is_detected(self):
        """The exact combination that passed the entire suite before this class existed."""
        def combo(d):
            d["expected_sha256"] = None
            d["checksum_match"] = None
            d["retrieved_utc"] = "not-a-timestamp"
            d["snapshot_kind"] = "provider_immutable"
            d.pop("composition_precondition_checked", None)
            d.pop("composition_justification", None)
        self._assert_detected("vgosdb", combo, "combined vgosDB mutation")

    def test_relabelling_snapshot_kind_is_detected(self):
        self._assert_detected("ppta",
                              lambda d: d["pins"][0].__setitem__("snapshot_kind", "provider_pid"),
                              "relabelled snapshot_kind to escape §5.1")

    def test_invalid_retrieved_utc_is_detected(self):
        self._assert_detected("ppta",
                              lambda d: d["pins"][0].__setitem__("retrieved_utc", "not-a-time"),
                              "invalid retrieval timestamp")

    def test_declaring_a_failed_report_is_detected(self):
        self._assert_detected("ppta", lambda d: d.__setitem__("n_failed", 2),
                              "committed a report declaring failures")

    def test_dropping_top_level_validation_is_detected(self):
        self._assert_detected("ppta", lambda d: d.pop("retrieval_validation", None),
                              "omitted the top-level retrieval_validation")


class TestConsumerGate(unittest.TestCase):
    """pinning.assert_report_usable must fail closed on ABSENT state, not only on bad state."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ftro-gate-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))
        with open(os.path.join(REPO, "phase0", "reports", "igs-artifact-pins.json"),
                  encoding="utf-8") as fh:
            self.good = json.load(fh)

    def _check(self, doc):
        import pinning
        path = os.path.join(self.tmp, "r.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return pinning.assert_report_usable(path)

    def test_clean_report_is_accepted(self):
        self._check(self.good)

    def test_registry_binding_rejects_truncation_and_fabrication(self):
        """Completeness, not self-description (FTRO-DEF-054)."""
        import pinning
        reg = os.path.join(REPO, "phase0", "evidence", "expected-digests.json")
        for label, mutate in (
                ("truncated to one pin",
                 lambda d: (d.__setitem__("pins", d["pins"][:1]),
                            d.__setitem__("n_pinned", 1))),
                ("fabricated matching digests",
                 lambda d: (d["pins"][0].__setitem__("sha256", "b" * 64),
                            d["pins"][0].__setitem__("expected_sha256", "b" * 64))),
                ("duplicated pin",
                 lambda d: (d["pins"].append(json.loads(json.dumps(d["pins"][0]))),
                            d.__setitem__("n_pinned", len(d["pins"]) + 1)))):
            with self.subTest(case=label):
                doc = json.loads(json.dumps(self.good))
                mutate(doc)
                path = os.path.join(self.tmp, "reg.json")
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh)
                with self.assertRaises(SystemExit):
                    pinning.assert_report_usable(path, registry=reg, section="igs")

    def test_absent_fields_are_rejected(self):
        for field in ("retrieval_validation", "n_failed", "n_without_expected_digest"):
            with self.subTest(removed=field):
                doc = json.loads(json.dumps(self.good))
                doc.pop(field)
                with self.assertRaises(SystemExit):
                    self._check(doc)

    def test_wrong_typed_counter_is_rejected(self):
        doc = json.loads(json.dumps(self.good))
        doc["n_failed"] = "0"
        with self.assertRaises(SystemExit):
            self._check(doc)

    def test_nonzero_counters_are_rejected(self):
        for field in ("n_failed", "n_without_expected_digest"):
            with self.subTest(field=field):
                doc = json.loads(json.dumps(self.good))
                doc[field] = 1
                with self.assertRaises(SystemExit):
                    self._check(doc)

    def test_pin_level_required_state(self):
        """Profile §9.2 requires retrieval_validation on every record, pins included."""
        doc = json.loads(json.dumps(self.good))
        for pin in doc["pins"]:
            pin.pop("retrieval_validation", None)
        with self.assertRaises(SystemExit):
            self._check(doc)

    def test_n_pinned_must_be_present_and_a_true_int(self):
        for label, mutate in (
                ("absent", lambda d: d.pop("n_pinned")),
                ("float", lambda d: d.__setitem__("n_pinned", float(len(d["pins"])))),
                ("bool", lambda d: (d.__setitem__("pins", d["pins"][:1]),
                                    d.__setitem__("n_pinned", True))),
                ("wrong count", lambda d: d.__setitem__("n_pinned", len(d["pins"]) - 1))):
            with self.subTest(case=label):
                doc = json.loads(json.dumps(self.good))
                mutate(doc)
                with self.assertRaises(SystemExit):
                    self._check(doc)

    def test_container_shape_is_required(self):
        """Wrong-typed containers previously slipped past the coherence checks entirely."""
        for label, mutate in (
                ("failures is an object", lambda d: d.__setitem__("failures", {})),
                ("uncovered is a string",
                 lambda d: d.__setitem__("uncovered_by_registry", "ghost")),
                ("pins is an object", lambda d: d.__setitem__("pins", {})),
                ("failures absent", lambda d: d.pop("failures", None)),
                ("uncovered absent", lambda d: d.pop("uncovered_by_registry", None)),
                ("a pin is not an object",
                 lambda d: d["pins"].__setitem__(0, "not-an-object"))):
            with self.subTest(case=label):
                doc = json.loads(json.dumps(self.good))
                mutate(doc)
                with self.assertRaises(SystemExit):
                    self._check(doc)

    def test_counters_must_agree_with_their_lists(self):
        for lst, counter in (("failures", "n_failed"),
                             ("uncovered_by_registry", "n_without_expected_digest")):
            with self.subTest(list=lst):
                doc = json.loads(json.dumps(self.good))
                doc[lst] = [{"name": "x", "error": "y"}]
                with self.assertRaises(SystemExit):
                    self._check(doc)

    def test_pin_without_expectation_is_rejected(self):
        doc = json.loads(json.dumps(self.good))
        doc["pins"][0]["expected_sha256"] = None
        with self.assertRaises(SystemExit):
            self._check(doc)

    def test_empty_pins_is_rejected(self):
        doc = json.loads(json.dumps(self.good))
        doc["pins"] = []
        with self.assertRaises(SystemExit):
            self._check(doc)

    def test_production_consumer_rejects_a_stripped_report(self):
        """Mutation-test the real consumer, in a COPIED tree.

        This previously wrote into the tracked checkout, against this repository's own
        rule that a test must never modify the tree it inspects (D-067).
        """
        work = os.path.join(self.tmp, "repo")
        shutil.copytree(REPO, work, symlinks=True,
                        ignore=shutil.ignore_patterns("data", ".git", "__pycache__"))
        target = os.path.join(work, "phase0", "reports", "igs-artifact-pins.json")
        if True:
            doc = json.loads(json.dumps(self.good))
            doc.pop("n_failed")
            with open(target, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2)
            r = subprocess.run([sys.executable, "src/ftro/four_domain_intersection.py"],
                               cwd=work, capture_output=True, text=True, timeout=600)
            self.assertNotEqual(r.returncode, 0,
                                "the production consumer accepted a report missing n_failed")
            # Assert the SPECIFIC gate diagnostic. A bare non-zero exit is
            # self-confirming: on a clean archive the consumer already exits 1 because
            # the raw optical data are absent, so bypassing the gate would still pass
            # (FTRO-DEF-047).
            combined = r.stdout + r.stderr
            self.assertIn("is not a clean success", combined,
                          f"exited non-zero for some other reason:\n{combined[-800:]}")
            self.assertIn("n_failed absent", combined)
            # The tracked report must be untouched by this test.
            with open(os.path.join(REPO, "phase0", "reports",
                                   "igs-artifact-pins.json"), encoding="utf-8") as fh:
                self.assertIn("n_failed", json.load(fh))


MINI_ARCHIVE = os.path.join(FIXTURES, "mini-archive")


def independent_runs(path, tol_s, tick_s=0.0864):
    """Segment a .dat WITHOUT calling analyse_optical.

    Written from the specification, not by delegating: the previous oracle called
    contiguous_runs() down both of its "independent" routes, so it could only detect a
    broken adapter, never a broken segmenter. Halving every run's span preserved all four
    run counts and changed optical support by 40 percent while all 86 tests passed
    (FTRO-DEF-048).
    """
    ticks, flags = [], []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            ip, _, fr = parts[0].partition(".")
            ticks.append(int(ip) * 1_000_000 + int(fr.ljust(6, "0")[:6]))
            flags.append(int(parts[2]))
    tol = int(tol_s / tick_s + 1e-9)
    runs, cur = [], []
    for t, f in zip(ticks, flags):
        if f not in (1, 2):
            if cur:
                runs.append(cur)
                cur = []
            continue
        if cur and t - cur[-1] > tol:
            runs.append(cur)
            cur = []
        cur.append(t)
    if cur:
        runs.append(cur)
    return [(r[0], r[-1], len(r)) for r in runs]


class TestSegmentationOracle(unittest.TestCase):
    """Check segmentation against an INDEPENDENT implementation and a tuple manifest.

    Three mutually reinforcing checks:
      1. the production segmenter agrees with independent_runs() above, tuple for tuple;
      2. both agree with a manifest derived when the fixture was built;
      3. the two production routes agree with each other.
    Counts alone are insufficient -- they validate topology, not extent.
    """

    TICK_S = 0.0864
    TOLERANCES = (1.1, 1.5, 2.0, 5.0)

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))
        cls.available = os.path.isdir(MINI_ARCHIVE)
        with open(os.path.join(MINI_ARCHIVE, "expected-runs.json"), encoding="utf-8") as fh:
            cls.manifest = json.load(fh)

    def _dat_files(self):
        out = []
        for comp in sorted(os.listdir(MINI_ARCHIVE)):
            cdir = os.path.join(MINI_ARCHIVE, comp)
            if not os.path.isdir(cdir):
                continue
            for fn in sorted(f for f in os.listdir(cdir) if f.endswith(".dat")):
                out.append((comp, fn, os.path.join(cdir, fn)))
        return out

    def _independent(self, tol):
        rows = []
        for comp, fn, path in self._dat_files():
            for s_, e_, n in independent_runs(path, tol, self.TICK_S):
                rows.append((comp, fn, s_, e_, n))
        return sorted(rows)

    def test_fixture_is_present(self):
        self.assertTrue(self.available, "tests/fixtures/mini-archive is required")

    def test_independent_segmenter_matches_the_manifest(self):
        """The manifest is not self-fulfilling: re-derive it and compare tuples."""
        for tol in self.TOLERANCES:
            with self.subTest(tolerance=tol):
                recorded = sorted(
                    (r["comparison"], r["file"], r["tick_start"], r["tick_end"], r["n_samples"])
                    for r in self.manifest["tolerances"][str(tol)]["runs"])
                self.assertEqual(self._independent(tol), recorded)

    def test_production_segmenter_matches_the_independent_one(self):
        """Tuple-for-tuple, so a change in extent cannot hide behind an unchanged count."""
        import analyse_optical as ao
        for tol in self.TOLERANCES:
            with self.subTest(tolerance=tol):
                produced = []
                for comp, fn, path in self._dat_files():
                    _h, rows, _b = ao.parse_dat(path)
                    ticks = [r[6] for r in rows]
                    flags = [r[2] for r in rows]
                    for s_, e_, n in ao.contiguous_runs(ticks, flags, keep={1, 2},
                                                        gap_tol_s=tol):
                        produced.append((comp, fn, s_, e_, n))
                self.assertEqual(sorted(produced), self._independent(tol),
                                 "production segmenter disagrees with the independent one")

    def test_total_span_matches_the_manifest(self):
        """Extent, not just topology: this is what the span-halving mutation changed."""
        for tol in self.TOLERANCES:
            with self.subTest(tolerance=tol):
                got = sum(e - s_ for _c, _f, s_, e, _n in self._independent(tol))
                self.assertEqual(got, self.manifest["tolerances"][str(tol)]["total_span_ticks"])

    def test_resegmenter_matches_the_independent_one(self):
        """The in-process sensitivity path, compared to code it does not call."""
        from optical_sensitivity import Resegmenter
        r = Resegmenter(MINI_ARCHIVE, src=os.path.join(REPO, "src/ftro/analyse_optical.py"))
        for tol in self.TOLERANCES:
            with self.subTest(tolerance=tol):
                got = sorted((c, f, a // 86400, b // 86400, n) for a, b, n, c, f in r.runs(tol))
                self.assertEqual(got, self._independent(tol))

    def test_subprocess_path_matches_the_independent_one(self):
        from optical_sensitivity import Resegmenter
        r = Resegmenter(MINI_ARCHIVE, src=os.path.join(REPO, "src/ftro/analyse_optical.py"))
        tmp = tempfile.mkdtemp(prefix="ftro-oracle-")
        self.addCleanup(shutil.rmtree, tmp, True)
        for tol in self.TOLERANCES:
            with self.subTest(tolerance=tol):
                got = sorted((c, f, a // 86400, b // 86400, n) for a, b, n, c, f
                             in r.subprocess_runs(tol, os.path.join(tmp, f"i{tol}.json")))
                self.assertEqual(got, self._independent(tol))

    def test_threshold_boundaries_are_exercised(self):
        """The fixture must contain gaps at each tolerance's threshold T and at T+1.

        Without them an off-by-one in the threshold is invisible: replacing int() with
        round() in contiguous_runs() left all 94 tests green while changing the published
        5 s row from 4,826 runs to 2,943, because 5.0 s floors to 57 ticks and rounds to
        58, and the real archive has 3,143 gaps of exactly 58 ticks (FTRO-DEF-053).
        """
        present = set(self.manifest["boundary_gaps_ticks"])
        for tol in self.TOLERANCES:
            t = int(tol / self.TICK_S + 1e-9)
            with self.subTest(tolerance=tol):
                self.assertIn(t, present, f"no gap at the threshold {t} ticks")
                self.assertIn(t + 1, present, f"no gap at threshold+1 = {t + 1} ticks")

    def test_threshold_gap_merges_and_threshold_plus_one_splits(self):
        """Directly assert the boundary semantics, per tolerance."""
        for tol in self.TOLERANCES:
            t = int(tol / self.TICK_S + 1e-9)
            runs = self._independent(tol)
            spans = {(c, f): [] for c, f, _s, _e, _n in runs}
            for c, f, s_, e, _n in runs:
                spans[(c, f)].append((s_, e))
            boundary = [v for k, v in spans.items() if k[0].startswith("EEE_")]
            self.assertTrue(boundary, "boundary comparison missing from the fixture")
            gaps = []
            for seq in boundary:
                seq.sort()
                gaps += [b[0] - a[1] for a, b in zip(seq, seq[1:])]
            with self.subTest(tolerance=tol):
                self.assertTrue(all(g > t for g in gaps),
                                f"a gap of <= {t} ticks survived as a split at {tol} s")
                self.assertIn(t + 1, gaps,
                              f"the threshold+1 gap did not split at {tol} s")

    def test_tolerances_actually_differentiate(self):
        counts = {tol: len(self._independent(tol)) for tol in self.TOLERANCES}
        self.assertGreater(len(set(counts.values())), 1,
                           f"every tolerance produced the same run count: {counts}")



class TestSensitivityAgreesWithMainComputation(unittest.TestCase):
    """The committed report must be internally coherent, and its summaries derived.

    Complements TestSegmentationOracle: that one checks the code, this one checks the
    artifact the code produced.
    """

    def setUp(self):
        with open(os.path.join(REPO, "phase0", "reports",
                               "four-domain-intersection.json"), encoding="utf-8") as fh:
            self.report = json.load(fh)

    def test_shipped_tolerance_row_matches_the_main_figures(self):
        conv = self.report["optical_support_convention"]["gap_tolerance_s"]
        scan = self.report["optical_support_sensitivity"]["gap_tolerance_scan"]
        row = scan.get(str(conv)) or scan.get(f"{conv:.1f}")
        self.assertIsNotNone(row, f"no scan row for the shipped tolerance {conv}")
        for label, main, scanned in (
                ("optical", self.report["domain_support"]["optical"]["total_hours"],
                 row["domain_h"]["optical"]),
                ("optical|vlbi", self.report["pairwise"]["optical|vlbi"]["total_hours"],
                 row["pairwise_h"]["optical|vlbi"])):
            with self.subTest(quantity=label):
                self.assertAlmostEqual(main, scanned, places=3,
                                       msg="scan and main computation disagree")

    def test_scan_run_counts_are_not_degenerate(self):
        scan = self.report["optical_support_sensitivity"]["gap_tolerance_scan"]
        counts = {k: v["n_runs"] for k, v in scan.items()}
        self.assertGreater(len(set(counts.values())), 1,
                           f"every tolerance produced the same run count: {counts}")
        self.assertGreater(min(counts.values()), 1000,
                           f"run counts implausibly low, suggesting no splitting: {counts}")

    def test_invariance_is_derived_from_every_variant_row(self):
        """Do not trust the summary fields: recompute them from the rows.

        The previous version asserted two summary booleans, so changing a variant row to
        `overlap` passed while the summaries stayed untouched (FTRO-DEF-046).
        """
        sens = self.report["optical_support_sensitivity"]
        # The variant keys are part of the claim: a renamed row silently drops a variant
        # from the invariance statement.
        self.assertEqual(sorted(sens["gap_tolerance_scan"]), ["1.1", "1.5", "2.0", "5.0"])
        self.assertEqual(sorted(sens["sample_credit"]),
                         ["per_run_nominal_block", "per_sample_nominal_1s_credit",
                          "run_span_plus_trailing_gate"])
        self.assertEqual(sorted(sens["uniform_tag_shift"]), ["+0s", "+1s", "-1s"])
        statuses, checked = set(), 0
        for group in ("gap_tolerance_scan", "sample_credit", "uniform_tag_shift"):
            for name, row in sens.get(group, {}).items():
                if not isinstance(row, dict) or "four_domain_status" not in row:
                    continue
                with self.subTest(group=group, variant=name):
                    self.assertEqual(row["four_domain_status"], "no_common_support")
                    self.assertEqual(row.get("four_domain_h"), 0.0)
                    # An empty intersection has zero intervals; a status string alone
                    # can disagree with the geometry it summarises.
                    self.assertEqual(row.get("four_domain_n_intervals"), 0)
                statuses.add(row["four_domain_status"])
                checked += 1
        self.assertEqual(checked, 10, f"expected 10 variant rows, found {checked}")
        self.assertEqual(statuses, {"no_common_support"})
        # The summaries must AGREE with what the rows say, not stand in for them.
        self.assertEqual(set(sens["four_domain_status_over_all_variants"]), statuses)
        self.assertIs(sens["four_domain_status_invariant"], len(statuses) == 1)


class TestVersionGate(unittest.TestCase):
    """The git-based version gate (C10).

    Replaced a 275-line registry state machine whose maintenance flags produced four
    defects of their own. git is the trusted base; there is no registry to fall out of
    date and no flag that can weaken a check.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ftro-ver-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _run(self, cwd):
        return subprocess.run([sys.executable, "src/ftro/check_versions.py", "--check"],
                              cwd=cwd, capture_output=True, text=True, timeout=120)

    def test_an_unmodified_repo_is_clean(self):
        work = self._mutated_repo(lambda _w: None)
        self.assertEqual(self._run(work).returncode, 0, self._run(work).stderr)

    BASELINE = "# FTRO Source Ledger\n\n**Version:** 0.4.0 · **Opened:** 2026-08-25\n\nbody\n"

    def _mutated_repo(self, mutate):
        """A self-contained git repo with one versioned file, then mutated (M12).

        Built from scratch rather than cloned: cloning REPO made these tests skip on a
        clean `git archive` export, which is exactly the "a skipped test reports success"
        failure recorded as FTRO-DEF-031.
        """
        work = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(work, "ledgers"), exist_ok=True)
        shutil.copytree(os.path.join(REPO, "src"), os.path.join(work, "src"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        with open(os.path.join(work, "ledgers", "source-ledger.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self.BASELINE)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        for cmd in (["init", "--quiet", "-b", "main"], ["add", "-A"],
                    ["commit", "--quiet", "-m", "baseline"]):
            r = subprocess.run(["git", *cmd], cwd=work, capture_output=True,
                               text=True, timeout=120, env=env)
            self.assertEqual(r.returncode, 0, f"git {cmd[0]} failed: {r.stderr[:200]}")
        mutate(work)
        return work

    def test_content_change_without_a_bump_is_detected(self):
        def mutate(work):
            with open(os.path.join(work, "ledgers", "source-ledger.md"), "a",
                      encoding="utf-8") as fh:
                fh.write("\n<!-- substantive change with no version bump -->\n")
        r = self._run(self._mutated_repo(mutate))
        self.assertEqual(r.returncode, 1, "the version gate did not detect content drift")
        self.assertIn("content changed but version is still", r.stderr)

    def test_gaining_a_version_is_not_a_fault(self):
        """A previously unversioned document that gains a version has nothing to advance from.

        Found by running the gate against HEAD~1 after the consolidation commit: the
        branch was unguarded and raised AttributeError.
        """
        def mutate(work):
            t = os.path.join(work, "ledgers", "source-ledger.md")
            with open(t, encoding="utf-8") as fh:
                body = fh.read()
            with open(t, "w", encoding="utf-8") as fh:
                fh.write(body.replace("**Version:** 0.4.0 · ", "", 1))
        work = self._mutated_repo(mutate)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        subprocess.run(["git", "commit", "--quiet", "-am", "drop version"],
                       cwd=work, capture_output=True, timeout=120, env=env)
        with open(os.path.join(work, "ledgers", "source-ledger.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(self.BASELINE)
        r = self._run(work)
        self.assertEqual(r.returncode, 0, f"gaining a version was treated as a fault: {r.stderr}")
        self.assertNotIn("Traceback", r.stderr)

    def test_version_downgrade_is_detected(self):
        def mutate(work):
            t = os.path.join(work, "ledgers", "source-ledger.md")
            with open(t, encoding="utf-8") as fh:
                body = fh.read()
            m = re.search(r"\*\*Version:\*\* ([0-9]+\.[0-9]+\.[0-9]+)", body)
            with open(t, "w", encoding="utf-8") as fh:
                fh.write(body.replace(m.group(0), "**Version:** 0.0.1", 1))
        r = self._run(self._mutated_repo(mutate))
        self.assertEqual(r.returncode, 1)
        self.assertIn("went backwards", r.stderr)

    def test_removing_a_version_is_detected(self):
        def mutate(work):
            t = os.path.join(work, "ledgers", "source-ledger.md")
            with open(t, encoding="utf-8") as fh:
                body = fh.read()
            m = re.search(r"\*\*Version:\*\* [0-9]+\.[0-9]+\.[0-9]+ · ", body)
            with open(t, "w", encoding="utf-8") as fh:
                fh.write(body.replace(m.group(0), "", 1))
        r = self._run(self._mutated_repo(mutate))
        self.assertEqual(r.returncode, 1)
        self.assertIn("was removed", r.stderr)

class TestPreflightDigestValidation(unittest.TestCase):
    """A registry entry must be a digest, not merely a key (FTRO-DEF-042)."""

    def setUp(self):
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))
        self.tmp = tempfile.mkdtemp(prefix="ftro-pf-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_malformed_expectations_are_rejected(self):
        import pinning
        good = "a" * 64
        for bad in (None, "", "abc", "A" * 64, 12345, "g" * 64, good[:63]):
            with self.subTest(value=bad):
                with self.assertRaises(SystemExit):
                    pinning.preflight({"x": bad}, ["x"], what="thing")

    def test_trailing_whitespace_is_not_a_digest(self):
        """fullmatch, not match: a trailing newline used to validate."""
        import pinning
        for bad in ("a" * 64 + "\n", " " + "a" * 64, "a" * 64 + " "):
            with self.subTest(value=repr(bad)):
                self.assertFalse(pinning.valid_digest(bad))

    def test_explicit_digest_argument_is_validated_before_retrieval(self):
        out = os.path.join(self.tmp, "x.json")
        cache = os.path.join(self.tmp, "xcache")
        r = subprocess.run(
            [sys.executable, "src/ftro/pin_vgosdb.py",
             "--url", "file://" + os.path.join(FIXTURES, "vgosdb_min.tgz"),
             "--session", "R11040", "--cache", cache, "--out", out,
             "--expect-sha256", "abc"],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertIn("preflight", r.stderr + r.stdout)
        self.assertFalse(os.path.isdir(cache) and os.listdir(cache),
                         "an invalid explicit digest still caused a fetch")

    def test_a_well_formed_digest_is_accepted(self):
        import pinning
        self.assertEqual(pinning.preflight({"x": "a" * 64}, ["x"], what="thing"), [])

    def test_allow_unpinned_does_not_excuse_a_malformed_entry(self):
        """--allow-unpinned means 'not recorded yet', not 'recorded as garbage'."""
        import pinning
        with self.assertRaises(SystemExit):
            pinning.preflight({"x": None}, ["x"], allow_unpinned=True, what="thing")

    def test_no_request_is_issued_when_preflight_fails(self):
        """Count REQUESTS, not cached bytes.

        The earlier test observed the diagnostic and an empty cache directory -- but bytes
        are not cached until verification, so moving retrieval before the preflight error
        kept every test green (FTRO-DEF-057). This spies on urlopen itself.
        """
        import importlib
        import urllib.request
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))
        calls = []
        real = urllib.request.urlopen

        def spy(*a, **kw):
            calls.append(a[0])
            return real(*a, **kw)

        pv = importlib.import_module("pin_vgosdb")
        urllib.request.urlopen = spy
        self.addCleanup(setattr, urllib.request, "urlopen", real)
        reg = os.path.join(self.tmp, "spy-registry.json")
        with open(reg, "w", encoding="utf-8") as fh:
            json.dump({"vgosdb": {"vgosdb_min.tgz": None}}, fh)
        argv = sys.argv
        sys.argv = ["pin_vgosdb.py",
                    "--url", "file://" + os.path.join(FIXTURES, "vgosdb_min.tgz"),
                    "--session", "R11040",
                    "--cache", os.path.join(self.tmp, "spycache"),
                    "--out", os.path.join(self.tmp, "spy.json"),
                    "--expect", reg]
        try:
            with self.assertRaises(SystemExit):
                pv.main()
        finally:
            sys.argv = argv
        self.assertEqual(calls, [], "preflight failed but a request was still issued")

    def test_null_expectation_stops_the_pinner_before_retrieval(self):
        reg = os.path.join(self.tmp, "reg.json")
        with open(reg, "w", encoding="utf-8") as fh:
            json.dump({"vgosdb": {"vgosdb_min.tgz": None}}, fh)
        out = os.path.join(self.tmp, "pin.json")
        cache = os.path.join(self.tmp, "cache")
        r = subprocess.run(
            [sys.executable, "src/ftro/pin_vgosdb.py",
             "--url", "file://" + os.path.join(FIXTURES, "vgosdb_min.tgz"),
             "--session", "R11040", "--cache", cache, "--out", out, "--expect", reg],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertIn("64-character hex", r.stderr + r.stdout)
        self.assertFalse(os.path.exists(out), "a null expectation minted an identity")
        self.assertFalse(os.path.isdir(cache) and os.listdir(cache),
                         "a null expectation cached bytes")


class TestSchemaContract(unittest.TestCase):
    """C3: one declaration, applied by producer and consumer alike."""

    def setUp(self):
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))

    def test_every_committed_report_conforms(self):
        import schema
        for name in ("igs-artifact-pins", "ppta-artifact-pins",
                     "evidence-repo-pins", "vlbi-vgosdb-pin"):
            with self.subTest(report=name):
                with open(os.path.join(REPO, "phase0", "reports", f"{name}.json"),
                          encoding="utf-8") as fh:
                    doc = json.load(fh)
                if not isinstance(doc.get("pins"), list):
                    doc = dict(doc, pins=[doc])
                self.assertEqual(schema.validate(doc, schema.PIN_REPORT), [])

    def test_schema_rejects_the_whole_absent_field_family(self):
        """The eight-entry family that was previously fixed one site at a time."""
        import schema
        with open(os.path.join(REPO, "phase0", "reports", "igs-artifact-pins.json"),
                  encoding="utf-8") as fh:
            good = json.load(fh)
        cases = {
            "counter absent": lambda d: d.pop("n_failed"),
            "counter is false": lambda d: d.__setitem__("n_failed", False),
            "counter is float": lambda d: d.__setitem__("n_pinned", 57.0),
            "list absent": lambda d: d.pop("failures"),
            "list is object": lambda d: d.__setitem__("failures", {}),
            "list is string": lambda d: d.__setitem__("uncovered_by_registry", "ghost"),
            "pins is object": lambda d: d.__setitem__("pins", {}),
            "pin entry not object": lambda d: d["pins"].__setitem__(0, "x"),
            "pin field absent": lambda d: d["pins"][0].pop("retrieval_validation"),
            "digest truncated": lambda d: d["pins"][0].__setitem__("sha256", "abc"),
            "count disagrees": lambda d: d.__setitem__("n_pinned", 1),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                doc = json.loads(json.dumps(good))
                mutate(doc)
                self.assertNotEqual(schema.validate(doc, schema.PIN_REPORT), [],
                                    f"schema accepted: {label}")

    def test_producer_cannot_promote_a_nonconforming_report(self):
        """C3: promotion validates the same declaration the consumer applies."""
        import pinning
        tmp = tempfile.mkdtemp(prefix="ftro-promo-")
        self.addCleanup(shutil.rmtree, tmp, True)
        out = os.path.join(tmp, "r.json")
        bad = {"generator": "x", "retrieval_validation": "content_validated",
               "n_pinned": 1, "n_failed": 0, "n_without_expected_digest": 0,
               "pins": [{"name": "a"}], "failures": [], "uncovered_by_registry": []}
        self.assertFalse(pinning.promote(bad, out, True),
                         "a non-conforming report was promoted")
        self.assertFalse(os.path.exists(out))
        self.assertTrue(os.path.exists(out + ".rejected"))


class TestDerivedSemantics(unittest.TestCase):
    """C5: meaning is derived from authenticated names, not read from unbound fields."""

    def setUp(self):
        sys.path.insert(0, os.path.join(REPO, "src", "ftro"))

    def test_igs_day_is_derived_from_the_filename(self):
        import four_domain_intersection as fdi
        self.assertEqual(fdi.igs_day_from_name("igs21980.sp3.Z"), 59630)
        self.assertEqual(fdi.igs_day_from_name("igs21992.clk.Z"), 59639)
        self.assertIsNone(fdi.igs_day_from_name("igs21987.erp.Z"), "day 7 is the weekly summary")
        self.assertIsNone(fdi.igs_day_from_name("igr21980.sp3.Z"), "Rapid is not a Final product")

    def test_relabelling_a_report_field_has_no_effect(self):
        """M6: the mutation that drove GNSS support from 240 h to 0 h."""
        import four_domain_intersection as fdi
        names = ["igs21980.sp3.Z", "igs21981.sp3.Z"]
        as_igs = sorted(d for d in (fdi.igs_day_from_name(n) for n in names) if d)
        self.assertEqual(as_igs, [59630, 59631],
                         "derivation depends on something other than the name")


if __name__ == "__main__":
    unittest.main(verbosity=2)
