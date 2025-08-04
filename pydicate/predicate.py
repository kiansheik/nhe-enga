from copy import deepcopy
import re
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun

# let's make a function which takes a string and where there are sumbolys like ˜i, ˜u, ˆy, ˜y, ´y; it will combine then into a single unicode character
def combine_symbols(s):
    symbol_map = {
        "˜i": "ĩ",
        "˜u": "ũ",
        "ˆy": "ŷ",
        "˜y": "ỹ",
        "´y": "ý"
    }
    for key, value in symbol_map.items():
        s = s.replace(key, value)
    return s

def remove_adjacent_tags(to_remove_from):
    # Remove adjacent duplicate tags from the string.
    pattern = r"(\[.*?\])(?=\1)"
    return re.sub(pattern, "", to_remove_from)

class Predicate:
    def __init__(self, verbete, category, min_args, max_args=None, definition="", tag="[PREDICATE]"):
        """
        Initialize a Predicate object.
        :param verbete: The core lexeme or word root.
        :param category: The linguistic category (e.g., 'verb', 'noun').
        :param min_args: Minimum number of required arguments.
        :param max_args: Maximum number of arguments (default: same as min_args; None for unlimited).
        """
        self.verbete = combine_symbols(verbete)
        self.category = category
        self.min_args = min_args
        self.max_args = max_args if max_args is not None else min_args
        self.arguments = []
        self.compositions = []
        self.pre_adjuncts = []
        self.post_adjuncts = []
        self.negated = False
        self.definition = definition
        self.principal = None
        self.rua = False
        self.tag = tag  # Tag for the predicate, useful for debugging or annotation

    def copy(self):
        """
        Create a deep copy of the predicate.
        :return: A deep copy of the predicate.
        """
        return deepcopy(self)

    def __mul__(self, other):
        """
        Add an argument using the * operator.
        :param other: The argument to add.
        :return: Self (to enable chaining).
        """
        if self.max_args is not None and len(self.arguments) >= self.max_args:
            raise ValueError(
                f"Cannot add more arguments. Max arguments ({self.max_args}) reached."
            )
        mult = self.copy()
        other_copy = other.copy()
        mult.arguments.append(other_copy)
        return mult

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete

    def compose(self, modifier):
        """
        use the / operator to compose predicates
        :return: Self (to enable chaining).
        """
        orig = self.copy()
        orig_n = TupiNoun(self.verbete, self.definition)
        mod_n = TupiNoun(modifier.verbete, modifier.definition)
        new_n = orig_n.compose(mod_n).verbete()
        # Modify the copy of self
        orig.definition = self.definition
        orig.compositions += [modifier]
        orig.refresh_verbete(new_n)
        return orig

    def __truediv__(self, modifier):
        return self.compose(modifier)

    def __neg__(self):
        """
        Negate the predicate using the - operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.negated = not neg.negated
        return neg

    def __add__(self, other):
        """
        Add an adjunct using the + operator.
        :param other: The adjunct to add.
        :return: Self (to enable chaining).
        """
        mult = self.copy()
        other_copy = other.copy()
        mult.post_adjuncts.append(other_copy)
        return mult

    def __addpre__(self, other):
        """
        Add an adjunct using the + operator.
        :param other: The adjunct to add.
        :return: Self (to enable chaining).
        """
        mult = self.copy()
        other_copy = other.copy()
        mult.pre_adjuncts.append(other_copy)
        return mult

    def is_valid(self):
        """
        Check if the predicate has a valid number of arguments.
        :return: True if the number of arguments is within the min/max range, False otherwise.
        """
        return len(self.arguments) >= self.min_args

    def __ne__(self, other):
        return -(self == other)

    def signature(self):
        args = ", ".join(repr(arg) for arg in self.arguments)
        pre_adjuncts = ", ".join(repr(adj) for adj in self.pre_adjuncts)
        post_adjuncts = ", ".join(repr(adj) for adj in self.post_adjuncts)
        return (
            f"Predicate(verbete={self.verbete}, category={self.category}, "
            f"arguments=[{args}], pre_adjuncts=[{pre_adjuncts}], post_adjuncts=[{post_adjuncts}], "
            f"min_args={self.min_args}, max_args={self.max_args})"
        )


    def semantic(self):
        """
        Get self.definition for each of the arguments and adjuncts recusrively and show it in a clear string representation. 
        Assume each argument and adjunct is a Predicate object.
        """
        args = ", ".join(arg.semantic() for arg in self.arguments)
        pre_adjuncts = " + ".join(adj.semantic() for adj in reversed(self.pre_adjuncts))
        if len(pre_adjuncts) > 1:
            pre_adjuncts = f"({pre_adjuncts}) >> "
        post_adjuncts = " + ".join(adj.semantic() for adj in self.post_adjuncts)
        if len(post_adjuncts) > 1:
            post_adjuncts = f" << ({post_adjuncts})"
        if args:
            args = f"({args})"
        return f"{pre_adjuncts}[{self.definition if self.definition else self.tag}]{args}{post_adjuncts}"
    
    def __repr__(self):
        return self.eval(annotated=False)

    def __str__(self):
        return self.__repr__()

    def eval(self, annotated=False):
        prev = self.copy()
        pre = prev.preval(annotated=annotated).strip()
        neg = "" if not annotated else "[NEGATION_PARTICLE:NA]"
        neg_suf = "" if not annotated else "[NEGATION_PARTICLE:RUA]"
        if prev.rua:
            pre = f"nda{neg} {pre} ruã{neg_suf}"
        return remove_adjacent_tags(pre).strip()

    def __invert__(self):
        """
        Mark noun as negative copula the predicate using the ~ operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.rua = True
        return neg

    def preval(self, annotated=False):
        """
        Evaluate the predicate by applying the arguments and adjuncts.
        Default response: f"{self.verbete}(args...) + adjunct1 + adjunct2 + ..."
        :return: The result of applying the predicate.
        """
        prev = self.copy()
        args = ", ".join(arg.eval(annotated=annotated) for arg in prev.arguments)
        pre_adjuncts = (
            " + ".join(adj.eval(annotated=annotated) for adj in prev.pre_adjuncts)
            if prev.pre_adjuncts
            else ""
        )
        post_adjuncts = (
            " + ".join(adj.eval(annotated=annotated) for adj in prev.post_adjuncts)
            if prev.post_adjuncts
            else ""
        )
        repr = f"{prev.verbete}"
        args_repr = f"{repr}({args})" if args else repr
        post_adjuncts_repr = (
            f"{args_repr} + {post_adjuncts}" if post_adjuncts else args_repr
        )
        pre_adjuncts_repr = (
            f"{pre_adjuncts} + {post_adjuncts_repr}"
            if pre_adjuncts
            else post_adjuncts_repr
        )
        return pre_adjuncts_repr

    def is_subordinated(self):
        return self.principal is not None

    def subject(self):
        return self.arguments[0] if self.arguments else None

    def same_subject(self):
        if self.is_subordinated():
            return self.subject().verbete == self.principal.subject().verbete
        return None

    def same_subject(self):
        return self.subject().verbete == self.principal.subject().verbete

    def subordinate(self, sub, pre=True):
        subordinated = sub.copy()
        principalled = self.copy()
        subordinated.principal = principalled
        if pre:
            principalled.pre_adjuncts.append(subordinated)
        else:
            principalled.post_adjuncts.append(subordinated)
        return principalled

    def __lshift__(self, other):
        return self.subordinate(other, pre=False)

    def __rshift__(self, other):
        return other.subordinate(self, pre=True)
