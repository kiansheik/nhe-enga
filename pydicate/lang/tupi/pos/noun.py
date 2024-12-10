from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun
from .copula import Copula


class Noun(Predicate):
    def __init__(self, value, inflection="3p", pro_drop=False, definition=""):
        """Initialize a Noun object."""
        super().__init__(
            verbete=value, category="noun", min_args=0, definition=definition
        )
        self.noun = TupiNoun(value, definition)
        self._inflection = inflection
        self.pro_drop = pro_drop
        for val, infl in self.noun.personal_inflections.items():
            if value.lower() == infl[0]:
                self._inflection = val
                break

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete
        self.noun = TupiNoun(self.verbete, self.definition)

    def __invert__(self):
        """
        Mark noun as pro_drop the predicate using the ~ operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.pro_drop = True
        return neg

    def eval(self):
        """Evaluate the Noun object."""
        vbt = self.noun.substantivo()
        if self.negated:
            neg_prefix = "nd" if vbt[0] in self.noun.vogais else "nda"
            vbt = f"{neg_prefix} {vbt} ruã"
        return vbt

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
        return f"Noun({self.verbete})"


class Pronoun(Noun):
    def __init__(self, inflection, pro_drop=False):
        """Initialize a Prounoun object."""
        pronoun = TupiNoun.personal_inflections[inflection][0]
        super().__init__(value=pronoun, inflection=inflection, pro_drop=pro_drop)
        self.category = "pronoun"


ixé = Pronoun("1ps")
îandé = Pronoun("1ppi")
oré = Pronoun("1ppe")
endé = Pronoun("2ps")
pee = Pronoun("2pp")
ae = Pronoun("3p")
