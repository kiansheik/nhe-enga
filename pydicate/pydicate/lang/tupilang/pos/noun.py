from pydicate import Predicate
from tupi import Noun as TupiNoun
from pydicate.lang.tupilang.pos.copula import Copula
from tupi import AnnotatedString


class Noun(Predicate):
    def __init__(
        self,
        value,
        definition="",
        inflection=None,
        pro_drop=False,
        tag="[NOUN]",
        category="noun",
    ):
        """Initialize a Noun object."""
        super().__init__(
            verbete=value, category=category, min_args=0, definition=definition, tag=tag
        )
        self.noun = TupiNoun(self.verbete, self.functional_definition)
        self._inflection = inflection
        if inflection:
            self.plural = "pp" in inflection
        self.pro_drop = pro_drop
        for val, infl in self.noun.personal_inflections.items():
            if self.verbete.lower() == infl[0]:
                self._inflection = val
                break
        self.posto = "posposto"

    def refresh_verbete(self, new_verbete):
        old = self.copy()
        self.verbete = new_verbete
        self.noun = TupiNoun(self.verbete, self.definition)
        self.noun.m_pluriforme = old.noun.m_pluriforme
        self.noun.pluriforme = old.noun.pluriforme

    def __pos__(self):
        """
        Mark noun as pro_drop the predicate using the + operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.pro_drop = True
        return neg

    def __add__(self, other):
        """
        Add a Noun or Copula to the current Noun.
        :param other: The Noun or Copula to add.
        :return: A new Noun with the added argument.
        """
        if isinstance(other, Conjunction):
            cop = self.copy()
            conj = other.copy()
            # add cop to front of arguments
            conj.arguments.insert(0, cop)
            return conj
        if isinstance(other, (Noun)):
            cop = self.copy()
            oth = other.copy()
            conj = Conjunction("", tag="[CONJUNCTION:AND]")
            conj.arguments.append(cop)
            conj.arguments.append(oth)
            return conj
        return super().__add__(other)

    def __addpre__(self, other):
        """
        Add an adjunct using the + operator.
        :param other: The adjunct to add.
        :return: Self (to enable chaining).
        """
        mult = self.copy()
        other_copy = other.copy()
        # prepend the adjunct to the pre_adjuncts
        mult.pre_adjuncts.insert(0, other_copy)
        return mult

    def noun_function(self, neg=False, annotated=False):
        """Return the noun in its base form."""
        if neg:
            return self.noun.eym().absoluta().substantivo(annotated)
        return self.noun.absoluta().substantivo(annotated)

    def preval(self, annotated=False):
        """Evaluate the Noun object."""
        vbt = self.noun_function(neg=self.negated, annotated=annotated)
        ret_val = f"{vbt}{self.tag if annotated else ''}"
        for adj in self.pre_adjuncts:
            ret_val = f"{adj.eval(annotated=annotated)} {ret_val}"
        ret_val = ret_val.strip()
        for adj in self.post_adjuncts:
            ret_val = f"{ret_val} {adj.eval(annotated=annotated)}"
        return ret_val.strip()

    def __mul__(self, other):
        # When its another Noun, we treat it as a possessive construction
        if other.verbete == "emi":
            deverbal = other.copy()
            deverbal.arguments[0].arguments.append(self.copy())
            return deverbal
        if "deverbal" in other.category:
            possessor = self.copy()
            base_noun = Noun(other.eval(True), definition=other.definition)

            base_noun.arguments.append(possessor)
            base_noun.noun = base_noun.noun.possessive(
                possessor.inflection(),
                None
                if possessor.category == "pronoun"
                else possessor.eval(annotated=True),
            )
            base_noun.noun.pluriforme = possessor.noun.pluriforme
            return base_noun
        if isinstance(other, Noun):
            possessor = self.copy()
            base_noun = other.copy()

            base_noun.arguments.append(possessor)
            base_noun.noun = base_noun.noun.possessive(
                possessor.inflection(),
                None
                if possessor.category == "pronoun"
                else possessor.eval(annotated=True),
            )
            base_noun.noun.pluriforme = possessor.noun.pluriforme
            base_noun.noun.m_pluriforme = possessor.noun.m_pluriforme
            return base_noun
        # Otherwise, treat itself as the argument to the other predicate
        self_cop = self.copy()
        other_cop = other.copy()
        self_cop.posto = "anteposto"
        return other_cop * self_cop

    def __eq__(self, other):
        # Make sure both are Noun objects
        # if not isinstance(other, self.__class__) or not isinstance(other, Copula):
        #     # raise error that the types being compared are not the same
        #     raise TypeError(f"Cannot compare Noun object with {type(other)} object.")
        return Copula() * self * other

    def __matmul__(self, other):
        return self.__eq__(other)

    def inflection(self, setter=None):
        if setter:
            self._inflection = setter
        return self._inflection if self._inflection else "3p"

    def __repr__(self):
        return self.eval(annotated=False)

    def voc(self):
        """Return the noun in its vocative form."""
        voc_cop = self.copy()
        voc_cop.noun = voc_cop.noun.vocativo()
        return voc_cop


class Conjunction(Noun):
    def __init__(
        self, value, definition="", tag="[CONJUNCTION]", category="conjunction"
    ):
        """Initialize a Conjunction object."""
        super().__init__(
            value,
            inflection="3p",
            pro_drop=False,
            definition=definition,
            tag=tag,
            category=category,
        )
        self.min_args = 2
        self.tag = tag
        self.max_args = None

    def preval(self, annotated=False):
        """Evaluate the Conjunction object."""
        nec = " ".join([x.eval(annotated=annotated) for x in self.arguments]) + (
            f" {self.verbete}{self.tag}" if self.verbete else f"{self.tag}"
        )
        if self.post_adjuncts:
            # TODO: When evaling adjunct, check if yfix for space or y
            nec += " " + " ".join(
                [x.eval(annotated=annotated).strip() for x in self.adjuncts]
            )
        if self.pre_adjuncts:
            nec = (
                " ".join([x.eval(annotated=annotated) for x in self.pre_adjuncts])
                + " "
                + nec.strip()
            )
        return AnnotatedString(nec).verbete(annotated=annotated).strip()

    def inflection(self):
        retval = "3p"
        arg_inflections = [x.inflection() for x in self.arguments]
        arg_inflections = [x for x in arg_inflections if x]
        # if "1p" or "2p" are present in any strings in arg_inflections, then return true
        if any("1p" in x for x in arg_inflections) and any(
            "2p" in x for x in arg_inflections
        ):
            retval = "1ppi"
        elif any("1p" in x for x in arg_inflections):
            retval = "1ppe"
        elif any("2p" in x for x in arg_inflections):
            retval = "2pp"
        return retval

    def __add__(self, other):
        if isinstance(other, Noun):
            cop = self.copy()
            cop.arguments.append(other.copy())
            return cop
        else:
            return super().__add__(other)


class ProperNoun(Noun):
    def __init__(
        self, value, tag="[PROPER_NOUN]", category="proper_noun", definition=""
    ):
        super().__init__(
            value=value,
            inflection="3p",
            definition=value,
            pro_drop=False,
            tag=tag,
            category=category,
        )

    def noun_function(self, neg=False, annotated=False):
        """Return the noun in its base form."""
        if neg:
            return self.noun.eym().substantivo(annotated)
        return AnnotatedString(f"{self.verbete}{self.tag}").verbete(annotated)


class Pronoun(Noun):
    def __init__(
        self,
        inflection_or_verbete,
        pro_drop=False,
        definition="",
        tag="[PRONOUN]",
        category="pronoun",
    ):
        """Initialize a Pronoun object."""
        if inflection_or_verbete in TupiNoun.personal_inflections.keys():
            pronoun = TupiNoun.personal_inflections[inflection_or_verbete][0]
            inflection = inflection_or_verbete
        else:
            pronoun = inflection_or_verbete
            inflection = "3p"
        super().__init__(
            value=pronoun,
            inflection=inflection,
            pro_drop=pro_drop,
            definition=definition,
            tag=tag,
            category=category,
        )
        self.category = "pronoun"

    def noun_function(self, neg=False, annotated=False):
        """Return the noun in its base form."""
        if neg:
            return AnnotatedString(self.noun.eym().verbete()).verbete(annotated)
        return AnnotatedString(self.noun.verbete()).verbete(annotated)


ixé = Pronoun("1ps", definition="I")
xe = Pronoun("1ps", definition="I")
îandé = Pronoun("1ppi", definition="we (inclusive)")
oré = Pronoun("1ppe", definition="we (exclusive)")
endé = Pronoun("2ps", definition="you")
nde = Pronoun("2ps", definition="you")
pee = Pronoun("2pp", definition="y'all'")
ae = Pronoun("3p", definition="he/she/it/they")
îe = Pronoun(
    "refl", definition="to oneself, one's own", tag="[OBJECT_PREFIX:REFLEXIVE]"
)
îo = Pronoun("mut", definition="to one another", tag="[OBJECT_PREFIX:RECIPROCAL]")
og = Pronoun(
    "o",
    definition="refers to the subject of the main clause",
    tag="[PRONOUN:MAIN_CLAUSE_SUBJECT]",
)
og._inflection = "suj"

asé = Noun(
    "asé", definition="We, people in general, all of us", tag="[PRONOUN:UNIVERSAL_WE]"
)

pronoun_verbetes = [x.verbete for x in [ixé, îandé, oré, endé, pee, ae]]
