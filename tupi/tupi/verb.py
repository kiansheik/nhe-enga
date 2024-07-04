from .tupi import TupiAntigo
import re


class Verb(TupiAntigo):
    def __init__(self, verbete, verb_class, raw_definition, vid=None):
        super().__init__()
        self.verbete = verbete  # The name of the verb in its dictionary form
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
    
    def object_marker(self):
        return (
            ""
            if self.ero
            else "îos" + f"[OBJECT_MARKER:3p:PLURIFORM_PREFIX:MONOSYLLABIC]"
            if self.ios
            else "s" + f"[PLURIFORM_PREFIX:S]"
            if self.pluriforme
            else "îo" + f"[OBJECT_MARKER:3p:MONOSYLLABIC]"
            if self.monosilibica()
            else "î" + f"[OBJECT_MARKER:3p:DEFAULT]"
        )
    
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
            result = f"{result[:-1]}[{last_tag}{result[-1]}" + "[NEGATION_SUFFIX:VOWEL_ENDING]"
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
        dir_subj_raw=None,
        mode="indicativo",
        pos="anteposto",
        pro_drop=False,
        negative=False,
        anotar=False,
    ):  
        result = ''
        perm_mode = False
        if mode == "permissivo":
            perm_mode = True
        if mode == "gerundio":
            if not self.segunda_classe:
                subj = (
                    self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                    if dir_subj_raw is None
                    else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                )
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
                    pref = f"{subj_pref}-"
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
                                dir_obj = f"s[PLURIFORM_PREFIX:S]-"
                            elif self.monosilibica():
                                dir_obj = f"îo[OBJECT:3p:MONOSYLLABIC]-"
                        else:
                            dir_obj += f'{f"r[PLURIFORM_PREFIX:R]-" if self.pluriforme or self.ero else ""}'
                    pref = dir_obj
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]a[GERUND_SUFFIX:CLASS_1]"
                vbt += f"[ROOT]"
                result = f"{pref}{vbt}{suf}"
            else:
                subj = (
                    self.personal_inflections[subject_tense][1]
                    if "3p" not in subject_tense
                    else "o"
                ) + f"[SUBJECT:{subject_tense}]"
                suf = "amo" + f"[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                vbt = self.verbete + f"[ROOT]"
                if self.verbete[-1] in self.vogais_nasais:
                    suf = "namo" + f"[GERUND_SUFFIX:CLASS_2:NASAL_VOWEL_ENDING]"
                elif self.verbete[-1] in self.vogais:
                    suf = "ramo" + f"[GERUND_SUFFIX:CLASS_2:ORAL_VOWEL_ENDING]"
                pluriforme = ""
                if self.pluriforme and "3p" not in subject_tense:
                    pluriforme += "r[PLURIFORM_PREFIX:R]-"
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]amo[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                result = f"{subj}{pluriforme}{vbt}{suf}"
        elif "2p" not in subject_tense and mode == "circunstancial":
            subj = self.personal_inflections[subject_tense][1] + f"[SUBJECT:{subject_tense}]"
            if "3p" in subject_tense and dir_subj_raw:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    subj = self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                if (subject_tense == object_tense and subject_tense != "3p") or object_tense == "refl":
                    obj = "îe" + f"[OBJECT:REFLEXIVE]"
                elif object_tense == "mut":
                    obj = "îo" + f"[OBJECT:MUTUAL]"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}" + f"[OBJECT:DIRECT]"
                    ) 
                    if self.pluriforme or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = f"s[PLURIFORM_PREFIX:S]-"
                        else:
                            obj = f"{obj}r[PLURIFORM_PREFIX:R]-"
            circ = (
                f"[CIRCUMSTANTIAL_SUFFIX:NULL_ENDING]"
                if self.verbete[-1] in "ûuũî"
                else "û" + f"[CIRCUMSTANTIAL_SUFFIX:VOWEL_ENDING]"
                if self.verbete[-1] in self.vogais
                else "i" + f"[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            )
            if self.pluriforme and not self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    obj = f"s[PLURIFORM_PREFIX:S]-"
                    subj = ""
                else:
                    obj += f"r[PLURIFORM_PREFIX:R]-"
            if negative:
                circ = "e'ym[NEGATION_SUFFIX]i[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            vbt = f"{self.verbete}[ROOT]"
            result = f"{subj if not pro_drop else ''}{' ' if not self.segunda_classe else ''}{obj}{vbt}{circ}"
        elif self.segunda_classe:
            subj_prefix = (
                self.personal_inflections[subject_tense][1] + f"[SUBJECT_PREFIX:{subject_tense}]"
            )
            subj = ""
            if dir_subj_raw is not None:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            pluriforme = ""
            if self.pluriforme:
                if "3p" in subject_tense:
                    pluriforme = f"s[PLURIFORM_PREFIX:S]-"
                    subj_prefix = ""
                else:
                    pluriforme = f"r[PLURIFORM_PREFIX:R]-"
            vb =  f"{subj_prefix}{pluriforme}{self.verbete}[ROOT]"
            perm = self.choose_perm(vb, perm_mode)
            result = f"{subj} {perm}{vb}"
            if negative:
                result = self.negate_verb(result, mode)
        elif not self.segunda_classe and not self.transitivo:
            subj = (self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]" 
                    if dir_subj_raw is None 
                    else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            )
            conj = (
                self.imperativo[subject_tense][0] + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                if (mode == "imperativo" and "2p" in subject_tense)
                else self.personal_inflections[subject_tense][2] + f"[SUBJECT_PREFIX:{subject_tense}]"
            )
            vbt = f"{conj}{self.verbete}[ROOT]"
            perm = self.choose_perm(vbt, perm_mode)
            vb = f"{perm}{vbt}"
            if negative:
                vb = self.negate_verb(vb, mode)
            result = f"{subj if not pro_drop else ''} {vb}"
        elif self.transitivo:
            if pos not in ["posposto", "incorporado", "anteposto"]:
                raise Exception("Position Not Valid")
            if object_tense in self.personal_inflections.keys():
                if (subject_tense != '3p' and object_tense == subject_tense) or (object_tense in ('refl', 'mut')):
                    if object_tense == subject_tense:
                        object_tense = 'refl'
                    subj = (
                        self.personal_inflections[subject_tense][0] if not '3p' == subject_tense else "a'e"
                    ) + f"[SUBJECT:{subject_tense}]"
                    subj = subj if dir_subj_raw is None else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                    conj = (
                        self.imperativo[subject_tense][0] + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2] + f"[SUBJECT_PREFIX:{subject_tense}]"
                    )
                    obj = "îe[OBJECT:REFLEXIVE]" if object_tense == 'refl' else "îo[OBJECT:MUTUAL]"
                    vbt = f"{conj}{obj}{self.verbete}[ROOT]"
                    perm = self.choose_perm(vbt, perm_mode)
                    vb = f"{perm}{vbt}"
                    if negative:
                        vb = self.negate_verb(vb, mode)
                    result = f"{subj if not pro_drop else ''} {vb}"
                elif "3p" in object_tense:
                    subj = (
                        self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                        if dir_subj_raw is None
                        else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                    ) if not pro_drop else ""
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
                    ) + f"[ROOT]"
                    pluriforme = self.object_marker()
                    if pos == "posposto":
                        perm = self.choose_perm(conj, perm_mode)
                        vb = f"{perm}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{subj} x`{vb} {dir_obj}"
                        )
                    elif pos == "anteposto":
                        perm = self.choose_perm(conj, perm_mode)
                        vb = f"{perm}{conj}-{pluriforme}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{subj} {dir_obj} {vb}"
                        )
                    elif pos == "incorporado":
                        perm = self.choose_perm(conj, perm_mode)
                        vb = f"{perm}{conj}-{pluriforme if dir_obj_raw is None else dir_obj}-{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{subj} {vb}"
                if "2p" in object_tense:
                    if "1p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                            if not dir_subj_raw
                            else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                        )
                        obj = self.personal_inflections[object_tense][3] + f"[OBJECT:{object_tense}:SUBJECT_1P]"
                        vbt = f"{obj}{self.verbete}[ROOT]"
                        perm = self.choose_perm(vbt, perm_mode)
                        result = f"{perm}{vbt}"
                        if negative:
                            result = self.negate_verb(result, mode)
                        result = f"{subj if not pro_drop else ''} {result}"
                        
                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = self.personal_inflections[subject_tense][4] + f"[SUBJECT:{subject_tense}:OBJECT_1P]"
                        obj = self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        pluriforme = f"r[PLURIFORM_PREFIX:R]-" if self.pluriforme or self.ero else ""
                        vbt = f"{obj}{pluriforme}{self.verbete}[ROOT]"
                        perm = self.choose_perm(vbt, perm_mode)
                        vb = f"{perm}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vb} {subj}"
                if "2p" in object_tense or "1p" in object_tense:
                    if "3p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0] + f"[SUBJECT:{subject_tense}]"
                            if dir_subj_raw is None
                            else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                        )
                        obj = (
                            self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                            # if dir_obj_raw is None
                            # else dir_obj_raw + f"[OBJECT]:{object_tense}:DIRECT]"
                        )
                        pluriforme = f"r[PLURIFORM_PREFIX:R]-" if self.pluriforme or self.ero else ""
                        vbt = f"{obj}{pluriforme}{self.verbete}[ROOT]"
                        perm = self.choose_perm(vbt, perm_mode)
                        vb = f"{perm}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vb} {subj if not pro_drop else ''}" if pos == "anteposto" else f"{subj if not pro_drop else ''} {vb}"
        result = self.fix_phonetics(result)
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
            ("1ppi", "3p"),
            ("1ppi", "refl"),
            ("1ppi", "mut"),
            # Endé
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            # ("2ps", "2ps"),
            ("2ps", "3p"),
            ("2ps", "refl"),
            # pee
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
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
            ("1ps", "refl"),
            ("1ps", "mut"),
            ("1ps", "1ppe"),
            ("1ps", "1ppi"),
            ("1ps", "2ps"),
            ("1ps", "2pp"),
            ("1ps", "3p"),
            # oré
            ("1ppe", "1ps"),
            ("1ppe", "refl"),
            ("1ppe", "mut"),
            ("1ppe", "2ps"),
            ("1ppe", "2pp"),
            ("1ppe", "3p"),
            # iande
            ("1ppi", "1ps"),
            ("1ppi", "refl"),
            ("1ppi", "mut"),
            ("1ppi", "3p"),
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
        "imperativo": [
            # ende
            ("2ps", "1ps"),
            ("2ps", "1ppe"),
            ("2ps", "2ps"),
            ("2ps", "3p"),
            # pe'e
            ("2pp", "1ps"),
            ("2pp", "1ppe"),
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
        return {(token, annotation) for token, annotation in matches if '[ROOT]' not in annotation}

    print("test")
    from collections import Counter
    c = Counter()
    for res in results:
        c.update(tokenize_string(res['anotated']))
    print(c.most_common())
