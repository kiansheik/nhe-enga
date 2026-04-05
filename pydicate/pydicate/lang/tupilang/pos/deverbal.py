from pydicate.lang.tupilang.pos.verb import (
    Verb,
)  # only used for type checking, not at runtime

from pydicate.lang.tupilang.pos.noun import Noun
from pydicate.lang.tupilang.pos.y_fix import YFix
from tupi import Noun as TupiNoun, AnnotatedString
from copy import deepcopy
import re


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
        self.noun_morphology = None
        self.vocative = False

    @property
    def noun(self):
        ret_noun = None
        if self._augment_noun:
            ret_noun = self._augment_noun
        elif self.arguments and isinstance(self.arguments[0], Verb):
            if callable(self.noun_morphology):
                ret_noun = self.noun_morphology(self, self.arguments[0])
            else:
                ret_noun = TupiNoun(
                    self.eval(True), self.functional_definition, noroot=True
                )
                ret_noun.pluriforme = self.arguments[0].verb.pluriforme
            # verb = self.arguments[0]
            # vbt = verb.copy()
            # if vbt.arguments:
            #     vbt.arguments[0].pro_drop = True
            # # ret_noun = TupiNoun(self.eval(True), self.functional_definition)
            # print(self.eval(True))
            # ret_noun = vbt.base_nominal(True).noun
        else:
            ret_noun = TupiNoun(self.verbete, self.functional_definition, noroot=True)
        return ret_noun

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

    def _apply_compositions(self, surface, annotated=False):
        if getattr(self, "_compositions_frozen", False):
            return surface
        if not self.compositions:
            return surface
        composed = TupiNoun(surface, self.functional_definition, noroot=True)
        for modifier in self.compositions:
            mod_surface = modifier.verbete
            use_resolved_surface = getattr(modifier, "category", "") in {
                "deverbal_noun",
                "classifier_noun",
                "deadverbal_noun",
            }
            if use_resolved_surface:
                try:
                    mod_eval = modifier.eval(annotated=True)
                    mod_eval_clean = re.sub(r"\[[^\]]+\]", "", mod_eval).strip()
                    if mod_eval_clean and " " not in mod_eval_clean:
                        mod_surface = mod_eval
                except Exception:
                    pass
            preserve_terminal_a = "[SUBSTANTIVE_SUFFIX:" in mod_surface and (
                getattr(modifier, "category", "")
                in {"deverbal_noun", "classifier_noun", "deadverbal_noun"}
            )
            mod_n = TupiNoun(
                mod_surface,
                modifier.functional_definition,
                noroot=True,
                preserve_terminal_a=preserve_terminal_a,
            )
            composed = composed.compose(mod_n)
        return composed.verbete(annotated)

    def preval(self, annotated=False):
        retval = ""
        if self.arguments:
            verb = self.arguments[0]
            mf = self.morphology(self, verb, annotated=annotated)
            mf = self._apply_compositions(mf, annotated=annotated)
            retval = ""
            for adj in verb.v_adjuncts_pre + verb.pre_adjuncts:
                retval = adj.eval(annotated=annotated) + " " + retval.strip()
            retval = f"{retval.strip()} {mf.strip()}".strip()
            for adj in verb.v_adjuncts + verb.post_adjuncts:
                retval = retval.strip() + " " + adj.eval(annotated=annotated)
            retval = retval.strip()
        else:
            bare = AnnotatedString(f"{self.verbete}{self.tag}").verbete(
                annotated=annotated
            )
            retval = self._apply_compositions(bare, annotated=annotated)
        return retval

    def __mul__(self, other):
        # if len(self.arguments) == 1:
        #     return other * self
        if isinstance(other, Verb) and not self.arguments:
            cop = self.copy()
            cop.arguments.append(other)
            return cop
        else:
            return super().__mul__(other)

    def __add__(self, other):
        if self.vocative:
            return other.__addpre__(self)
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
            arg = self.arguments[0]
            # Preserve stacked classifier surfaces when chaining classifiers.
            if getattr(arg, "category", "") == "classifier_noun":
                try:
                    arg_eval = arg.eval(annotated=True)
                    arg_eval_clean = re.sub(r"\[[^\]]+\]", "", arg_eval).strip()
                    if arg_eval_clean and " " not in arg_eval_clean:
                        return TupiNoun(
                            arg_eval, arg.functional_definition, noroot=True
                        )
                except Exception:
                    pass
            # Morphology should operate on the argument's noun base, not its
            # fully rendered surface (adjuncts are reapplied in preval).
            arg_noun = arg.noun
            if hasattr(arg_noun, "_clone"):
                return arg_noun._clone()
            return deepcopy(arg_noun)
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
            arg = self.arguments[0]
            retval = self.morphology(self, arg, annotated=annotated).strip()
            # Classifiers over deverbals should preserve verbal adjunct context
            # carried by the argument chain.
            arg_pre = list(arg.pre_adjuncts)
            arg_post = list(arg.post_adjuncts)
            if arg.arguments and isinstance(arg.arguments[0], Verb):
                verb = arg.arguments[0]
                arg_pre = list(verb.v_adjuncts_pre) + list(verb.pre_adjuncts) + arg_pre
                arg_post = arg_post + list(verb.v_adjuncts) + list(verb.post_adjuncts)
            for adj in reversed(arg_pre):
                adj_txt = adj.eval(annotated=annotated).strip()
                if adj_txt and adj_txt not in retval:
                    retval = f"{adj_txt} {retval}".strip()
            for adj in arg_post:
                adj_txt = adj.eval(annotated=annotated).strip()
                if adj_txt and adj_txt not in retval:
                    retval = f"{retval} {adj_txt}".strip()
        else:
            retval = AnnotatedString(f"{self.verbete}{self.tag}").verbete(
                annotated=annotated
            )
        for adj in self.pre_adjuncts:
            retval = f"{adj.eval(annotated=annotated)} {retval}".strip()
        for adj in self.post_adjuncts:
            retval = f"{retval} {adj.eval(annotated=annotated)}".strip()
        return retval

    def __mul__(self, other):
        if isinstance(other, Noun) and not self.arguments:
            cop = self.copy()
            cop.arguments.append(other)
            return cop
        else:
            return super().__mul__(other)

    def __add__(self, other):
        if self.vocative:
            return other.__addpre__(self)
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
    if verb.object():
        if verb.object().inflection() in ["3p", "refl", "mut", "suj", None]:
            return verb.verb.bae(
                obj=verb.object().eval(annotated=annotated), anotar=annotated
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


def sara_morphology(self, verbin, annotated=False):
    """Resolve the morphology of the Deverbal object."""
    verb = verbin.copy()
    verb.arguments = [verb.object()] if verb.object() else []
    nom = verb.base_nominal(True).noun
    # breakpoint()
    nom.latest_verbete.drop_until_last_tag()
    if verb.negated:
        nom = nom.eym()
    variation_id = 0 if self.variation_id is None else self.variation_id
    nom = nom.sara(variation_id=variation_id)
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
saba.noun_morphology = lambda self, verb: verb.base_nominal(True).noun.saba()

# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
rama = Classifier(
    "ram",
    definition="Nominal future, what will be",
    tag="[CLASSIFIER:FUTURE]",
)


def rama_morphology(self, verb, annotated=False):
    """
    Morphology for the 'rama' classifier.
    Returns the nominal future form, applying negation if needed.
    """
    noun = self.noun.ram()
    if getattr(self, "negated", False):
        noun = noun.eym()
    return noun.substantivo(annotated).strip()


rama.morphology = rama_morphology
# -sab(a) (suf. nominalizador) - 1) nominalizador de complemento circunstancial. Traduz-se por tempo, lugar, companhia, modo, causa, instrumento, finalidade, etc. Tem os alomorfes -ab(a), -b(a), -á, -ndab(a), etc.: îukasaba - tempo, lugar, instrumento, causa, modo, companhia, etc. de matar (Anch., Arte, 19); ...N'i papasabi. - Não há modo de contá-los. (Ar., Cat., 38); ...i 'ekatûaba kotysaba é... - o que estava à sua direita (isto é, a companhia do lado da sua mão direita) (Anch., Diál. da Fé, 190); Xe 'angorypaba. - A causa da alegria de minha alma. (Anch., Poemas, 106); 2) Forma substantivos abstratos: angaipaba - maldade (lit. - qualidade da alma ruim) (Anch., Teatro, 34)
pûera = Classifier(
    "pûer",
    definition="Nominal past, what was, ex",
    tag="[CLASSIFIER:PAST]",
)
pûera.morphology = (
    lambda sef, verb, annotated=False: sef.noun.puer().substantivo(annotated).strip()
)


def pûer_morphology(self, verb, annotated=False):
    """
    Morphology for the 'pûera' classifier.
    """
    noun = self.noun.puer()
    if getattr(self, "negated", False):
        noun = noun.eym()
    return noun.substantivo(annotated).strip()


pûera.morphology = pûer_morphology
