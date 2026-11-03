"""Released V1 failures are V2 development regressions, never a new test set."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlb"))
from mining.orthography import compile_model, prior_model
from mining.pipeline import Corpus, evaluate, make_surfaces, rank_citation
from mining.quotation import parse_quotations


class QuoteStructureTest(unittest.TestCase):
    def test_parenthesized_and_slash_alternatives_keep_literal_offsets(self):
        for text, expected in [("(s.) - noite; Pytũ 'ã (ou Pytun iã). - Eis que é noite.",
                                ["Pytũ 'ã", "Pytun iã"]),
                               ("(s.) - exemplo: Forma longa / Outra forma. - tradução.",
                                ["Forma longa", "Outra forma"])]:
            parsed = parse_quotations(text)
            self.assertEqual([q["text"] for q in parsed["quotes"]], expected)
            for quote in parsed["quotes"]:
                self.assertEqual(text[quote["context_start"]:quote["context_end"]], quote["text"])

    def test_optional_argument_keeps_following_postposition(self):
        text = "); Xe resaraî (mba'e) suí. - Eu me esqueci de algo. ("
        parsed = parse_quotations(text)
        quote = parsed["quotes"][0]
        self.assertEqual(quote["text"], "Xe resaraî (mba'e) suí")
        self.assertEqual([text[a:b] for a, b in quote["optional_intervals"]], ["(mba'e)"])

    def test_unassembled_alternative_tail_requires_review(self):
        parsed = parse_quotations("(s.) - item: Forma (ou alternativa) supé. - tradução.")
        self.assertEqual(parsed["status"], "partial")
        self.assertIn("alternative_shared_tail_requires_review", [x["reason"] for x in parsed["issues"]])

    def test_unclosed_example_cannot_disappear_without_a_parse_issue(self):
        parsed = parse_quotations("(v.tr.) - desejar: Aîpotar (mba'e - desejo algo.")
        self.assertEqual(parsed["status"], "partial")
        self.assertIn("nested_or_unclosed_example_separator", [x["reason"] for x in parsed["issues"]])

    def test_long_explicit_compound_is_not_limited_by_lemma_length(self):
        citation = {"headword": "pó", "context": "); pó-piranga-pukusamoîna. - exemplo."}
        surfaces, _ = make_surfaces(citation, "(s.) - item")
        self.assertIn("pó-piranga-pukusamoîna", [s["form"] for s in surfaces])


class ReleasedFailureRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = Corpus(ROOT)
        cls.model = compile_model(prior_model())
        cls.results = {}

    def result(self, page_id, row, position):
        key = (page_id, row, position)
        if key not in self.results:
            page = self.corpus.page_by_id[page_id]
            citation = next(c for c in page["citations"] if c["entry_index"] == row and
                            c["citation_start"] == position)
            self.results[key] = rank_citation(self.corpus, page, citation, self.model)
        return self.results[key]

    def test_full_quoted_predicate_beats_standalone_exact_lemma(self):
        result = self.result("II-050", 9199, 955)
        self.assertEqual(result["candidates"][0]["source_id"], "vlb-emerson-r568-p05224")
        self.assertIn(result["candidates"][0]["attested_span"]["text"], ["Pigtuã", "Pigtuniã"])

    def test_explicit_long_compound_beats_bare_verb(self):
        result = self.result("II-033", 5490, 304)
        self.assertEqual(result["candidates"][0]["source_id"], "vlb-emerson-r568-p04778")
        self.assertEqual(result["candidates"][0]["attested_span"]["text"], "Ajucamatutenhe")

    def test_postposition_disambiguates_neighbouring_construction(self):
        result = self.result("I-127", 4230, 221)
        best = result["candidates"][0]
        self.assertEqual(best["source_id"], "vlb-emerson-r568-p03340")
        self.assertIn("çuî", [m["historical_token"] for m in best["local_quotation_matches"]])

    def test_tiny_head_does_not_highlight_portuguese_article(self):
        result = self.result("I-137", 2314, 265)
        best = result["candidates"][0]
        self.assertEqual(best["source_id"], "vlb-emerson-r568-p03612")
        self.assertEqual(best["attested_span"]["text"], "Apixapaba")

    def test_cited_nominal_compound_is_offered(self):
        result = self.result("I-062", 9662, 866)
        self.assertEqual(result["candidates"][0]["source_id"], "vlb-emerson-r568-p01349")
        self.assertEqual(result["candidates"][0]["attested_span"]["text"], "Xeçoocuguab")

    def test_repeated_form_offers_citation_specific_later_occurrence(self):
        result = self.result("II-067", 9680, 619)
        self.assertEqual(result["candidates"][0]["source_id"], "vlb-emerson-r568-p05589")
        options = [result["candidates"][0], *result["candidates"][0]["span_alternatives"]]
        self.assertIn("Uinte çoce", [c["attested_span"]["text"] for c in options])
        best_span = result["candidates"][0]["attested_span"]
        self.assertGreater(best_span["start0"], 325034)

    def test_all_saved_alternatives_have_exact_source_spans_and_no_review_claim(self):
        for page, row, position in [("II-050", 9199, 955), ("II-067", 9680, 619)]:
            result = self.result(page, row, position)
            self.assertFalse(result["status_is_editorial_verification"])
            self.assertEqual(len({c["source_id"] for c in result["candidates"]}), len(result["candidates"]))
            for candidate in result["candidates"]:
                self.assertLessEqual(len(candidate["span_alternatives"]), 3)
                for option in [candidate, *candidate["span_alternatives"]]:
                    span = option["attested_span"]
                    self.assertEqual(self.corpus.text[span["start0"]:span["end0"]], span["text"])
                    self.assertEqual(option["review_status"], "unreviewed")
                    self.assertFalse(option["ocr_target"].get("is_exact_glyph_box", False))
                    if option is not candidate:
                        self.assertNotIn("span_alternatives", option)

    def test_evaluator_counts_alternative_span_separately_from_legacy_top_three(self):
        label = {"cases": [{"case_id": "synthetic", "citation_id": "c", "page_id": "p",
                            "source_ids": ["s"], "status": "clear", "headword": "test",
                            "targets": [{"source_id": "s", "form_start0": 5, "form_end0": 9}]}]}
        candidate = {"source_id": "s", "attested_span": {"start0": 1, "end0": 4},
                     "span_alternatives": [{"source_id": "s", "attested_span": {"start0": 5, "end0": 9}}]}
        result = evaluate(label, {("c", "p"): {"candidates": [candidate], "status": "needs_review"}}, {})
        self.assertEqual(result["counts"]["top1_correct"], 1)
        self.assertEqual(result["counts"]["top1_exact_attested_span"], 0)
        self.assertEqual(result["counts"]["top3_exact_attested_span"], 0)
        self.assertEqual(result["counts"]["offered_exact_attested_span"], 1)


if __name__ == "__main__":
    unittest.main()
