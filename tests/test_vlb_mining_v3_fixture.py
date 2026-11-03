"""Deterministic and contamination-safe V3 review fixture checks."""
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


if __name__ == "__main__":
    unittest.main()
