from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun
from .copula import Copula


class Noun(Predicate):
    def __init__(self, value, definition="", inflection=None, pro_drop=False):
        """Initialize a Noun object."""
        super().__init__(
            verbete=value, category="noun", min_args=0, definition=definition
        )
        self.noun = TupiNoun(self.verbete, definition)
        self._inflection = inflection
        if inflection:
            self.plural = "pp" in inflection
        self.pro_drop = pro_drop
        for val, infl in self.noun.personal_inflections.items():
            if self.verbete.lower() == infl[0]:
                self._inflection = val
                break

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete
        self.noun = TupiNoun(self.verbete, self.definition)

    def __pos__(self):
        """
        Mark noun as pro_drop the predicate using the + operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.pro_drop = True
        return neg

    def preval(self, annotated=False):
        """Evaluate the Noun object."""
        vbt = self.noun.substantivo(annotated)
        if self.negated:
            # neg_prefix = "nd" if vbt[0] in self.noun.vogais else "nda"
            vbt = self.noun.eym().substantivo(annotated)
        return vbt

    def __mul__(self, other):
        # When its another Noun, we treat it as a possessive construction
        if isinstance(other, Noun):
            possessor = self.copy()
            base_noun = other.copy()

            base_noun.arguments.append(possessor)
            base_noun.noun = base_noun.noun.possessive(
                possessor._inflection,
                None
                if possessor.category == "pronoun"
                else possessor.eval(annotated=True),
            )
            base_noun.noun.pluriforme = possessor.noun.pluriforme
            return base_noun
        # Otherwise, treat itself as the argument to the other predicate
        return other * self

    def __eq__(self, other):
        # Make sure both are Noun objects
        # if not isinstance(other, self.__class__) or not isinstance(other, Copula):
        #     # raise error that the types being compared are not the same
        #     raise TypeError(f"Cannot compare Noun object with {type(other)} object.")
        return Copula() * self * other

    def inflection(self, setter=None):
        if setter:
            self._inflection = setter
        return self._inflection

    def __repr__(self):
        return self.eval(annotated=False)


class ProperNoun(Noun):
    def __init__(self, value):
        super().__init__(value=value, inflection="3p", definition=value, pro_drop=False)


class Pronoun(Noun):
    def __init__(self, inflection, pro_drop=False, definition=""):
        """Initialize a Pronoun object."""
        pronoun = TupiNoun.personal_inflections[inflection][0]
        super().__init__(value=pronoun, inflection=inflection, pro_drop=pro_drop, definition=definition)
        self.category = "pronoun"


ixé = Pronoun("1ps", definition="I")
îandé = Pronoun("1ppi", definition="we (inclusive)")
oré = Pronoun("1ppe", definition="we (exclusive)")
endé = Pronoun("2ps", definition="you")
pee = Pronoun("2pp", definition="y'all'")
ae = Pronoun("3p", definition="he/she/it/they")
îe = Pronoun("refl", definition="to oneself, one's own")
îo = Pronoun("mut", definition="to one another")

pronoun_verbetes = [x.verbete for x in [ixé, îandé, oré, endé, pee, ae]]
