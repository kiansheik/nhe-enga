from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")

from tupi import Noun as TupiNoun


class Copula(Predicate):
    def __init__(self, definition="to be"):
        """Initialize a Copula object."""
        super().__init__(verbete="=", category="Copula", min_args=1, max_args=2, definition=definition)
        self.negated = False

    def preval(self, annotated=False):
        """Evaluate the Copula object."""
        first = self.arguments[0]
        vbt = first.eval(annotated=annotated)
        if self.negated:
            neg_prefix = "nd" if vbt[0] in TupiNoun.vogais else "nda"
            vbt = f"{neg_prefix} {vbt} ruã"
        nec = " ".join([x.eval(annotated=annotated) for x in self.arguments[1:]])
        nec = f"{vbt} {nec}"
        if self.post_adjuncts:
            nec += " " + " ".join([x.eval(annotated=annotated) for x in self.post_adjuncts])
        if self.pre_adjuncts:
            nec = (
                " ".join([x.eval(annotated=annotated) for x in self.pre_adjuncts])
                + " "
                + nec
            )
        return nec

    def __eq__(self, other):
        if isinstance(other, Copula):
            retval = self
            for arg in other.arguments:
                retval *= arg
            return retval
        return self * other
        # raise TypeError(f"Cannot compare Noun object with {type(other)} object.")