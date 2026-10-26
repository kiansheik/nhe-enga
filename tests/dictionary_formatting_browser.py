#!/usr/bin/env python3
"""Real-Chromium regressions for dictionary definition boundary formatting.

Run from the repository root with::

    .venv/bin/python tests/dictionary_formatting_browser.py

The test reuses the maintained audit capture instead of duplicating its local
server or browser setup. It exercises the production page, search path,
formatter, citation linker, highlighter, and browser HTML parser.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.qa.sample_dictionary_entries import (  # noqa: E402
    capture_entries,
    describe_record,
    read_dictionary,
)


AUDITED_FIXTURES = {
    2340: ("'aba", ""),
    2356: ("abaíba", ""),
    2393: ("abé", "2"),
    2406: ("abõ", ""),
    2407: ("abo'o", ""),
    2418: ("abyky", "2"),
    2425: ("aé", "2"),
    2435: ("aembé", ""),
    2831: ("ambyasy", ""),
    2858: ("amõamõnume", ""),
    3774: ("eboûinga", ""),
    3918: ("(e)mbetara", ""),
    4329: ("gûaîbĩ", ""),
    4609: ("-'ĩ", "2"),
    4755: ("ianga", ""),
    5299: ("îoesé", ""),
    5752: ("kakuab", "1"),
    6189: ("kûarasy", ""),
    6233: ("kûepe", ""),
    6882: ("mendara", ""),
    7015: ("moanhan", ""),
    7016: ("moanhẽ", ""),
    7212: ("mokanhem", "1"),
    7326: ("mondá", "1"),
    7340: ("mondó", ""),
    7765: ("-ne", "3"),
    7917: ("nhe'ẽpyo'u", ""),
    8463: ("parati", "1"),
    8525: ("peẽmo", ""),
    8713: ("piraîké", ""),
    8997: ("poromonhang", ""),
    9007: ("pororoka", ""),
    9012: ("poru", "1"),
    9168: ("pupé", ""),
    9433: ("ri", "2"),
    9405: ("ranhẽ", "2"),
    9773: ("syk", "3"),
    10473: ("tuîba'e", "1"),
}

COMPACT_DASH_CASES = {
    4148: (
        ("erok", "1"),
        "Abápe nde rerokara?",
        "Quem foi tua madrinha? (Anch., Teatro, 166)",
    ),
    4588: (
        ("gûyrype", ""),
        "\"-I katupe temõ mã!\", erépe, nde gûyrype kunhã resé nde rekó mo'ang'iré?",
        "Disseste: -Ah, quem me dera estivesse nua!, após imaginares estar com uma mulher debaixo de ti? (Anch., Doutr. Cristã, II, 93)",
    ),
    5110: (
        ("îeraba", ""),
        "Marã e'ipe Tupã i tĩ-îeraba repîaka?",
        "Que disse Deus vendo seu frouxo pudor? (Ar., Cat., 41)",
    ),
    5197: (
        ("iké", "2"),
        "Marã Santa Maria rekóremepe, karaibebé reîkéû i xupé?",
        "Como estava Santa Maria quando o anjo entrou para junto dela? (Ar., Cat., 30v)",
    ),
    5299: (
        ("îoesé", ""),
        "Oîkuab, o îoesé Îandé Îara ma'ẽneme.",
        "Reconheceu-o ao olhar Nosso Senhor para ele. (Ar., Cat., 57)",
    ),
    7533: (
        ("mosapyra", ""),
        "Marã e'ipe i mosapyra?",
        "Que diz o terceiro deles? (Ar., Cat., 76v)",
    ),
    8381: (
        ("paîegûasu", ""),
        "Paîegûasu remimonhanga.",
        "Obra de um artífice. (Léry, Histoire, 345)",
    ),
    10101: (
        ("tatapu'i", ""),
        "Ererupe tatapu'i setá?",
        "Trouxeste muita pólvora? (D'Evreux, Viagem, 246)",
    ),
}

POST_DIALOGUE_CASES = {
    2343: (
        ("abá", "2"),
        "...abá 'anga momoxŷabo.",
        "estragando as almas dos índios. (Anch., Teatro, 44)",
    ),
    3972: (
        ("(e)mityma", ""),
        "O emitymaysó Paraíso Terreal seryba'epe.",
        'No seu jardim formoso chamado "Paraíso Terreal". (Ar., Cat., 39)',
    ),
    4609: (
        ("-'ĩ", "2"),
        "...Nd'e'ikatuî oîepé'ĩ tiruã Tupã nhe'enga abŷagûera o îoupé i mombe'upyrûera mombegûabo abá supé...",
        "Não pode sequer uma única vez contar para alguém a transgressão da palavra de Deus que foi contada para si. (Ar., Cat., 98)",
    ),
    6982: (
        ("-mo", "3"),
        "...Esykyîébomo, ereîkó-katumo.",
        "Tendo medo, farias bem. (Ar., Cat., 112)",
    ),
    7192: (
        ("mokaba", ""),
        "Saûsupara, aîuruîuba, mokaba ogûeru tenhẽ...",
        "Seus amigos, os franceses, trouxeram armas de fogo em vão. (Anch., Teatro, 52)",
    ),
    7575: (
        ("motyb", ""),
        "Aûîé, kó temiminõ nd' ogûari Tupã rekó, nd'osaûsubi, n'omotybi...",
        "Enfim, esses temiminós não tomam a lei de Deus, não a amam, não a acatam... (Anch., Teatro, 20)",
    ),
}

ANNOTATED_GLOSS_CASES = {
    2738: (("akûeî", ""), "aquele (es, a, as); esse (es, a, as)"),
    2932: (("ang", ""), "este (es, a, as), esse (es, a, as)"),
    3409: (("'ari", ""), "em cima de, sobre (Anch., Arte, 41)"),
    3445: (("aryba", ""), "cacho (de bananas, de uvas, etc.)"),
    3791: (("eî", ""), "lavar"),
    3899: (("ekûá", ""), "Vai!"),
    3900: (("ekûãî", ""), "Vai!"),
    3990: (
        ("en", "2"),
        "derramar, fazer verter, entornar (p.ex., o líquido, a farinha)",
    ),
    4297: (("gû", "2"), "seu, seu próprio (s, a, as)"),
    4613: (("iã", ""), "eis que"),
    4754: (("iang", ""), "este (es, a, as); esse (es, a, as) (VLB, II, 15)"),
    4930: (
        ("îeerekomemûã", ""),
        "ficar de mal [com alguém: compl. com esé (r, s)]",
    ),
    5226: (("imbé", ""), "ficar, estar (VLB, I, 128)"),
    5229: (("imẽ", ""), "estar"),
    5595: (("ixébe", ""), "a mim, para mim"),
    6157: (("kûãî!", ""), "vai!"),
    6178: (("kuapamoindaba", ""), "marca, ferrete (para gado, para escravos)"),
    6444: (
        ("ma'enan", ""),
        "vigiar, velar, espiar [compl. com esé (r, s) ou ri]",
    ),
    7291: (("mombyk", "2"), "fazer cessar, parar, acabar com"),
    7854: (("-nhe-", ""), "me, te, se, nos, vos"),
    8362: (("pá", "1"), "sim (Fig., Arte, 133)"),
    8501: (("pe", "2"), "haver de"),
    8505: (("pé", "1"), "a, para, junto de, em busca de, etc."),
    8532: (("peîori", ""), "vinde! (Anch., Arte, 57v)"),
    8692: (("-pipó?", ""), "de fato? por acaso? porventura?"),
    9395: (("rambûer", "1"), "o que seria"),
    10540: (("tupãrasara", ""), "comungante"),
    10747: (("ûer", ""), "antigo, passado, que foi"),
    10759: (("ûĩ", "1"), "eis que; eis que esse (es, a, as)"),
    10789: (("umanĩ", "1"), "devagar"),
}

NUMBERED_ANNOTATION_CONTROLS = {
    2851: ("amõ", "1"),
    3766: ("ebokûé", ""),
    3767: ("ebokûea", ""),
    4114: ("erĩ", ""),
    9410: ("ra'u", ""),
    9413: ("re'ĩ", "1"),
}

FIXTURES = dict(AUDITED_FIXTURES)
FIXTURES.update(
    {
        2312: ("-a", "2"),
        2314: ("'a", "1"),
        2320: ("aan", "2"),
        2353: ("abaeté", "2"),
        2357: ("abaîeru", ""),
        2379: ("abati", ""),
        2420: ("a'e", "1"),
        2421: ("a'e", "2"),
        2422: ("a'e", "3"),
        2423: ("a'e?", "4"),
        2442: ("a'enipó", ""),
        2452: ("ãgûa", ""),
        2511: ("aíba", "1"),
        2569: ("aîuba", ""),
        2622: ("akaîgûá", ""),
        2728: ("akuba", ""),
        2739: ("akûeîa", ""),
        2844: ("amĩ", ""),
        2996: ("anhera'upe", ""),
        3025: ("anõîa", ""),
        3372: ("arasamirĩ", ""),
        3412: ("arinhama", ""),
        3432: ("arûaba", ""),
        3433: ("arũaíba", ""),
        3446: ("arybé", ""),
        3483: ("asy", ""),
        3508: ("atapyĩ'ok", ""),
        3512: ("ate'ẽ", ""),
        3571: ("a'uba", ""),
        3624: ("aŷpy", "2"),
        3703: ("-bo", "2"),
        3729: ("byter", ""),
        3740: ("é", "8"),
        3744: ("é?", "10"),
        3805: ("eîori", ""),
        3887: ("ekoposyîa", ""),
        3897: ("ekotebẽ", ""),
        4080: ("epyk", ""),
        4105: ("erekoara", "2"),
        4120: ("erimba'e", "1"),
        4190: ("esá", ""),
        4296: ("-gû-", "1"),
        4374: ("gûam", ""),
        4398: ("gûapyk", ""),
        4521: ("gûy", ""),
        4600: ("-i", "2"),
        4601: ("-i", "3"),
        4608: ("-'ĩ", "1"),
        4703: ("îakatu", "2"),
        4888: ("i'e", ""),
        4953: ("i'ekatu", ""),
        5201: ("ikó", "1"),
        5202: ("ikó", "2"),
        5274: ("îó", "2"),
        5308: ("îoîtyîtyk", ""),
        5316: ("îori", ""),
        5351: ("irũmo", ""),
        5352: ("irũnamo", ""),
        5356: ("itá", ""),
        5466: ("îub", ""),
        5468: ("îuba", ""),
        5504: ("îukyra", ""),
        5549: ("îuru", "1"),
        5667: ("ka'apeba", ""),
        5790: ("kambuká", ""),
        5825: ("kanga", "2"),
        5827: ("kanga", "3"),
        5885: ("karaíba", "3"),
        5980: ("katupabẽ", ""),
        6061: ("ko'ema", ""),
        6109: ("korikoria'ub", ""),
        6145: ("kuab", ""),
        6212: ("ku'e", ""),
        6368: ("kururu", ""),
        6444: ("ma'enan", ""),
        6456: ("mahmõ!", ""),
        6458: ("maîé", ""),
        6529: ("manhana", ""),
        6624: ("marangoty?", ""),
        6811: ("mboryb", "2"),
        6812: ("mbosyî", ""),
        6859: ("membyrara", ""),
        7048: ("moapysyk", ""),
        7170: ("moingó", ""),
        7181: ("moîoîab", ""),
        7219: ("mokõîa", ""),
        7223: ("mokon", ""),
        7652: ("murukuîagûasu", ""),
        7700: ("na", ""),
        7785: ("nupã", ""),
        7889: ("nhe'engapaparaíba", ""),
        8032: ("nhemongetá", "1"),
        8033: ("nhemongetá", "2"),
        8253: ("oîoparaba", ""),
        8297: ("okyra", ""),
        8440: ("paraba", "1"),
        8926: ("porambyrambyka", ""),
        8948: ("poreaûsuba", ""),
        9271: ("pyma", ""),
        9302: ("pyryb", "1"),
        9399: ("ramõ", ""),
        9400: ("-(r)amo", ""),
        9420: ("-reme", ""),
        9461: ("rumby", ""),
        9469: ("s-", ""),
        9508: ("sama", ""),
        9577: ("sé", ""),
        9596: ("sem", ""),
        9701: ("-sûer", "1"),
        9776: ("sykaba", ""),
        9852: ("taîasu", "1"),
        10159: ("-te", "4"),
        10341: ("tĩ", "4"),
        10356: ("tieté", ""),
        10558: ("tupinakyîa", ""),
        10606: ("tyk", ""),
        10756: ("ûi-", ""),
        10717: ("uba", "4"),
        10757: ("u'i", ""),
        10993: ("yaíba", ""),
        11005: ("yapu", ""),
        11091: ("ybŷá", ""),
        11219: ("ybysopuku", ""),
    }
)
for source_index, (key, _definition) in ANNOTATED_GLOSS_CASES.items():
    FIXTURES[source_index] = key
FIXTURES.update(NUMBERED_ANNOTATION_CONTROLS)
FIXTURES.update(
    {
        2782: ("am", ""),
        4122: ("(e)ro-", ""),
    }
)
for source_index, (key, _tupi, _portuguese) in {
    **COMPACT_DASH_CASES,
    **POST_DIALOGUE_CASES,
}.items():
    FIXTURES[source_index] = key


def quote_text(capture):
    fields = (
        "tupi",
        "portuguese",
        "dialogue_tupi",
        "dialogue_portuguese",
        "direct_text",
    )
    return "\n".join(
        value
        for quote in capture["semantic_outline"]["quotes"]
        for field in fields
        for value in quote[field]
    )


def regular_pairs(capture):
    pairs = []
    for quote in capture["semantic_outline"]["quotes"]:
        if len(quote["tupi"]) == 1 and len(quote["portuguese"]) == 1:
            pairs.append((quote["tupi"][0], quote["portuguese"][0]))
    return pairs


class DictionaryFormattingBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records, _source = read_dictionary(ROOT / "docs/dict-conjugated.json.gz")
        selected = []
        for source_index, expected_key in FIXTURES.items():
            record = records[source_index]
            actual_key = (record.get("f", ""), str(record.get("o", "")))
            if actual_key != expected_key:
                raise AssertionError(
                    f"served dictionary index {source_index} changed: "
                    f"expected {expected_key!r}, got {actual_key!r}"
                )
            selected.append(
                describe_record(record, source_index, "formatting regression fixture")
            )

        captures = capture_entries(selected, records, screenshots=None)
        cls.captures = dict(zip(FIXTURES, captures, strict=True))

    def capture(self, source_index):
        capture = self.captures[source_index]
        self.assertEqual(
            capture["diagnostics"]["flags"],
            [],
            f"unexpected DOM structure for {capture['headword']}",
        )
        return capture

    def assert_pair(self, capture, tupi, portuguese):
        self.assertIn((tupi, portuguese), regular_pairs(capture))

    def assert_dialogue(self, capture, tupi, portuguese):
        self.assertTrue(
            any(
                quote["dialogue_tupi"] == tupi
                and quote["dialogue_portuguese"] == portuguese
                for quote in capture["semantic_outline"]["quotes"]
            ),
            f"missing dialogue rows {(tupi, portuguese)!r}",
        )

    def test_ranhe_adverb_heading_and_first_example_are_siblings(self):
        capture = self.capture(9405)
        self.assertEqual(
            capture["semantic_outline"]["section_titles"],
            ["Advérbio:", "Verbetes relacionados:"],
        )
        self.assertEqual(
            capture["semantic_outline"]["definitions"][0],
            "primeiro, antes, primeiramente (na afirm.)",
        )
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            capture,
            "...Ereîkuá ranhẽ meémo emonã nde rekorama...",
            "Deverias ter sabido antes do teu agir assim. (Ar., Cat., 57v)",
        )

    def test_pupe_recovers_compact_example_and_keeps_explanation_as_prose(self):
        capture = self.capture(9168)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 12)
        self.assert_pair(capture, "itá pupé", "com uma pedra (VLB, I, 77)")
        self.assert_pair(
            capture,
            "A'a nde pupé.",
            "Caí no mesmo lugar de ti (isto é, caí em teus costumes)",
        )
        self.assertNotIn(
            '<span class="quote-citation">(isto é, caí em teus costumes)</span>',
            capture["preview_html"],
        )

    def test_diminutive_suffix_keeps_post_dialogue_example(self):
        capture = self.capture(4609)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 9)
        dialogue = capture["semantic_outline"]["quotes"][6]
        self.assertEqual(len(dialogue["dialogue_tupi"]), 2)
        self.assertEqual(len(dialogue["dialogue_portuguese"]), 2)
        self.assert_pair(
            capture,
            "...Nd'e'ikatuî oîepé'ĩ tiruã Tupã nhe'enga abŷagûera o îoupé i mombe'upyrûera mombegûabo abá supé...",
            "Não pode sequer uma única vez contar para alguém a transgressão da palavra de Deus que foi contada para si. (Ar., Cat., 98)",
        )
        pairs = regular_pairs(capture)
        self.assertLess(
            pairs.index(
                (
                    "...Nd'e'ikatuî oîepé'ĩ tiruã Tupã nhe'enga abŷagûera o îoupé i mombe'upyrûera mombegûabo abá supé...",
                    "Não pode sequer uma única vez contar para alguém a transgressão da palavra de Deus que foi contada para si. (Ar., Cat., 98)",
                )
            ),
            pairs.index(("Turusu'ĩ.", "Ele é medianamente grande. (VLB, II, 34)")),
        )

    def test_future_particle_separates_note_and_shared_citation_examples(self):
        capture = self.capture(7765)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 9)
        self.assert_pair(
            capture,
            "Osapirõ-n'asé og uba o sy kanhemagûera...",
            "Há de prantear a gente o desaparecimento de seu pai e de sua mãe. (Anch., Doutr. Cristã, II, 112)",
        )
        self.assert_pair(capture, "T'asóne.", "Hei de ir. (Anch., Arte, 23)")
        self.assert_pair(capture, "T'orosóne.", "Havemos de ir. (Anch., Arte, 23)")
        note = "(Com o permissivo, geralmente só se usa com a 1ª p.)"
        self.assertIn(note, capture["rendered_text"])
        self.assertNotIn(note, quote_text(capture))

    def test_ioese_splits_translation_dash_without_a_following_space(self):
        capture = self.capture(5299)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            capture,
            "Oîkuab, o îoesé Îandé Îara ma'ẽneme.",
            "Reconheceu-o ao olhar Nosso Senhor para ele. (Ar., Cat., 57)",
        )

    def test_all_compact_dash_examples_split_into_source_and_translation(self):
        for source_index, (_key, tupi, portuguese) in COMPACT_DASH_CASES.items():
            with self.subTest(
                source_index=source_index, headword=FIXTURES[source_index]
            ):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_kakuab_ignores_semicolon_inside_square_brackets(self):
        capture = self.capture(5752)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 5)
        self.assertIn(
            "crescer; fazer-se (rapaz ou moça)",
            capture["semantic_outline"]["definitions"],
        )
        self.assertIn(
            "envelhecer [o homem ou o animal; fal. de coisas, v. aíb ou nhemoaíb]; ter muita idade",
            capture["semantic_outline"]["definitions"],
        )

    def test_ambyasy_adjective_heading_does_not_absorb_example(self):
        capture = self.capture(2831)
        self.assertEqual(
            capture["semantic_outline"]["section_titles"],
            ["Adjetivo:", "Verbetes relacionados:"],
        )
        self.assertIn(
            "faminto; (xe) ter fome",
            capture["semantic_outline"]["definitions"],
        )
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            capture,
            "I ambyasy bépe, i 'useî bépe asé îabé?...",
            "Tinha também fome, tinha também sede como nós? (Ar., Cat., 44v)",
        )

    def test_literal_etymological_angle_brackets_do_not_hide_examples(self):
        aba = self.capture(2340)
        self.assertIn("pelo da cabeça < 'a + aba", aba["rendered_text"])
        self.assertEqual(aba["diagnostics"]["sense_quote_count"], 6)
        self.assert_pair(
            aba,
            "Aî'abeky-ekyî.",
            "Fiquei-lhe puxando os pêlos; fiquei-o arrepelando. (VLB, I, 42)",
        )

        kuarasy = self.capture(6189)
        self.assertIn("origem deste dia < kó 'ara sy", kuarasy["rendered_text"])
        self.assertEqual(kuarasy["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            kuarasy,
            "Kûarasy onhemoputun...",
            "O sol se eclipsa. (Ar., Cat., 64)",
        )

    def test_punctuation_adjacent_translation_dashes_are_recovered(self):
        cases = {
            2356: (
                9,
                "I abaí xebo sa'anga.",
                "É difícil para mim tentá-los. (Anch., Teatro, 16)",
            ),
            2406: (
                1,
                "... O îoesé bé tatá rerekóbo, o endy îandy i abõmo nhẽ.",
                "Em si também tendo fogo, suas chamas o óleo avivando. (Ar., Cat., 161)",
            ),
            2407: (2, "Asabo'o.", "Pelei-o. (VLB, II, 70)"),
        }
        for source_index, (count, tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertEqual(capture["diagnostics"]["sense_quote_count"], count)
                self.assert_pair(capture, tupi, portuguese)

        self.assert_pair(
            self.capture(2407),
            "Aî'apir-abo'o.",
            "Eu lhe pélo o couro cabeludo. (VLB, II, 70)",
        )

    def test_spaced_dialogue_markers_form_dialogue_rows(self):
        cases = {
            2393: (
                ["💬 Marãpe pe rubixabetae'ym?", "🗨️ Nd'oroerekóî nhẽ oré ramuîa abé."],
                [
                    "Por que vós não tendes muitos reis?",
                    "Não os temos desde nossos avós. (Léry, Histoire, 362)",
                ],
            ),
            2858: (
                [
                    "💬 Nd'oîaby-angáîpe omendaryba'e Tupã rekó oîopotá?",
                    "🗨️ Amõamõnyme.",
                ],
                [
                    "Não transgridem de modo algum os casados a lei de Deus, desejando-se um ao outro?",
                    "Às vezes. (Anch., Doutr. Cristã, I, 228)",
                ],
            ),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertEqual(capture["diagnostics"]["sense_quote_count"], 1)
                quote = capture["semantic_outline"]["quotes"][0]
                self.assertEqual(quote["dialogue_tupi"], tupi)
                self.assertEqual(quote["dialogue_portuguese"], portuguese)

    def test_bracketed_category_label_becomes_a_heading_and_opens_examples(self):
        capture = self.capture(2435)
        self.assertIn(
            "Adjetivo: aembé (r, s)",
            capture["semantic_outline"]["section_titles"],
        )
        self.assertIn(
            "afiado (p.ex., faca) (VLB, I, 27)",
            capture["semantic_outline"]["definitions"],
        )
        self.assertNotIn("[adj: aembé (r, s)]", quote_text(capture))
        self.assert_pair(capture, "Saembé.", "Ela está afiada. (VLB, I, 83)")

    def test_direct_pos_heading_examples_are_quote_cards_not_definitions(self):
        cases = {
            4329: (
                "Kó aîkó sygepûera t'arasó i nhy'ãbebuîa abé xe raîxó-gûaîbĩ supé.",
                "Aqui estou para levar seu ventre e também seus pulmões para minha sogra velha. (Anch., Teatro, 66)",
            ),
            7326: (
                "Abá-mondá...",
                "Um homem ladrão... (Ar., Cat., 59v)",
            ),
            7917: ("Xe nhe'ẽpyo'u.", "Eu estou rouco. (VLB, I, 117)"),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(
                    "Adjetivo:", capture["semantic_outline"]["section_titles"]
                )
                self.assert_pair(capture, tupi, portuguese)
                self.assertNotIn(tupi, capture["semantic_outline"]["definitions"])

        monda = self.capture(7326)
        self.assertEqual(
            monda["semantic_outline"]["definitions"],
            ["ladrão (VLB, II, 17)", "roubo, furto"],
        )
        self.assert_pair(monda, "Xe mondá.", "Eu sou ladrão. (VLB, II, 17)")

    def test_numbered_senses_separate_glosses_from_inline_examples(self):
        cases = {
            3774: (
                "(dem. pron.) - esse (es, a, as), isso",
                "Eboûinga abépe ybakype nd'asé mondóî?",
                "Esse também não faz a gente ir para o céu? (Anch., Doutr. Cristã, I, 201)",
            ),
            4755: (
                "aqui",
                "Asẽ esapy'a temõ ianga suí mã!",
                "Oxalá eu saísse logo daqui! (Ar., Cat., 164v)",
            ),
            6882: (
                "casado(a)",
                "Ereîkópe mendara, mendarûera resé?",
                "Tens relações com uma casada, com uma que foi casada? (Anch., Doutr. Cristã, II, 89)",
            ),
            7340: (
                "largar (p.ex., a corda, algo da mão)",
                "Aîmondó-mondó.",
                "Eu os fui largando. (VLB, II, 18)",
            ),
            8525: (
                "a vós, para vós, vos",
                "Marãeté'ĩ-pipó peẽmo?",
                "Como vos parece, porventura? (Ar., Cat., 56v)",
            ),
            9773: (
                "acabar",
                "...Ikó îope'asagûera syk'iré esepîá-ukar orébe...",
                "Após acabar este desterro comum, faze-nos vê-lo. (Ar., Cat., 14v)",
            ),
        }
        for source_index, (definition, tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(definition, capture["semantic_outline"]["definitions"])
                self.assert_pair(capture, tupi, portuguese)
                self.assertNotIn(tupi, capture["semantic_outline"]["definitions"])

        self.assertIn(
            "Advérbio:", self.capture(4755)["semantic_outline"]["section_titles"]
        )

        mokanhem = self.capture(7212)
        self.assertIn(
            "destruir, arruinar, desgraçar...",
            mokanhem["semantic_outline"]["definitions"],
        )
        self.assert_pair(
            mokanhem,
            "Oporomokanhem ikó...",
            "Este desgraça as pessoas. (Ar., Cat., 66v)",
        )

        ri = self.capture(9433)
        self.assertIn("com (instr.)", ri["semantic_outline"]["definitions"])
        self.assert_pair(
            ri,
            "Xe abá nhe'enga ri.",
            "Com minha palavra de homem. (Anch., Teatro, 154, 2006)",
        )

    def test_citation_clusters_and_unpaginated_cross_reference_stay_owned(self):
        self.assert_pair(
            self.capture(2418),
            "Aîabyky.",
            "Manuseio-o. (Anch., Arte, 49v) (Anch., Arte, 50)",
        )
        self.assert_pair(
            self.capture(8463),
            "Nd'aruri amõ parati.",
            "Não trouxe nenhum parati. (Anch., Poemas, 152) (D'Abbeville, Histoire, 244v)",
        )
        kuepe = self.capture(6233)
        self.assert_pair(
            kuepe,
            "Îasytatá kûepe é i nhemimi...",
            "As estrelas bem longe se escondem... (Valente, Cantigas, IV, in Ar., Cat)",
        )
        self.assert_pair(
            kuepe,
            "...Îaîu kûepe suí.",
            "Viemos de longe. (Anch., Poemas, 96)",
        )

    def test_citation_boundaries_do_not_leak_separator_commas(self):
        cases = {
            2425: (
                "Oré rekó-rekó-aé oroerekó.",
                "Temos nossos modos de ser diferentes. (VLB, I, 103)",
            ),
            10473: (
                "...O tuîba'e pupé te'õ kuapa.",
                "Conhecendo a morte em sua velhice. (Ar., Cat., 157v)",
            ),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assert_pair(capture, tupi, portuguese)
                self.assertFalse(
                    any(
                        line.startswith(",")
                        for quote in capture["semantic_outline"]["quotes"]
                        for line in quote["tupi"]
                    )
                )

    def test_lowercase_roman_and_bracketed_locators_remain_definition_prose(self):
        piraike = self.capture(8713)
        self.assertEqual(piraike["diagnostics"]["sense_quote_count"], 0)
        self.assertIn("cap. xviii", piraike["rendered_text"])

        pororoka = self.capture(9007)
        self.assertEqual(pororoka["diagnostics"]["sense_quote_count"], 0)
        self.assertEqual(len(pororoka["semantic_outline"]["definitions"]), 2)
        self.assertIn("III, 176]", pororoka["rendered_text"])

    def test_embetara_ends_translation_before_usage_note_and_cross_form(self):
        capture = self.capture(3918)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            capture,
            "metaroby",
            "tembetá verde ou azul (Marcgrave, Hist. Nat. Bras., 271)",
        )
        note = "(Pode também ser pluriforme regular, com forma absol. em t-)"
        cross_form = "tembetara (Anch., Arte, 13v)"
        self.assertIn(note, capture["rendered_text"])
        self.assertIn(cross_form, capture["rendered_text"])
        self.assertNotIn(note, quote_text(capture))
        self.assertNotIn(cross_form, quote_text(capture))

    def test_moanhe_splits_adjacent_citation_delimited_pairs(self):
        capture = self.capture(7016)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 4)
        self.assert_pair(
            capture,
            "...Te'õ moanhẽ-anhẽmo...",
            "Ficando a esperar ansiosamente a morte. (Ar., Cat., 158v)",
        )
        self.assert_pair(
            capture,
            "...Korikorinhẽa'ub 'ara repîaki, i moanhẽmo...",
            "Deseja logo ver o dia, ficando ansioso por ele. (Anch., Doutr. Cristã, II, 79)",
        )

    def test_all_post_dialogue_examples_remain_separate_quote_pairs(self):
        for source_index, (_key, tupi, portuguese) in POST_DIALOGUE_CASES.items():
            with self.subTest(
                source_index=source_index, headword=FIXTURES[source_index]
            ):
                capture = self.capture(source_index)
                quotes = capture["semantic_outline"]["quotes"]
                expected_pair = (tupi, portuguese)
                pair_index = next(
                    (
                        index
                        for index, quote in enumerate(quotes)
                        if len(quote["tupi"]) == 1
                        and len(quote["portuguese"]) == 1
                        and (quote["tupi"][0], quote["portuguese"][0]) == expected_pair
                    ),
                    None,
                )
                self.assertIsNotNone(pair_index, f"missing pair {expected_pair!r}")
                self.assertTrue(
                    any(
                        quote["dialogue_tupi"] and quote["dialogue_portuguese"]
                        for quote in quotes[:pair_index]
                    ),
                    "expected a dialogue block before the recovered pair",
                )

    def test_poru_preserves_shared_citation_control(self):
        capture = self.capture(9012)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 8)
        self.assert_pair(
            capture,
            "Aîporu aoba karaíba suí.",
            "Tomei emprestada a roupa do homem branco (VLB, I, 113)",
        )
        self.assert_pair(
            capture,
            "Aîporu abá ygara.",
            "Tomei emprestada a canoa do índio. (VLB, I, 113)",
        )

    def test_moanhan_preserves_quoted_hyphens_control(self):
        capture = self.capture(7015)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 3)
        self.assert_pair(
            capture,
            "Ereîmomaranype nde mena... \"-t'oropyk\" i 'éreme, i moanhana?",
            'Resististe a teu marido quando ele disse: "-hei de te cobrir", empurrando-o? (Anch., Doutr. Cristã, II, 98)',
        )

    def test_poromonhang_preserves_dialogue_control(self):
        capture = self.capture(8997)
        self.assertEqual(capture["diagnostics"]["sense_quote_count"], 2)
        dialogue, regular = capture["semantic_outline"]["quotes"]
        self.assertEqual(
            dialogue["dialogue_tupi"],
            ["💬 Mba'erama resépe abá mendari?", "🗨️ O poromonhanga potá."],
        )
        self.assertEqual(
            dialogue["dialogue_portuguese"],
            [
                "Por que alguém se casa?",
                "Querendo gerar filhos. (Ar., Cat., 95)",
            ],
        )
        self.assertEqual(
            (regular["tupi"], regular["portuguese"]),
            (
                [
                    "...Oito anhõ o nhe'enga rupi tekoara oporomonhangyba'erama raûsubá..."
                ],
                [
                    "Compadecendo-se somente de oito que viviam segundo suas palavras e que gerariam filhos. (Ar., Cat., 106v)"
                ],
            ),
        )

    def test_plain_semicolon_continuations_remain_complete_definitions(self):
        expected = {
            2320: "nenhum; ninguém (VLB, II, 49)",
            2357: (
                'o fruto dessa planta,... "da feição e tamanho das ameixas... '
                'e de cor roxa; come-se como ameixas, mas tem maior caroço..." '
                "(Sousa, Trat. Descr., 188) (o mesmo que gûaîeru - v.)"
            ),
            2511: "maldade, ruindade; AÍVA, coisa vil (VLB, I, 136; II, 145)",
            4105: (
                "guardião, o que toma conta de; tutor (como de órfão) " "(VLB, II, 129)"
            ),
            5356: ("metal; ferro (VLB, I, 138); ferros de prisão (VLB, I, 138)"),
        }
        for source_index, definition in expected.items():
            with self.subTest(source_index=source_index):
                self.assertIn(
                    definition,
                    self.capture(source_index)["semantic_outline"]["definitions"],
                )

    def test_examples_immediately_after_definitions_become_quote_cards(self):
        expected_pairs = {
            2511: [
                (
                    "...Îandé aíba t'oîpe'a.",
                    "Que afaste nossa maldade. (Anch., Poemas, 182)",
                )
            ],
            4105: [
                (
                    "Iesu toryberekoara",
                    "Jesus, guardião da alegria. "
                    "(Valente, Cantigas, I, in Ar., Cat., 1618)",
                ),
                (
                    "Oré oroîkó pe rerekoaretéramo.",
                    "Nós somos vossos verdadeiros guardiães. "
                    "(D'Abbeville, Histoire, 341v)",
                ),
            ],
            5356: [
                (
                    "Ererupe itá kysé amõ?",
                    "Trouxeste algumas facas de ferro? (Léry, Histoire, 346)",
                ),
                ("Itá resé aín.", "Estou preso nos ferros. (VLB, II, 85)"),
            ],
            7048: [
                (
                    "Xe moapysy-katu.",
                    "Deleita-me muito. (VLB, I, 27; 93)",
                )
            ],
        }
        for source_index, pairs in expected_pairs.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                for tupi, portuguese in pairs:
                    self.assert_pair(capture, tupi, portuguese)

        ita = self.capture(5356)
        for tupi, portuguese in (
            ("itagûasu", "penedo grande (VLB, II, 69, 72)"),
            (
                "itá-tyba (ou itá-tybusu)",
                "jazimento de pedras, pedreira (VLB, II, 69, 72)",
            ),
            (
                "itagûasutyba",
                "jazimento de pedras grandes, penedia (VLB, II, 69, 72)",
            ),
        ):
            self.assert_pair(ita, tupi, portuguese)

    def test_two_dash_definition_shape_splits_gloss_from_examples(self):
        capture = self.capture(10606)
        self.assertEqual(
            capture["semantic_outline"]["definitions"],
            ["em multidão; em grande número, em muitos (com o v. no pl.)"],
        )
        self.assert_pair(
            capture,
            "Tyk oro'é (ou Tyk oro'é nhẽ).",
            "Em grande número estamos. (VLB, II, 44; Anch., Arte, 57)",
        )
        self.assert_pair(
            capture,
            "Tyk e'i.",
            "Estão em grande número, são muitos. (Anch., Arte, 57)",
        )

    def test_grammatical_markers_never_become_tupi_quote_lines(self):
        expected = {
            2728: ("Adjetivo: akub (r, s)", "quente"),
            3432: ("Adjetivo: arûab (r, s)", "impedido, (xe) impedir-se"),
            3433: (
                "Adjetivo: arũaíb",
                "chocarrice, gracejo, motejo, escárnio",
            ),
            3446: (
                "Adjetivo:",
                "tranquilo; quieto, bonançoso (falando-se do mar) (VLB, I, 18)",
            ),
            3887: ("Adjetivo: ekoposyî (r, s)", "grave (VLB, II, 11)"),
            5885: (
                "Adjetivo: karaíb ou karaí",
                "santo, bento; divino, sagrado, virtuoso, benzido",
            ),
            9508: (
                "Adjetivo: sam",
                "(xe) ter corda; formar fios (p.ex., o visgo, a clara de açúcar, etc.) (VLB, I, 139)",
            ),
            10717: ("Adjetivo: ub (r, s)", "(xe) ter ova (o peixe) (VLB, II, 60)"),
            11005: (
                "Adjetivo: yapu (r, s)",
                "barulhento, estrondoso; (xe) soar ou tocar; rugir, fazer barulho ou estrondo",
            ),
        }
        for source_index, (heading, definition) in expected.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(heading, capture["semantic_outline"]["section_titles"])
                self.assertIn(definition, capture["semantic_outline"]["definitions"])
                for quote in capture["semantic_outline"]["quotes"]:
                    for line in quote["tupi"]:
                        self.assertFalse(
                            line.lstrip()
                            .lower()
                            .startswith(("(adj", "(adv", "(v.", "[adj", "[adv"))
                        )

        verb = self.capture(8033)
        self.assertEqual(
            verb["semantic_outline"]["definitions"], ["pensar, refletir, devanear"]
        )
        self.assert_pair(
            verb,
            "Nd'ei te'e, o py'a pupé oîemongetá-ngetábo, Tupã momburukatûabo...",
            "Por isso mesmo é que, em seus corações ficando a refletir, "
            "desafiam muito a Deus. (Anch., Teatro, 30)",
        )

    def test_translation_semicolon_and_shared_pair_boundaries_are_preserved(self):
        desire = self.capture(6109)
        self.assert_pair(
            desire,
            "Korikoria'ub oroepîak.",
            "Desejo muito ver-te; não via a hora de ver-te. (VLB, II, 48)",
        )

        opinion = self.capture(2423)
        self.assert_pair(
            opinion,
            "A'e-tepe nde?",
            "E quanto a ti? (isto é, qual é tua opinião?) (VLB, I, 78)",
        )
        self.assert_pair(
            opinion,
            "A'e-tepe nde nhe'enga?",
            "E qual é a tua palavra? (i.e, que dizes sobre isso?) (VLB, I, 78)",
        )

        pity = self.capture(8948)
        self.assert_pair(
            pity,
            "I poreaûsubĩ mã! (ou I poreaûsubeté'ĩ mã! ou I poreaûsubĩ ra'u mã!)",
            "Ah, coitadinho dele! (VLB, I, 76; II, 53; Ar., Cat., 155v)",
        )
        self.assert_pair(
            pity,
            "Xe poreaûsubĩ mã! (ou Xe poreaûsubeté'ĩ ra'u mã!)",
            "Ah, coitadinho de mim! (A mulher diz também amaeîu - v.) "
            "(VLB, I, 76; II, 53; Ar., Cat., 155v)",
        )

    def test_unnumbered_main_glosses_are_definition_spans(self):
        expected = {
            2314: "cabeça",
            2442: "e parece que",
            3508: (
                "espevitar (o fogo, tirar a pevide, o morrão às velas ou "
                "candieiros para darem luz mais clara)"
            ),
            3624: (
                "reigada, lugar em que a parte está mais junta a seu todo "
                "(como o cacho de frutas à árvore, o dedo à mão, a orelha à "
                "cabeça, etc.), base, raiz"
            ),
            4703: "como (de comparação), da mesma forma que",
            5468: "o amarelo, a cor amarela; a cor loura; a cor ruiva",
            8253: "intercalação",
            10757: (
                "farinha (feita pelos índios com raspas espremidas de raízes "
                "como a mandioca ou a macaxeira) (D'Abbeville, Histoire, 305)"
            ),
            9577: "sei lá! não sei (VLB, II, 47)",
        }
        for source_index, definition in expected.items():
            with self.subTest(source_index=source_index):
                self.assertIn(
                    definition,
                    self.capture(source_index)["semantic_outline"]["definitions"],
                )

        definitionless_suffix = self.capture(2312)
        self.assertEqual(definitionless_suffix["semantic_outline"]["definitions"], [])
        self.assert_pair(
            definitionless_suffix,
            "sepîaka",
            "vendo-o (Anch., Arte, 28v)",
        )

    def test_annotated_unnumbered_glosses_are_definition_spans(self):
        for source_index, (_key, expected_definition) in ANNOTATED_GLOSS_CASES.items():
            with self.subTest(source_index=source_index):
                self.assertEqual(
                    self.capture(source_index)["semantic_outline"]["definitions"],
                    [expected_definition],
                )

        # A bare part-of-speech marker is a section heading, not an annotated
        # definition preamble. This sentinel protects that distinction.
        self.assertIn(
            "Advérbio:", self.capture(3729)["semantic_outline"]["section_titles"]
        )

    def test_annotated_prefix_does_not_consume_numbered_sense_markers(self):
        expected_counts = {
            2851: 7,
            3766: 3,
            3767: 2,
            4114: 2,
            9410: 5,
            9413: 2,
        }
        for source_index, expected_count in expected_counts.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertEqual(
                    capture["preview_html"].count('class="sense-number"'),
                    expected_count,
                )
                self.assertTrue(
                    all(
                        "1)" not in definition
                        for definition in capture["semantic_outline"]["definitions"]
                    )
                )

    def test_related_entry_semicolons_remain_inside_glosses(self):
        expected_text = {
            2353: "de bravura, de terror; terror; força; bravura, etc.",
            2379: "variedade de bebida feita de milho; vinho de milho",
            5825: "osso fora do corpo, osso descarnado; espinha já fora do peixe",
            7219: "segundo; segunda vez",
            10757: "farinha feita de mandiopuba; bolas de farinha puba",
        }
        for source_index, text in expected_text.items():
            with self.subTest(source_index=source_index):
                self.assertIn(text, self.capture(source_index)["rendered_text"])

    def test_parenthetical_hyphens_and_citation_colons_stay_in_their_roles(self):
        self.assert_pair(
            self.capture(3744),
            "Abáp'akó é?",
            "Ora, quem seria aquele? (a mulher diz ri - v.) (VLB, II, 58)",
        )
        marangoty = self.capture(6624)
        related_gloss = (
            "marãngoty suí? - de que parte? de que lado? "
            "(mais específico que mamõ suí? - donde?) (VLB, I, 95)"
        )
        self.assertIn(related_gloss, marangoty["rendered_text"])
        self.assertNotIn("marãngoty suí?", quote_text(marangoty))
        self.assert_pair(
            self.capture(9400),
            "...Ybyramo i moingó-ukare'yma.",
            "Em terra não os fazendo transformar. (Ar., Cat., 179v)",
        )
        self.assert_pair(
            self.capture(9420),
            "Oîerokype asé Jesus 'ereme?",
            "Inclina-se a gente sempre quando diz Jesus? (Ar., Cat., 23)",
        )
        self.assert_pair(
            self.capture(9420),
            "Xe îekyîme, t'ereîu...",
            "Quando eu morrer, que venhas. (Anch., Poemas, 102)",
        )

    def test_implicit_first_senses_and_pos_continuations_have_boundaries(self):
        expected_definitions = {
            3372: [
                "ARAÇÁ-MIRIM, planta mirtácea (Psidium guineense Sw.)",
                "o fruto dessa árvore (Marcgrave, Hist. Nat. Bras., 62)",
            ],
            5790: [
                "CAMBUCÁ, árvore da família das mirtáceas (Plinia edulis (Vell.) Sobral)",
                "o fruto dessa árvore, de cor amarela, muito doce "
                "(Sousa, Trat. Descr., 197)",
            ],
            9852: ["porco (em geral) (VLB, II, 82)"],
        }
        for source_index, definitions in expected_definitions.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                for definition in definitions:
                    self.assertIn(
                        definition, capture["semantic_outline"]["definitions"]
                    )

        caapeba = self.capture(5667)
        self.assertEqual(len(caapeba["semantic_outline"]["definitions"]), 2)
        self.assertTrue(
            caapeba["semantic_outline"]["definitions"][1].startswith(
                "Designa também plantas da família das piperáceas"
            )
        )

        okyra = self.capture(8297)
        self.assertIn(
            "Adjetivo: okyr (r, s)", okyra["semantic_outline"]["section_titles"]
        )
        self.assertIn(
            "(xe) reverdecer (a planta) (VLB, II, 104)",
            okyra["semantic_outline"]["definitions"],
        )
        yaiba = self.capture(10993)
        self.assertIn(
            "Adjetivo: yaíb (r, t)", yaiba["semantic_outline"]["section_titles"]
        )
        self.assertIn("(xe) - fazer ondas", yaiba["rendered_text"])
        productive = self.capture(11219)
        self.assertEqual(
            productive["semantic_outline"]["section_titles"],
            ["Adjetivo: ybysopuku (r, s)"],
        )
        self.assertEqual(productive["diagnostics"]["sense_quote_count"], 0)

    def test_no_gloss_example_lists_are_all_cards(self):
        allomorph = self.capture(2782)
        self.assertEqual(allomorph["semantic_outline"]["definitions"], [])
        self.assert_pair(
            allomorph,
            "menama",
            "futuro marido (Anch., Arte, 34)",
        )

        aiyuba = self.capture(2569)
        self.assertEqual(aiyuba["semantic_outline"]["definitions"], ["ruivo"])
        self.assert_pair(aiyuba, "Xe aîub.", "Eu sou ruivo (VLB, II, 109)")
        self.assert_pair(
            aiyuba,
            "Xe rendybá-aîub.",
            "Eu tenho barba ruiva. (VLB, II, 109)",
        )

        suffix = self.capture(4601)
        self.assertEqual(suffix["semantic_outline"]["definitions"], [])
        self.assertEqual(suffix["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            suffix,
            "Emonãnamo, xe ruri...",
            "Portanto, eu vim. (Anch., Poemas, 100)",
        )

        swallow = self.capture(7223)
        self.assertEqual(swallow["semantic_outline"]["definitions"], [])
        self.assertEqual(swallow["diagnostics"]["sense_quote_count"], 5)
        self.assert_pair(
            swallow,
            "Sobaké Anhanga onheŷnhanga, i mokona motá...",
            "Diante deles os diabos ajuntando-se, querendo engoli-los. "
            "(Ar., Cat., 161v)",
        )

        causative = self.capture(4122)
        self.assertEqual(causative["semantic_outline"]["definitions"], [])
        self.assert_pair(
            causative,
            "Abebé kó ybytu îá; anonhan, arobebéne...",
            "Vôo como este vento; fá-los-ei correr comigo, fá-los-ei voar "
            "comigo... (Anch., Teatro, 40)",
        )
        self.assert_pair(
            causative,
            "...Xe anametá aroporaseî seru.",
            "Meus parentes trazendo, faço-os dançar comigo. " "(Anch., Poemas, 138)",
        )

        boastful = self.capture(7889)
        self.assertEqual(
            boastful["semantic_outline"]["section_titles"],
            ["Adjetivo: nhe'engapaparaíb"],
        )
        self.assert_pair(
            boastful,
            "Nde nhe'engapaparaípe mba'epoxy resé nde ma'enduaramo?",
            "Tu foste gabola, lembrando-te de coisas más? "
            "(Anch., Doutr. Cristã, II, 92)",
        )

    def test_malformed_brackets_recover_definition_and_example_boundaries(self):
        cases = {
            5308: (
                "lutar [apenas no plural] (com alguém: compl. com esé (r, s) ou ndi]",
                "Oroîoîtyîtyk Peró ndi (ou Peró resé).",
                "Lutei com Pedro. (VLB, II, 25)",
            ),
            6812: (
                "carregar-se, levar carga, ficar carregado (com algo: compl. com "
                "esé (r, s)]",
                "Ambosyî ahẽ resé.",
                "Fiquei carregado com ele (isto é, carreguei-o, levei-o às costas). "
                "(VLB, I, 67)",
            ),
            8032: (
                "combinar, concertar, tratar [sobre algo, de algo: compl. com esé (r, s)]",
                "...Aîpó tekoagûama resé o nhemongetá e'ymebé.",
                "Antes de tratar sobre aquele procedimento. (Ar., Cat., 279)",
            ),
            10558: (
                "TUPINIQUIM, TUPINAQUI, nome de nação indígena ou indivíduo dessa nação",
                "Soryb, xe îabé, xe ruba tupinakyîa.",
                "Está alegre, como eu, meu pai tupiniquim. (Anch., Poemas, 110)",
            ),
        }
        for source_index, (definition, tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(definition, capture["semantic_outline"]["definitions"])
                self.assert_pair(capture, tupi, portuguese)

    def test_definition_like_hyphens_are_not_promoted_to_examples(self):
        adverb = self.capture(3025)
        self.assertEqual(adverb["diagnostics"]["sense_quote_count"], 0)
        self.assertIn("outra parte; acolá; anõîa suí - de lá", adverb["rendered_text"])

        cross_reference = self.capture(4374)
        self.assertEqual(cross_reference["diagnostics"]["sense_quote_count"], 0)
        self.assertIn("alomorfe de ram - v.", cross_reference["rendered_text"])

        portuguese_control = self.capture(6212)
        self.assertEqual(portuguese_control["diagnostics"]["sense_quote_count"], 1)
        self.assertIn(
            "Abalei-me. Afrouxei. (VLB, I, 17)",
            portuguese_control["rendered_text"],
        )
        self.assertNotIn("Abalei-me.", quote_text(portuguese_control))

    def test_compact_and_embedded_dialogues_keep_turn_boundaries(self):
        incitement = self.capture(2622)
        self.assert_pair(
            incitement,
            "Akaîgûá! Ne'ĩ, t'asó nde irũmo, ta xe rembiá...",
            "Eia, hei de ir contigo, para que eu tenha presas... "
            "(Anch., Teatro, 64)",
        )
        self.assertIn("(V. tb. akaî e kaî.)", incitement["rendered_text"])
        self.assertNotIn("(V. tb. akaí e kaí.)", quote_text(incitement))

        self.assert_dialogue(
            self.capture(3897),
            [
                "💬 Mba'e i 'upyra resé nhõpe asé îeruréû Tupã supé?",
                "🗨️ Aani; amboaé o ekotebẽsaba resé bé...",
            ],
            [
                "Só pelas coisas que são comidas a gente pede a Deus?",
                "Não; também por suas outras necessidades. "
                "(Anch., Diál. da Fé, 227)",
            ],
        )

        self.assert_pair(
            self.capture(5274),
            'Marãpe Anhanga serekóû i moapysyka? "-Pe îu ipó, pe îó peẽ. '
            "Iîá, iîá\" e'i i xupé...",
            'Como o diabo os trata para consolá-los? "-Ui, ai de vós; bem '
            'feito, bem feito" diz para eles. (Ar., Cat., 159v)',
        )

        self.assert_dialogue(
            self.capture(6456),
            ["💬 (I) ybaté-katupe?", "🗨️ Mahmõ!"],
            ["Elas são muito altas?", "Demais! (Léry, Histoire, 363)"],
        )

    def test_compact_translation_dashes_after_punctuation_are_recovered(self):
        cases = {
            4080: (
                "Erĩ! Xe rapy Tupã, o boîá repyka nhẽ.",
                "Ai! Queima-me Deus, vingando seu servo. (Anch., Teatro, 90)",
            ),
            4120: (
                "...Peẽ bé ybŷá pe tymagûama na peîkuabi, \"-rimba'e ipó ixénone\" 'ee'yma?",
                "Vós também não reconheceis que vos enterrarão, não dizendo "
                '"-futuramente serei eu também"? (Ar., Cat., 155v)',
            ),
            5201: (
                "Mobype asé ikó mosanga rarine?",
                "Quantas vezes a gente tomará esse remédio? "
                "(Anch., Doutr. Cristã, I, 208)",
            ),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_related_glosses_stop_before_cited_examples(self):
        cases = {
            2739: (
                "aquele (es, a, as), esse (es, a, as), aquilo, isso",
                "Akó 'y asé reté moîasuka îabé, akûeîa îabé.",
                "Assim como esta água lava o corpo da gente, aquela também "
                "(lava). (Anch., Doutr. Cristã, I, 201)",
            ),
            3571: (
                "fingir que, fazer que",
                "Asó-asó-a'ub.",
                "Finjo que vou. (Anch., Arte, 35)",
            ),
            7170: (
                "o que é (ou deve ser) colocado, posto, encarregado, etc.",
                "Abaré asé rerekoaramo i moingopyra.",
                "O padre que é colocado como guardião da gente. (Ar., Cat., 94)",
            ),
            7785: (
                "lugar, tempo, companhia, resultado, etc. de castigar, de açoitar",
                "Oîaratã serã i aoba i nupãsagûera i moperé-perebagûera resé?",
                "Pegou-se fortemente sua roupa com que ele foi castigado por o "
                "ficarem ferindo? (Ar., Cat., 62)",
            ),
        }
        for source_index, (gloss, tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(gloss, capture["rendered_text"])
                self.assert_pair(capture, tupi, portuguese)
                self.assertFalse(
                    any(
                        line.startswith(gloss)
                        for line in quote_text(capture).splitlines()
                    )
                )

        triple_dash_cases = {
            4190: (
                "Xe resá-kûá-rorẽ.",
                "Eu tenho olhos encovados",
            ),
            6145: (
                "Oîabyeté seté tiruã oîkuabe'ymba'e.",
                "Transgride-os muito o que não conhece sequer sua substância. "
                "(Bettendorff, Compêndio, 103)",
            ),
            9399: (
                "Aîkó ramõ anga resé.",
                "Sou novato nisto. (VLB, II, 51)",
            ),
        }
        for source_index, (tupi, portuguese) in triple_dash_cases.items():
            with self.subTest(source_index=source_index):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_cited_pairs_with_omitted_translation_dash_are_bounded(self):
        recovered = {
            3412: (
                "Endé-te, nde resemõ arinhama, taîasu.",
                "Mas a ti, sobram-te galinhas e porcos. (Anch., Poemas, 152)",
            ),
            3740: ("Aindé.", "Estou à parte. (Anch., Arte, 58)"),
            4398: (
                "Nde robaké ûigûapyka...",
                "Diante de ti sentando-me. (Anch., Poemas, 96)",
            ),
            4521: ("Pero gûy!", "Ó Pedro! (VLB, II, 60)"),
            6368: (
                "Ené, rõ, kururu-asyka!",
                "Eia, pois, sapo maneta! (Anch., Teatro, 42)",
            ),
            6811: (
                "Na xe poromborybi.",
                "Eu não sou tolerante com as pessoas. (VLB, II, 114)",
            ),
            6859: (
                "N'i tybi tugûy nde membyrasápe.",
                "Não houve sangue em teu parto. (Anch., Poemas, 118)",
            ),
        }
        for source_index, (tupi, portuguese) in recovered.items():
            with self.subTest(source_index=source_index):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_shared_citations_are_copied_to_each_complete_pair(self):
        cases = {
            2844: [
                ("Anhamĩ.", "Espremi-o. (VLB, I, 127)"),
                ("Aty-amĩ.", "Espremi o sumo dela. (VLB, I, 127)"),
            ],
            3729: [
                (
                    "A'é byter aîpó gûi'îabo.",
                    "Ainda digo isso. (VLB, II, 74)",
                ),
                (
                    "E'i byté-byterĩ ahẽ xe amotare'yma.",
                    "Ainda, ainda me odeia fulano. (VLB, II, 74)",
                ),
            ],
            5202: [
                ("Kó taba pupé aîkó.", "Moro nesta aldeia. (VLB, II, 41)"),
                (
                    "Aîkó iké xe roka pupé.",
                    "Moro aqui em minha casa. (VLB, II, 41)",
                ),
                ("Aîkó Pero irũnamo.", "Moro com Pedro. (VLB, II, 41)"),
            ],
            8926: [
                (
                    "I porambyrambyk xe rekó ixébo.",
                    "São-me agradáveis meus afazeres. (VLB, I, 71)",
                ),
                (
                    "I porambyrambykĩ xe nhemosaraîa ixébo.",
                    "Estava-me agradável meu jogo. (VLB, I, 71)",
                ),
            ],
        }
        for source_index, pairs in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                for tupi, portuguese in pairs:
                    self.assert_pair(capture, tupi, portuguese)

    def test_editorial_leads_stay_outside_source_lines(self):
        cases = {
            4953: (
                "o mesmo que e'ikatu [3ª p. do indic. de 'ikatu / 'ekatu (v.)]",
                "I'ekatupe abaregûasu Papa angaîpaba resé nhyrõ me'enga asébo?",
                "Pode o bispo Papa dar para a gente o perdão dos pecados? "
                "(Bettendorff, Compêndio, 57)",
            ),
            5351: (
                "Pode aparecer com as partículas nhẽ ou bé",
                "Irũmo nhẽ aîkó (ou Irũmo bé aîkó).",
                "Estou com ele. (VLB, II, 114)",
            ),
            5352: (
                "Faz cair o pronome i antes de si: i irũnamo → irũnamo - com ele",
                "Irũnamo aîkó.",
                "Estou com ele. (VLB, I, 20)",
            ),
            9461: (
                "Pode ser acompanhado no período por ko'yté",
                "Rumby ahẽ oú ko'yté.",
                "Finalmente ele vem. (VLB, II, 115)",
            ),
        }
        for source_index, (lead, tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(lead, capture["rendered_text"])
                self.assertNotIn(lead, quote_text(capture))
                self.assert_pair(capture, tupi, portuguese)

    def test_annotations_and_internal_dashes_keep_their_semantic_roles(self):
        asy = self.capture(3483)
        gerund_note = "Também se emprega com o gerúndio."
        self.assertIn(gerund_note, asy["rendered_text"])
        self.assertNotIn(gerund_note, quote_text(asy))
        self.assert_pair(
            asy,
            "Sasy-eté ahẽ osóbo.",
            "É doloroso ir-se fulano. (VLB, II, 75)",
        )

        self.assert_pair(
            self.capture(6529),
            "...Manhana, sygûaraîy - n'aîpotari abá seîara.",
            "Alcovitice, prostituição - não quero que ninguém as deixe. "
            "(Anch., Teatro, 8)",
        )
        self.assert_pair(
            self.capture(7181),
            "Xe moîoîab ikó xe ra'yra.",
            "Este meu filho iguala-me; este meu filho é de meu tamanho " "(VLB, II, 9)",
        )
        self.assert_pair(
            self.capture(9776),
            "Oîoirundy tekó sykaba... - og orypápe Tupã asébe tekobé "
            "opaba'erame'yma me'enga i xykaba.",
            "Quatro são os últimos dos fatos: o último deles é Deus dar para a "
            "gente, em seu paraíso, a vida que não acabará. (Ar., Cat., 154v)",
        )

    def test_malformed_category_delimiters_still_expose_examples(self):
        cases = {
            4888: (
                "Emonã i'e ra'e.",
                "Dizem que é assim. (VLB, I, 104)",
            ),
            6444: (
                "Ema'enãngatu xe ri, xe mbo'are'ymuká.",
                "Vela bem por mim, fazendo que não me derrubem. "
                "(Anch., Poemas, 142)",
            ),
            6458: (
                "Osekyî kunhã maîé Karûara.",
                "Invocam as mulheres o pajé Caruara. (Anch., Teatro, 148)",
            ),
            9271: (
                '"Oú temõ ké kunhã xe posé", erépe, nde mba\'e-pymamo?',
                '"Oxalá viesse aqui uma mulher para o meu lado", disseste, '
                "tendo o teu membro ereto? (Anch., Doutr. Cristã, II, 93)",
            ),
            10356: (
                "Arasó tieté a'é.",
                "Tenho desgosto por o ter levado. (VLB, I, 43)",
            ),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_compact_two_turn_dialogue_keeps_both_languages_aligned(self):
        self.assert_dialogue(
            self.capture(7652),
            [
                "💬 Ma'epe ereîpotar?",
                "🗨️ ...Îetyka, komandaûasu, komandá-mirĩ, murukuîaûasu, " "ma'e tiruã.",
            ],
            [
                "Que queres?",
                "Batata-doce, favas grandes, feijões, laranjas, quaisquer "
                "coisas. (Léry, Histoire, 347)",
            ],
        )

    def test_variant_specific_source_citation_stays_with_its_tupi_variant(self):
        capture = self.capture(10341)
        self.assert_pair(
            capture,
            "T'otĩ umẽ... Îesu Cristo... mombegûabo.",
            "Que não se envergonhe de proclamar a Jesus Cristo. " "(Ar., Cat., 81)",
        )
        self.assert_pair(
            capture,
            "T'otĩ umẽ Îesu Cristo mombe'u resé...",
            "Que não se envergonhe de proclamar a Jesus Cristo. " "(Ar., Cat., 83v)",
        )
        self.assertEqual(
            capture["preview_html"].count('class="quote-variant-separator">ou</div>'),
            1,
        )

    def test_shared_gloss_and_translation_variants_are_complete_cards(self):
        cases = {
            3703: [
                ("kóbo", "nas roças (Anch., Arte, 42)"),
                ("kóbo", "pelas roças (Anch., Arte, 42v)"),
            ],
            5827: [
                ("ó-kanga", "armação de casa (VLB, I, 41)"),
                (
                    "ó-kangûama",
                    "madeira ou armação para futura casa (VLB, I, 41)",
                ),
            ],
            7700: [
                (
                    "Na xe ruba ruã ymã",
                    "Tomara fosse meu pai aqui (VLB, II, 47)",
                ),
                (
                    "Na xe ruba ruã iké ymã",
                    "Tomara fosse meu pai aqui (VLB, II, 47)",
                ),
            ],
            9596: [
                (
                    "kûara sembaba",
                    "lugar de sair do sol, o nascente (VLB, II, 46)",
                ),
                (
                    "kûarasy sembaba",
                    "a saída do sol, o nascer do sol (VLB, II, 46)",
                ),
            ],
        }
        for source_index, pairs in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                for tupi, portuguese in pairs:
                    self.assert_pair(capture, tupi, portuguese)

    def test_related_headword_glosses_remain_prose(self):
        cases = {
            2420: ["a'e remebé", "a'e remengatutenhẽ"],
            2996: ["anhẽ ra'upe é?", "anhẽ ra'upe re'i?"],
            5504: ["îukyre'ẽ", "îukyrapu'a"],
            5549: ["îuru-py-pyk"],
            6061: ["ko'emĩneme", "ko'emĩnemebé", "ko'ẽme"],
            6145: ["oîkuaba'e", "i kugûabypypabẽ", "i kuabypyre'yma"],
            8440: ["ũ-mbarab", "tĩ-mbarab", "pará-paraba"],
            9302: ["pyrybĩ", "pyrybĩ nhõte"],
            9701: ["-sûerĩ"],
            10159: ["-te nakó"],
        }
        for source_index, prose_headwords in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                tupi_lines = {
                    tupi
                    for quote in capture["semantic_outline"]["quotes"]
                    for tupi in quote["tupi"]
                }
                for headword in prose_headwords:
                    self.assertIn(headword, capture["rendered_text"])
                    self.assertNotIn(headword, tupi_lines)

        self.assertIn(
            "-sûerĩ - por um triz que não... (VLB, I, 19)",
            self.capture(9701)["rendered_text"],
        )
        self.assertIn(
            "-te nakó - mas antes (VLB, II, 32)",
            self.capture(10159)["rendered_text"],
        )

        self.assert_pair(
            self.capture(5549),
            "Aîuru-pyk.",
            "Tapei-lhe a boca (VLB, II, 124)",
        )
        self.assert_pair(
            self.capture(6061),
            "...Ko'ẽme gûemi'urama resé onhemosaînana...",
            "De manhã, cuidando de sua comida. (Ar., Cat., 11v)",
        )
        self.assert_pair(
            self.capture(8440),
            "tu'ĩîu-paraba",
            "tuim manchado de amarelo (nome de uma ave) "
            "(Theat. Rer. Nat. Bras., I, 171)",
        )

    def test_editorial_tails_stay_outside_quote_cards(self):
        cases = {
            2452: "(o mesmo que ãûa - v.)",
            5466: (
                "(O gerúndio tem forma irregular na 1ª pess. do sing.: "
                "gûitupa - estando eu deitado.)"
            ),
        }
        for source_index, note in cases.items():
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertIn(note, capture["rendered_text"])
                self.assertNotIn(note, quote_text(capture))

    def test_definitionless_and_prefix_entries_expose_their_first_examples(self):
        cases = {
            3805: ("Eîori, eîori!", "Vem, vem! (Carder, The Rel., 1188)"),
            4296: (
                "T'orogûerekó (leia-se torowerekó), setãme, nde pyri, tekó-puku.",
                "Que tenhamos, em sua terra, junto de ti, a vida eterna. "
                "(Anch., Teatro, 122)",
            ),
            4600: (
                "Marãpe nd'erenhemimi?",
                "Por que não te escondes? (Anch., Teatro, 32)",
            ),
            5316: (
                "Kaburé, îori enhana...",
                "Caburé, vem correndo! (Anch., Teatro, 64)",
            ),
            9469: (
                "N'aîpotari abá seîara.",
                "Não quero que os índios deixem isso. (Anch., Teatro, 10, 2006)",
            ),
            10756: (
                "...Nde robaké ûigûapyka...",
                "Diante de ti sentando-me eu. (Anch., Poemas, 96)",
            ),
            11091: (
                "Kó 'ara nungara pupé Santa Maria sóû o ykera amõ ybá "
                "Santa Isabel supa.",
                "Num dia semelhante a este, Santa Maria foi para visitar uma "
                "certa prima sua, Santa Isabel. (Ar., Cat., 6v)",
            ),
        }
        for source_index, (tupi, portuguese) in cases.items():
            with self.subTest(source_index=source_index):
                self.assert_pair(self.capture(source_index), tupi, portuguese)

    def test_numbered_definitions_drop_source_separator_dashes(self):
        for source_index in (2421, 2422, 5980, 6145, 9469):
            with self.subTest(source_index=source_index):
                capture = self.capture(source_index)
                self.assertTrue(capture["semantic_outline"]["definitions"])
                self.assertTrue(
                    all(
                        not definition.lstrip().startswith(("-", "–"))
                        for definition in capture["semantic_outline"]["definitions"]
                    )
                )

    def test_credits_form_a_non_overlapping_sticky_footer(self):
        initial = self.capture(2312)["initial_page_layout"]
        self.assertEqual(initial["credits_position"], "static")
        self.assertAlmostEqual(
            initial["credits"]["bottom"], initial["viewport_height"], delta=1
        )
        self.assertEqual(initial["document_height"], initial["viewport_height"])
        self.assertIsNotNone(initial["offline_link"])
        self.assertLessEqual(
            initial["offline_link"]["bottom"], initial["credits"]["top"]
        )

        expanded = self.capture(10757)["expanded_page_layout"]
        self.assertEqual(expanded["credits_position"], "static")
        self.assertGreater(expanded["document_height"], expanded["viewport_height"])
        self.assertLessEqual(expanded["entry"]["bottom"], expanded["main"]["bottom"])
        self.assertGreaterEqual(expanded["credits"]["top"], expanded["main"]["bottom"])
        self.assertAlmostEqual(
            expanded["credits"]["bottom"], expanded["document_height"], delta=1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
