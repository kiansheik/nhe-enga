#!/usr/bin/env python3
"""Register fresh citation cases using metadata only, without model predictions.

The old 48 released cases are development/regression data in version two.
New cases are selected by deterministic SHA256 order from remaining pages and
headwords. One case per page and normalized headword limits dependent items.
The resulting sample is conditional on these exclusions, not a population
accuracy survey. This script never reads mining outputs or annotation labels.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).resolve().parent
SEED = "VLB-review-loop-independent-v2-2026-11-03"
COUNT = 24


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def norm(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.lower()) if c.isalpha())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main():
    manifest = read(ROOT / "vlb/data/manifest.json")
    previous = read(ROOT / "vlb/mining/benchmark/preregistered_sample.json")
    pages = [read(ROOT / "vlb/data" / row["data_file"]) for row in manifest["pages"]]
    page_map = {page["id"]: page for page in pages}
    excluded_heads = set(previous["holdout_headwords"]) | set(previous["excluded_prior_pilot_headwords"])
    excluded_heads = {norm(x) for x in excluded_heads}
    excluded_pages = set(previous["holdout_page_ids"]) | {"I-017", "I-018"}
    excluded_sources = set(previous["holdout_source_ids"])
    # Never select another fragment of a previously inspected test paragraph.
    excluded_pages.update(page["id"] for page in pages if any(f["id"] in excluded_sources for f in page["fragments"]))
    pool = []
    for page in pages:
        if page["id"] in excluded_pages:
            continue
        for citation in page["citations"]:
            if norm(citation["headword"]) in excluded_heads:
                continue
            identity = citation["id"] + "|" + page["id"]
            order = hashlib.sha256((SEED + "|" + identity).encode()).hexdigest()
            pool.append((order, page, citation))
    selected, material, seen_heads, seen_pages = [], [], set(), set()
    for order, page, citation in sorted(pool, key=lambda x: x[0]):
        head = norm(citation["headword"])
        if head in seen_heads or page["id"] in seen_pages:
            continue
        seen_heads.add(head)
        seen_pages.add(page["id"])
        case = {"case_id": "v2-" + order[:12], "citation_id": citation["id"],
                "page_id": page["id"], "headword": citation["headword"],
                "entry_index": citation["entry_index"], "homonym": citation.get("homonym", ""),
                "volume": page["volume"], "normalized_headword": head,
                "adapted": citation.get("adapted", False), "split": "test",
                "selection_order": len(selected) + 1}
        selected.append(case)
        material.append({**case, "citation": {k: v for k, v in citation.items() if k != "associations"},
                         "fragments": [{k: v for k, v in f.items() if k not in ("associations", "ocr")}
                                       for f in page["fragments"]]})
        if len(selected) == COUNT:
            break
    assert len(selected) == COUNT
    old_development = [{**row, "split": "dev", "previous_split": row["split"]} for row in previous["selected"]]
    holdout_pages = set(previous["holdout_page_ids"]) | seen_pages
    holdout_sources = set(previous["holdout_source_ids"])
    holdout_sources.update(f["id"] for page_id in seen_pages for f in page_map[page_id]["fragments"])
    result = {"schema_version": 1, "seed": SEED, "purpose": "V2 metadata-only registration; all V1 cases are released development data.",
              "selection_basis": "Fixed SHA256 ordering, excluding V1 headwords/pages/continuations and prior pilot heads; accept one case per page and normalized headword until 24. No rankings or labels read.",
              "population_limit": "Conditional sample of previously unselected pages/headwords; not an unbiased full-corpus prevalence estimate.",
              "dictionary_sha256": previous["dictionary_sha256"], "source_sha256": previous["source_sha256"],
              "selected": old_development + selected,
              "holdout_headwords": sorted(set(previous["holdout_headwords"]) | seen_heads),
              "holdout_page_ids": sorted(holdout_pages), "holdout_source_ids": sorted(holdout_sources),
              "new_test_count": COUNT, "previous_development_count": len(old_development),
              "human_verified": False}
    write(DEST / "preregistered_sample.json", result)
    write(DEST / "review_material.json", {"schema_version": 1, "rankings_included": False,
                                          "dictionary_sha256": previous["dictionary_sha256"],
                                          "source_sha256": previous["source_sha256"], "cases": material})
    print(json.dumps([{k: c[k] for k in ("case_id", "headword", "page_id")} for c in selected], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
