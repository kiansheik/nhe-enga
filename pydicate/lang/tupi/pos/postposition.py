from .adverb import Adverb
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun

class Postposition(Adverb):
    def __init__(self, value):
        """Initialize a Postposition object."""
        super().__init__(value)
        self.category="Postposition"
        self.min_args = 1
        self.max_args = 1

    def preval(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 1:
            arg0 = self.arguments[0].verbete
            found = False
            for val, infl in TupiNoun.personal_inflections.items():
                if arg0.lower() == infl[0]:
                    arg0 = infl[1]
                    found = True
                    break
            if not found:
                arg0 = self.arguments[0].eval(annotated=annotated)
            return f"{arg0} {self.verbete}"
        return self.verbete

    def __repr__(self):
        return f"Postposition({self.verbete})"

sosé = Postposition("sosé")
koty = Postposition("koty")