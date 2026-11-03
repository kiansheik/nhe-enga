#!/usr/bin/env python3
"""Register fresh V3 citation cases from pinned metadata only.

This selector deliberately reads no mining output, candidate ranking, or label
file. It excludes every V1/V2 selected headword and page, all source records
reserved by those registrations (including split continuations), and every
correction-ledger decision available in the checkout. A fixed SHA-256 order
then selects one citation per normalized headword and printed page.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import unicodedata


ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).resolve().parent
SEED = "VLB-review-loop-independent-v3-2026-11-03"
COUNT = 24
V1_PATH = ROOT / "vlb/mining/benchmark/preregistered_sample.json"
V2_PATH = ROOT / "vlb/mining/benchmark-v2/preregistered_sample.json"
MANIFEST_PATH = ROOT / "vlb/data/manifest.json"
LEDGER_PATH = ROOT / "vlb/corrections/ledger.jsonl"
CORRECTION_EVENT_IDS = (
    "vlb-correction-91e2dcecb830aa991048-r0001",
    "vlb-correction-5832f39a3422b9709015-r0001",
    "vlb-correction-9eba4de54e9551520e28-r0001",
    "vlb-correction-b1047ede2d9d93974112-r0001",
    "vlb-correction-77eb71202e027510b7c1-r0001",
    "vlb-correction-6475d2e1ea8ae4764b40-r0001",
    "vlb-correction-042ba3d348e9f512e14c-r0001",
    "vlb-correction-791ddae535bd4963a064-r0001",
)
# These pages were explicitly withheld by the V2 metadata selector because
# they had already been inspected during reader development.
LEGACY_DEVELOPMENT_PAGES = {"I-017", "I-018"}


def read(path: Path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value.lower())
        if character.isalpha()
    )


def read_ledger():
    if not LEDGER_PATH.is_file():
        assert not CORRECTION_EVENT_IDS
        return [], None
    rows = [(line, json.loads(line)) for line in LEDGER_PATH.read_text().splitlines() if line.strip()]
    by_id = {event["event_id"]: (line, event) for line, event in rows}
    assert set(CORRECTION_EVENT_IDS) <= set(by_id)
    selected = [by_id[event_id] for event_id in CORRECTION_EVENT_IDS]
    snapshot = "".join(line + "\n" for line, _event in selected).encode()
    return [event for _line, event in selected], hashlib.sha256(snapshot).hexdigest()


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def build():
    manifest = read(MANIFEST_PATH)
    v1 = read(V1_PATH)
    v2 = read(V2_PATH)
    pages = [read(ROOT / "vlb/data" / row["data_file"]) for row in manifest["pages"]]
    page_map = {page["id"]: page for page in pages}
    ledger_events, ledger_sha256 = read_ledger()

    assert v1["dictionary_sha256"] == v2["dictionary_sha256"]
    assert v1["source_sha256"] == v2["source_sha256"]
    assert sha256(ROOT / "docs/dict-conjugated.json.gz") == v2["dictionary_sha256"]
    assert sha256(ROOT / "vlb/source/emerson_vlb.txt") == v2["source_sha256"]

    prior_selected = [*v1["selected"], *v2["selected"]]
    excluded_heads = {
        norm(value)
        for registration in (v1, v2)
        for value in registration.get("holdout_headwords", [])
    }
    excluded_heads.update(norm(case["headword"]) for case in prior_selected)
    excluded_pages = {
        page_id
        for registration in (v1, v2)
        for page_id in registration.get("holdout_page_ids", [])
    }
    excluded_pages.update(case["page_id"] for case in prior_selected)
    excluded_pages.update(LEGACY_DEVELOPMENT_PAGES)
    excluded_sources = {
        source_id
        for registration in (v1, v2)
        for source_id in registration.get("holdout_source_ids", [])
    }
    excluded_citations = set()

    ledger_heads = set()
    ledger_pages = set()
    ledger_sources = set()
    for event in ledger_events:
        citation = event["citation"]
        page = event["page"]
        ledger_heads.add(norm(citation["headword"]))
        ledger_pages.add(page["page_id"])
        excluded_citations.add(citation["citation_id"])
        ledger_sources.update(span["source_id"] for span in event.get("selected_spans", []))
    excluded_heads.update(ledger_heads)
    excluded_pages.update(ledger_pages)
    excluded_sources.update(ledger_sources)

    # A split source record makes every page carrying that record ineligible,
    # even if only one of its page fragments appeared in a prior review.
    source_exclusion_pages = {
        page["id"]
        for page in pages
        if any(fragment["id"] in excluded_sources for fragment in page["fragments"])
    }
    excluded_pages.update(source_exclusion_pages)

    pool = []
    for page in pages:
        if page["id"] in excluded_pages:
            continue
        for citation in page["citations"]:
            normalized_headword = norm(citation["headword"])
            if normalized_headword in excluded_heads or citation["id"] in excluded_citations:
                continue
            identity = citation["id"] + "|" + page["id"]
            order = hashlib.sha256((SEED + "|" + identity).encode()).hexdigest()
            pool.append((order, page, citation, normalized_headword))

    selected = []
    material = []
    seen_heads = set()
    seen_pages = set()
    for order, page, citation, normalized_headword in sorted(pool, key=lambda row: row[0]):
        if normalized_headword in seen_heads or page["id"] in seen_pages:
            continue
        seen_heads.add(normalized_headword)
        seen_pages.add(page["id"])
        case = {
            "adapted": citation.get("adapted", False),
            "case_id": "v3-" + order[:12],
            "citation_id": citation["id"],
            "entry_index": citation["entry_index"],
            "headword": citation["headword"],
            "homonym": citation.get("homonym", ""),
            "normalized_headword": normalized_headword,
            "page_id": page["id"],
            "selection_order": len(selected) + 1,
            "split": "test",
            "volume": page["volume"],
        }
        selected.append(case)
        material.append(
            {
                **case,
                "citation": {
                    key: value
                    for key, value in citation.items()
                    if key != "associations"
                },
                "fragments": [
                    {
                        key: value
                        for key, value in fragment.items()
                        if key not in ("associations", "ocr")
                    }
                    for fragment in page["fragments"]
                ],
            }
        )
        if len(selected) == COUNT:
            break
    assert len(selected) == COUNT, len(selected)

    new_sources = {
        fragment["id"]
        for page_id in seen_pages
        for fragment in page_map[page_id]["fragments"]
    }
    holdout_heads = excluded_heads | seen_heads
    holdout_pages = excluded_pages | seen_pages
    holdout_sources = excluded_sources | new_sources
    unique_prior_cases = {
        (case["citation_id"], case["page_id"])
        for case in prior_selected
    }
    inputs = {
        "correction_ledger": {
            "event_ids": list(CORRECTION_EVENT_IDS),
            "events": len(ledger_events),
            "path": "vlb/corrections/ledger.jsonl" if ledger_sha256 else None,
            "sha256": ledger_sha256,
            "unique_corrections": len({event["correction_id"] for event in ledger_events}),
        },
        "manifest_sha256": sha256(MANIFEST_PATH),
        "selector_sha256": sha256(Path(__file__)),
        "v1_preregistration_sha256": sha256(V1_PATH),
        "v2_preregistration_sha256": sha256(V2_PATH),
    }
    registration = {
        "correction_decision_count": len(ledger_events),
        "dictionary_sha256": v2["dictionary_sha256"],
        "holdout_headwords": sorted(holdout_heads),
        "holdout_page_ids": sorted(holdout_pages),
        "holdout_source_ids": sorted(holdout_sources),
        "human_verified": False,
        "inputs": inputs,
        "labels_read": False,
        "model_outputs_read": False,
        "new_test_count": COUNT,
        "population_limit": (
            "Conditional sample after prior registrations, development pages, and correction decisions; "
            "not an unbiased corpus-wide accuracy sample."
        ),
        "preselection_exclusion_counts": {
            "citation_ids": len(excluded_citations),
            "normalized_headwords": len(excluded_heads),
            "page_ids": len(excluded_pages),
            "source_ids": len(excluded_sources),
        },
        "prior_selected_case_count": len(unique_prior_cases),
        "purpose": (
            "V3 metadata-only blind registration; all V1/V2 cases and correction-ledger decisions "
            "remain development evidence and are excluded."
        ),
        "schema_version": 1,
        "seed": SEED,
        "selected": selected,
        "selection_basis": (
            "Fixed SHA256 ordering over citation/page identity after excluding every V1/V2 registered "
            "headword, page, and source continuation plus correction-ledger decisions; accept one case "
            "per printed page and normalized headword until 24. No mining output or labels are read."
        ),
        "source_sha256": v2["source_sha256"],
    }
    review_packet = {
        "cases": material,
        "dictionary_sha256": v2["dictionary_sha256"],
        "labels_included": False,
        "model_outputs_included": False,
        "rankings_included": False,
        "review_instructions": (
            "Review the unchanged dictionary occurrence against only the supplied cited-page fragments. "
            "Record clear, ambiguous, or not-found independently; do not infer correctness from selection order."
        ),
        "schema_version": 1,
        "seed": SEED,
        "source_sha256": v2["source_sha256"],
    }
    return registration, review_packet


def main() -> None:
    registration, review_packet = build()
    write(DEST / "preregistered_sample.json", registration)
    write(DEST / "review_material.json", review_packet)
    print(
        json.dumps(
            [
                {key: case[key] for key in ("case_id", "headword", "page_id", "citation_id")}
                for case in registration["selected"]
            ],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
