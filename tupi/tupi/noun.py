from .tupi import TupiAntigo
from .verb import Verb
import copy, inspect, re

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
    "ó": "osar",
    "á": "asar",
    "í": "isar",
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
    "ó": "osab",
    "á": "asab",
    "í": "isab",
}

def ends_with_any(s, endings):
    return any(s.endswith(ending) for ending in endings)

def starts_with_any(s, endings):
    return any(s.startswith(ending) for ending in endings)

def remove_ending_if_any(s, endings):
    for ending in endings:
        if s.endswith(ending):
            return s[:-len(ending)]
    return s

def remove_starting_if_any(s, endings):
    for ending in endings:
        if s.startswith(ending):
            return s[len(ending):]
    return s

def tokenize_string(annotated_string):
    matches = re.findall(r'([^\s\[\]]+)?\[(.*?)\]', annotated_string)
    notes = [(token, annotation) for token, annotation in matches]
    return notes

class Noun(TupiAntigo):
    def __init__(self, verbete, raw_definition):
        super().__init__()
        self.base_verbete = (verbete if verbete[-1] != 'a' else verbete[:-1]) + "[ROOT]" # The name of the verb in its dictionary form
        self.latest_verbete = self.base_verbete # The name of the verb in its dictionary form
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.aglutinantes = [self]
        raw_def = self.raw_definition[:50]
        if "(r, s)" in raw_def or "(s)" in raw_def or "-s-" in raw_def:
            self.pluriforme = "r, s"
        elif "(s, r, s)" in raw_def:
            self.pluriforme = "s, r, s"
        elif "(t)" in raw_def:
            self.pluriforme = "t"
        elif "(t, t)" in raw_def:
            self.pluriforme = "t, t"
        else:
            self.pluriforme = None
        self.recreate = f'Noun("{self.verbete()}", "({self.pluriforme})")'
        self.ios = "-îo-" in raw_def and "-s-" in raw_def
        self.segunda_classe = (
            "2ª classe" in self.raw_definition or "adj." in self.raw_definition
        )
        self.transitivo ="v.tr." in raw_def.replace(
            " ", ""
        )
        self.ero = self.verbete().startswith("ero") or self.verbete().startswith("eno") or self.verbete().startswith("eru")
        self.objeto_raw = None
    
    def compose(self, modifier):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = ret_noun.verbete()
        vbt_an = ret_noun.verbete(anotated=True)
        mod_vbt = modifier.verbete()
        mod_vbt_an = modifier.verbete(anotated=True)
        # Define some useful groups
        vogais_orais = "á e é i í y ý o ó u ú".split(" ")
        vogais_nasais =  "ã ẽ ĩ ỹ õ ũ".split(" ")
        nasais = "m n ng nh mb nd".split(" ")
        consoantes = "p b t s k ' r gû û î ŷ".split(" ")

        if ends_with_any(vbt, vogais_orais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            last_letter = self.accent_map.get(start[-1], start[-1])
            ret_noun.latest_verbete = f"{start[:-1]}{last_letter}[{parts[-1]}{mod_vbt_an}"
        elif ends_with_any(vbt, nasais) and starts_with_any(mod_vbt, vogais_orais+vogais_nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an}"
        elif ends_with_any(vbt, nasais) and starts_with_any(mod_vbt, consoantes+nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            start = remove_ending_if_any(start, nasais)
            second_last_letter = self.nasal_map.get(start[-1], start[-1])
            first_nasal = self.nasal_prefix_map.get(mod_vbt_an[0], mod_vbt_an[0])
            ret_noun.latest_verbete = f"{start[:-1]}{second_last_letter}[{parts[-1]}{first_nasal}{mod_vbt_an[1:]}"
        elif ends_with_any(vbt, vogais_nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            second_last_letter = self.nasal_map.get(start[-2], start[-2])
            first_nasal = self.nasal_prefix_map.get(mod_vbt_an[0], mod_vbt_an[0])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{first_nasal}{mod_vbt_an[1:]}"
        elif vbt[-1] in self.consoantes:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}{mod_vbt_an}"
        elif vbt[-1] in self.nasais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            other = self.nasal_prefix_map.get(parts[-1][0], parts[-1][0])
            ret_noun.latest_verbete = f"{start[:-1]}[{other}{parts[-1][1:]}{mod_vbt_an}"

        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    
    def verb(self):
        raiz =  self.verbete()
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
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
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
                prefixes = "]".join(root_split[0].split(']')[:-1])
                if prefixes:
                    prefixes += "]"
                root = root_split[0].split(']')[-1]
                print(root, prefixes, suffixes)

                n = Noun(root, prefixes)
                for suffix in suffixes.split("]"):
                    if "FACILITY_SUFFIX" in suffix:
                        n = n.saba()
                    if "ACTIVE_AGENT_SUFFIX" in suffix:
                        n = n.sara()
                    if "SUBSTANTIVE_SUFFIX" in suffix:
                        break
                tokens.append(self.keep_brackets_contents(prefixes)+root+self.keep_brackets_contents(suffixes))
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
        return self.remove_brackets_and_contents(self.latest_verbete) if not anotated else self.latest_verbete
    
    def base_substantivo(self):
        return f"{self.verbete(anotated=True)}{'a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]' if self.verbete(anotated=False)[-1] not in self.vogais else '[SUBSTANTIVE_SUFFIX:VOWEL_ENDING]'}"
        
    def substantivo(self, anotated=False):
        bs = self.base_substantivo() if anotated else self.remove_brackets_and_contents(self.base_substantivo())
        return bs
    
    def __repr__(self) -> str:
        return self.substantivo()
    
    def __str__(self) -> str:
        return repr(self)

    def pluriform_prefix(self, person='absoluta'):
        plf = self.pluriforme
        if plf:
            if '3p' in person:
                if plf == "t, t":
                    return "t[PLURIFORM_PREFIX:T]"
                elif plf:
                    return "s[PLURIFORM_PREFIX:S]"
            if person == 'absoluta':
                if plf == "t, t" or plf == "t":
                    return "t[PLURIFORM_PREFIX:T]"
                if plf == "s, r, s":
                    return "s[PLURIFORM_PREFIX:S]"
            if '1p' in person or '2p' in person:
                return "r[PLURIFORM_PREFIX:R]"
        return ""

    # TODO: Implement rest of phonetic changes
    def sara(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = ret_noun.verbete()
        vbt_an = ret_noun.verbete(anotated=True)
        if self.ends_with(vbt, self.vogais_nasais):
            ret_noun.latest_verbete = f"{vbt_an}an"  
        elif self.ends_with(vbt, ["î"]):
            if self.ends_with(vbt[:-1], self.nasais):
                ret_noun.latest_verbete = f"{vbt_an}ndar"   
            else:
                ret_noun.latest_verbete = f"{vbt_an}tar"           
        elif vbt[-1] == 'o' and vbt[-2] in (self.vogais + ["'"]):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}ûar"    
        elif vbt[-2:] == 'ng':
            ret_noun.latest_verbete = f"{vbt_an}ar" 
        elif vbt[-1] in sara_consoante_map.keys():
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}{sara_consoante_map[vbt[-1]]}"
        elif vbt[-1] not in self.vogais:
            ret_noun.latest_verbete = f"{vbt_an}ar"
        else:
            ret_noun.latest_verbete = f"{vbt_an}sar"
        ret_noun.latest_verbete += "[ABSOLUTE_AGENT_SUFFIX]"
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
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = ret_noun.verbete()
        vbt_an = ret_noun.verbete(anotated=True)
        if self.ends_with(vbt, self.vogais_nasais):
            ret_noun.latest_verbete = f"{vbt_an}ab"  
        elif self.ends_with(vbt, ["î"]):
            if self.ends_with(vbt[:-1], self.nasais):
                ret_noun.latest_verbete = f"{vbt_an}ndab"   
            else:
                ret_noun.latest_verbete = f"{vbt_an}tab"           
        elif vbt[-1] == 'o' and vbt[-2] in (self.vogais + ["'"]):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}ûab"    
        elif vbt[-2:] == 'ng':
            ret_noun.latest_verbete = f"{vbt_an}ab" 
        elif vbt[-1] in sara_consoante_map.keys():
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}{saba_consoante_map[vbt[-1]]}"
        else:
            ret_noun.latest_verbete = f"{vbt_an}sab"
        ret_noun.latest_verbete += "[FACILITY_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun

    # TODO: Implement rest of phonetic changes
    def possessive(self, person='3p'):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        if person == 'absoluta':
            return self.absoluta()
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = self.remove_parens_and_contents(ret_noun.verbete(anotated=True))
        pref = ret_noun.pluriform_prefix(person)
        if pref:
            vbt = ret_noun.verbete(anotated=True).replace('(', '').replace(')', '')
        pronoun = f"{self.personal_inflections[person][1]}[POSSESSIVE_PRONOUN:{person}]"
        ret_noun.latest_verbete = f"{'' if '3p' in person and self.pluriforme else pronoun} {pref}{vbt}".strip()
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
        # TODO: Implement rest of phonetic changes
    def absoluta(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # TODO: Figure out verbetes como '(a)pé' which have the perntheses and that vowel only if there's no prefix
        vbt = self.remove_parens_and_contents(ret_noun.verbete(anotated=True))
        pref = ret_noun.pluriform_prefix('absoluta')
        if pref:
            vbt = ret_noun.verbete(anotated=True).replace('(', '').replace(')', '')
        ret_noun.latest_verbete = f"{pref}{vbt}".strip()
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    def bae(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        if vbt[-1] in 'bmp':
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{self.accent_last_vowel(start[:-1])}[{parts[-1]}ba'e"
        elif vbt[-1] in self.vogais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{self.remove_accent_last_vowel(start)}[{parts[-1]}ba'e"
        else:
            ret_noun.latest_verbete = f"{ret_noun.latest_verbete}yba'e"
        ret_noun.latest_verbete += "[RELATIVE_AGENT_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    def puer(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        if vbt[-1] in self.vogais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}pûer"
            if vbt[-1] in self.vogais_nasais:
                ret_noun.latest_verbete = f"{start}[{parts[-1]}mbûer"
        elif vbt[-1] in ['b']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}gûer"
        elif vbt[-1] in ['n']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}der"
        elif vbt[-1] in ['r']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}ûer"
        elif vbt[-1] in ['m']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}bûer"
        else:
            ret_noun.latest_verbete = f"{ret_noun.latest_verbete}ûer"
        ret_noun.latest_verbete += "[PRETERITE_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    def ram(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        if vbt[-1] in self.vogais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}ram"
            if vbt[-1] in self.vogais_nasais:
                ret_noun.latest_verbete = f"{start}[{parts[-1]}nam"
        elif vbt[-1] in ['b']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}gûam"
        elif vbt[-1] in ['n']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}am"
        elif vbt[-1] in ['r']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}am"
        elif vbt[-1] in ['m']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{self.nasaliza_final(start[:-1])}[{parts[-1]}gûam"
        else:
            ret_noun.latest_verbete = f"{ret_noun.latest_verbete}ûam"
        ret_noun.latest_verbete += "[FUTURE_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    def pyr(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        if vbt[-1] in self.vogais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}pyr"
            if vbt[-1] in self.vogais_nasais:
                ret_noun.latest_verbete = f"{start}[{parts[-1]}mbyr"
        elif vbt[-1] in ['b', 'p']:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start[:-1]}[{parts[-1]}pyr"
        else:
            ret_noun.latest_verbete = f"{ret_noun.latest_verbete}ypyr"
        obj_pref = f"{ret_noun.pluriform_prefix('3p')}"
        if obj_pref:
            obj_pref += "[OBJECT_PRONOUN]"
        else:
            obj_pref = "i[OBJECT_PRONOUN] "
        ret_noun.latest_verbete = f"{obj_pref}{ret_noun.latest_verbete}"
        ret_noun.latest_verbete += "[INDEFINITE_SUBJET_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    # TODO: Not yet tested -reme
    def reme(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        if vbt[-1] in self.vogais:
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}reme"
            if vbt[-1] in self.vogais_nasais:
                ret_noun.latest_verbete = f"{start}[{parts[-1]}reme"
        else:
            ret_noun.latest_verbete = f"{ret_noun.latest_verbete}eme"
        ret_noun.latest_verbete += "[CIRCUMSTANCE_SUBSTANTATIVE_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    def emi(self):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        # --------------------------------
        vbt = self.verbete()
        ret_noun.pluriforme = "t"
        token = "[PATIENT_PREFIX]"
        if vbt[0] in self.nasal_prefix_map.keys():
            # if any of self.nasais are present in vbt
            if not any(nasal in vbt for nasal in self.nasais):
                suf = "emi"
                if self.monosilibica():
                    suf = "embi"
                ret_noun.latest_verbete = f"{suf}{token}{self.nasal_prefix_map[ret_noun.latest_verbete[0]]}{ret_noun.latest_verbete[1:]}"
        elif self.monosilibica() and not any(nasal in vbt for nasal in self.nasais):
            ret_noun.latest_verbete = f"embi{token}{ret_noun.latest_verbete}"
        else:
            ret_noun.latest_verbete = f"emi{token}{ret_noun.latest_verbete}"
        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.segunda_classe = True
        ret_noun.transitivo = False
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun
    
if __name__ == "__main__":
    # Example usage:
    # noun_examples = [Noun("apysyk", "adj.: "),
    #                     Noun("ker", "v.intr."),
    #                     Noun("aûsub", "v.tr. (r, s)"),
    #                     Noun("nhan", "v.intr.")
    # ]
    noun_examples = [(Noun("kytĩ", "adj.: "), "kytĩsara,kytĩana"),
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
        # print("\tBase substantivo:\t", noun_example.substantivo())
        # print("\tSaba form:\t", noun_example.saba())
        # print(noun_example.verbete)
        # print(noun_example.base_substantivo)
        # print(noun_example.pluriforme)
        # print(noun_example.saba())
    n = Noun("(a)pé", "(r, s)")
    print()
    print(n.recreate)
    print(n.verbete())
    print(n.substantivo(True))
    print(n.possessive('absoluta'), n.possessive('absoluta').recreate)
    print(n.possessive('absoluta').possessive('1ps'), n.possessive('absoluta').possessive('1ps').recreate)
    print(n.possessive('1ps'))
    print(n.possessive('3p'), n.possessive('3p').recreate)

    print()
    print("Puera, rama test")
    noun_examples = [(Noun("ybyrá", "adj.: "), "ybyrárama,ybyrápûera"),
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
        if noun_example.ram().substantivo() not in solution or noun_example.puer().substantivo() not in solution:
            print(noun_example.verbete(), "\t", noun_example.ram(), "\t", noun_example.puer(), "\t", solution)
    n = Noun("embi'u", "(t)").puer().possessive('1ps')
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)

    print()
    print("(r)emi- test")
    noun_examples = [(Noun("ka'u", "adj.: "), "eminga'u"),
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
    n = Noun("'u", "(v.tr) ingerir").emi().puer().possessive('1ps')
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)

    print()
    print("pyr- test")
    noun_examples = [(Noun("îuká", "adj.: "), "i îukápyra"),
                        (Noun("aûsub", "(s)"), "saûsupyra"),
                        (Noun("potar", ""), "i potarypyra"),
                        (Noun("kuab", ""), "i kuapyra"),
    ]
    print()
    for noun_example, solution in noun_examples:
        if noun_example.pyr().substantivo().strip() != solution.strip():
            print(noun_example.verbete(), "\t", noun_example.pyr(), "\t", solution)
    n = Noun("'u", "(v.tr.) ingerir").pyr().ram().puer().possessive('1ps')
    print(n)
    print(n.recreate)
    print(n.substantivo(True))
    print(n.aglutinantes)