from copy import deepcopy
import copy
import re
import inspect
import itertools
import re
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional, NamedTuple
import random
from contextlib import contextmanager
from dataclasses import dataclass, field
from xml.etree.ElementTree import indent
from tupi import Noun as TupiNoun
from tupi import Verb as TupiVerb
from tupi.emit import render_annotated
from pydicate.trackable import Trackable
from pydicate.dbexplorer import NavarroDB
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

db_explorer = NavarroDB()

REGISTRY = dict()
FULL_REGISTRY = []

_NID_COUNTER = itertools.count(1)
_EVAL_CTX = None


@dataclass
class EvalCtx:
    out_by_nid: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MorphPiece:
    surface: str
    tags: Tuple[str, ...]


_MORPH_TAG_RE = re.compile(r"([^\[\]\s]+)((?:\[[^\]]+\])+)", flags=re.UNICODE)
_PEDAGOGICAL_NEWLINE_RE = re.compile(r",n\s*")
_PEDAGOGICAL_LINE_JOIN = " // "


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


@contextmanager
def pushed_eval_ctx(ctx):
    global _EVAL_CTX
    old = _EVAL_CTX
    _EVAL_CTX = ctx
    try:
        yield
    finally:
        _EVAL_CTX = old


def parse_annotated_morphs(s: str) -> List[MorphPiece]:
    out: List[MorphPiece] = []
    i = 0
    n = len(s)
    while i < n:
        while i < n and s[i].isspace():
            i += 1
        if i >= n:
            break

        start = i
        while i < n and s[i] != "[":
            i += 1
        surface = s[start:i].strip()
        if not surface:
            continue

        tags = []
        while i < n and s[i] == "[":
            j = s.find("]", i)
            if j == -1:
                break
            tags.append(s[i + 1 : j])
            i = j + 1

        if not tags:
            tags = ["BARE"]
        out.append(MorphPiece(surface=surface, tags=tuple(sorted(tags))))

    return out


def _as_pairs(emitted):
    if not emitted:
        return []
    first = emitted[0]
    if hasattr(first, "surface") and hasattr(first, "tags"):
        return [(t.surface, set(t.tags)) for t in emitted]
    return [(s, set(tags)) for s, tags in emitted]


def _norm_surface(s: str) -> str:
    # Normalize only for matching, keep original surface for output.
    return s.lstrip()


