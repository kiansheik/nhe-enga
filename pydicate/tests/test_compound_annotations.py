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
