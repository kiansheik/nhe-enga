"""Protect the viewer's source evidence, snapshot identities, and review scope.

Run: python -m unittest discover -s tests -p test_vlb_viewer_data.py
The pinned inputs are evidence fixtures; no generator internals are imported.
"""

from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "vlb/data"
SOURCE = ROOT / "vlb/source"


def read(path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    return json.loads(path.read_text(encoding="utf-8"))


class VLBViewerDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(DATA / "manifest.json")
        cls.pages = [read(DATA / p["data_file"]) for p in cls.manifest["pages"]]
        cls.index = read(DATA / cls.manifest["source_index_file"])
        cls.raw = (SOURCE / "emerson_vlb.txt").read_text(encoding="utf-8")
        cls.source_lines = cls.raw.split("\n")
        cls.citations = read(SOURCE / "citation_links.json.gz")
        cls.dictionary_path = ROOT / "docs/dict-conjugated.json.gz"
        cls.dictionary = read(cls.dictionary_path)

    def test_snapshot_hashes_and_exact_source_fragments(self):
        provenance = self.manifest["provenance"]
        self.assertEqual(hashlib.sha256(self.raw.encode()).hexdigest(),
                         provenance["source_text_sha256"])
        self.assertEqual(hashlib.sha256(self.dictionary_path.read_bytes()).hexdigest(),
                         provenance["dictionary_snapshot_sha256"],
                         "Dictionary row deep links require rebuilding against this snapshot.")
        fragments = defaultdict(list)
        for page in self.pages:
            for fragment in page["fragments"]:
                start, end = fragment["source_start0"], fragment["source_end0"]
                self.assertEqual(fragment["text"], self.raw[start:end])
                fragments[fragment["id"]].append((page["id"], fragment))
        self.assertEqual(set(fragments), {entry["source_id"] for entry in self.index})
        for entry in self.index:
            parts = sorted(fragments[entry["source_id"]], key=lambda p: p[1]["source_start0"])
            self.assertEqual(entry["text"], self.source_lines[entry["source_line"] - 1])
            self.assertEqual("".join(p[1]["text"] for p in parts), entry["text"])
            self.assertEqual([p[0] for p in parts], entry["page_ids"])
            for previous, current in zip(parts, parts[1:]):
                self.assertEqual(previous[1]["source_end0"], current[1]["source_start0"])
                self.assertTrue(previous[1]["continues_on_next"])
                self.assertTrue(current[1]["continues_from_previous"])
            if len(parts) > 1:
                self.assertEqual(entry["fragments"],
                                 [{"page_id": pid, "text": fragment["text"]}
                                  for pid, fragment in parts])
            else:
                self.assertNotIn("fragments", entry)
        page_files = [DATA / page["data_file"] for page in self.manifest["pages"]]
        self.assertLess(max(path.stat().st_size for path in page_files), 20_000,
                        "The reader must keep candidates page-scoped for mobile loading.")
        self.assertLess(sum(path.stat().st_size for path in DATA.rglob("*") if path.is_file()),
                        4_000_000, "The full mining audit must stay outside browser data.")

    def test_split_search_can_open_the_actual_matching_continuation(self):
        # Both boundaries were independently checked against the printed pages.
        # Sending every full-paragraph hit to page_ids[0] hides these matches.
        for source_line, term, expected_page in [
            (5859, "Cetigmã cangupiara", "II-078"),
            (7401, "Ajapigretab", "II-138"),
        ]:
            entry = next(e for e in self.index if e["source_line"] == source_line)
            matches = [f["page_id"] for f in entry["fragments"] if term in f["text"]]
            self.assertEqual(matches, [expected_page])
            self.assertNotEqual(expected_page, entry["page_ids"][0])

    def test_every_citation_keeps_its_identity_and_original_dictionary_span(self):
        expected = {c["citation_id"]: c for c in self.citations}
        self.assertEqual(len(expected), len(self.citations))
        seen = set()
        for page in self.pages:
            self.assertEqual(page["pdf_page"], page["page"] + (154 if page["volume"] == "II" else 0))
            for citation in page["citations"]:
                seen.add(citation["id"])
                pinned = expected[citation["id"]]
                row = self.dictionary[citation["entry_index"]]
                self.assertEqual(citation["headword"], row["f"])
                self.assertEqual(citation["raw_citation"], row["d"][citation["citation_start"]:citation["citation_end"]])
                self.assertEqual(citation["context"], row["d"][citation["context_start"]:citation["context_end"]])
                self.assertEqual(citation["adapted"], bool(pinned["adapted_citation"]))
        unresolved = read(DATA / self.manifest["unresolved_citations_file"])
        unresolved_ids = {c["citation_id"] for c in unresolved}
        self.assertFalse(seen & unresolved_ids)
        self.assertEqual(seen | unresolved_ids, set(expected))
        index = read(DATA / self.manifest["citation_index_file"])
        self.assertEqual({c["id"] for c in index}, set(expected))
        # The adapted inherited occurrence must not vanish while its sibling survives.
        inherited = [c for p in self.pages if p["id"] == "II-109"
                     for c in p["citations"] if c["entry_index"] == 7915]
        self.assertEqual(len(inherited), 1)
        self.assertTrue(inherited[0]["adapted"])
        self.assertEqual(inherited[0]["citation_type"], "inherited")

    def test_review_scope_and_ocr_evidence_remain_separate(self):
        ledger = [json.loads(line) for line in
                  (ROOT / "vlb/corrections/ledger.jsonl").read_text(encoding="utf-8").splitlines()
                  if line.strip()]
        latest = {}
        for row in ledger:
            latest[row["correction_id"]] = row
        latest_rows = list(latest.values())
        expected = {(row["citation"]["citation_id"], row["page"]["page_id"],
                     span["source_id"], span["start0"], span["end0"], span["text"])
                    for row in latest_rows if row["disposition"] == "accepted"
                    for span in row["selected_spans"]}
        expected_ambiguous = {(row["citation"]["citation_id"], row["page"]["page_id"],
                               span["source_id"], span["start0"], span["end0"], span["text"])
                              for row in latest_rows if row["disposition"] == "ambiguous"
                              for span in row["selected_spans"]}
        observed, observed_ambiguous = set(), set()
        reviewed_association_count = 0
        for page in self.pages:
            fragments = {f["id"]: f for f in page["fragments"]}
            lines = {line["id"]: line for line in page["ocr_lines"]}
            for fragment in fragments.values():
                self.assertEqual(fragment["ocr"]["boxes"],
                                 [lines[line_id]["box"] for line_id in fragment["ocr"]["line_ids"]])
                for left, top, right, bottom in fragment["ocr"]["boxes"]:
                    self.assertTrue(0 <= left < right <= 1 and 0 <= top < bottom <= 1)
                self.assertFalse(fragment["ocr"]["confidence_is_probability"])
            for citation in page["citations"]:
                if (citation.get("correction") or {}).get("disposition") in {
                    "not_found", "rejected"
                }:
                    self.assertTrue(citation["associations"])
                    self.assertTrue(all(association.get("suppressed_by_correction")
                                        for association in citation["associations"]))
                for association in citation["associations"]:
                    self.assertIn(association["source_id"], fragments)
                    span = association.get("span")
                    if span:
                        fragment = fragments[association["source_id"]]
                        relative_start = span["start0"] - fragment["source_start0"]
                        relative_end = span["end0"] - fragment["source_start0"]
                        self.assertEqual(fragment["text"][relative_start:relative_end],
                                         span["text"])
                        self.assertFalse(span["ocr_is_exact_glyph_box"])
                    if association["status"] == "reviewed":
                        self.assertFalse(association["covers_entire_source_record"])
                        reviewed_association_count += 1
                        if association.get("correction_event_id"):
                            self.assertIsNotNone(span)
                            observed.add((citation["id"], page["id"], association["source_id"],
                                          span["start0"], span["end0"], association["source_form"]))
                    elif association["status"] == "ambiguous":
                        self.assertEqual(association["disposition"], "ambiguous")
                        observed_ambiguous.add((citation["id"], page["id"],
                                                association["source_id"], span["start0"],
                                                span["end0"], association["source_form"]))
                    else:
                        self.assertEqual(association["status"], "proposed")
                        self.assertFalse(association["score_is_probability"])
        self.assertEqual(observed, expected)
        self.assertEqual(observed_ambiguous, expected_ambiguous)
        counts = self.manifest["counts"]
        self.assertEqual(counts["reviewed_associations"], reviewed_association_count)
        self.assertEqual(counts["correction_events"], len(ledger))
        self.assertEqual(counts["correction_decisions"], len(latest_rows))
        self.assertEqual(
            counts["correction_dispositions"],
            dict(sorted(Counter(row["disposition"] for row in latest_rows).items())),
        )
        provenance = self.manifest["provenance"]
        self.assertEqual(provenance["proposal_algorithm_version"], "vlb-page-ranker-v3")
        self.assertEqual(provenance["navigation_policy_version"],
                         "vlb-navigation-policy-v3.1")
        self.assertEqual(provenance["proposal_output_sha256"], hashlib.sha256(
            (ROOT / "vlb/mining/output-v3/candidates.json.gz").read_bytes()).hexdigest())
        self.assertEqual(provenance["correction_ledger_sha256"], hashlib.sha256(
            (ROOT / "vlb/corrections/ledger.jsonl").read_bytes()).hexdigest())
        self.assertFalse(any(page["image_index"] in (25, 26) for page in self.pages))
        plate_slots = [slot for slot in self.manifest["scan_slots"] if slot["image_index"] in (25, 26)]
        self.assertEqual(len(plate_slots), 2)
        self.assertTrue(all(slot["page_id"] is None and slot["page"] is None for slot in plate_slots))


if __name__ == "__main__":
    unittest.main()
