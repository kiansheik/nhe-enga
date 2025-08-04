from pydicate.lang.tupilang.pos.verb import Verb  # only used for type checking, not at runtime

from pydicate.lang.tupilang.pos.noun import Noun
from pydicate.lang.tupilang.pos.y_fix import YFix
from tupi import Noun as TupiNoun, AnnotatedString
from copy import deepcopy

class Deverbal(Noun):
    def __init__(self, value, definition="", tag="[DEVERBAL]"):
        """Initialize a Deverbal object."""
        super().__init__(value, inflection=None, pro_drop=False, definition=definition)
        self.min_args = 0
        self.max_args = 1
        self.category = "deverbal"
        self.tag = tag

    def morphology(self, verb, annotated=False):
        return verb.eval(annotated=annotated)

    def preval(self, annotated=False):
        retval = ""
        if self.arguments:
            verb = self.arguments[0]
            mf = self.morphology(verb, annotated=annotated)
            retval = ""
            for adj in verb.pre_adjuncts:
                retval = adj.eval(annotated=annotated) + " " + retval
            for adj in verb.post_adjuncts:
                retval = retval + " " + adj.eval(annotated=annotated)
            retval = f"{retval} {mf}".strip()
        else:
            retval = AnnotatedString(f"{self.verbete}{self.tag}").verbete(annotated=annotated)
        return retval

    def __mul__(self, other):
        if isinstance(other, Verb):
            cop = self.copy()
            cop.arguments.append(other)
            return cop
        else:
            return super().__mul__(other)

def bae_morphology(verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    if len(verb.arguments) == 2:
        if verb.arguments[1].inflection() in ["3p", None]:
            return verb.verb.bae(obj=verb.arguments[1].eval(annotated=annotated), anotar=annotated)
        else:
            return sara_morphology(verb, annotated=annotated)
    return verb.verb.bae(anotar=annotated)

def sara_morphology(verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    vbt = verb.copy()
    vbt.arguments[0].pro_drop = True
    nom = vbt.base_nominal(annotated=annotated)

    return nom.noun.sara().substantivo(annotated)

def a_morphology(verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    vbt = verb.copy()
    nom = vbt.base_nominal(annotated=annotated)

    return nom.noun.substantivo(annotated)


bae = Deverbal("ba'e", definition="refers to subject of the verb, the doer, the agent", tag="[DEVERBAL:AGENT]")
bae.morphology = bae_morphology

sara = Deverbal("sara", definition="refers to subject of the verb, the doer, the agent", tag="[DEVERBAL:AGENT]")
sara.morphology = sara_morphology

a = Deverbal("a", definition="verbal action, instance of verb, basic noun related to verb", tag="[DEVERBAL:BASIC]")
a.morphology = a_morphology

# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
saba = Deverbal("saba", definition="Adverbial complement nominalizer, the who/what/where/when/how or why a verb happened", tag="[DEVERBAL:CIRCUMSTANTIAL]")
saba.morphology = lambda verb, annotated=False: verb.base_nominal(annotated).noun.saba().substantivo(annotated).strip()
