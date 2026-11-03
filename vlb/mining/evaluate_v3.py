#!/usr/bin/env python3
"""Evaluate frozen V3 predictions after sealed blind labels are released."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_OUTPUT = HERE / "output-v3"
DEFAULT_BENCHMARK = HERE / "benchmark-v3"
sys.path.insert(0, str(HERE.parent))

from mining.pipeline import Corpus, evaluate, existing_ranking  # noqa: E402


def read_json(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freezes(output: Path, benchmark: Path) -> dict:
    model = read_json(output / "model-freeze.json")
    candidates = output / "candidates.json.gz"
    expected = model["output_sha256"]["candidates.json.gz"]
    if sha256(candidates) != expected:
        raise ValueError("Frozen V3 candidate output hash changed")
    for relative, digest in model["algorithm_sha256"].items():
        if sha256(ROOT / relative) != digest:
            raise ValueError(f"Frozen V3 algorithm input changed: {relative}")
    annotation = read_json(benchmark / "annotation-freeze.json")
    labels = benchmark / Path(annotation["labels_path"]).name
    packet = benchmark / Path(annotation["packet_path"]).name
    if sha256(labels) != annotation["labels_sha256"]:
        raise ValueError("Frozen V3 labels changed")
    if sha256(packet) != annotation["packet_sha256"]:
        raise ValueError("Frozen V3 review packet changed")
    return {
        "model_freeze_sha256": sha256(output / "model-freeze.json"),
        "prediction_sha256": expected,
        "annotation_freeze_sha256": sha256(benchmark / "annotation-freeze.json"),
        "packet_sha256": annotation["packet_sha256"],
        "labels_sha256": annotation["labels_sha256"],
        "labels_path": labels,
        "packet_path": packet,
    }


def join_labels(labels_path: Path, packet_path: Path) -> dict:
    labels = read_json(labels_path)
    packet = read_json(packet_path)
    cases = {row["case_id"]: row for row in packet["cases"]}
    decisions = labels.get("labels")
    if not isinstance(decisions, list) or set(cases) != {
        row.get("case_id") for row in decisions
    }:
        raise ValueError("Blind labels and review packet contain different case IDs")
    joined = []
    for decision in decisions:
        case = cases[decision["case_id"]]
        targets = decision.get("targets") or []
        joined.append(
            {
                "case_id": case["case_id"],
                "citation_id": case["citation_id"],
                "page_id": case["page_id"],
                "headword": case["headword"],
                "status": decision["status"],
                "source_ids": sorted({row["source_id"] for row in targets}),
                "targets": targets,
            }
        )
    return {"cases": joined}


def automatic_target(prediction: dict, abstain_prefix: bool) -> bool:
    if prediction["status"] != "suggested" or not prediction["candidates"]:
        return False
    best = prediction["candidates"][0]
    span = best.get("attested_span")
    ocr = best.get("ocr_target") or {}
    independent = bool(best.get("quoted_surface_evidence")) or best.get(
        "portuguese_context_score", 0
    ) > 0
    if abstain_prefix and (best.get("query_surface") or {}).get("kind") == "surface_prefix_hypothesis":
        return False
    return bool(
        span
        and ocr.get("status") == "form_token_match"
        and ocr.get("line_ids")
        and independent
        and not best.get("page_boundary_uncertain")
        and not span.get("common_portuguese_or_grammar_token")
    )


def policy_result(joined, predictions, ranker_rows, abstain_prefix):
    rows = []
    for case in joined["cases"]:
        prediction = predictions[(case["citation_id"], case["page_id"])]
        ranker = ranker_rows[case["case_id"]]
        targeted = automatic_target(prediction, abstain_prefix)
        best = prediction["candidates"][0] if prediction["candidates"] else None
        rows.append(
            {
                "case_id": case["case_id"],
                "headword": case["headword"],
                "label_status": case["status"],
                "automatic_target": targeted,
                "query_kind": (best.get("query_surface") or {}).get("kind") if best else None,
                "correct_paragraph": ranker["top1_correct"] if targeted and case["status"] == "clear" else None,
                "exact_span": ranker["top1_exact_attested_span"] if targeted and case["status"] == "clear" else None,
                "narrow_ocr_lines": bool(targeted and best and (best.get("ocr_target") or {}).get("line_ids")),
            }
        )
    clear = [row for row in rows if row["label_status"] == "clear"]
    uncertain = [row for row in rows if row["label_status"] != "clear"]
    targets = [row for row in rows if row["automatic_target"]]
    clear_targets = [row for row in clear if row["automatic_target"]]
    counts = {
        "targets": len(targets),
        "clear_targets": len(clear_targets),
        "ambiguous_or_not_found_targets": sum(row["automatic_target"] for row in uncertain),
        "correct_paragraph_clear_targets": sum(bool(row["correct_paragraph"]) for row in clear_targets),
        "exact_span_clear_targets": sum(bool(row["exact_span"]) for row in clear_targets),
        "narrow_ocr_line_targets": sum(row["narrow_ocr_lines"] for row in targets),
        "clear_abstentions": sum(not row["automatic_target"] for row in clear),
        "ambiguous_or_not_found_abstentions": sum(not row["automatic_target"] for row in uncertain),
    }

    def ratio(a, b):
        return round(a / b, 6) if b else None

    rates = {
        "clear_case_coverage": ratio(counts["clear_targets"], len(clear)),
        "paragraph_precision_all_targets": ratio(counts["correct_paragraph_clear_targets"], counts["targets"]),
        "exact_span_precision_all_targets": ratio(counts["exact_span_clear_targets"], counts["targets"]),
        "ambiguity_abstention_rate": ratio(counts["ambiguous_or_not_found_abstentions"], len(uncertain)),
    }
    return {"counts": counts, "rates": rates, "cases": rows}


def render_report(result: dict) -> str:
    rank = result["ranker"]["counts"]
    blind = result["navigation_policy"]["blind_release_policy"]
    revised = result["navigation_policy"]["post_release_safety_gate"]

    def pct(value):
        return f"{value * 100:.1f}%"

    lines = [
        "# VLB alignment V3 evaluation",
        "",
        "V3 predictions and code were frozen before the independent review packet was annotated. The 24-case review is assistant-produced and not human-verified, so these are bounded sample results rather than corpus-wide accuracy estimates.",
        "",
        "## Frozen ranker on the fresh blind sample",
        "",
        f"- Clear cases: {rank['clear_cases']} of {rank['all_cases']}; ambiguous: {rank['ambiguous_cases']}; not found: {rank['not_found_cases']}.",
        f"- Correct first paragraph: {rank['top1_correct']}/{rank['clear_cases']} ({pct(rank['top1_correct']/rank['clear_cases'])}).",
        f"- Correct paragraph in the first three: {rank['top3_contains_gold']}/{rank['clear_cases']} ({pct(rank['top3_contains_gold']/rank['clear_cases'])}).",
        f"- Exact first span: {rank['top1_exact_attested_span']}/{rank['clear_cases']} ({pct(rank['top1_exact_attested_span']/rank['clear_cases'])}).",
        f"- Exact span among offered alternatives: {rank['offered_exact_attested_span']}/{rank['clear_cases']} ({pct(rank['offered_exact_attested_span']/rank['clear_cases'])}).",
        f"- Previous reader ranking, for comparison only: top paragraph {rank['existing_top1_correct']}/{rank['clear_cases']}; top three {rank['existing_top3_contains_gold']}/{rank['clear_cases']}.",
        "",
        "## Automatic navigation policy",
        "",
        f"The policy present when labels were released targeted {blind['counts']['targets']} cases. It chose a correct clear-case paragraph in {blind['counts']['correct_paragraph_clear_targets']}, but also targeted {blind['counts']['ambiguous_or_not_found_targets']} ambiguous case. That false-positive signal is retained here.",
        "",
        "After release, that failure became a development regression. The browser policy now abstains from automatically asserting inferred prefix hypotheses; candidates remain available for manual review. Reuse of this sample for the gate is not a new held-out result:",
        "",
        f"- Automatic targets: {revised['counts']['targets']}.",
        f"- Clear-case coverage: {revised['counts']['clear_targets']}/{rank['clear_cases']} ({pct(revised['rates']['clear_case_coverage'])}).",
        f"- Paragraph precision across all automatic targets: {revised['counts']['correct_paragraph_clear_targets']}/{revised['counts']['targets']} ({pct(revised['rates']['paragraph_precision_all_targets'])}).",
        f"- Exact-span precision across all automatic targets: {revised['counts']['exact_span_clear_targets']}/{revised['counts']['targets']} ({pct(revised['rates']['exact_span_precision_all_targets'])}).",
        f"- Ambiguous/not-found abstention: {revised['counts']['ambiguous_or_not_found_abstentions']}/{rank['ambiguous_cases'] + rank['not_found_cases']} ({pct(revised['rates']['ambiguity_abstention_rate'])}).",
        f"- Narrowed OCR line available: {revised['counts']['narrow_ocr_line_targets']}/{revised['counts']['targets']}.",
        "",
        "OCR line availability is not exact scan-glyph accuracy. The boxes cover OCR line regions and are not human-verified glyph boxes.",
        "",
        "## Integrity",
        "",
        f"- Prediction SHA-256: `{result['provenance']['prediction_sha256']}`",
        f"- Blind packet SHA-256: `{result['provenance']['packet_sha256']}`",
        f"- Labels SHA-256: `{result['provenance']['labels_sha256']}`",
        "",
        "Reproduce with `python3 vlb/mining/benchmark-v3/validate_annotations.py` and `python3 vlb/mining/evaluate_v3.py`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    args = parser.parse_args()
    provenance = verify_freezes(args.output, args.benchmark)
    joined = join_labels(provenance["labels_path"], provenance["packet_path"])
    frozen = read_json(args.output / "candidates.json.gz")
    predictions = {(row["citation_id"], row["page_id"]): row for row in frozen["records"]}
    corpus = Corpus(ROOT)
    baseline = {(citation["id"], page["id"]): existing_ranking(citation) for page in corpus.pages for citation in page["citations"]}
    ranker = evaluate(joined, predictions, baseline)
    ranker_rows = {row["case_id"]: row for row in ranker["cases"]}
    result = {
        "schema_version": 1,
        "evaluation_status": "fresh blind evaluation of frozen V3 predictions",
        "reviewer_type": "assistant",
        "human_verified": False,
        "corpus_wide_accuracy": False,
        "ranker": ranker,
        "navigation_policy": {
            "blind_release_policy": policy_result(joined, predictions, ranker_rows, False),
            "post_release_safety_gate": policy_result(joined, predictions, ranker_rows, True),
            "post_release_result_is_held_out": False,
            "policy_version": "vlb-navigation-policy-v3.1",
        },
        "not_measured": ["human-verified lexical equivalence", "exact scan glyph-box accuracy", "corpus-wide accuracy"],
        "provenance": {key: value for key, value in provenance.items() if not key.endswith("_path")},
    }
    (args.output / "test_labels-evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "REPORT.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps({"ranker": ranker["counts"], "navigation": result["navigation_policy"]["post_release_safety_gate"]["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
