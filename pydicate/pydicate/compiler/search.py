from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import re
import unicodedata

from .constraints import DEFAULT_CONSTRAINTS, resolve_constraints
from .ir import Atom, IRKind, IRNode, MorphOp, Op
from .lexicon import LexiconRegistry, build_lexicon
from .pretty import canonicalize_ir, render_ir, render_pydicate
from .registry import PredicateRegistry, build_registry
from .scoring import DefaultScorer, Scorer
from .tokens import Token, ensure_tokens, parse_annotated

try:
    from tupi import TupiAntigo
except Exception:  # pragma: no cover - optional dependency at runtime
    TupiAntigo = None


@dataclass
class DecompileResult:
    ir: IRNode
    cost: float
    code: str
    beam: List[Tuple[IRNode, float]]
    debug: Dict[str, Any]


_VERBISH_POS = {"Verb"}
_NOUNISH_POS = {"Noun", "ProperNoun", "Pronoun", "Deverbal", "Deadverbal"}

_MORPH_ALLOWED_POS = {
    "VOC": _NOUNISH_POS,
    "IMP": _VERBISH_POS,
    "PERM": _VERBISH_POS,
    "CIRC": _VERBISH_POS,
    "REDUP": _VERBISH_POS,
    "BASE_NOMINAL": _VERBISH_POS,
}

_INFLECTION_CODES = {
    "1ps",
    "1ppi",
    "1ppe",
    "2ps",
    "2pp",
    "3p",
    "refl",
    "mut",
    "suj",
}

_STATIVE_PREFIXES: Tuple[str, ...] = ()
_ACTIVE_PREFIXES: Tuple[str, ...] = ()
if TupiAntigo is not None:
    stative: List[str] = []
    active: List[str] = []
    for vals in getattr(TupiAntigo, "personal_inflections", {}).values():
        if len(vals) > 1 and vals[1]:
            stative.append(str(vals[1]))
        if len(vals) > 2 and vals[2]:
            active.append(str(vals[2]))
    _STATIVE_PREFIXES = tuple(dict.fromkeys(stative))
    _ACTIVE_PREFIXES = tuple(dict.fromkeys(active))

_PREFIX_TAG_KINDS = {
    "PLURIFORM_PREFIX",
    "PATIENT_PREFIX",
    "SUBJECT_PREFIX",
    "OBJECT_PREFIX",
    "OBJECT_MARKER",
    "GERUND_SUBJECT_PREFIX",
    "IMPERATIVE_PREFIX",
    "PERMISSIVE_PREFIX",
    "CAUSATIVE_PREFIX",
}


def _wrap_morph_ops(node: IRNode, morph_ops: Sequence[str]) -> IRNode:
    wrapped = node
    for op in morph_ops:
        allowed = _MORPH_ALLOWED_POS.get(op)
        if allowed is not None:
            if node.kind != IRKind.ATOM or node.name not in allowed:
                continue
        wrapped = MorphOp(op, wrapped)
    return wrapped


def _node_token(node: IRNode) -> Optional[Token]:
    if node.kind == IRKind.ATOM:
        return node.attrs.get("token")
    if node.kind == IRKind.MORPH and node.children:
        return _node_token(node.children[0])
    if node.kind == IRKind.OP and node.name == "SEQ" and node.children:
        return _node_token(node.children[0])
    return None


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


_POSTPOSED_SUBJECT_PRONOUNS = {
    _normalize_key("îepé"),
    _normalize_key("peîepé"),
}


def _strip_tags(value: str) -> str:
    return re.sub(r"\[[^\]]+\]", "", value)


def _inflection_from_token(token: Token) -> Optional[str]:
    for tag in token.tags:
        parts = tag.split(":")
        for part in parts:
            if part in _INFLECTION_CODES:
                return part
    return None


def _subject_prefix_verb_class(token: Optional[Token]) -> Optional[str]:
    if token is None:
        return None
    if "SUBJECT_PREFIX" not in token.tag_kinds:
        return None
    key = _normalize_key(token.m)
    stative = {_normalize_key(p) for p in _STATIVE_PREFIXES if p}
    active = {_normalize_key(p) for p in _ACTIVE_PREFIXES if p}
    if key in stative and key not in active:
        return "adj."
    return None


def _dative_variation_id(noun_token: Token, postposition_token: Token) -> Optional[int]:
    if TupiAntigo is None:
        return None
    inflection = _inflection_from_token(noun_token)
    if not inflection:
        return None
    forms = getattr(TupiAntigo, "dative_inflections", {}).get(inflection)
    if not forms:
        return None
    noun = _normalize_key(noun_token.m)
    suffix = _normalize_key(postposition_token.m)
    combined = _normalize_key(f"{noun_token.m}{postposition_token.m}")

    for idx, form in enumerate(forms):
        clean = _normalize_key(_strip_tags(form))
        if clean == combined:
            return idx
    for idx, form in enumerate(forms):
        clean = _normalize_key(_strip_tags(form))
        if clean.endswith(suffix) and noun in clean:
            return idx
    for idx, form in enumerate(forms):
        clean = _normalize_key(_strip_tags(form))
        if clean.endswith(suffix):
            return idx
    return None


def _apply_postposition_variation(postposition: IRNode, target: IRNode) -> IRNode:
    token = _node_token(postposition)
    target_token = _node_token(target)
    if not token or not target_token:
        return postposition
    if not token.has_tag("POSTPOSITION", "DATIVE"):
        return postposition
    variation_id = _dative_variation_id(target_token, token)
    if variation_id is None:
        return postposition
    return MorphOp("VAR", postposition, value=variation_id)


def _node_tag_kinds(node: IRNode) -> Tuple[str, ...]:
    token = _node_token(node)
    kinds: List[str] = []
    if token:
        kinds.extend(list(token.tag_kinds))
    extra = node.attrs.get("extra_tag_kinds")
    if extra:
        kinds.extend(list(extra))
    return tuple(dict.fromkeys(kinds))


def _node_pos(node: IRNode) -> Optional[str]:
    if node.kind == IRKind.ATOM:
        return node.name
    if node.kind == IRKind.MORPH and node.children:
        return _node_pos(node.children[0])
    return None


def _is_prefix(node: IRNode) -> bool:
    return any(kind in _PREFIX_TAG_KINDS for kind in _node_tag_kinds(node))


def _has_tag_kind(node: IRNode, kind: str) -> bool:
    return kind in _node_tag_kinds(node)


def _pluriform_mode(node: IRNode) -> Optional[str]:
    token = _node_token(node)
    if not token:
        return None
    for tag in token.tags:
        if not tag.startswith("PLURIFORM_PREFIX"):
            continue
        parts = tag.split(":")
        for part in parts[1:]:
            if part in {"R", "T", "ABSOLUTE"}:
                return part
    return None


def _mark_pluriform(node: IRNode) -> IRNode:
    if node.kind == IRKind.ATOM:
        attrs = dict(node.attrs)
        attrs["pluriform"] = True
        return IRNode(node.kind, node.name, node.children, attrs)
    if node.kind == IRKind.MORPH and node.children:
        child = _mark_pluriform(node.children[0])
        return IRNode(node.kind, node.name, (child,), dict(node.attrs))
    return node


def _is_nounish(node: IRNode) -> bool:
    pos = _node_pos(node)
    if pos in _NOUNISH_POS:
        return True
    if node.kind == IRKind.OP and node.name == "AT":
        return True
    if node.kind == IRKind.OP and node.name == "MUL" and node.children:
        left = node.children[0]
        if _node_pos(left) == "Postposition":
            return True
        return _is_nounish(left)
    if node.kind == IRKind.OP and node.name == "ADD" and node.children:
        return all(_is_nounish(child) for child in node.children)
    return any(
        kind in {"NOUN", "NNOUN", "PROPER_NOUN", "PRONOUN", "DEVERBAL", "DEADVERBAL"}
        for kind in _node_tag_kinds(node)
    )


def _is_possessor_noun(node: IRNode) -> bool:
    token = _node_token(node)
    if not token:
        return False
    return token.has_tag("NOUN", "POSSESSOR")


def _is_possessed_nounish(node: IRNode) -> bool:
    if node.kind != IRKind.OP or node.name != "MUL" or len(node.children) != 2:
        return False
    left, right = node.children
    return (_is_possessor_noun(left) or _is_possessive_pronoun(left)) and _is_nounish(
        right
    )