def _lcs_mapping(A, B):
    """Return one LCS mapping as list[(i_in_A, j_in_B)]."""
    m, n = len(A), len(B)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        ai = A[i]
        for j in range(n):
            if ai == B[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = (
                    dp[i][j + 1] if dp[i][j + 1] >= dp[i + 1][j] else dp[i + 1][j]
                )

    i, j = m, n
    pairs = []
    while i > 0 and j > 0:
        if A[i - 1] == B[j - 1]:
            pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        else:
            # tie-break left (stable-ish)
            if dp[i][j - 1] >= dp[i - 1][j]:
                j -= 1
            else:
                i -= 1
    pairs.reverse()
    return pairs


class _Cand(NamedTuple):
    score: int  # number of matched tokens
    span: tuple[int, int]  # (start,end) in GLOBAL indices (window covering matches)
    mapping: list  # [(local_i, global_i)]
    matched: frozenset  # set of global indices matched


@dataclass
class _Node:
    node_id: str
    nid: int
    parent_id: Optional[str]
    depth: int
    rel_type: str
    kind: str  # "arg" | "pre" | "post"
    verbete: str
    pred_obj: object
    local_parts: list = field(default_factory=list)
    local_norm: list = field(default_factory=list)
    children: list = field(default_factory=list)

    # filled during solving
    core_mapping: list = field(default_factory=list)  # [(local_i, global_i)]
    core_span: Optional[tuple[int, int]] = None


class Predicate(Trackable):
    _COPY_LIST_FIELDS = (
        "arguments",
        "compositions",
        "pre_adjuncts",
        "post_adjuncts",
        "v_adjuncts",
        "v_adjuncts_pre",
        "_arguments",
    )
    _COPY_PREDICATE_FIELDS = ("principal", "_augmentee", "_augmentor", "_subject")

    def __deepcopy__(self, memo):
        cls = self.__class__
        new_obj = cls.__new__(cls)
        memo[id(self)] = new_obj

        # Start with a shallow dict copy, then deep-copy only the fields that
        # actually need isolation. This avoids copying heavy, read-only data.
        new_obj.__dict__ = self.__dict__.copy()

        for field in self._COPY_LIST_FIELDS:
            if field in self.__dict__:
                src = self.__dict__[field]
                new_obj.__dict__[field] = [copy.deepcopy(x, memo) for x in src]

        for field in self._COPY_PREDICATE_FIELDS:
            if field in self.__dict__:
                val = self.__dict__[field]
                if isinstance(val, Predicate):
                    new_obj.__dict__[field] = copy.deepcopy(val, memo)
                else:
                    new_obj.__dict__[field] = val

        # Clone embedded Tupi objects to avoid cross-copy mutation.
        if "verb" in self.__dict__ and isinstance(self.__dict__["verb"], TupiVerb):
            verb = self.__dict__["verb"]
            verb_copy = verb.__class__.__new__(verb.__class__)
            verb_copy.__dict__ = verb.__dict__.copy()
            if isinstance(getattr(verb, "irregular", None), dict):
                verb_copy.irregular = copy.deepcopy(verb.irregular, memo)
            new_obj.__dict__["verb"] = verb_copy

        if "noun" in self.__dict__ and isinstance(self.__dict__["noun"], TupiNoun):
            noun = self.__dict__["noun"]
            if hasattr(noun, "_clone"):
                new_obj.__dict__["noun"] = noun._clone()
            else:
                new_obj.__dict__["noun"] = copy.deepcopy(noun, memo)

        return new_obj

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
        self.nid = f"node_{next(_NID_COUNTER)}"
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
        self.ped_label = None
        self.tag = tag  # Tag for the predicate, useful for debugging or annotation
        self.fname = None  # Filename or picture
        self.variation_id = None  # Variation ID for different forms
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

    @classmethod
    def _default_category(cls):
        try:
            params = inspect.signature(cls.__init__).parameters
        except (TypeError, ValueError):
            return None
        category = params.get("category")
        if category and category.default is not inspect._empty:
            return category.default
        return None

    @classmethod
    def _filter_init_kwargs(cls, kwargs):
        try:
            params = inspect.signature(cls.__init__).parameters
        except (TypeError, ValueError):
            return kwargs
        return {k: v for k, v in kwargs.items() if k in params}

    @classmethod
    def iter_db_entries(cls, category=None, db=None, **predicate_kwargs):
        """
        Iterate over all DB entries of a given category and yield predicate instances.
        If called on a subclass, that subclass is used for instantiation.
        """
        db = db or db_explorer
        if category is None:
            category = cls._default_category()

        def _iter():
            if db is None:
                return
            if category is None:
                raise ValueError("category is required to iterate DB entries.")

            for entry in db.iter_words_by_classname(category):
                if cls is Predicate:
                    min_args = predicate_kwargs.get("min_args", 0)
                    max_args = predicate_kwargs.get("max_args", min_args)
                    init_kwargs = {
                        "category": category,
                        "min_args": min_args,
                        "max_args": max_args,
                        "definition": entry.definition,
                    }
                    if "tag" in predicate_kwargs:
                        init_kwargs["tag"] = predicate_kwargs["tag"]
                    yield cls(entry.verbete, **init_kwargs)
                else:
                    init_kwargs = {"definition": entry.definition}
                    if "category" not in predicate_kwargs:
                        init_kwargs["category"] = category
                    init_kwargs.update(predicate_kwargs)
                    init_kwargs = cls._filter_init_kwargs(init_kwargs)
                    yield cls(entry.verbete, **init_kwargs)

        return _iter()

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

    def var(self, setter):
        """
        set the variation ID of the predicate.
        :param setter: The new variation ID to set (optional).
        :return: The variation ID of the predicate.
        """
        varcop = self.copy()
        if setter is not None:
            varcop.variation_id = setter
        return varcop

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

        # Prefer composing on the realized surface for select noun-like
        # predicates (e.g., classifiers, deadverbals) when it is a single token.
        def _resolve_compose_surface(pred, fallback, respect_apply_compositions=True):
            try:
                from pydicate.lang.tupilang.pos.noun import Noun as PydicateNoun
            except Exception:
                return fallback, False
            if not isinstance(pred, PydicateNoun):
                return fallback, False
            allow_eval_categories = {"classifier_noun", "deadverbal_noun"}
            if getattr(pred, "category", "") not in allow_eval_categories:
                return fallback, False
            # Predicates that already apply compositions to their realized
            # surface should keep their internal structure intact.
            if respect_apply_compositions and hasattr(pred, "_apply_compositions"):
                return fallback, False
            try:
                pred_eval = pred.eval(annotated=True)
                pred_eval_clean = re.sub(r"\[[^\]]+\]", "", pred_eval).strip()
                if pred_eval_clean and " " not in pred_eval_clean:
                    return pred_eval, True
            except Exception:
                pass
            return fallback, False

        orig_surface, orig_used_eval = _resolve_compose_surface(
            orig, orig.verbete, respect_apply_compositions=True
        )
        orig_n = TupiNoun(orig_surface, orig.definition, noroot=True)
        mod_surface = modifier.verbete
        use_resolved_surface = getattr(modifier, "category", "") in {
            "deverbal_noun",
            "classifier_noun",
            "deadverbal_noun",
        }
        # Compose from the realized lexical surface when the modifier is a
        # single-word derived form (e.g., `saba * v(x)` -> `...aba`), while
        # preserving legacy behavior for multiword predicates.
        if use_resolved_surface:
            mod_surface, _ = _resolve_compose_surface(
                modifier, mod_surface, respect_apply_compositions=False
            )
        preserve_terminal_a = "[SUBSTANTIVE_SUFFIX:" in mod_surface and (
            getattr(modifier, "category", "")
            in {"deverbal_noun", "classifier_noun", "deadverbal_noun"}
        )
        mod_n = TupiNoun(
            mod_surface,
            modifier.definition,
            noroot=True,
            preserve_terminal_a=preserve_terminal_a,
        )
        new_n = orig_n.compose(mod_n).verbete(True)
        # Modify the copy of self
        orig.compositions += [modifier]
        orig.refresh_verbete(new_n)
        if orig_used_eval:
            # Freeze the composed surface for noun-like predicates to avoid
            # re-applying their internal morphology/adjuncts.
            orig.arguments = []
            orig.pre_adjuncts = []
            orig.post_adjuncts = []
            orig.v_adjuncts_pre = []
            orig.v_adjuncts = []
            orig._compositions_frozen = True

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

    def eval(self, annotated=False, ctx: Optional[EvalCtx] = None):
        prev = self.copy()
        use_ctx = ctx if ctx is not None else _EVAL_CTX
        if ctx is not None:
            with pushed_eval_ctx(ctx):
                pre = prev.preval(annotated=annotated).strip()
        else:
            pre = prev.preval(annotated=annotated).strip()
        neg = "" if not annotated else "[NEGATION_PARTICLE:NA]"
        neg_suf = "" if not annotated else "[NEGATION_PARTICLE:RUA]"
        if prev.rua:
            pre = f"na{neg} {pre} ruã{neg_suf}"
        out = remove_adjacent_tags(pre).strip()
        if use_ctx is not None:
            use_ctx.out_by_nid[self.nid] = out
        return out

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
        final_pf = (
            f"{pre_adjuncts} + {post_adjuncts_repr}"
            if pre_adjuncts
            else post_adjuncts_repr
        )
        return final_pf

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
            return JOIN_STR.join(self.functional_gloss.english_glosses[:3])
        elif self.gloss:
            # if the clean_def string appears in any of the gloss definitions, return that gloss's english_glosses
            for g in self.gloss:
                if clean_def and g.definition and clean_def in g.definition:
                    return JOIN_STR.join(g.english_glosses[:3])
            # then check if it appears in any of the english_glosses themselves, if so return those english_glosses
            for g in self.gloss:
                if clean_def and any(clean_def in eg for eg in g.english_glosses):
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

    def __iter__(self):
        # Backward compatibility: allow `list += predicate` idiom used in
        # corpus source files by treating a predicate as a single-item iterable.
        yield self

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
        r"""
        Returns a tuple: (forest_body_str, tikz_overlay_str_list).
        - forest_body_str: Forest node string (with children) for inclusion inside \begin{forest}...\end{forest}
        - tikz_overlay_str_list: list of strings with TikZ \path[...] ...; to draw AFTER the forest
        """
        if links is None:
            links = []

        augmentee = getattr(self, "_augmentee", None)
        core_self = self.copy()
        if augmentee is not None:
            effective_arguments = [augmentee]
            core_self = core_self._augmentor.copy()
        else:
            effective_arguments = list(self.arguments or [])

        has_adjuncts = any(
            (
                self.v_adjuncts,
                self.post_adjuncts,
                self.v_adjuncts_pre,
                self.pre_adjuncts,
            )
        )

        has_leaves = effective_arguments or has_adjuncts

        indent_str = " "
        child_indent = " "

        # ---- Safe, unique node names ----
        myname = f"n{indent}_{id(self)}"

        # ---- Build label text ----
        this = self.copy()
        if indent != 0:
            this.principal = None  # Prevent recursion
        label_text = escape_latex(this.eval())

        # label content with optional tag/definition
        if self.tag and (not has_leaves or ctype in ["core"]):
            tag_text = self.format_tag()
            if augmentee is not None or (not has_leaves and self.definition_simple()):
                def_text = escape_latex_forest_node(self.definition_simple())
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
            if augmentee is not None or (not has_leaves and self.definition_simple()):
                def_text = escape_latex_forest_node(self.definition_simple())
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
        stripped = core_self
        stripped.pre_adjuncts = []
        stripped.post_adjuncts = []
        stripped.principal = None
        emit_core_node = has_leaves and self.eval() != stripped.verbete
        cnn = myname
        if emit_core_node:
            stripped_text = escape_latex(stripped.verbete)
            bits = [f"\\textit{{{stripped_text}}}"]
            if stripped.tag:
                bits.append(f"\\texttt{{{stripped.format_tag()}}}")
            if stripped.definition_simple():
                bits.append(
                    f"\\texttt{{{escape_latex_forest_node(stripped.definition_simple())}}}"
                )
            core_label = "\\shortstack{" + " \\\\ ".join(bits) + "}"

            core_name = f"n{indent}_core_{id(self)}"
            cnn = core_name
            if arg_children:
                stripped_node = (
                    f"[{core_label}, core, name={core_name}"
                    + child_indent
                    + child_indent.join(arg_children)
                    + "]"
                )
            else:
                stripped_node = f"[{core_label}, core, name={core_name}]"
            children.append(stripped_node)
        else:
            core_name = myname  # if no extra core node, the current node is the anchor
            children.extend(arg_children)

        # adjuncts
        pre_adjuncts = list(reversed((self.v_adjuncts + self.post_adjuncts) or []))
        post_adjuncts = (self.v_adjuncts_pre + self.pre_adjuncts) or []

        pre_children = []
        for adj in pre_adjuncts:
            subtree, adj_links = adj.to_forest_tree(
                indent + 1, ctype="pre_adjunct", parent=self, links=links
            )
            pre_children.append(subtree)
            # cross-edge: adjunct (east) -> core (west)
            adj_name = f"n{indent+1}_{id(adj)}"
            # links.append(
            #     f"\\path[black!70] ({adj_name}.east) .. controls +(0,7pt) and +(0,7pt) .. ({cnn}.west);"
            # )

        post_children = []
        for adj in post_adjuncts:
            subtree, adj_links = adj.to_forest_tree(
                indent + 1, ctype="post_adjunct", parent=self, links=links
            )
            post_children.append(subtree)
            # cross-edge: adjunct (west) -> core (east)
            adj_name = f"n{indent+1}_{id(adj)}"
            # links.append(
            #     f"\\path[black!70] ({adj_name}.west) .. controls +(0,7pt) and +(0,7pt) .. ({cnn}.east);"
            # )
        # Emit order: core chunk first so anchors exist, then pre (left), then post (right)
        all_children = pre_children + children + post_children
        # if indent == 0:
        #     all_children = reversed(all_children)
        if all_children:
            child_str = child_indent + child_indent.join(all_children)
            forest_str = f"{label} {child_str}\n{indent_str}]"
        else:
            forest_str = f"{label}]"

        return forest_str, links

    def to_semantic_forest(self, indent=0, width_break=3):
        """
        Build the *semantics* forest subtree string.
        width_break: max items per line before inserting '\\' (smaller => taller tree).
        """
        comp_glosses = []
        for comp in getattr(self, "compositions", []) or []:
            if comp.functional_gloss:
                comp_glosses.extend(comp.functional_gloss.english_glosses)

        if getattr(self, "gloss", None):
            base_gloss = [g for x in self.gloss for g in x.english_glosses]
        elif getattr(self, "definition", None):
            base_gloss = [self.definition]
        elif getattr(self, "tag", None):
            base_gloss = [self.tag]
        else:
            base_gloss = [getattr(self, "verbete", "")]

        base_gloss = [escape_latex_forest_node(x) for x in base_gloss]
        comp_glosses = [escape_latex_forest_node(x) for x in comp_glosses]

        # ✅ Centered, wrapped node text
        core_label = _format_semfit_label(
            base_gloss, modifiers=comp_glosses, width_break=width_break
        )

        pre_adjuncts = list(reversed((self.v_adjuncts_pre + self.pre_adjuncts) or []))
        post_adjuncts = (self.v_adjuncts + self.post_adjuncts) or []
        args = list(self.arguments or [])

        def plus_group(nodes, name_op):
            if not nodes:
                return ""
            children = [
                n.to_semantic_forest(indent + 2, width_break=width_break) for n in nodes
            ]
            if len(children) == 1:
                return f"[{name_op}, semop " + " ".join(children) + "]"
            plus = "[$\\oplus$, semop " + " ".join(children) + "]"
            return f"[{name_op}, semop {plus}]"

        pre_branch = plus_group(pre_adjuncts, r"$\gg$")
        arg_branch = plus_group(args, r"$\bullet$")
        post_branch = plus_group(post_adjuncts, r"$\ll$")

        kids = " ".join(x for x in [pre_branch, arg_branch, post_branch] if x)
        name_here = f"s{indent}_{id(self)}"
        return (
            f"[{core_label}, semroot, name={name_here} {kids}]"
            if kids
            else f"[{core_label}, semroot, name={name_here}]"
        )

    def to_semantic_block(
        self,
        width_ratio=0.38,  # narrower nodes => taller tree
        width_break=3,  # more wrapping
        s_sep_pt=5,  # tighter siblings (horizontal)
        l_sep_pt=16,  # more vertical spacing
        edge_style="-Latex",  # either a raw TikZ spec ('-Latex')
        use_named_edge_style=False,  # or a named style (edge_style) set via \tikzset
    ):
        sem_body = self.to_semantic_forest(width_break=width_break)
        # If you defined \tikzset{edge_style/.style=...}, set use_named_edge_style=True
        edge_clause = (
            "edge=edge_style"
            if use_named_edge_style
            else f"edge={{{{ {edge_style} }}}}"
        )

        return rf"""
    % --- semantics tree only ---
    \begingroup
    \setlength\semtextwidth{{{width_ratio}\linewidth}}
    \begin{{forest}}
    for tree={{
    grow'=south,
    s sep={s_sep_pt}pt,
    l sep={l_sep_pt}pt,
    {edge_clause}
    }}
    {sem_body}
    \end{{forest}}
    \endgroup
    """

    def morpheme_tag_frequencies(
        self, annotated_text: Optional[str] = None, top_pairs: Optional[int] = None
    ):
        """
        Parse self.eval(annotated=True) output and compute frequencies.

        All tag counting collapses tags to their *kind* = substring before the first ':'.
        Examples:
        'SUBSTANTIVE_SUFFIX:CONSONANT_ENDING:CLITIC' -> 'SUBSTANTIVE_SUFFIX'

        Returns a dict with:
        - morph_counts: Counter of morpheme -> count
        - tag_counts:   Counter of tag-kind -> count
        - pair_counts:  Counter of (morpheme, tag-kind) -> count
        - latex_morpheme_table: LaTeX tabular (morpheme, freq)
        - latex_tag_table:      LaTeX tabular (tag, freq)
        - latex_pair_table:     LaTeX tabular (morpheme, tag, freq)
        """
        if annotated_text is None:
            annotated_text = self.eval(annotated=True)

        morph_counts = Counter()
        tag_counts = Counter()
        pair_counts = Counter()

        for m in _MORPH_TAG_RE.finditer(annotated_text):
            morph = m.group(1)
            tags_blob = m.group(2)
            tags = re.findall(r"\[([^\]]+)\]", tags_blob)

            morph_counts[morph] += 1
            for t in tags:
                tag_kind = t.split(":", 1)[0]  # <-- take only index 0
                tag_counts[tag_kind] += 1
                pair_counts[(morph, tag_kind)] += 1

        # Sort descending by count, tie-breaker lexicographically
        def _sort_counts(c: Counter):
            return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))

        morph_rows = _sort_counts(morph_counts)
        tag_rows = _sort_counts(tag_counts)

        # pairs -> 3-column table
        pair_rows = _sort_counts(pair_counts)
        if top_pairs is not None:
            pair_rows = pair_rows[:top_pairs]

        # Build LaTeX tables
        latex_morph = _make_simple_table(morph_rows, "Morpheme", "Freq")
        latex_tags = _make_simple_table(tag_rows, "Tag", "Freq")

        # 3-col pair table
        lines = [
            r"\begin{tabular}{l l r}",
            r"\hline",
            r"Morpheme & Tag & Freq \\",
            r"\hline",
        ]
        for (morph, tag_kind), n in pair_rows:
            lines.append(f"{_latex_escape(morph)} & {_latex_escape(tag_kind)} & {n} \\")
        lines += [r"\hline", r"\end{tabular}"]
        latex_pairs = "\n".join(lines)

        return {
            "morph_counts": morph_counts,
            "tag_counts": tag_counts,
            "pair_counts": pair_counts,
            "latex_morpheme_table": latex_morph,
            "latex_tag_table": latex_tags,
            "latex_pair_table": latex_pairs,
        }

    def _iter_children(self):
        return (
            list(self.arguments)
            + list(self.pre_adjuncts)
            + list(self.post_adjuncts)
            + list(self.v_adjuncts)
            + list(self.v_adjuncts_pre)
        )

    def _collect_nodes(self):
        nodes = []
        children_map = {}
        depth = {}
        dfs_index = {}
        dfs_counter = [0]

        def dfs(node, d):
            nodes.append(node)
            depth[node.nid] = d
            dfs_counter[0] += 1
            dfs_index[node.nid] = dfs_counter[0]
            kids = node._iter_children()
            children_map[node.nid] = [k.nid for k in kids]
            for k in kids:
                dfs(k, d + 1)

        dfs(self, 0)
        return nodes, children_map, depth, dfs_index

    def provenance_with_gen(self, seed: int = 0):
        st = random.getstate()
        random.seed(seed)
        try:
            ctx = EvalCtx()
            root_out = self.eval(annotated=True, ctx=ctx)

            _, children_map, depth, dfs_index = self._collect_nodes()
            pieces_cache = {}

            def pieces(nid):
                if nid not in pieces_cache:
                    pieces_cache[nid] = parse_annotated_morphs(
                        ctx.out_by_nid.get(nid, "")
                    )
                return pieces_cache[nid]

            own_ctr = {}
            # post-order so children exist; tie-break by DFS index for determinism
            order = sorted(
                depth.items(),
                key=lambda kv: (-kv[1], -dfs_index.get(kv[0], 0)),
            )
            for nid, _d in order:
                node_ctr = Counter(pieces(nid))
                child_ctr = Counter()
                for cid in children_map.get(nid, []):
                    child_ctr += Counter(pieces(cid))
                own_ctr[nid] = node_ctr - child_ctr

            root_pieces = parse_annotated_morphs(root_out)
            sorted_nids = [nid for nid, _d in order]
            pieces_with_gen = []
            unknown_pieces = []
            for piece in root_pieces:
                gen = "UNKNOWN"
                for nid in sorted_nids:
                    if own_ctr.get(nid, Counter()).get(piece, 0) > 0:
                        gen = nid
                        own_ctr[nid][piece] -= 1
                        break
                if gen == "UNKNOWN":
                    unknown_pieces.append(piece)
                pieces_with_gen.append((piece, gen))

            leftover_own = {}
            for nid, ctr in own_ctr.items():
                for piece, count in ctr.items():
                    if count > 0:
                        leftover_own.setdefault(nid, []).append((piece, count))

            return {
                "root_output": root_out,
                "pieces_with_gen": pieces_with_gen,
                "unknown_count": len(unknown_pieces),
                "unknown_pieces": unknown_pieces,
                "leftover_own": leftover_own,
            }
        finally:
            random.setstate(st)

    def render_with_gen(self, pieces_with_gen):
        chunks = []
        for piece, gen in pieces_with_gen:
            tags = "".join(f"[{t}]" for t in piece.tags)
            chunks.append(f"{piece.surface}{tags}[GEN:{gen}]")
        return " ".join(chunks)

    def pedagogical_representation(self):
        """
        Return a string representation suitable for pedagogical purposes,
        showing the verbete along with its main glosses and definition.
        Only print out the potiguara and tupi lines if they differ from the navarro line.
        """
        navarro = self.eval(False)
        tn = TupiNoun("na", "na")
        potiguara = tn.map_orthography(navarro, "POTIGUARA")
        tupinamba = tn.map_orthography(navarro, "TUPINAMBA")

        def format_variant_text(text: str) -> str:
            if not text:
                return ""
            parts = []
            for chunk in text.split("\n"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                parts.append(chunk[:1].upper() + chunk[1:])
            return _PEDAGOGICAL_LINE_JOIN.join(parts) if parts else ""

        nl = format_variant_text(escape_latex(navarro))
        pl = format_variant_text(escape_latex(potiguara))
        tl = format_variant_text(escape_latex(tupinamba))
        derf = self.definition.strip() if not self.ped_label else self.ped_label.strip()
        derfn = (
            self.fname.strip()
            if self.fname
            else self.definition.strip()
            if not self.ped_label
            else self.ped_label.strip()
        )
        capdfn = format_variant_text(escape_latex(derf))

        # get self.definition but as a unix-safe filename
        def_fn = re.sub(r"[^a-zA-Z0-9_-áéíóúãõâêôçÁÉÍÓÚÃÕÂÊÔÇ]", "_", derfn)[
            :40
        ].lower()

        latex_lines = []
        all_same = True
        one_different = None
        if pl.lower() != nl.lower():
            latex_lines.append(f"\\tp{{{pl}}}")
            all_same = False
            one_different = "tdo"
        if tl.lower() != nl.lower():
            latex_lines.append(f"\\tdo{{{tl}}}")
            all_same = False
            if one_different:
                one_different = None
            else:
                one_different = "tp"
        # if all of them are the same then use \tall for navarro and prepend the others with it
        if all_same:
            latex_lines = [f"\\tall{{{nl}}}"]
        elif one_different:
            latex_lines = [f"\\ta{one_different}{{{nl}}}"] + latex_lines
        else:
            latex_lines = [f"\\ta{{{nl}}}"] + latex_lines

        latex_template = f"""
        \\variantgroupimg{{{capdfn}}}{{
            {' '.join(latex_lines)}
        }}
        {{imgs/{def_fn}.png}}
        """

        return latex_template

    def emit(self):
        reprs = self.eval(annotated=True).strip()
        # split on [] to get "dfsfw[w:dew]dewd[dwe] dewd [dew][dewd][dew]dwe[ROOT]" into ["dfsfw", "[w:dew]", "dewd", "[dwe]", " dewd ", "[dew:dewd:dew]", "dwe", "[ROOT]"
        parts = [x for x in re.split(r"(\[[^\]]+\])", reprs) if x]
        assert "".join(parts) == reprs, "Split should preserve all text"
        all_tags = dict()
        current_tag = None
        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                content = part[1:-1]
                tags = content.split(":")
                all_tags[current_tag].update(tags)
            else:
                current_tag = part
                all_tags[current_tag] = set()
        # reconstruct into ordered list so we can "".join it back together in the same order but with unique tags
        recon = []
        current_tag = None
        for part in parts:
            if part.startswith("[") and part.endswith("]"):
                continue  # skip tags in reconstruction, we'll add them back in with unique sets
            else:
                recon.append((part, all_tags[part]))
        return recon

    def hierarchical_representation(self):
        """
        Return a string representation showing the hierarchical structure of the predicate flattened out,
        with indentation representing depth in the tree. Uses '*' for arguments and '+' for adjuncts.
        Each node gets a unique incrementing ID, and children reference their parent's ID.
        LEAF nodes are marked, and the last node is marked as TERMINAL.
        Each node is .eval'ed as though it had no adjuncts.
        """
        node_counter = [0]  # mutable counter
        parts = self.emit()
        em = dict(parts)
        seen = {k: set() for k in em.keys()}
        seen_tags = {i: set() for k in parts for i in k[1]}
        node_seen_morpheme = defaultdict(
            set
        )  # node_id -> set of morphemes seen in that node
        node_seen_tags = defaultdict(set)  # node_id -> set of tags seen in that node
        print(parts)

        def recurse(pred, indent=0, rel_type="-", parent_id=None):
            node_counter[0] += 1
            node_id = f"node_{node_counter[0]}"
            indent_str = "  " * indent
            children = pred.arguments + pred.pre_adjuncts + pred.post_adjuncts
            ref = f"parent={parent_id}" if parent_id else "ROOT"
            if not children:
                leaf_marker = " LEAF"
            else:
                leaf_marker = ""
            # Evaluate node as though it had no adjuncts
            stripped = pred.copy()
            stripped.pre_adjuncts = []
            stripped.post_adjuncts = []
            stripped.v_adjuncts = []
            stripped.v_adjuncts_pre = []
            eval_str = stripped.eval(annotated=True)
            lines = [
                f"{indent_str}{rel_type} {pred.verbete} [{node_id}] - {eval_str} [{ref}]{leaf_marker}"
            ]
            for arg in pred.arguments:
                lines.extend(recurse(arg, indent + 1, "*", node_id))
            for adj in pred.pre_adjuncts + pred.post_adjuncts:
                lines.extend(recurse(adj, indent + 1, "+", node_id))
            em_this_node = stripped.emit()
            nid = int(node_id.replace("node_", ""))
            for k, tags in em_this_node:
                # here we want to iterate over the morphemes present which are also in seen, and add to its set there the node id so we know where it appears in the tree
                if k in seen:
                    seen[k].add(nid)
                for tag in tags:
                    if tag in seen_tags:
                        seen_tags[tag].add(nid)
                node_seen_morpheme[node_id].add(k)
                node_seen_tags[node_id].update(tags)
            return lines

        lines = recurse(self, parent_id=None)
        if lines:
            lines[-1] += " TERMINAL"
        # for each of these morphemes, we can get the largest number node in the set and add it to the set of tags for that morpheme in em, so we know the deepest node in the tree where it appears
        for k, node_ids in seen.items():
            if node_ids:
                max_id = max(node_ids)
                em[k].add(f"DEEPEST_NODE_{max_id}")
        # replace sets in parts with those in em, and join them back together into a string
        final_parts = []
        for part, tags in parts:
            unique_tags = em.get(part, set())
            final_parts.append(part + "".join(f"[{t}]" for t in unique_tags))
        final_str = "".join(final_parts)
        print("\n".join(lines))
        print("\n\n")
        print("SEEN:", seen)
        print("SEEN_TAGS:", seen_tags)
        print("NODE_SEEN_MORPHEME:", node_seen_morpheme)
        print("NODE_SEEN_TAGS:", node_seen_tags)
        return final_str

    def hierarchical_representation_v4(self):
        node_counter = [0]
        lines = []
        nodes: list[_Node] = []

        global_parts = _as_pairs(self.emit())
        G_raw = [s for s, _ in global_parts]
        G = [_norm_surface(s) for s in G_raw]
        N = len(G)

        # per-occurrence tags (start with global emission tags)
        tags_by_idx = [set(tags) for _, tags in global_parts]
        matched_nodes_by_idx = [
            set() for _ in range(N)
        ]  # global idx -> set of node nids

        def build_tree(pred, indent=0, rel_type="-", parent_id=None, kind="arg"):
            node_counter[0] += 1
            nid = node_counter[0]
            node_id = f"node_{nid}"

            stripped = pred.copy()
            stripped.pre_adjuncts = []
            stripped.post_adjuncts = []
            stripped.v_adjuncts = []
            stripped.v_adjuncts_pre = []

            eval_str = stripped.eval(annotated=True)
            local_parts = _as_pairs(stripped.emit())
            local_norm = [_norm_surface(s) for s, _ in local_parts]

            node = _Node(
                node_id=node_id,
                nid=nid,
                parent_id=parent_id,
                depth=indent,
                rel_type=rel_type,
                kind=kind,
                verbete=getattr(pred, "verbete", "?"),
                pred_obj=pred,
                local_parts=local_parts,
                local_norm=local_norm,
            )
            nodes.append(node)

            indent_str = "  " * indent
            ref = f"parent={parent_id}" if parent_id else "ROOT"
            children_preds = pred.arguments + pred.pre_adjuncts + pred.post_adjuncts
            leaf_marker = " LEAF" if not children_preds else ""
            lines.append(
                f"{indent_str}{rel_type} {node.verbete} [{node_id}] - {eval_str} [{ref}]{leaf_marker}"
            )

            # children — keep KIND so we can search them in sensible subranges
            for arg in pred.arguments:
                child = build_tree(arg, indent + 1, "*", node_id, kind="arg")
                node.children.append(child)
            for adj in pred.pre_adjuncts:
                child = build_tree(adj, indent + 1, "+", node_id, kind="pre")
                node.children.append(child)
            for adj in pred.post_adjuncts:
                child = build_tree(adj, indent + 1, "+", node_id, kind="post")
                node.children.append(child)

            return node

        root = build_tree(self, 0, "-", None, kind="arg")
        if lines:
            lines[-1] += " TERMINAL"

        def exact_candidates(child: _Node, lo: int, hi: int):
            """All exact substring matches of child.local_norm in G[lo:hi]."""
            A = child.local_norm
            L = len(A)
            if L == 0:
                return []
            out = []
            max_start = hi - L
            for s in range(lo, max_start + 1):
                if G[s : s + L] == A:
                    mapping = [(i, s + i) for i in range(L)]
                    matched = frozenset(s + i for i in range(L))
                    out.append(
                        _Cand(
                            score=L, span=(s, s + L), mapping=mapping, matched=matched
                        )
                    )
            return out

        def lcs_best_candidate(child: _Node, lo: int, hi: int):
            """One best LCS candidate inside G[lo:hi] (can be 0-match)."""
            B = G[lo:hi]
            pairs = _lcs_mapping(child.local_norm, B)
            if not pairs:
                # ε-candidate: no matches, zero-width span at lo
                return _Cand(score=0, span=(lo, lo), mapping=[], matched=frozenset())
            mapping = [(li, lo + bj) for (li, bj) in pairs]
            matched = frozenset(gj for _, gj in mapping)
            s = min(matched)
            e = max(matched) + 1
            return _Cand(
                score=len(mapping), span=(s, e), mapping=mapping, matched=matched
            )

        def candidates(child: _Node, lo: int, hi: int):
            """
            Candidate generation:
            - all exact matches (best when available)
            - else: if single-token, exact positions of that token
            - else: one LCS-based best candidate (may be ε)
            """
            lo = max(0, lo)
            hi = min(N, hi)
            if lo > hi:
                lo = hi

            ex = exact_candidates(child, lo, hi)
            if ex:
                return ex

            A = child.local_norm
            if len(A) == 1:
                tok = A[0]
                out = []
                for i in range(lo, hi):
                    if G[i] == tok:
                        out.append(
                            _Cand(
                                score=1,
                                span=(i, i + 1),
                                mapping=[(0, i)],
                                matched=frozenset([i]),
                            )
                        )
                if out:
                    return out

            return [lcs_best_candidate(child, lo, hi)]

        def pick_nonoverlapping(
            children: list[_Node], cand_map: dict[str, list[_Cand]]
        ):
            """
            Backtracking selection: choose 1 candidate per child maximizing total score,
            disallowing overlap on matched GLOBAL indices (ε candidates have empty matched set).
            """
            # sort children by best possible score (prune)
            order = sorted(
                children,
                key=lambda ch: max(c.score for c in cand_map[ch.node_id]),
                reverse=True,
            )

            best = None  # (total_score, assignment_dict)
            used = set()
            assignment = {}

            def bt(k, total):
                nonlocal best
                if k == len(order):
                    if best is None or total > best[0]:
                        best = (total, dict(assignment))
                    return

                ch = order[k]
                for c in sorted(
                    cand_map[ch.node_id],
                    key=lambda x: (x.score, -(x.span[1] - x.span[0])),
                    reverse=True,
                ):
                    if c.matched and (used & c.matched):
                        continue
                    assignment[ch.node_id] = c
                    if c.matched:
                        used.update(c.matched)
                    bt(k + 1, total + c.score)
                    if c.matched:
                        used.difference_update(c.matched)
                    del assignment[ch.node_id]

            bt(0, 0)
            return best[1] if best else {}

        def solve(node: _Node, lo: int, hi: int):
            """
            Solve within CONTAINER [lo,hi]:
            - align node core (doesn't constrain children)
            - place children in subranges relative to core anchor
            - recurse with child container spans (or group range if ε)
            """
            # core alignment (can be ε if nothing matches)
            core = lcs_best_candidate(node, lo, hi)
            node.core_mapping = core.mapping
            node.core_span = core.span

            # apply core mapping tags
            for li, gi in node.core_mapping:
                _surf, tset = node.local_parts[li]
                tags_by_idx[gi].update(tset)
                matched_nodes_by_idx[gi].add(node.nid)

            anchor_s, anchor_e = node.core_span
            # If ε core, anchor is at lo
            if anchor_s == anchor_e:
                anchor_s = anchor_e = lo

            # group children by kind and choose placements independently
            groups = {
                "pre": (lo, anchor_s),
                "post": (anchor_e, hi),
                "arg": (lo, hi),
            }

            # Slight preference for args that can match INSIDE core window (helps your oré argument)
            core_lo, core_hi = node.core_span

            # Build candidates per group, pick non-overlapping per group, recurse
            for kind in ("pre", "arg", "post"):
                kids = [ch for ch in node.children if ch.kind == kind]
                if not kids:
                    continue

                glo, ghi = groups[kind]
                cand_map = {}
                for ch in kids:
                    cand_list = candidates(ch, glo, ghi)

                    # heuristic: if arg has a candidate inside core span, bump it to front by +1 score
                    if kind == "arg" and core_lo < core_hi:
                        bumped = []
                        for c in cand_list:
                            if c.matched and all(
                                core_lo <= i < core_hi for i in c.matched
                            ):
                                bumped.append(
                                    _Cand(
                                        score=c.score + 1,
                                        span=c.span,
                                        mapping=c.mapping,
                                        matched=c.matched,
                                    )
                                )
                            else:
                                bumped.append(c)
                        cand_list = bumped

                    cand_map[ch.node_id] = cand_list

                chosen = pick_nonoverlapping(kids, cand_map)

                for ch in kids:
                    c = chosen.get(ch.node_id)
                    if c is None:
                        # If this happens, we couldn't place without overlap; fall back to best solo candidate.
                        c = max(cand_map[ch.node_id], key=lambda x: x.score)

                    # apply mapping tags
                    for li, gi in c.mapping:
                        _surf, tset = ch.local_parts[li]
                        tags_by_idx[gi].update(tset)
                        matched_nodes_by_idx[gi].add(ch.nid)

                    # recurse: if ε, keep container as group range; else use matched window span
                    child_lo, child_hi = (glo, ghi) if c.score == 0 else c.span
                    solve(ch, child_lo, child_hi)

        # Solve entire tree within full sentence
        solve(root, 0, N)

        # deepest per TOKEN OCCURRENCE = max depth among nodes that matched that index
        nodes_by_nid = {n.nid: n for n in nodes}
        deepest = []
        for i in range(N):
            if not matched_nodes_by_idx[i]:
                deepest.append(root.nid)
                continue
            best_nid = None
            best_depth = -1
            for nid in matched_nodes_by_idx[i]:
                d = nodes_by_nid[nid].depth
                if d > best_depth:
                    best_depth = d
                    best_nid = nid
            deepest.append(best_nid)

        out_parts = []
        for i, (surf, _orig) in enumerate(global_parts):
            t = set(tags_by_idx[i])
            t.add(f"DEEPEST_NODE_{deepest[i]}")
            out_parts.append(surf + "[" + ":".join(f"{x}" for x in sorted(t)) + "]")

        final_str = "".join(out_parts)

        # print("\n".join(lines))
        return final_str


def _format_semfit_label(gloss_main, modifiers=None, width_break=3):
    r"""
    Return a single LaTeX label wrapped in \semfit{...}, with optional '\\'
    inserted every `width_break` items to encourage vertical wrapping.
    All strings are assumed already escaped for forest via escape_latex_forest_node.
    """
    modifiers = modifiers or []

    def block(items):
        if not items:
            return ""
        parts = []
        for i, s in enumerate(items, 1):
            parts.append(s)
            if i < len(items):
                parts.append(", ")
            if width_break and (i % width_break == 0) and (i < len(items)):
                parts.append(r"\\ ")
        return "".join(parts)

    body = block(gloss_main)
    if modifiers:
        body += r"\\ \textcolor{black!60}{\footnotesize modifiers:} " + block(modifiers)
    return rf"\semfit{{{body}}}"


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
    text = _PEDAGOGICAL_NEWLINE_RE.sub("\n", text)
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


def _make_simple_table(
    rows: List[Tuple[str, int]], left_header: str, right_header: str
) -> str:
    lines = [
        r"\begin{tabular}{l r}",
        r"\hline",
        f"{_latex_escape(left_header)} & {_latex_escape(right_header)} \\\\",
        r"\hline",
    ]
    for name, n in rows:
        lines.append(f"{_latex_escape(name)} & {n} \\\\")
    lines += [r"\hline", r"\end{tabular}"]
    return "\n".join(lines)


def _latex_escape(s: str) -> str:
    return escape_latex(s)


def escape_latex_forest_node(text: str) -> str:
    # For Forest/TikZ NODE CONTENT ONLY
    # (1) Do NOT escape backslashes (we need \\ for line breaks)
    # Replace ",n " (comma n space) with a newline for better formatting
    text = _PEDAGOGICAL_NEWLINE_RE.sub("\n", text)
    s = (
        text.replace("{", "\\{")
        .replace("}", "\\}")
        .replace("_", "\\_")
        .replace("#", "\\#")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("^", "\\^{}")
        .replace("~", "\\~{}")
    )
    # (2) Support both real newlines and literal "\n"
    s = s.replace("\\n", r"\\").replace("\n", r"\\")
    # (3) Keep the breaks confined to the node with a shortstack
    return r"\shortstack{" + s + r"}"


def _chunk_list(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def _shortstack(lines):
    return r"\shortstack{" + r"\\ ".join(lines) + "}" if lines else r"\phantom{~}"


def _escape_join(chunk):
    return ", ".join(chunk)  # assume inputs already forest-safe


def _escape_lines_for_stack(texts, max_per_line=5):
    return [_escape_join(chunk) for chunk in _chunk_list(texts, max_per_line)]


def _format_sem_label(gloss_main, modifiers=None, width_break=3):
    """Wrap lists into multiple lines; smaller width_break => more vertical growth."""
    modifiers = modifiers or []
    lines = []
    lines.extend(_escape_lines_for_stack(gloss_main, width_break))
    if modifiers:
        lines.append(r"\textcolor{black!60}{\footnotesize modifiers:}")
        lines.extend(_escape_lines_for_stack(modifiers, max(2, width_break - 1)))
    return _shortstack(lines)
