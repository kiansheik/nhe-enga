from tupi import TupiAntigo
import re


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
        self.ero = self.verbete.startswith("ero") or self.verbete.startswith("eno") or self.verbete.startswith("eru")
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
    def remove_brackets_and_contents(self, s):
        return re.sub(r'\[.*?\]', '', s)
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
            else "îos" + f"[OBJECT_MARKER:3p:PLURIFORM_PREFIX:MONOSYLLABIC]"
            if self.ios
            else "s" + f"[OBJECT_MARKER:3p:PLURIFORM_PREFIX]"
            if self.pluriforme
            else "îo" + f"[OBJECT_MARKER:3p:MONOSYLLABIC]"
            if self.monosilibica()
            else "î" + f"[OBJECT_MARKER:3p:DEFAULT]"
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
            "-": ""
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
    
    def negate_verb(self, result, modo):
        if modo in ('permissivo', 'imperativo'):
            return f"{result} umẽ[NEGATION_PARTICLE:UME]"
        spleet = result.split('[')
        last_tag = spleet[-1]
        result = '['.join(spleet[:-1])
        if result[0] in TupiAntigo.vogais or result[0] == 'î':
            result = f"n'[NEGATION_PREFIX]{result}"
        else:
            result = f"na[NEGATION_PARTICLE:NA] {result}"
        if result[-1] == 'i' or result[-1] == 'î':
            result = f"{result[:-1]}[{last_tag}î" + "[NEGATION_SUFFIX:VOWEL_ENDING]"
        elif result[-1] in TupiAntigo.vogais:
            result = f"{result}[{last_tag}î" + "[NEGATION_SUFFIX:VOWEL_ENDING]"
        else:
            result = f"{result}[{last_tag}i" + "[NEGATION_SUFFIX:CONSONANT_ENDING]"
        return result

    def conjugate(
        self,
        subject_tense="1ps",
        object_tense=None,
        dir_obj_raw=None,
        mode="indicativo",
        pos="anteposto",
        pro_drop=False,
        negative=False,
        anotar=False,
    ):  
        perm_suf = ["", ""]
        if mode == "permissivo":
            obj_perm = ("1p" in object_tense and "2p" in subject_tense) or (("2p" in object_tense or "1p" in object_tense) and "3p" in subject_tense)
            perm_suf = self.permissivo_anotado[object_tense if obj_perm else subject_tense]

        if mode == "gerundio":
            if not self.segunda_classe:
                subj = self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                suf = "bo[GERUND_SUFFIX:CLASS_1:ORAL_VOWEL]"
                vbt = self.verbete
                if self.verbete[-1] in "ĩ ỹ ũ":
                    suf = f"amo[GERUND_SUFFIX:CLASS_1:NASAL_IYU]"
                elif self.verbete[-1] in "i í y ý u ú":
                    suf = f"abo[GERUND_SUFFIX:CLASS_1:IYU]"
                elif self.verbete[-1] in self.vogais_nasais:
                    suf = "mo[GERUND_SUFFIX:CLASS_1:NASAL_VOWEL]"
                elif self.verbete[-1] == "b":
                    suf = "pa[GERUND_SUFFIX:CLASS_1:B]"
                    vbt = vbt[:-1]
                elif self.verbete[-1] == "r":
                    vbt = self.accent_last_vowel(vbt[:-1])
                    suf = vbt[-1] + "[GERUND_SUFFIX:CLASS_1:R]"
                    vbt = vbt[:-1]
                elif self.verbete[-1] not in self.vogais:
                    suf = "a" + "[GERUND_SUFFIX:CLASS_1:CONSONANT]"
                if not self.transitivo:
                    subj_pref = self.gerundio[subject_tense][0] + f"[GERUND_SUBJECT_PREFIX:{subject_tense}]"
                    pref = f"{f'{subj} ' if not pro_drop else ''}{subj_pref}-"
                else:
                    dir_obj = (
                        f"{self.personal_inflections[object_tense][1]}[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else dir_obj_raw + f"[OBJECT:DIRECT]"
                    )
                    if object_tense  in ('refl', 'mut'):
                        dir_obj =  f"îe[OBJECT:REFLEXIVE]-" if object_tense == 'refl' else f"îo[OBJECT:MUTUAL]-"
                    else:
                        if object_tense == "3p" and dir_obj_raw is None:
                            if self.pluriforme or self.ero:
                                dir_obj = f"s[OBJECT:PLURIFORM_PREFIX:{object_tense}]-"
                            elif self.monosilibica():
                                dir_obj = f"îo[OBJECT:3p:MONOSYLLABIC]-"
                        else:
                            dir_obj += f' {f"r[PLURIFORM_PREFIX]-" if self.pluriforme or self.ero else ""}'
                    pref = dir_obj
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]a[GERUND_SUFFIX:CLASS_1]"
                vbt += f"[VERB]"
                result = f"{pref}{vbt}{suf}"
            else:
                subj = (
                    self.personal_inflections[subject_tense][1]
                    if "3p" not in subject_tense
                    else "o"
                ) + f"[SUBJECT:{subject_tense}]"
                suf = "amo" + f"[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                vbt = self.verbete + f"[VERB]"
                if self.verbete[-1] in self.vogais_nasais:
                    suf = "namo" + f"[GERUND_SUFFIX:CLASS_2:NASAL_VOWEL_ENDING]"
                elif self.verbete[-1] in self.vogais:
                    suf = "ramo" + f"[GERUND_SUFFIX:CLASS_2:ORAL_VOWEL_ENDING]"
                pluriforme = ""
                if self.pluriforme and "3p" not in subject_tense:
                    pluriforme += "r[PLURIFORM_PREFIX]-"
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]amo[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                result = f"{subj} {pluriforme}{vbt}{suf}"
        elif "2p" not in subject_tense and mode == "circunstancial":
            subj = self.personal_inflections[subject_tense][1] + f"[SUBJECT:{subject_tense}]"
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense:
                    subj = self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                if subject_tense == object_tense:
                    obj = "îe" + f"[OBJECT:REFLEXIVE]"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}" + f"[OBJECT:DIRECT]"
                    ) 
                    if self.pluriforme or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = f"s[PLURIFORM_PREFIX:{object_tense}]-"
                        else:
                            obj = f"{obj} r[PLURIFORM_PREFIX]-"
                    else:
                        obj += " "
            circ = (
                f"[CIRCUMSTANTIAL_SUFFIX:NULL_ENDING]"
                if self.verbete[-1] in "ûuũî"
                else "û" + f"[CIRCUMSTANTIAL_SUFFIX:VOWEL_ENDING]"
                if self.verbete[-1] in self.vogais
                else "i" + f"[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            )
            if self.pluriforme and not self.transitivo:
                if "3p" in subject_tense:
                    obj = f"s[PLURIFORM_PREFIX:{subject_tense}]-"
                    subj = ""
                else:
                    obj += f"r[PLURIFORM_PREFIX]-"
            if negative:
                circ = "e'ym[NEGATION_SUFFIX]i[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            vbt = f"{self.verbete}[VERB]"
            result = f"{subj} {obj}{vbt}{circ}"
        elif self.segunda_classe:
            subj = self.personal_inflections[subject_tense][1] + f"[SUBJECT:{subject_tense}]"
            pluriforme = ""
            if self.pluriforme:
                if "3p" in subject_tense:
                    pluriforme = f"s[PLURIFORM_PREFIX:{subject_tense}]-"
                    subj = ""
                else:
                    pluriforme = f"r[PLURIFORM_PREFIX]-"
            vb =  f"{pluriforme}{self.verbete}[VERB]"
            result = f"{perm_suf[1]}{subj} {vb}"
            if negative:
                result = self.negate_verb(result, mode)
        elif not self.segunda_classe and not self.transitivo:
            subj = self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]" if not pro_drop else ""
            conj = (
                self.imperativo[subject_tense][0] + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                if (mode == "imperativo" and "2p" in subject_tense)
                else self.personal_inflections[subject_tense][2] + f"[SUBJECT_PREFIX:{subject_tense}]"
            )
            vbt = f"{self.verbete}[VERB]"
            vb = f"{perm_suf[0]}{conj}-{vbt}"
            if negative:
                vb = self.negate_verb(vb, mode)
            result = f"{subj} {vb}"
        elif self.transitivo:
        # TODO: Implement rest of the annotation tags
            if pos not in ["posposto", "incorporado", "anteposto"]:
                raise Exception("Position Not Valid")
            if object_tense in self.personal_inflections.keys():
                if (subject_tense != '3p' and object_tense == subject_tense) or (object_tense in ('refl', 'mut')):
                    subj = (
                        self.personal_inflections[subject_tense][1] if not '3p' == subject_tense else "a'e"
                        if not pro_drop
                        else ""
                    ) + f"[SUBJECT:{subject_tense}]" if not pro_drop else ""
                    conj = (
                        self.imperativo[subject_tense][0] + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2] + f"[SUBJECT_PREFIX:{subject_tense}]"
                    )
                    obj = "îe[OBJECT:REFLEXIVE]" if object_tense == 'refl' else "îo[OBJECT:MUTUAL]"
                    vbt = f"{self.verbete}[VERB]"
                    vb = f"{perm_suf[0]}{conj}-{obj}-{vbt}"
                    if negative:
                        vb = self.negate_verb(vb, mode)
                    result = f"{subj} {vb}"
                elif "3p" in object_tense:
                    subj = (
                        self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                        if not pro_drop
                        else ""
                    )
                    conj = (
                        self.imperativo[subject_tense][0] + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2] + f"[SUBJECT_PREFIX:{subject_tense}]"
                    )
                    dir_obj = (
                        self.personal_inflections["3p"][0] + f"[OBJECT:3p]"
                        if dir_obj_raw is None
                        else dir_obj_raw + f"[OBJECT:DIRECT]"
                    )
                    vbt = (
                        self.verbete[1:]
                        if self.ero and subject_tense in ["1ps", "1ppi", "2ps", "2pp"]
                        else self.verbete
                    ) + f"[VERB]"
                    pluriforme = self.object_marker()
                    if pos == "posposto":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{subj} {vb} {dir_obj}"
                        )
                    elif pos == "anteposto":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{subj} {dir_obj} {vb}"
                        )
                    elif pos == "incorporado":
                        vb = f"{perm_suf[0]}{conj}-{pluriforme if dir_obj_raw is None else dir_obj}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{subj} {vb}"
                if "2p" in object_tense:
                    if "1p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][1] + f"[SUBJECT:{subject_tense}]"
                            if not pro_drop
                            else ""
                        )
                        obj = self.personal_inflections[object_tense][3] + f"[OBJECT:{object_tense}:SUBJECT_1P]"
                        vbt = f"{self.verbete}[VERB]"
                        result = f"{perm_suf[0]}{obj}-{vbt}"
                        if negative:
                            result = self.negate_verb(result, mode)
                        result = f"{subj} {result}"
                        
                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = self.personal_inflections[subject_tense][4] + f"[SUBJECT:{subject_tense}:OBJECT_1P]"
                        obj = self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        pluriforme = f"r[PLURIFORM_PREFIX]-" if self.pluriforme or self.ero else ""
                        vbt = f"{self.verbete}[VERB]"
                        vb = f"{perm_suf[1]}{obj} {pluriforme}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vb} {subj}"
                if "2p" in object_tense or "1p" in object_tense:
                    if "3p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                            if dir_obj_raw is None
                            else dir_obj_raw + f"[OBJECT:DIRECT]"
                        )
                        obj = self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        pluriforme = f"r[PLURIFORM_PREFIX]-" if self.pluriforme or self.ero else ""
                        vbt = f"{self.verbete}[VERB]"
                        vb = f"{perm_suf[1]}{obj} {pluriforme}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vb} {subj}"
        # else:
        #     return "Invalid/Unimplemented tense"
        result = self.fix_phonetics(result)
        # print(
        #     f"({subject_tense} -> {object_tense}):",
        #     f"\t",
        #     result.strip().replace("-", ""),
        #     "\t",
        # )
        # self.ipa(result.strip().replace("-", ""))
        return result if anotar else self.remove_brackets_and_contents(result)


