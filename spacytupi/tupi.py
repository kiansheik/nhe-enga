import spacy


class TupiAntigo(spacy.language.Language):
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere", "oro", "îepé"],
        "2pp": ["pe'ẽ", "pe", "pe", "opo", "peîepé"],
        "3p": ["a'e", "i", "o"],
        # "4p": ["asé", "asé", "o"],
    }

    sound_graf = {
        "ipa": "p pʷ pʲ β t s sʷ k kʷ ʔ m mʷ n r ɲ ŋ mb mbʷ nd ndʷ ŋɡ ŋɡʷ w w j a ˈa e ˈɛ i ˈi ɨ ˈɨ o ˈɔ u ˈu ã ɛ̃ ĩ ɨ̃ ɔ̃ ũ ʃ".split(
            " "
        ),
        "navarro": "p pû pî b t s sû k kû ' m mû n r nh ng mb mbû nd ndû ng ngû gû û î a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ x".split(
            " "
        ),
    }

    vogais = "a á e é i í y ý o ó u ú ã ẽ ĩ ỹ õ ũ".split(" ")

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

    def inflect_verb(self, verb, inflection):
        inf = self.personal_inflections[inflection]
        return f"{inf[0]} {inf[2]}{verb}"


class Verb(TupiAntigo):
    def __init__(self, verbete, verb_class, raw_definition):
        super().__init__()
        self.verbete = verbete  # The name of the verb in its dictionary form
        self.substantivo = f"{verbete}{'a' if verbete[-1] not in self.vogais else ''}"
        self.verb_class = verb_class  # Class of the verb (string)
        self.transitive = (
            "v.tr." in verb_class
        )  # Whether the verb is transitive (boolean)
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.pluriforme = "(s)" in self.verb_class

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

    def conjugate(
        self,
        subject_tense="1ps",
        object_tense=None,
        dir_obj_raw=None,
        mode="indicativo",
        pos="anteposto",
        pro_drop=False,
        io_pref=False,
    ):
        if "2p" not in subject_tense and mode == "circunstancial":
            subj = self.personal_inflections[subject_tense][0]
            obj = ""
            if self.transitive:
                if subject_tense == object_tense:
                    subj = self.personal_inflections[subject_tense][1]
                    obj = "îe"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1]
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}"
                    )
                    if self.pluriforme:
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
            result = f"{subj} {obj}{self.verbete}{circ}"
        # A simple conjugation function (you can expand this based on language rules)
        elif self.verb_class in ["adj.: "]:
            result = f"{self.personal_inflections[subject_tense][1]} {self.verbete}"
        elif "v. intr." in self.verb_class:
            subj = self.personal_inflections[subject_tense][0] if not pro_drop else ""
            result = (
                f"{subj} {self.personal_inflections[subject_tense][2]}-{self.verbete}"
            )
        elif self.verb_class in ["(v.tr.)", "(s) (v.tr.)"]:
            if pos not in ["posposto", "incorporado", "anteposto"]:
                raise Error("Postposition Not Valid")
            if object_tense in self.personal_inflections.keys():
                if object_tense == subject_tense:
                    subj = (
                        self.personal_inflections[subject_tense][1]
                        if not pro_drop
                        else ""
                    )
                    result = f"{subj} {self.personal_inflections[subject_tense][2]}-{'îe' if not io_pref else 'îo'}-{self.verbete}"
                elif "3p" in object_tense:
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        if not pro_drop
                        else ""
                    )
                    pref = self.personal_inflections[subject_tense][2]
                    dir_obj = (
                        self.personal_inflections["3p"][0]
                        if dir_obj_raw is None
                        else dir_obj_raw
                    )
                    pluriforme = "s" if self.pluriforme else "î"
                    if pos == "posposto":
                        result = f"{subj} {pref}-{pluriforme}-{self.verbete} {dir_obj}"
                    elif pos == "anteposto":
                        result = f"{subj} {dir_obj} {pref}-{pluriforme}-{self.verbete}"
                    elif pos == "incorporado":
                        result = f"{subj} {pref}-{pluriforme if dir_obj_raw is None else dir_obj}-{self.verbete}"
                if "2p" in object_tense:
                    if "1p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][1]
                            if not pro_drop
                            else ""
                        )
                        obj = self.personal_inflections[object_tense][3]
                        result = f"{subj} {obj}-{self.verbete}"
                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = self.personal_inflections[subject_tense][4]
                        obj = self.personal_inflections[object_tense][1]
                        pluriforme = "r-" if self.pluriforme else ""
                        result = f"{obj} {pluriforme}{self.verbete} {subj}"
                if "2p" in object_tense or "1p" in object_tense:
                    if "3p" in subject_tense or "4p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0]
                            if dir_obj_raw is None
                            else dir_obj_raw
                        )
                        obj = self.personal_inflections[object_tense][1]
                        pluriforme = "r-" if self.pluriforme else ""
                        result = f"{obj} {pluriforme}{self.verbete} {subj}"
        else:
            return "Invalid/Unimplemented tense"
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
