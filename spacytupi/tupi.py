import spacy


class TupiAntigo(spacy.language.Language):
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere", "oro", "îepé"],
        "2pp": ["pe'ẽ", "pe", "pe", "opo", "peîepé"],
        "3p": ["a'e", "i", "o"],
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

    def inflect_verb(self, verb, inflection):
        inf = self.personal_inflections[inflection]
        return f"{inf[0]} {inf[2]}{verb}"


class Verb(TupiAntigo):
    def __init__(self, verbete, verb_class, raw_definition, vid=None):
        super().__init__()
        self.verbete = verbete  # The name of the verb in its dictionary form
        self.substantivo = f"{verbete}{'a' if verbete[-1] not in self.vogais else ''}"
        self.verb_class = verb_class  # Class of the verb (string)
        self.transitivo = "v.tr." in verb_class.replace(
            " ", ""
        )  # Whether the verb is transitive (boolean)
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.pluriforme = (
            "(s)" in self.verb_class
            or "(r, s)" in self.verb_class
            or "-s-" in self.verb_class
        )
        self.ios = "-îo-" in self.verb_class and "-s-" in self.verb_class
        self.segunda_classe = (
            "2ª classe" in self.verb_class or "adj." in self.verb_class
        )
        self.ero = self.verbete.startswith("ero") or self.verbete.startswith("eno")
        self.vid = vid

    def silibas(self):
        silibas = self.siliba_string()
        patterns = ["CVC", "CV", "VC", "V"]
        num = 0
        while silibas != "":
            for pattern in patterns:
                if silibas[: len(pattern)] == pattern:
                    num += 1
                    silibas = silibas[len(pattern) :]
                    break
        return num

    def monosilibica(self):
        return self.silibas() == 1

    def siliba_string(self, inp=None):
        if inp is None:
            inp = self.verbete
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
            inp = self.verbete
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

    def object_marker(self):
        return (
            ""
            if self.ero
            else "îos"
            if self.ios
            else "s"
            if self.pluriforme
            else "îo"
            if self.monosilibica()
            else "î"
        )

    def accent_last_vowel(self, input_string):
        vowels = "aeiyou"

        # Check if the last character is a vowel
        if input_string[-1] in vowels:
            # Accent the last vowel
            return input_string[:-1] + input_string[-1] + "́"
        return input_string

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
        }
        new_str = input_str
        for b4, aft in replacements.items():
            new_str = new_str.replace(b4, aft)
        return new_str
    
    def negate_verb(self, result):
        if result[0] in TupiAntigo.vogais or result[0] == 'î':
            result = f"n'{result}"
        else:
            result = f"na {result}"
        if result[-1] == 'i' or result[-1] == 'î':
            result = f"{result[:-1]}î"
        elif result[-1] in TupiAntigo.vogais:
            result = f"{result}î"
        else:
            result = f"{result}i"
        return result

    def conjugate(
        self,
        subject_tense="1ps",
        object_tense=None,
        dir_obj_raw=None,
        mode="indicativo",
        pos="anteposto",
        pro_drop=False,
        io_pref=False,
        negative=False,
    ):
        perm_suf = ["", ""]
        if mode == "permissivo":
            perm_suf = self.permissivo[subject_tense]

        if mode == "gerundio":
            if not self.segunda_classe:
                subj = self.personal_inflections[subject_tense][0]
                suf = "bo"
                vbt = self.verbete
                if self.verbete[-1] in self.nasais and self.verbete[-1] in self.vogais:
                    suf = "mo"
                if self.verbete[-1] in "i í y ý u ú ĩ ỹ ũ":
                    suf = f"a{suf}"
                elif self.verbete[-1] == "b":
                    suf = "pa"
                    vbt = vbt[:-1]
                elif self.verbete[-1] == "r":
                    suf = ""
                    vbt = self.accent_last_vowel(vbt[:-1])
                elif self.verbete[-1] not in self.vogais:
                    suf = "a"
                if not self.transitivo:
                    pref = f"{f'{subj} ' if not pro_drop else ''}{self.gerundio[subject_tense][0]}-"
                else:
                    dir_obj = (
                        f"{self.personal_inflections[object_tense][1]}"
                        if dir_obj_raw is None
                        else dir_obj_raw
                    )
                    if subject_tense == object_tense:
                        dir_obj = "îe-"
                    else:
                        if dir_obj == "i":
                            if self.pluriforme or self.ero:
                                dir_obj = "s-"
                            elif self.monosilibica():
                                dir_obj = "îo-"
                        else:
                            dir_obj += f' {"r-" if self.pluriforme or self.ero else ""}'
                    pref = dir_obj
                # TODO: modify last sound of verbete in accordance with gerundio
                result = f"{pref}{vbt}{suf}"
            else:
                subj = (
                    self.personal_inflections[subject_tense][1]
                    if "3p" not in subject_tense
                    else "o"
                )
                suf = "amo"
                vbt = self.verbete
                if self.verbete[-1] in self.nasais and self.verbete[-1] in self.vogais:
                    suf = "namo"
                elif self.verbete[-1] in self.vogais:
                    suf = "ramo"
                # TODO: modify last sound of verbete in accordance with gerundio (annamo -> ãnamo)
                pluriforme = ""
                if self.pluriforme and "3p" not in subject_tense:
                    pluriforme += "r-"
                result = f"{subj} {pluriforme}{vbt}{suf}"
        elif "2p" not in subject_tense and mode == "circunstancial":
            subj = self.personal_inflections[subject_tense][1]
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense:
                    subj = self.personal_inflections[subject_tense][0]
                if subject_tense == object_tense:
                    obj = "îe"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1]
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}"
                    )
                    if self.pluriforme or self.ero:
                        if obj == "i":
                            obj = "s-"
                        else:
                            obj = f"{obj} r-"
                    else:
                        obj += " "
            circ = (
                ""
                if self.verbete[-1] in "ûuũî"
                else "û"
                if self.verbete[-1] in self.vogais
                else "i"
            )
            if self.pluriforme and not self.transitivo:
                if "3p" in subject_tense:
                    obj = "x-"
                    subj = ""
                else:
                    obj += "r-"
            result = f"{subj} {obj}{self.verbete}{circ}"
        elif self.segunda_classe:
            subj = self.personal_inflections[subject_tense][1]
            pluriforme = ""
            if self.pluriforme:
                if "3p" in subject_tense:
                    pluriforme = "x-"
                    subj = ""
                else:
                    pluriforme = "r-"
            vb =  f"{pluriforme}{self.verbete}"
            result = f"{perm_suf[1]}{subj} {vb}"
            if negative:
                result = self.negate_verb(result)
        elif not self.segunda_classe and not self.transitivo:
            subj = self.personal_inflections[subject_tense][0] if not pro_drop else ""
            conj = (
                self.imperativo[subject_tense][0]
                if (mode == "imperativo" and "2p" in subject_tense)
                else self.personal_inflections[subject_tense][2]
            )
            vb = f"{perm_suf[0]}{conj}-{self.verbete}"
            if negative:
                vb = self.negate_verb(vb)
            result = f"{subj} {vb}"
        elif self.transitivo:
            if pos not in ["posposto", "incorporado", "anteposto"]:
                raise Exception("Position Not Valid")
            if object_tense in self.personal_inflections.keys():
                if object_tense == subject_tense:
                    subj = (
                        self.personal_inflections[subject_tense][1]
                        if not pro_drop
                        else ""
                    )
                    conj = (
                        self.imperativo[subject_tense][0]
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2]
                    )
                    obj = "îe" if not io_pref else "îo"
                    vb = f"{perm_suf[0]}{conj}-{obj}-{self.verbete}"
                    if negative:
                        vb = self.negate_verb(vb)
                    result = f"{subj} {vb}"
                elif "3p" in object_tense:
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        if not pro_drop
                        else ""
                    )
                    conj = (
                        self.imperativo[subject_tense][0]
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2]
                    )
                    dir_obj = (
                        self.personal_inflections["3p"][0]
                        if dir_obj_raw is None
                        else dir_obj_raw
                    )
                    vbt = (
                        self.verbete[1:]
                        if self.ero and subject_tense in ["1ps", "1ppi", "2ps", "2pp"]
                        else self.verbete
                    )
                    pluriforme = self.object_marker()
                    if pos == "posposto":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb)
                        result = (
                            f"{subj} {vb} {dir_obj}"
                        )
                    elif pos == "anteposto":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb)
                        result = (
                            f"{subj} {dir_obj} {vb}"
                        )
                    elif pos == "incorporado":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme if dir_obj_raw is None else dir_obj}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb)
                        result = f"{subj} {vb}"
                if "2p" in object_tense:
                    if "1p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][1]
                            if not pro_drop
                            else ""
                        )
                        obj = self.personal_inflections[object_tense][3]
                        result = f"{perm_suf[0]}{obj}-{self.verbete}"
                        if negative:
                            result = self.negate_verb(result)
                        result = f"{subj} {result}"
                        
                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = self.personal_inflections[subject_tense][4]
                        obj = self.personal_inflections[object_tense][1]
                        pluriforme = "r-" if self.pluriforme or self.ero else ""
                        perm_suf = (
                            self.permissivo[object_tense]
                            if mode == "permissivo"
                            else ["", ""]
                        )
                        vb = f"{perm_suf[1]}{obj} {pluriforme}{self.verbete}"
                        if negative:
                            vb = self.negate_verb(vb)
                        result = f"{vb} {subj}"
                if "2p" in object_tense or "1p" in object_tense:
                    if "3p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0]
                            if dir_obj_raw is None
                            else dir_obj_raw
                        )
                        obj = self.personal_inflections[object_tense][1]
                        pluriforme = "r-" if self.pluriforme or self.ero else ""
                        perm_suf = (
                            self.permissivo[object_tense]
                            if mode == "permissivo"
                            else ["", ""]
                        )
                        vb = f"{perm_suf[1]}{obj} {pluriforme}{self.verbete}"
                        if negative:
                            vb = self.negate_verb(vb)
                        result = f"{vb} {subj}"
        # else:
        #     return "Invalid/Unimplemented tense"
        result = self.fix_phonetics(result.strip().replace("-", ""))
        print(
            f"({subject_tense} -> {object_tense}):",
            f"\t",
            result.strip().replace("-", ""),
            "\t",
        )
        # self.ipa(result.strip().replace("-", ""))
        return result.strip()


if __name__ == "__main__":
    lang = TupiAntigo()
    # Example usage:
    verb_example = Verb("apysyk", "adj.: ", True, "gostar")
    print(lang.inflect_verb("nhe'eng", "1ppi"))
    print(verb_example.conjugate("1ps"))
    print(verb_example.conjugate("1ppi"))
    print(verb_example.conjugate("1ppe"))
    print(verb_example.conjugate("2ps"))
    print(verb_example.conjugate("2pp"))
    print(verb_example.conjugate("3p"))