def _contains_tag_kind(node: IRNode, kind: str) -> bool:
    return any(kind in _node_tag_kinds(n) for n in node.walk())


def _has_object_non_main_clause_subject(node: IRNode) -> bool:
    for n in node.walk():
        if n.kind != IRKind.ATOM:
            continue
        token = n.attrs.get("token")
        if token and token.has_tag("OBJECT", "NON_MAIN_CLAUSE_SUBJECT"):
            return True
    return False


def _has_object_3p(node: IRNode) -> bool:
    for n in node.walk():
        if n.kind != IRKind.ATOM:
            continue
        token = n.attrs.get("token")
        if token and token.has_tag("OBJECT", "3p"):
            return True
    return False


def _is_nominalized(node: IRNode) -> bool:
    kinds = _node_tag_kinds(node)
    return any(
        k in kinds
        for k in (
            "SUBSTANTIVE_SUFFIX",
            "NOUN",
            "NNOUN",
            "DEVERBAL",
            "DEADVERBAL",
        )
    )


def _is_verbish(node: IRNode) -> bool:
    pos = _node_pos(node)
    if pos in _VERBISH_POS:
        return True
    return "VERB" in _node_tag_kinds(node)


def _is_postposition(node: IRNode) -> bool:
    pos = _node_pos(node)
    if pos == "Postposition":
        return True
    return "POSTPOSITION" in _node_tag_kinds(node)


def _is_postposition_head(node: IRNode) -> bool:
    if _node_pos(node) == "Postposition":
        return True
    if node.kind == IRKind.OP and node.name == "MUL" and node.children:
        left = node.children[0]
        return _is_postposition(left)
    return False


def _is_object_marker_arg(node: IRNode) -> bool:
    if node.kind == IRKind.MORPH and node.name == "PRO_DROP":
        tok = _node_token(node)
        if tok and "OBJECT_MARKER" in tok.tag_kinds:
            return True
    return False


def _strip_object_marker_args(node: IRNode) -> IRNode:
    if node.kind == IRKind.OP and node.name == "MUL" and node.children:
        left, right = node.children
        if _is_object_marker_arg(right):
            return _strip_object_marker_args(left)
        return Op(
            "MUL", _strip_object_marker_args(left), _strip_object_marker_args(right)
        )
    if node.kind == IRKind.MORPH and node.children:
        child = _strip_object_marker_args(node.children[0])
        return IRNode(node.kind, node.name, (child,), dict(node.attrs))
    return node


def _is_particle(node: IRNode) -> bool:
    pos = _node_pos(node)
    if pos == "Particle":
        return True
    return "PARTICLE" in _node_tag_kinds(node)


def _is_clitic_particle(node: IRNode) -> bool:
    token = _node_token(node)
    if token and token.has_tag("PARTICLE", "ADVERSATIVE"):
        return True
    return False


def _is_clitic_adverb(node: IRNode) -> bool:
    token = _node_token(node)
    if not token:
        return False
    return bool(getattr(token, "glue_prev", False))


def _is_postposed_subject_pronoun(node: IRNode) -> bool:
    token = _node_token(node)
    if not token:
        return False
    if "SUBJECT" not in token.tag_kinds:
        return False
    return _normalize_key(token.m) in _POSTPOSED_SUBJECT_PRONOUNS


def _is_adverbish(node: IRNode) -> bool:
    pos = _node_pos(node)
    if pos in {"Adverb", "Postposition"}:
        return True
    kinds = _node_tag_kinds(node)
    return "ADVERB" in kinds or "POSTPOSITION" in kinds


def _has_morph(node: IRNode, names: Iterable[str]) -> bool:
    name_set = set(names)
    for n in node.walk():
        if n.kind == IRKind.MORPH and n.name in name_set:
            return True
    return False


def _is_possessive_pronoun(node: IRNode) -> bool:
    return "POSSESSIVE_PRONOUN" in _node_tag_kinds(node)


def _with_extra_tags(node: IRNode, extra: Iterable[str]) -> IRNode:
    extra = tuple(extra)
    if not extra:
        return node
    attrs = dict(node.attrs)
    prev = tuple(attrs.get("extra_tag_kinds", ()))
    merged = tuple(dict.fromkeys(prev + extra))
    attrs["extra_tag_kinds"] = merged
    return IRNode(node.kind, node.name, node.children, attrs)


def _with_suffix_morph(node: IRNode, morph: str) -> IRNode:
    if not morph:
        return node
    attrs = dict(node.attrs)
    prev = tuple(attrs.get("suffix_morphs", ()))
    merged = tuple(dict.fromkeys(prev + (morph,)))
    attrs["suffix_morphs"] = merged
    return IRNode(node.kind, node.name, node.children, attrs)


def _with_noun_extra_tag(node: IRNode, tag: str) -> IRNode:
    if not tag:
        return node
    attrs = dict(node.attrs)
    if attrs.get("noun_extra_tag"):
        return node
    attrs["noun_extra_tag"] = tag
    return IRNode(node.kind, node.name, node.children, attrs)


def _deverbal_with_vocative(deverbal: IRNode, suffix_node: IRNode) -> IRNode:
    if "VOCATIVE" in _node_tag_kinds(suffix_node):
        return MorphOp("VOC", deverbal)
    return deverbal


def _with_verb_class(node: IRNode, verb_class: Optional[str]) -> IRNode:
    if not verb_class:
        return node
    if node.kind == IRKind.ATOM and node.name == "Verb":
        attrs = dict(node.attrs)
        if attrs.get("verb_class"):
            return node
        attrs["verb_class"] = verb_class
        return IRNode(node.kind, node.name, node.children, attrs)
    if node.children:
        updated = []
        changed = False
        for child in node.children:
            new_child = _with_verb_class(child, verb_class)
            if new_child is not child:
                changed = True
            updated.append(new_child)
        if changed:
            return IRNode(node.kind, node.name, tuple(updated), dict(node.attrs))
    return node


def _as_pos(node: IRNode, pos: str) -> IRNode:
    if node.kind != IRKind.ATOM:
        return node
    return IRNode(node.kind, pos, node.children, dict(node.attrs))


def _is_subject_marker(node: IRNode) -> bool:
    if _node_pos(node) in {"Deverbal", "Deadverbal", "Noun", "ProperNoun"}:
        return False
    token = _node_token(node)
    if token and token.has_tag("SUBJECT_PREFIX", "IMPERATIVE"):
        return False
    kinds = _node_tag_kinds(node)
    if "SUBJECT_PREFIX" in kinds or "GERUND_SUBJECT_PREFIX" in kinds:
        return True
    if "SUBJECT" in kinds:
        return _is_postposed_subject_pronoun(node)
    return False


def _is_object_marker(node: IRNode) -> bool:
    kinds = _node_tag_kinds(node)
    if _node_pos(node) in {"Deverbal", "Deadverbal", "Noun", "ProperNoun"}:
        return False
    token = _node_token(node)
    if token and token.has_tag("OBJECT_MARKER", "IMPERATIVE"):
        return False
    return any(
        k in kinds
        for k in ("OBJECT", "OBJECT_PREFIX", "OBJECT_MARKER", "PATIENT_PREFIX")
    )


def _is_implicit_marker(node: IRNode) -> bool:
    if _node_pos(node) != "Pronoun":
        return False
    token = _node_token(node)
    if not token:
        return False
    kinds = _node_tag_kinds(node)
    if "OBJECT_MARKER" in kinds:
        return False
    # Subject prefixes do not surface as standalone pronouns, even when the
    # prefix is multi-character (e.g., "ere").
    if "SUBJECT_PREFIX" in kinds or "GERUND_SUBJECT_PREFIX" in kinds:
        return True
    if len(token.m) > 1:
        return False
    return any(k in kinds for k in ("OBJECT_PREFIX", "PATIENT_PREFIX"))


def _is_subject_prefix_marker(node: IRNode) -> bool:
    token = _node_token(node)
    if not token:
        return False
    kinds = _node_tag_kinds(node)
    return "SUBJECT_PREFIX" in kinds or "GERUND_SUBJECT_PREFIX" in kinds


