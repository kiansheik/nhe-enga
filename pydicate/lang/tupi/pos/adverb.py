from ....predicate import Predicate


class Adverb(Predicate):
    def __init__(self, value, definition="", tag="[ADVERB]"):
        """Initialize a Adverb object."""
        super().__init__(verbete=value, category="adverb", min_args=0, max_args=None, definition=definition)
        self.tag = tag

    def preval(self, annotated=False):
        """Evaluate the Adverb object."""
        if annotated:
            return f"{self.verbete}{self.tag}"
        return self.verbete

    def __add__(self, other):
        return other.__addpre__(self)
