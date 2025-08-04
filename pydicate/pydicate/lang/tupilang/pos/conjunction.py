from .noun import Noun
from tupi import AnnotatedString

class Conjunction(Noun):
    def __init__(self, value, definition="", tag="[CONJUNCTION]"):
        """Initialize a Conjunction object."""
        super().__init__(value, inflection="3p", pro_drop=False, definition=definition)
        self.category = "conjunction"
        self.min_args = 2
        self.tag = tag
        self.max_args = None

    def preval(self, annotated=False):
        """Evaluate the Conjunction object."""
        nec = (
            " ".join([x.eval(annotated=annotated) for x in self.arguments])
            + f" {self.verbete}{self.tag}"
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
        return AnnotatedString(nec).verbete(annotated=annotated)

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

    def __mul__(self, other):
        if isinstance(other, Noun):
            cop = self.copy()
            cop.arguments.append(other.copy())
            return cop
        else:
            return super().__mul__(other)