from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Tuple, Dict, Any, Optional
import re


@dataclass(frozen=True)
class Morpheme:
    text: str
    tags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class OpEvent:
    name: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Emit:
    surface: str
    morphs: List[Morpheme] = field(default_factory=list)
    ops: List[OpEvent] = field(default_factory=list)
    op_scopes: List[int] = field(default_factory=list)

    def __add__(self, other: "Emit") -> "Emit":
        return Emit(
            self.surface + other.surface,
            self.morphs + other.morphs,
            self.ops + other.ops,
            self.op_scopes + other.op_scopes,
        )

    @staticmethod
    def raw(s: str) -> "Emit":
        return Emit(surface=s, morphs=[Morpheme(text=s, tags=())], ops=[], op_scopes=[])


def render_annotated(morphs: Iterable[Morpheme]) -> str:
    out: List[str] = []
    for m in morphs:
        if m.tags:
            op_ids = sorted({t for t in m.tags if t.startswith("OP_ID_")})
            base_tags = [t for t in m.tags if not t.startswith("OP_ID_")]
            if (
                base_tags
                and op_ids
                and not any(
                    t.startswith("OP_TYPE_")
                    or t.startswith("OP_SCOPE_")
                    or t.startswith("OP_MAX_ARGS_")
                    for t in base_tags
                )
            ):
                tags_out = base_tags + op_ids
            else:
                tags_out = list(m.tags)
            blob = "[" + ":".join(tags_out) + "]"
        else:
            blob = ""
        out.append(m.text + blob)
    return "".join(out)


_TAG_RE = re.compile(r"\[([^\]]+)\]")
_CHUNK_RE = re.compile(r"\[([^\]]+)\]|([^\[]+)")


def morphs_from_annotated(text: str) -> List[Morpheme]:
    morphs: List[Morpheme] = []
    pending_text = None
    pending_tags: List[str] = []

    def flush():
        nonlocal pending_text, pending_tags
        if pending_text is None:
            pending_tags = []
            return
        raw_tags = list(pending_tags)
        tags = _normalize_tags(raw_tags)
        morphs.append(Morpheme(text=pending_text, tags=tags))
        pending_text = None
        pending_tags = []

    for m in _CHUNK_RE.finditer(text):
        tag = m.group(1)
        chunk = m.group(2)
        if tag is not None:
            pending_tags.append(tag)
            continue
        if chunk is not None:
            # starting a new text chunk: flush previous morph if it had tags
            if pending_text is not None:
                flush()
            pending_text = chunk

    flush()
    return morphs


def _normalize_tags(raw_tags: Iterable[str]) -> Tuple[str, ...]:
    """
    Normalize repeated bracket tags into a flat tuple of tag + features.
    Treat [TAG][feat][x] as equivalent to [TAG:feat:x] when parsing.
    Remove duplicate features while preserving order.
    Result format: (TAG, feat, x, ...)
    """
    normalized: List[str] = []
    pending_kind = None
    features: List[str] = []

    def flush():
        nonlocal pending_kind, features
        if pending_kind is None:
            return
        normalized.append(pending_kind)
        # dedupe while preserving order
        deduped = list(dict.fromkeys(features))
        normalized.extend(deduped)
        pending_kind = None
        features = []

    for tag in raw_tags:
        if not tag:
            continue
        parts = [p for p in tag.split(":") if p]
        if not parts:
            continue
        kind = parts[0]
        extra = parts[1:]
        if pending_kind is None:
            pending_kind = kind
            features.extend(extra)
            continue
        if kind == pending_kind and not extra:
            # [TAG][TAG] case, just skip duplicate
            continue
        if kind == pending_kind and extra:
            features.extend(extra)
            continue
        # treat this as a new tag (flush previous)
        flush()
        pending_kind = kind
        features.extend(extra)

    flush()
    return tuple(normalized)


def op_morpheme(op_id: int, event: OpEvent, max_args: Optional[int] = None) -> Morpheme:
    tags = [
        f"OP_TYPE_{event.name}",
        f"OP_ID_{op_id}",
        f"OP_SCOPE_{op_id}",
    ]
    if max_args is not None:
        tags.append(f"OP_MAX_ARGS_{max_args}")
    return Morpheme(text="", tags=tuple(tags))


def with_op_morphs(
    em: Emit,
    max_args: Optional[Dict[int, int]] = None,
    position: str = "prefix",
) -> List[Morpheme]:
    """
    Return a linear morph stream with op-morphemes inserted.
    position: "prefix" inserts ops before the full morph stream.
    """
    if position not in ("prefix",):
        raise ValueError("position must be 'prefix'")
    max_args = max_args or {}
    ops = [op_morpheme(i, ev, max_args.get(i)) for i, ev in enumerate(em.ops or [])]
    return ops + list(em.morphs or [])


def interleave_ops_by_origin(
    morphs: List[Morpheme],
    ops: List[OpEvent],
    max_args: Optional[Dict[int, int]] = None,
) -> List[Morpheme]:
    """
    Insert op-morphemes before the first morpheme that carries OP_ID_<op_id>.
    """
    max_args = max_args or {}
    out = list(morphs)
    first_pos: Dict[int, int] = {}
    for idx, m in enumerate(out):
        for tag in m.tags:
            if tag.startswith("OP_ID_"):
                try:
                    op_id = int(tag.split("_", 1)[1])
                except ValueError:
                    continue
                if op_id not in first_pos:
                    first_pos[op_id] = idx
    offset = 0
    for op_id, ev in enumerate(ops):
        insert_at = first_pos.get(op_id)
        if insert_at is None:
            insert_at = len(out)
        insert_at += offset
        out.insert(insert_at, op_morpheme(op_id, ev, max_args.get(op_id)))
        offset += 1
    return out