def _is_explicit_marker(node: IRNode) -> bool:
    if _is_implicit_marker(node):
        return False
    return _is_subject_marker(node) or _is_object_marker(node)


def _contains_verbish(node: IRNode) -> bool:
    for n in node.walk():
        if n.kind == IRKind.ATOM and n.name in _VERBISH_POS:
            return True
    return False


def _verbish_arg_count(node: IRNode) -> int:
    count = 0
    cur = node
    while cur.kind == IRKind.OP and cur.name == "MUL" and len(cur.children) == 2:
        left, right = cur.children
        if _contains_verbish(left):
            count += 1
            cur = left
            continue
        if _contains_verbish(right):
            count += 1
            cur = right
            continue
        break
    return count


def _strip_verb_args(node: IRNode) -> IRNode:
    if _is_verbish(node):
        return node
    if node.kind == IRKind.MORPH and node.children:
        child = node.children[0]
        if _contains_verbish(child):
            return MorphOp(node.name, _strip_verb_args(child), **dict(node.attrs))
        return node
    if node.kind == IRKind.OP and node.name == "MUL" and node.children:
        left, right = node.children
        left_has = _contains_verbish(left)
        right_has = _contains_verbish(right)
        if left_has and not right_has:
            return _strip_verb_args(left)
        if right_has and not left_has:
            return _strip_verb_args(right)
        if right_has:
            return _strip_verb_args(right)
        if left_has:
            return _strip_verb_args(left)
        return node
    if node.kind == IRKind.OP and node.children:
        for child in node.children:
            if _contains_verbish(child):
                return _strip_verb_args(child)
    return node


def _apply_negation_suffix(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        if _has_tag_kind(node, "NEGATION_SUFFIX"):
            if out:
                out[-1] = MorphOp("NEG", out[-1])
            continue
        out.append(node)
    return out


def _rewrite_verb_lexeme(node: IRNode, fn) -> IRNode:
    if node.kind == IRKind.ATOM and node.name == "Verb":
        lexeme = node.attrs.get("lexeme")
        new_lexeme = fn(lexeme)
        if new_lexeme == lexeme:
            return node
        attrs = dict(node.attrs)
        attrs["lexeme"] = new_lexeme
        return IRNode(node.kind, node.name, node.children, attrs)
    if not node.children:
        return node
    new_children = tuple(_rewrite_verb_lexeme(child, fn) for child in node.children)
    if new_children == node.children:
        return node
    return IRNode(node.kind, node.name, new_children, dict(node.attrs))


def _force_abs_agent_allomorph(node: IRNode, token: Optional[Token]) -> IRNode:
    if not token or not token.m or not token.m.startswith("ar"):
        return node

    def _accent_o(lexeme: Optional[str]) -> Optional[str]:
        if not lexeme:
            return lexeme
        if lexeme.endswith("o"):
            return f"{lexeme[:-1]}ó"
        return lexeme

    return _rewrite_verb_lexeme(node, _accent_o)


def _force_conjunctive_allomorph(node: IRNode) -> IRNode:
    def _rewrite(n: IRNode) -> IRNode:
        if n.kind == IRKind.ATOM and n.name == "Verb":
            lexeme = n.attrs.get("lexeme")
            if n.attrs.get("pluriform") and lexeme in {"ú", "u", "û", "îu"}:
                attrs = dict(n.attrs)
                attrs["lexeme"] = "îub"
                return IRNode(n.kind, n.name, n.children, attrs)
        if not n.children:
            return n
        new_children = tuple(_rewrite(child) for child in n.children)
        if new_children == n.children:
            return n
        return IRNode(n.kind, n.name, new_children, dict(n.attrs))

    return _rewrite(node)


def _apply_circumstantial_suffix(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        if _has_tag_kind(node, "CIRCUMSTANTIAL_SUFFIX"):
            continue
        out.append(node)
    return out


def _apply_conjunctive_suffix(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _has_tag_kind(node, "CONJUNCTIVE_SUFFIX"):

            def _is_subject_pronoun(n: IRNode) -> bool:
                if _node_pos(n) != "Pronoun":
                    return False
                token = _node_token(n)
                return bool(token and "SUBJECT" in token.tag_kinds)

            # Try to attach the nearest verb to the left as a post-adjunct
            # of the nearest verb to the left of that.
            j = len(out) - 1
            while j >= 0 and not _contains_verbish(out[j]):
                j -= 1
            if j >= 0:
                sub = out[j]
                subj = None
                if j - 1 >= 0 and _is_subject_pronoun(out[j - 1]):
                    subj = out[j - 1]
                    del out[j - 1]
                    j -= 1
                if subj is not None:
                    sub = Op("MUL", sub, subj)
                sub = _force_conjunctive_allomorph(sub)
                k = j - 1
                while k >= 0 and not _contains_verbish(out[k]):
                    k -= 1
                if k >= 0 and j == k + 1:
                    principal = out[k]
                    out = out[:k]
                    out.append(Op("SHIFT_L", principal, sub))
                    i += 1
                    continue
                # Fallback: attach to nearest verb on the right as pre-adjunct.
                r = i + 1
                while r < len(nodes) and not _contains_verbish(nodes[r]):
                    r += 1
                if r < len(nodes):
                    principal = nodes[r]
                    out.append(Op("SHIFT_R", sub, principal))
                    i = r + 1
                    continue
            i += 1
            continue
        out.append(node)
        i += 1
    return out


def _apply_ume_negation(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        token = _node_token(node)
        is_ume = bool(token and token.has_tag("NEGATION_PARTICLE", "UME"))
        if is_ume and out and _contains_verbish(out[-1]):
            if not _has_morph(out[-1], ("IMP", "PERM")):
                out[-1] = MorphOp("IMP", out[-1])
            out[-1] = MorphOp("NEG", out[-1])
            continue
        out.append(node)
    return out


def _attach_particle_adjuncts(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _is_particle(node) and _is_clitic_particle(node):
            if out and _contains_verbish(out[-1]):
                out[-1] = Op("SHIFT_L", out[-1], node)
                i += 1
                continue
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _contains_verbish(nodes[j]):
                out.append(Op("SHIFT_L", nodes[j], node))
                i = j + 1
                continue
        if _is_adverbish(node) and _is_clitic_adverb(node):
            if out and _contains_verbish(out[-1]):
                prev = out[-1]
                if prev.kind == IRKind.OP and prev.name == "SHIFT_L" and prev.children:
                    left = prev.children[0]
                    right = prev.children[1] if len(prev.children) > 1 else None
                    if right is not None and _contains_verbish(right):
                        out[-1] = Op("SHIFT_L", left, Op("SHIFT_L", right, node))
                    else:
                        out[-1] = Op("SHIFT_L", prev, node)
                else:
                    out[-1] = Op("SHIFT_L", prev, node)
                i += 1
                continue
        out.append(node)
        i += 1
    return out


def _apply_pluriform_relations(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _has_tag_kind(node, "PLURIFORM_PREFIX"):
            mode = _pluriform_mode(node)
            if mode in {"T", "ABSOLUTE"}:
                if i + 1 < len(nodes):
                    nodes[i + 1] = _mark_pluriform(nodes[i + 1])
                i += 1
                continue
            if out and i + 1 < len(nodes):
                nxt = _mark_pluriform(nodes[i + 1])
                prev_token = _node_token(out[-1])
                if (
                    prev_token
                    and "SUBJECT" in prev_token.tag_kinds
                    and "SUBJECT_PREFIX" not in prev_token.tag_kinds
                    and "GERUND_SUBJECT_PREFIX" not in prev_token.tag_kinds
                    and _contains_verbish(nxt)
                ):
                    out.append(nxt)
                    i += 2
                    continue
                if (
                    nxt.kind == IRKind.ATOM
                    and nxt.name == "Deverbal"
                    and nxt.attrs.get("lexeme") == "emi"
                    and i + 2 < len(nodes)
                ):
                    verb_target = nodes[i + 2]
                    if not _contains_verbish(verb_target) and "ROOT" in _node_tag_kinds(
                        verb_target
                    ):
                        verb_target = _as_pos(verb_target, "Verb")
                    if (
                        not _contains_verbish(verb_target)
                        and _node_pos(verb_target) != "Verb"
                    ):
                        # can't attach yet, fall through
                        pass
                    else:
                        attached = Op("MUL", verb_target, out[-1])
                        merged = Op("MUL", nxt, attached)
                        outer = merged
                        carry = [
                            k
                            for k in _node_tag_kinds(verb_target)
                            if k
                            in {
                                "NOUN",
                                "NNOUN",
                                "DEVERBAL",
                                "DEADVERBAL",
                                "SUBSTANTIVE_SUFFIX",
                                "SUBJECT",
                                "OBJECT",
                                "VOCATIVE",
                            }
                        ]
                        if carry:
                            outer = _with_extra_tags(outer, carry)
                        out[-1] = outer
                        i += 3
                        continue
                if _is_postposition(nxt):
                    nodes[i + 1] = nxt
                    i += 1
                    continue
                merged = Op("MUL", out[-1], nxt)
                carry = [
                    k
                    for k in _node_tag_kinds(nxt)
                    if k
                    in {
                        "NOUN",
                        "NNOUN",
                        "DEVERBAL",
                        "DEADVERBAL",
                        "SUBSTANTIVE_SUFFIX",
                        "SUBJECT",
                        "OBJECT",
                        "VOCATIVE",
                    }
                ]
                if carry:
                    merged = _with_extra_tags(merged, carry)
                out[-1] = merged
                i += 2
                continue
            i += 1
            continue
        out.append(node)
        i += 1
    return out


def _apply_pluriform_marks(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _has_tag_kind(node, "PLURIFORM_PREFIX"):
            mode = _pluriform_mode(node)
            if mode in {"T", "ABSOLUTE"}:
                if i + 1 < len(nodes):
                    nodes[i + 1] = _mark_pluriform(nodes[i + 1])
                i += 1
                continue
        out.append(node)
        i += 1
    return out


def _apply_deverbal_suffixes(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        kinds = _node_tag_kinds(node)
        token = _node_token(node)
        suffix_only = "ROOT" not in kinds
        if "FACILITY_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                    out[-1] = Op("MUL", head, out[-1])
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "saba"), node))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                out.append(Op("MUL", head, node))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                out[-1] = Op("MUL", head, out[-1])
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "saba"), node))
            continue
        if "ABSOLUTE_AGENT_SUFFIX" in kinds or "ACTIVE_AGENT_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                    out[-1] = Op(
                        "MUL", head, _force_abs_agent_allomorph(out[-1], token)
                    )
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "sara"), node))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                out.append(Op("MUL", head, _force_abs_agent_allomorph(node, token)))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                out[-1] = Op("MUL", head, _force_abs_agent_allomorph(out[-1], token))
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "sara"), node))
            continue
        if "AGENTLESS_PATIENT_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    # Drop the implicit 3p object immediately to the left; pyra supplies it.
                    if (
                        out[-1].kind == IRKind.ATOM
                        and out[-1].name == "Pronoun"
                        and (
                            _has_object_non_main_clause_subject(out[-1])
                            or _has_object_3p(out[-1])
                        )
                    ):
                        out.pop()
                    if not out:
                        out.append(
                            _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                        )
                        continue
                    head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                    target = out[-1]
                    out[-1] = Op("MUL", head, _strip_verb_args(target))
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "pyra"), node))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                target = node
                out.append(Op("MUL", head, _strip_verb_args(target)))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                target = out[-1]
                out[-1] = Op("MUL", head, _strip_verb_args(target))
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "pyra"), node))
            continue
        if "RELATIVE_AGENT_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "ba'e"), node)
                    out[-1] = Op("MUL", head, out[-1])
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "ba'e"), node))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "ba'e"), node)
                out.append(Op("MUL", head, node))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "ba'e"), node)
                out[-1] = Op("MUL", head, out[-1])
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "ba'e"), node))
            continue
        out.append(node)
    return out


