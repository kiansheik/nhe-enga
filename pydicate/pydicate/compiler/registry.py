from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Dict, Iterable, List, Optional

from pydicate.predicate import Predicate


OPS = {
    "__mul__": "*",
    "__add__": "+",
    "__eq__": "==",
    "__matmul__": "@",
    "__lshift__": "<<",
    "__rshift__": ">>",
    "__truediv__": "/",
    "__neg__": "unary -",
    "__pos__": "unary +",
    "__invert__": "unary ~",
}

METHOD_HINTS = (
    "imp",
    "voc",
    "perm",
    "circ",
    "redup",
    "var",
    "eval",
    "base_nominal",
    "card",
)


@dataclass(frozen=True)
class PredicateInfo:
    name: str
    qualname: str
    init_sig: Optional[str]
    default_category: Optional[str]
    operators: List[str]
    methods: List[str]


@dataclass(frozen=True)
class PredicateRegistry:
    predicates: Dict[str, PredicateInfo]
    operators: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, Dict[str, object]]:
        return {name: info.__dict__ for name, info in self.predicates.items()}


def _iter_subclasses(cls: type) -> Iterable[type]:
    seen = set()
    stack = [cls]
    while stack:
        c = stack.pop()
        for sc in c.__subclasses__():
            if sc in seen:
                continue
            seen.add(sc)
            stack.append(sc)
            yield sc


def _method_list(cls: type) -> List[str]:
    methods: List[str] = []
    for name in dir(cls):
        if name.startswith("_"):
            continue
        if not name.startswith(METHOD_HINTS):
            continue
        obj = getattr(cls, name, None)
        if obj is None:
            continue
        if inspect.isfunction(obj) or inspect.ismethoddescriptor(obj):
            methods.append(name)
    return sorted(set(methods))


def _operator_list(cls: type, base_cls: type) -> List[str]:
    ops = []
    for meth, sym in OPS.items():
        if not hasattr(cls, meth):
            continue
        if getattr(cls, meth, None) is getattr(base_cls, meth, None):
            continue
        ops.append(sym)
    return ops


def build_registry(base_cls: type = Predicate) -> PredicateRegistry:
    predicates: Dict[str, PredicateInfo] = {}
    operators: Dict[str, List[str]] = {}

    for cls in _iter_subclasses(base_cls):
        try:
            init_sig = str(inspect.signature(cls.__init__))
        except (TypeError, ValueError):
            init_sig = None
        try:
            default_category = cls._default_category()
        except Exception:
            default_category = None
        info = PredicateInfo(
            name=cls.__name__,
            qualname=f"{cls.__module__}.{cls.__name__}",
            init_sig=init_sig,
            default_category=default_category,
            operators=_operator_list(cls, base_cls),
            methods=_method_list(cls),
        )
        predicates[cls.__name__] = info
        for op in info.operators:
            operators.setdefault(op, []).append(cls.__name__)

    return PredicateRegistry(predicates=predicates, operators=operators)