if __name__ == "__main__":
    import json
    # Example usage:
    test_cases_map = {
        "indicativo": [
            # Ixe
            # ("1ps", "1ps"),
            ("1ps", "2ps"),
            ("1ps", "2pp"),
            ("1ps", "3p"),
            ("1ps", "refl"),
            # Oré
            # ("1ppe", "1ppe"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            ("1ppe", "refl"),
            ("1ppe", "mut"),
            # Îandé
            # ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            ("1ppi", "refl"),
            ("1ppi", "mut"),
            # Endé
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            ("2ps", "1ppi"),
            # ("2ps", "2ps"),
            ("2ps", "3p"),
            ("2ps", "refl"),
            # pe'e
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
            ("2pp", "1ppi"),
            # ("2pp", "2pp"),
            ("2pp", "3p"),
            ("2pp", "refl"),
            ("2pp", "mut"),
            # a'e
            ("3p", "1ps"),
            ("3p", "1ppe"),
            ("3p", "1ppi"),
            ("3p", "2ps"),
            ("3p", "2pp"),
            ("3p", "3p"),
            ("3p", "refl"),
            ("3p", "mut"),
        ],
        "gerundio": [
            ("1ps", "1ps"),
            ("1ppe", "1ppe"),
            ("1ppi", "1ppi"),
            ("2ps", "2ps"),
            ("2pp", "2pp"),
            ("3p", "3p"),
        ],
        "circunstancial": [
            # ixe
            ("1ps", "1ps"),
            ("1ps", "1ppe"),
            ("1ps", "1ppi"),
            ("1ps", "2ps"),
            ("1ps", "2pp"),
            ("1ps", "3p"),
            # oré
            ("1ppe", "1ps"),
            ("1ppe", "1ppe"),
            ("1ppe", "1ppi"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            # iande
            ("1ppi", "1ps"),
            ("1ppi", "1ppe"),
            ("1ppi", "1ppi"),
            ("1ppi", "2ps"),
            ("1ppi", "2pp"),
            ("1ppi", "3p"),
            # a'e
            ("3p", "1ps"),
            ("3p", "1ppe"),
            ("3p", "1ppi"),
            ("3p", "2ps"),
            ("3p", "2pp"),
            ("3p", "3p"),
        ],
        "imperativo": [
            # ende
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            ("2ps", "1ppi"),
            ("2ps", "2ps"),
            ("2ps", "3p"),
            # pe'e
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
            ("2pp", "1ppi"),
            ("2pp", "2pp"),
            ("2pp", "3p"),
        ],
    }
    results = []
    test_cases_map["permissivo"] = test_cases_map["indicativo"]
    verbs = [Verb("apysyk", "adj.", "gostar"), Verb("nhe'eng", "v. intr.", "gostar"), Verb("enõî", "v.tr. (r, s)", "gostar"),]
    for modo, test_cases in [(x[0], x[1]) for x in test_cases_map.items()]:
        for v in verbs:
            # Print the result
            if v.transitivo:
                for subj, obj in test_cases:
                    try:
                        res = v.conjugate(
                            subject_tense=subj,
                            object_tense=obj,
                            mode=modo,
                            anotar=True
                        )
                        neg_res = v.conjugate(
                            subject_tense=subj,
                            object_tense=obj,
                            mode=modo,
                            negative=True,
                            anotar=True
                        )
                        # print(f"{res}")
                        results.append({"anotated":res, "label":v.remove_brackets_and_contents(res)})
                    except Exception as e:
                        pass
            else:
                for subj in sorted({x[0] for x in test_cases}):
                    try:
                        res = v.conjugate(
                            subject_tense=subj,
                            mode=modo,
                            anotar=True
                        )
                        neg_res = v.conjugate(
                            subject_tense=subj,
                            mode=modo,
                            negative=True,
                            anotar=True
                        )
                        print(f"{res}")
                        results.append({"anotated":res, "label":v.remove_brackets_and_contents(res)})
                    except Exception as e:
                        pass

    # Write results to file
    with open('anotated_results.json', 'w') as f:
        # use json to write to file
        json.dump(results, f)

    def tokenize_string(annotated_string):
        matches = re.findall(r'([^\s\[\]]+)?(\[.*?\])', annotated_string)
        return {(token, annotation) for token, annotation in matches if '[VERB]' not in annotation}

    print("test")
    from collections import Counter
    c = Counter()
    for res in results:
        c.update(tokenize_string(res['anotated']))
    print(c.most_common())
