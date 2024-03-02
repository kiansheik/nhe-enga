from tupi import TupiAntigo
import copy

sara_consoante_map = {
    "b": "par",
    "k": "kar",
    "m": "mbar",
    "n": "ndar",
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
        self.base_verbete = verbete  # The name of the verb in its dictionary form
        self.latest_verbete = verbete  # The name of the verb in its dictionary form
        self.raw_definition = raw_definition  # Raw definition of the verb (string)
        self.aglutinantes = [self]

        self.pluriforme = (
            "(s)" in self.raw_definition
            or "(r, s)" in self.raw_definition
            or "-s-" in self.raw_definition
        )

    def verbete(self):
        return self.latest_verbete
    
    def base_substantivo(self):
        return f"{self.verbete()}{'a' if self.verbete()[-1] not in self.vogais else ''}"
        
    def substantivo(self):
        return self.base_substantivo()
    
    def __repr__(self) -> str:
        return self.substantivo()
    
    def __str__(self) -> str:
        return repr(self)

    # TODO: Implement rest of phonetic changes
    def saba(self):
        ret_noun = copy.deepcopy(self)
        vbt = ret_noun.verbete()
        if vbt[-1] in ret_noun.vogais:
            ret_noun.latest_verbete = f"{ret_noun.verbete()}b"
        else:
            ret_noun.latest_verbete = f"{ret_noun.verbete()[:-1]}{saba_consoante_map[ret_noun.verbete()[-1]]}"
        ret_noun.aglutinantes.append(ret_noun)
        return ret_noun
    
    # TODO: Implement rest of phonetic changes
    def sara(self):
        ret_noun = copy.deepcopy(self)
        vbt = ret_noun.verbete()
        if self.ends_with(vbt, self.vogais_nasais):
            ret_noun.latest_verbete = f"{vbt}an"  
        elif self.ends_with(vbt, ["î"]):
            if self.ends_with(vbt[:-1], self.nasais):
                ret_noun.latest_verbete = f"{vbt}ndar"   
            else:
                ret_noun.latest_verbete = f"{vbt}tar"           
        elif vbt[-1] == 'o' and vbt[-2] in (self.vogais + ["'"]):
            ret_noun.latest_verbete = f"{vbt[:-1]}ûar"    
        elif vbt[-2:] == 'ng':
            ret_noun.latest_verbete = f"{vbt}ar" 
        elif vbt[-1] in sara_consoante_map.keys():
            ret_noun.latest_verbete = f"{vbt[:-1]}{sara_consoante_map[vbt[-1]]}"
        else:
            ret_noun.latest_verbete = f"{vbt}sar"
        ret_noun.aglutinantes.append(ret_noun)
        return ret_noun

    # TODO: Implement rest of phonetic changes
    def saba(self):
        ret_noun = copy.deepcopy(self)
        vbt = ret_noun.verbete()
        if self.ends_with(vbt, self.vogais_nasais):
            ret_noun.latest_verbete = f"{vbt}ab"  
        elif self.ends_with(vbt, ["î"]):
            if self.ends_with(vbt[:-1], self.nasais):
                ret_noun.latest_verbete = f"{vbt}ndab"   
            else:
                ret_noun.latest_verbete = f"{vbt}tab"           
        elif vbt[-1] == 'o' and vbt[-2] in (self.vogais + ["'"]):
            ret_noun.latest_verbete = f"{vbt[:-1]}ûab"    
        elif vbt[-2:] == 'ng':
            ret_noun.latest_verbete = f"{vbt}ab" 
        elif vbt[-1] in sara_consoante_map.keys():
            ret_noun.latest_verbete = f"{vbt[:-1]}{saba_consoante_map[vbt[-1]]}"
        else:
            ret_noun.latest_verbete = f"{vbt}sab"
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