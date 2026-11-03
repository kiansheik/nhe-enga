"""Durable VLB correction history, source validation, and imports."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vlb"))

from corrections.ledger import (  # noqa: E402
    CorrectionContext,
    LedgerError,
    canonical_json,
    correction_id_for,
    export_feedback,
    import_events,
    load_ledger,
    parse_issue_body,
    validate_event,
    validate_events,
)


LEDGER = ROOT / "vlb/corrections/ledger.jsonl"
SEED_EVENT_IDS = (
    "vlb-correction-91e2dcecb830aa991048-r0001",
    "vlb-correction-5832f39a3422b9709015-r0001",
    "vlb-correction-9eba4de54e9551520e28-r0001",
    "vlb-correction-b1047ede2d9d93974112-r0001",
    "vlb-correction-77eb71202e027510b7c1-r0001",
    "vlb-correction-6475d2e1ea8ae4764b40-r0001",
    "vlb-correction-042ba3d348e9f512e14c-r0001",
    "vlb-correction-791ddae535bd4963a064-r0001",
)


class CorrectionLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = CorrectionContext(ROOT)
        cls.events = load_ledger(LEDGER)
        by_event_id = {row["event_id"]: row for row in cls.events}
        try:
            cls.seed_events = [by_event_id[event_id] for event_id in SEED_EVENT_IDS]
        except KeyError as exc:
            raise AssertionError(f"Missing historical seed event {exc.args[0]}") from exc

    def event(self, headword):
        return deepcopy(
            next(
                row
                for row in self.seed_events
                if row["citation"]["headword"] == headword
            )
        )

    def write_seed_ledger(self, target):
        target.write_text(
            "\n".join(canonical_json(row) for row in self.seed_events) + "\n",
            encoding="utf-8",
        )

    def test_seeded_reviews_are_exact_and_keep_uncertainty(self):
        summary = validate_events(self.context, self.events)
        self.assertEqual(summary["events"], len(self.events))
        self.assertEqual(
            summary["corrections"],
            len({row["correction_id"] for row in self.events}),
        )
        self.assertEqual(
            sum(summary["current_dispositions"].values()), summary["corrections"]
        )
        self.assertEqual(
            [row["event_id"] for row in self.seed_events], list(SEED_EVENT_IDS)
        )
        self.assertEqual(
            {
                row["citation"]["headword"]: row["disposition"]
                for row in self.seed_events
            },
            {
                "mokanãî": "accepted",
                "motumung": "accepted",
                "putuna": "accepted",
                "sosé": "accepted",
                "esé": "accepted",
                "'ybapekanga": "not_found",
                "ikó": "accepted",
                "aembé": "ambiguous",
            },
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
            all(
                row["review"]["reviewer_type"] == "assistant"
                for row in self.seed_events
            )
        )
        self.assertTrue(
            all(
                not row["review"]["approved_for_training"]
                for row in self.seed_events
            )
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
            self.write_seed_ledger(target)
            before = target.read_bytes()
            event = self.seed_events[0]
            result = import_events(self.context, target, [event])
            self.assertEqual(result["appended"], [])
            self.assertEqual(result["skipped"], [event["event_id"]])
            self.assertEqual(target.read_bytes(), before)

    def test_revision_appends_history_and_preserves_multiple_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "ledger.jsonl"
            self.write_seed_ledger(target)
            revision = self.event("putuna")
            previous_event_id = revision["event_id"]
            revision["revision"] += 1
            revision["event_id"] = (
                f'{revision["correction_id"]}-r{revision["revision"]:04d}'
            )
            revision["supersedes_event_id"] = previous_event_id
            revision["recorded_at"] = "2026-11-03T12:30:00-03:00"
            revision["review"][
                "notes"
            ] += " Re-saved without collapsing either accepted span."
            result = import_events(self.context, target, [revision])
            self.assertEqual(result["appended"], [revision["event_id"]])
            rows = load_ledger(target)
            self.assertEqual(len(rows), len(self.seed_events) + 1)
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
            self.write_seed_ledger(target)
            before = target.read_bytes()
            revision = self.event("sosé")
            revision["revision"] += 1
            revision["event_id"] = (
                f'{revision["correction_id"]}-r{revision["revision"]:04d}'
            )
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
        issue_event = deepcopy(self.seed_events[0])
        issue_event["review"]["approved_for_regression"] = False
        envelope = {
            "schema_version": "vlb-correction-submission-1",
            "events": [issue_event],
        }
        body = (
            "## Correção estruturada\n\n```json\n"
            + json.dumps(envelope, ensure_ascii=False)
            + "\n```\n"
        )
        self.assertEqual(parse_issue_body(body), [issue_event])
        issue_event["review"]["approved_for_regression"] = True
        unsafe_body = (
            "```json\n"
            + json.dumps(envelope, ensure_ascii=False)
            + "\n```\n"
        )
        with self.assertRaisesRegex(LedgerError, "approvals must be false"):
            parse_issue_body(unsafe_body)
        latest = validate_events(self.context, self.events)["latest"].values()
        for kind, flag in (
            ("regression", "approved_for_regression"),
            ("training", "approved_for_training"),
        ):
            exported = export_feedback(self.events, kind)
            self.assertEqual(
                {row["event_id"] for row in exported["records"]},
                {row["event_id"] for row in latest if row["review"][flag]},
            )

        regression = export_feedback(self.seed_events, "regression")
        training = export_feedback(self.seed_events, "training")
        self.assertEqual(
            {row["event_id"] for row in regression["records"]}, set(SEED_EVENT_IDS)
        )
        self.assertEqual(training["records"], [])
        putuna = next(
            row
            for row in regression["records"]
            if row["citation"]["headword"] == "putuna"
        )
        self.assertEqual(len(putuna["selected_spans"]), 2)


if __name__ == "__main__":
    unittest.main()
