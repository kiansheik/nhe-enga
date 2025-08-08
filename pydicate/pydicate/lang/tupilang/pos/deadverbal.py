from pydicate.lang.tupilang.pos.verb import (
    Adverb,
)  # only used for type checking, not at runtime

from pydicate.lang.tupilang.pos.noun import Noun
from pydicate.lang.tupilang.pos.y_fix import YFix
from tupi import Noun as TupiNoun, AnnotatedString
from copy import deepcopy


class Deadverbal(Noun):
    def __init__(
        self, value, definition="", tag="[DEADVERBAL]", category="deadverbal_noun"
    ):
        """Initialize a Deadverbal object."""
        super().__init__(
            value,
            inflection=None,
            pro_drop=False,
            definition=definition,
            tag=tag,
            category=category,
        )
        self.min_args = 0
        self.max_args = 1
        self._augment_noun = None
        self.vocative = False

    @property
    def noun(self):
        if self._augment_noun:
            return self._augment_noun
        if self.arguments and isinstance(self.arguments[0], Adverb):
            verb = self.arguments[0]
            vbt = verb.copy()
            if vbt.arguments:
                vbt.arguments[0].pro_drop = True
            return vbt.base_nominal(True).noun
        return TupiNoun(self.verbete, self.functional_definition)

    @noun.setter
    def noun(self, value):
        self._augment_noun = value

    def voc(self):
        """Return the noun in its vocative form."""
        voc_cop = self.copy()
        voc_cop.vocative = True
        return voc_cop

    def morphology(self, sef, verb, annotated=False):
        return verb.eval(annotated=annotated)

    def preval(self, annotated=False):
        retval = ""
        if self.arguments:
            verb = self.arguments[0]
            mf = self.morphology(self, verb, annotated=annotated)
            retval = ""
            for adj in verb.pre_adjuncts:
                retval = adj.eval(annotated=annotated) + " " + retval
            for adj in verb.post_adjuncts:
                retval = retval.strip() + " " + adj.eval(annotated=annotated)
            retval = f"{retval.strip()} {mf}".strip()
        else:
            retval = AnnotatedString(f"{self.verbete}{self.tag}").verbete(
                annotated=annotated
            )
        return retval

    def __mul__(self, other):
        if isinstance(other, Adverb) and not self.arguments:
            cop = self.copy()
            cop.arguments.append(other)
            return cop
        else:
            return super().__mul__(other)

    def __add__(self, other):
        selfcop = self.copy()
        if selfcop.arguments:
            selfcop.arguments[0] = selfcop.arguments[0].__add__(other)
            return selfcop
        return super().__add__(other)

    def __addpre__(self, other):
        selfcop = self.copy()
        if selfcop.arguments:
            selfcop.arguments[0] = selfcop.arguments[0].__addpre__(other)
            return selfcop
        return super().__addpre__(other)


def nduara_morphology(self, adverb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    nom = AnnotatedString(adverb.eval(annotated=annotated))
    if any(nom.endswith(x) for x in TupiNoun.consoantes):
        nom += "i"
        nom += "[CONSONANT_CLASH]"
    nom += "ndûar"
    nom += self.tag
    res = Noun(
        nom.original,
        definition=self.functional_definition
        + ": "
        + self.arguments[0].functional_definition,
        inflection="3p",
        tag=self.tag,
    )
    return res.eval(annotated=annotated)


nduara = Deadverbal(
    "ndûara",
    definition="Adverbial nominalizer, 'what is [ADVERB]', used to turn adverbs into adjectives",
    tag="[DEADVERBAL]",
)
nduara.morphology = nduara_morphology
