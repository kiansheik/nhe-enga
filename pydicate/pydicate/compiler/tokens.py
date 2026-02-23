from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from tupi import Emit, Morpheme

_MORPH_TAG_RE = re.compile(r"([^\[\]\s]+)((?:\[[^\]]+\])+)", flags=re.UNICODE)
_TAG_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class Token:
    m: str
    t: Optional[str] = None
    s: Tuple[str, ...] = ()
    surface: Optional[str] = None
    glue_prev: bool = False

    @property
    def tags(self) -> Tuple[str, ...]:
        tags: List[str] = []
        if self.t:
            tags.append(self.t)
        tags.extend(list(self.s))
        return tuple(tags)

    @property
    def tag_kinds(self) -> Tuple[str, ...]:
        kinds = []
        for tag in self.tags:
            if not tag:
                continue
            kinds.append(tag.split(":", 1)[0])
        return tuple(kinds)

    @property
    def tag_features(self) -> Dict[str, Tuple[str, ...]]:
        features: Dict[str, Tuple[str, ...]] = {}
        for tag in self.tags:
            if not tag:
                continue
            parts = [p for p in tag.split(":") if p]
            if not parts:
                continue
            kind = parts[0]
            values = tuple(parts[1:])
            if not values:
                continue
            prev = features.get(kind, ())
            merged = tuple(dict.fromkeys(prev + values))
            features[kind] = merged
        return features

    def tag_values(self, kind: str) -> Tuple[str, ...]:
        return self.tag_features.get(kind, ())

    def has_tag(self, kind: str, value: Optional[str] = None) -> bool:
        if value is None:
            return kind in self.tag_kinds
        return value in self.tag_values(kind)


def token_from_raw(raw: Any) -> Token:
    if isinstance(raw, Token):
        return raw
    if isinstance(raw, Morpheme):
        tags = tuple(raw.tags or ())
        t = tags[0] if tags else None
        s = tuple(tags[1:]) if tags else ()
        surface = raw.text + "".join(f"[{tag}]" for tag in tags)
        return Token(m=raw.text, t=t, s=s, surface=surface)
    if isinstance(raw, dict):
        m = raw.get("m", raw.get("M", raw.get("morph")))
        t = raw.get("t", raw.get("T", raw.get("tag")))
        s = raw.get("s", raw.get("S", raw.get("tags", ())))
        surface = raw.get("surface")
        if s is None:
            s = ()
        if isinstance(s, str):
            s = (s,)
        return Token(
            m=str(m) if m is not None else "",
            t=t,
            s=tuple(s),
            surface=surface,
            glue_prev=bool(raw.get("glue_prev", False)),
        )
    if isinstance(raw, (list, tuple)):
        if len(raw) == 0:
            return Token(m="")
        if len(raw) == 1:
            return Token(m=str(raw[0]))
        if len(raw) == 2:
            return Token(m=str(raw[0]), t=raw[1])
        return Token(m=str(raw[0]), t=raw[1], s=tuple(raw[2]))
    return Token(m=str(raw))


def ensure_tokens(items: Iterable[Any]) -> List[Token]:
    if isinstance(items, Emit):
        return [token_from_raw(m) for m in items.morphs] if items.morphs else [
            Token(m=items.surface, surface=items.surface)
        ]
    if isinstance(items, Morpheme):
        return [token_from_raw(items)]
    if isinstance(items, (list, tuple)) and items and isinstance(items[0], Morpheme):
        return [token_from_raw(m) for m in items]
    return [token_from_raw(x) for x in items]


def parse_annotated(text: str) -> List[Token]:
    tokens: List[Token] = []
    last_end = 0
    for m in _MORPH_TAG_RE.finditer(text):
        morph = m.group(1)
        tags_blob = m.group(2)
        tags = _TAG_RE.findall(tags_blob)
        if tags:
            t = tags[0]
            s = tuple(tags[1:])
        else:
            t = None
            s = ()
        inter = text[last_end : m.start()]
        glue_prev = (m.start() == last_end and last_end != 0) or (
            bool(inter) and not inter.isspace()
        )
        prefix = inter.strip()
        if prefix:
            morph = f"{prefix} {morph}"
        tokens.append(Token(m=morph, t=t, s=s, surface=m.group(0), glue_prev=glue_prev))
        last_end = m.end()
    return tokens
