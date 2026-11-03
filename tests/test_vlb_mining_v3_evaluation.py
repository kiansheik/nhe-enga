"""Integrity and disclosure checks for the post-release V3 evaluation."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "vlb/mining/output-v3"


class V3EvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, "vlb/mining/benchmark-v3/validate_annotations.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [sys.executable, "vlb/mining/evaluate_v3.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        cls.result = json.loads(
            (OUTPUT / "test_labels-evaluation.json").read_text(encoding="utf-8")
        )

    def test_frozen_ranker_metrics_are_bounded_and_reproducible(self):
        counts = self.result["ranker"]["counts"]
        self.assertEqual(counts["all_cases"], 24)
        self.assertEqual(counts["clear_cases"], 21)
        self.assertEqual(counts["ambiguous_cases"], 3)
        self.assertEqual(counts["top1_correct"], 20)
        self.assertEqual(counts["top1_exact_attested_span"], 15)
        self.assertEqual(counts["offered_exact_attested_span"], 19)
        self.assertEqual(counts["existing_top1_correct"], 15)
        self.assertEqual(counts["existing_top3_contains_gold"], 18)
        self.assertEqual(
            self.result["provenance"]["pre_v3_reader_source_commit"],
            "b5df369af6a7d2db72f933746ca6b5c13a44310d",
        )
        self.assertFalse(self.result["human_verified"])
        self.assertFalse(self.result["corpus_wide_accuracy"])

    def test_post_release_gate_is_not_misrepresented_as_held_out(self):
        policies = self.result["navigation_policy"]
        self.assertEqual(
            policies["blind_release_policy"]["counts"][
                "ambiguous_or_not_found_targets"
            ],
            1,
        )
        revised = policies["post_release_safety_gate"]
        self.assertEqual(revised["counts"]["targets"], 9)
        self.assertEqual(revised["counts"]["ambiguous_or_not_found_targets"], 0)
        self.assertEqual(revised["counts"]["correct_paragraph_clear_targets"], 9)
        self.assertEqual(revised["counts"]["exact_span_clear_targets"], 8)
        self.assertFalse(policies["post_release_result_is_held_out"])
        report = (OUTPUT / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("not a new held-out result", report)
        self.assertIn("not exact scan-glyph accuracy", report)


if __name__ == "__main__":
    unittest.main()
