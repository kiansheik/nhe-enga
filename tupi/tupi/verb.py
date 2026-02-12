import random
from .tupi import TupiAntigo
from .annotated_string import AnnotatedString
from .tupi import ALT_ORTS
import json
import json
import unicodedata
from importlib import resources


def get_irregular_verb(verbete, id):
    verbete = unicodedata.normalize("NFC", verbete)
    target_suffix = f"{verbete}_{id}.json"
    try:
        for file in resources.files("tupi.irregular").iterdir():
            normalized_name = unicodedata.normalize("NFC", file.name)
            if normalized_name.endswith(target_suffix):
                with file.open("r") as f:
                    return json.load(f)
    except ModuleNotFoundError:
        pass
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
        self.irregular = get_irregular_verb(verbete, vid + 1 if vid else None)
        self.t_type = "(t, t)" in raw_definition[:500]
        self.tr_type = "(t)" in raw_definition[:100]
        self.pluriforme = False  # Whether the verb has a plural form (boolean)
        if self.t_type:
            self.pluriforme = True
            self.pluriforme_type = "t, t"
        elif self.tr_type:
            self.pluriforme = True
            self.pluriforme_type = "t"
        elif "(s)" in self.verb_class:
            self.pluriforme_type = "s"
            self.pluriforme = True
        elif "-s-" in self.verb_class:
            self.pluriforme_type = "s"
            self.pluriforme = True
        elif "(r, s)" in self.verb_class:
            self.pluriforme_type = "r, s"
            self.pluriforme = True

        self.ios = "-îo-" in self.verb_class and "-s-" in self.verb_class
        self.segunda_classe = (
            "2ª classe" in self.verb_class or "adj." in self.verb_class
        )
        self.ero = (
            self.verbete.startswith("ero")
            or self.verbete.startswith("eno")
            or self.verbete.startswith("eru")
            or self.verbete.startswith("erekó")
            or self.verbete.startswith("ereko")
        )
        if self.ero:
            self.pluriforme = True
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
        if modo in ("permissivo", "imperativo"):
            return f"{result} umẽ[NEGATION_PARTICLE:UME]"
        spleet = result.split("[")
        last_tag = spleet[-1]
        result = "[".join(spleet[:-1])
        if result[0] in TupiAntigo.vogais or result[0] == "î":
            result = f"n[NEGATION_PREFIX]{result}"
        else:
            result = f"na[NEGATION_PARTICLE:NA] {result}"
        if result[-1] == "i" or result[-1] == "î":
            result = (
                f"{result[:-1]}[{last_tag}{result[-1]}"
                + "[NEGATION_SUFFIX:VOWEL_ENDING]"
            )
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
        pro_drop_obj=False,
        vadjs="",
        vadjs_pre="",
        redup=False,
    ):
        result = ""
        perm_mode = False
        pluri_check = self.pluriforme
        base_verbete = self.verbete
        overwrite = False
        if vadjs_pre:
            vadjs_pre = f" {vadjs_pre} "
        # search for the (subject_tense, mode) in the irregular verb and if found, set base_verbete and pluriform to those values
        if self.irregular:
            # breakpoint()
            subj_key = subject_tense if subject_tense else "ø"
            obj_key = object_tense if object_tense else "ø"
            obj_key = "3p" if obj_key == "none" else obj_key
            if mode == "gerundio" and self.transitivo:
                # In transitive gerund, the subject prefix is not realized;
                # irregular gerund forms are keyed under "ø".
                subj_key = "ø"
            if obj_key == "absoluta":
                if self.transitivo:
                    subj_key = "3p"
                    obj_key = "3p"
                else:
                    subj_key = "3p"
                    obj_key = "ø"
            if obj_key == "3p" and subj_key == "3p" and not self.transitivo:
                obj_key = "ø"
            if subj_key in ["refl", "mut", "suj"]:
                subj_key = "3p"
            subj = self.irregular.get(subj_key)
            if subj:
                obj = subj.get(obj_key)
                if obj is None and obj_key in ["refl", "mut", "suj"]:
                    # fall back to 3p object if no irregular refl/mut entry exists
                    obj = subj.get("3p")
                if obj:
                    ms = mode[:2]
                    if mode == "permissivo":
                        ms = "in"
                    elif mode == "nominal":
                        ms = "co"
                    tr = obj.get(ms)
                    if tr:
                        base_verbete = tr["verbete"]
                        pluri_check = tr["pluriforme"]
                        overwrite = tr["overwrite"]
        if not subject_tense:
            subject_tense = object_tense
        if mode == "permissivo":
            perm_mode = True
        if mode == "gerundio":
            if not self.segunda_classe:
                subj = (
                    self.personal_inflections[subject_tense][0]
                    + f"[SUBJECT:{subject_tense}]"
                    if dir_subj_raw is None
                    else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                )
                suf = "bo[GERUND_SUFFIX:CLASS_1:ORAL_VOWEL]"
                vbt = base_verbete
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]a[GERUND_SUFFIX:CLASS_1]"
                elif ends_with_any(base_verbete, "ĩ ỹ ũ".split()):
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
                elif base_verbete[-2:] in ["'o", "'u"]:
                    vbt = vbt[:-2] + "'ûa"
                if not self.transitivo or object_tense in ["refl", "mut"]:
                    dir_obj = ""
                    if object_tense == "refl":
                        dir_obj = "îe" + f"[OBJECT:REFLEXIVE]"
                    elif object_tense == "mut":
                        dir_obj = "îo" + f"[OBJECT:MUTUAL]"
                    subj_pref = (
                        self.gerundio[subject_tense][0]
                        + dir_obj
                        + f"[GERUND_SUBJECT_PREFIX:{subject_tense}]"
                    )
                    pref = f"{subj_pref}"
                else:
                    dir_obj = (
                        f"{self.personal_inflections[object_tense][1]}[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else dir_obj_raw + f"[OBJECT:DIRECT]"
                    )
                    if dir_obj_raw is not None:
                        dir_obj += " "
                    # else:
                    #     # remove accented ´ from dir_obj if present, as it will be combined without a space
                    #     dir_obj = (
                    #         dir_obj.replace("á", "a")
                    #         .replace("é", "e")
                    #         .replace("í", "i")
                    #         .replace("ó", "o")
                    #         .replace("ú", "u")
                    #         .replace("ý", "y")
                    #     )
                    if object_tense == "3p" and dir_obj_raw is None:
                        if pluri_check or self.ero:
                            dir_obj = (
                                f"s[PLURIFORM_PREFIX:S]"
                                if not self.t_type
                                else "t[PLURIFORM_PREFIX:T]"
                            )
                        # elif self.monosilibica():
                        #     dir_obj = f"îo[OBJECT:3p:MONOSYLLABIC]"
                    else:
                        dir_obj += f'{f"r[PLURIFORM_PREFIX:R]" if pluri_check or self.ero else ""}'
                    pref = dir_obj
                if vbt and suf[0] in self.vogais and vbt[-1] in "i y u".split():
                    vbt = vbt[:-1] + self.semi_vogais_map[vbt[-1]]
                vbt += f"[ROOT]"
                if redup:
                    vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()
                result = f"{vadjs_pre}{pref}{vbt}{suf}{vadjs}".strip()
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
                    pluriforme += "r[PLURIFORM_PREFIX:R]"
                if negative:
                    suf = "e'ym[NEGATION_SUFFIX]amo[GERUND_SUFFIX:CLASS_2:DEFAULT]"
                result = f"{vadjs_pre}{subj}{pluriforme}{vbt}{suf}{vadjs}".strip()
        elif mode == "conjuntivo":
            subj = (
                self.personal_inflections[subject_tense][1]
                + f"[SUBJECT:{subject_tense}]"
            )
            if "3p" in subject_tense and dir_subj_raw:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        + f"[SUBJECT:{subject_tense}]"
                    )
                if (
                    subject_tense == object_tense and subject_tense != "3p"
                ) or object_tense == "refl":
                    obj = "îe" + f"[OBJECT:REFLEXIVE]"
                elif object_tense == "mut":
                    obj = "îo" + f"[OBJECT:MUTUAL]"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1]
                        + f"[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}" + f"[OBJECT:DIRECT]"
                    )
                    if pluri_check or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = (
                                f"s[PLURIFORM_PREFIX:S]"
                                if not self.t_type
                                else "t[PLURIFORM_PREFIX:T]"
                            )
                        else:
                            obj = f"{obj}r[PLURIFORM_PREFIX:R]"
            vbt = base_verbete
            if negative:
                eme = "e'ym[NEGATION_SUFFIX]e[CONJUNCTIVE_SUFFIX:NEGATIVE]"
            else:
                if vbt[-1] in "bm":
                    vbt = self.accent_last_vowel(vbt[:-1])
                    eme = "me" + f"[CONJUNCTIVE_SUFFIX]"
                else:
                    if vbt[-1] in self.vogais_nasais:
                        vbt += "n"
                    elif vbt[-1] in self.vogais:
                        vbt += "r"
                    eme = "eme" + f"[CONJUNCTIVE_SUFFIX]"
            if pluri_check and not self.transitivo:
                if ("3p" in subject_tense and dir_subj_raw is None) or (
                    vadjs_pre != ""
                ):
                    obj = (
                        f"s[PLURIFORM_PREFIX:S]"
                        if not self.t_type
                        else "t[PLURIFORM_PREFIX:T]"
                    )
                    if vadjs_pre == "":
                        subj = ""
                else:
                    obj += f"r[PLURIFORM_PREFIX:R]"
            # For transitives, the pluriforme R (if any) is already handled
            # when building the object prefix above. Adding it again here
            # yields double R (e.g., "nderrareme").
            vbt = f"{vbt}[ROOT]"
            redup_space = f"{obj}{vbt}"
            if redup:
                redup_space = self.reduplicate(
                    AnnotatedString(redup_space)
                ).get_annotated()
            result = f"{subj if not pro_drop else ''}{' ' if not self.segunda_classe else ''}{vadjs_pre}{redup_space}{eme}{vadjs}".strip()
        elif mode == "nominal":
            subj = self.personal_inflections[subject_tense][1]
            tag = (
                f"[SUBJECT:{subject_tense}]"
                if subject_tense != "suj"
                else "[PRONOUN:MAIN_CLAUSE_SUBJECT_REFERENCE]"
            )
            subj += tag
            if "3p" in subject_tense and dir_subj_raw:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        + f"[SUBJECT:{subject_tense}]"
                    )

                if (subject_tense == "3p" and dir_subj_raw is None) and (
                    object_tense == "refl" or object_tense == "mut"
                ):
                    subj = "i" + f"[SUBJECT:{subject_tense}]"
                if (
                    subject_tense == object_tense and subject_tense != "3p"
                ) or object_tense == "refl":
                    obj = "îe" + f"[OBJECT:REFLEXIVE]"
                elif object_tense == "mut":
                    obj = "îo" + f"[OBJECT:MUTUAL]"
                elif object_tense == "absoluta" and dir_obj_raw is None:
                    if self.pluriforme:
                        obj = f""
                        # if base_verbete[0] in self.vogais:
                        #     obj = "mor[OBJECT:GENERIC:PEOPLE]"
                        # else:
                        #     obj = "moro[OBJECT:GENERIC:PEOPLE]"
                    else:
                        obj = f""
                else:
                    obj = ""
                    if object_tense:
                        obj = (
                            self.personal_inflections[
                                object_tense if object_tense != "none" else "3p"
                            ][1]
                            + f"[OBJECT:{object_tense}]"
                            if dir_obj_raw is None
                            else f"{dir_obj_raw}" + f"[OBJECT:DIRECT]"
                        )
                    if pluri_check or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = (
                                f"s[PLURIFORM_PREFIX:S]"
                                if not self.t_type
                                else "t[PLURIFORM_PREFIX:T]"
                            )
            vbt = base_verbete
            if (
                pluri_check
                and not self.transitivo
                and (subject_tense not in ["refl", "mut", "suj"])
            ):
                if ("3p" in subject_tense and dir_subj_raw is None) or (
                    vadjs_pre != ""
                ):
                    obj = (
                        ""
                        if object_tense == "none"
                        else f"t[PLURIFORM_PREFIX:T]"
                        if object_tense == "absoluta"
                        else f"s[PLURIFORM_PREFIX:S]"
                        if not self.t_type
                        else "t[PLURIFORM_PREFIX:T]"
                    )
                    if vadjs_pre == "":
                        subj = ""
                elif vadjs_pre == "":
                    obj += f"r[PLURIFORM_PREFIX:R]"
            elif (
                pluri_check
                and self.transitivo
                and (object_tense not in ["3p", "absoluta"] or dir_obj_raw is not None)
                and (object_tense not in ["refl", "mut", "suj"])
            ):
                obj += f"r[PLURIFORM_PREFIX:R]"
            vbt = f"{vbt}[ROOT]"
            redup_space = f"{obj}{vbt}"
            if redup:
                redup_space = self.reduplicate(
                    AnnotatedString(redup_space)
                ).get_annotated()
            result = (
                f"{subj if not pro_drop else ''}{' ' if not self.segunda_classe else ''}{vadjs_pre}{redup_space}{vadjs}"
            ).strip()
        elif "2p" not in subject_tense and mode == "circunstancial":
            subj = (
                self.personal_inflections[subject_tense][1]
                + f"[SUBJECT:{subject_tense}]"
            )
            dsr = False
            if "3p" in subject_tense and dir_subj_raw:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                dsr = True
            obj = ""
            if self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        + f"[SUBJECT:{subject_tense}]"
                    )
                if (
                    subject_tense == object_tense and subject_tense != "3p"
                ) or object_tense == "refl":
                    obj = "îe" + f"[OBJECT:REFLEXIVE]"
                elif object_tense == "mut":
                    obj = "îo" + f"[OBJECT:MUTUAL]"
                else:
                    obj = (
                        self.personal_inflections[object_tense][1]
                        + f"[OBJECT:{object_tense}]"
                        if dir_obj_raw is None
                        else f"{dir_obj_raw}" + f"[OBJECT:DIRECT]"
                    )
                    if pluri_check or self.ero:
                        if object_tense == "3p" and dir_obj_raw is None:
                            obj = (
                                f"s[PLURIFORM_PREFIX:S]"
                                if not self.t_type
                                else "t[PLURIFORM_PREFIX:T]"
                            )
                        else:
                            obj = f"{obj}r[PLURIFORM_PREFIX:R]"
            circ = (
                f"[CIRCUMSTANTIAL_SUFFIX:NULL_ENDING]"
                if base_verbete[-1] in "û u ũ î".split()
                else "û" + f"[CIRCUMSTANTIAL_SUFFIX:VOWEL_ENDING]"
                if base_verbete[-1] in self.vogais
                else "i" + f"[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            )
            if pluri_check and not self.transitivo:
                if "3p" in subject_tense and dir_subj_raw is None:
                    obj = (
                        f"s[PLURIFORM_PREFIX:S]"
                        if not self.t_type
                        else "t[PLURIFORM_PREFIX:T]"
                    )
                    subj = ""
                elif dsr and vadjs_pre != "":
                    obj += f"s[PLURIFORM_PREFIX:R]"
                else:
                    obj += f"r[PLURIFORM_PREFIX:R]"
            if negative:
                circ = "e'ym[NEGATION_SUFFIX]i[CIRCUMSTANTIAL_SUFFIX:CONSONANT_ENDING]"
            vbt = f"{base_verbete}[ROOT]"
            subj = (subj if (not pro_drop or not self.transitivo) else "") + (
                " " if not self.segunda_classe else ""
            )
            if vadjs_pre != "":
                redup_space = f"{obj}{vbt}"
            else:
                redup_space = (
                    f"{subj}{' ' if not self.segunda_classe else ''}{obj}{vbt}"
                )
            if redup:
                redup_space = self.reduplicate(
                    AnnotatedString(redup_space)
                ).get_annotated()
            if vadjs_pre == "":
                subj = ""
            result = f"{subj}{vadjs_pre}{redup_space}{circ}{vadjs}".strip()
        elif self.segunda_classe:
            subj_prefix = (
                self.personal_inflections[subject_tense][1]
                + f"[SUBJECT_PREFIX:{subject_tense}"
                + ("]" if not mode == "imperativo" else ":IMPERATIVE]")
            )
            subj = ""
            if not pro_drop:
                subj = (
                    self.personal_inflections[subject_tense][0]
                    + f"[SUBJECT_PRONOUN:{subject_tense}]"
                )
            if dir_subj_raw is not None and not pro_drop:
                subj = dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            pluriforme = ""
            if pluri_check:
                if "3p" in subject_tense:
                    pluriforme = (
                        f"s[PLURIFORM_PREFIX:S]"
                        if not self.t_type
                        else "t[PLURIFORM_PREFIX:T]"
                    )
                    subj_prefix = ""
                else:
                    pluriforme = f"r[PLURIFORM_PREFIX:R]"
            # TODO: Organize the pluriform types into a table like Gerardi has, but adding the ting case
            if (
                base_verbete.split("[")[0].startswith("ting") and subject_tense == "3p"
            ):  # as anchieta says, it is a unique exception which gets not P
                subj_prefix = "[PLURIFORM_PREFIX:NULL:TING]"
            vb = f"{subj_prefix}{pluriforme}{base_verbete}[ROOT]"
            if redup:
                vb = self.reduplicate(AnnotatedString(vb)).get_annotated()
            perm = self.choose_perm(vb, perm_mode)
            result = f"{perm}{vb}"
            if negative:
                result = self.negate_verb(result, mode)
            result += vadjs
            if pos == "anteposto":
                result = f"{subj} {vadjs_pre}{result}"
            else:
                result = f"{vadjs_pre}{result} {subj}"
        elif not self.segunda_classe and not self.transitivo:
            subj = (
                self.personal_inflections[subject_tense][0]
                + f"[SUBJECT:{subject_tense}]"
                if dir_subj_raw is None
                else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
            )
            conj = (
                self.imperativo[subject_tense][0]
                + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                if (mode == "imperativo" and "2p" in subject_tense)
                else self.personal_inflections[subject_tense][2]
                + f"[SUBJECT_PREFIX:{subject_tense}]"
            )
            conj = "" if overwrite else conj
            vbt = f"{conj}{base_verbete}[ROOT]"
            if redup:
                vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()
            perm = self.choose_perm(vbt, perm_mode)
            vb = f"{perm}{vbt}"
            if negative:
                vb = self.negate_verb(vb, mode)
            if pos == "anteposto":
                result = f"{subj if not pro_drop else ''} {vadjs_pre}{vb}{vadjs}"
            else:
                result = f"{vadjs_pre}{vb}{vadjs} {subj if not pro_drop else ''}"
        elif self.transitivo:
            if pos not in ["posposto", "incorporado", "anteposto"]:
                raise Exception("Position Not Valid")
            if object_tense in self.personal_inflections.keys():
                if (subject_tense != "3p" and object_tense == subject_tense) or (
                    object_tense in ("refl", "mut")
                ):
                    if object_tense == subject_tense:
                        object_tense = "refl"
                    subj = (
                        self.personal_inflections[subject_tense][0]
                        if not "3p" == subject_tense
                        else "a'e"
                    ) + f"[SUBJECT:{subject_tense}]"
                    subj = (
                        subj
                        if dir_subj_raw is None
                        else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                    )
                    conj = (
                        self.imperativo[subject_tense][0]
                        + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2]
                        + f"[SUBJECT_PREFIX:{subject_tense}]"
                    )
                    obj = (
                        "îe[OBJECT:REFLEXIVE]"
                        if object_tense == "refl"
                        else "îo[OBJECT:MUTUAL]"
                    )
                    vbt = f"{conj}{obj}{base_verbete}[ROOT]"
                    perm = self.choose_perm(vbt, perm_mode)
                    if overwrite:
                        # base_verbete already contains the subject prefix; keep conj/object
                        # but avoid duplicating the subject prefix from base_verbete.
                        subj_pref_raw = self.remove_brackets_and_contents(conj)
                        stem = (
                            base_verbete[len(subj_pref_raw) :]
                            if subj_pref_raw and base_verbete.startswith(subj_pref_raw)
                            else base_verbete
                        )
                        vbt = f"{conj}{obj}{stem}[ROOT]"
                    if redup:
                        vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()
                    vb = f"{perm}{vbt}"
                    if negative:
                        vb = self.negate_verb(vb, mode)
                    subj = subj if not pro_drop else ""
                    result = f"{vadjs_pre}{vb}{vadjs} {subj}".strip()
                    if pos == "anteposto":
                        result = f"{subj} {vadjs_pre}{vb}{vadjs}"
                elif "3p" in object_tense:
                    subj = (
                        (
                            self.personal_inflections[subject_tense][0]
                            + f"[SUBJECT:{subject_tense}]"
                            if dir_subj_raw is None
                            else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                        )
                        if not pro_drop
                        else ""
                    )
                    conj = (
                        self.imperativo[subject_tense][0]
                        + f"[IMPERATIVE_PREFIX:{subject_tense}]"
                        if (mode == "imperativo" and "2p" in subject_tense)
                        else self.personal_inflections[subject_tense][2]
                        + f"[SUBJECT_PREFIX:{subject_tense}]"
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
                        trm = f"{conj}{pluriforme}{vbt}"
                        if overwrite:
                            trm = f"{vbt}"
                        if redup:
                            trm = self.reduplicate(AnnotatedString(trm)).get_annotated()
                        vb = f"{perm}{trm}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{subj} {vadjs_pre}{vb}{vadjs} {dir_obj if not pro_drop_obj else ''}".strip()
                    elif pos == "anteposto":
                        perm = self.choose_perm(conj, perm_mode)
                        trm = f"{conj}{pluriforme}{vbt}"
                        if overwrite:
                            trm = f"{vbt}"
                        if redup:
                            trm = self.reduplicate(AnnotatedString(trm)).get_annotated()
                        vb = f"{perm}{trm}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{subj}{' '+ dir_obj if not pro_drop_obj else ''} {vadjs_pre}{vb}{vadjs}".strip()
                    elif pos == "incorporado":
                        perm = self.choose_perm(conj, perm_mode)
                        vb = f"{perm}{conj}{pluriforme if dir_obj_raw is None else dir_obj}{vbt}"
                        if redup:
                            vb = self.reduplicate(AnnotatedString(vb)).get_annotated()
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{subj} {vadjs_pre}{vb}{vadjs}"
                if "2p" in object_tense:
                    if "1p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0]
                            + f"[SUBJECT:{subject_tense}]"
                            if not dir_subj_raw
                            else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                        )
                        obj = (
                            self.personal_inflections[object_tense][3]
                            + f"[OBJECT:{object_tense}:SUBJECT_1P]"
                        )
                        vbt = f"{obj}{base_verbete}[ROOT]"
                        if overwrite:
                            vbt = f"{base_verbete}[ROOT]"
                        if redup:
                            vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()

                        perm = self.choose_perm(vbt, perm_mode)
                        result = f"{perm}{vbt}"
                        if negative:
                            result = self.negate_verb(result, mode)
                        # breakpoint()
                        if pos == "posposto":
                            result = f"{vadjs_pre}{result}{vadjs} {subj if not pro_drop else ''}"
                        else:
                            result = f"{subj if not pro_drop else ''} {vadjs_pre}{result}{vadjs}"

                if "1p" in object_tense:
                    if "2p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][4]
                            + f"[SUBJECT:{subject_tense}:OBJECT_1P]"
                        )
                        obj = (
                            self.personal_inflections[object_tense][1]
                            + f"[OBJECT:{object_tense}]"
                        )
                        pluriforme = (
                            f"r[PLURIFORM_PREFIX:R]" if pluri_check or self.ero else ""
                        )
                        vbt = f"{obj}{pluriforme}{base_verbete}[ROOT]"
                        if redup:
                            vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()
                        perm = self.choose_perm(vbt, perm_mode)
                        vb = f"{perm}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = f"{vadjs_pre}{vb}{vadjs} {subj}"
                if "2p" in object_tense or "1p" in object_tense:
                    if "3p" in subject_tense:
                        subj = (
                            self.personal_inflections[subject_tense][0]
                            + f"[SUBJECT:{subject_tense}]"
                            if dir_subj_raw is None
                            else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
                        )
                        obj = (
                            self.personal_inflections[object_tense][1]
                            + f"[OBJECT:{object_tense}]"
                            # if dir_obj_raw is None
                            # else dir_obj_raw + f"[OBJECT]:{object_tense}:DIRECT]"
                        )
                        pluriforme = (
                            f"r[PLURIFORM_PREFIX:R]" if pluri_check or self.ero else ""
                        )
                        vbt = f"{obj}{pluriforme}{base_verbete}[ROOT]"
                        if redup:
                            vbt = self.reduplicate(AnnotatedString(vbt)).get_annotated()
                        perm = self.choose_perm(vbt, perm_mode)
                        vb = f"{perm}{vbt}"
                        if negative:
                            vb = self.negate_verb(vb, mode)
                        result = (
                            f"{vadjs_pre}{vb}{vadjs} {subj if not pro_drop else ''}"
                            if pos == "posposto"
                            else f"{subj if not pro_drop else ''} {vadjs_pre}{vb}{vadjs}"
                        )
        return (
            result
            if anotar
            else self.fix_phonetics(self.remove_brackets_and_contents(result))
        )

    def bae(self, obj=None, anotar=False):
        # We will conjugate for the 3rd person prod_drop first, and then apply the suffix
        obj_t = "3p"
        obj_clean = None if not obj else AnnotatedString(obj).get_clean()
        if obj_clean == "îe":
            obj_t = "refl"
        elif obj_clean == "îo":
            obj_t = "mut"
        vbt = self.conjugate(
            subject_tense="3p",
            object_tense=obj_t,
            dir_obj_raw=obj,
            dir_subj_raw=None,
            mode="indicativo",
            pos="anteposto",
            pro_drop=True,
            negative=False,
            anotar=True,
        )
        vbt = AnnotatedString(vbt)
        if ends_with_any(vbt, ["b", "p"]):
            vbt.replace_clean(-1, 1, "")
            vbt.insert_suffix("ba'e")
        elif ends_with_any(vbt, ["m"]):
            vbt.insert_suffix("ba'e")
        elif ends_with_any(vbt, self.vogais):
            vbt.replace_clean(-1, 1, self.remove_accent_last_vowel(vbt[-1]))
            vbt.insert_suffix("ba'e")
        else:
            vbt.insert_suffix("y[CONSONANT_CLASH]ba'e")
        vbt += "[RELATIVE_AGENT_SUFFIX]"
        return vbt.verbete(anotar)


def ends_with_any(s, endings):
    return any(s.endswith(ending) for ending in endings)


def starts_with_any(s, endings):
    return any(s.startswith(ending) for ending in endings)
