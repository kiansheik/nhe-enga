from .noun import Noun
from copy import deepcopy
from tupi import AnnotatedString

class Demonstrative(Noun):
    def __init__(self, value, definition="", tag="[DEMONSTRATIVE]"):
        """Initialize a Demonstrative object."""
        super().__init__(value, inflection=None, pro_drop=False, definition=definition)
        self.min_args = 0
        self.max_args = 1
        self.category = "demonstrative"
        self.tag = tag

    def preval(self, annotated=False):
        """Evaluate the Demonstrative object."""
        if len(self.arguments) >= 1:
            arg0 = self.arguments[0].copy()
            vbt = arg0.noun.latest_verbete
            vbt.insert_prefix(f"{self.verbete}{self.tag} ")
            return arg0.eval(annotated)
        # TODO: a few demonstratives have multiple attested noun forms, so we need to handle that in the future
        suf = "ba'e[SUBSTANTIVE_SUFFIX:DEMONSTRATIVE_VOWEL_ENDING]"
        if any(self.noun.verbete().endswith(x) for x in self.noun.consoantes):
            suf = "a[SUBSTANTIVE_SUFFIX:DEMONSTRATIVE_CONSONANT_ENDING]"
        if any(self.noun.verbete().endswith(x) for x in self.noun.vogais_nasais):
            suf = "[SUBSTANTIVE_SUFFIX:DEMONSTRATIVE_NULL_ENDING]"
        pl = AnnotatedString(f"{self.verbete}{self.tag}{suf}")
        return pl.verbete(annotated=annotated)

    def __mul__(self, other):
        if isinstance(other, Noun):
            cop = self.copy()
            cop.arguments.append(other)
            return cop
        return super().__mul__(other)

kó = Demonstrative("kó", tag="[DEMONSTRATIVE:1p:VISIBLE]")
ikó = Demonstrative("ikó", tag="[DEMONSTRATIVE:1p:VISIBLE]")

ã = Demonstrative("ã", tag="[DEMONSTRATIVE:1p:NOT_VISIBLE]")
ang = Demonstrative("ang", tag="[DEMONSTRATIVE:1p:NOT_VISIBLE]")
iang = Demonstrative("iang", tag="[DEMONSTRATIVE:1p:NOT_VISIBLE]")
iã = Demonstrative("iã", tag="[DEMONSTRATIVE:1p:NOT_VISIBLE]")

ebokûeî = Demonstrative("ebokûeî", tag="[DEMONSTRATIVE:2p:VISIBLE]")
ebokûé = Demonstrative("ebokûé", tag="[DEMONSTRATIVE:2p:VISIBLE]")
eboûing = Demonstrative("eboûing", tag="[DEMONSTRATIVE:2p:VISIBLE]")
eboûĩ = Demonstrative("eboûĩ", tag="[DEMONSTRATIVE:2p:VISIBLE]")
ûĩ = Demonstrative("ûĩ", tag="[DEMONSTRATIVE:2p:VISIBLE]")

kûeî = Demonstrative("kûeî", tag="[DEMONSTRATIVE:3p:VISIBLE]")
kûé = Demonstrative("kûé", tag="[DEMONSTRATIVE:3p:VISIBLE]")

akó = Demonstrative("akó", tag="[DEMONSTRATIVE:3p:NOT_VISIBLE]")
akûeî = Demonstrative("akûeî", tag="[DEMONSTRATIVE:3p:NOT_VISIBLE]")
aîpó = Demonstrative("aîpó", tag="[DEMONSTRATIVE:3p:NOT_VISIBLE:AUDIBLE]")

amõ = Demonstrative("amõ", definition="some", tag="[DEMONSTRATIVE:3p:INDETERMINATE]")
amoaé = Demonstrative("amoaé", definition="other, another", tag="[DEMONSTRATIVE:3p:OTHER]")
