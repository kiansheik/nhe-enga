"""Regression for adapted VLB source inheritance in the production audit."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "source_inventory", ROOT / "scripts/data/source_inventory.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class VLBCitationInventoryTests(unittest.TestCase):
    def test_adapted_inherited_reference_preserves_source_and_offsets(self):
        dictionary, _ = AUDIT.read_dictionary(ROOT / "docs/dict-conjugated.json.gz")
        original = dictionary[7915]
        self.assertEqual(original["f"], "nhe'ẽporangaíba")
        # Keep the real attestation; only the surrounding corpus is bounded.
        fixture = [original, {"f": "BIBLIOGRAFIA", "d": ""}]
        records, _, summary = AUDIT.inventory(fixture, AUDIT.read_bibliography())
        references = [row for row in records if row.get("source") == "VLB"]
        self.assertEqual([row["tail"] for row in references], ["I, 34", "II, 109, adapt."])
        inherited = references[1]
        self.assertEqual(inherited["classification"], "inherited_same_parenthesis")
        self.assertEqual(original["d"][inherited["start"]:inherited["end"]], inherited["raw"])
        work = next(work for work in summary["works"] if work["source"] == "VLB")
        self.assertEqual(work["viewer_books"], ["vlb"])

    def test_audit_executes_linker_with_optional_dictionary_row_argument(self):
        targets, _ = AUDIT.link_targets(["VLB, I, 17", "VLB, II, 7"])
        self.assertEqual(targets, [["/nhe-enga/vlb/?volume=I&page=17&mode=continuous&focus=auto"], ["/nhe-enga/vlb/?volume=II&page=7&mode=continuous&focus=auto"]])


if __name__ == "__main__":
    unittest.main()
