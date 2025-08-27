from .tupi import TupiAntigo
from .verb import Verb
import copy, inspect, re
from .annotated_string import AnnotatedString  # assuming the class is in this module

sara_consoante_map = {
    "b": "par",
    "k": "kar",
    "m": "mbar",
    "n": "ndar",
    "d": "ndar",
    "r": "sar",
    "i": "îar",
    "u": "ûar",
    "y": "ŷar",
    "é": "esar",
    "ó": "oar",
    "á": "asar",
    "í": "isar",
    "ú": "usar",
}
saba_consoante_map = {
    "b": "pab",
    "k": "kab",
    "m": "mbab",
    "n": "ndab",
    "d": "ndab",
    "r": "sab",
    "i": "îab",
    "u": "ûab",
    "y": "ŷab",
    "é": "esab",
    "ó": "oab",
    "á": "asab",
    "í": "isab",
    "ú": "usab",
}


def ends_with_any(s, endings):
    return any(s.endswith(ending) for ending in endings)


def starts_with_any(s, endings):
    return any(s.startswith(ending) for ending in endings)


def remove_ending_if_any(s, endings):
    for ending in endings:
        if s.endswith(ending):
            return s[: -len(ending)]
    return s


def remove_starting_if_any(s, endings):
    for ending in endings:
        if s.startswith(ending):
            return s[len(ending) :]
    return s


def tokenize_string(annotated_string):
    matches = re.findall(r"([^\s\[\]]+)?\[(.*?)\]", annotated_string)
    notes = [(token, annotation) for token, annotation in matches]
    return notes


