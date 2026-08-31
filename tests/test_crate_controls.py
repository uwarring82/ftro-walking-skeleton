#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independent boundary tests for the root RO-Crate publication controls."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ftro_refresh_crate_controls", REPO / "src" / "ftro" / "refresh_crate.py"
)
REFRESH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REFRESH)

# These are intentionally independent of refresh_crate.py.  A production scope mutation
# must disagree with the test oracle instead of shrinking both populations together.
EXPECTED_PHASE_ROOTS = ("phase1", "phase2")
EXPECTED_SUFFIXES = frozenset({".md", ".json", ".py"})
EXPECTED_MAX_DEPTH = 3  # path components below a phase root, including the file name
EXPECTED_EXCLUDED_DIRECTORIES = frozenset({"__pycache__", ".ipynb_checkpoints"})
EXPECTED_FLAT_DOCUMENTS = {
    "labnotes": frozenset({".md"}),
    "ledgers": frozenset({".json", ".md"}),
    "tests": frozenset({".py"}),
}
EXPECTED_DISCOVERED_COLLECTIONS = {"tests": "tests/"}


@contextlib.contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def independent_phase_population(repo, root):
    base = repo / root
    paths = []
    if not base.is_dir():
        return paths
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        below = path.relative_to(base).parts
        if any(part in EXPECTED_EXCLUDED_DIRECTORIES for part in below[:-1]):
            continue
        if len(below) > EXPECTED_MAX_DEPTH:
            continue
        if path.suffix not in EXPECTED_SUFFIXES:
            raise AssertionError(f"unknown in-scope phase suffix: {path.relative_to(repo)}")
        paths.append(path.relative_to(repo).as_posix())
    return paths


def independent_reference_ids(entity, key):
    value = entity.get(key, [])
    rows = value if isinstance(value, list) else [value]
    return {
        row["@id"] for row in rows
        if isinstance(row, dict) and isinstance(row.get("@id"), str)
    }


