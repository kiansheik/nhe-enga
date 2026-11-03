import hashlib
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VLB = ROOT / "vlb"

import sys
sys.path.insert(0, str(VLB))

from mining.pipeline import read_json, write_json


class VlbReverseConcordanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = VLB / "mining/reverse-output"
        cls.inventory = read_json(cls.output / "source-dictionary-concordance.json.gz")
        cls.summary = read_json(cls.output / "summary.json")
        cls.source = (VLB / "source/emerson_vlb.txt").read_text(encoding="utf-8")
        cls.dictionary = read_json(ROOT / "docs/dict-conjugated.json.gz")

    def test_all_source_records_are_retained_without_paragraph_coverage_claims(self):
        records = self.inventory["records"]
        self.assertEqual(7534, len(records))
        self.assertEqual(7534, len({record["source_id"] for record in records}))
        source_lines = [record["source_line"] for record in records]
        self.assertEqual(source_lines, sorted(source_lines))
        self.assertEqual(7534, len(set(source_lines)))
        self.assertEqual(3, source_lines[0])
        self.assertEqual(7678, source_lines[-1])
        self.assertEqual(0, self.inventory["counts"]["fully_covered_records"])
        self.assertTrue(all(not record["coverage"]["fully_covered"] for record in records))
        self.assertEqual(
            7534,
            sum(self.inventory["counts"]["status"].values()),
        )

    def test_source_and_candidate_spans_are_exact_and_page_bounded(self):
        for record in self.inventory["records"]:
            self.assertEqual(
                record["text"],
                self.source[record["source_start0"]:record["source_end0"]],
            )
            for candidate in record["candidates"]:
                row = self.dictionary[candidate["entry_index"]]
                self.assertEqual(row["f"], candidate["headword"])
                for evidence in candidate["evidence"]:
                    span = evidence.get("source_span")
                    if span is None:
                        continue
                    self.assertIn(span["page_id"], record["page_ids"])
                    self.assertEqual(
                        span["text"], self.source[span["start0"]:span["end0"]]
                    )
                    self.assertGreaterEqual(span["start0"], record["source_start0"])
                    self.assertLessEqual(span["end0"], record["source_end0"])

    def test_reviewed_mokanai_link_is_retained_but_not_full_coverage(self):
        record = next(row for row in self.inventory["records"]
                      if row["source_id"] == "vlb-emerson-r568-p00013")
        candidate = next(row for row in record["candidates"]
                         if row["entry_index"] == 7210)
        self.assertEqual("reviewed", candidate["review_status"])
        self.assertTrue(any(
            evidence.get("source_span", {}).get("text") == "Aimocanãy"
            for evidence in candidate["evidence"]
        ))
        self.assertEqual("partially_reviewed", record["review_status"])
        self.assertFalse(record["coverage"]["fully_covered"])

    def test_checked_artifact_names_the_current_algorithm_inputs(self):
        provenance = self.inventory["provenance"]
        for field, path in {
            "reverse_concordance_code_sha256": VLB / "mining/reverse_concordance.py",
            "shared_pipeline_code_sha256": VLB / "mining/pipeline.py",
            "orthography_code_sha256": VLB / "mining/orthography.py",
        }.items():
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), provenance[field]
            )

    def test_checked_artifact_has_deterministic_serialization(self):
        with tempfile.TemporaryDirectory() as directory:
            checked_artifact = self.output / "source-dictionary-concordance.json.gz"
            rebuilt_artifact = Path(directory) / checked_artifact.name
            write_json(rebuilt_artifact, self.inventory)
            self.assertEqual(
                hashlib.sha256(checked_artifact.read_bytes()).hexdigest(),
                hashlib.sha256(rebuilt_artifact.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                self.summary["artifact_sha256"],
                hashlib.sha256(rebuilt_artifact.read_bytes()).hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
