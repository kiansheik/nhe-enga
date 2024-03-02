class TupiAntigo(object):
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere", "oro", "îepé"],
        "2pp": ["pe'ẽ", "pe", "pe", "opo", "peîepé"],
        "3p": ["a'e", "i", "o"],
        "refl": ["îe"],
        "mut": ["îo"],
    }

    gerundio = {
        "1ps": ["gûi"],
        "1ppi": ["îa"],
        "1ppe": ["oro"],
        "2ps": ["e"],
        "2pp": ["pe"],
        "3p": [
            "o",
        ],
    }

    permissivo = {
        "1ps": ["t'", "ta "],
        "1ppi": ["t'", "t'"],
        "1ppe": ["t'", "t'"],
        "2ps": ["t'", "ta "],
        "2pp": ["ta ", "ta "],
        "3p": ["t'", "ta "],
    }
    permissivo_anotado = {
        "1ps": ["t'[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PARTICLE:CONSONANT] "],
        "1ppi": ["t'[PERMISSIVE_PREFIX:VOWEL]", "t'[PERMISSIVE_PREFIX:VOWEL]"],
        "1ppe": ["t'[PERMISSIVE_PREFIX:VOWEL]", "t'[PERMISSIVE_PREFIX:VOWEL]"],
        "2ps": ["t'[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PARTICLE:CONSONANT] "],
        "2pp": ["ta[PERMISSIVE_PARTICLE:CONSONANT] ", "ta[PERMISSIVE_PARTICLE:CONSONANT] "],
        "3p": ["t'[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PARTICLE:CONSONANT] "],
    }
    imperativo = {
        "2ps": ["e-", "nde "],
        "2pp": ["pe-", "pe "],
    }

    sound_graf = {
        "ipa": "p pʷ pʲ β t s sʷ k kʷ ʔ m mʷ n r ɲ ŋ mb mbʷ nd ndʷ ŋɡ ŋɡʷ g w w j ɨ a ˈa e ˈɛ i ˈi ɨ ˈɨ o ˈɔ u ˈu ã ɛ̃ ĩ ɨ̃ ɔ̃ ũ ʃ".split(
            " "
        ),
        "navarro": "p pû pî b t s sû k kû ' m mû n r nh ng mb mbû nd ndû ng ngû gû g û î ŷ a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ x".split(
            " "
        ),
    }

    vogais = "a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ".split(" ")
    nasais = "m n ng ã ẽ ĩ ỹ õ ũ".split(" ")
    vogais_nasais = list(set(vogais).intersection(set(nasais)))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ipa_map = sorted(
            [
                (self.sound_graf["navarro"][i], self.sound_graf["ipa"][i])
                for i in range(len(self.sound_graf["ipa"]))
            ],
            key=lambda x: len(x[0]),
            reverse=True,
        )
        self.siliba_map = sorted(
            [
                (
                    self.sound_graf["navarro"][i],
                    "V" if self.sound_graf["navarro"][i] in self.vogais else "C",
                )
                for i in range(len(self.sound_graf["navarro"]))
            ],
            key=lambda x: len(x[0]),
            reverse=True,
        )
    def ends_with(self, word, citeria):
        return any(word.endswith(citerium) for citerium in citeria)
