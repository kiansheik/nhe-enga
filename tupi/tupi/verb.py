import random
from .tupi import TupiAntigo
from .tupi import ALT_ORTS
import json
import re

#  Get path of current file directory
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

# Make a function which takes a string and int id, and looks for that file in "irregular/{stirng}_{id}.json" and returns the object if it finds it, otherwise None
def get_irregular_verb(verbete, id):
    try:
        
        with open(current_dir+f"/irregular/{verbete}_{id}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None 

class Verb(TupiAntigo):
    def __init__(self, verbete, verb_class, raw_definition, vid=None):
        super().__init__()
        self.verbete = verbete  # The name of the verb in its dictionary form
        self.verb_class = verb_class  # Class of the verb (string)
        self.transitivo = "v.tr." in verb_class.replace(
            " ", ""
        )  # Whether the verb is transitive (boolean)
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.irregular = get_irregular_verb(verbete, vid)
        self.t_type = "(t, t)" in raw_definition[:500]
        self.pluriforme = (
            "(s)" in self.verb_class
            or "(r, s)" in self.verb_class
            or "-s-" in self.verb_class
            or self.t_type
        )
        self.ios = "-îo-" in self.verb_class and "-s-" in self.verb_class
        self.segunda_classe = (
            "2ª classe" in self.verb_class or "adj." in self.verb_class
        )
        self.ero = self.verbete.startswith("ero") or self.verbete.startswith("eno") or self.verbete.startswith("eru") or self.verbete.startswith("erekó") or self.verbete.startswith("ereko")
        self.vid = vid

    def object_marker(self, pc):
        return (
            ""
            if self.ero
            else "îos" + f"[OBJECT_MARKER:3p:PLURIFORM_PREFIX:MONOSYLLABIC]"
            if self.ios
            else (f"s[PLURIFORM_PREFIX:S]")
            if (pc and not self.t_type)
            else "t[PLURIFORM_PREFIX:T]"
            if (pc and self.t_type)
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
            result = f"n[NEGATION_PREFIX]{result}"
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
        subject_tense=None,
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
        pluri_check = self.pluriforme
        base_verbete = self.verbete
        overwrite = False
        # search for the (subject_tense, mode) in the irregular verb and if found, set base_verbete and pluriform to those values
        if self.irregular:
            # if mode == "gerundio":
            #     breakpoint()
            subj_key = subject_tense if subject_tense else 'ø'
            obj_key = object_tense if object_tense else 'ø'
            subj = self.irregular.get(subj_key)
            if subj:
                obj = subj.get(obj_key)
                if obj:
                    ms = mode[:2]
                    if mode == "permissivo":
                        ms = 'in'
                    tr = obj.get(ms)
                    if tr:
                        base_verbete = tr['verbete']
                        pluri_check = tr['pluriforme']
                        overwrite = tr['overwrite']
        if not subject_tense:
            subject_tense = object_tense


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
                vbt = base_verbete
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]a[GERUND_SUFFIX:CLASS_1]"
                elif base_verbete[-1] in "ĩ ỹ ũ".split():
                    suf = f"amo[GERUND_SUFFIX:CLASS_1:NASAL_IYU]"
                elif base_verbete[-1] in "i í y ý u ú".split():
                    suf = f"abo[GERUND_SUFFIX:CLASS_1:IYU]"
                elif base_verbete[-1] in self.vogais_nasais:
                    suf = "mo[GERUND_SUFFIX:CLASS_1:NASAL_VOWEL]"
                elif base_verbete[-1] == "b":
                    suf = "pa[GERUND_SUFFIX:CLASS_1:B]"
                    vbt = vbt[:-1]
                elif base_verbete[-1] == "r":
                    vbt = self.accent_last_vowel(vbt[:-1])
                    suf = vbt[-1] + "[GERUND_SUFFIX:CLASS_1:R]"
                    vbt = vbt[:-1]
                elif base_verbete[-1] not in self.vogais:
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
                            if pluri_check or self.ero:
                                dir_obj = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                            # elif self.monosilibica():
                            #     dir_obj = f"îo[OBJECT:3p:MONOSYLLABIC]-"
                        else:
                            dir_obj += f'{f"r[PLURIFORM_PREFIX:R]-" if pluri_check or self.ero else ""}'
                    pref = dir_obj
                if suf[0] in self.vogais and vbt[-1] in "i y u".split():
                    vbt = vbt[:-1] + self.semi_vogais_map[vbt[-1]]
                vbt += f"[ROOT]"
                result = f"{pref}{vbt}{suf}"
            else:
                subj = (
                    self.personal_inflections[subject_tense][1]
                    if "3p" not in subject_tense
                    else "o"
                ) + f"[GERUND_SUBJECT_PREFIX:{subject_tense}]"
                suf = "amo" + f"[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                vbt = base_verbete + f"[ROOT]"
                if base_verbete[-1] in self.vogais_nasais:
                    suf = "namo" + f"[GERUND_SUFFIX:CLASS_2:NASAL_VOWEL_ENDING]"
                elif base_verbete[-1] in self.vogais:
                    suf = "ramo" + f"[GERUND_SUFFIX:CLASS_2:ORAL_VOWEL_ENDING]"
                pluriforme = ""
                if pluri_check and "3p" not in subject_tense:
                    pluriforme += "r[PLURIFORM_PREFIX:R]-"
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]amo[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                result = f"{subj}{pluriforme}{vbt}{suf}"
        elif mode == "conjuntivo":
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
                    if pluri_check or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                        else:
                            obj = f"{obj}r[PLURIFORM_PREFIX:R]-"
            vbt = base_verbete
            if negative:
                eme = "e'ym[NEGATION_SUFFIX]e[CONJUNCTIVE_SUFFIX:NEGATIVE]"
            else:
                if vbt[-1] in "bm":
                    vbt = self.accent_last_vowel(vbt[:-1])
                    eme = (
                        "me" + f"[CONJUNCTIVE_SUFFIX]"
                    )
                else:
                    if vbt[-1] in self.vogais_nasais:
                        vbt += "n"
                    elif vbt[-1] in self.vogais:
                        vbt += "r"
                    eme = (
                        "eme" + f"[CONJUNCTIVE_SUFFIX]"
                    )
            if pluri_check and not self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    obj = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                    subj = ""
                else:
                    obj += f"r[PLURIFORM_PREFIX:R]-"
            vbt = f"{vbt}[ROOT]"
            result = f"{subj if not pro_drop else ''}{' ' if not self.segunda_classe else ''}{obj}{vbt}{eme}"
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
                    if pluri_check or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                        else:
                            obj = f"{obj}r[PLURIFORM_PREFIX:R]-"
            circ = (
                f"[CIRCUMSTANTIAL_SUFFIX:NULL_ENDING]"
                if base_verbete[-1] in "û u ũ î".split()
                else "û" + f"[CIRCUMSTANTIAL_SUFFIX:VOWEL_ENDING]"
                if base_verbete[-1] in self.vogais
                else "i" + f"[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            )
            if pluri_check and not self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    obj = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                    subj = ""
                else:
                    obj += f"r[PLURIFORM_PREFIX:R]-"
            if negative:
                circ = "e'ym[NEGATION_SUFFIX]i[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            vbt = f"{base_verbete}[ROOT]"
            result = f"{subj if not pro_drop else ''}{' ' if not self.segunda_classe else ''}{obj}{vbt}{circ}"
        elif self.segunda_classe:
            subj_prefix = (
                self.personal_inflections[subject_tense][1] + f"[SUBJECT_PREFIX:{subject_tense}]"
            )
            subj = ""
            if dir_subj_raw is not None:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            pluriforme = ""
            if pluri_check:
                if "3p" in subject_tense:
                    pluriforme = f"s[PLURIFORM_PREFIX:S]-" if not self.t_type else "t[PLURIFORM_PREFIX:T]-"
                    subj_prefix = ""
                else:
                    pluriforme = f"r[PLURIFORM_PREFIX:R]-"
            vb =  f"{subj_prefix}{pluriforme}{base_verbete}[ROOT]"
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
            conj = "" if overwrite else conj
            vbt = f"{conj}{base_verbete}[ROOT]"
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
                    vbt = f"{conj}{obj}{base_verbete}[ROOT]"
                    perm = self.choose_perm(vbt, perm_mode)
                    if overwrite:
                        vbt = f"{base_verbete[1:]}[ROOT]"
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
                        base_verbete[1:]
                        if self.ero and subject_tense in ["1ps", "1ppi", "2ps", "2pp"]
                        else base_verbete
                    ) + f"[ROOT]"
                    pluriforme = self.object_marker(pluri_check)
                    if pos == "posposto":
                        perm = self.choose_perm(conj, perm_mode)
                        trm = f"{conj}-{pluriforme}-{vbt}"
                        if overwrite:
                            trm = f"{vbt}"
                        vb = f"{perm}{trm}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{subj} {vb} {dir_obj}"
                        )
                    elif pos == "anteposto":
                        perm = self.choose_perm(conj, perm_mode)
                        trm = f"{conj}-{pluriforme}-{vbt}"
                        if overwrite:
                            trm = f"{vbt}"
                        vb = f"{perm}{trm}"
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
                        vbt = f"{obj}{base_verbete}[ROOT]"
                        if overwrite:
                            vbt = f"{base_verbete}[ROOT]"
                        perm = self.choose_perm(vbt, perm_mode)
                        result = f"{perm}{vbt}"
                        if negative:
                            result = self.negate_verb(result, mode)
                        result = f"{subj if not pro_drop else ''} {result}"
                        
                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = self.personal_inflections[subject_tense][4] + f"[SUBJECT:{subject_tense}:OBJECT_1P]"
                        obj = self.personal_inflections[object_tense][1] + f"[OBJECT:{object_tense}]"
                        pluriforme = f"r[PLURIFORM_PREFIX:R]-" if pluri_check or self.ero else ""
                        vbt = f"{obj}{pluriforme}{base_verbete}[ROOT]"
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
                        pluriforme = f"r[PLURIFORM_PREFIX:R]-" if pluri_check or self.ero else ""
                        vbt = f"{obj}{pluriforme}{base_verbete}[ROOT]"
                        perm = self.choose_perm(vbt, perm_mode)
                        vb = f"{perm}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vb} {subj if not pro_drop else ''}" if pos == "anteposto" else f"{subj if not pro_drop else ''} {vb}"
        return result if anotar else self.fix_phonetics(self.remove_brackets_and_contents(result))
