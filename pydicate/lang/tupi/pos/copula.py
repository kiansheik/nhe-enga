from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")


class Copula(Predicate):
    def __init__(self):
        """Initialize a Copula object."""
        super().__init__(verbete="=", category="Copula", min_args=2, max_args=None)
        self.negated = False

    def eval(self):
        """Evaluate the Copula object."""
        first = self.arguments[0]
        vbt = first.noun.verbete()
        if self.negated:
            neg_prefix = "nd" if vbt[0] in first.noun.vogais else "nda"
            vbt = f"{neg_prefix} {vbt} ruã"
        nec = " ".join([x.eval() for x in self.arguments[1:]])
        nec = f"{vbt} {nec}"
        if self.post_adjuncts:
            nec += " " + " ".join([x.eval() for x in self.adjuncts])
        if self.pre_adjuncts:
            nec = " ".join([x.eval() for x in self.pre_adjuncts]) + " " + nec
        return nec

    def __eq__(self, other):
        if isinstance(other, Copula):
            retval = self
            for arg in other.arguments:
                retval *= arg
            return retval
        return self * other
        # raise TypeError(f"Cannot compare Noun object with {type(other)} object.")

    def __repr__(self):
        return f"Copula({self.verbete})"
