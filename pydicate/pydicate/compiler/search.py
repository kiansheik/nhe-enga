from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .constraints import DEFAULT_CONSTRAINTS, resolve_constraints
from .ir import Atom, IRKind, IRNode, MorphOp, Op
from .pretty import canonicalize_ir, render_ir, render_pydicate
from .registry import PredicateRegistry, build_registry
from .scoring import DefaultScorer, Scorer
from .tokens import Token, ensure_tokens


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

_PREFIX_TAG_KINDS = {
    "PLURIFORM_PREFIX",
    "PATIENT_PREFIX",
    "SUBJECT_PREFIX",
    "OBJECT_PREFIX",
    "OBJECT_MARKER",
    "GERUND_SUBJECT_PREFIX",
    "IMPERATIVE_PREFIX",
    "PERMISSIVE_PREFIX",
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
    if node.kind == IRKind.OP and node.name == "MUL" and node.children:
        return _is_nounish(node.children[0])
    if node.kind == IRKind.OP and node.name == "ADD" and node.children:
        return all(_is_nounish(child) for child in node.children)
    return any(
        kind in {"NOUN", "NNOUN", "PROPER_NOUN", "PRONOUN", "DEVERBAL", "DEADVERBAL"}
        for kind in _node_tag_kinds(node)
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


def _as_pos(node: IRNode, pos: str) -> IRNode:
    if node.kind != IRKind.ATOM:
        return node
    return IRNode(node.kind, pos, node.children, dict(node.attrs))


def _is_subject_marker(node: IRNode) -> bool:
    kinds = _node_tag_kinds(node)
    return any(
        k in kinds for k in ("SUBJECT", "SUBJECT_PREFIX", "GERUND_SUBJECT_PREFIX")
    )


def _is_object_marker(node: IRNode) -> bool:
    kinds = _node_tag_kinds(node)
    return any(
        k in kinds
        for k in ("OBJECT", "OBJECT_PREFIX", "OBJECT_MARKER", "PATIENT_PREFIX")
    )


def _is_implicit_marker(node: IRNode) -> bool:
    kinds = _node_tag_kinds(node)
    return any(
        k in kinds
        for k in (
            "SUBJECT_PREFIX",
            "GERUND_SUBJECT_PREFIX",
            "OBJECT_PREFIX",
            "OBJECT_MARKER",
            "PATIENT_PREFIX",
        )
    )


def _contains_verbish(node: IRNode) -> bool:
    for n in node.walk():
        if n.kind == IRKind.ATOM and n.name in _VERBISH_POS:
            return True
    return False


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
        suffix_only = "ROOT" not in kinds
        if "FACILITY_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    out[-1] = Op("MUL", Atom("Deverbal", "saba"), out[-1])
                else:
                    out.append(Atom("Deverbal", "saba"))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                out.append(Op("MUL", Atom("Deverbal", "saba"), node))
            elif out:
                out[-1] = Op("MUL", Atom("Deverbal", "saba"), out[-1])
            else:
                out.append(Atom("Deverbal", "saba"))
            continue
        if "ABSOLUTE_AGENT_SUFFIX" in kinds or "ACTIVE_AGENT_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    out[-1] = Op("MUL", Atom("Deverbal", "sara"), out[-1])
                else:
                    out.append(Atom("Deverbal", "sara"))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                out.append(Op("MUL", Atom("Deverbal", "sara"), node))
            elif out:
                out[-1] = Op("MUL", Atom("Deverbal", "sara"), out[-1])
            else:
                out.append(Atom("Deverbal", "sara"))
            continue
        if "AGENTLESS_PATIENT_SUFFIX" in kinds:
            if suffix_only:
                if out:
                    out[-1] = Op(
                        "MUL", Atom("Deverbal", "pyra"), _strip_verb_args(out[-1])
                    )
                else:
                    out.append(Atom("Deverbal", "pyra"))
                continue
            if _contains_verbish(node) or "ROOT" in kinds:
                out.append(Op("MUL", Atom("Deverbal", "pyra"), _strip_verb_args(node)))
            elif out:
                out[-1] = Op("MUL", Atom("Deverbal", "pyra"), _strip_verb_args(out[-1]))
            else:
                out.append(Atom("Deverbal", "pyra"))
            continue
        out.append(node)
    return out


def _drop_substantive_suffix_tokens(nodes: List[IRNode]) -> List[IRNode]:
    out: List[IRNode] = []
    for node in nodes:
        kinds = _node_tag_kinds(node)
        if "SUBSTANTIVE_SUFFIX" in kinds:
            morph = None
            token = _node_token(node)
            if token:
                morph = token.m
            if morph and len(morph) <= 2:
                if out:
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
                    if "DEVERBAL" in kinds:
                        out[-1] = _as_pos(out[-1], "Deverbal")
                    elif "DEADVERBAL" in kinds:
                        out[-1] = _as_pos(out[-1], "Deadverbal")
                    elif "NOUN" in kinds or "NNOUN" in kinds:
                        if _node_pos(out[-1]) not in _NOUNISH_POS:
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
        if (
            "IMPERATIVE_PREFIX" in kinds
            and i + 1 < len(nodes)
            and _is_verbish(nodes[i + 1])
        ):
            out.append(MorphOp("IMP", nodes[i + 1]))
            i += 2
            continue
        out.append(node)
        i += 1
    return out


def _merge_possessives_and_postpositions(nodes: List[IRNode]) -> List[IRNode]:
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
        if _is_postposition(node) and out:
            for idx in range(len(out) - 1, -1, -1):
                if _is_nounish(out[idx]):
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


def _merge_possessives(nodes: List[IRNode]) -> List[IRNode]:
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


def _attach_markers(nodes: List[IRNode], marker_fn) -> List[IRNode]:
    out: List[IRNode] = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if marker_fn(node):
            if _is_implicit_marker(node):
                # Agreement prefixes don't surface as pronouns; drop after use.
                i += 1
                continue
            j = i + 1
            while j < len(nodes) and _is_prefix(nodes[j]):
                j += 1
            if j < len(nodes) and _contains_verbish(nodes[j]):
                out.append(Op("MUL", node, nodes[j]))
                i = j + 1
                continue
            if out and _contains_verbish(out[-1]):
                out[-1] = Op("MUL", out[-1], node)
                i += 1
                continue
        out.append(node)
        i += 1
    return out


def _attach_argument_markers(nodes: List[IRNode]) -> List[IRNode]:
    # Attach subjects first so objects can wrap verb+subject when needed.
    nodes = _attach_markers(nodes, _is_subject_marker)
    nodes = _attach_markers(nodes, _is_object_marker)
    return nodes


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
    nodes = _apply_negation_suffix(nodes)
    nodes = _drop_substantive_suffix_tokens(nodes)
    nodes = _apply_pluriform_marks(nodes)
    nodes = _apply_conjunctions(nodes)
    nodes = _apply_pluriform_relations(nodes)
    nodes = _merge_possessives(nodes)
    nodes = _attach_argument_markers(nodes)
    nodes = _apply_deverbal_suffixes(nodes)
    nodes = _merge_possessives_and_postpositions(nodes)
    if len(nodes) == 1:
        return nodes[0]
    return Op("SEQ", *nodes)


def _combine_seq(lhs: Optional[IRNode], rhs: IRNode) -> IRNode:
    if lhs is None:
        return rhs
    if lhs.kind == IRKind.OP and lhs.name == "SEQ":
        return IRNode(IRKind.OP, "SEQ", lhs.children + (rhs,), dict(lhs.attrs))
    return Op("SEQ", lhs, rhs)


def _candidate_atoms(token: Token, constraints: Dict[str, Any]) -> List[IRNode]:
    allowed_pos, morph_ops = resolve_constraints(token.tag_kinds, constraints)
    if not allowed_pos:
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
        atom = Atom(pos, token.m, token=token)
        wrapped = _wrap_morph_ops(atom, morph_ops)
        candidates.append(wrapped)
    return candidates


def decompile(
    tokens: Iterable[Any],
    *,
    registry: Optional[PredicateRegistry] = None,
    constraints: Optional[Dict[str, Any]] = None,
    scorer: Optional[Scorer] = None,
    beam_size: int = 32,
    emit: str = "ir",
    allow_seq: bool = True,
    seq_op: str = "+",
) -> DecompileResult:
    registry = registry or build_registry()
    constraints = constraints or DEFAULT_CONSTRAINTS
    scorer = scorer or DefaultScorer()

    stream = ensure_tokens(tokens)
    beam: List[Tuple[Optional[IRNode], float]] = [(None, 0.0)]

    for token in stream:
        candidates = _candidate_atoms(token, constraints)
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

    best_ir, best_cost = beam[0]
    best_ir = canonicalize_ir(_rewrite_sequence(best_ir))

    if emit == "pydicate":
        code = render_pydicate(best_ir, allow_seq=allow_seq, seq_op=seq_op)
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
        },
    )