class CrateFixture:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / "phase1").mkdir(parents=True)
        (self.root / "phase2").mkdir(parents=True)
        (self.root / "phase1" / "visible.md").write_text("AA\n", encoding="utf-8")
        (self.root / "phase2" / "visible.json").write_text("{}\n", encoding="utf-8")
        self.write_crate({
            "@context": "https://w3id.org/ro/crate/1.3/context",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.json",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"},
                    "name": "RO-Crate Metadata Descriptor",
                },
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Dataset A",
                    "dateModified": "2026-08-29",
                    "hasPart": [{"@id": "tests/"}],
                },
                {
                    "@id": "tests/",
                    "@type": "Dataset",
                    "name": "Tests",
                    "hasPart": [],
                },
            ],
        })

    @property
    def crate_path(self):
        return self.root / "ro-crate-metadata.json"

    def read_crate(self):
        return json.loads(self.crate_path.read_text(encoding="utf-8"))

    def write_crate(self, crate):
        self.crate_path.write_text(
            json.dumps(crate, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def run(self, *argv, date="2026-08-30"):
        stdout, stderr = io.StringIO(), io.StringIO()
        with working_directory(self.root), mock.patch.dict(
            os.environ, {REFRESH.CRATE_DATE_ENV: date}, clear=False
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = REFRESH.main(list(argv))
        return result, stdout.getvalue(), stderr.getvalue()

    def establish(self, date="2026-08-30"):
        result, stdout, stderr = self.run(date=date)
        if result != 0:
            raise AssertionError(stdout + stderr)


class TestBoundedPhaseDiscovery(unittest.TestCase):
    def test_production_policy_matches_the_independent_fixed_scope(self):
        self.assertEqual(set(REFRESH.DISCOVERED_DOCUMENTS), set(EXPECTED_FLAT_DOCUMENTS))
        for root, suffixes in EXPECTED_FLAT_DOCUMENTS.items():
            self.assertEqual(frozenset(REFRESH.DISCOVERED_DOCUMENTS[root]), suffixes)
        self.assertEqual(REFRESH.DISCOVERED_COLLECTIONS, EXPECTED_DISCOVERED_COLLECTIONS)
        self.assertEqual(tuple(sorted(REFRESH.DISCOVERED_TREES)), EXPECTED_PHASE_ROOTS)
        for root in EXPECTED_PHASE_ROOTS:
            self.assertEqual(frozenset(REFRESH.DISCOVERED_TREES[root]), EXPECTED_SUFFIXES)
        self.assertEqual(REFRESH.MAX_DISCOVERY_DEPTH, EXPECTED_MAX_DEPTH)
        self.assertEqual(
            frozenset(REFRESH.EXCLUDED_DIRECTORY_NAMES), EXPECTED_EXCLUDED_DIRECTORIES
        )
        self.assertEqual(REFRESH.UNKNOWN_PHASE_SUFFIX_POLICY, "error")

    def test_current_phase_population_has_graph_and_root_membership(self):
        crate = json.loads((REPO / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        root_parts = independent_reference_ids(graph["./"], "hasPart")
        expected = set()
        for root in EXPECTED_PHASE_ROOTS:
            expected.update(independent_phase_population(REPO, root))
        with working_directory(REPO):
            produced = {
                path for path in REFRESH.discovered_documents()
                if path.startswith(("phase1/", "phase2/"))
            }
        self.assertEqual(produced, expected)
        self.assertEqual(expected - set(graph), set())
        self.assertEqual(expected - root_parts, set())

    def test_current_flat_test_population_has_graph_and_root_membership(self):
        crate = json.loads((REPO / "ro-crate-metadata.json").read_text(encoding="utf-8"))
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        root_parts = independent_reference_ids(graph["./"], "hasPart")
        collection_parts = independent_reference_ids(graph["tests/"], "hasPart")
        expected = {
            path.relative_to(REPO).as_posix()
            for path in (REPO / "tests").glob("*.py")
            if path.is_file()
        }
        with working_directory(REPO):
            produced = {
                path for path in REFRESH.discovered_documents()
                if path.startswith("tests/")
            }
        self.assertEqual(produced, expected)
        self.assertEqual(expected - set(graph), set())
        self.assertEqual(expected - root_parts, set())
        self.assertEqual(expected - collection_parts, set())

    def test_new_flat_test_is_added_to_graph_root_and_collection(self):
        with tempfile.TemporaryDirectory(prefix="ftro-crate-flat-test-") as temporary:
            fixture = CrateFixture(temporary)
            path = fixture.root / "tests" / "helper.py"
            path.parent.mkdir()
            path.write_text("VALUE = 1\n", encoding="utf-8")
            result, stdout, stderr = fixture.run(date="2026-08-31")
            self.assertEqual(result, 0, stdout + stderr)
            graph = {row["@id"]: row for row in fixture.read_crate()["@graph"]}
            self.assertIn("tests/helper.py", graph)
            self.assertIn("tests/helper.py", independent_reference_ids(graph["./"], "hasPart"))
            self.assertIn(
                "tests/helper.py", independent_reference_ids(graph["tests/"], "hasPart")
            )

    def test_inclusive_depth_T_and_T_plus_one(self):
        with tempfile.TemporaryDirectory(prefix="ftro-crate-depth-") as temporary:
            root = Path(temporary, "phase1")
            at_limit = root / "a" / "b" / "at-limit.json"
            beyond = root / "a" / "b" / "c" / "beyond.json"
            at_limit.parent.mkdir(parents=True)
            beyond.parent.mkdir(parents=True)
            at_limit.write_text("{}\n", encoding="utf-8")
            beyond.write_text("{}\n", encoding="utf-8")
            found = set(REFRESH.discovered_tree(str(root), EXPECTED_SUFFIXES))
            self.assertIn(str(at_limit).replace(os.sep, "/"), found)
            self.assertNotIn(str(beyond).replace(os.sep, "/"), found)

    def test_excluded_directories_have_real_fixtures(self):
        with tempfile.TemporaryDirectory(prefix="ftro-crate-exclusion-") as temporary:
            root = Path(temporary, "phase1")
            visible = root / "visible.py"
            hidden_cache = root / "__pycache__" / "hidden.py"
            hidden_notebook = root / ".ipynb_checkpoints" / "hidden.md"
            for path in (visible, hidden_cache, hidden_notebook):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("pass\n", encoding="utf-8")
            found = set(REFRESH.discovered_tree(str(root), EXPECTED_SUFFIXES))
            self.assertIn(str(visible).replace(os.sep, "/"), found)
            self.assertNotIn(str(hidden_cache).replace(os.sep, "/"), found)
            self.assertNotIn(str(hidden_notebook).replace(os.sep, "/"), found)

    def test_unknown_phase_suffix_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="ftro-crate-suffix-") as temporary:
            root = Path(temporary, "phase1")
            root.mkdir()
            (root / "future.csv").write_text("x\n", encoding="utf-8")
            with self.assertRaisesRegex(REFRESH.DiscoveryPolicyError, "future.csv"):
                REFRESH.discovered_tree(str(root), EXPECTED_SUFFIXES)

    def test_unknown_phase_suffix_stops_publication_without_rewriting_crate(self):
        with tempfile.TemporaryDirectory(prefix="ftro-crate-suffix-main-") as temporary:
            fixture = CrateFixture(temporary)
            fixture.establish()
            before = fixture.crate_path.read_bytes()
            (fixture.root / "phase2" / "future.csv").write_text("x\n", encoding="utf-8")
            result, stdout, stderr = fixture.run(date="2026-08-31")
            self.assertEqual(result, 1)
            self.assertIn("PUBLICATION POLICY ERROR", stdout + stderr)
            self.assertEqual(fixture.crate_path.read_bytes(), before)

    def test_per_suffix_metadata_and_unknown_factory_suffix(self):
        expected = {
            "a.md": ("text/markdown", REFRESH.CC_BY, "File"),
            "a.json": ("application/json", REFRESH.CC_BY, "File"),
            "a.py": ("text/x-python", REFRESH.APACHE, ["File", "SoftwareSourceCode"]),
        }
        for path, (encoding, licence, kinds) in expected.items():
            with self.subTest(path=path):
                entity = REFRESH.document_entity(path)
                self.assertEqual(entity["encodingFormat"], encoding)
                self.assertEqual(entity["license"]["@id"], licence)
                self.assertEqual(entity["@type"], kinds)
        with self.assertRaises(ValueError):
            REFRESH.document_entity("a.csv")


class TestCrateGraphAndPublicationFingerprint(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ftro-crate-control-")
        self.fixture = CrateFixture(self.temporary.name)
        self.fixture.establish()

    def tearDown(self):
        self.temporary.cleanup()

    def test_both_graph_entity_and_root_membership_are_required(self):
        for mutation, message in (
            ("graph", "graph entity phase2/visible.json"),
            ("root", "root hasPart phase2/visible.json"),
        ):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory(
                    prefix=f"ftro-crate-{mutation}-"
                ) as temporary:
                    fixture = CrateFixture(temporary)
                    fixture.establish()
                    crate = fixture.read_crate()
                    if mutation == "graph":
                        crate["@graph"] = [
                            row for row in crate["@graph"]
                            if row.get("@id") != "phase2/visible.json"
                        ]
                    else:
                        root = next(
                            row for row in crate["@graph"] if row.get("@id") == "./"
                        )
                        root["hasPart"] = [
                            row for row in root["hasPart"]
                            if row.get("@id") != "phase2/visible.json"
                        ]
                    fixture.write_crate(crate)
                    result, stdout, stderr = fixture.run("--check", date="2026-08-31")
                    self.assertEqual(result, 1)
                    self.assertIn(message, stdout + stderr)

    def test_clean_older_publication_remains_current_on_a_later_day(self):
        result, stdout, stderr = self.fixture.run("--check", date="2026-08-31")
        self.assertEqual(result, 0, stdout + stderr)

    def test_same_size_local_content_change_is_detected_and_advances_date(self):
        target = self.fixture.root / "phase2" / "visible.json"
        self.assertEqual(target.stat().st_size, len("[]\n".encode("utf-8")))
        target.write_text("[]\n", encoding="utf-8")
        result, stdout, stderr = self.fixture.run("--check", date="2026-08-31")
        self.assertEqual(result, 1)
        self.assertIn("publication-control identifier", stdout + stderr)
        self.assertIn("./ dateModified", stdout + stderr)

        result, stdout, stderr = self.fixture.run(date="2026-08-31")
        self.assertEqual(result, 0, stdout + stderr)
        crate = self.fixture.read_crate()
        graph = {row["@id"]: row for row in crate["@graph"]}
        self.assertEqual(graph["./"]["dateModified"], "2026-08-31")
        self.assertEqual(
            graph[REFRESH.PUBLICATION_CONTROL_ID]["dateModified"], "2026-08-31"
        )
        result, stdout, stderr = self.fixture.run("--check", date="2026-09-01")
        self.assertEqual(result, 0, stdout + stderr)

    def test_root_descriptor_semantic_change_is_detected_even_at_equal_length(self):
        before_size = self.fixture.crate_path.stat().st_size
        crate = self.fixture.read_crate()
        root = next(row for row in crate["@graph"] if row.get("@id") == "./")
        self.assertEqual(len(root["name"]), len("Dataset B"))
        root["name"] = "Dataset B"
        self.fixture.write_crate(crate)
        self.assertEqual(self.fixture.crate_path.stat().st_size, before_size)
        result, stdout, stderr = self.fixture.run("--check", date="2026-08-31")
        self.assertEqual(result, 1)
        self.assertIn("publication-control identifier", stdout + stderr)
        self.assertIn("./ dateModified", stdout + stderr)

    def test_control_semantic_change_is_detected_even_at_equal_length(self):
        before_size = self.fixture.crate_path.stat().st_size
        crate = self.fixture.read_crate()
        control = next(
            row for row in crate["@graph"]
            if row.get("@id") == REFRESH.PUBLICATION_CONTROL_ID
        )
        replacement = "FTRO root-crate publication controL"
        self.assertEqual(len(control["name"]), len(replacement))
        control["name"] = replacement
        self.fixture.write_crate(crate)
        self.assertEqual(self.fixture.crate_path.stat().st_size, before_size)
        result, stdout, stderr = self.fixture.run("--check", date="2026-08-31")
        self.assertEqual(result, 1)
        self.assertIn("publication-control identifier", stdout + stderr)

    def test_legacy_or_extended_control_declaration_cannot_be_re_signed(self):
        canonical_description = REFRESH.publication_control_entity("2026-08-30")[
            "description"
        ]
        for mutation in ("legacy_description", "extra_field"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                prefix=f"ftro-crate-control-declaration-{mutation}-"
            ) as temporary:
                fixture = CrateFixture(temporary)
                fixture.establish()
                crate = fixture.read_crate()
                control = next(
                    row for row in crate["@graph"]
                    if row.get("@id") == REFRESH.PUBLICATION_CONTROL_ID
                )
                if mutation == "legacy_description":
                    control["description"] = (
                        "Deterministic SHA-256 over the root-crate graph (excluding this "
                        "control node) and every non-volatile local file entity. It detects "
                        "same-size content drift and semantic edits to ro-crate-metadata.json."
                    )
                else:
                    control["unregisteredScope"] = "silently widened"
                # Re-sign the mutated declaration exactly as the former implementation did.
                control["identifier"] = (
                    REFRESH.PUBLICATION_FINGERPRINT_PREFIX
                    + REFRESH.publication_fingerprint(crate)
                )
                fixture.write_crate(crate)

                result, stdout, stderr = fixture.run("--check", date="2026-08-31")
                self.assertEqual(result, 1)
                self.assertIn(REFRESH.PUBLICATION_CONTROL_ID, stdout + stderr)

                result, stdout, stderr = fixture.run(date="2026-08-31")
                self.assertEqual(result, 0, stdout + stderr)
                repaired = {
                    row["@id"]: row for row in fixture.read_crate()["@graph"]
                }[REFRESH.PUBLICATION_CONTROL_ID]
                self.assertEqual(repaired["description"], canonical_description)
                self.assertEqual(
                    set(repaired),
                    {"@id", "@type", "name", "description", "identifier", "dateModified"},
                )
                result, stdout, stderr = fixture.run("--check", date="2026-09-01")
                self.assertEqual(result, 0, stdout + stderr)

    def test_failed_write_is_atomic_at_the_descriptor_boundary(self):
        target = self.fixture.root / "phase2" / "visible.json"
        target.unlink()
        before = self.fixture.crate_path.read_bytes()
        result, stdout, stderr = self.fixture.run(date="2026-08-31")
        self.assertEqual(result, 1)
        self.assertIn("MISSING FILE", stdout + stderr)
        self.assertIn("left unchanged", stdout + stderr)
        self.assertEqual(self.fixture.crate_path.read_bytes(), before)

    def test_atomic_replace_failure_leaves_descriptor_unchanged(self):
        target = self.fixture.root / "phase2" / "visible.json"
        target.write_text("[]\n", encoding="utf-8")
        before = self.fixture.crate_path.read_bytes()
        with mock.patch.object(REFRESH.os, "replace", side_effect=OSError("injected")):
            result, stdout, stderr = self.fixture.run(date="2026-08-31")
        self.assertEqual(result, 1)
        self.assertIn("left unchanged", stdout + stderr)
        self.assertEqual(self.fixture.crate_path.read_bytes(), before)

    def test_successful_atomic_write_preserves_descriptor_permissions(self):
        os.chmod(self.fixture.crate_path, 0o644)
        target = self.fixture.root / "phase2" / "visible.json"
        target.write_text("[]\n", encoding="utf-8")
        result, stdout, stderr = self.fixture.run(date="2026-08-31")
        self.assertEqual(result, 0, stdout + stderr)
        self.assertEqual(stat.S_IMODE(self.fixture.crate_path.stat().st_mode), 0o644)

    def test_control_node_and_root_subject_are_both_required(self):
        for mutation, message in (
            ("node", f"graph entity {REFRESH.PUBLICATION_CONTROL_ID}"),
            ("link", f"root subjectOf {REFRESH.PUBLICATION_CONTROL_ID}"),
        ):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory(
                    prefix=f"ftro-crate-{mutation}-"
                ) as temporary:
                    fixture = CrateFixture(temporary)
                    fixture.establish()
                    crate = fixture.read_crate()
                    if mutation == "node":
                        crate["@graph"] = [
                            row for row in crate["@graph"]
                            if row.get("@id") != REFRESH.PUBLICATION_CONTROL_ID
                        ]
                    else:
                        root = next(
                            row for row in crate["@graph"] if row.get("@id") == "./"
                        )
                        root.pop("subjectOf")
                    fixture.write_crate(crate)
                    result, stdout, stderr = fixture.run("--check", date="2026-08-31")
                    self.assertEqual(result, 1)
                    self.assertIn(message, stdout + stderr)


if __name__ == "__main__":
    unittest.main()
