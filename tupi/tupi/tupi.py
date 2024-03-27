import re, random
class TupiAntigo(object):
    cv_patterns = ["CVC", "CV", "VC", "V"]
    personal_inflections = {
        "1ps": ["ixé", "xe", "a-"],
        "1ppi": ["îandé", "îandé", "îa-"],
        "1ppe": ["oré", "oré", "oro-"],
        "2ps": ["endé", "nde", "ere-", "oro-", "îepé"],
        "2pp": ["peẽ", "pe", "pe-", "opo-", "peîepé"],
        "3p": ["a'e", "i", "o-"],
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
    # Identify all non-ascii special chars in the navarro alphabet
    special_chars = list(enumerate("û î ŷ á é í ý ó ú ã ẽ ĩ ỹ õ ũ '".split(" ")))
    # Create a two-way dictionary
    special_chars_map = {char: index for index, char in list(enumerate(special_chars))+[(x,i)for i, x in list(enumerate(special_chars))]}

    vogais = "a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ".split(" ")
    accent_map = {"á": "a",
                  "é": "e",
                    "í": "i",
                    "ý": "y",
                    "ó": "o",
                    "ú": "u",
                  }
    nasal_prefix_map = {
        "p": "mb",
        "k": "ng",
        "t": "nd",
        "s": "nd",
    }
    nasal_map = {"á": "ã",
                "é": "ẽ",
                "í": "ĩ",
                "ý": "ỹ",
                "ó": "õ",
                "ú": "ũ",
                "a": "ã",
                "e": "ẽ",
                "i": "ĩ",
                "y": "ỹ",
                "o": "õ",
                "u": "ũ",
                } 
    semi_vogais = "û î ŷ".split(" ")
    nasais = "m n ng ã ẽ ĩ ỹ õ ũ".split(" ")
    consoantes = "p b t s k ' m n r nh ng mb nd ng g û î ŷ".split(" ")
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
    
    def remove_brackets_and_contents(self, s):
        return re.sub(r'\[.*?\]', '', s)
    def keep_brackets_contents(self, s):
        return ''.join(re.findall(r'(\[.*?\])', s))
    def simplify_tags(self, s):
        # Find all brackets and their contents
        brackets_contents = re.findall(r'\[.*?\]', s)

        # Iterate over each match
        for match in brackets_contents:
            # Remove the brackets and split the contents
            split_content = "["+match[1:-1].split(':')[0]+"]"
            # Replace the original match with the split content
            s = s.replace(match, split_content)
        return s

    def remove_parens_and_contents(self, s):
        return re.sub(r'\(.*?\)', '', s)

    def fix_phonetics(self, input_str):
        replacements = {
            "is": "ix",
            "i s": "i x",
            "nn": "n",
            "oer": "ogûer",
            "oen": "ogûen",
            "îeer": "îer",
            "îî": "î",
            "ee": "e",
            "  ": " ",
            "-": "",
            "'û": "gû",
        }

        # Split the string into parts inside and outside of brackets
        parts = re.split(r'(\[.*?\])', input_str.strip())

        # Apply replacements only to parts outside of brackets
        for i in range(len(parts)):
            if not parts[i].startswith('['):
                for b4, aft in replacements.items():
                    parts[i] = parts[i].replace(b4, aft)

        # Reassemble the string
        new_str = ''.join(parts)

        return new_str.strip()

    def silibas(self):
        silibas = self.siliba_string()
        num = 0
        while silibas != "":
            for pattern in self.cv_patterns:
                if silibas[: len(pattern)] == pattern:
                    num += 1
                    silibas = silibas[len(pattern) :]
                    break
            else:  # No match found
                silibas = silibas[1:]
        return num

    def monosilibica(self):
        return self.silibas() == 1
    def siliba_string(self, inp=None):
        if inp is None:
            inp = self.verbete if type(self.verbete) == str else self.verbete()
        sorted_clusters = [x[0] for x in self.siliba_map]
        result_string = inp.replace("-", "")
        cluster_mapping = dict(self.siliba_map)
        replaced_positions = set()

        for cluster in sorted_clusters:
            replacement = cluster_mapping[cluster]
            start = 0

            while start < len(result_string):
                position = result_string.find(cluster, start)

                if position == -1:
                    break

                # Check for collisions with previous replacements
                if any(
                    pos in replaced_positions
                    for pos in range(position, position + len(cluster))
                ):
                    start = position + 1
                    continue

                result_string = (
                    result_string[:position]
                    + replacement
                    + result_string[position + len(cluster) :]
                )
                replaced_positions.update(range(position, position + len(replacement)))
                start = position + len(replacement)

        return result_string

    def ipa(self, inp=None):
        if inp is None:
            inp = self.verbete if type(self.verbete) == str else self.verbete()
        sorted_clusters = [x[0] for x in self.ipa_map]
        result_string = inp.replace("-", "")
        cluster_mapping = dict(self.ipa_map)
        replaced_positions = set()

        for cluster in sorted_clusters:
            replacement = cluster_mapping[cluster]
            start = 0

            while start < len(result_string):
                position = result_string.find(cluster, start)

                if position == -1:
                    break

                # Check for collisions with previous replacements
                if any(
                    pos in replaced_positions
                    for pos in range(position, position + len(cluster))
                ):
                    start = position + 1
                    continue

                result_string = (
                    result_string[:position]
                    + replacement
                    + result_string[position + len(cluster) :]
                )
                replaced_positions.update(range(position, position + len(replacement)))
                start = position + len(replacement)

        return result_string

    def accent_last_vowel(self, input_string):
        vowels = "aeiyou"

        # Check if the last character is a vowel
        if input_string[-1] in vowels:
            # Accent the last vowel
            return input_string[:-1] + input_string[-1] + "́"
        return input_string

    def remove_accent_last_vowel(self, input_string):
        vowels = "áéíýóú"
        # Check if the last character is an accented vowel
        if input_string[-1] in vowels:
            # Remove the accent from the last vowel
            return input_string[:-1] + self.accent_map[input_string[-1]]
        return input_string
    def nasaliza_final(self, input_string):
        vowels = "áéíýóú"
        # Check if the last character is an accented vowel
        if input_string[-1] in self.nasal_map.keys():
            # Remove the accent from the last vowel
            return input_string[:-1] + self.nasal_map[input_string[-1]]
        return input_string
    # Define a function which returns a randomly generated tupi antigo string between 1 and 3 syllables
    def random_tupi_antigo(self):
        # Define a list of possible syllable patterns
        syllable_patterns = self.cv_patterns
        # Define a list of consonants and vowels
        consonants = self.consoantes
        vowels = list(set(self.vogais) - set("á é í ý ó ú".split(" ")))
        # Generate a random number of syllables between 1 and 3
        num_syllables = random.randint(1, 3)
        res = ""
        letter = ""
        # Generate the specified number of syllables
        for _ in range(num_syllables):
            # Generate a random syllable pattern
            pattern = random.choice([x for x in syllable_patterns if letter == "" or not x.startswith(letter)])
            for letter in pattern:
                if letter == "C":
                    res += random.choice(consonants)
                else:
                    res += random.choice(vowels)

        # Join the syllables together and return the result
        no_glottal_end = res if "'" != res[-1] else res[:-1]
        tonic = self.tonic_vowel(no_glottal_end)
        return self.fix_phonetics(tonic)

    # function to make a single random vowel in a string tonic if none have accents already
    def tonic_vowel(self, input_string):
        vowels = []
        v_map = {
            'a':'á',
            'e':'é',
            'i':'í',
            'y':'ý',
            'o':'ó',
            'u':'ú' 
        }
        for i, x in enumerate(input_string):
            if x in self.vogais_nasais:
                return input_string
            if x in self.vogais:
                vowels.append(i)
        tonic = random.choice(vowels)
        tonic_str = input_string[:tonic] + v_map[input_string[tonic]] + input_string[tonic + 1 :]
        return random.choice([input_string, tonic_str])
    
    # function to make a single random vowel in a string tonic if none have accents already
    def recreate_annotated(self):
        matches = re.findall(r'Noun\(\"([^\"]+)\", \"([^\"]+)\"\)((?:\.[^\)]+\))*)', self.recreate)
        vbt = matches[0]
        defn = matches[0][1]
        fns = ''
        for match in matches[0][2:]:
            for fn in match[1:].split('.'):
                fns += f"[{fn}]".replace("'", '"')
        out_str = f"{vbt[0]}[{defn}]{fns}"
        return out_str
            
