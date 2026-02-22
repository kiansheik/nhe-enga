from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, Optional, Tuple


class IRKind(str, Enum):
    ATOM = "atom"
    OP = "op"
    MORPH = "morph"
    SUGAR = "sugar"


@dataclass(frozen=True)
class IRNode:
    kind: IRKind
    name: str
    children: Tuple["IRNode", ...] = ()
    attrs: Dict[str, Any] = field(default_factory=dict)

    def with_children(self, *children: "IRNode") -> "IRNode":
        return IRNode(self.kind, self.name, tuple(children), dict(self.attrs))

    def walk(self) -> Iterable["IRNode"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def size(self) -> int:
        return sum(1 for _ in self.walk())


def Atom(pos: str, lexeme: Optional[str] = None, **attrs: Any) -> IRNode:
    payload = dict(attrs)
    if lexeme is not None:
        payload.setdefault("lexeme", lexeme)
    return IRNode(IRKind.ATOM, pos, (), payload)


def Op(name: str, *children: IRNode, **attrs: Any) -> IRNode:
    return IRNode(IRKind.OP, name, tuple(children), dict(attrs))


def MorphOp(name: str, child: IRNode, **attrs: Any) -> IRNode:
    return IRNode(IRKind.MORPH, name, (child,), dict(attrs))


def Sugar(name: str, *children: IRNode, **attrs: Any) -> IRNode:
    return IRNode(IRKind.SUGAR, name, tuple(children), dict(attrs))
