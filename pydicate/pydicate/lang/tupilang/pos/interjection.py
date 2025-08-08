from pydicate import Predicate


class Interjection(Predicate):
    def __init__(self, value, definition="", tag="[INTERJECTION]", category="interjection"):
        """Initialize a Interjection object."""
        super().__init__(
            verbete=value,
            category=category,
            min_args=0,
            max_args=0,
            definition=definition,
            tag=tag
        )

    def preval(self, annotated=False):
        """Evaluate the Interjection object."""
        if annotated:
            return f"{self.verbete}{self.tag}"
        return self.verbete

    def __add__(self, other):
        return other.__addpre__(self)


pá = Interjection("pá", definition="yes, affirmative", tag="[INTERJECTION:AFFIRMATIVE]")
