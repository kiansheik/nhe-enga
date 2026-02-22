from __future__ import annotations

import csv
import os
from functools import lru_cache
from typing import Dict, Optional


_DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "lexeme_normalization.csv")


def _read_csv(path: str) -> Dict[str, Dict[str, str]]:
    table: Dict[str, Dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pos = (row.get("pos") or "").strip()
            surface = (row.get("surface") or "").strip()
            lemma = (row.get("lemma") or "").strip()
            if not surface or not lemma:
                continue
            if not pos:
                pos = "*"
            table.setdefault(pos, {})[surface] = lemma
    return table


@lru_cache(maxsize=1)
def _normalization_table() -> Dict[str, Dict[str, str]]:
    path = os.environ.get("PYDICATE_LEXEME_CSV", _DEFAULT_CSV)
    if not os.path.exists(path):
        return {}
    try:
        return _read_csv(path)
    except Exception:
        return {}


def normalize_lexeme(pos: str, lexeme: Optional[str]) -> Optional[str]:
    if lexeme is None:
        return lexeme
    table = _normalization_table()
    if not table:
        return lexeme
    if pos in table and lexeme in table[pos]:
        return table[pos][lexeme]
    if "*" in table and lexeme in table["*"]:
        return table["*"][lexeme]
    return lexeme
