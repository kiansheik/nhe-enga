from ....predicate import Predicate
import sys
sys.path.append("/Users/kian/code/nhe-enga/tupi")

class Conjunction(Predicate):
    def __init__(self, value):
        """Initialize a Conjunction object."""
        super().__init__(verbete=value, category="conjunction", min_args=2, max_args=None)

    def eval(self):
        """Evaluate the Conjunction object."""
        nec = " ".join([x.eval() for x in self.arguments]) + " abé"
        if self.adjuncts:
            nec += " " + " ".join([x.eval() for x in self.adjuncts])
        return nec
    
    def __repr__(self):
        return f"Conjunction({self.verbete})"

