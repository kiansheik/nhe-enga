"""Nominalization retains Araújo 73's construction, not a multiword ROOT.

The authored expression combines asé, aûsub and a dropped object before
base_nominal(). Annotation flags must not discard that structure from the
returned predicate; eval() selects its rendering.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "pydicate"), str(REPO / "tupi")]
from pydicate.lang.tupilang.pos import (
    Noun,
    ProperNoun,
    Verb,
    asé,
    ixé,
    îe,
    îo,
    opakatu,
    oré,
    saba,
    sosé,
    tetiruã,
)
from tupi import AnnotatedString, TupiAntigo


class NominalAnnotationPreservationTest(unittest.TestCase):
    def setUp(self):
        self.love = Verb("aûsub", definition="to love")
        self.tell = Verb("mombe'u", verb_class="v.tr.")
        self.things = opakatu + (Noun("mba'e") + tetiruã)

    def nominal_modes(self, expression):
        return (
            expression.base_nominal(),
            expression.base_nominal(False),
            expression.base_nominal(True),
        )

    def assert_surface_and_pieces(self, expression, surface, pieces):
        for nominal in self.nominal_modes(expression):
            with self.subTest(expression=surface, stored=nominal.verbete):
                self.assertEqual(nominal.eval(), surface)
                annotated = nominal.eval(True)
                self.assertEqual(AnnotatedString(annotated).get_clean(), surface)
                for piece in pieces:
                    self.assertIn(piece, annotated)

    def test_araujo73_default_retains_subject_prefix_and_lexical_root(self):
        expression = asé * self.love * +self.things
        self.assert_surface_and_pieces(
            expression,
            "asé saûsuba",
            (
                "asé[ROOT]",
                "[SUBJECT:3p:DIRECT]",
                "s[PLURIFORM_PREFIX:S]",
                "aûsub[ROOT]",
                "a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]",
            ),
        )
        for nominal in self.nominal_modes(expression):
            self.assertNotIn("asé saûsub[ROOT]", nominal.eval(True))
            self.assertEqual(nominal.arguments[1].eval(), "opakatu mba'e tetiruã")
            self.assertTrue(nominal.arguments[1].pro_drop)

    def test_zero_argument_nominal_possessor_and_compound(self):
        self.assert_surface_and_pieces(
            self.love,
            "aûsuba",
            ("aûsub[ROOT]", "[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]"),
        )
        for nominal in self.nominal_modes(self.love):
            possessed = ProperNoun("Tupã") * nominal
            self.assertEqual(possessed.eval(), "Tupã raûsuba")
            self.assertIn("r[PLURIFORM_PREFIX:R]aûsub[ROOT]", possessed.eval(True))
            compound = nominal / Noun("ypy")
            self.assertEqual(compound.eval(), "aûsubypy")
            self.assertIn("aûsub[ROOT]ypy[ROOT]", compound.eval(True))

    def test_one_argument_subject_and_object_are_distinct(self):
        self.assert_surface_and_pieces(
            ixé * Verb("ker", verb_class="v.intr."),
            "xe kera",
            ("xe[SUBJECT:1ps]", "ker[ROOT]"),
        )
        self.assert_surface_and_pieces(
            self.love * Noun("abá"),
            "abáraûsuba",
            ("abá[ROOT]", "[OBJECT:DIRECT]", "r[PLURIFORM_PREFIX:R]", "aûsub[ROOT]"),
        )

    def test_two_overt_arguments_keep_roles(self):
        self.assert_surface_and_pieces(
            asé * self.love * Noun("abá"),
            "asé abáraûsuba",
            ("[SUBJECT:3p:DIRECT]", "[OBJECT:DIRECT]", "aûsub[ROOT]"),
        )

    def test_reflexive_reciprocal_and_short_variants_keep_prefixes(self):
        for pronoun, ordinary, short, tag in (
            (îe, "oîemombe'u", "îemombe'u", "refl"),
            (îo, "oîomombe'u", "îomombe'u", "mut"),
        ):
            expression = pronoun * self.tell
            self.assert_surface_and_pieces(
                expression,
                ordinary,
                ("o[SUBJECT_PREFIX:3p:CORRELATIONAL]", "mombe'u[ROOT]"),
            )
            self.assert_surface_and_pieces(
                expression.var(1), short, (f"[SUBJECT:{tag}]", "mombe'u[ROOT]")
            )

    def test_negative_short_nominal_preserves_negation(self):
        self.assert_surface_and_pieces(
            -(îe * self.tell).var(1),
            "îemombe'ue'yma",
            ("îe[SUBJECT:refl]", "mombe'u[ROOT]", "e'ym[NEGATION_SUFFIX]"),
        )

    def test_non_reflexive_variation_does_not_take_short_prefix(self):
        self.assert_surface_and_pieces(
            (Noun("abá") * self.love).var(1),
            "abáraûsuba",
            ("[OBJECT:DIRECT]", "r[PLURIFORM_PREFIX:R]", "aûsub[ROOT]"),
        )

    def test_common_noun_phonetics_contrasts_with_proper_noun(self):
        expression = Noun("missa") * Verb("endub")
        for nominal in (expression.base_nominal(), expression.base_nominal(False)):
            self.assertEqual(nominal.eval(), "mixsarenduba")
            self.assertIn("mixs[ROOT]", nominal.eval(True))
            self.assertIn("[OBJECT:DIRECT]", nominal.eval(True))
        # Explicit True historically retains pre-normalization spelling.
        self.assertEqual(expression.base_nominal(True).eval(), "missarenduba")
        self.assert_surface_and_pieces(
            ProperNoun("missa") * Verb("endub"),
            "missarenduba",
            ("missa[PROPER_NOUN]", "[OBJECT:DIRECT]", "endub[ROOT]"),
        )

    def test_explicit_annotation_mode_retains_legacy_stem_spelling(self):
        expression = îe * Verb("erobîar", verb_class="v.tr.")
        # Araújo and Bettendorff 18 use this base inside a derivation with an
        # explicit True path. Preserve îeer- there; this patch does not decide
        # between that spelling and the existing plain-mode îer- contraction.
        ordinary = expression.base_nominal()
        explicit = expression.base_nominal(True)
        self.assertEqual(ordinary.eval(), "oîerobîara")
        self.assertEqual(explicit.eval(), "oîeerobîara")
        self.assertFalse(ordinary._nominalization_annotated_argument)
        self.assertTrue(explicit._nominalization_annotated_argument)
        self.assertIn("îe[OBJECT:REFLEXIVE]", ordinary.eval(True))
        self.assertIn("robîar[ROOT]", ordinary.eval(True))
        self.assertIn("erobîar[ROOT]", explicit.eval(True))

    def test_derived_reflexive_nominal_keeps_both_historic_record18_spellings(self):
        # The same attested construction appears in Araújo 18 and Bettendorff
        # 18. saba's explicit annotated nominal path must not contract îeer-.
        expression = saba * (oré * Verb("erobîar") * îe)
        self.assertEqual(expression.eval(), "oré îeerobîasaba")
        self.assertIn("îe[OBJECT:REFLEXIVE]", expression.eval(True))

    def test_existing_phonetic_rules_preserve_all_tags_and_boundaries(self):
        phonetics = TupiAntigo()
        cases = (
            ("i[A]s[B]", "i[A]x[B]"),
            ("i[A] s[B]", "i[A] x[B]"),
            ("n[A]n[B]", "n[A][B]"),
            ("o[A]er[B]", "o[A]gûer[B]"),
            ("o[A]en[B]", "o[A]gûen[B]"),
            ("îe[A]er[B]", "îe[A]r[B]"),
            ("î[A]î[B]", "î[A][B]"),
            ("a[A]  b[B]", "a[A] b[B]"),
            ("a[A]-[JOIN]b[B]", "a[A][JOIN]b[B]"),
            ("'[A]û[B]", "g[A]û[B]"),
            (" [BEFORE] a[A] [AFTER]", "[BEFORE]a[A][AFTER]"),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                got = phonetics.fix_phonetics_annotated(source)
                self.assertEqual(got, expected)
                self.assertEqual(
                    AnnotatedString(got).get_clean(),
                    phonetics.fix_phonetics_preserving_tags(source, set()),
                )
        protected = "missa[PROPER_NOUN][OBJECT] i[A]s[B]"
        result = phonetics.fix_phonetics_annotated(protected, {"PROPER_NOUN"})
        self.assertEqual(result, "missa[PROPER_NOUN][OBJECT] i[A]x[B]")
        self.assertEqual(
            AnnotatedString(result).get_clean(),
            phonetics.fix_phonetics_preserving_tags(protected, {"PROPER_NOUN"}),
        )

    def test_proper_name_protection_spans_adjacent_annotation_groups(self):
        phonetics = TupiAntigo()
        source = "missa[ROOT][PROPER_NOUN][OBJECT:DIRECT] i[ROOT]s[SUFFIX]"
        self.assertEqual(
            phonetics.fix_phonetics_annotated(source, {"PROPER_NOUN"}),
            "missa[ROOT][PROPER_NOUN][OBJECT:DIRECT] i[ROOT]x[SUFFIX]",
        )

    def test_proper_name_protection_recognizes_composite_annotation_group(self):
        phonetics = TupiAntigo()
        source = "missa[PROPER_NOUN:OBJECT:DIRECT] i[ROOT]s[SUFFIX]"
        self.assertEqual(
            phonetics.fix_phonetics_annotated(source, {"PROPER_NOUN"}),
            "missa[PROPER_NOUN:OBJECT:DIRECT] i[ROOT]x[SUFFIX]",
        )

    def test_source_tree_is_an_independent_nominalization_snapshot(self):
        for expression in (
            self.love,
            asé * self.love * +self.things,
            (îe * self.tell).var(1),
            -(îe * self.tell).var(1),
        ):
            nominal = expression.base_nominal()
            self.assertEqual(nominal._nominalization_operation, "base_nominal")
            source = nominal._nominalization_source
            self.assertIsNot(source, expression)
            self.assertEqual(source.category, expression.category)
            self.assertEqual(source.variation_id, expression.variation_id)
            self.assertEqual(source.negated, expression.negated)
            self.assertEqual(source.verb.transitivo, expression.verb.transitivo)
            self.assertEqual(source.eval(True), expression.eval(True))
            self.assertEqual(len(source.arguments), len(expression.arguments))
            if source.arguments:
                self.assertIsNot(source.arguments[0], expression.arguments[0])

    def test_full_araujo73_surface_is_unchanged(self):
        for first in self.nominal_modes(asé * self.love * +self.things):
            expression = (
                self.things
                + (first * sosé)
                + (asé * (ProperNoun("Tupã") * self.love.base_nominal()))
            )
            self.assertEqual(
                expression.eval(),
                "opakatu mba'e tetiruã asé saûsuba sosé asé Tupã raûsuba",
            )
            self.assertNotIn("asé saûsub[ROOT]", expression.eval(True))


if __name__ == "__main__":
    unittest.main()
