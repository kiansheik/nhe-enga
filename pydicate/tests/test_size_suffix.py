import unittest

from pydicate.lang.tupilang.pos import Noun, SizeSuffix, Verb


class SizeSuffixTests(unittest.TestCase):
    def test_attested_compositions(self):
        examples = [
            ("pira", "-gûasu", "piragûasu"),  # Navarro, -ûasu: peixão
            ("pytun", "-usu", "pytunusu"),  # Ar., Cat., 80
            ("membyra", "-'ĩ", "membyrĩ"),  # Anch., Poemas, 102
            ("mba'e", "-'ĩ", "mba'e'ĩ"),  # Anch., Arte, 54
            ("îaboti", "mirĩ", "îabotimirĩ"),  # Sousa, Trat. Descr., 255
        ]
        for stem, suffix, surface in examples:
            with self.subTest(stem=stem, suffix=suffix):
                self.assertEqual((Noun(stem) / SizeSuffix(suffix)).eval(), surface)

    def test_size_after_nominal_classifier(self):
        from pydicate.lang.tupilang.pos import Adverb
        from pydicate.lang.tupilang.pos.deverbal import pûera, rama, saba

        # Pending Araujo: "Abá marã cecó agoérĩ"; requested analysis,
        # not an independently approved historical reference.
        source = pûera * (saba * (Noun("abá") * (
            Adverb("marã") >> Verb("ikó", verb_class="(v. intr. irreg.)", vid=5202)
        )))
        original = source.eval()
        result = source / SizeSuffix("-'ĩ")
        self.assertEqual(" ".join(result.eval().split()), "abá marã sekoagûerĩ")
        self.assertEqual(source.eval(), original)
        annotated = result.eval(annotated=True)
        self.assertIn("gûer[PRETERITE_SUFFIX]ĩ[SIZE_SUFFIX]", annotated)
        self.assertEqual(annotated.count("[PRETERITE_SUFFIX]"), 1)
        self.assertEqual(result.arguments[0].definition, source.arguments[0].definition)
        self.assertEqual(result.verbete, source.verbete)
        self.assertEqual((pûera * Noun("abá") / SizeSuffix("-'ĩ")).eval(), "abápûerĩ")
        self.assertEqual((rama * Noun("abá") / SizeSuffix("-'ĩ")).eval(), "abáramĩ")

    def test_verbal_base(self):
        self.assertEqual(
            (Verb("îur", verb_class="(v.i.)") / SizeSuffix("-usu")).eval(), "îurusu"
        )

    def test_general_composition_stays_unchanged(self):
        self.assertEqual((Noun("pira") / Noun("gûasu")).eval(), "pigûasu")

    def test_consonant_variant_rejects_vowel_stem(self):
        with self.assertRaisesRegex(ValueError, "consonant-stem"):
            Noun("pira") / SizeSuffix("-usu")
        with self.assertRaisesRegex(ValueError, "after a consonant"):
            Noun("pytun") / SizeSuffix("-gûasu")


if __name__ == "__main__":
    unittest.main()
