"""Deterministic and contamination-safe V3 review fixture checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class V3BlindFixtureTest(unittest.TestCase):
    def test_metadata_only_registration_rebuilds_and_validates(self):
        result = subprocess.run(
            [sys.executable, "vlb/mining/benchmark-v3/validate_fixture.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["cases"], 24)
        self.assertEqual(report["correction_decisions_excluded"], 8)
        self.assertEqual(
            report["live_manifest_sha256"],
            hashlib.sha256((ROOT / "vlb/data/manifest.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            report["normalized_live_citation_fields"],
            ["correction", "definition_sha256"],
        )
        registration = json.loads(
            (ROOT / "vlb/mining/benchmark-v3/preregistered_sample.json").read_text()
        )
        self.assertEqual(
            report["frozen_manifest_sha256"],
            registration["inputs"]["manifest_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
