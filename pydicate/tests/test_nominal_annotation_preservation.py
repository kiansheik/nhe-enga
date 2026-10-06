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


class QuantifiedNominalArgumentTest(unittest.TestCase):
    def test_deadverbal_phrase_is_a_third_person_subject(self):
        # Pending Araújo draft: implementation of the contributor's analysis,
        # not an independently approved historical reference.
        from pydicate.lang.tupilang.pos import Number, Particle, nduara, esé

        number = Number("sete")
        derived = nduara * (
            esé * (Noun("abá") * Noun("eté", definition="(t) (s.) corpo"))
        )
        phrase = number * derived
        say = Verb("'i")
        result = Particle("nã") >> (phrase * say)
        self.assertEqual(result.eval(), "sete abá reté reséndûara nã e'i")
        self.assertEqual(AnnotatedString(result.eval(True)).get_clean(), result.eval())
        self.assertEqual(result.subject().inflection(), "3p")
        self.assertEqual(result.subject().arguments[0].category, "deadverbal_noun")
        self.assertEqual(phrase.eval(), "sete abá reté reséndûara")
        self.assertEqual(len(phrase.arguments), 1)
        self.assertEqual(len(number.arguments), 0)
        self.assertEqual(len(say.arguments), 0)
        self.assertEqual(
            (Particle("nã") >> (derived * say)).eval(), "abá reté reséndûara nã e'i"
        )

    def test_ordinary_nominal_and_transitive_object_contrast(self):
        from pydicate.lang.tupilang.pos import Number

        number = Number("sete")
        phrase = number * Noun("abá")
        self.assertEqual((phrase * Verb("'i")).eval(), "sete abá e'i")
        result = phrase * Verb("aûsub")
        self.assertEqual(result.eval(), "sete abá osaûsub")
        self.assertEqual(result.object().eval(), "sete abá")
        self.assertIsNone(result.subject())
        self.assertEqual(number.eval(), "sete")
        with self.assertRaises(ValueError):
            phrase * Noun("kunhã")


class IrregularAgentNominalTest(unittest.TestCase):
    def test_sara_attachment_explicit_atara_and_nominal_object(self):
        # Pending Araújo "Atâra mombytá.": requested analysis, not approval.
        from pydicate.lang.tupilang.pos import sara, mo

        verb = Verb("gûatá", verb_class="(v. intr.)", definition="andar")
        regular = sara * verb
        varied = regular.var(1)
        self.assertEqual(regular.eval(), "gûatasara")
        self.assertEqual(varied.eval(), "atara")
        self.assertEqual(
            varied.eval(True),
            "at[ROOT]ar[ABSOLUTE_AGENT_SUFFIX]"
            "a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]",
        )
        self.assertEqual(varied.var(0).eval(), "gûatasara")
        self.assertEqual(verb.eval(), "gûatá")
        self.assertEqual(varied.arguments[0].definition, "andar")
        self.assertEqual(
            (sara * Verb("îeruré", verb_class="(v. intr.)")).var(1).eval(), "îeruresara"
        )
        result = (
            varied * (mo.var(2) * Verb("pytá", verb_class="(v. intr.)"))
        ).base_nominal()
        self.assertEqual(result.eval(), "ataramombytá")
        self.assertIn("at[ROOT]ar[ABSOLUTE_AGENT_SUFFIX]", result.eval(True))

    def test_explicit_atara_variant_and_contrasts(self):
        # Studio pending Araújo draft, 2026-09-30: contributor's proposal,
        # not an independently established historical attestation.
        from pydicate.lang.tupilang.pos import sara

        verb = Verb("gûatá", verb_class="(v. intr.)", definition="andar")
        nominal = (verb / sara).base_nominal()
        varied = nominal.var(1)
        self.assertEqual(nominal.eval(), "gûatasara")
        self.assertEqual(varied.eval(), "atara")
        self.assertEqual(AnnotatedString(varied.eval(True)).get_clean(), "atara")
        self.assertEqual(varied.var(0).eval(), "gûatasara")
        self.assertEqual(varied.definition, nominal.definition)
        self.assertEqual(
            varied._nominalization_source.eval(), nominal._nominalization_source.eval()
        )
        self.assertEqual(verb.base_nominal().var(1).eval(), "gûatá")
        self.assertEqual(
            (Verb("îeruré", verb_class="(v. intr.)") / sara)
            .base_nominal()
            .var(1)
            .eval(),
            "îeruresara",
        )
        self.assertEqual(Noun("gûatasara").var(1).eval(), "gûatasara")


