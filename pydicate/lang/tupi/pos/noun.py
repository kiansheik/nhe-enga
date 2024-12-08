from ....predicate import Predicate
import sys
sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun

class Noun(Predicate):
    def __init__(self, value):
        """Initialize a Noun object."""
        super().__init__(verbete=value, category="noun", min_args=0)
        self.noun = TupiNoun(value,"")

    def eval(self):
        """Evaluate the Noun object."""
        return self.noun.verbete()
    
    def __repr__(self):
        return f"Noun({self.verbete})"

