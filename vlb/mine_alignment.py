#!/usr/bin/env python3
"""Precompute orthography-aware VLB candidates from pinned local snapshots.

No network, source rewriting, morphology-engine invocation, or website mutation.
Use --help for a full run, a development subset, or evaluation of frozen outputs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import time

from mining.orthography import compile_model, prior_model, train
from mining.pipeline import (CONFIG, Corpus, digest, evaluate, existing_ranking,
                             rank_citation, read_json, sha, write_json)
from mining.seeds import extract_seeds
from mining.form_index import build_form_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "mining/output-v2")
    parser.add_argument("--benchmark", type=Path, default=Path(__file__).resolve().parent / "mining/benchmark-v2/preregistered_sample.json")
    parser.add_argument("--labels", type=Path, help="Optional independent labels. Never used by the ranker or trainer.")
    parser.add_argument("--subset", choices=["dev", "test", "benchmark", "all"], default="all")
    parser.add_argument("--model", choices=["uniform", "prior", "learned"], default="prior")
    parser.add_argument("--evaluate-only", action="store_true", help="Evaluate already-frozen candidates; requires --labels.")
    parser.add_argument("--freeze", action="store_true", help="Record code/config/output hashes after a full run without labels. The caller must separately enforce blind label release.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    corpus = Corpus(root)
    baseline = {(c["id"], p["id"]): existing_ranking(c) for p in corpus.pages for c in p["citations"]}
    output = args.output
    if output.resolve() == (root / "vlb/mining/output").resolve():
        parser.error("vlb/mining/output is the frozen V1 experiment; choose a separate output directory")
    if args.freeze and (args.subset != "all" or args.labels or args.evaluate_only):
        parser.error("--freeze requires a full run without --labels or --evaluate-only")
    if args.evaluate_only:
        if not args.labels:
            parser.error("--evaluate-only requires --labels")
        saved = read_json(output / "candidates.json.gz")
        predictions = {(r["citation_id"], r["page_id"]): r for r in saved["records"]}
        result = evaluate(read_json(args.labels), predictions, baseline)
        result["prediction_sha256"] = sha(output / "candidates.json.gz")
        result["labels_sha256"] = sha(args.labels)
        write_json(output / (args.labels.stem + "-evaluation.json"), result, pretty=True)
        print(result["counts"], flush=True)
        return
    benchmark = read_json(args.benchmark)
    exclusions = benchmark
    seeds = extract_seeds(corpus.pages, benchmark["holdout_headwords"], benchmark["holdout_page_ids"], benchmark["holdout_source_ids"])
    learned = train(seeds, exclusions)
    model_data = learned if args.model == "learned" else prior_model()
    if args.model == "uniform":
        model_data = {"schema_version": 1, "direction": "Navarro surface -> Emerson surface",
                      "method": "uniform character edit costs; same shortlist, context and surface hypotheses as orthographic models",
                      "weights_are_probabilities": False, "rules": [],
                      "default_costs": {"edit": 1.0, "stress_mark_difference": 1.0, "nasal_mark_difference": 1.0}}
    model = compile_model(model_data)
    write_json(output / "seeds.json.gz", seeds)
    write_json(output / "orthography-model.json", model_data, pretty=True)
    selected = None
    if args.subset != "all":
        selected = {(row["citation_id"], row["page_id"]) for row in benchmark["selected"]
                    if args.subset == "benchmark" or row.get("split") == args.subset}
    records = []
    start = time.monotonic()
    for page in corpus.pages:
        before = len(records)
        for citation in page["citations"]:
            if selected is not None and (citation["id"], page["id"]) not in selected:
                continue
            records.append(rank_citation(corpus, page, citation, model))
        if len(records) > before and (args.subset != "all" or len(records) // 500 != before // 500):
            print(f"{page['id']}: {len(records)} memberships, {time.monotonic()-start:.1f}s", flush=True)
    assert len({(r["citation_id"], r["page_id"]) for r in records}) == len(records)
    expected = corpus.manifest["counts"]["page_citation_memberships"] if selected is None else len(selected)
    assert len(records) == expected, (len(records), expected)
    summary = {"schema_version": 1, "config": CONFIG, "provenance": corpus.provenance,
               "model_kind": args.model, "model_sha256": digest(model_data),
               "seed_sha256": digest(seeds), "benchmark_sha256": sha(args.benchmark),
               "counts": {"page_memberships": len(records), "silver_training_pairs": len(seeds),
                          "status": dict(Counter(r["status"] for r in records)),
                          "top_candidate_ocr": dict(Counter(r["candidates"][0]["ocr_target"]["status"] for r in records if r["candidates"]))},
               "source_modified": False, "production_targets_modified": False,
               "review_status": "all newly mined associations are unreviewed",
               "span_alternative_scope": "Up to three additional exact source spans per candidate paragraph, with independent evidence; never editorial verification",
               "scores_are_probabilities": False,
               "unresolved_citations": read_json(root / "vlb/data/unresolved-citations.json")}
    write_json(output / "candidates.json.gz", {**summary, "records": records})
    form_index = build_form_index(records, corpus.provenance)
    write_json(output / "headword-form-index.json.gz", form_index)
    summary["candidates_sha256"] = sha(output / "candidates.json.gz")
    summary["headword_form_index_sha256"] = sha(output / "headword-form-index.json.gz")
    summary["headword_form_index_entries"] = form_index["entry_count"]
    write_json(output / "summary.json", summary, pretty=True)
    if args.freeze:
        paths = ["vlb/mine_alignment.py", "vlb/mining/pipeline.py", "vlb/mining/quotation.py",
                 "vlb/mining/orthography.py", "vlb/mining/seeds.py", "vlb/mining/form_index.py"]
        write_json(output / "model-freeze.json", {
            "schema_version": 1, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "algorithm_sha256": {path: sha(root / path) for path in paths},
            "config": CONFIG, "config_sha256": digest(CONFIG),
            "benchmark_sha256": sha(args.benchmark), "model_kind": args.model,
            "output_sha256": {name: sha(output / name) for name in
                              ["candidates.json.gz", "headword-form-index.json.gz",
                               "orthography-model.json", "seeds.json.gz", "summary.json"]},
            "labels_supplied_to_run": False,
            "protocol": "Immutable prediction/code snapshot. Independent label withholding and release are recorded separately by the reviewer.",
        }, pretty=True)
    if args.labels:
        result = evaluate(read_json(args.labels), {(r["citation_id"], r["page_id"]): r for r in records}, baseline)
        result["prediction_sha256"] = summary["candidates_sha256"]
        result["labels_sha256"] = sha(args.labels)
        write_json(output / (args.labels.stem + "-evaluation.json"), result, pretty=True)
        print(result["counts"], flush=True)
    print(summary["counts"], flush=True)


if __name__ == "__main__":
    main()
