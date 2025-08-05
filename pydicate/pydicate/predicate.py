from copy import deepcopy
import re
from tupi import Noun as TupiNoun
from pydicate.trackable import Trackable

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

class Predicate(Trackable):
    def __init__(self, verbete, category, min_args, max_args=None, definition="", tag="[PREDICATE]"):
        """
        Initialize a Predicate object.
        :param verbete: The core lexeme or word root.
        :param category: The linguistic category (e.g., 'verb', 'noun').
        :param min_args: Minimum number of required arguments.
        :param max_args: Maximum number of arguments (default: same as min_args; None for unlimited).
        """
        super().__init__()
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
            f"{self.var_name} = " + self.__class__.__name__ + f"(verbete=\"{self.verbete}\", category=\"{self.category}\", "
            f"arguments=[{args}], pre_adjuncts=[{pre_adjuncts}], post_adjuncts=[{post_adjuncts}], "
            f"min_args={self.min_args}, max_args={self.max_args}, "
            f"negated={self.negated}, rua={self.rua}, definition=\"{self.definition}\", tag=\"{self.tag}\")"
        )


    def simple_signature(self):
        tr = self.var_name
        return (
            f"{self.var_name if self.var_name else self.verbete.replace("'", "_")} = " + self.__class__.__name__ + f"(\"{self.verbete}\", definition=\"{self.definition}\", tag=\"{self.tag}\")"
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
    
    def definition_simple(self):
        """
        Get the first part of the definition, split by comma (not including initial () which should be ignored for the , split but then reprepended before returning)
        :return: The first part of the definition or an empty string if no definition is set.
        """
        parts = self.definition.split(") ")
        if len(parts) == 1:
            return parts[0].split(",")[0].strip()
        elif len(parts) > 1:
            return parts[0] + ") " + parts[1].split(",")[0].strip()

    def same_subject(self):
        one = self.subject() if self.subject() else None
        princ = self.principal.subject() if (self.principal.subject() and self.is_subordinated()) else None
        return one.verbete == princ.verbete if one and princ else False

    def subordinate(self, sub, pre=True):
        subordinated = sub.copy()
        principalled = self.copy()
        subordinated.principal = principalled
        if pre:
            principalled.pre_adjuncts.append(subordinated)
        else:
            principalled.post_adjuncts.append(subordinated)
        return principalled

    def format_tag(self):
        tf = [escape_latex(x.lower().capitalize().replace("_", " ")) for x in self.tag[1:-1].split(":")]
        return "\\textit{" + (", ".join(tf)) + "}"
    
    def __len__(self):
        return 1 + sum(len(x) for x in self.arguments + self.pre_adjuncts + self.post_adjuncts)

    def __lshift__(self, other):
        return self.subordinate(other, pre=False)

    def __rshift__(self, other):
        return other.subordinate(self, pre=True)
    
    def to_forest_tree(self, indent=0, ctype='result', parent=None) -> str:
        """
        Recursively generate a forest-compatible LaTeX forest package string from a Predicate.
        Displays tag (if present) below the word using \shortstack.
        Adds an intermediate stripped node if tag is present and eval != verbete.
        Appends adjuncts at the same level as the core predicate.
        """
        indent_str = " " # "\t" * indent
        child_indent = " " #  "\n" + "\t" * (indent + 1)

        # Compose top label

        this = self.copy()
        if indent != 0:
            this.principal = None  # Prevent recursion
        label_text = escape_latex(this.eval())
        style_pre = f"""
edge path={{
    \\noexpand\path[black!200, draw]
    (\\forestoption{{name}}.east) .. controls +(north:7pt) and +(north:7pt) .. (core{indent-1}{id(parent)}.west) \\forestoption{{edge label}};
}}
"""
        
        style_post = f"""
edge path={{
    \\noexpand\path[black!200, draw]
    (\\forestoption{{name}}.west) .. controls +(north:7pt) and +(north:7pt) .. (core{indent-1}{id(parent)}.east) \\forestoption{{edge label}};
}}
"""
        style = ", " + (style_pre if ctype == 'pre_adjunct' else style_post)
        if 'adjunct' not in ctype:
            style = ""
        if self.tag and (not self.arguments or ctype in ['core']):
            tag_text = self.format_tag()
            if len(self.arguments) == 0 and self.definition:
                def_text = escape_latex(self.definition_simple())
                label = f"[\\shortstack{{\\textit{{{label_text}}} \\\\ \\texttt{{{tag_text}}} \\\\ \\texttt{{{def_text}}}}}, {ctype}{style}"
            else:
                label = f"[\\shortstack{{\\textit{{{label_text}}} \\\\ \\texttt{{{tag_text}}}}}, {ctype}{style}"
        else:
            if len(self.arguments) == 0 and self.definition:
                def_text = escape_latex(self.definition_simple())
                label = f"[\\shortstack{{\\textit{{{label_text}}} \\\\ \\texttt{{{def_text}}}}}, {ctype}{style}"
            else:
                label = f"[\\textit{{{label_text}}}, {ctype}{style}"

        # Collect post_adjuncts (they go to the left in rendering)
        post_children = [
            adj.to_forest_tree(indent + 1, ctype='pre_adjunct', parent=self)
            for adj in self.pre_adjuncts or []
        ]
        # Collect pre_adjuncts (they go to the right in rendering)
        pre_children = [
            adj.to_forest_tree(indent + 1, ctype='post_adjunct', parent=self)
            for adj in reversed(self.post_adjuncts or [])
        ]
        # Collect arguments (default style, can be tagged 'arg' if desired)
        arg_children = [
            arg.to_forest_tree(indent + 1, ctype='arg', parent=self) for arg in reversed(self.arguments or [])
        ]

        children = []

        # Prepare stripped node
        stripped = self.copy()
        stripped.pre_adjuncts = []
        stripped.post_adjuncts = []
        stripped.principal = None
        if self.arguments and stripped.eval() != stripped.verbete:
            stripped_text = escape_latex(stripped.verbete)
            tag_label = ""
            def_label = ""
            if stripped.tag:
                tag_label = f" \\\\ \\texttt{{{stripped.format_tag()}}}"
            if stripped.definition:
                def_label = f" \\\\ \\texttt{{{escape_latex(stripped.definition_simple())}}}"
            if tag_label or def_label:
                core_label = f"\\shortstack{{\\textit{{{stripped_text}}}{tag_label}{def_label}}}"
            else:
                core_label = f"\\textit{{{stripped_text}}}"

            stripped_node = f"[{core_label}, core, name=core{indent}{id(self)}" + child_indent + child_indent.join(arg_children) + f"]"
            children.append(stripped_node)
        else:
            children.extend(arg_children)

        # Combine all
        all_children = pre_children + children + post_children

        if all_children:
            child_str = child_indent + child_indent.join(all_children)
            return f"{label} {child_str}\n{indent_str}]"
        else:
            retval = f"{label}]"
            # retval = f"[, {ctype} "+retval[1:]
            return retval


def escape_latex(text: str) -> str:
    return (
        text.replace("\\", "\\textbackslash{}")
            .replace("{", "\\textbraceleft{}")
            .replace("}", "\\textbraceright{}")
            .replace("_", "\\_")
            .replace("#", "\\#")
            .replace("%", "\\%")
            .replace("&", "\\&")
            .replace("^", "\\^{}")
            .replace("~", "\\~{}")
    )