def _apply_deverbal_suffixes_next(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        kinds = _node_tag_kinds(node)
        token = _node_token(node)
        suffix_only = "ROOT" not in kinds
        if "FACILITY_SUFFIX" in kinds:
            if suffix_only and i + 1 < len(nodes):
                target = nodes[i + 1]
                if _contains_verbish(target) or "ROOT" in _node_tag_kinds(target):
                    head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                    out.append(Op("MUL", head, target))
                    i += 2
                    continue
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                    out[-1] = Op("MUL", head, out[-1])
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "saba"), node))
                i += 1
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                out.append(Op("MUL", head, node))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "saba"), node)
                out[-1] = Op("MUL", head, out[-1])
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "saba"), node))
            i += 1
            continue
        if "ABSOLUTE_AGENT_SUFFIX" in kinds or "ACTIVE_AGENT_SUFFIX" in kinds:
            if suffix_only and i + 1 < len(nodes):
                target = nodes[i + 1]
                if _contains_verbish(target) or "ROOT" in _node_tag_kinds(target):
                    head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                    out.append(
                        Op("MUL", head, _force_abs_agent_allomorph(target, token))
                    )
                    i += 2
                    continue
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                    out[-1] = Op(
                        "MUL", head, _force_abs_agent_allomorph(out[-1], token)
                    )
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "sara"), node))
                i += 1
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                out.append(Op("MUL", head, _force_abs_agent_allomorph(node, token)))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                out[-1] = Op("MUL", head, _force_abs_agent_allomorph(out[-1], token))
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "sara"), node))
            i += 1
            continue
        if "AGENTLESS_PATIENT_SUFFIX" in kinds:
            if suffix_only and i + 1 < len(nodes):
                target = nodes[i + 1]
                if _contains_verbish(target) or "ROOT" in _node_tag_kinds(target):
                    head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                    out.append(Op("MUL", head, _strip_verb_args(target)))
                    i += 2
                    continue
            if suffix_only:
                if out:
                    head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                    out[-1] = Op("MUL", head, _strip_verb_args(out[-1]))
                else:
                    out.append(_deverbal_with_vocative(Atom("Deverbal", "pyra"), node))
                i += 1
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                out.append(Op("MUL", head, _strip_verb_args(node)))
            elif out:
                head = _deverbal_with_vocative(Atom("Deverbal", "pyra"), node)
                out[-1] = Op("MUL", head, _strip_verb_args(out[-1]))
            else:
                out.append(_deverbal_with_vocative(Atom("Deverbal", "pyra"), node))
                i += 1
                continue
        if "RELATIVE_AGENT_SUFFIX" in kinds:
            if suffix_only and i + 1 < len(nodes):
                target = nodes[i + 1]
                if _contains_verbish(target) or "ROOT" in _node_tag_kinds(target):
                    head = _deverbal_with_vocative(Atom("Deverbal", "ba'e"), node)
                    out.append(Op("MUL", head, target))
                    i += 2
                    continue
            if out:
                head = _deverbal_with_vocative(Atom("Deverbal", "ba'e"), node)
                out[-1] = Op("MUL", head, out[-1])
                i += 1
                continue
            out.append(_deverbal_with_vocative(Atom("Deverbal", "ba'e"), node))
            i += 1
            continue
        out.append(node)
        i += 1
    return out


