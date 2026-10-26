#!/usr/bin/env python3
"""Rank documentary scan pages for each cited Anchieta Teatro page.

This is an evidence-producing helper, not an automatic source-map writer.
It compares the text surrounding each served-dictionary citation with Internet
Archive's DjVu XML OCR for the Martins documentary edition and prints candidate
PDF indices for human review.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET


CITATION_RE = re.compile(
    r"\bAnch\.,?\s*Teatro,\s*(?P<page>\d+)(?:\s*,\s*(?P<year>\d{4}))?",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[a-z0-9]{3,}")
STOPWORDS = {
    "ainda",
    "assim",
    "como",
    "com",
    "das",
    "delas",
    "deles",
    "depois",
    "dos",
    "ela",
    "ele",
    "eles",
    "essa",
    "esse",
    "esta",
    "este",
    "isso",
    "isto",
    "mais",
    "mas",
    "meu",
    "minha",
    "muito",
    "nao",
    "nas",
    "nos",
    "para",
    "pela",
    "pelo",
    "por",
    "porque",
    "que",
    "quem",
    "seu",
    "sua",
    "tambem",
    "todo",
    "uma",
    "voces",
}


def normalized_words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    text = text.replace("ŷ", "y").replace("î", "i").replace("û", "u")
    return [word for word in WORD_RE.findall(text) if word not in STOPWORDS]


def citation_contexts(dictionary_path: Path) -> dict[tuple[int, str | None], list[str]]:
    with gzip.open(dictionary_path, "rt", encoding="utf-8") as dictionary_file:
        entries = json.load(dictionary_file)
    contexts: dict[tuple[int, str | None], list[str]] = defaultdict(list)
    for entry in entries:
        definition = entry.get("d", "")
        for match in CITATION_RE.finditer(definition):
            # Prefer the final source/translation pair immediately before the
            # citation. The broader bounded window is a fallback for entries
            # whose delimiter is missing or malformed.
            start = max(0, match.start() - 300)
            context = definition[start : match.start()]
            delimiter = context.rfind(" - ")
            if delimiter >= 0:
                source_prefix = context[:delimiter]
                boundary = max(
                    source_prefix.rfind(")"),
                    source_prefix.rfind(";"),
                    source_prefix.rfind("●"),
                    source_prefix.rfind(":"),
                )
                source = source_prefix[boundary + 1 :]
                translation = context[delimiter + 3 :]
                focused = f"{source} {translation}".strip()
                if len(normalized_words(focused)) >= 3:
                    context = focused
            contexts[(int(match.group("page")), match.group("year"))].append(context)
    return contexts


def ocr_pages(ocr_path: Path) -> list[str]:
    root = ET.parse(ocr_path).getroot()
    return [
        " ".join(word.text or "" for word in page.findall(".//WORD"))
        for page in root.findall(".//OBJECT")
    ]


def tf_idf_vectors(
    documents: list[list[str]],
) -> tuple[list[Counter[str]], dict[str, float]]:
    vectors = [Counter(document) for document in documents]
    frequencies: Counter[str] = Counter()
    for vector in vectors:
        frequencies.update(vector.keys())
    total = len(vectors)
    weights = {
        word: math.log((total + 1) / (frequency + 1)) + 1
        for word, frequency in frequencies.items()
    }
    return vectors, weights


def cosine(left: Counter[str], right: Counter[str], weights: dict[str, float]) -> float:
    shared = left.keys() & right.keys()
    numerator = sum(
        left[word] * right[word] * weights.get(word, 1) ** 2 for word in shared
    )
    left_norm = math.sqrt(
        sum(count**2 * weights.get(word, 1) ** 2 for word, count in left.items())
    )
    right_norm = math.sqrt(
        sum(count**2 * weights.get(word, 1) ** 2 for word, count in right.items())
    )
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ocr", required=True, type=Path, help="Internet Archive DjVu XML"
    )
    parser.add_argument(
        "--dictionary", type=Path, default=Path("docs/dict-conjugated.json.gz")
    )
    parser.add_argument("--first-pdf-index", type=int, default=620)
    parser.add_argument("--last-pdf-index", type=int, default=830)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    contexts = citation_contexts(args.dictionary)
    pages = ocr_pages(args.ocr)
    first = max(0, args.first_pdf_index)
    last = min(len(pages) - 1, args.last_pdf_index)
    ocr_documents = [normalized_words(pages[index]) for index in range(first, last + 1)]
    query_documents = [
        normalized_words(" ".join(dict.fromkeys(contexts[locator])))
        for locator in sorted(contexts, key=lambda item: (item[1] or "", item[0]))
    ]
    vectors, weights = tf_idf_vectors(ocr_documents + query_documents)
    ocr_vectors = vectors[: len(ocr_documents)]
    query_vectors = vectors[len(ocr_documents) :]

    locators = sorted(contexts, key=lambda item: (item[1] or "", item[0]))
    for (cited_page, year), query in zip(locators, query_vectors, strict=True):
        ranked = sorted(
            (
                (cosine(query, candidate, weights), first + offset)
                for offset, candidate in enumerate(ocr_vectors)
            ),
            reverse=True,
        )[: args.top]
        candidates = " ".join(f"{index}:{score:.4f}" for score, index in ranked)
        edition = year or "1999"
        print(
            f"{edition} {cited_page:>3}  {len(contexts[(cited_page, year)]):>3} citations  "
            f"{candidates}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
