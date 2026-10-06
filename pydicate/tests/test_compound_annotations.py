"""Composition preserves lexical metadata without changing realization.

Historic attestation: oldtupicorpus/historic/araujo_catecismo_1686.tu.py,
record 81. Its existing regression expects the compound oemitymbûerypy;
this regression restores only the already declared ypy root annotation.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "pydicate"), str(REPO / "tupi")]

from pydicate import Predicate
from pydicate.lang.tupilang.pos import Noun, Verb, emi, og, pûera, nde
from tupi import Noun as TupiNoun

tym = Verb("tym")
ypy = Noun("ypy", definition="início, primeiro, começar, começo")
apixara = Noun("apixara", "(t)")


class CompoundAnnotationTest(unittest.TestCase):
    def test_explicit_nasal_mo_causative(self):
        from pydicate.lang.tupilang.pos.verb import mo

        root = Verb("pytá")
        before = root.eval(annotated=True)
        result = mo.var(2) * root
        self.assertEqual(result.eval(), "mombytá")
        self.assertEqual(result.eval(annotated=True), "mo[CAUSATIVE_PREFIX:MO]mbytá")
        self.assertTrue(result.verb.transitivo)
        self.assertIsNotNone(result._augmentee)
        self.assertEqual(result._augmentee.eval(), "pytá")
        self.assertEqual(result._augmentor.variation_id, 2)
        self.assertEqual(root.eval(annotated=True), before)
        self.assertEqual((mo * root).eval(), "mopytá")
        self.assertEqual((mo.var(1) * root).eval(), "mbopytá")
        self.assertEqual(mo.var(2).eval(), "mo")
        self.assertEqual((mo.var(2) / root).eval(), "mopytá")

    def test_nasal_causative_onsets_and_annotation(self):
        from pydicate.lang.tupilang.pos.verb import mo

        for stem, expected in (
            ("só", "mondó"),
            ("katú", "mongatú"),
            ("tá", "mondá"),
            ("tym", "motym"),
            ("abá", "moabá"),
            ("pytá[ROOT]", "mombytá"),
        ):
            with self.subTest(stem=stem):
                root = Verb(stem)
                self.assertEqual((mo.var(2) * root).eval(), expected)
                self.assertEqual(root.verbete, stem)
        self.assertIn("mbytá[ROOT]", (mo.var(2) * Verb("pytá[ROOT]")).eval(True))
        # The next * fills a verbal argument; it must not apply sandhi again.
        nasal = mo.var(2) * Verb("pytá")
        ordinary = mo * Verb("pytá")
        self.assertEqual(
            (nasal * nde).eval(), (ordinary * nde).eval().replace("pytá", "mbytá")
        )
        self.assertEqual((mo * nasal).eval(), "momombytá")

    def test_compound_preserves_semivowels_before_consonants(self):
        # Pending Araujo 110: Uceibôra moyú; requested îb, not b.
        # Synthetic stems below test the rule, not historic attestations.
        for glide in ("î", "û", "ŷ", "gû"):
            stem = "ka" + glide
            with self.subTest(glide=glide):
                compound = Noun(stem) / Noun("bor")
                self.assertEqual(compound.eval(), stem + "bora")
                self.assertIn(stem + "[ROOT]", compound.eval(True))
        compound = (Verb("'u") / Verb("seî")).base_nominal() / Noun("bor")
        self.assertEqual(compound.eval(), "'useîbora")

    def test_compound_non_semivowel_contrasts(self):
        self.assertEqual((Noun("pak") / Noun("bor")).eval(), "pabora")
        self.assertEqual((Noun("pã") / Noun("bor")).eval(), "pãbora")
        self.assertEqual((Noun("kaî") / Noun("eté")).eval(), "kaîeté")

    def test_classifier_compound_keeps_modifier_root(self):
        e = (pûera * (og * (emi * tym))) / ypy
        self.assertEqual(e.eval(), "oemitymbûerypy")
        self.assertEqual(
            e.eval(True),
            "o[PRONOUN:MAIN_CLAUSE_SUBJECT:3p]emi[PATIENT_PREFIX]tym[ROOT]bûer[PRETERITE_SUFFIX]ypy[ROOT][CLASSIFIER:PAST]",
        )
        self.assertEqual(e.eval(True).count("ypy[ROOT]"), 1)

    def test_deverbal_compound_keeps_modifier_root(self):
        e = (og * (emi * tym)) / ypy
        self.assertEqual(e.eval(), "oemitymypy")
        self.assertEqual(
            e.eval(True),
            "o[PRONOUN:MAIN_CLAUSE_SUBJECT:3p]emi[PATIENT_PREFIX]tym[ROOT]ypy[ROOT]",
        )

    def test_possession_and_past_without_compound_are_unchanged(self):
        self.assertEqual((emi * tym).eval(), "temityma")
        self.assertEqual((nde * (emi * tym)).eval(), "nde remityma")
        self.assertEqual((og * (emi * tym)).eval(), "oemityma")
        self.assertEqual((pûera * (og * (emi * tym))).eval(), "oemitymbûera")
        self.assertEqual((nde * apixara).eval(), "nde rapixara")

    def test_low_level_already_preserves_root_metadata(self):
        e = TupiNoun(
            "tym[ROOT]bûer[PRETERITE_SUFFIX]a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]",
            "",
            noroot=True,
        ).compose(TupiNoun("ypy[ROOT]", "", noroot=True))
        self.assertEqual(e.verbete(True), "tym[ROOT]bûer[PRETERITE_SUFFIX]ypy[ROOT]")
        self.assertEqual(e.verbete(), "tymbûerypy")

    def test_plain_noun_compound_keeps_both_declared_roots(self):
        # Araújo and Bettendorff record 22 explicitly encode
        # nde * (esá / poraûsubara). Composition must preserve that boundary.
        compound = Noun("esá") / Noun("poraûsubara")
        possessed = nde * compound
        self.assertEqual(possessed.eval(), "nde resaporaûsubara")
        self.assertEqual(
            possessed.eval(True),
            "nde[POSSESSIVE_PRONOUN:2ps] "
            "r[PLURIFORM_PREFIX:R]"
            "esa[ROOT]poraûsubar[ROOT]"
            "a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING][NOUN]",
        )

    def test_plain_noun_compound_does_not_invent_an_opted_out_left_root(self):
        compound = Noun("esá", noroot=True) / Noun("poraûsubara")
        possessed = nde * compound
        self.assertEqual(possessed.eval(), "nde resaporaûsubara")
        self.assertNotIn("esa[ROOT]", possessed.eval(True))
        self.assertIn("poraûsubar[ROOT]", possessed.eval(True))

    def test_uncertain_or_already_tagged_modifiers_are_not_reannotated(self):
        values = [
            Noun("ypy", noroot=True),
            Noun("ypy[ROOT]"),
            Noun("ypy[ROOT][ROOT]"),
            Noun("ypy abá"),
            Noun("ypy") / Noun("eté"),
            Noun(""),
        ]
        for value in values:
            with self.subTest(surface=value.verbete):
                self.assertEqual(Predicate._compose_modifier_base(value), value.verbete)
        self.assertEqual(Predicate._compose_modifier_base(Noun("ypy")), "ypy[ROOT]")
        self.assertEqual(Predicate._compose_modifier_base(Noun("oka")), "ok[ROOT]")


if __name__ == "__main__":
    unittest.main()
