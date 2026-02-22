from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from typing import Dict, Iterable, Optional, Sequence, Tuple

from pydicate.predicate import Predicate

from .normalize import normalize_lexeme


def _default_lexicon_modules() -> Tuple[str, ...]:
    env = os.environ.get("PYDICATE_LEXICON_MODULES", "")
    if env.strip():
        modules = [m.strip() for m in env.split(",") if m.strip()]
        return tuple(modules)
    return (
        "pydicate.lang.tupilang.pos",
        "pydicate.lang.tupilang.nouns",
    )


@dataclass(frozen=True)
class LexemeInfo:
    symbol: str
    qualname: str
    pos: str
    lexeme: str


@dataclass(frozen=True)
class LexiconRegistry:
    entries: Dict[Tuple[str, str], LexemeInfo]
    pos_by_lexeme: Dict[str, Tuple[str, ...]]

    def lookup(self, pos: str, lexeme: str) -> Optional[LexemeInfo]:
        return self.entries.get((pos, lexeme))

    def pos_candidates(self, lexeme: str) -> Tuple[str, ...]:
        return self.pos_by_lexeme.get(lexeme, ())


def _iter_predicate_instances(module) -> Iterable[Tuple[str, Predicate]]:
    for name, obj in vars(module).items():
        if isinstance(obj, Predicate):
            yield name, obj


def build_lexicon(
    modules: Optional[Sequence[str]] = None,
) -> LexiconRegistry:
    entries: Dict[Tuple[str, str], LexemeInfo] = {}
    pos_by_lexeme: Dict[str, set] = {}
    modules = modules or _default_lexicon_modules()

    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for symbol, pred in _iter_predicate_instances(module):
            lexeme = getattr(pred, "verbete", None)
            if not lexeme:
                continue
            pos = pred.__class__.__name__
            info = LexemeInfo(
                symbol=symbol,
                qualname=f"{module_name}.{symbol}",
                pos=pos,
                lexeme=lexeme,
            )
            pos_candidates = {pos}
            category = getattr(pred, "category", "") or ""
            if pos in {"VerbAugmentor"} or category.startswith("verb"):
                pos_candidates.add("Verb")
            if category == "particle":
                pos_candidates.add("Particle")
            for pos_name in pos_candidates:
                for key in (lexeme, normalize_lexeme(pos_name, lexeme)):
                    if not key:
                        continue
                    entries.setdefault((pos_name, key), info)
                    pos_by_lexeme.setdefault(key, set()).add(pos_name)

    pos_final = {k: tuple(sorted(v)) for k, v in pos_by_lexeme.items()}
    return LexiconRegistry(entries=entries, pos_by_lexeme=pos_final)
