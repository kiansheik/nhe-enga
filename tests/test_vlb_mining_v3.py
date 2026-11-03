"""V3 development regressions from released V1/V2 evidence.

These cases are no longer held out. They protect general construction-level
retrieval and conservative suggestion gates; none is human verification.
"""
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlb"))

from mining.orthography import compile_model, prior_model
from mining.pipeline import CONFIG, Corpus, rank_citation


class ReleasedV2FailureRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = Corpus(ROOT)
        cls.model = compile_model(prior_model())
        cls.cache = {}

    def result(self, page_id, entry_index, citation_start):
        key = (page_id, entry_index, citation_start)
        if key not in self.cache:
            page = self.corpus.page_by_id[page_id]
            citation = next(c for c in page["citations"]
                            if c["entry_index"] == entry_index and
                            c["citation_start"] == citation_start)
            self.cache[key] = rank_citation(self.corpus, page, citation, self.model)
        return self.cache[key]

    def test_version_is_new_and_frozen_v2_artifacts_are_not_rewritten(self):
        self.assertEqual(CONFIG["version"], "vlb-page-ranker-v3")
        self.assertTrue((ROOT / "vlb/mining/output-v2/model-freeze.json").is_file())

    def test_complete_question_fusion_retrieves_baerecepe_but_requires_review(self):
        result = self.result("II-082", 4237, 2909)
        best = result["candidates"][0]
        self.assertEqual(best["source_id"], "vlb-emerson-r568-p05968")
        self.assertEqual(best["attested_span"]["text"], "Baerecepe")
        self.assertEqual(best["query_surface"]["kind"], "quoted_question_fusion_hypothesis")
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("question_fusion_hypothesis_requires_review", result["review_reasons"])

    def test_complete_explicit_expression_beats_its_incomplete_subspan(self):
        result = self.result("I-099", 5202, 2222)
        best = result["candidates"][0]
        self.assertEqual(best["source_id"], "vlb-emerson-r568-p02506")
        self.assertEqual(best["attested_span"]["text"], "Naicoŷ cece coigte")

    def test_complete_repeated_expression_beats_the_bare_occurrence(self):
        result = self.result("II-067", 9680, 619)
        best = result["candidates"][0]
        self.assertEqual(best["source_id"], "vlb-emerson-r568-p05589")
        self.assertEqual(best["attested_span"]["text"], "Uinte çoce")

    def test_spelling_only_match_does_not_override_missing_sense_evidence(self):
        result = self.result("II-062", 11055, 159)
        self.assertEqual(result["candidates"][0]["attested_span"]["text"], "Gigbapecanga")
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("form_only_without_independent_context", result["review_reasons"])

    def test_released_ambiguous_case_remains_unasserted(self):
        result = self.result("I-083", 2435, 178)
        self.assertEqual(result["status"], "needs_review")
        self.assertGreaterEqual(len(result["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
