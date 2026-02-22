from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple


from .ir import IRKind, IRNode
from .lexicon import LexiconRegistry
from .normalize import normalize_lexeme

_OP_SYMBOLS: Dict[str, str] = {
    "MUL": "*",
    "ADD": "+",
    "EQ": "==",
    "AT": "@",
    "SHIFT_L": "<<",
    "SHIFT_R": ">>",
}

_MORPH_METHODS: Dict[str, str] = {
    "VOC": "voc",
    "IMP": "imp",
    "PERM": "perm",
    "CIRC": "circ",
    "REDUP": "redup",
    "BASE_NOMINAL": "base_nominal",
    "VAR": "var",
}

_PRONOUN_VARS = {
    "ixé",
    "xe",
    "îandé",
    "oré",
    "endé",
    "nde",
    "pee",
    "ae",
    "îe",
    "îo",
    "og",
}

_DEVERBAL_VARS = {
    "pyra",
    "emi",
    "sara",
    "a",
    "saba",
}


_POSTPOSITION_VARS = {
    "esé",
    "suí",
    "pupé",
    "pe",
    "supé",
    "amo",
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


def _pronoun_inflection_from_token(node: IRNode) -> Optional[str]:
    token = None
    if node.kind == IRKind.ATOM:
        token = node.attrs.get("token")
    if not token:
        return None
    for tag in token.tags:
        parts = tag.split(":")
        for part in parts:
            if part in _INFLECTION_CODES:
                return part
    return None


def _pronoun_tag_from_token(node: IRNode) -> Optional[str]:
    token = None
    if node.kind == IRKind.ATOM:
        token = node.attrs.get("token")
    if not token:
        return None
    for tag in token.tags:
        kind = tag.split(":", 1)[0]
        if kind in {
            "SUBJECT",
            "OBJECT",
            "OBJECT_PREFIX",
            "OBJECT_MARKER",
            "POSSESSIVE_PRONOUN",
            "PRONOUN",
        }:
            return f"[{tag}]"
    return None


def _is_pluriform(node: IRNode) -> bool:
    return bool(node.attrs.get("pluriform"))


def canonicalize_ir(node: IRNode) -> IRNode:
    if not node.children:
        return node

    children = tuple(canonicalize_ir(c) for c in node.children)
    if node.kind == IRKind.OP and node.name in {"SEQ"}:
        flattened = []
        for child in children:
            if child.kind == IRKind.OP and child.name == node.name:
                flattened.extend(child.children)
            else:
                flattened.append(child)
        children = tuple(flattened)
    return IRNode(node.kind, node.name, children, dict(node.attrs))


def render_ir(node: IRNode) -> str:
    if node.kind == IRKind.ATOM:
        lexeme = node.attrs.get("lexeme")
        if lexeme is None:
            return f"{node.name}()"
        return f"{node.name}({lexeme!r})"

    if node.kind == IRKind.MORPH:
        inner = render_ir(node.children[0]) if node.children else ""
        if node.name in _MORPH_METHODS:
            return f"{node.name}({inner})"
        return f"{node.name}({inner})"

    if node.kind == IRKind.SUGAR:
        args = ", ".join(render_ir(c) for c in node.children)
        return f"{node.name}({args})"

    if node.kind == IRKind.OP:
        if node.name == "SEQ":
            args = ", ".join(render_ir(c) for c in node.children)
            return f"SEQ({args})"
        symbol = _OP_SYMBOLS.get(node.name)
        if symbol and node.children:
            joined = f" {symbol} ".join(render_ir(c) for c in node.children)
            return f"({joined})"
        args = ", ".join(render_ir(c) for c in node.children)
        return f"{node.name}({args})"

    return "<unknown>"


def render_pydicate(
    node: IRNode,
    allow_seq: bool = False,
    seq_op: str = "+",
    lexicon: Optional[LexiconRegistry] = None,
) -> str:
    def _lexicon_symbol(
        pos: str, lexeme: Optional[str], *, node: Optional[IRNode] = None
    ) -> Optional[str]:
        if not lexicon or not lexeme:
            return None
        info = lexicon.lookup(pos, lexeme)
        if info:
            return info.symbol
        if node:
            suffixes = tuple(node.attrs.get("suffix_morphs", ()))
            if suffixes:
                for suffix in suffixes:
                    candidate = f"{lexeme}{suffix}"
                    candidate = normalize_lexeme(pos, candidate)
                    info = lexicon.lookup(pos, candidate)
                    if info:
                        return info.symbol
        return None

    if node.kind == IRKind.ATOM:
        lexeme = node.attrs.get("lexeme")
        if node.name in {"Predicate", "Tok", "Unknown"}:
            lexeme = lexeme if lexeme is not None else ""
            return f"Predicate({lexeme!r}, category='tok', min_args=0, tag='[TOK]')"
        if node.name == "Pronoun":
            lexeme = normalize_lexeme("Pronoun", lexeme)
            infl = _pronoun_inflection_from_token(node)
            tag = _pronoun_tag_from_token(node)
            if lexeme in _PRONOUN_VARS:
                if tag and (tag.startswith("[OBJECT") or tag.startswith("[SUBJECT")):
                    if infl:
                        return f"Pronoun({lexeme!r}, inflection_override={infl!r}, tag={tag!r})"
                    return f"Pronoun({lexeme!r}, tag={tag!r})"
                return lexeme
            if infl:
                if lexeme:
                    if tag:
                        return f"Pronoun({lexeme!r}, inflection_override={infl!r}, tag={tag!r})"
                    return f"Pronoun({lexeme!r}, inflection_override={infl!r})"
                if tag:
                    return f"Pronoun({infl!r}, tag={tag!r})"
                return f"Pronoun({infl!r})"
            symbol = _lexicon_symbol("Pronoun", lexeme, node=node)
            if symbol:
                return symbol
            if lexeme is None:
                return "Pronoun()"
            if tag:
                return f"Pronoun({lexeme!r}, tag={tag!r})"
            return f"Pronoun({lexeme!r})"
        if node.name == "Postposition":
            lexeme = normalize_lexeme("Postposition", lexeme)
            if lexeme in _POSTPOSITION_VARS:
                return lexeme
            if lexeme is None:
                return "Postposition()"
            if _is_pluriform(node):
                return f"Postposition({lexeme!r}, definition='(t) undef')"
            symbol = _lexicon_symbol("Postposition", lexeme, node=node)
            if symbol:
                return symbol
            return f"Postposition({lexeme!r})"
        if node.name == "Verb":
            lexeme = normalize_lexeme("Verb", lexeme)
            if lexeme is None:
                return "Verb()"
            symbol = _lexicon_symbol("Verb", lexeme, node=node)
            if symbol:
                return symbol
            verb_class = node.attrs.get("verb_class")
            if verb_class:
                if _is_pluriform(node):
                    if not str(verb_class).strip().startswith("(t)"):
                        verb_class = f"(t) {verb_class}"
                return f"Verb({lexeme!r}, verb_class={verb_class!r})"
            if _is_pluriform(node):
                return f"Verb({lexeme!r}, verb_class='(t) undef')"
            return f"Verb({lexeme!r})"
        if node.name == "Noun":
            lexeme = normalize_lexeme("Noun", lexeme)
            if lexeme is None:
                return "Noun()"
            if _is_pluriform(node):
                return f"Noun({lexeme!r}, definition='(t) undef')"
            symbol = _lexicon_symbol("Noun", lexeme, node=node)
            if symbol:
                return symbol
            return f"Noun({lexeme!r})"
        if node.name == "ProperNoun":
            lexeme = normalize_lexeme("ProperNoun", lexeme)
            if lexeme is None:
                return "ProperNoun()"
            if _is_pluriform(node):
                return f"ProperNoun({lexeme!r}, definition='(t) undef')"
            symbol = _lexicon_symbol("ProperNoun", lexeme, node=node)
            if symbol:
                return symbol
            return f"ProperNoun({lexeme!r})"
        if node.name == "Deverbal":
            lexeme = normalize_lexeme("Deverbal", lexeme)
            if lexeme in _DEVERBAL_VARS:
                return lexeme
            symbol = _lexicon_symbol("Deverbal", lexeme, node=node)
            if symbol:
                return symbol
            if lexeme is None:
                return "Deverbal()"
            return f"Deverbal({lexeme!r})"
        symbol = _lexicon_symbol(node.name, lexeme, node=node)
        if symbol:
            return symbol
        if lexeme is None:
            return f"{node.name}()"
        return f"{node.name}({lexeme!r})"

    if node.kind == IRKind.MORPH:
        if not node.children:
            return node.name
        inner = render_pydicate(
            node.children[0], allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon
        )
        if node.name == "NEG":
            return f"-({inner})"
        if node.name == "RUA":
            return f"~({inner})"
        if node.name == "PRO_DROP":
            if inner and inner[0].isidentifier():
                return f"+{inner}"
            return f"+({inner})"
        method = _MORPH_METHODS.get(node.name)
        if method:
            if node.name == "VAR":
                value = node.attrs.get("value")
                if value is None:
                    return f"({inner}).{method}()"
                return f"({inner}).{method}({value!r})"
            return f"({inner}).{method}()"
        return f"{node.name}({inner})"

    if node.kind == IRKind.SUGAR:
        args = ", ".join(
            render_pydicate(c, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon)
            for c in node.children
        )
        return f"{node.name}({args})"

    if node.kind == IRKind.OP:
        if node.name == "SEQ":
            if not allow_seq:
                raise ValueError("SEQ is not directly representable in pydicate")
            joined = f" {seq_op} ".join(
                render_pydicate(c, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon)
                for c in node.children
            )
            return f"({joined})"
        symbol = "@" if node.name == "EQ" else _OP_SYMBOLS.get(node.name)
        if symbol and node.children:
            joined = f" {symbol} ".join(
                render_pydicate(c, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon)
                for c in node.children
            )
            return f"({joined})"
        args = ", ".join(
            render_pydicate(c, allow_seq=allow_seq, seq_op=seq_op, lexicon=lexicon)
            for c in node.children
        )
        return f"{node.name}({args})"

    return "<unknown>"
