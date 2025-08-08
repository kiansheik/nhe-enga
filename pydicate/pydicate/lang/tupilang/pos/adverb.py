from pydicate import Predicate
from pydicate.lang.tupilang.pos.particle import Particle
from pydicate.lang.tupilang.pos.interjection import Interjection
from tupi import AnnotatedString


class Adverb(Predicate):
    def __init__(self, value, definition="", tag="[ADVERB]", category="adverb"):
        """Initialize a Adverb object."""
        super().__init__(
            verbete=value,
            category=category,
            min_args=0,
            max_args=None,
            definition=definition,
        )
        self.tag = tag

    def preval(self, annotated=False):
        """Evaluate the Adverb object."""
        ret_val = f"{self.verbete}{self.tag}"
        for adj in self.pre_adjuncts:
            ret_val = f"{adj.eval(True)} " + ret_val
        ret_val = ret_val.strip()
        for adj in self.post_adjuncts:
            ret_val += f" {adj.eval(True)}"
        return AnnotatedString(ret_val).verbete(annotated=annotated)

    def __add__(self, other):
        if isinstance(other, Adverb) or isinstance(other, Particle) or isinstance(other, Interjection):
            return super().__add__(other)
        return other.__addpre__(self)


koyré = Adverb(
    "koyré", definition="right now, at this moment", tag="[ADVERB:TEMPORAL:IMMEDIATE]"
)
