import unittest

from tupi import Noun as TupiNoun

from pydicate.lang.tupilang.pos import Noun, Postposition, bo, pe


class DiffusiveBoTests(unittest.TestCase):
    """Navarro, -bo2 (posp.): diffuse/indeterminate locative, 'em, por, per'."""

    def test_attested_vowel_final_hosts(self):
        examples = [
            ("kó", "kóbo"),  # Anch., Arte, 42: kóbo 'nas roças'
            ("ka'a", "ka'abo"),  # VLB, II, 81: ka'abo 'pelas matas'
            # VLB, II, 81: nhũbo 'pelos campos'. Unlike -pe (nhũme), no
            # nasal allomorph after a nasal vowel.
            ("nhũ", "nhũbo"),
        ]
        for stem, surface in examples:
            with self.subTest(stem=stem):
                self.assertEqual((bo * Noun(stem)).eval(), surface)

    def test_attested_sab_deverbal(self):
        # Ar., Cat., 53: i potasábo; Ar., Cat., 3: ekomonhangábo. Final -ab
        # becomes -á before the postposition, as with -pe (sekasápe).
        self.assertEqual(TupiNoun("potasaba", "").bo().verbete(), "potasábo")
        self.assertEqual(TupiNoun("ekomonhangaba", "").bo().verbete(), "ekomonhangábo")

    def test_consonant_final_host_takes_epenthetic_y(self):
        # Not attested in the -bo2 entry. By analogy with -pe's -ype and
        # Navarro's epenthetic -y- (nhemim-y îanondé): okybo, not okbo.
        self.assertEqual((bo * Noun("oka")).eval(), "okybo")
        self.assertIn(
            "y[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING:CLITIC]bo[POSTPOSITION:DIFFUSIVE]",
            (bo * Noun("oka")).eval(annotated=True),
        )

    def test_annotated_tag(self):
        self.assertTrue(
            (bo * Noun("ka'a")).eval(annotated=True).endswith("bo[POSTPOSITION:DIFFUSIVE]")
        )

    def test_locative_contrast_unchanged(self):
        self.assertEqual((pe * Noun("oka")).eval(), "okype")
        self.assertEqual((pe * Noun("nhũ")).eval(), "nhũme")


class HyphenatedPostpositionTests(unittest.TestCase):
    """A dictionary headword such as -bo or -pe names a bound postposition."""

    def test_hyphenated_value_uses_bound_allomorphy(self):
        self.assertEqual((Postposition("-bo", definition="em, por") * Noun("ka'a")).eval(), "ka'abo")
        self.assertEqual((Postposition("-bo") * Noun("oka")).eval(), "okybo")
        self.assertEqual((Postposition("-pe") * Noun("oka")).eval(), "okype")
        self.assertEqual((Postposition("-pe") * Noun("nhũ")).eval(), "nhũme")

    def test_hyphenated_value_keeps_definition_and_bound_tag(self):
        p = Postposition("-bo", definition="em, por, per")
        self.assertEqual(p.definition, "em, por, per")
        self.assertTrue(
            (p * Noun("ka'a")).eval(annotated=True).endswith("bo[POSTPOSITION:DIFFUSIVE]")
        )

    def test_hyphenated_value_without_argument_shows_bare_form(self):
        self.assertEqual(Postposition("-bo").eval(), "-bo")

    def test_free_postposition_contrast_unchanged(self):
        self.assertEqual((Postposition("pupé") * Noun("oka")).eval(), "oka pupé")

    def test_unimplemented_hyphenated_value_unchanged(self):
        # Only bound forms with implemented allomorphy are rerouted.
        self.assertEqual((Postposition("-reme") * Noun("oka")).eval(), "oka -reme")


if __name__ == "__main__":
    unittest.main()
