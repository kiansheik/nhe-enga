"""Acceptance checks for the read-only Pages size preflight."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_pages_size.py"
SPEC = importlib.util.spec_from_file_location("check_pages_size", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PagesSizeTests(unittest.TestCase):
    def test_complete_tree_counts_repeated_blob_paths_and_book_groups(self):
        # Identical bytes served at different URLs still consume artifact space.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tree.json"
            path.write_text(json.dumps({"truncated": False, "tree": [
                {"type": "tree", "path": "docs", "sha": "directory"},
                {"type": "tree", "path": "docs/primary_sources", "sha": "directory"},
                {"type": "tree", "path": "docs/primary_sources/book", "sha": "directory"},
                {"type": "blob", "path": "docs/primary_sources/book/1.jpg", "size": 40, "sha": "same"},
                {"type": "blob", "path": "docs/primary_sources/book/2.jpg", "size": 40, "sha": "same"},
                {"type": "blob", "path": "index.html", "size": 20, "sha": "other"},
            ]}))
            report = MODULE.summarize(MODULE.entries_from_tree(path), 100, 40)
            self.assertEqual(report["total_bytes"], 100)
            self.assertTrue(report["within_budget"])
            self.assertEqual(report["groups"]["docs/primary_sources/book"]["bytes"], 80)
            self.assertFalse(MODULE.summarize(MODULE.entries_from_tree(path), 99, 40)["within_budget"])

    def test_incomplete_tree_is_not_a_passing_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tree.json"
            for tree in [
                {"truncated": True, "tree": []},
                {"tree": []},
                {"truncated": False, "tree": [{"type": "blob", "path": "missing-size"}]},
                {"truncated": False, "tree": [
                    {"type": "tree", "path": "docs"},
                    {"type": "blob", "path": "index.html", "size": 25},
                ]},
                {"truncated": False, "tree": [
                    {"type": "blob", "path": "docs/index.html", "size": 25},
                ]},
            ]:
                path.write_text(json.dumps(tree))
                result = subprocess.run([sys.executable, str(SCRIPT), "--tree-json", str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("PASS", result.stdout)

    def test_oversized_file_fails_even_with_total_headroom(self):
        report = MODULE.summarize([("large.pdf", 51), ("index.html", 1)], 1000, 50)
        self.assertFalse(report["within_budget"])
        self.assertEqual(report["oversized_files"], [{"path": "large.pdf", "bytes": 51}])

    def test_directory_cli_measures_bytes_without_changing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "docs/primary_sources/book/1.jpg"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"x" * 31)
            (root / "index.html").write_bytes(b"x" * 10)
            result = subprocess.run([sys.executable, str(SCRIPT), str(root), "--max-bytes", "40", "--json"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["total_bytes"], 41)
            self.assertEqual(image.read_bytes(), b"x" * 31)

    def test_unreadable_directory_is_not_silently_omitted(self):
        def inaccessible_walk(root, *, onerror):
            onerror(PermissionError("Unreadable artifact directory"))
            yield  # Keep this a generator, as os.walk is.

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(MODULE.os, "walk", inaccessible_walk):
                with self.assertRaises(PermissionError):
                    MODULE.entries_from_directory(Path(directory))

    def test_symlink_directory_is_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "book").mkdir()
            (root / "book/1.jpg").write_bytes(b"x" * 31)
            (root / "alias").symlink_to(root / "book", target_is_directory=True)
            result = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
