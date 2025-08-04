from pydicate import Predicate
from .y_fix import YFix


class Particle(Predicate):
    def __init__(self, value, definition="", tag="[PARTICLE]"):
        """Initialize a Particle object."""
        super().__init__(verbete=value, category="particle", min_args=0, max_args=1, definition=definition)
        self.tag = tag

    def preval(self, annotated=False):
        """Evaluate the Particle object."""
        if annotated:
            return f"{self.verbete}{self.tag}"
        return self.verbete

    def __add__(self, other):
        return other.__addpre__(self)

é = Particle("é", definition="really is, actually is, gives focus to what precedes", tag="[PARTICLE:FOCUS]")
te = Particle("te", definition="ADVERSATIVE discourse marker, shifting focus to what precedes it, 'on the other hand...', 'but this in contrast...", tag="[PARTICLE:ADVERSATIVE]")