class EmiAbsoluteVariantTest(unittest.TestCase):
    def test_absolute_variant_and_context_contrasts(self):
        # Pending Araújo "Imomĩauçubipyra renocêma.": contributor's
        # requested analysis, not an independently approved reference.
        from pydicate.lang.tupilang.pos import emi, mo, pyra, nde, og

        love = Verb("aûsub", definition="to love")
        regular = emi * love
        varied = regular.var(1)
        self.assertEqual(regular.eval(), "temiaûsuba")
        self.assertEqual(varied.eval(), "miaûsuba")
        self.assertEqual(AnnotatedString(varied.eval(True)).get_clean(), "miaûsuba")
        self.assertIn("mi[PATIENT_PREFIX]", varied.eval(True))
        self.assertEqual(varied.var(0).eval(), regular.eval())
        self.assertEqual(varied.arguments[0].definition, love.definition)
        for possessor in (nde, og):
            self.assertEqual((possessor * varied).eval(), (possessor * regular).eval())
        self.assertEqual((pyra * love).var(1).eval(), (pyra * love).eval())
        result = (Verb("enosem") * (pyra * (varied * mo))).base_nominal()
        self.assertEqual(result.eval(), "imomiaûsupyrarenosema")
        self.assertEqual(AnnotatedString(result.eval(True)).get_clean(), result.eval())


class NominalPastAbsoluteTest(unittest.TestCase):
    def test_absolute_and_relational_past(self):
        # Pending Araújo "Tëõboêra tyma.": contributor's analysis, not approval.
        # The supplied definition contrasts pirá re'õmbûera and se'õmbûera.
        from pydicate.lang.tupilang.pos import pûera, nde, ae, emi

        death = Noun("e'õ", definition="(t) (s.) morte")
        past = pûera * death
        self.assertEqual(death.eval(), "te'õ")
        self.assertEqual(past.eval(), "te'õmbûera")
        self.assertEqual(AnnotatedString(past.eval(True)).get_clean(), past.eval())
        self.assertIn("t[PLURIFORM_PREFIX:T:ABSOLUTE]", past.eval(True))
        for possessor, expected in ((nde, "nde re'õmbûera"), (ae, "se'õmbûera")):
            self.assertEqual((possessor * past).eval(), expected)
            self.assertEqual((pûera * (possessor * death)).eval(), expected)
        self.assertEqual((pûera * (emi * Verb("tym"))).eval(), "temitymbûera")


class ObjectBoundNominalAbsoluteTest(unittest.TestCase):
    def test_enonhen_object_blocks_second_absolute_prefix(self):
        # Pending Araújo: "Oicomemoãbäe renonhêna." The supplied lexical
        # definition also cites Bettendorff, Compêndio 23. Not approval.
        from pydicate.lang.tupilang.pos import bae, moro

        verb = Verb(
            value="enonhen",
            verb_class="(s) (v.tr.)",
            definition="(ou enonhẽ) (s) (v.tr.) - 1) repreender; corrigir, doutrinar em costumes (p.ex., o pai ao filho): Enonhẽ, eîakaká, t'oîepysyrõ-motá anhanga ratá suí. - Corrige-os, censura-os, para que queiram livrar-se do inferno. (Anch., Poemas, 158); Morubixaba tuîba'e onhe'eng memẽ i xupé, senonhena, i akakapa. - Os chefes velhos falam sempre a eles, repreendendo-os, censurando-os. (Anch., Teatro, 34); 2) reprimir: Mba'e-aí-potara renonhena. - Reprimir o desejo de coisas más. (Ar., Cat., 19v) ● enonhẽndara (t) - o repreensor, o que corrige, o que repreende: E'ikatu ipó senonhẽndarama supé é... - Pode certamente (contá-lo) para quem o repreenderá. (Ar., Cat., 73v)",
            vid=4050,
        )
        obj = bae * (Verb("ikó") / Noun("memûã"))
        nominal = (obj * verb).base_nominal()
        self.assertEqual(nominal.eval(), "oîkomemûãba'erenonhena")
        self.assertIn("[OBJECT:DIRECT]r[PLURIFORM_PREFIX:R]", nominal.eval(True))
        self.assertNotIn("[AGENT_PREFIX:GENERIC:PEOPLE:ABSOLUTE]", nominal.eval(True))
        self.assertEqual(verb.base_nominal().eval(), "morenonhena")
        self.assertEqual((Noun("abá") * verb).base_nominal().eval(), "abárenonhena")
        self.assertEqual((moro * verb).base_nominal().eval(), "mororenonhena")
        self.assertIsNone(nominal._nominalization_source.subject())
        self.assertEqual(nominal._nominalization_source.object().eval(), obj.eval())


if __name__ == "__main__":
    unittest.main()