def _force_deverbal_suffixes(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        kinds = _node_tag_kinds(node)
        suffix_only = "ROOT" not in kinds
        if suffix_only and (
            "ABSOLUTE_AGENT_SUFFIX" in kinds or "ACTIVE_AGENT_SUFFIX" in kinds
        ):
            if out:
                for idx in range(len(out) - 1, -1, -1):
                    if _contains_verbish(out[idx]):
                        head = _deverbal_with_vocative(Atom("Deverbal", "sara"), node)
                        out[idx] = Op(
                            "MUL",
                            head,
                            _force_abs_agent_allomorph(out[idx], _node_token(node)),
                        )
                        break
                else:
                    out.append(node)
                continue
        out.append(node)
    return out


def _apply_deverbal_suffixes_variants(nodes: List[IRNode]) -> List[List[IRNode]]:
    base = _apply_deverbal_suffixes(nodes)
    alt = _apply_deverbal_suffixes_next(list(nodes))
    if alt != base:
        return [base, alt]
    return [base]


def _drop_substantive_suffix_tokens(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        kinds = _node_tag_kinds(node)
        if "SUBSTANTIVE_SUFFIX" in kinds:
            morph = None
            token = _node_token(node)
            if token:
                morph = token.m
            if morph and len(morph) <= 2 and "ROOT" not in kinds:
                if out:
                    out[-1] = _with_suffix_morph(out[-1], morph)
                    if token:
                        for tag in token.tags:
                            if tag.startswith("NOUN:LOAN_WORD"):
                                out[-1] = _with_noun_extra_tag(out[-1], tag)
                                break
                    carry_tags = [
                        k
                        for k in kinds
                        if k
                        in {
                            "NOUN",
                            "NNOUN",
                            "DEVERBAL",
                            "DEADVERBAL",
                            "SUBSTANTIVE_SUFFIX",
                            "SUBJECT",
                            "OBJECT",
                            "POSSESSIVE_PRONOUN",
                        }
                    ]
                    if carry_tags:
                        out[-1] = _with_extra_tags(out[-1], carry_tags)
                    attrs = out[-1].attrs if out[-1].kind == IRKind.ATOM else {}
                    prefer_verb_nominal = bool(attrs.get("noun_from_verb"))
                    if "DEVERBAL" in kinds:
                        out[-1] = _as_pos(out[-1], "Deverbal")
                    elif "DEADVERBAL" in kinds:
                        out[-1] = _as_pos(out[-1], "Deadverbal")
                    elif "NOUN" in kinds or "NNOUN" in kinds:
                        if (
                            _node_pos(out[-1]) not in _NOUNISH_POS
                            and not prefer_verb_nominal
                        ):
                            out[-1] = _as_pos(out[-1], "Noun")
                    else:
                        # Substantive suffix nominalizes by default.
                        if (
                            _node_pos(out[-1]) not in _NOUNISH_POS
                            and not prefer_verb_nominal
                        ):
                            out[-1] = _as_pos(out[-1], "Noun")
                continue
        out.append(node)
    return out


def _apply_prefix_morph(nodes: List[IRNode]) -> List[IRNode]:
    if not nodes:
        return nodes
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        kinds = _node_tag_kinds(node)
        if "PERMISSIVE_PREFIX" in kinds:
            # Skip the prefix token itself and apply .perm() to the next verbish node,
            # even if pronoun markers intervene.
            j = i + 1
            while j < len(nodes) and not _is_verbish(nodes[j]):
                j += 1
            if j < len(nodes):
                nodes[j] = MorphOp("PERM", nodes[j])
            i += 1
            continue
        token = _node_token(node)
        imperative_subject = bool(
            token and token.has_tag("SUBJECT_PREFIX", "IMPERATIVE")
        )
        if "IMPERATIVE_PREFIX" in kinds or imperative_subject:
            # Skip the prefix token itself and apply .imp() to the next verbish node,
            # even if pronoun markers intervene.
            j = i + 1
            while j < len(nodes) and not _is_verbish(nodes[j]):
                j += 1
            if j < len(nodes):
                base_node = nodes[j]
                base_node = _with_verb_class(
                    base_node, _subject_prefix_verb_class(token)
                )
                infl = None
                if token:
                    for tag in token.tags:
                        parts = tag.split(":")
                        for part in parts:
                            if part in _INFLECTION_CODES:
                                infl = part
                                break
                        if infl:
                            break
                if infl:
                    lexeme = "endé" if infl == "2ps" else infl
                    pro = MorphOp("PRO_DROP", Atom("Pronoun", lexeme))
                    base_node = Op("MUL", base_node, pro)
                nodes[j] = MorphOp("IMP", base_node)
            i += 1
            continue
        out.append(node)
        i += 1
    return out


def _apply_causative_prefix(nodes: List[IRNode]) -> List[IRNode]:
    if not nodes:
        return nodes
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _has_tag_kind(node, "CAUSATIVE_PREFIX"):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _contains_verbish(nodes[j]):
                out.append(Op("MUL", node, nodes[j]))
                i = j + 1
                continue
        out.append(node)
        i += 1
    return out


def _merge_possessives_and_postpositions(
    nodes: List[IRNode], *, postposition_direction: str = "left"
) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _is_possessive_pronoun(node):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _is_nounish(nodes[j]):
                if j == i + 1:
                    target = nodes[j]
                else:
                    target = Op("SEQ", *nodes[i + 1 : j + 1])
                out.append(Op("MUL", node, target))
                i = j + 1
                continue
        if _is_postposition(node):
            token = _node_token(node)
            force_left = bool(token and "SIMULATIVE_SUFFIX" in token.tag_kinds)
            if postposition_direction == "right":
                if force_left:
                    # Simulative postpositions should bind to the left (e.g., pyra * verb)
                    pass
                else:
                    k = i + 1
                    while k < len(nodes) and _is_prefix(nodes[k]):
                        k += 1
                    if k < len(nodes) and _is_nounish(nodes[k]):
                        if _contains_verbish(nodes[k]) and not _is_nominalized(
                            nodes[k]
                        ):
                            # Prefer left attachment when the right candidate is verbish.
                            pass
                        else:
                            node = _apply_postposition_variation(node, nodes[k])
                            nodes[k] = Op("MUL", node, nodes[k])
                            i += 1
                            continue
            if out:
                for idx in range(len(out) - 1, -1, -1):
                    if _is_nounish(out[idx]):
                        node = _apply_postposition_variation(node, out[idx])
                        out[idx] = Op("MUL", node, out[idx])
                        i += 1
                        break
                else:
                    out.append(node)
                    i += 1
                continue
        out.append(node)
        i += 1
    return out


def _merge_possessives_and_postpositions_variants(
    nodes: List[IRNode],
) -> List[List[IRNode]]:
    base = _merge_possessives_and_postpositions(nodes, postposition_direction="left")
    alt = _merge_possessives_and_postpositions(
        list(nodes), postposition_direction="right"
    )
    if alt != base:
        return [base, alt]
    return [base]


def _merge_possessives(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        token = _node_token(node)
        if _is_possessor_noun(node):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _is_nounish(nodes[j]):
                if j == i + 1:
                    target = nodes[j]
                else:
                    target = Op("SEQ", *nodes[i + 1 : j + 1])
                merged = Op("MUL", node, target)
                carry = [
                    k
                    for k in _node_tag_kinds(target)
                    if k
                    in {
                        "NOUN",
                        "NNOUN",
                        "DEVERBAL",
                        "DEADVERBAL",
                        "SUBSTANTIVE_SUFFIX",
                        "SUBJECT",
                        "OBJECT",
                        "VOCATIVE",
                    }
                ]
                if carry:
                    merged = _with_extra_tags(merged, carry)
                out.append(merged)
                i = j + 1
                continue
        if (
            _node_pos(node) == "Pronoun"
            and token
            and "SUBJECT" in token.tag_kinds
            and "SUBJECT_PREFIX" not in token.tag_kinds
            and "GERUND_SUBJECT_PREFIX" not in token.tag_kinds
            and not _is_postposed_subject_pronoun(node)
        ):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if (
                j < len(nodes)
                and _is_nounish(nodes[j])
                and not _contains_verbish(nodes[j])
            ):
                if j == i + 1:
                    target = nodes[j]
                else:
                    target = Op("SEQ", *nodes[i + 1 : j + 1])
                out.append(Op("MUL", node, target))
                i = j + 1
                continue
        if _is_possessive_pronoun(node):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _is_nounish(nodes[j]):
                if j == i + 1:
                    target = nodes[j]
                else:
                    target = Op("SEQ", *nodes[i + 1 : j + 1])
                if (
                    target.kind == IRKind.OP
                    and target.name == "MUL"
                    and len(target.children) == 2
                    and _is_nounish(target.children[0])
                    and _contains_verbish(target.children[1])
                ):
                    possessed = Op("MUL", node, target.children[0])
                    merged = Op("MUL", possessed, target.children[1])
                else:
                    merged = Op("MUL", node, target)
                carry = [
                    k
                    for k in _node_tag_kinds(target)
                    if k
                    in {
                        "NOUN",
                        "NNOUN",
                        "DEVERBAL",
                        "DEADVERBAL",
                        "SUBSTANTIVE_SUFFIX",
                        "SUBJECT",
                        "OBJECT",
                        "VOCATIVE",
                    }
                ]
                if carry:
                    merged = _with_extra_tags(merged, carry)
                out.append(merged)
                i = j + 1
                continue
        out.append(node)
        i += 1
    return out


def _attach_markers(
    nodes: List[IRNode], marker_fn, *, preverb_right: bool = False
) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if marker_fn(node):
            verb_class = None
            if marker_fn is _is_subject_marker:
                verb_class = _subject_prefix_verb_class(_node_token(node))
                if _is_postposed_subject_pronoun(node):
                    attached = False
                    for idx in range(len(out) - 1, -1, -1):
                        if _contains_verbish(out[idx]):
                            out[idx] = _with_verb_class(out[idx], verb_class)
                            out[idx] = Op("MUL", out[idx], node)
                            i += 1
                            attached = True
                            break
                    if attached:
                        continue
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _is_postposition(nodes[j]):
                out.append(node)
                i += 1
                continue
            if _is_implicit_marker(node):
                # Agreement prefixes don't surface as pronouns; attach as pro-drop.
                if _is_subject_prefix_marker(node):
                    token = _node_token(node)
                    if token and token.has_tag("SUBJECT_PREFIX", "3p"):
                        k = j
                        saw_object = False
                        while k < len(nodes) and not _contains_verbish(nodes[k]):
                            if _is_object_marker(nodes[k]):
                                saw_object = True
                            k += 1
                        if (
                            saw_object
                            and k < len(nodes)
                            and _has_morph(nodes[k], ("PERM",))
                        ):
                            i += 1
                            continue
                        if k < len(nodes) and _has_morph(nodes[k], ("PERM",)) and out:
                            found_subject = False
                            for idx in range(len(out) - 1, -1, -1):
                                if _is_nounish(out[idx]):
                                    if _contains_tag_kind(out[idx], "SUBJECT"):
                                        found_subject = True
                                    break
                            if found_subject:
                                i += 1
                                continue
                    if j < len(nodes) and _contains_verbish(nodes[j]):
                        if _verbish_arg_count(nodes[j]) >= 2:
                            i += 1
                            continue
                    node = MorphOp("PRO_DROP", node)
                else:
                    token = _node_token(node)
                    if token and token.has_tag("OBJECT", "NON_MAIN_CLAUSE_SUBJECT"):
                        node = MorphOp("PRO_DROP", node)
                    else:
                        i += 1
                        continue
            if j < len(nodes) and _contains_verbish(nodes[j]):
                target = _with_verb_class(nodes[j], verb_class)
                if preverb_right:
                    out.append(Op("MUL", target, node))
                else:
                    out.append(Op("MUL", node, target))
                i = j + 1
                continue
            if out and _contains_verbish(out[-1]):
                out[-1] = _with_verb_class(out[-1], verb_class)
                out[-1] = Op("MUL", out[-1], node)
                i += 1
                continue
        out.append(node)
        i += 1
    return out


def _attach_argument_markers(nodes: List[IRNode]) -> List[IRNode]:
    # Attach subjects first so objects can wrap verb+subject when needed.
    nodes = _attach_markers(nodes, _is_subject_marker, preverb_right=False)
    nodes = _attach_markers(nodes, _is_object_marker, preverb_right=True)
    return nodes


def _attach_argument_markers_variants(nodes: List[IRNode]) -> List[List[IRNode]]:
    base = _attach_argument_markers(nodes)
    alt = _attach_markers(
        _attach_markers(list(nodes), _is_subject_marker, preverb_right=True),
        _is_object_marker,
        preverb_right=False,
    )
    if alt != base:
        return [base, alt]
    return [base]


def _attach_nounish_markers(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if (
            node.kind == IRKind.OP
            and node.name == "MUL"
            and len(node.children) == 2
            and i + 1 < len(nodes)
        ):
            left, right = node.children

            def _is_markerish(n: IRNode) -> bool:
                if _node_pos(n) != "Pronoun":
                    return False
                kinds = _node_tag_kinds(n)
                return any(
                    k in kinds
                    for k in (
                        "SUBJECT",
                        "OBJECT",
                        "OBJECT_PREFIX",
                        "OBJECT_MARKER",
                        "PATIENT_PREFIX",
                    )
                )

            if _is_markerish(left) and _is_markerish(right):
                subj = left if "SUBJECT" in _node_tag_kinds(left) else None
                obj = right if _is_object_marker(right) else None
                if subj is None and "SUBJECT" in _node_tag_kinds(right):
                    subj = right
                if obj is None and _is_object_marker(left):
                    obj = left
                if (
                    subj is not None
                    and obj is not None
                    and _is_nounish(nodes[i + 1])
                    and (
                        not _contains_verbish(nodes[i + 1])
                        or _is_nominalized(nodes[i + 1])
                    )
                ):
                    head = nodes[i + 1]
                    head = Op("MUL", head, obj)
                    out.append(subj)
                    out.append(head)
                    i += 2
                    continue
        if _is_explicit_marker(node):
            markers: List[IRNode] = []
            j = i
            while j < len(nodes) and _is_explicit_marker(nodes[j]):
                markers.append(nodes[j])
                j += 1
            k = j
            while k < len(nodes) and _is_prefix(nodes[k]):
                k += 1
            if (
                k < len(nodes)
                and _is_nounish(nodes[k])
                and (not _contains_verbish(nodes[k]) or _is_nominalized(nodes[k]))
            ):
                head = nodes[k]
                has_object_marker = any(_is_object_marker(marker) for marker in markers)
                deferred: List[IRNode] = []
                if (
                    head.kind == IRKind.ATOM
                    and head.name == "Noun"
                    and "ROOT" in _node_tag_kinds(head)
                    and _is_nominalized(head)
                    and markers
                ):
                    if not any(
                        _is_subject_marker(marker) or _is_possessive_pronoun(marker)
                        for marker in markers
                    ):
                        head = _as_pos(head, "Verb")
                for marker in markers:
                    if (
                        has_object_marker
                        and _is_nominalized(head)
                        and _is_subject_marker(marker)
                        and not _is_possessive_pronoun(marker)
                    ):
                        deferred.append(marker)
                        continue
                    if _is_subject_marker(marker) or _is_possessive_pronoun(marker):
                        marker_node = marker
                        head = Op("MUL", marker_node, head)
                    else:
                        head = Op("MUL", head, marker)
                out.extend(deferred)
                out.append(head)
                i = k + 1
                continue
        out.append(node)
        i += 1
    return out


def _attach_deadverbal_args(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if (
            i + 2 < len(nodes)
            and _is_nounish(node)
            and _is_postposition(nodes[i + 1])
            and _node_pos(nodes[i + 2]) in {"Deverbal", "Deadverbal"}
        ):
            post = nodes[i + 1]
            deadv = nodes[i + 2]
            post = _apply_postposition_variation(post, node)
            out.append(Op("MUL", deadv, Op("MUL", post, node)))
            i += 3
            continue
        if i + 1 < len(nodes) and _node_pos(nodes[i + 1]) in {"Deverbal", "Deadverbal"}:
            if _is_nounish(node) or _is_adverbish(node):
                out.append(Op("MUL", nodes[i + 1], node))
                i += 2
                continue
        out.append(node)
        i += 1
    return out


def _contains_emi(node: IRNode) -> bool:
    for n in node.walk():
        if (
            n.kind == IRKind.ATOM
            and n.name == "Deverbal"
            and n.attrs.get("lexeme") == "emi"
        ):
            return True
    return False


def _contains_deverbalish(node: IRNode) -> bool:
    for n in node.walk():
        if n.kind == IRKind.ATOM and n.name in {"Deverbal", "Deadverbal"}:
            return True
    return False


def _apply_copula_pairs(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        if (
            i + 1 < len(nodes)
            and _is_nounish(nodes[i])
            and _is_possessed_nounish(nodes[i + 1])
            and not _is_postposition_head(nodes[i])
            and not _contains_verbish(nodes[i])
        ):
            out.append(Op("AT", nodes[i], nodes[i + 1]))
            i += 2
            continue
        if (
            i + 1 < len(nodes)
            and _is_nounish(nodes[i])
            and _is_nounish(nodes[i + 1])
            and _contains_emi(nodes[i])
            and _contains_deverbalish(nodes[i + 1])
        ):
            out.append(Op("AT", nodes[i], nodes[i + 1]))
            i += 2
            continue
        out.append(nodes[i])
        i += 1
    return out


def _is_imperative_verb(node: IRNode) -> bool:
    if node.kind == IRKind.MORPH and node.name in {"IMP", "PERM"}:
        return True
    for n in node.walk():
        if n.kind == IRKind.MORPH and n.name in {"IMP", "PERM"}:
            return True
    return False


def _attach_preverbal_objects(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if (
            out
            and _is_imperative_verb(out[-1])
            and _is_nounish(node)
            and _contains_emi(node)
            and not _is_postposition_head(node)
        ):
            prev = out[-1]
            if (
                prev.kind == IRKind.OP
                and prev.name == "MUL"
                and len(prev.children) == 2
                and _is_object_marker(prev.children[1])
            ):
                verb_part, obj_marker = prev.children
                out[-1] = Op("MUL", Op("MUL", verb_part, node), obj_marker)
            else:
                out[-1] = Op("MUL", prev, node)
            i += 1
            continue
        allow_possessed = False
        if _is_imperative_verb(node) and _has_morph(node, ("PERM",)):
            allow_possessed = True
        if (
            _is_imperative_verb(node)
            and out
            and _is_nounish(out[-1])
            and not _is_postposition_head(out[-1])
            and (allow_possessed or not _is_possessed_nounish(out[-1]))
            and not (out[-1].kind == IRKind.OP and out[-1].name == "AT")
        ):
            obj = out.pop()
            node = _strip_object_marker_args(node)
            out.append(Op("MUL", obj, node))
            i += 1
            continue
        out.append(node)
        i += 1
    return out


def _attach_emi_deverbal(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if (
            node.kind == IRKind.ATOM
            and node.name == "Deverbal"
            and node.attrs.get("lexeme") == "emi"
        ):
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes):
                target = nodes[j]
                if not _contains_verbish(target) and "ROOT" in _node_tag_kinds(target):
                    target = _as_pos(target, "Verb")
                if _contains_verbish(target) or _node_pos(target) == "Verb":
                    out.append(Op("MUL", node, target))
                    i = j + 1
                    continue
        out.append(node)
        i += 1
    return out


def _attach_pronoun_deverbal_copula(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if _node_pos(node) == "Pronoun" and i + 1 < len(nodes):
            nxt = nodes[i + 1]
            if _contains_deverbalish(nxt) and _contains_tag_kind(
                nxt, "RELATIVE_AGENT_SUFFIX"
            ):
                out.append(Op("AT", node, nxt))
                i += 2
                continue
        out.append(node)
        i += 1
    return out


def _apply_conjunctions(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        if _has_tag_kind(node, "CONJUNCTION") and _is_nounish(node):
            conj_nodes: List[IRNode] = []
            while out and _is_nounish(out[-1]):
                conj_nodes.insert(0, out.pop())
            conj_nodes.append(node)
            acc = conj_nodes[0]
            for nxt in conj_nodes[1:]:
                acc = Op("ADD", acc, nxt)
            out.append(acc)
            continue
        out.append(node)
    return out


def _rewrite_sequence(node: IRNode) -> IRNode:
    if node.kind != IRKind.OP or node.name != "SEQ":
        return node
    nodes = list(node.children)
    nodes = _apply_prefix_morph(nodes)
    nodes = _apply_causative_prefix(nodes)
    nodes = _apply_ume_negation(nodes)
    nodes = _apply_negation_suffix(nodes)
    nodes = _apply_circumstantial_suffix(nodes)
    nodes = _drop_substantive_suffix_tokens(nodes)
    nodes = _apply_pluriform_marks(nodes)
    nodes = _apply_conjunctions(nodes)
    nodes = _apply_pluriform_relations(nodes)
    nodes = _attach_emi_deverbal(nodes)
    nodes = _merge_possessives(nodes)
    nodes = _attach_argument_markers(nodes)
    nodes = _attach_nounish_markers(nodes)
    nodes = _apply_conjunctive_suffix(nodes)
    nodes = _attach_particle_adjuncts(nodes)
    nodes = _apply_deverbal_suffixes_next(nodes)
    nodes = _force_deverbal_suffixes(nodes)
    nodes = _attach_deadverbal_args(nodes)
    nodes = _attach_pronoun_deverbal_copula(nodes)
    nodes = _merge_possessives_and_postpositions(nodes)
    nodes = _apply_copula_pairs(nodes)
    nodes = _attach_preverbal_objects(nodes)
    if len(nodes) == 1:
        return nodes[0]
    return Op("SEQ", *nodes)


def _expand_variants(
    sequences: List[List[IRNode]],
    fn,
    *,
    max_variants: int,
) -> List[List[IRNode]]:
    out: List[List[IRNode]] = []
    for seq in sequences:
        for variant in fn(list(seq)):
            out.append(variant)
            if len(out) >= max_variants:
                return out
    return out


def _rewrite_sequence_variants(node: IRNode, *, max_variants: int = 4) -> List[IRNode]:
    if node.kind != IRKind.OP or node.name != "SEQ":
        return [node]
    nodes = list(node.children)
    nodes = _apply_prefix_morph(nodes)
    nodes = _apply_causative_prefix(nodes)
    nodes = _apply_ume_negation(nodes)
    nodes = _apply_negation_suffix(nodes)
    nodes = _apply_circumstantial_suffix(nodes)
    nodes = _drop_substantive_suffix_tokens(nodes)
    nodes = _apply_pluriform_marks(nodes)
    nodes = _apply_conjunctions(nodes)
    nodes = _apply_pluriform_relations(nodes)
    nodes = _attach_emi_deverbal(nodes)
    nodes = _merge_possessives(nodes)

    sequences: List[List[IRNode]] = [nodes]
    sequences = _expand_variants(
        sequences, _attach_argument_markers_variants, max_variants=max_variants
    )
    sequences = [_attach_nounish_markers(seq) for seq in sequences]
    sequences = [_apply_conjunctive_suffix(seq) for seq in sequences]
    sequences = [_attach_particle_adjuncts(seq) for seq in sequences]
    sequences = _expand_variants(
        sequences, _apply_deverbal_suffixes_variants, max_variants=max_variants
    )
    sequences = [_attach_deadverbal_args(seq) for seq in sequences]
    sequences = [_attach_pronoun_deverbal_copula(seq) for seq in sequences]
    sequences = _expand_variants(
        sequences,
        _merge_possessives_and_postpositions_variants,
        max_variants=max_variants,
    )
    sequences = [_apply_copula_pairs(seq) for seq in sequences]
    sequences = [_attach_preverbal_objects(seq) for seq in sequences]

    out_nodes: List[IRNode] = []
    for seq in sequences:
        if len(seq) == 1:
            out_nodes.append(seq[0])
        else:
            out_nodes.append(Op("SEQ", *seq))
    return out_nodes


def _combine_seq(lhs: Optional[IRNode], rhs: IRNode) -> IRNode:
    if lhs is None:
        return rhs
    if lhs.kind == IRKind.OP and lhs.name == "SEQ":
        return IRNode(IRKind.OP, "SEQ", lhs.children + (rhs,), dict(lhs.attrs))
    return Op("SEQ", lhs, rhs)


def _candidate_atoms(
    token: Token,
    constraints: Dict[str, Any],
    lexicon: Optional[LexiconRegistry] = None,
) -> List[IRNode]:
    if token.m in {"emi", "embi"} and "PATIENT_PREFIX" in token.tag_kinds:
        allowed_pos = ("Deverbal",)
        morph_ops: Tuple[str, ...] = ()
        candidates = []
        for pos in allowed_pos:
            atom = Atom(pos, "emi", token=token)
            wrapped = _wrap_morph_ops(atom, morph_ops)
            candidates.append(wrapped)
        return candidates
    allowed_pos, morph_ops = resolve_constraints(
        token.tag_kinds, constraints, token=token
    )
    nounish_kinds = set(token.tag_kinds)
    prefer_verb_nominal = False
    if lexicon and "NOUN" in nounish_kinds and "ROOT" in nounish_kinds:
        pos_hits = lexicon.pos_candidates(token.m)
        if "Verb" in pos_hits:
            prefer_verb_nominal = True
            if "Verb" not in allowed_pos:
                allowed_pos = tuple(dict.fromkeys(list(allowed_pos) + ["Verb"]))
    if not allowed_pos:
        if lexicon:
            pos_hits = lexicon.pos_candidates(token.m)
            if pos_hits:
                allowed_pos = pos_hits
        if "ROOT" in token.tag_kinds:
            if (
                "SUBSTANTIVE_SUFFIX" in token.tag_kinds
                or "NOUN" in token.tag_kinds
                or "VOCATIVE" in token.tag_kinds
            ):
                allowed_pos = ("Noun",)
            elif "DEVERBAL" in token.tag_kinds:
                allowed_pos = ("Deverbal",)
            elif "DEADVERBAL" in token.tag_kinds:
                allowed_pos = ("Deadverbal",)
            else:
                allowed_pos = ("Verb",)
        else:
            allowed_pos = ("Predicate",)
    candidates = []
    for pos in allowed_pos:
        lexeme = token.m
        if pos == "Postposition" and token.has_tag("POSTPOSITION", "DATIVE"):
            lexeme = "supé"
        attrs = {"token": token}
        if pos == "Verb" and prefer_verb_nominal:
            attrs["noun_from_verb"] = True
            attrs["verb_class"] = "adj."
        atom = Atom(pos, lexeme, **attrs)
        wrapped = _wrap_morph_ops(atom, morph_ops)
        if "OBJECT_MARKER" in token.tag_kinds:
            wrapped = MorphOp("PRO_DROP", wrapped)
        candidates.append(wrapped)
    return candidates


def _tokens_from_rerank_output(value: Any) -> Optional[List[Token]]:
    if value is None:
        return None
    if isinstance(value, str):
        return parse_annotated(value)
    if isinstance(value, Token):
        return [value]
    if isinstance(value, (list, tuple)):
        return ensure_tokens(value)
    return None


def _contains_deverbal_lexeme(node: IRNode, lexeme: str) -> bool:
    for n in node.walk():
        if n.kind == IRKind.ATOM and n.name == "Deverbal":
            if n.attrs.get("lexeme") == lexeme:
                return True
    return False


def _token_distance(
    observed: List[Token],
    generated: List[Token],
    *,
    morph_weight: float = 1.0,
    tag_weight: float = 0.25,
) -> float:
    dist = abs(len(observed) - len(generated)) * morph_weight
    limit = min(len(observed), len(generated))
    for idx in range(limit):
        exp = observed[idx]
        act = generated[idx]
        if exp.m != act.m:
            dist += morph_weight
        diff = set(exp.tags) ^ set(act.tags)
        if diff:
            dist += tag_weight * len(diff)
    return dist


def _rewrite_candidates(node: IRNode, *, max_variants: int) -> List[IRNode]:
    if max_variants <= 1:
        return [canonicalize_ir(_rewrite_sequence(node))]
    variants = _rewrite_sequence_variants(node, max_variants=max_variants)
    return [canonicalize_ir(v) for v in variants]


def _select_best_by_cost(
    candidates: Iterable[IRNode], scorer: Scorer
) -> Tuple[IRNode, float]:
    best_ir = None
    best_cost = None
    for ir in candidates:
        cost = scorer.cost(ir)
        if best_cost is None or cost < best_cost:
            best_ir = ir
            best_cost = cost
    if best_ir is None or best_cost is None:
        raise ValueError("No candidates available for selection")
    return best_ir, best_cost


def _rerank_candidates(
    candidates: Iterable[Tuple[IRNode, float, int, int]],
    observed: List[Token],
    *,
    scorer: Scorer,
    rerank_fn,
    allow_seq: bool,
    seq_op: str,
    lexicon: Optional[LexiconRegistry],
    weight: float,
) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for ir, beam_cost, beam_idx, variant_idx in candidates:
        try:
            code = render_pydicate(
                ir, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon
            )
        except Exception:
            continue
        try:
            rerank_out = rerank_fn(code)
        except Exception:
            continue
        tokens = _tokens_from_rerank_output(rerank_out)
        if not tokens:
            continue
        dist = _token_distance(observed, tokens)
        complexity = scorer.cost(ir)
        score = dist + weight * complexity
        ranked.append(
            {
                "ir": ir,
                "code": code,
                "score": score,
                "distance": dist,
                "complexity": complexity,
                "beam_cost": beam_cost,
                "beam_index": beam_idx,
                "variant_index": variant_idx,
            }
        )
    ranked.sort(key=lambda item: item["score"])
    return ranked


def decompile(
    tokens: Iterable[Any],
    *,
    registry: Optional[PredicateRegistry] = None,
    constraints: Optional[Dict[str, Any]] = None,
    scorer: Optional[Scorer] = None,
    beam_size: int = 32,
    emit: str = "ir",
    lexicon: Optional[LexiconRegistry] = None,
    lexicon_modules: Optional[Sequence[str]] = None,
    use_lexicon: bool = True,
    finalize_top_k: int = 8,
    rewrite_max_variants: int = 4,
    rerank_top_k: int = 0,
    rerank_weight: float = 1.0,
    rerank_fn: Optional[Callable[[str], Any]] = None,
    allow_seq: bool = True,
    seq_op: str = "+",
) -> DecompileResult:
    registry = registry or build_registry()
    constraints = constraints or DEFAULT_CONSTRAINTS
    scorer = scorer or DefaultScorer()
    if use_lexicon:
        lexicon = lexicon or build_lexicon(lexicon_modules)
    else:
        lexicon = None

    stream = ensure_tokens(tokens)
    beam: List[Tuple[Optional[IRNode], float]] = [(None, 0.0)]

    for token in stream:
        candidates = _candidate_atoms(token, constraints, lexicon)
        new_beam: List[Tuple[IRNode, float]] = []
        for prefix, prefix_cost in beam:
            for cand in candidates:
                combined = _combine_seq(prefix, cand)
                cost = prefix_cost + scorer.cost(cand)
                new_beam.append((combined, cost))
        new_beam.sort(key=lambda x: x[1])
        beam = new_beam[: max(1, beam_size)]

    if not beam:
        raise ValueError("No candidates generated from tokens")

    best_ir = None
    best_cost = None
    rerank_info: Optional[Dict[str, Any]] = None

    if rerank_top_k > 0:
        if rerank_fn is None:
            raise ValueError("rerank_fn is required when rerank_top_k > 0")
        top_k = min(len(beam), rerank_top_k)
        candidates: List[Tuple[IRNode, float, int, int]] = []
        for idx, (ir, cost) in enumerate(beam[:top_k]):
            for v_idx, variant in enumerate(
                _rewrite_candidates(ir, max_variants=max(1, rewrite_max_variants))
            ):
                candidates.append((variant, cost, idx, v_idx))
        reranked = _rerank_candidates(
            candidates,
            stream,
            scorer=scorer,
            rerank_fn=rerank_fn,
            allow_seq=allow_seq,
            seq_op=seq_op,
            lexicon=lexicon,
            weight=rerank_weight,
        )
        if reranked:
            best = reranked[0]
            best_ir = best["ir"]
            best_cost = best["score"]
        rerank_info = {
            "candidates": len(candidates),
            "scored": len(reranked),
            "top": reranked[:5],
        }

    if best_ir is None:
        top_k = len(beam) if finalize_top_k <= 0 else min(len(beam), finalize_top_k)
        candidates: List[IRNode] = []
        for ir, _ in beam[:top_k]:
            candidates.extend(
                _rewrite_candidates(ir, max_variants=max(1, rewrite_max_variants))
            )
        if any(t.has_tag("ABSOLUTE_AGENT_SUFFIX") for t in stream):
            with_sara = [c for c in candidates if _contains_deverbal_lexeme(c, "sara")]
            if with_sara:
                candidates = with_sara
        best_ir, best_cost = _select_best_by_cost(candidates, scorer)

    if emit == "pydicate":
        code = render_pydicate(
            best_ir, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon
        )
    else:
        code = render_ir(best_ir)

    return DecompileResult(
        ir=best_ir,
        cost=best_cost,
        code=code,
        beam=[(ir, cost) for ir, cost in beam],
        debug={
            "tokens": stream,
            "beam_size": beam_size,
            "emit": emit,
            "allow_seq": allow_seq,
            "seq_op": seq_op,
            "registry_size": len(registry.predicates),
            "lexicon_size": len(lexicon.entries) if lexicon else 0,
            "finalize_top_k": finalize_top_k,
            "rewrite_max_variants": rewrite_max_variants,
            "rerank": rerank_info,
        },
    )
