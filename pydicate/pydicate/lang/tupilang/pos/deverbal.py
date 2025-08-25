from pydicate.lang.tupilang.pos.verb import (
    Verb,
)  # only used for type checking, not at runtime

from pydicate.lang.tupilang.pos.noun import Noun
from pydicate.lang.tupilang.pos.y_fix import YFix
from tupi import Noun as TupiNoun, AnnotatedString
from copy import deepcopy


class Deverbal(Noun):
    def __init__(
        self, value, definition="", tag="[DEVERBAL]", category="deverbal_noun"
    ):
        """Initialize a Deverbal object."""
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
        if self.arguments and isinstance(self.arguments[0], Verb):
            return TupiNoun(self.eval(True), self.functional_definition, noroot=True)
            # verb = self.arguments[0]
            # vbt = verb.copy()
            # if vbt.arguments:
            #     vbt.arguments[0].pro_drop = True
            # # return TupiNoun(self.eval(True), self.functional_definition)
            # print(self.eval(True))
            # return vbt.base_nominal(True).noun
        return TupiNoun(self.verbete, self.functional_definition, noroot=True)

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
                retval = adj.eval(annotated=annotated) + " " + retval.strip()
            retval = f"{retval.strip()} {mf.strip()}".strip()
            for adj in verb.post_adjuncts:
                retval = retval.strip() + " " + adj.eval(annotated=annotated)
            retval = retval.strip()
        else:
            retval = AnnotatedString(f"{self.verbete}{self.tag}").verbete(
                annotated=annotated
            )
        return retval

    def __mul__(self, other):
        if len(self.arguments) == 1:
            return other * self
        if isinstance(other, Verb) and not self.arguments:
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


class Classifier(Noun):
    def __init__(
        self, value, definition="", tag="[Classifier]", category="classifier_noun"
    ):
        """Initialize a Classifier object."""
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
        if self.arguments and isinstance(self.arguments[0], Noun):
            return TupiNoun(self.eval(True), self.functional_definition, noroot=True)
            # verb = self.arguments[0]
            # vbt = verb.copy()
            # if vbt.arguments:
            #     vbt.arguments[0].pro_drop = True
            # # return TupiNoun(self.eval(True), self.functional_definition)
            # print(self.eval(True))
            # return vbt.base_nominal(True).noun
        return TupiNoun(self.verbete, self.functional_definition, noroot=True)

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
        if isinstance(other, Noun) and not self.arguments:
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


def bae_morphology(self, verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    if len(verb.arguments) == 2:
        if verb.arguments[1].inflection() in ["3p", None]:
            return verb.verb.bae(
                obj=verb.arguments[1].eval(annotated=annotated), anotar=annotated
            )
        else:
            return sara_morphology(verb, annotated=annotated)
    return verb.verb.bae(anotar=annotated)


def pyra_morphology(self, verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    nom = verb.base_nominal(True).noun.pyr()
    if verb.negated:
        nom = nom.eym()
    if self.vocative:
        nom = nom.vocativo()
    return nom.substantivo(annotated)


def emi_morphology(self, verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    if len(verb.arguments) == 2:
        subj = verb.arguments[1]
    elif len(verb.arguments) == 1:
        subj = verb.arguments[0]
    else:
        subj = None
    verb_base = verb.copy()
    verb_base.arguments = []
    nom = verb_base.base_nominal(True).noun.emi()
    if verb.negated:
        nom = nom.eym()
    if subj and subj.inflection() in ["3p", None]:
        nom = nom.possessive(
            subj.inflection(),
            None if subj.category == "pronoun" else subj.eval(annotated=True),
        )
    elif not subj:
        nom = nom.possessive("absoluta", self.pro_drop)
    else:
        nom = nom.possessive(subj.inflection(), None)
    if self.vocative:
        nom = nom.vocativo()
    return nom.substantivo(annotated)


def sara_morphology(self, verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    nom = verb.base_nominal(True).noun
    # breakpoint()
    nom.latest_verbete.drop_until_last_tag()
    if verb.negated:
        nom = nom.eym()
    nom = nom.sara()
    if self.vocative:
        nom = nom.vocativo()
    return nom.substantivo(annotated)


def a_morphology(self, verb, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    vbt = verb.copy()

    return vbt.noun.substantivo(annotated)


bae = Deverbal(
    "ba'e",
    definition="refers to subject of the verb, the doer, the agent",
    tag="[DEVERBAL:AGENT]",
)
bae.morphology = bae_morphology

pyra = Deverbal(
    "pyra",
    definition="passive, patient of verb, the one affected by the action, what will be affected by the verb",
    tag="[DEVERBAL:PATIENT:NO_AGENT]",
)
pyra.morphology = pyra_morphology

emi = Deverbal(
    "emi",
    definition="passive, patient of verb, the one affected by the action, what will be affected by the verb",
    tag="[DEVERBAL:PATIENT:AGENT_EXPLICIT]",
)
emi.morphology = emi_morphology

sara = Deverbal(
    "sara",
    definition="refers to subject of the verb, the doer, the agent",
    tag="[DEVERBAL:AGENT]",
)
sara.morphology = sara_morphology

a = Deverbal(
    "a",
    definition="verbal action, instance of verb, basic noun related to verb",
    tag="[DEVERBAL:BASIC]",
)
a.morphology = a_morphology

# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
saba = Deverbal(
    "saba",
    definition="Adverbial complement nominalizer, the who/what/where/when/how or why a verb happened",
    tag="[DEVERBAL:CIRCUMSTANTIAL]",
)
saba.morphology = (
    lambda self, verb, annotated=False: verb.base_nominal(annotated)
    .noun.saba()
    .substantivo(annotated)
    .strip()
)

# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
rama = Classifier(
    "ram",
    definition="Nominal future, what will be",
    tag="[CLASSIFIER:FUTURE]",
)
rama.morphology = (
    lambda self, verb, annotated=False: verb.noun.ram().substantivo(annotated).strip()
)
# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
pûera = Classifier(
    "pûer",
    definition="Nominal past, what was, ex",
    tag="[CLASSIFIER:PAST]",
)
pûera.morphology = (
    lambda self, verb, annotated=False: verb.noun.puer().substantivo(annotated).strip()
)
