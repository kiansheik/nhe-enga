from .orth import ALT_ORTS, get_nasality_î

import re, random
class TupiAntigo(object):
    cv_patterns = ["CVC", "CV", "VC", "V"]
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere", "oro", "îepé"],
        "2pp": ["peẽ", "pe", "pe", "opo", "peîepé"],
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
        "1ps": ["t", "ta"],
        "1ppi": ["t", "t"],
        "1ppe": ["t", "t"],
        "2ps": ["t", "ta"],
        "2pp": ["ta", "ta"],
        "3p": ["t", "ta"],
    }
    permissivo_anotado = {
        "1ps": ["t[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PREFIX:CONSONANT]"],
        "1ppi": ["t[PERMISSIVE_PREFIX:VOWEL]", "t[PERMISSIVE_PREFIX:VOWEL]"],
        "1ppe": ["t[PERMISSIVE_PREFIX:VOWEL]", "t[PERMISSIVE_PREFIX:VOWEL]"],
        "2ps": ["t[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PREFIX:CONSONANT]"],
        "2pp": ["ta[PERMISSIVE_PREFIX:CONSONANT]", "ta[PERMISSIVE_PREFIX:CONSONANT]"],
        "3p": ["t[PERMISSIVE_PREFIX:VOWEL]", "ta[PERMISSIVE_PREFIX:CONSONANT]"],
    }
    imperativo = {
        "2ps": ["e", "nde"],
        "2pp": ["pe", "pe"],
    }

    sound_graf = {
        "ipa": "p pʷ pʲ β t s sʷ k kʷ ʔ m mʷ n r ɲ ŋ mb mbʷ nd ndʷ ŋɡ ŋɡʷ g w w j ɨ a ˈa e ˈɛ i ˈi ɨ ˈɨ o ˈɔ u ˈu ã ɛ̃ ĩ ɨ̃ ɔ̃ ũ ʃ".split(
            " "
        ),
        "navarro": "p pû pî b t s sû k kû ' m mû n r nh ng mb mbû nd ndû ng ngû gû g û î ŷ a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ x".split(
            " "
        ),
    }
    def generate_html_table(self):
        table_header = "<tr><th>Navarro</th><th>IPA</th></tr>"
        table_rows = [
            f"<tr><td>{navarro}</td><td>{ipa}</td></tr>"
            for navarro, ipa in zip(self.sound_graf["navarro"], self.sound_graf["ipa"])
        ]
        table = f"<table>{table_header}{''.join(table_rows)}</table>"
        return table
    def generate_html_table_from_dict(self, data):
        headers = data.keys()
        table_header = "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        table_rows = [
            "<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"
            for values in zip(*data.values())
        ]
        table = f"<table>{table_header}{''.join(table_rows)}</table>"
        return table
    # Identify all non-ascii special chars in the navarro alphabet
    special_chars = list(enumerate("û î ŷ á é í ý ó ú ã ẽ ĩ ỹ õ ũ '".split(" ")))
    # Create a two-way dictionary
    special_chars_map = {char: index for index, char in list(enumerate(special_chars))+[(x,i)for i, x in list(enumerate(special_chars))]}

    def choose_perm(self, inp_str, on=False):
        if not on:
            return ""
        testr = inp_str[0]
        if testr in (self.vogais + self.semi_vogais):
            return "t[PERMISSIVE_PREFIX:VOWEL]"
        return "ta[PERMISSIVE_PREFIX:CONSONANT]"

    vogais = "a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ".split(" ")
    accented_vogais = "á é í ý ó ú ã ẽ ĩ ỹ õ ũ".split(" ")
    accent_map = {"á": "a",
                  "é": "e",
                    "í": "i",
                    "ý": "y",
                    "ó": "o",
                    "ú": "u",
                  }
    accent_map_reverse = {
        "a": "á", "e": "é", "i": "í", "y": "ý", "o": "ó", "u": "ú"
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
    nasais = "m n nh ng ã ẽ ĩ ỹ õ ũ mb nd".split(" ")
    consoantes = "p b t s x k ' m n r nh ng mb nd ng g û î ŷ".split(" ")
    vogais_nasais = list(set(vogais).intersection(set(nasais)))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orthographies = {
            "ipa": dict(sorted(
                [
                    (self.sound_graf["navarro"][i], self.sound_graf["ipa"][i])
                    for i in range(len(self.sound_graf["ipa"]))
                ],
                key=lambda x: len(x[0]),
                reverse=True,
            ))
        }
        self.ipa_map = self.orthographies["ipa"]
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

    def is_nasal(self, c):
        # check if c has any of self.nasais present inside of it
        return any(nasal in c for nasal in self.nasais)

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

    def add_accent(self, word=None):
        if not word:
            word = self.verbete
        # Find vowels in the word and their positions
        suffix = ""
        # if the word ends in -eme or -amo, remove the final two characters before passing through the process, save for later
        if True in [word.endswith(suf) for suf in ["eme", "amo"]]:
            suffix = word[-2:]
            word = word[:-2]
        if word[0] == "'":
            # If the word starts with a glottal stop, remove it
            word = word[1:]
        if word[-2:].startswith("'"):
            # If the penultimate character is a glottal stop, make the vowel following it accented and return
            return word[:-1] + self.accent_map_reverse.get(word[-1], word[-1]) + suffix
        vowels = [(i, c) for i, c in enumerate(word) if c in self.vogais + self.accented_vogais]
        if len(vowels) < 2:
            # If there are fewer than 2 vowels, no need to accent
            return word + suffix
        # Identify the last, penultimate, and antepenultimate vowels
        last_vowel_idx, last_vowel = vowels[-1]
        penultimate_vowel_idx, penultimate_vowel = vowels[-2]
        antepenultimate_vowel_idx, antepenultimate_vowel = vowels[-3] if len(vowels) > 2 else (None, None)
        if last_vowel in ["i", "u", "y"]:
            return word + suffix  # Assume it's already oxítona, no changes needed

        # Check if the last and antepenultimate vowels are unaccented
        if last_vowel not in self.accented_vogais and (antepenultimate_vowel is None or antepenultimate_vowel not in self.accented_vogais):
            # Determine if the penultimate vowel should be nasalized or accented
            if penultimate_vowel_idx + 1 < len(word) and word[penultimate_vowel_idx + 1:penultimate_vowel_idx + 3] in self.nasais:
                # Nasalize the penultimate vowel
                accented_vowel = self.nasal_map.get(penultimate_vowel, penultimate_vowel)
            else:
                # Add an acute accent to the penultimate vowel
                accented_vowel = self.accent_map_reverse.get(penultimate_vowel, penultimate_vowel)

            # Replace the penultimate vowel with its accented or nasalized form
            word = word[:penultimate_vowel_idx] + accented_vowel + word[penultimate_vowel_idx + 1:]

        return word + suffix

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
        return self.transliterate('ipa', inp=inp)
    
    def map_orthography(self, text, orth='anchieta_1'):
        if orth.lower() == 'ipa':
            orthography_map = self.ipa_map
        else:
            orthography_map = ALT_ORTS[orth.upper()]
        result = []
        i = 0
        while i < len(text):
            # Check for bracketed section
            if text[i] == '[':
                closing_bracket_index = text.find(']', i)
                if closing_bracket_index != -1:
                    # Append the entire bracketed section
                    result.append(text[i:closing_bracket_index + 1])
                    i = closing_bracket_index + 1
                    continue
                else:
                    # If no closing bracket is found, treat it as a normal character
                    result.append(text[i])
                    i += 1
                    continue

            # Existing logic for mapping orthography
            match = None
            match_length = 0
            for cluster, replacement in orthography_map.items():
                if text[i:i+len(cluster)].lower() == cluster and len(cluster) > match_length:
                    match = replacement
                    match_length = len(cluster)
            
            if match:
                result.append(match)
                i += match_length
            else:
                result.append(text[i])
                i += 1
        
        return ''.join(result)

    def transliterate(self, codex, inp=None):
        if inp is None:
            inp = self.verbete if type(self.verbete) == str else self.verbete()
        codex_map = list(self.orthographies[codex].items())
        sorted_clusters = sorted(codex_map, key=lambda x: len(x[0]), reverse=True)
        sorted_clusters = [x[0] for x in sorted_clusters]
        result_string = inp.replace("-", "")
        cluster_mapping = dict(codex_map)
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
        # Check if the last character is an accented vowel
        if input_string[-1] in self.nasal_map.keys():
            # Remove the accent from the last vowel
            return input_string[:-1] + self.nasal_map[input_string[-1]]
        return input_string
    def nasaliza_prefixo(self, input_string):
        if input_string[0] in self.nasal_prefix_map.keys():
            return  self.nasal_prefix_map[input_string[0]] + input_string[1:]
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
            
