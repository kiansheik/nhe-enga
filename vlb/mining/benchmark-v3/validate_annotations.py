#!/usr/bin/env python3
"""Validate the frozen, blind V3 review annotations without mining imports."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, default=SCRIPT_DIR / "review_material.json")
    parser.add_argument("--labels", type=Path, default=SCRIPT_DIR / "test_labels.json")
    parser.add_argument("--freeze", type=Path, default=SCRIPT_DIR / "annotation-freeze.json")
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "vlb" / "source" / "emerson_vlb.txt",
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=REPO_ROOT / "docs" / "dict-conjugated.json.gz",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_packet(
    packet: dict[str, Any], source_path: Path, dictionary_path: Path
) -> str:
    require(packet.get("schema_version") == 1, "unsupported packet schema")
    require(packet.get("labels_included") is False, "packet includes labels")
    require(packet.get("model_outputs_included") is False, "packet includes model outputs")
    require(packet.get("rankings_included") is False, "packet includes rankings")
    require(packet.get("source_sha256") == sha256(source_path), "source hash mismatch")
    require(
        packet.get("dictionary_sha256") == sha256(dictionary_path),
        "dictionary hash mismatch",
    )

    # Confirm the gzip is readable as an additional pinned-input sanity check.
    with gzip.open(dictionary_path, "rb") as stream:
        require(stream.read(1) in {b"[", b"{"}, "dictionary gzip is not JSON")

    source = source_path.read_text(encoding="utf-8")
    cases = packet.get("cases")
    require(isinstance(cases, list) and len(cases) == 24, "packet must have 24 cases")
    case_ids: set[str] = set()
    selection_orders: set[int] = set()
    for case in cases:
        require(isinstance(case, dict), "packet case is not an object")
        case_id = case.get("case_id")
        require(isinstance(case_id, str) and case_id, "packet case_id is invalid")
        require(case_id not in case_ids, f"duplicate packet case_id: {case_id}")
        case_ids.add(case_id)
        order = case.get("selection_order")
        require(isinstance(order, int), f"{case_id}: invalid selection_order")
        require(order not in selection_orders, f"duplicate selection_order: {order}")
        selection_orders.add(order)
        fragments = case.get("fragments")
        require(isinstance(fragments, list) and fragments, f"{case_id}: no fragments")
        fragment_ids: set[str] = set()
        for fragment in fragments:
            source_id = fragment.get("id")
            start = fragment.get("source_start0")
            end = fragment.get("source_end0")
            text = fragment.get("text")
            require(
                isinstance(source_id, str) and source_id not in fragment_ids,
                f"{case_id}: invalid or duplicate fragment id",
            )
            fragment_ids.add(source_id)
            require(
                isinstance(start, int)
                and isinstance(end, int)
                and 0 <= start < end <= len(source),
                f"{case_id}/{source_id}: invalid fragment span",
            )
            require(
                isinstance(text, str) and source[start:end] == text,
                f"{case_id}/{source_id}: fragment text does not match pinned source",
            )
    require(selection_orders == set(range(1, 25)), "selection_order must be 1 through 24")
    return source


def validate_labels(
    labels_doc: dict[str, Any],
    packet: dict[str, Any],
    packet_path: Path,
    source: str,
) -> dict[str, int]:
    require(labels_doc.get("schema_version") == 1, "unsupported labels schema")
    require(labels_doc.get("packet_sha256") == sha256(packet_path), "labels packet hash mismatch")
    require(
        labels_doc.get("source_sha256") == packet.get("source_sha256"),
        "labels source hash mismatch",
    )
    require(
        labels_doc.get("dictionary_sha256") == packet.get("dictionary_sha256"),
        "labels dictionary hash mismatch",
    )
    require(labels_doc.get("reviewer_type") == "assistant", "invalid global reviewer_type")
    require(labels_doc.get("human_verified") is False, "invalid global human_verified")

    packet_cases = sorted(packet["cases"], key=lambda case: case["selection_order"])
    packet_ids = [case["case_id"] for case in packet_cases]
    labels = labels_doc.get("labels")
    require(isinstance(labels, list) and len(labels) == 24, "labels must contain 24 cases")
    require(
        [label.get("case_id") for label in labels] == packet_ids,
        "label case IDs or order differ from the packet",
    )

    allowed_statuses = {"clear", "ambiguous", "not_found"}
    metrics = {status: 0 for status in sorted(allowed_statuses)}
    for case, label in zip(packet_cases, labels, strict=True):
        case_id = case["case_id"]
        status = label.get("status")
        require(status in allowed_statuses, f"{case_id}: invalid status")
        metrics[status] += 1
        require(label.get("reviewer_type") == "assistant", f"{case_id}: invalid reviewer_type")
        require(label.get("human_verified") is False, f"{case_id}: invalid human_verified")
        note = label.get("evidence_note")
        require(isinstance(note, str) and note.strip(), f"{case_id}: missing evidence_note")
        targets = label.get("targets")
        require(isinstance(targets, list), f"{case_id}: targets is not an array")
        if status == "not_found":
            require(not targets, f"{case_id}: not_found must not have targets")
        else:
            require(targets, f"{case_id}: {status} must have a target")

        fragments = {fragment["id"]: fragment for fragment in case["fragments"]}
        seen_targets: set[tuple[str, int, int, str]] = set()
        for target in targets:
            require(isinstance(target, dict), f"{case_id}: target is not an object")
            source_id = target.get("source_id")
            start = target.get("form_start0")
            end = target.get("form_end0")
            text = target.get("form_text")
            require(source_id in fragments, f"{case_id}: target source_id is outside its packet")
            fragment = fragments[source_id]
            require(
                isinstance(start, int)
                and isinstance(end, int)
                and fragment["source_start0"] <= start < end <= fragment["source_end0"],
                f"{case_id}/{source_id}: target span is outside its fragment",
            )
            require(
                isinstance(text, str) and source[start:end] == text,
                f"{case_id}/{source_id}: form text does not match pinned source",
            )
            target_key = (source_id, start, end, text)
            require(target_key not in seen_targets, f"{case_id}: duplicate target")
            seen_targets.add(target_key)
    return metrics


def validate_freeze(
    freeze: dict[str, Any],
    packet_path: Path,
    labels_path: Path,
) -> None:
    require(freeze.get("schema_version") == 1, "unsupported freeze schema")
    require(freeze.get("packet_sha256") == sha256(packet_path), "freeze packet hash mismatch")
    require(freeze.get("labels_sha256") == sha256(labels_path), "freeze labels hash mismatch")
    require(freeze.get("case_count") == 24, "freeze case_count must be 24")
    require(freeze.get("reviewer_type") == "assistant", "freeze reviewer_type is invalid")
    require(freeze.get("human_verified") is False, "freeze human_verified is invalid")
    require(freeze.get("rankings_inspected") is False, "freeze must record blind ranking review")
    scope = freeze.get("reviewer_scope")
    require(isinstance(scope, str) and scope.strip(), "freeze reviewer_scope is missing")
    excluded = freeze.get("excluded_material")
    require(isinstance(excluded, list) and excluded, "freeze excluded_material is missing")
    timestamp = freeze.get("frozen_at")
    require(isinstance(timestamp, str) and timestamp.endswith("Z"), "freeze timestamp must be UTC")
    parsed = datetime.fromisoformat(timestamp.removesuffix("Z") + "+00:00")
    require(parsed.tzinfo == timezone.utc, "freeze timestamp is not UTC")


def main() -> None:
    args = parse_args()
    packet = load_json(args.packet)
    labels_doc = load_json(args.labels)
    freeze = load_json(args.freeze)
    source = validate_packet(packet, args.source, args.dictionary)
    metrics = validate_labels(labels_doc, packet, args.packet, source)
    validate_freeze(freeze, args.packet, args.labels)
    print(
        "validated 24 blind annotations: "
        + ", ".join(f"{status}={metrics[status]}" for status in sorted(metrics))
    )


if __name__ == "__main__":
    main()
