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
