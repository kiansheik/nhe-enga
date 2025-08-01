from ....predicate import Predicate
from .noun import Noun
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")


class Conjunction(Noun):
    def __init__(self, value, definition=""):
        """Initialize a Conjunction object."""
        super().__init__(value, inflection="3p", pro_drop=False, definition=definition)
        self.category = "conjunction"
        self.min_args = 2
        self.max_args = None

    def preval(self, annotated=False):
        """Evaluate the Conjunction object."""
        nec = (
            " ".join([x.eval(annotated=annotated) for x in self.arguments])
            + f" {self.verbete}"
        )
        if self.post_adjuncts:
            # TODO: When evaling adjunct, check if yfix for space or y
            nec += " " + " ".join([x.eval(annotated=annotated) for x in self.adjuncts])
        if self.pre_adjuncts:
            nec = (
                " ".join([x.eval(annotated=annotated) for x in self.pre_adjuncts])
                + " "
                + nec
            )
        return nec

    def inflection(self):
        retval = "3p"
        arg_inflections = [x.inflection() for x in self.arguments]
        # if "1p" or "2p" are present in any strings in arg_inflections, then return true
        if any("1p" in x for x in arg_inflections) and any(
            "2p" in x for x in arg_inflections
        ):
            retval = "1ppi"
        elif any("1p" in x for x in arg_inflections):
            retval = "1ppe"
        elif any("2p" in x for x in arg_inflections):
            retval = "2pp"
        return retval
