from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, List, Optional, Sequence, Tuple

_MORPH_TAG_RE = re.compile(r"([^\[\]\s]+)((?:\[[^\]]+\])+)", flags=re.UNICODE)
_TAG_RE = re.compile(r"\[([^\]]+)\]")


@dataclass(frozen=True)
class Token:
    m: str
    t: Optional[str] = None
    s: Tuple[str, ...] = ()
    surface: Optional[str] = None

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


def token_from_raw(raw: Any) -> Token:
    if isinstance(raw, Token):
        return raw
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
            m=str(m) if m is not None else "", t=t, s=tuple(s), surface=surface
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
        prefix = inter.strip()
        if prefix:
            morph = f"{prefix} {morph}"
        tokens.append(Token(m=morph, t=t, s=s, surface=m.group(0)))
        last_end = m.end()
    return tokens
