"""Strict validation and append-only import for VLB correction events.

The ledger records editorial decisions; it never rewrites the dictionary,
Emerson transcription, OCR snapshot, or frozen mining outputs.  Python's
standard library is sufficient so the same checks can run locally and in CI.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Iterable


SCHEMA_VERSION = 1
SUBMISSION_SCHEMA = "vlb-correction-submission-1"
DISPOSITIONS = {"accepted", "rejected", "ambiguous", "not_found", "unresolved"}
REVIEWER_TYPES = {"human", "assistant", "automated"}
PROPOSAL_STATUSES = {
    "suggested",
    "needs_review",
    "weak_candidates",
    "no_candidate",
    "reviewed",
    "unavailable",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "event_id",
    "correction_id",
    "revision",
    "supersedes_event_id",
    "recorded_at",
    "citation",
    "page",
    "selected_spans",
    "disposition",
    "previous_proposal",
    "review",
    "snapshots",
}
CITATION_KEYS = {
    "citation_id",
    "entry_index",
    "legacy_id",
    "headword",
    "homonym",
    "definition_sha256",
    "citation_start0",
    "citation_end0",
}
PAGE_KEYS = {"page_id", "volume", "printed_page"}
SPAN_KEYS = {"source_id", "start0", "end0", "text", "ocr_targets"}
OCR_KEYS = {"line_id", "box", "box_source", "previous_box"}
PROPOSAL_KEYS = {
    "algorithm_version",
    "output_sha256",
    "status",
    "source_id",
    "start0",
    "end0",
    "text",
}
REVIEW_KEYS = {
    "reviewer_type",
    "reviewer",
    "provenance",
    "notes",
    "approved_for_regression",
    "approved_for_training",
}
SNAPSHOT_KEYS = {
    "source_text_sha256",
    "dictionary_snapshot_sha256",
    "citation_links_sha256",
    "page_alignment_sha256",
    "ocr_layout_sha256",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EVENT_ID = re.compile(r"^vlb-correction-[0-9a-f]{20}-r[0-9]{4}$")


class LedgerError(ValueError):
    """A correction record is stale, malformed, inconsistent, or conflicting."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(path.read_text(encoding="utf-8"))


def correction_id_for(citation_id: str, page_id: str) -> str:
    suffix = hashlib.sha256(f"{citation_id}\0{page_id}".encode()).hexdigest()[:20]
    return f"vlb-correction-{suffix}"


def _require_exact_keys(value: dict, expected: set[str], where: str) -> None:
    missing = expected - set(value)
    extra = set(value) - expected
    if missing or extra:
        parts = []
        if missing:
            parts.append("missing " + ", ".join(sorted(missing)))
        if extra:
            parts.append("unknown " + ", ".join(sorted(extra)))
        raise LedgerError(f"{where}: {'; '.join(parts)}")


def _require_string(value, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise LedgerError(f"{where}: expected a non-empty string")
    return value


def _require_int(value, where: str, *, minimum: int | None = None) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or (minimum is not None and value < minimum)
    ):
        raise LedgerError(
            f"{where}: expected an integer"
            + (f" >= {minimum}" if minimum is not None else "")
        )
    return value


def _require_hash(value, where: str) -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise LedgerError(f"{where}: expected a lowercase SHA-256")
    return value


def _require_timestamp(value, where: str) -> None:
    _require_string(value, where)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LedgerError(f"{where}: invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise LedgerError(f"{where}: timestamp must include a timezone")


def _require_box(value, where: str) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(
            isinstance(number, bool)
            or not isinstance(number, (int, float))
            or not math.isfinite(number)
            for number in value
        )
    ):
        raise LedgerError(f"{where}: box must contain four finite numbers")
    box = [float(number) for number in value]
    if (
        any(number < 0 or number > 1 for number in box)
        or box[0] >= box[2]
        or box[1] >= box[3]
    ):
        raise LedgerError(
            f"{where}: box must be normalized with positive width and height"
        )
    return box


