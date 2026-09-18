"""Noun/verb incorporation; attested in Araujo Catecismo 1686, record 81."""

import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "pydicate"), str(REPO / "tupi")]

from pydicate.lang.tupilang.pos import Noun, Verb


class IncorporatedObjectVerbTest(unittest.TestCase):
    def test_m_class_and_valency_variation(self):
        portion = Noun("potaba", "(m) portion")
        give = Verb("me'eng", verb_class="v.tr.")
        god = Noun("Tupã")
        compound = portion / give

        self.assertFalse(compound.verb.transitivo)
        self.assertEqual(compound.base_nominal().eval(), "motame'enga")
        self.assertIn(
            "m[PLURIFORM_PREFIX:M:ABSOLUTE]", compound.base_nominal().eval(True)
        )
        self.assertEqual(
            (compound.var(1) * god).base_nominal().eval(), "Tupã potame'enga"
        )
        self.assertIn(
            "p[PLURIFORM_PREFIX:P]", (compound.var(1) * god).base_nominal().eval(True)
        )
        self.assertIn("[INCORPORATED_OBJECT]", compound.base_nominal().eval(True))

    def test_ordinary_composition_and_direct_object_stay_distinct(self):
        portion = Noun("potaba", "(m) portion")
        give = Verb("me'eng", verb_class="v.tr.")
        self.assertEqual((portion / Noun("ypy")).eval(), "motabypy")
        self.assertEqual((portion * give).eval(), "motaba oîme'eng")

    def test_direct_verb_argument_roles(self):
        # kó is a test noun here, not the corpus's demonstrative kó.
        field = Noun("kó", definition="field")
        give = Verb("me'eng", verb_class="v.tr.")
        actor = Noun("ixé", inflection="1ps")
        owner = Noun("Pedro")
        generic = (field / give) * actor
        possessed = (field / give).var(1) * actor * owner

        self.assertIsNone(generic.object())
        self.assertEqual(generic.subject().verbete, "ixé")
        self.assertEqual(possessed.subject().verbete, "ixé")
        self.assertEqual(possessed.object().verbete, "Pedro")
        self.assertIn("[OBJECT:INCORPORATED:GENERIC]", generic.eval(True))
        self.assertIn(
            "[OBJECT:DIRECT:INCORPORATED_NOUN_POSSESSOR]", possessed.eval(True)
        )


if __name__ == "__main__":
    unittest.main()
