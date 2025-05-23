from ....predicate import Predicate


class Adverb(Predicate):
    def __init__(self, value):
        """Initialize a Adverb object."""
        super().__init__(verbete=value, category="adverb", min_args=0, max_args=None)

    def preval(self, annotated=False):
        """Evaluate the Adverb object."""
        if annotated:
            return f"{self.verbete}[ADVERB]"
        return self.verbete

    def __add__(self, other):
        return other.__addpre__(self)

    def __repr__(self):
        return f"Adverb({self.verbete})"
