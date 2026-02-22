from __future__ import annotations

import argparse
import importlib
import json
from typing import Iterable, List, Optional

from pydicate.predicate import Predicate

from .tokens import Token, parse_annotated


def _iter_predicates(module) -> Iterable[tuple[str, Predicate]]:
    for name, obj in vars(module).items():
        if isinstance(obj, Predicate):
            yield name, obj


def _token_to_dict(token: Token) -> dict:
    return {"m": token.m, "t": token.t, "s": list(token.s), "surface": token.surface}


def generate_examples(modules: List[str], *, limit: Optional[int] = None) -> List[dict]:
    examples: List[dict] = []
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for symbol, pred in _iter_predicates(module):
            if limit is not None and len(examples) >= limit:
                return examples
            try:
                annotated = pred.eval(annotated=True)
            except Exception:
                continue
            tokens = parse_annotated(annotated)
            examples.append(
                {
                    "symbol": symbol,
                    "module": module_name,
                    "code": symbol,
                    "pos": pred.__class__.__name__,
                    "lexeme": getattr(pred, "verbete", None),
                    "annotated": annotated,
                    "tokens": [_token_to_dict(t) for t in tokens],
                }
            )
    return examples


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic decompilation examples from lexicon modules."
    )
    parser.add_argument(
        "--modules",
        default="pydicate.lang.tupilang.pos,pydicate.lang.tupilang.nouns",
        help="Comma-separated module list to scan for Predicate instances.",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--out", default="-", help="Output JSONL path or '-' for stdout."
    )

    args = parser.parse_args(argv)
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    limit = None if args.limit <= 0 else args.limit

    examples = generate_examples(modules, limit=limit)
    if args.out == "-":
        for ex in examples:
            print(json.dumps(ex, ensure_ascii=False))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False))
                f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
