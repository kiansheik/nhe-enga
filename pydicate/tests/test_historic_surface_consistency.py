"""Ordinary and annotated surfaces agree for three historic constructions."""

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "pydicate"), str(REPO / "tupi")]

from pydicate.lang.tupilang.pos import (
    Noun,
    ProperNoun,
    Verb,
    abé,
    ae,
    cop,
    ixé,
    oré,
    pûera,
    saba,
    îe,
)


def surface(annotated):
    return re.sub(r"\[[^]]+\]", "", annotated)


class HistoricSurfaceConsistencyTest(unittest.TestCase):
    def assert_ordinary_matches_annotated(self, expression, expected):
        self.assertEqual(expression.eval(), expected)
        self.assertEqual(surface(expression.eval(annotated=True)), expected)

    def test_araujo_bettendorff_20_finite_gerund_applies_phonetics(self):
        expression = oré * Verb("îase'o")
        expression.mood = "gerundio"

        self.assert_ordinary_matches_annotated(expression, "oroîasegûabo")
        self.assertIn("îasegûa[ROOT]", expression.eval(annotated=True))

    def test_araujo_bettendorff_28_nested_proper_noun_is_protected(self):
        title = ProperNoun("Jesus") / ProperNoun("Christo") / abé
        object_phrase = cop() * title * Noun("a'yra")
        expression = +ixé * Verb("erobîar") * object_phrase

        self.assert_ordinary_matches_annotated(
            expression, "arobîar JesusChristoabé ta'yra"
        )

        # The general i-s rewrite still applies outside a proper-name span.
        common_phrase = cop() * Noun("Christo") * Noun("a'yra")
        common_expression = +ixé * Verb("erobîar") * common_phrase
        self.assert_ordinary_matches_annotated(
            common_expression, "arobîar Chrixto ta'yra"
        )

    def test_araujo_55_and_60_classifier_keeps_possessor_boundary(self):
        for root, expected in (
            ("monhang", "i îemonhangagûera"),
            ("upir", "i îeupiragûera"),
        ):
            with self.subTest(root=root):
                expression = pûera * (saba * (ae * Verb(root) * îe))
                self.assert_ordinary_matches_annotated(expression, expected)
                self.assertIn(
                    "i[POSSESSIVE_PRONOUN:3p] îe[SUBJECT:refl]",
                    expression.eval(annotated=True),
                )


if __name__ == "__main__":
    unittest.main()