class CorrectionContext:
    """Pinned source indexes used to reject stale or fabricated corrections."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        source = self.root / "vlb/source"
        data = self.root / "vlb/data"
        self.text = (source / "emerson_vlb.txt").read_text(encoding="utf-8")
        source_meta = _read_json(source / "source_metadata.json")
        source_hash = hashlib.sha256(self.text.encode()).hexdigest()
        if source_hash != source_meta["text_sha256"]:
            raise LedgerError(
                "Pinned Emerson source hash does not match source_metadata.json"
            )
        citations = _read_json(source / "citation_links.json.gz")
        self.citations = {row["citation_id"]: row for row in citations}
        if len(self.citations) != len(citations):
            raise LedgerError("Pinned citation IDs are not unique")
        dictionary_hashes = {row["dictionary_snapshot_sha256"] for row in citations}
        if len(dictionary_hashes) != 1:
            raise LedgerError("Pinned citations do not share one dictionary snapshot")
        self.manifest = _read_json(data / "manifest.json")
        self.page_meta = {row["id"]: row for row in self.manifest["pages"]}
        self._pages: dict[str, dict] = {}
        self.snapshots = {
            "source_text_sha256": source_hash,
            "dictionary_snapshot_sha256": dictionary_hashes.pop(),
            "citation_links_sha256": _sha(source / "citation_links.json.gz"),
            "page_alignment_sha256": _sha(source / "page_alignment.json.gz"),
            "ocr_layout_sha256": _sha(source / "ocr_layout.json.gz"),
        }
        self.algorithm_outputs = {}
        for summary_path in sorted(
            (self.root / "vlb/mining").glob("output*/summary.json")
        ):
            summary = _read_json(summary_path)
            version = summary.get("config", {}).get("version")
            candidates_path = summary_path.parent / "candidates.json.gz"
            if version and candidates_path.exists():
                digest = _sha(candidates_path)
                previous = self.algorithm_outputs.setdefault(version, digest)
                if previous != digest:
                    raise LedgerError(
                        f"Conflicting frozen outputs for algorithm version {version}"
                    )

    def page(self, page_id: str) -> dict:
        if page_id not in self.page_meta:
            raise LedgerError(f"Unknown VLB page: {page_id}")
        if page_id not in self._pages:
            self._pages[page_id] = _read_json(
                self.root / "vlb/data" / self.page_meta[page_id]["data_file"]
            )
        return self._pages[page_id]


def _citation_projection(
    context: CorrectionContext, citation_id: str, page_id: str
) -> tuple[dict, dict]:
    citation = context.citations.get(citation_id)
    if not citation:
        raise LedgerError(f"Unknown citation occurrence: {citation_id}")
    page = context.page(page_id)
    projected = next(
        (row for row in page.get("citations", []) if row["id"] == citation_id), None
    )
    if not projected:
        raise LedgerError(f"Citation {citation_id} is not a member of {page_id}")
    expected_page = (page["volume"], page["page"])
    original_memberships = {
        (row.get("volume"), row.get("printed_page"))
        for row in citation.get("page_links", [])
        if row.get("link_status") == "page_range_linked"
    }
    if expected_page not in original_memberships:
        raise LedgerError(
            f"Citation {citation_id} lacks original page membership for {page_id}"
        )
    return citation, page


def _validate_source_span(
    context: CorrectionContext, page: dict, span: dict, where: str
) -> dict:
    _require_exact_keys(span, SPAN_KEYS, where)
    source_id = _require_string(span["source_id"], f"{where}.source_id")
    start = _require_int(span["start0"], f"{where}.start0", minimum=0)
    end = _require_int(span["end0"], f"{where}.end0", minimum=1)
    text = _require_string(span["text"], f"{where}.text")
    if start >= end or end > len(context.text) or context.text[start:end] != text:
        raise LedgerError(
            f"{where}: text does not equal the pinned source at [{start}, {end})"
        )
    fragment = next(
        (row for row in page.get("fragments", []) if row["id"] == source_id), None
    )
    if not fragment:
        raise LedgerError(f"{where}: source {source_id} is not present on {page['id']}")
    if start < fragment["source_start0"] or end > fragment["source_end0"]:
        raise LedgerError(
            f"{where}: span is outside this source's fragment on {page['id']}"
        )
    targets = span["ocr_targets"]
    if not isinstance(targets, list):
        raise LedgerError(f"{where}.ocr_targets: expected an array")
    line_map = {row["id"]: row for row in page.get("ocr_lines", [])}
    fragment_lines = set(fragment.get("ocr", {}).get("line_ids", []))
    seen_lines = set()
    for index, target in enumerate(targets):
        target_where = f"{where}.ocr_targets[{index}]"
        if not isinstance(target, dict):
            raise LedgerError(f"{target_where}: expected an object")
        _require_exact_keys(target, OCR_KEYS, target_where)
        line_id = _require_string(target["line_id"], f"{target_where}.line_id")
        if line_id in seen_lines:
            raise LedgerError(f"{target_where}: duplicate OCR line {line_id}")
        seen_lines.add(line_id)
        line = line_map.get(line_id)
        if not line or line_id not in fragment_lines:
            raise LedgerError(
                f"{target_where}: OCR line is not aligned to this source fragment"
            )
        box = _require_box(target["box"], f"{target_where}.box")
        source_kind = target["box_source"]
        if source_kind == "pinned_ocr":
            if target["previous_box"] is not None:
                raise LedgerError(
                    f"{target_where}: pinned OCR target must set previous_box to null"
                )
            if box != [float(number) for number in line["box"]]:
                raise LedgerError(
                    f"{target_where}: pinned OCR box does not match current data"
                )
        elif source_kind == "reviewer_correction":
            previous = _require_box(
                target["previous_box"], f"{target_where}.previous_box"
            )
            if previous != [float(number) for number in line["box"]]:
                raise LedgerError(
                    f"{target_where}: corrected box does not identify the current pinned box"
                )
        else:
            raise LedgerError(
                f"{target_where}.box_source: expected pinned_ocr or reviewer_correction"
            )
    return fragment


def _validate_proposal(
    context: CorrectionContext, page: dict, proposal, where: str
) -> None:
    if proposal is None:
        return
    if not isinstance(proposal, dict):
        raise LedgerError(f"{where}: expected an object or null")
    _require_exact_keys(proposal, PROPOSAL_KEYS, where)
    _require_string(proposal["algorithm_version"], f"{where}.algorithm_version")
    output_hash = _require_hash(proposal["output_sha256"], f"{where}.output_sha256")
    expected_output = context.algorithm_outputs.get(proposal["algorithm_version"])
    if expected_output is None:
        raise LedgerError(
            f"{where}.algorithm_version: no pinned output has this version"
        )
    if output_hash != expected_output:
        raise LedgerError(f"{where}.output_sha256: stale algorithm output hash")
    if proposal["status"] not in PROPOSAL_STATUSES:
        raise LedgerError(f"{where}.status: unsupported proposal status")
    if proposal["status"] == "no_candidate":
        if any(
            proposal[key] is not None for key in ("source_id", "start0", "end0", "text")
        ):
            raise LedgerError(
                f"{where}: no_candidate proposal cannot name a source span"
            )
        return
    compact_span = {
        "source_id": proposal["source_id"],
        "start0": proposal["start0"],
        "end0": proposal["end0"],
        "text": proposal["text"],
        "ocr_targets": [],
    }
    _validate_source_span(context, page, compact_span, where)


def validate_event(
    context: CorrectionContext, event: dict, where: str = "event"
) -> None:
    if not isinstance(event, dict):
        raise LedgerError(f"{where}: expected an object")
    _require_exact_keys(event, TOP_LEVEL_KEYS, where)
    if event["schema_version"] != SCHEMA_VERSION:
        raise LedgerError(f"{where}.schema_version: expected {SCHEMA_VERSION}")
    revision = _require_int(event["revision"], f"{where}.revision", minimum=1)
    citation_fields = event["citation"]
    page_fields = event["page"]
    if not isinstance(citation_fields, dict) or not isinstance(page_fields, dict):
        raise LedgerError(f"{where}: citation and page must be objects")
    _require_exact_keys(citation_fields, CITATION_KEYS, f"{where}.citation")
    _require_exact_keys(page_fields, PAGE_KEYS, f"{where}.page")
    citation_id = _require_string(
        citation_fields["citation_id"], f"{where}.citation.citation_id"
    )
    page_id = _require_string(page_fields["page_id"], f"{where}.page.page_id")
    correction_id = _require_string(event["correction_id"], f"{where}.correction_id")
    expected_correction_id = correction_id_for(citation_id, page_id)
    if correction_id != expected_correction_id:
        raise LedgerError(f"{where}.correction_id: expected {expected_correction_id}")
    event_id = _require_string(event["event_id"], f"{where}.event_id")
    expected_event_id = f"{correction_id}-r{revision:04d}"
    if not EVENT_ID.fullmatch(event_id) or event_id != expected_event_id:
        raise LedgerError(f"{where}.event_id: expected {expected_event_id}")
    if revision == 1 and event["supersedes_event_id"] is not None:
        raise LedgerError(f"{where}.supersedes_event_id: first revision must be null")
    if revision > 1:
        _require_string(event["supersedes_event_id"], f"{where}.supersedes_event_id")
    _require_timestamp(event["recorded_at"], f"{where}.recorded_at")

    citation, page = _citation_projection(context, citation_id, page_id)
    expected_citation = {
        "citation_id": citation_id,
        "entry_index": citation["entry_index"],
        "legacy_id": citation.get("legacy_id"),
        "headword": citation["headword"],
        "homonym": citation.get("homonym", ""),
        "definition_sha256": citation["definition_sha256"],
        "citation_start0": citation["citation_start"],
        "citation_end0": citation["citation_end_exclusive"],
    }
    if citation_fields != expected_citation:
        raise LedgerError(f"{where}.citation: identity or offsets are stale")
    expected_page = {
        "page_id": page_id,
        "volume": page["volume"],
        "printed_page": page["page"],
    }
    if page_fields != expected_page:
        raise LedgerError(f"{where}.page: page identity is stale")

    snapshots = event["snapshots"]
    if not isinstance(snapshots, dict):
        raise LedgerError(f"{where}.snapshots: expected an object")
    _require_exact_keys(snapshots, SNAPSHOT_KEYS, f"{where}.snapshots")
    for key, expected in context.snapshots.items():
        _require_hash(snapshots[key], f"{where}.snapshots.{key}")
        if snapshots[key] != expected:
            raise LedgerError(f"{where}.snapshots.{key}: stale source hash")

    spans = event["selected_spans"]
    if not isinstance(spans, list):
        raise LedgerError(f"{where}.selected_spans: expected an array")
    span_identities = set()
    for index, span in enumerate(spans):
        if not isinstance(span, dict):
            raise LedgerError(f"{where}.selected_spans[{index}]: expected an object")
        _validate_source_span(context, page, span, f"{where}.selected_spans[{index}]")
        identity = (span["source_id"], span["start0"], span["end0"])
        if identity in span_identities:
            raise LedgerError(f"{where}.selected_spans[{index}]: duplicate source span")
        span_identities.add(identity)

    disposition = event["disposition"]
    if disposition not in DISPOSITIONS:
        raise LedgerError(f"{where}.disposition: unsupported value")
    if disposition == "accepted" and not spans:
        raise LedgerError(
            f"{where}: accepted correction requires at least one exact span"
        )
    if disposition == "ambiguous" and len(spans) < 2:
        raise LedgerError(
            f"{where}: ambiguous correction requires at least two defensible spans"
        )
    if disposition in {"rejected", "not_found"} and spans:
        raise LedgerError(
            f"{where}: {disposition} correction cannot contain accepted spans"
        )

    _validate_proposal(
        context, page, event["previous_proposal"], f"{where}.previous_proposal"
    )
    if disposition == "rejected" and event["previous_proposal"] is None:
        raise LedgerError(
            f"{where}: rejected correction must identify the rejected proposal"
        )

    review = event["review"]
    if not isinstance(review, dict):
        raise LedgerError(f"{where}.review: expected an object")
    _require_exact_keys(review, REVIEW_KEYS, f"{where}.review")
    if review["reviewer_type"] not in REVIEWER_TYPES:
        raise LedgerError(f"{where}.review.reviewer_type: unsupported value")
    for key in ("reviewer", "provenance", "notes"):
        _require_string(review[key], f"{where}.review.{key}")
    for key in ("approved_for_regression", "approved_for_training"):
        if not isinstance(review[key], bool):
            raise LedgerError(f"{where}.review.{key}: expected boolean")
    if review["reviewer_type"] == "automated" and (
        disposition != "unresolved"
        or review["approved_for_regression"]
        or review["approved_for_training"]
    ):
        raise LedgerError(
            f"{where}: automated suggestions cannot become reviewed correction evidence"
        )
    if disposition in {"ambiguous", "unresolved"} and review["approved_for_training"]:
        raise LedgerError(
            f"{where}: ambiguous or unresolved records cannot be training examples"
        )


def validate_events(context: CorrectionContext, events: Iterable[dict]) -> dict:
    rows = list(events)
    latest: dict[str, dict] = {}
    event_ids = set()
    for index, event in enumerate(rows):
        validate_event(context, event, f"ledger line {index + 1}")
        event_id = event["event_id"]
        correction_id = event["correction_id"]
        if event_id in event_ids:
            raise LedgerError(f"ledger line {index + 1}: duplicate event_id {event_id}")
        event_ids.add(event_id)
        previous = latest.get(correction_id)
        if previous is None:
            if event["revision"] != 1:
                raise LedgerError(
                    f"ledger line {index + 1}: correction history must start at revision 1"
                )
        elif (
            event["revision"] != previous["revision"] + 1
            or event["supersedes_event_id"] != previous["event_id"]
        ):
            raise LedgerError(
                f"ledger line {index + 1}: stale or conflicting correction revision"
            )
        latest[correction_id] = event
    return {
        "events": len(rows),
        "corrections": len(latest),
        "current_dispositions": dict(
            sorted(Counter(row["disposition"] for row in latest.values()).items())
        ),
        "latest": latest,
    }


def load_ledger(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if canonical_json(value) != raw:
            raise LedgerError(
                f"{path}:{line_number}: ledger lines must use canonical JSON"
            )
        rows.append(value)
    return rows


def parse_submission(value) -> list[dict]:
    if not isinstance(value, dict) or value.get("schema_version") != SUBMISSION_SCHEMA:
        raise LedgerError(f"Submission must use schema_version {SUBMISSION_SCHEMA}")
    if set(value) != {"schema_version", "events"} or not isinstance(
        value["events"], list
    ):
        raise LedgerError(
            "Submission must contain only schema_version and an events array"
        )
    return value["events"]


def parse_issue_body(body: str) -> list[dict]:
    blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", body, flags=re.IGNORECASE)
    matches = []
    for block in blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema_version") == SUBMISSION_SCHEMA:
            matches.append(value)
    if len(matches) != 1:
        raise LedgerError(
            "Issue body must contain exactly one fenced VLB correction submission"
        )
    return parse_submission(matches[0])


def import_events(
    context: CorrectionContext,
    ledger_path: Path,
    incoming: Iterable[dict],
    *,
    write: bool = True,
) -> dict:
    existing = load_ledger(ledger_path)
    validate_events(context, existing)
    by_event_id = {row["event_id"]: row for row in existing}
    appended, skipped = [], []
    for event in incoming:
        if not isinstance(event, dict):
            raise LedgerError("Imported events must be objects")
        event_id = event.get("event_id")
        if event_id in by_event_id:
            if canonical_json(by_event_id[event_id]) != canonical_json(event):
                raise LedgerError(f"Conflicting content for existing event {event_id}")
            skipped.append(event_id)
            continue
        appended.append(event)
        by_event_id[event_id] = event
    combined = existing + appended
    summary = validate_events(context, combined)
    if write and appended:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = (
            ""
            if not ledger_path.exists() or ledger_path.stat().st_size == 0
            else "\n" if not ledger_path.read_bytes().endswith(b"\n") else ""
        )
        payload = prefix + "\n".join(canonical_json(row) for row in appended) + "\n"
        with ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
    return {
        **{key: value for key, value in summary.items() if key != "latest"},
        "appended": [row["event_id"] for row in appended],
        "skipped": skipped,
    }


def export_feedback(events: Iterable[dict], kind: str) -> dict:
    rows = list(events)
    if kind not in {"regression", "training"}:
        raise LedgerError("Feedback export kind must be regression or training")
    latest = {}
    for event in rows:
        latest[event["correction_id"]] = event
    flag = (
        "approved_for_regression" if kind == "regression" else "approved_for_training"
    )
    selected = [row for row in latest.values() if row["review"][flag]]
    selected.sort(
        key=lambda row: (row["citation"]["citation_id"], row["page"]["page_id"])
    )
    return {
        "schema_version": f"vlb-correction-{kind}-1",
        "source": "vlb/corrections/ledger.jsonl",
        "selection": f"latest correction revisions with review.{flag}=true",
        "records": selected,
    }
