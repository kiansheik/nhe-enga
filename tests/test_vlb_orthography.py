"""Focused invariants for offline spelling retrieval, not linguistic ground truth."""

import copy
import unittest

from vlb.mining.orthography import align, compile_model, normalize_form, normalize_headword, prior_model, score, train
from vlb.mining.seeds import extract_seeds


class OrthographyTests(unittest.TestCase):
    def test_documented_multigraph_without_global_g_deletion(self):
        result = align("potyra", "Potigra")
        self.assertEqual([(o["modern"], o["historical"]) for o in result["informative_operations"]], [("y", "ig")])
        self.assertLess(result["normalized_cost"], .04)
        self.assertGreater(score("pota", "potga"), .15)

    def test_historical_context_controls_c_and_qu(self):
        self.assertIn("velar-qu", [o.get("rule_id") for o in align("kyrara", "quîrara")["operations"]])
        self.assertNotIn("velar-qu", [o.get("rule_id") for o in align("kara", "quara")["operations"]])
        self.assertIn("sibilant-c", [o.get("rule_id") for o in align("sira", "cira")["operations"]])
        self.assertNotIn("sibilant-c", [o.get("rule_id") for o in align("sara", "cara")["operations"]])
        self.assertNotIn("velar-c", [o.get("rule_id") for o in align("kira", "cira")["operations"]])

    def test_marks_and_apostrophes_remain_evidence(self):
        self.assertEqual(normalize_form("KU’Ã"), "ku'ã")
        self.assertEqual(score("mokana\u0303i", "mokanãi"), 0)
        self.assertGreater(score("mã", "ma"), score("má", "ma"))
        self.assertGreater(score("ku'a", "kua"), 0)
        self.assertEqual(score("", ""), 0)
        self.assertEqual(score("a", ""), 1)

    def test_prefixes_are_supplied_not_free_spelling(self):
        self.assertLess(score("aîmotumung", "Aimotumung"), score("motumung", "Aimotumung"))
        result = align("motumung", "Aimotumung")
        self.assertTrue(any(o["kind"] == "insert" for o in result["operations"]))
        self.assertFalse(any(o.get("rule_id", "").startswith("prefix") for o in result["operations"]))

    def test_learning_excludes_heads_and_pages_before_counts(self):
        def seed(identifier, head, page, modern, historical):
            return {"seed_id": identifier, "citation_id": "c-" + identifier,
                    "source_id": "s-" + identifier, "headword": head, "page_id": page,
                    "modern_form": modern, "vlb_form": historical,
                    "evidence_kind": "synthetic_control_only"}
        seeds = [seed("1", "holdout", "I-001", "xa", "za"),
                 seed("2", "other", "I-099", "xb", "zb"),
                 seed("3", "one", "I-002", "xaba", "zaba"),
                 seed("4", "two", "I-003", "xebe", "zebe"),
                 seed("5", "three", "I-004", "xibi", "zibi"),
                 seed("6", "prefix", "I-005", "motumung", "Aimotumung")]
        frozen = copy.deepcopy(seeds)
        model = train(seeds, {"headwords": ["holdout"], "page_ids": ["I-099"]})
        self.assertEqual(seeds, frozen)
        self.assertEqual(model["training"]["counts"]["excluded_seeds"], 2)
        rules = [r for r in model["rules"] if r["origin"] == "learned_silver"]
        self.assertTrue(any((r["from"], r["to"]) == ("x", "z") for r in rules))
        self.assertTrue(all(r["from"] and r["to"] for r in rules))
        self.assertFalse(any(e["headword"] in {"holdout", "other"} for r in rules for e in r["examples"]))
        self.assertEqual(model, train(list(reversed(seeds)), {"headwords": ["holdout"], "page_ids": ["I-099"]}))

    def test_score_and_trace_agree_and_model_cache_is_separate(self):
        model = compile_model(prior_model())
        pair = ("aîmokanãî", "Aimocanãy")
        self.assertAlmostEqual(model.score(*pair), model.align(*pair)["normalized_cost"], places=7)
        model.score(*pair)
        self.assertGreaterEqual(model.cache_info().hits, 1)
        plain = prior_model()
        plain["rules"] = []
        self.assertGreater(score("potyra", "Potigra", compile_model(plain)), model.score("potyra", "Potigra"))

    def test_inert_observations_are_reported_without_changing_distances(self):
        seeds = [{"seed_id": str(i), "citation_id": "c" + str(i), "source_id": "p" + str(i),
                  "page_id": "I-00" + str(i), "headword": word, "modern_form": word,
                  "vlb_form": word.replace("á", "â"), "evidence_kind": "synthetic_control_only"}
                 for i, word in enumerate(("xába", "xábe", "xábi"), 1)]
        model = train(seeds)
        self.assertEqual(model["training"]["supported_learned_observation_count"], 1)
        self.assertEqual(model["training"]["effective_learned_rule_count"], 0)
        observation = model["training"]["learned_candidates"][0]
        self.assertTrue(observation["supported"])
        self.assertFalse(observation["active"])
        self.assertEqual(observation["inactivity_reason"], "cost_does_not_improve_existing_fallback")
        with_inert = copy.deepcopy(model)
        with_inert["rules"].append(observation)
        for modern, historical in (("xába", "xâba"), ("áá", "ââ"), ("aîxába", "aixâba")):
            self.assertEqual(align(modern, historical, model), align(modern, historical, with_inert))

    def test_exclusion_aliases_and_unicode_variants_apply_before_training(self):
        seeds = [
            {"seed_id": "head", "citation_id": "c1", "source_id": "s1", "page_id": "I-001", "headword": "KU’Ã", "modern_form": "ku'a", "vlb_form": "cua"},
            {"seed_id": "page", "citation_id": "c2", "source_id": "s2", "page_id": "I-002", "headword": "page", "modern_form": "page", "vlb_form": "page"},
            {"seed_id": "source", "citation_id": "c3", "source_id": "continued", "page_id": "I-003", "headword": "source", "modern_form": "source", "vlb_form": "source"},
            {"seed_id": "punctuation", "citation_id": "c4", "source_id": "s4", "page_id": "I-004", "headword": "marã?", "modern_form": "marã", "vlb_form": "marã"},
        ]
        model = train(seeds, {"holdout_headwords": ["ku'a\u0303", "marã"], "holdout_page_ids": ["I-002"], "holdout_source_ids": ["continued"]})
        self.assertEqual(model["training"]["counts"]["excluded_seeds"], 4)
        self.assertEqual(model["training"]["counts"].get("accepted_seeds", 0), 0)
        self.assertEqual(model["training"]["learned_candidates"], [])
        self.assertEqual(normalize_headword("  MARA\u0303?  "), "marã")
        self.assertNotEqual(normalize_headword("ku'ã"), normalize_headword("kuã"))

    def test_seed_offsets_exclusions_and_morphology_labels(self):
        text = "Acender com hũa braza. — Aimojepotar."
        citation = {"id": "c1", "headword": "moîepotar", "context": "(v.tr.) - acender (",
                    "associations": [{"source_id": "p1", "evidence": [{"type": "context_to_Portuguese_head_token_overlap", "tokens": ["acender"]}]}]}
        page = {"id": "I-017", "fragments": [{"id": "p1", "text": text, "source_start0": 100, "source_line": 13}], "citations": [citation]}
        seeds = extract_seeds([page])
        self.assertEqual(len(seeds), 1)
        seed = seeds[0]
        self.assertEqual(seed["modern_form"], "aîmoîepotar")
        self.assertEqual(seed["morphology"]["kind"], "hypothesized_prefix")
        self.assertEqual(text[seed["source_form_start_in_fragment"]:seed["source_form_end_in_fragment"]], seed["vlb_form"])
        self.assertEqual(seed["source_start0"], 100 + seed["source_form_start_in_fragment"])
        self.assertEqual(extract_seeds([page], ["moîepotar"]), [])
        self.assertEqual(extract_seeds([page], [], ["I-017"]), [])
        self.assertEqual(extract_seeds([page], [], [], ["p1"]), [])
        unsegmented = copy.deepcopy(page)
        unsegmented["fragments"][0]["text"] = text.replace("—", ".")
        self.assertEqual(extract_seeds([unsegmented]), [])
        ambiguous = copy.deepcopy(page)
        ambiguous["fragments"].append({"id": "p2", "text": "Outra entrada. — Aimojepotar.", "source_start0": 200})
        self.assertEqual(extract_seeds([ambiguous]), [])
        apostrophe = copy.deepcopy(page)
        apostrophe["citations"][0]["headword"] = "'anga"
        apostrophe["fragments"][0]["text"] = "Abrigada. — 'Anga."
        self.assertEqual(extract_seeds([apostrophe])[0]["vlb_form"], "'Anga")


if __name__ == "__main__":
    unittest.main()
