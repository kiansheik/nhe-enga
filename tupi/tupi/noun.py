from tupi import TupiAntigo
import copy

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
    "á": "asab",
    "ó": "osab",
    "í": "isab",
}

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

                n = Noun(root, prefixes)
                for suffix in suffixes.split("]"):
                    
                    if "FACILITY_SUFFIX" in suffix:
                        n = n.saba()
                    if "ACTIVE_AGENT_SUFFIX" in suffix:
                        n = n.sara()
                    if "SUBSTANTIVE_SUFFIX" in suffix:
                        break
                for suffix in suffixes.split("]"):
                    
                    if "FACILITY_SUFFIX" in suffix:
                        n = n.saba()
                    if "ACTIVE_AGENT_SUFFIX" in suffix:
                        n = n.sara()
                    if "SUBSTANTIVE_SUFFIX" in suffix:
                        break
                return self.keep_brackets_contents(prefixes)+root+self.keep_brackets_contents(suffixes), n
            else:
                tokens.append(self.keep_brackets_contents(word.split(']')))
        return f"{input_string}[{input_string}]"

    def verbete(self, anotated=False):
        return self.remove_brackets_and_contents(self.latest_verbete) if not anotated else self.latest_verbete
    
    def base_substantivo(self):
        return f"{self.verbete(anotated=True)}{'a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]' if self.verbete(anotated=False)[-1] not in self.vogais else '[SUBSTANTIVE_SUFFIX:VOWEL_ENDING]'}"
        
    def substantivo(self, anotated=False):
        return self.base_substantivo() if anotated else self.fix_phonetics(self.remove_brackets_and_contents(self.base_substantivo()))
    
    def __repr__(self) -> str:
        return self.substantivo()
    
    def __str__(self) -> str:
        return repr(self)

    # TODO: Implement rest of phonetic changes
    def sara(self):
        ret_noun = copy.deepcopy(self)
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
        ret_noun.latest_verbete += "[ACTIVE_AGENT_SUFFIX]"
        ret_noun.aglutinantes.append(ret_noun)
        return ret_noun


    # TODO: Implement rest of phonetic changes
    def saba(self):
        ret_noun = copy.deepcopy(self)
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
        return ret_noun

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
    def possessive(self, person='3p'):
        if person == 'absoluta':
            return self.absoluta()
        ret_noun = copy.deepcopy(self)
        vbt = ret_noun.verbete(anotated=True)
        pref = ret_noun.pluriform_prefix(person)
        pronoun = f"{self.personal_inflections[person][1]}[POSSESSIVE_PRONOUN:{person}]"
        ret_noun.latest_verbete = f"{'' if '3p' in person and self.pluriforme else pronoun} {pref}{vbt}".strip()
        ret_noun.aglutinantes.append(ret_noun)
        return ret_noun
        # TODO: Implement rest of phonetic changes
    def absoluta(self):
        ret_noun = copy.deepcopy(self)
        vbt = self.remove_parens_and_contents(ret_noun.verbete(anotated=True))
        pref = ret_noun.pluriform_prefix('absoluta')
        ret_noun.latest_verbete = f"{pref}{vbt}".strip()
        ret_noun.aglutinantes.append(ret_noun)
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
    for noun_example, solution in noun_examples:
        print(noun_example.verbete(), "\t", noun_example.sara())
        # print("\tBase substantivo:\t", noun_example.substantivo())
        # print("\tSaba form:\t", noun_example.saba())
        # print(noun_example.verbete)
        # print(noun_example.base_substantivo)
        # print(noun_example.pluriforme)
        # print(noun_example.saba())