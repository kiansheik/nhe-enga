"""Regression checks for citation evidence, source offsets and abstention.

Examples are development cases already inspected while building the reader.
They are deliberately excluded from the independent accuracy benchmark.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlb"))
from mining.orthography import compile_model, prior_model
from mining.pipeline import (Corpus, fragment_features, make_surfaces,
                             ocr_target, quote_support, rank_citation)


class MiningPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = Corpus(ROOT)
        cls.model = compile_model(prior_model())

    def citation(self, page_id, row, position=None):
        page = self.corpus.page_by_id[page_id]
        citation = next(c for c in page["citations"] if c["entry_index"] == row and
                        (position is None or c["citation_start"] == position))
        return page, citation

    def test_ig_multigraph_finds_actual_span(self):
        page, citation = self.citation("I-017", 9082)
        result = rank_citation(self.corpus, page, citation, self.model)
        target = result["candidates"][0]
        self.assertEqual(target["source_id"], "vlb-emerson-r568-p00022")
        self.assertEqual(target["attested_span"]["text"], "Potigra")
        self.assertIn("central-vowel-ig", [o.get("rule_id") for o in target["orthographic_alignment"]["operations"]])
        self.assertEqual(target["review_status"], "unreviewed")
        self.assertFalse(result["status_is_editorial_verification"])

    def test_target_word_does_not_supply_its_own_context(self):
        page, citation = self.citation("I-017", 7210)
        result = rank_citation(self.corpus, page, citation, self.model)
        target = result["candidates"][0]
        self.assertEqual(target["source_id"], "vlb-emerson-r568-p00013")
        self.assertEqual(target["quotation_context_score"], 0)
        self.assertTrue(target["quoted_surface_evidence"])
        self.assertEqual(result["existing_reviewed_source_ids"], [target["source_id"]])

    def test_fuller_quote_conflict_cannot_auto_suggest_other_sense(self):
        page, citation = self.citation("I-018", 2778, 285)
        result = rank_citation(self.corpus, page, citation, self.model)
        # A generic Xe akyrar form in paragraph 45 describes the abortion being
        # born; Navarro quotes the mother's fuller Xe membyrakyrar expression.
        if result["candidates"][0]["source_id"] != "vlb-emerson-r568-p00044":
            self.assertNotEqual(result["status"], "suggested")
            self.assertIn("explicit_quoted_surface_not_matched", result["review_reasons"])

    def test_every_dictionary_supplied_surface_keeps_literal_offsets(self):
        for page in self.corpus.pages:
            for citation in page["citations"]:
                definition = self.corpus.dictionary[citation["entry_index"]]["d"]
                surfaces, quotes = make_surfaces(citation, definition)
                for surface in surfaces:
                    if "definition_start" in surface:
                        self.assertEqual(definition[surface["definition_start"]:surface["definition_end"]], surface["form"])
                    for occurrence in surface.get("quotation_occurrences", []):
                        self.assertEqual(citation["context"][occurrence["context_start"]:occurrence["context_end"]], occurrence["text"])
                for quote in quotes:
                    self.assertEqual(citation["context"][quote["context_start"]:quote["context_end"]], quote["text"])

    def test_cross_references_and_multiword_stopwords_are_not_tupi_tags(self):
        for value, expected in [("Largo. — uide. Liberal.", "cross_reference"),
                                ("Todos. — para todos", "post_separator_text")]:
            fragment = {"text": value, "source_start0": 0}
            feature = fragment_features(fragment, {"text": value, "start": 0})
            self.assertTrue(feature.spans)
            self.assertTrue(all(s["role"] == expected for s in feature.spans))
            if expected == "post_separator_text":
                self.assertTrue(all(s["common_portuguese_or_grammar_token"] for s in feature.spans))

    def test_ocr_does_not_join_across_skipped_lines(self):
        page = {"ocr_lines": [{"id": str(i), "text": text, "box": [0, 0, 1, 1]}
                              for i, text in enumerate(["Aimo", "unrelated passage", "tumung"])]}
        fragment = {"ocr": {"line_ids": ["0", "2"]}}
        self.assertEqual(ocr_target(page, fragment, "Aimotumung")["status"], "paragraph_only")
        page["ocr_lines"] = [page["ocr_lines"][0], page["ocr_lines"][2]]
        self.assertEqual(ocr_target(page, fragment, "Aimotumung")["status"], "form_token_match")

    def test_ocr_multiple_occurrences_are_not_claimed_unique_glyphs(self):
        page = {"ocr_lines": [{"id": "one", "text": "Potigra Potigra", "box": [0, 0, 1, 1]}]}
        target = ocr_target(page, {"ocr": {"line_ids": ["one"]}}, "Potigra")
        self.assertEqual(target["matching_token_runs"], 2)
        self.assertFalse(target["is_exact_glyph_box"])
        self.assertFalse(target["match_is_editorial_verification"])


if __name__ == "__main__":
    unittest.main()
