"""Durable VLB correction history, source validation, and imports."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlb"))

from corrections.ledger import (  # noqa: E402
    CorrectionContext,
    LedgerError,
    correction_id_for,
    export_feedback,
    import_events,
    load_ledger,
    parse_issue_body,
    validate_event,
    validate_events,
)


LEDGER = ROOT / "vlb/corrections/ledger.jsonl"


class CorrectionLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = CorrectionContext(ROOT)
        cls.events = load_ledger(LEDGER)

    def event(self, headword):
        return deepcopy(
            next(row for row in self.events if row["citation"]["headword"] == headword)
        )

    def test_seeded_reviews_are_exact_and_keep_uncertainty(self):
        summary = validate_events(self.context, self.events)
        self.assertEqual(summary["events"], 8)
        self.assertEqual(summary["corrections"], 8)
        self.assertEqual(
            summary["current_dispositions"],
            {"accepted": 6, "ambiguous": 1, "not_found": 1},
        )
        putuna = self.event("putuna")
        self.assertEqual(
            [span["text"] for span in putuna["selected_spans"]], ["Pigtuã", "Pigtuniã"]
        )
        self.assertEqual(self.event("esé")["selected_spans"][0]["text"], "Baerecepe")
        self.assertEqual(
            self.event("ikó")["selected_spans"][0]["text"], "Naicoŷ cece coigte"
        )
        self.assertEqual(self.event("aembé")["disposition"], "ambiguous")
        self.assertEqual(self.event("'ybapekanga")["disposition"], "not_found")
        self.assertTrue(
            all(row["review"]["reviewer_type"] == "assistant" for row in self.events)
        )
        self.assertTrue(
            all(not row["review"]["approved_for_training"] for row in self.events)
        )

    def test_exact_source_text_offsets_and_page_membership_are_required(self):
        event = self.event("mokanãî")
        event["selected_spans"][0]["text"] = "Aimocanai"
        with self.assertRaisesRegex(LedgerError, "pinned source"):
            validate_event(self.context, event)

        event = self.event("mokanãî")
        event["page"] = {"page_id": "I-018", "volume": "I", "printed_page": 18}
        event["correction_id"] = correction_id_for(
            event["citation"]["citation_id"], "I-018"
        )
        event["event_id"] = event["correction_id"] + "-r0001"
        with self.assertRaisesRegex(LedgerError, "not a member"):
            validate_event(self.context, event)

    def test_stale_source_and_algorithm_hashes_are_rejected(self):
        event = self.event("sosé")
        event["snapshots"]["source_text_sha256"] = "0" * 64
        with self.assertRaisesRegex(LedgerError, "stale source hash"):
            validate_event(self.context, event)

        event = self.event("sosé")
        event["previous_proposal"]["output_sha256"] = "0" * 64
        with self.assertRaisesRegex(LedgerError, "stale algorithm output hash"):
            validate_event(self.context, event)

    def test_ocr_lines_and_boxes_must_resolve_to_the_selected_fragment(self):
        event = self.event("mokanãî")
        event["selected_spans"][0]["ocr_targets"][0]["line_id"] = "ocr-017-037"
        with self.assertRaisesRegex(LedgerError, "not aligned to this source fragment"):
            validate_event(self.context, event)

        event = self.event("mokanãî")
        event["selected_spans"][0]["ocr_targets"][0]["box"][0] += 0.01
        with self.assertRaisesRegex(LedgerError, "does not match current data"):
            validate_event(self.context, event)

        event = self.event("mokanãî")
        target = event["selected_spans"][0]["ocr_targets"][0]
        target["box_source"] = "reviewer_correction"
        target["previous_box"] = target["box"][:]
        target["box"] = [target["box"][0] + 0.001, *target["box"][1:]]
        validate_event(self.context, event)

    def test_automated_suggestion_cannot_be_promoted_to_review_evidence(self):
        event = self.event("mokanãî")
        event["review"]["reviewer_type"] = "automated"
        with self.assertRaisesRegex(LedgerError, "cannot become reviewed"):
            validate_event(self.context, event)

    def test_idempotent_import_skips_identical_event(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ledger.jsonl"
            shutil.copyfile(LEDGER, target)
            before = target.read_bytes()
            result = import_events(self.context, target, [self.events[0]])
            self.assertEqual(result["appended"], [])
            self.assertEqual(result["skipped"], [self.events[0]["event_id"]])
            self.assertEqual(target.read_bytes(), before)

    def test_revision_appends_history_and_preserves_multiple_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ledger.jsonl"
            shutil.copyfile(LEDGER, target)
            revision = self.event("putuna")
            revision["revision"] = 2
            revision["event_id"] = revision["correction_id"] + "-r0002"
            revision["supersedes_event_id"] = revision["correction_id"] + "-r0001"
            revision["recorded_at"] = "2026-11-03T12:30:00-03:00"
            revision["review"][
                "notes"
            ] += " Re-saved without collapsing either accepted span."
            result = import_events(self.context, target, [revision])
            self.assertEqual(result["appended"], [revision["event_id"]])
            rows = load_ledger(target)
            self.assertEqual(len(rows), 9)
            self.assertEqual(len(rows[-1]["selected_spans"]), 2)
            self.assertEqual(
                rows[-1]["supersedes_event_id"], self.event("putuna")["event_id"]
            )
            second = import_events(self.context, target, [revision])
            self.assertEqual(second["appended"], [])
            self.assertEqual(second["skipped"], [revision["event_id"]])

    def test_conflicting_or_stale_revision_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ledger.jsonl"
            shutil.copyfile(LEDGER, target)
            before = target.read_bytes()
            revision = self.event("sosé")
            revision["revision"] = 2
            revision["event_id"] = revision["correction_id"] + "-r0002"
            revision["supersedes_event_id"] = (
                "vlb-correction-00000000000000000000-r0001"
            )
            with self.assertRaisesRegex(LedgerError, "stale or conflicting"):
                import_events(self.context, target, [revision])
            self.assertEqual(target.read_bytes(), before)

            conflict = self.event("sosé")
            conflict["review"][
                "notes"
            ] = "Conflicting content under an existing event ID."
            with self.assertRaisesRegex(LedgerError, "Conflicting content"):
                import_events(self.context, target, [conflict])
            self.assertEqual(target.read_bytes(), before)

    def test_issue_payload_and_feedback_exports_are_explicit(self):
        envelope = {
            "schema_version": "vlb-correction-submission-1",
            "events": [self.events[0]],
        }
        body = (
            "## Correção estruturada\n\n```json\n"
            + json.dumps(envelope, ensure_ascii=False)
            + "\n```\n"
        )
        self.assertEqual(parse_issue_body(body), [self.events[0]])
        regression = export_feedback(self.events, "regression")
        training = export_feedback(self.events, "training")
        self.assertEqual(len(regression["records"]), 8)
        self.assertEqual(training["records"], [])
        putuna = next(
            row
            for row in regression["records"]
            if row["citation"]["headword"] == "putuna"
        )
        self.assertEqual(len(putuna["selected_spans"]), 2)


if __name__ == "__main__":
    unittest.main()
