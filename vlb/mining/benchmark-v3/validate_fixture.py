#!/usr/bin/env python3
"""Validate the deterministic, metadata-only V3 preregistration packet."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path: Path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_selector():
    spec = importlib.util.spec_from_file_location("vlb_benchmark_v3_selector", HERE / "select_sample.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> None:
    selector = load_selector()
    registration = read(HERE / "preregistered_sample.json")
    packet = read(HERE / "review_material.json")
    rebuilt_registration, rebuilt_packet = selector.build()
    assert registration == rebuilt_registration
    assert packet == rebuilt_packet

    assert registration["labels_read"] is False
    assert registration["model_outputs_read"] is False
    assert packet["labels_included"] is False
    assert packet["model_outputs_included"] is False
    assert packet["rankings_included"] is False
    assert len(registration["selected"]) == selector.COUNT == 24
    assert len(packet["cases"]) == selector.COUNT

    cases = registration["selected"]
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert len({case["page_id"] for case in cases}) == len(cases)
    assert len({case["normalized_headword"] for case in cases}) == len(cases)
    assert [case["selection_order"] for case in cases] == list(range(1, 25))
    assert all(case["split"] == "test" and case["case_id"].startswith("v3-") for case in cases)

    v1 = read(ROOT / "vlb/mining/benchmark/preregistered_sample.json")
    v2 = read(ROOT / "vlb/mining/benchmark-v2/preregistered_sample.json")
    prior_cases = [*v1["selected"], *v2["selected"]]
    prior_pages = {case["page_id"] for case in prior_cases}
    prior_heads = {selector.norm(case["headword"]) for case in prior_cases}
    prior_sources = set(v1["holdout_source_ids"]) | set(v2["holdout_source_ids"])
    assert not ({case["page_id"] for case in cases} & prior_pages)
    assert not ({case["normalized_headword"] for case in cases} & prior_heads)

    ledger_events, ledger_sha256 = selector.read_ledger()
    ledger_pages = {event["page"]["page_id"] for event in ledger_events}
    ledger_heads = {selector.norm(event["citation"]["headword"]) for event in ledger_events}
    ledger_citations = {event["citation"]["citation_id"] for event in ledger_events}
    ledger_sources = {
        span["source_id"]
        for event in ledger_events
        for span in event.get("selected_spans", [])
    }
    assert not ({case["page_id"] for case in cases} & ledger_pages)
    assert not ({case["normalized_headword"] for case in cases} & ledger_heads)
    assert not ({case["citation_id"] for case in cases} & ledger_citations)
    assert registration["inputs"]["correction_ledger"]["sha256"] == ledger_sha256
    assert registration["inputs"]["correction_ledger"]["event_ids"] == list(selector.CORRECTION_EVENT_IDS)

    source = (ROOT / "vlb/source/emerson_vlb.txt").read_text()
    dictionary = json.loads(gzip.decompress((ROOT / "docs/dict-conjugated.json.gz").read_bytes()))
    packet_by_id = {case["case_id"]: case for case in packet["cases"]}
    forbidden_case_keys = {"associations", "ocr", "candidates", "prediction", "ranking", "score"}
    selected_sources = set()
    for case in cases:
        material = packet_by_id[case["case_id"]]
        for key in case:
            assert material[key] == case[key], (case["case_id"], key)
        assert dictionary[case["entry_index"]]["f"] == case["headword"]
        page = read(ROOT / f"vlb/data/pages/{case['page_id']}.json.gz")
        citation = next(item for item in page["citations"] if item["id"] == case["citation_id"])
        assert material["citation"] == {
            key: value for key, value in citation.items() if key != "associations"
        }
        assert not (forbidden_case_keys & set(material["citation"]))
        expected_fragments = [
            {key: value for key, value in fragment.items() if key not in ("associations", "ocr")}
            for fragment in page["fragments"]
        ]
        assert material["fragments"] == expected_fragments
        for fragment in material["fragments"]:
            assert not (forbidden_case_keys & set(fragment))
            assert source[fragment["source_start0"]:fragment["source_end0"]] == fragment["text"]
            selected_sources.add(fragment["id"])

    assert not (selected_sources & prior_sources)
    assert not (selected_sources & ledger_sources)
    assert selected_sources <= set(registration["holdout_source_ids"])
    assert {case["page_id"] for case in cases} <= set(registration["holdout_page_ids"])
    assert {case["normalized_headword"] for case in cases} <= set(registration["holdout_headwords"])

    result = {
        "cases": len(cases),
        "correction_decisions_excluded": len(ledger_events),
        "preregistered_sample_sha256": digest(HERE / "preregistered_sample.json"),
        "review_material_sha256": digest(HERE / "review_material.json"),
        "seed": registration["seed"],
        "status": "ok",
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
