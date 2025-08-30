from pydicate import Predicate
from tupi import Noun as TupiNoun


class Copula(Predicate):
    def __init__(
        self,
        definition="copula, to be, the arguments are all identical and one unit",
        category="copula",
    ):
        """Initialize a Copula object."""
        super().__init__(
            verbete="=",
            category=category,
            min_args=1,
            max_args=100000,
            definition=definition,
            tag="[COPULA]",
        )
        self.negated = False
        self.pro_drop = False
        self.posto = "posposto"

    def preval(self, annotated=False):
        """Evaluate the Copula object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}" if annotated else self.verbete
        first = self.arguments[0]
        vbt = first.eval(annotated=annotated)
        if self.negated:
            neg_prefix = "nd" if vbt[0] in TupiNoun.vogais else "nda"
            vbt = f"{neg_prefix} {vbt} ruã"
        nec = " ".join([x.eval(annotated=annotated) for x in self.arguments[1:]])
        nec = f"{vbt} {nec}".strip()
        if self.post_adjuncts:
            nec += " " + " ".join(
                [x.eval(annotated=annotated) for x in self.post_adjuncts]
            )
        if self.pre_adjuncts:
            nec = (
                " ".join([x.eval(annotated=annotated) for x in self.pre_adjuncts])
                + " "
                + nec
            )
        return nec.strip()

    def __eq__(self, other):
        if isinstance(other, Copula):
            retval = self
            for arg in other.arguments:
                retval *= arg
            return retval
        return self * other

    def __matmul__(self, other):
        return self.__eq__(other)

    def __mul__(self, other):
        if other.category == "verb":
            self.posto = "anteposto"
            return other * self
        return super().__mul__(other)


cop = Copula
