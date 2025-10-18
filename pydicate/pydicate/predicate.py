from copy import deepcopy
import re
import inspect
from xml.etree.ElementTree import indent
from tupi import Noun as TupiNoun
from pydicate.trackable import Trackable
from pydicate.dbexplorer import NavarroDB

db_explorer = NavarroDB()

REGISTRY = dict()
FULL_REGISTRY = []


# let's make a function which takes a string and where there are sumbolys like ˜i, ˜u, ˆy, ˜y, ´y; it will combine then into a single unicode character
def combine_symbols(s):
    symbol_map = {"˜i": "ĩ", "˜u": "ũ", "ˆy": "ŷ", "˜y": "ỹ", "´y": "ý", "˜e": "ẽ"}
    for key, value in symbol_map.items():
        s = s.replace(key, value)
    return s


def remove_adjacent_tags(to_remove_from):
    # Remove adjacent duplicate tags from the string.
    pattern = r"(\[.*?\])(?=\1)"
    return re.sub(pattern, "", to_remove_from)


class Predicate(Trackable):
    def __init__(
        self,
        verbete,
        category,
        min_args,
        max_args=None,
        definition="",
        tag="[PREDICATE]",
    ):
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
        self._inflection = None
        self.pre_adjuncts = []
        self.post_adjuncts = []
        self.v_adjuncts = []
        self.v_adjuncts_pre = []
        self.negated = False
        self.definition = definition
        self.principal = None
        self.rua = False
        self.tag = tag  # Tag for the predicate, useful for debugging or annotation
        self.gloss = (
            db_explorer.search_word(self.verbete, self.category)
            if db_explorer
            else None
        )
        self.functional_definition = definition
        self.functional_gloss = None
        if self.gloss and len(self.gloss) > 0:
            for g in self.gloss:
                # find the g.definition that is most similar to definition
                if g.definition and definition in g.definition:
                    self.functional_definition = g.definition
                    self.functional_gloss = g
                    break

    def inflection(self):
        """
        Get the inflection of the predicate.
        :return: The inflection of the predicate.
        """
        if self._inflection:
            return self._inflection
        if len(self.arguments) > 0:
            return self.arguments[0].inflection()
        else:
            return "3p"

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
        orig_n = TupiNoun(orig.verbete, orig.definition, noroot=True)
        mod_n = TupiNoun(modifier.verbete, modifier.definition, noroot=True)
        new_n = orig_n.compose(mod_n).verbete(True)
        # Modify the copy of self
        orig.compositions += [modifier]
        orig.refresh_verbete(new_n)

        # Compose irregular forms if present
        if (
            hasattr(self, "verb")
            and hasattr(self.verb, "irregular")
            and isinstance(self.verb.irregular, dict)
        ):
            new_irregular = {}
            for k1, v1 in self.verb.irregular.items():
                new_irregular[k1] = {}
                for k2, v2 in v1.items():
                    new_irregular[k1][k2] = {}
                    for k3, v3 in v2.items():
                        # Compose the verbete for each irregular form
                        base_verbete = v3.get("verbete", "")
                        base_n = TupiNoun(base_verbete, orig.definition, noroot=True)
                        composed_n = base_n.compose(mod_n)
                        new_verbete = composed_n.verbete(True)
                        # Copy other fields
                        new_irregular[k1][k2][k3] = dict(v3)
                        new_irregular[k1][k2][k3]["verbete"] = new_verbete
            orig.verb.irregular = new_irregular
            orig.verb.pluriforme = orig.verb.pluriforme
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
        pre_adjuncts = ", ".join(
            repr(adj) for adj in self.v_adjuncts_pre + self.pre_adjuncts
        )
        post_adjuncts = ", ".join(
            repr(adj) for adj in self.v_adjuncts + self.post_adjuncts
        )
        return (
            f"{self.var_name} = "
            + self.__class__.__name__
            + f'(verbete="{self.verbete}", category="{self.category}", '
            f"arguments=[{args}], pre_adjuncts=[{pre_adjuncts}], post_adjuncts=[{post_adjuncts}], "
            f"min_args={self.min_args}, max_args={self.max_args}, "
            f'negated={self.negated}, rua={self.rua}, definition="{self.definition}", tag="{self.tag}")'
        )

    def simple_signature(self):
        tr = self.var_name
        tr = (
            self.var_name
            if self.var_name
            else self.verbete.replace("'", "_")
            .replace(" ", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
        )
        if self.category == "pronoun":
            vbt = self.inflection()
        else:
            vbt = self.verbete
        return (
            f"{tr} = "
            + self.__class__.__name__
            + f'("{vbt}", definition="{self.definition}", tag="{self.tag}")'
        )

    def semantic(self):
        """
        Get self.definition for each of the arguments and adjuncts recusrively and show it in a clear string representation.
        Assume each argument and adjunct is a Predicate object.
        """
        args = ", ".join(arg.semantic() for arg in self.arguments)
        pre_adjuncts = " + ".join(
            adj.semantic() for adj in reversed(self.v_adjuncts_pre + self.pre_adjuncts)
        )
        if len(pre_adjuncts) > 1:
            pre_adjuncts = f"({pre_adjuncts}) >> "
        post_adjuncts = " + ".join(
            adj.semantic() for adj in self.v_adjuncts + self.post_adjuncts
        )
        if len(post_adjuncts) > 1:
            post_adjuncts = f" << ({post_adjuncts})"
        if args:
            args = f"({args})"
        if False and self.functional_gloss:
            tl = ", ".join(self.functional_gloss.english_glosses)
        else:
            comp_glosses = []
            for comp in self.compositions:
                if comp.functional_gloss:
                    comp_glosses.extend(comp.functional_gloss.english_glosses)
            tl = (
                ", ".join([y for x in self.gloss for y in x.english_glosses])
                if self.gloss
                else self.definition
                if self.definition
                else self.tag
            )
            # add comp_glosses in as adjectives
            if comp_glosses:
                # make it aparent in structure that these are modifiers of meaning on the original term like adjectives
                tl = f"{tl} meanings_modifying_previous_term([{', '.join(comp_glosses)}])"
        return f"{pre_adjuncts}[{tl}]{args}{post_adjuncts}"

    def __repr__(self):
        return self.eval(annotated=False)

    def __pos__(self):
        """
        Mark noun as pro_drop the predicate using the + operator.
        :return: Self (to enable chaining).
        """
        neg = self.copy()
        neg.pro_drop = True
        return neg

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

    def is_gerund_composto(self):
        for adj in (
            self.v_adjuncts_pre
            + self.pre_adjuncts
            + self.v_adjuncts
            + self.post_adjuncts
        ):
            if adj.principal == self and adj.same_subject():
                return adj
        return None

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
        JOIN_STR = ",\n"
        clean_def = self.definition.strip()
        if "); " in self.definition:
            clean_def_idx = clean_def.index("); ")
            clean_def = clean_def[clean_def_idx + 3 :].strip()
        if self.functional_gloss:
            return (
                JOIN_STR.join(self.functional_gloss.english_glosses[:3])
            )
        elif self.gloss:
            # if the clean_def string appears in any of the gloss definitions, return that gloss's english_glosses
            for g in self.gloss:
                if clean_def and g.definition and clean_def in g.definition:
                    return JOIN_STR.join(g.english_glosses[:3])
            # then check if it appears in any of the english_glosses themselves, if so return those english_glosses
            for g in self.gloss:
                if clean_def and any(
                    clean_def in eg for eg in g.english_glosses
                ):
                    return JOIN_STR.join(g.english_glosses[:3])
            # if we get to the end, return the first gloss's english_glosses which is not None or empty
            for g in self.gloss:
                if g.english_glosses and len(g.english_glosses) > 0:
                    return JOIN_STR.join(g.english_glosses[:3])
        else:
            parts = self.definition.split(") ")
            if len(parts) == 1:
                return JOIN_STR.join(x.strip() for x in parts[0].split(",")[:1]).strip()
            elif len(parts) > 1:
                return (
                    parts[0]
                    + ") "
                    + JOIN_STR.join(x.strip() for x in parts[1].split(",")[:1]).strip()
                )

    def same_subject(self):
        one = self.subject() if self.subject() else None
        princ = (
            self.principal.subject()
            if (self.principal.subject() and self.is_subordinated())
            else None
        )
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
        tf = [
            escape_latex(x.lower().capitalize().replace("_", " "))
            for x in self.tag[1:-1].split(":")
        ]
        return "\\textit{" + (", ".join(tf)) + "}"

    def __len__(self):
        return 1 + sum(
            len(x)
            for x in self.arguments
            + self.pre_adjuncts
            + self.post_adjuncts
            + self.v_adjuncts
            + self.v_adjuncts_pre
        )

    def __lshift__(self, other):
        return self.subordinate(other, pre=False)

    def __rshift__(self, other):
        if self.category != "verb" and other.category == "verb":
            self_cop = self.copy()
            other_cop = other.copy()
            other_cop.v_adjuncts_pre.append(self_cop)
            return other_cop
        return other.subordinate(self, pre=True)

    def translation_prompt(self, target_lang="English"):
        """
        Generate a prompt for translating a Tupi passage with grammatical annotation and syntax tree.
        :param target_lang: The target language for translation (default: English).
        :return: A formatted prompt string.
        """
        prompt = (
            f"The following passage is in Tupi, annotated grammatically.\n"
            f"Below, you see the same sentence structure represented hierarchically as a syntax tree, "
            f"recursively showing each part with English glosses as node values, including both arguments and adjuncts.\n"
            f"There are multiple sentences in the same narrative.\n"
            f"Interpret each into a {target_lang} story, choosing the best words to represent the meaning and structure.\n"
            f"Do not be creative; pay close attention to context and provide the most accurate {target_lang} interpretation possible."
        )
        output = [prompt, "\n\n"]
        output.append(f"{self.eval(annotated=False)}.")
        output.append("")
        output.append(f"{self.eval(annotated=True)}.")
        output.append("")
        output.append(f"{self.semantic()}")

        result_string = "\n\n".join(output)
        return result_string

    def to_forest_tree(self, indent=0, ctype="result", parent=None, links=None):
        """
        Returns a tuple: (forest_body_str, tikz_overlay_str_list).
        - forest_body_str: Forest node string (with children) for inclusion inside \begin{forest}...\end{forest}
        - tikz_overlay_str_list: list of strings with TikZ \path[...] ...; to draw AFTER the forest
        """
        if links is None:
            links = []

        augmentee = getattr(self, "_augmentee", None)
        augmentor = getattr(self, "_augmentor", None)
        effective_self = self.copy()
        if augmentee is not None:
            effective_arguments = [augmentee]
            effective_self = augmentor.copy()
        else:
            effective_arguments = list(self.arguments or [])

        indent_str = " "
        child_indent = " "

        # ---- Safe, unique node names ----
        myname = f"n{indent}_{id(self)}"

        # ---- Build label text ----
        this = effective_self.copy()
        if indent != 0:
            this.principal = None  # Prevent recursion
        label_text = escape_latex(self.eval())

        # label content with optional tag/definition
        if effective_self.tag and (not effective_arguments or ctype in ["core"]):
            tag_text = effective_self.format_tag()
            if not effective_arguments and effective_self.definition_simple():
                def_text = escape_latex_forest_node(effective_self.definition_simple())
                label = (
                    f"[\\shortstack{{\\textit{{{label_text}}} \\\\ "
                    f"\\texttt{{{tag_text}}} \\\\ \\texttt{{{def_text}}}}}, "
                    f"{ctype}, name={myname}"
                )
            else:
                label = (
                    f"[\\shortstack{{\\textit{{{label_text}}} \\\\ "
                    f"\\texttt{{{tag_text}}}}}, {ctype}, name={myname}"
                )
        else:
            if not effective_arguments and effective_self.definition_simple():
                def_text = escape_latex_forest_node(effective_self.definition_simple())
                label = (
                    f"[\\shortstack{{\\textit{{{label_text}}} \\\\ "
                    f"\\texttt{{{def_text}}}}}, {ctype}, name={myname}"
                )
            else:
                label = f"[\\textit{{{label_text}}}, {ctype}, name={myname}"

        # ---- children: we will emit CORE first so it exists ----
        # arguments
        arg_children = [
            arg.to_forest_tree(indent + 1, ctype="arg", parent=self, links=links)[0]
            for arg in reversed(effective_arguments)
        ]

        # stripped core (if needed)
        children = []
        stripped = effective_self.copy()
        stripped.pre_adjuncts = []
        stripped.post_adjuncts = []
        stripped.principal = None
        if effective_arguments and stripped.eval() != stripped.verbete:
            stripped_text = escape_latex(stripped.verbete)
            bits = [f"\\textit{{{stripped_text}}}"]
            if stripped.tag:
                bits.append(f"\\texttt{{{stripped.format_tag()}}}")
            if stripped.definition_simple():
                bits.append(f"\\texttt{{{escape_latex_forest_node(stripped.definition_simple())}}}")
            core_label = "\\shortstack{" + " \\\\ ".join(bits) + "}"

            core_name = f"n{indent}_core_{id(self)}"
            stripped_node = (
                f"[{core_label}, core, name={core_name}"
                + child_indent
                + child_indent.join(arg_children)
                + f"]"
            )
            children.append(stripped_node)
        else:
            core_name = myname  # if no extra core node, the current node is the anchor
            children.extend(arg_children)

        # adjuncts
        pre_adjuncts = list(reversed((self.v_adjuncts + self.post_adjuncts) or []))
        post_adjuncts = (self.v_adjuncts_pre + self.pre_adjuncts) or []

        pre_children = []
        for adj in pre_adjuncts:
            subtree, adj_links = adj.to_forest_tree(indent + 1, ctype="pre_adjunct", parent=self, links=links)
            pre_children.append(subtree)
            # cross-edge: adjunct (east) -> core (west)
            adj_name = f"n{indent+1}_{id(adj)}"
            links.append(
                f"\\path[black!70] ({adj_name}.east) .. controls +(0,7pt) and +(0,7pt) .. ({core_name}.west);"
            )

        post_children = []
        for adj in post_adjuncts:
            subtree, adj_links = adj.to_forest_tree(indent + 1, ctype="post_adjunct", parent=self, links=links)
            post_children.append(subtree)
            # cross-edge: adjunct (west) -> core (east)
            adj_name = f"n{indent+1}_{id(adj)}"
            links.append(
                f"\\path[black!70] ({adj_name}.west) .. controls +(0,7pt) and +(0,7pt) .. ({core_name}.east);"
            )

        # Emit order: core chunk first so anchors exist, then pre (left), then post (right)
        all_children = children + pre_children + post_children
        if indent == 0:
            all_children = reversed(all_children)
        if all_children:
            child_str = child_indent + child_indent.join(all_children)
            forest_str = f"{label} {child_str}\n{indent_str}]"
        else:
            forest_str = f"{label}]"

        return forest_str, links


def stack3(head=None, tag=None, gloss=None, align="l"):
    rows = []
    if head:
        rows.append(r"{\headfont " + head + "}")
    if tag:
        rows.append(r"{\tagfont " + tag + "}")
    if gloss:
        rows.append(r"{\glossfont " + gloss + "}")
    return r"\shortstack[" + align + "]{" + r" \\ ".join(rows) + "}"

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

def escape_latex_forest_node(text: str) -> str:
    # For Forest/TikZ NODE CONTENT ONLY
    # (1) Do NOT escape backslashes (we need \\ for line breaks)
    s = (text.replace("{", "\\{").replace("}", "\\}")
             .replace("_", "\\_").replace("#", "\\#")
             .replace("%", "\\%").replace("&", "\\&")
             .replace("^", "\\^{}").replace("~", "\\~{}"))
    # (2) Support both real newlines and literal "\n"
    s = s.replace("\\n", r"\\").replace("\n", r"\\")
    # (3) Keep the breaks confined to the node with a shortstack
    return r"\shortstack{" + s + r"}"