class Noun(TupiAntigo):
    def __init__(self, verbete, raw_definition, noroot=False):
        super().__init__()
        vbt = AnnotatedString(verbete)
        if (
            len(vbt.clean) >= 2
            and (vbt[-1] == "a" and vbt[-2] != "'")
            and vbt[-2] not in self.vogais
        ):
            vbt.replace_clean(-1, 1, "", drop_trailing_tag=True)
            # breakpoint()
        if not vbt.get_annotated().endswith("[ROOT]") and not noroot:
            vbt.insert_suffix("[ROOT]")
        self.m_pluriforme = False
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.aglutinantes = [self]
        raw_def = self.raw_definition[:50]
        if "(m)" in raw_def:
            self.m_pluriforme = True
            # vbt.replace_clean(0, 1, "")
        self.base_verbete = vbt.get_annotated()
        self.latest_verbete = AnnotatedString(
            self.base_verbete
        )  # The name of the verb in its dictionary form
        if "(r, s)" in raw_def or "(s)" in raw_def or "-s-" in raw_def:
            self.pluriforme = "r, s"
        elif "(s, r, s)" in raw_def:
            self.pluriforme = "s, r, s"
        elif "(t)" in raw_def:
            self.pluriforme = "t"
        elif "(t, t)" in raw_def:
            self.pluriforme = "t, t"
        elif "(m)" in raw_def:
            self.pluriforme = "m"
        else:
            self.pluriforme = None
        self.recreate = f'Noun("{self.verbete()}", "({self.pluriforme})")'
        self.ios = "-îo-" in raw_def and "-s-" in raw_def
        self.segunda_classe = (
            "2ª classe" in self.raw_definition or "adj." in self.raw_definition
        )
        self.transitivo = "v.tr." in raw_def.replace(" ", "")
        self.ero = (
            self.verbete().startswith("ero")
            or self.verbete().startswith("eno")
            or self.verbete().startswith("eru")
        )
        self.objeto_raw = None

    # Fix annotation and whole composition process
    def compose(self, modifier):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        mod_noun = copy.deepcopy(modifier)
        vbt = ret_noun.latest_verbete
        mod_vbt = mod_noun.latest_verbete
        # Define some useful groups
        vogais_nasais = self.vogais_nasais
        nasais = self.consoantes_nasais
        consoantes = self.consoantes_orais_normais

        vbt.remove_accent_last_vowel()
        if ends_with_any(vbt, consoantes) and starts_with_any(
            mod_vbt, consoantes + nasais
        ):
            vbt.remove_ending_if_any(consoantes)
        elif ends_with_any(vbt, nasais + consoantes) and starts_with_any(
            mod_vbt, [self.glottal_stop]
        ):
            mod_vbt.replace_clean(0, 1, "")
        elif ends_with_any(vbt, nasais + vogais_nasais) and starts_with_any(
            mod_vbt, consoantes + nasais
        ):
            semivogal = "î" if ends_with_any(vbt, ["nh"]) else ""
            vbt.remove_ending_if_any(nasais)
            vbt.nasaliza_final()
            vbt.insert_suffix(semivogal)
            if not self.is_nasal(mod_vbt):
                mod_vbt.nasaliza_prefixo()
        elif ends_with_any(vbt, self.semi_vogais) and ends_with_any(
            vbt[:-1], vogais_nasais
        ):
            if not self.is_nasal(mod_vbt):
                mod_vbt.nasaliza_prefixo()
        vbt.insert_suffix(mod_vbt.get_annotated())
        # ret_noun.pluriforme = self.pluriforme
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def verb(self):
        verb_class = ""
        if self.segunda_classe:
            verb_class += "2ª classe "
        if self.transitivo:
            verb_class += "v.tr. "
        if self.pluriforme:
            verb_class += f"({self.pluriforme}) "
        if self.ios:
            verb_class += "-îo- -s- "
        ret = Verb(self.verbete(), verb_class, self.raw_definition)
        return ret

    def objeto(self, objeto_raw=None):
        if not objeto_raw:
            return self.objeto_raw
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        ret_noun.objeto_raw = objeto_raw
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    # Define a .conjugate function which passes all args to .verb.conjugate()
    def conjugate(self, *args, **kwargs):
        # kwargs["dir_obj_raw"] = self.objeto()
        return self.verb().conjugate(*args, **kwargs)

    def annotated_min(self, input_string):
        words = input_string.split(" ")
        # The words are an assembly of tokens. we want to identify the [ROOT] token, and all other tokens saved in a list
        root = None
        tokens = []
        for word in words:
            if "[ROOT]" in word:
                root_split = word.split("[ROOT]")
                suffixes = "[ROOT]".join(root_split[1:])
                prefixes = "]".join(root_split[0].split("]")[:-1])
                if prefixes:
                    prefixes += "]"
                root = root_split[0].split("]")[-1]
                print(root, prefixes, suffixes)

                n = Noun(root, prefixes)
                for suffix in suffixes.split("]"):
                    if "FACILITY_SUFFIX" in suffix:
                        n = n.saba()
                    if "ACTIVE_AGENT_SUFFIX" in suffix:
                        n = n.sara()
                    if "SUBSTANTIVE_SUFFIX" in suffix:
                        break
                tokens.append(
                    self.keep_brackets_contents(prefixes)
                    + root
                    + self.keep_brackets_contents(suffixes)
                )
            else:
                tokens.append(self.keep_brackets_contents(word))
        return " ".join(tokens)

    def perform_recreate(self, recreate='epîak[(r, s)][possessive(person="1ps")]'):
        # root = recreate.split('[')[0]
        tokens = tokenize_string(recreate)
        noun_out = f'Noun("{tokens[0][0]}", "{tokens[0][1]}")'
        for token, annotation in tokens[1:]:
            noun_out += f".{annotation}"
        return noun_out

    def verbete(self, anotated=False):
        return (
            self.latest_verbete.get_clean()
            if not anotated
            else self.latest_verbete.get_annotated()
        )

    def base_substantivo(self):
        if self.latest_verbete.get_annotated().endswith("[VOCATIVE_REDUCED_FORM]"):
            return self.verbete(anotated=True)
        return f"{self.verbete(anotated=True)}{'a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]' if (self.verbete(anotated=False)[-1] not in self.vogais) else '[SUBSTANTIVE_SUFFIX:VOWEL_ENDING]'}"

    def substantivo(self, anotated=False):
        bs = (
            self.base_substantivo()
            if anotated
            else self.remove_brackets_and_contents(self.base_substantivo())
        )
        return bs

    def __repr__(self) -> str:
        return self.substantivo()

    def __str__(self) -> str:
        return repr(self)

    def pluriform_prefix(self, person="absoluta"):
        plf = self.pluriforme
        if plf:
            if "3p" in person:
                if plf == "t, t":
                    return "t[PLURIFORM_PREFIX:T]"
                elif plf:
                    return "s[PLURIFORM_PREFIX:S]"
            if person == "absoluta":
                if plf == "t, t" or plf == "t":
                    return "t[PLURIFORM_PREFIX:T:ABSOLUTE]"
                if plf == "s, r, s":
                    return "s[PLURIFORM_PREFIX:S:ABSOLUTE]"
                if self.verb().transitivo:
                    prefix = "mor"
                    if starts_with_any(self.latest_verbete, self.consoantes):
                        prefix += "o"
                    return prefix + "[AGENT_PREFIX:GENERIC:PEOPLE:ABSOLUTE]"
            if "1p" in person or "2p" in person:
                return "r[PLURIFORM_PREFIX:R]"
        if self.m_pluriforme:
            if person == "absoluta":
                return "m[PLURIFORM_PREFIX:M:ABSOLUTE]"
            else:
                return "p[PLURIFORM_PREFIX:P]"
        return ""

    def supe(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # ret_noun.latest_verbete.drop_last_tag()
        vbt = AnnotatedString(ret_noun.substantivo(True))
        # implement the logic for the "supe" postposition. check each
        found = False
        for infl, vals in self.personal_inflections.items():
            if str(vbt.get_clean()) == vals[0]:
                new_vbt = AnnotatedString(self.dative_inflections[infl][0])
                found = True
                vbt = new_vbt
                break
        if not found:
            vbt.insert_suffix(" supé")
        ret_noun.latest_verbete = vbt
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def pe(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        annotated = ret_noun.latest_verbete

        if ends_with_any(annotated, ["ab"]):
            annotated.replace_clean(-2, 2, "á")
            annotated.insert_suffix("pe")
        elif ends_with_any(annotated, ["î", "nh"]):
            if annotated.endswith("nh"):
                annotated.replace_clean(
                    -3, 1, self.nasal_map.get(annotated[-3], annotated[-3])
                )
                annotated.replace_clean(-2, 2, "î")
            if annotated[-2] in ret_noun.vogais_nasais:
                annotated.insert_suffix("me")
            else:
                annotated.insert_suffix("pe")
        elif ends_with_any(annotated, ret_noun.vogais_nasais):
            annotated.insert_suffix("me")
        elif ends_with_any(annotated, ["m"]):
            annotated.replace_clean(-2, 2, self.nasal_map[annotated[-2]])
            annotated.insert_suffix("me")
        elif ends_with_any(annotated, ret_noun.nasais):
            annotated.insert_suffix("y[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING:CLITIC]")
            annotated.insert_suffix("me")
        elif ends_with_any(annotated, ret_noun.semi_vogais):
            annotated.insert_suffix("pe")
        elif ends_with_any(annotated, ret_noun.consoantes):
            annotated.insert_suffix("y[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING:CLITIC]")
            annotated.insert_suffix("pe")
        else:
            annotated.insert_suffix("pe")
        annotated.insert_suffix("[POSTPOSITION:LOCATIVE]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def sara(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        annotated = ret_noun.latest_verbete

        if ends_with_any(annotated, ["m"]):
            annotated.insert_suffix("bar")
        elif annotated[-2:] == "ng":
            annotated.insert_suffix("ar")
        elif ends_with_any(annotated, ret_noun.consoantes_nasais):
            annotated.insert_suffix("an")
        elif ends_with_any(annotated, ["î"]):
            if ends_with_any(annotated[:-1], ret_noun.nasais):
                annotated.insert_suffix("ndar")
            else:
                annotated.insert_suffix("tar")
        elif annotated.endswith("o") and annotated[-2] in (ret_noun.vogais + ["'"]):
            annotated.replace_clean(-1, 1, "ûar")
        elif annotated[-1] in sara_consoante_map:
            sar_rep = sara_consoante_map[annotated[-1]]
            annotated.replace_clean(-1, 1, "")
            annotated.insert_suffix(sar_rep)
        elif annotated[-1] not in ret_noun.vogais:
            annotated.insert_suffix("ar")
        else:
            annotated.insert_suffix("sar")

        annotated.insert_suffix("[ABSOLUTE_AGENT_SUFFIX]")

        ret_noun.latest_verbete = annotated.strip()
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    # TODO: Implement rest of phonetic changes
    def saba(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )

        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self

        annotated = AnnotatedString(str(self.latest_verbete))  # make copy
        vbt = annotated.get_clean()

        if self.ends_with(vbt, self.vogais_nasais):
            annotated.insert_suffix("ab")
        elif self.ends_with(vbt, ["î"]):
            if self.ends_with(vbt[:-1], self.nasais):
                annotated.insert_suffix("ndab")
            else:
                annotated.insert_suffix("tab")
        elif vbt.endswith("o") and vbt[-2] in (self.vogais + ["'"]):
            annotated.replace_clean(-1, 1, "ûab")
        elif vbt[-2:] == "ng":
            annotated.insert_suffix("ab")
        elif vbt[-1] in sara_consoante_map:
            annotated.replace_clean(-1, 1, saba_consoante_map[vbt[-1]])
        else:
            annotated.insert_suffix("sab")

        annotated.insert_suffix("[FACILITY_SUFFIX]")

        ret_noun.latest_verbete = annotated
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def possessive(self, person=None, possessor=None):
        if possessor is not None and person != "absoluta":
            person = "3p"
        else:
            if person is None:
                person = "absoluta"

        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )

        if person == "absoluta":
            tl = self.absoluta()
            if type(possessor) == bool and possessor:  # this is code for (te)mi-drop
                tl.latest_verbete.replace_clean(0, 2, "")
                return tl
            return tl

        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self

        vbt = ret_noun.latest_verbete

        # Determine prefix (e.g., r[PLURIFORM_PREFIX:R]) for plural forms
        if possessor and self.pluriforme:
            prefix = "r[PLURIFORM_PREFIX:R]"
        else:
            prefix = ret_noun.pluriform_prefix(person)
        # Determine possessive pronoun or custom possessor noun
        if possessor:
            poss_str = f"{possessor.strip()}[NOUN:POSSESSOR] "
        elif not ("3p" in person and self.pluriforme):
            poss_str = f"{self.personal_inflections[person][1].strip()}[POSSESSIVE_PRONOUN:{person}] "
        else:
            poss_str = ""  # no prefix for 3p pluriforme without possessor
        # Build annotated string
        if self.m_pluriforme:
            vbt.replace_clean(0, 1, "")
        vbt.insert_prefix(prefix)
        vbt.insert_prefix(poss_str)
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

        # TODO: Implement rest of phonetic changes

    def absoluta(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # TODO: Figure out verbetes como '(a)pé' which have the perntheses and that vowel only if there's no prefix
        vbt = ret_noun.latest_verbete
        pref = ret_noun.pluriform_prefix("absoluta")
        if pref:
            if self.m_pluriforme:
                vbt.replace_clean(0, 1, "")
            vbt.insert_prefix(pref)
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def vocativo(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        if vbt[-1] in "a":
            vbt.replace_clean(-1, 1, "")
        vbt.insert_suffix("[VOCATIVE_REDUCED_FORM]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def bae(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        if vbt[-1] in "bmp":
            vbt.replace_clean(-1, 1, "")
            vbt.insert_suffix("ba'e")
        elif vbt[-1] in self.vogais:
            vbt.remove_accent_last_vowel()
            vbt.insert_suffix("ba'e")
        else:
            vbt.insert_suffix("yba'e")
        vbt.insert_suffix("[RELATIVE_AGENT_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def puer(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        if vbt[-1] in self.vogais:
            if vbt[-1] in self.vogais_nasais:
                vbt.insert_suffix("mbûer")
            else:
                vbt.insert_suffix("pûer")
        elif vbt[-1] in ["b"]:
            vbt.replace_clean(-1, 1, "")
            vbt.insert_suffix("gûer")
        elif vbt[-1] in ["n"]:
            vbt.insert_suffix("der")
        elif vbt[-1] in ["r"]:
            vbt.insert_suffix("ûer")
        elif vbt[-1] in ["m"]:
            vbt.insert_suffix("bûer")
        else:
            vbt.insert_suffix("ûer")
        vbt.insert_suffix("[PRETERITE_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def ram(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        if vbt[-1] in self.vogais:
            if vbt[-1] in self.vogais_nasais:
                vbt.insert_suffix("nam")
            else:
                vbt.insert_suffix("ram")
        elif vbt[-1] in ["b"]:
            vbt.replace_clean(-1, 1, "")
            vbt.insert_suffix("gûam")
        elif ends_with_any(vbt, ["n", "r", "nh"]):
            vbt.insert_suffix("am")
        elif vbt[-1] in ["m"]:
            vbt.replace_clean(-1, 1, "")
            vbt.nasaliza_final()
            vbt.insert_suffix("gûam")
        else:
            vbt.insert_suffix("ûam")
        vbt.insert_suffix("[FUTURE_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def ramo(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        if vbt[-1] in self.vogais:
            if vbt[-1] in self.vogais_nasais:
                vbt.insert_suffix("namo")
            else:
                vbt.insert_suffix("ramo")
        else:
            vbt.insert_suffix("amo")
        vbt.insert_suffix("[SIMULATIVE_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = False
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def pyr(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        # breakpoint()
        suf = "pyr"
        vbt = ret_noun.latest_verbete
        if ends_with_any(vbt, self.nasais):
            suf = "mbyr"
        if vbt[-1] in ["b", "p"]:
            vbt.replace_clean(-1, 1, "")
        elif ends_with_any(vbt, self.consoantes):
            suf = f"y[CONSONANT_CLASH]{suf}"
        if not self.pluriforme:
            vbt.insert_prefix("i[OBJECT:3p:NON_MAIN_CLAUSE_SUBJECT]")
        else:
            prefix = ret_noun.pluriform_prefix("3p")
            vbt.insert_prefix(prefix)
        vbt.insert_suffix(suf)
        vbt.insert_suffix("[AGENTLESS_PATIENT_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.pluriforme = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    # Updated -reme to match new logic and use class methods
    def reme(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = ret_noun.latest_verbete

        if vbt[-1] in "bm":
            # Remove last char, accent last vowel, then add "me[CONJUNCTIVE_SUFFIX]"
            vbt.replace_clean(-1, 1, "")
            vbt.accent_last_vowel()
            vbt.insert_suffix("me")
        else:
            if vbt[-1] in self.vogais_nasais:
                vbt.insert_suffix("n")
            elif vbt[-1] in self.vogais:
                vbt.insert_suffix("r")
            vbt.insert_suffix("eme")
        vbt.insert_suffix("[CONJUNCTIVE_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    def emi(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        token = "[PATIENT_PREFIX]"
        if vbt[0] in self.nasal_prefix_map_emi.keys():
            # if any of self.nasais are present in vbt
            if not any(nasal in vbt for nasal in self.nasais):
                suf = "emi"
                if self.monosilibica():
                    suf = "embi"
                vbt.replace_clean(0, 1, self.nasal_prefix_map_emi[vbt[0]])
                vbt.insert_prefix(f"{suf}{token}")
        elif self.monosilibica() and not any(nasal in vbt for nasal in self.nasais):
            vbt.insert_prefix(f"embi{token}")
        else:
            vbt.insert_prefix(f"emi{token}")
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.pluriforme = "t"
        ret_noun.recreate += f".{func_name}({args_str})"
        ret_noun.aglutinantes.append(ret_noun)
        return ret_noun

    def eym(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ", ".join(
            f"{arg}={repr(values[arg])}" for arg in args if "self" != arg
        )
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = ret_noun.latest_verbete
        vbt.remove_accent_last_vowel()
        vbt.insert_suffix("e'ym")
        vbt.insert_suffix("[NEGATION_SUFFIX]")
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun


if __name__ == "__main__":
    # Example usage:
    # noun_examples = [Noun("apysyk", "adj.: "),
    #                     Noun("ker", "v.intr."),
    #                     Noun("aûsub", "v.tr. (r, s)"),
    #                     Noun("nhan", "v.intr.")
    # ]
    noun_examples = [
        (Noun("kytĩ", "adj.: "), "kytĩsara,kytĩana"),
        (Noun("pysyrõ", "v.intr."), "pysyrõsara,pysyrõana"),
        (Noun("tym", "v.tr. (r, s)"), "tymbara"),
        (Noun("mosem", "v.tr. (r, s)"), "mosembara"),
        (Noun("nhan", "v.intr."), "nhandara"),
        (Noun("suban", "v.intr."), "subandara"),
        (Noun("kuab", "v.intr."), "kuapara"),
        (Noun("mooryb", "v.intr."), "moorypara"),
        (Noun("potar", "v.intr."), "potasara"),
        (Noun("'u", "v.intr."), "'ûara,gûara"),
        (Noun("so'o", "v.intr."), "so'ûara,sogûara"),
        (Noun("kaî", "v.intr."), "kaîtara"),
        (Noun("poî", "v.intr."), "poîtara"),
        (Noun("enõî", "v.intr."), "enõîndara"),
        (Noun("îekoty", "v.intr."), "îekotŷara"),
        (Noun("kating", "v.intr."), "katingara"),
        (Noun("îuká", "v.intr."), "îukasara"),
    ]
    print()
    for noun_example, solution in noun_examples:
        if noun_example.sara().substantivo() not in solution:
            print(noun_example.verbete(), "\t", noun_example.sara(), "\t", solution)
    n = Noun("(a)pé", "(r, s)")
    print()
    print(n.recreate)
    print(n.verbete())
    print(n.substantivo(True))
    print(n.possessive("absoluta"), n.possessive("absoluta").recreate)
    print(
        n.possessive("absoluta").possessive("1ps"),
        n.possessive("absoluta").possessive("1ps").recreate,
    )
    print(n.possessive("1ps"))
    print(n.possessive("3p"), n.possessive("3p").recreate)

    print()
    print("Puera, rama test")
    noun_examples = [
        (Noun("ybyrá", "adj.: "), "ybyrárama,ybyrápûera"),
        (Noun("embi'u", "(t)"), "embi'urama,embi'upûera"),
        (Noun("só", ""), "sórama,sópûera"),
        (Noun("nhũ", "v.tr. (r, s)"), "nhũnama,nhũmbûera"),
        (Noun("kunumĩ", "v.intr."), "kunumĩnama,kunumĩmbûera"),
        (Noun("anhanga", "v.intr."), "anhangûama,anhangûera"),
        (Noun("oka", "(r, s)"), "okûama,okûera"),
        (Noun("pesaba", "v.intr."), "pesagûama,pesagûera"),
        (Noun("sema", "v.intr."), "sẽgûama,sembûera"),
        (Noun("mena", "v.intr."), "menama,mendera"),
        (Noun("pira", "v.intr."), "pirama,pirera"),
    ]
    print()
    for noun_example, solution in noun_examples:
        if (
            noun_example.ram().substantivo() not in solution
            or noun_example.puer().substantivo() not in solution
        ):
            print(
                noun_example.verbete(),
                "\t",
                noun_example.ram(),
                "\t",
                noun_example.puer(),
                "\t",
                solution,
            )
    n = Noun("embi'u", "(t)").puer().possessive("1ps")
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)

    print()
    print("(r)emi- test")
    noun_examples = [
        (Noun("ka'u", "adj.: "), "eminga'u"),
        (Noun("su'u", ""), "emindu'u"),
        (Noun("potar", ""), "emimbotara"),
        (Noun("tym", ""), "emityma"),
        (Noun("tyr", ""), "embindyra"),
        (Noun("'u", ""), "embi'u"),
    ]
    print()
    for noun_example, solution in noun_examples:
        if noun_example.emi().substantivo() not in solution:
            print(noun_example.verbete(), "\t", noun_example.emi(), "\t", solution)
    n = Noun("'u", "(v.tr) ingerir").emi().puer().possessive("1ps")
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)

    print()
    print("pyr- test")
    noun_examples = [
        (Noun("îuká", "adj.: "), "i îukápyra"),
        (Noun("aûsub", "(s)"), "saûsupyra"),
        (Noun("potar", ""), "i potarypyra"),
        (Noun("kuab", ""), "i kuapyra"),
    ]
    print()
    for noun_example, solution in noun_examples:
        if noun_example.pyr().substantivo().strip() != solution.strip():
            print(noun_example.verbete(), "\t", noun_example.pyr(), "\t", solution)
    n = Noun("'u", "(v.tr.) ingerir").pyr().ram().puer().possessive("1ps")
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)
