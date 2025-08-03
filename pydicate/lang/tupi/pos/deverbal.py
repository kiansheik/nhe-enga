from .noun import Noun
from .verb import Verb
from .y_fix import YFix
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
            retval = self.morphology(verb, annotated=annotated)
            for adj in verb.pre_adjuncts:
                retval = adj.eval(annotated=annotated) + " " + retval
            for adj in verb.post_adjuncts:
                sepchar = " "
                # remove [*] from end of retval and get last character
                lastchar = verb.verb.remove_brackets_and_contents(retval).strip()[-1]
                if type(adj) == YFix and (
                    lastchar not in (verb.verb.vogais + verb.verb.semi_vogais)
                ):
                    sepchar = "y" + ("[CONSONANT_CLASH]" if annotated else "")
                retval = retval + sepchar + adj.eval(annotated=annotated)
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

    return nom.sara().substantivo(annotated)


bae = Deverbal("ba'e", definition="refers to subject of the verb, the doer, the agent", tag="[DEVERBAL:AGENT]")
bae.morphology = bae_morphology

sara = Deverbal("sara", definition="refers to subject of the verb, the doer, the agent", tag="[DEVERBAL:AGENT]")
sara.morphology = sara_morphology

