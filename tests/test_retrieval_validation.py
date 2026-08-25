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
        rec = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as fh:
                rec = json.load(fh)
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
                            continue          # timestamps differ per run by construction
                        self.assertEqual(pin[field], rec[field],
                                         "generator and manifest disagree")

    def test_generated_composition_fields_are_conforming(self):
        """Profile §5.1 must hold for generated output, not only for the stored manifest."""
        for path, expected in GENERATOR_REPORTS.items():
            pins = _report_pins(path)
            for cid in expected:
                pin = pins.get(cid, {})
                if pin.get("snapshot_kind") != "ftro_composed":
                    continue
                with self.subTest(report=path, concept=cid):
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
        """A digest in the registry must appear as ENFORCED in the report, not merely equal."""
        for section, path in self.SECTIONS.items():
            if section == "vgosdb":
                continue      # single pin, asserted by its own test
            with open(os.path.join(REPO, path), encoding="utf-8") as fh:
                doc = json.load(fh)
            for pin in doc["pins"]:
                with self.subTest(section=section, name=pin.get("name") or pin.get("key")):
                    self.assertIsNotNone(pin.get("expected_sha256"),
                                         "pinned without an expected digest: the registry "
                                         "exists but was not applied")
                    self.assertIs(pin.get("checksum_match"), True)

    def test_no_report_declares_incomplete_validation(self):
        for section, path in self.SECTIONS.items():
            with open(os.path.join(REPO, path), encoding="utf-8") as fh:
                doc = json.load(fh)
            with self.subTest(section=section):
                self.assertIn(doc.get("retrieval_validation"),
                              ("content_validated", None),
                              "a report declaring incomplete validation must not be committed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
