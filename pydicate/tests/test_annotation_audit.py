"""Structural contracts behind the Araújo 73 annotation repair.

These tests detect lost occurrence tags, fabricated alignment references and
scope leakage. They do not assert that all corpus annotations are linguistically
correct. Proper-name spans and ordinary/annotated differences remain explicit.
"""

from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "pydicate"), str(REPO / "tupi")]

from pydicate import Predicate
from pydicate.annotation_audit import (
    audit_annotation,
    parse_occurrences,
    validate_audit_report,
)
from pydicate.lang.tupilang.pos import Noun, Conjunction, Verb, mo


class Literal(Predicate):
    def __init__(self, annotated, ordinary=None):
        super().__init__("fixture", "test", 0)
        self.annotated_output = annotated
        self.ordinary_output = ordinary

    def preval(self, annotated=False):
        if annotated:
            return self.annotated_output
        return (
            self.ordinary_output
            if self.ordinary_output is not None
            else re.sub(r"\[[^\]]+\]", "", self.annotated_output)
        )


class Joined(Predicate):
    def __init__(self, *children):
        super().__init__("", "test", 0)
        self.arguments = list(children)

    def preval(self, annotated=False):
        return " ".join(child.eval(annotated=annotated) for child in self.arguments)


class AnnotationAuditTest(unittest.TestCase):
    def test_parser_is_occurrence_local_and_preserves_whitespace(self):
        pieces = parse_occurrences("a[SUBJECT:1ps] a[ROOT][NOUN] a[SUBSTANTIVE_SUFFIX]")
        self.assertEqual([p["surface"] for p in pieces], ["a", " a", " a"])
        self.assertEqual(pieces[0]["tags"], ["1ps", "SUBJECT"])
        self.assertEqual(pieces[1]["tags"], ["NOUN", "ROOT"])
        self.assertEqual(pieces[2]["tags"], ["SUBSTANTIVE_SUFFIX"])

    def test_malformed_tags_fail_without_hanging(self):
        for text in ("[ROOT]", "x[", "x]", "x[]", "x[[ROOT]", "x[ROOT:]", " [ROOT]"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_occurrences(text)

    def test_occurrence_integrity_catches_same_surface_wrong_tags(self):
        expression = Literal("a[SUBJECT:1ps] a[SUBSTANTIVE_SUFFIX]")
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])
        report["emitted_pieces"][0]["tags"] = ["SUBSTANTIVE_SUFFIX"]
        self.assertIn("emit_occurrence_mismatch", validate_audit_report(report))

    def test_hierarchy_may_not_import_context_free_tags(self):
        report = audit_annotation(Literal("oré[OBJECT:1ppe]"))
        report["hierarchy_annotated"] = report["hierarchy_annotated"].replace(
            "OBJECT", "OBJECT:POSSESSOR"
        )
        self.assertIn("hierarchy_occurrence_mismatch", validate_audit_report(report))

    def test_invented_deepest_node_is_rejected(self):
        report = audit_annotation(Literal("x[ROOT]"))
        report["hierarchy_annotated"] = re.sub(
            r"DEEPEST_NODE_\d+", "DEEPEST_NODE_999", report["hierarchy_annotated"]
        )
        self.assertIn("legacy_node_reference", validate_audit_report(report))

    def test_null_conjunction_has_construction_scope_not_suffix_tag(self):
        expression = Conjunction("") + Noun("aûsub") + Noun("potar")
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])
        coordination = [
            c for c in report["constructions"] if c["kind"] == "coordination"
        ]
        self.assertEqual(len(coordination), 1)
        self.assertTrue(coordination[0]["zero_surface_lexeme"])
        self.assertEqual(len(coordination[0]["scope"]), 2)
        self.assertFalse(any("CONJUNCTION" in p["tags"] for p in report["pieces"]))

    def test_overt_conjunction_retains_its_own_annotation(self):
        report = audit_annotation(Conjunction("abé") * Noun("aûsub") * Noun("potar"))
        self.assertTrue(report["passed"], report["hard_failures"])
        coordination = [p for p in report["pieces"] if "CONJUNCTION" in p["tags"]]
        self.assertEqual([p["surface"].strip() for p in coordination], ["abé"])

    def test_suffix_scope_leak_is_hard_failure(self):
        report = audit_annotation(Literal("a[SUBSTANTIVE_SUFFIX:CONJUNCTION:AND]"))
        self.assertIn("conjunction_on_substantive_suffix", report["hard_failures"])

    def test_full_paths_cover_relations_without_renumbering_legacy(self):
        expression = Literal("x[ROOT]")
        for field in ("v_adjuncts", "v_adjuncts_pre", "compositions"):
            setattr(expression, field, [Literal("x[ROOT]")])
        expression.principal = Literal("x[ROOT]")
        expression._nominalization_source = Literal("x[ROOT]")
        expression._nominalization_operation = "base_nominal"
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])
        paths = {n["path"] for n in report["tree"]}
        self.assertTrue(
            {
                "root.v_adjuncts[0]",
                "root.v_adjuncts_pre[0]",
                "root.compositions[0]",
                "root.principal",
                "root._nominalization_source",
            }
            <= paths
        )
        self.assertEqual(report["legacy_nodes"], [{"id": 1, "path": "root"}])

    def test_new_uninventoried_predicate_field_fails_gate(self):
        expression = Literal("x[ROOT]")
        expression.new_wrapper = Literal("y[ROOT]")
        report = audit_annotation(expression)
        self.assertIn("unsupported_predicate_relation", report["hard_failures"])

    def test_incorporated_object_sources_are_explicit_stored_relations(self):
        # Araújo 0110 and 0115 exercise the same stored relation shape through
        # larger causative/nominal chains. This neutral fixture checks structure,
        # not either passage's historical or linguistic analysis.
        incorporated = Noun("potaba", "portion") / Verb(
            "me'eng", verb_class="v.tr.", definition="give"
        )
        expression = (mo * incorporated).base_nominal()
        report = audit_annotation(expression)

        self.assertTrue(report["passed"], report["hard_failures"])
        paths = {node["path"] for node in report["tree"]}
        self.assertIn("root._nominalization_source.incorporated_object", paths)
        self.assertIn("root._nominalization_source.source_verb", paths)
        self.assertIn(
            "root._nominalization_source._augmentee.incorporated_object", paths
        )
        self.assertIn("root._nominalization_source._augmentee.source_verb", paths)
        self.assertFalse(report["unsupported_relations"])

    def test_unknown_nested_container_predicates_cannot_disappear(self):
        expression = Literal("x[ROOT]")
        expression.new_wrapper = {"child": [({"nested": Literal("y[ROOT]")},)]}
        report = audit_annotation(expression)
        self.assertIn("unsupported_predicate_relation", report["hard_failures"])
        self.assertEqual(
            report["unsupported_relations"],
            [
                {
                    "path": "root",
                    "field": "new_wrapper",
                    "kind": "container",
                    "container_path": "value:0/index:0/index:0/value:0",
                }
            ],
        )

    def test_unknown_container_cycles_terminate_and_still_find_predicates(self):
        expression = Literal("x[ROOT]")
        container = []
        container.append(container)
        container.append({"child": Literal("y[ROOT]")})
        expression.new_wrapper = container
        report = audit_annotation(expression)
        self.assertIn("unsupported_predicate_relation", report["hard_failures"])
        self.assertEqual(len(report["unsupported_relations"]), 1)
        self.assertEqual(
            report["unsupported_relations"][0]["container_path"], "index:1/value:0"
        )
        # A cyclic non-Predicate metadata container is not a hidden relation.
        container.pop()
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])

    def test_unknown_dict_key_predicate_is_also_detected(self):
        expression = Literal("x[ROOT]")
        expression.new_wrapper = {(Literal("y[ROOT]"),): "metadata"}
        report = audit_annotation(expression)
        self.assertIn("unsupported_predicate_relation", report["hard_failures"])
        self.assertEqual(
            report["unsupported_relations"][0]["container_path"], "key:0/index:0"
        )

    def test_flattened_nominalization_is_rejected_but_opaque_name_is_not(self):
        expression = Literal("asé saûsub[ROOT]")
        expression.verbete = "asé saûsub[ROOT]"
        expression._nominalization_source = Literal("asé[SUBJECT] saûsub[ROOT]")
        expression._nominalization_operation = "base_nominal"
        self.assertIn(
            "flattened_nominalization_root",
            audit_annotation(expression)["hard_failures"],
        )
        name = Literal("Virgem Maria[ROOT]")
        name.category = "proper_noun"
        report = audit_annotation(name)
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertEqual(report["metrics"]["multiword_root_piece_count"], 1)

    def test_ordinary_surface_difference_is_reported_separately(self):
        report = audit_annotation(Literal("x[ROOT]", ordinary="y"))
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertFalse(report["surface"]["matches"])
        report = audit_annotation(Literal("x[ROOT]  y[ROOT]", ordinary="x y"))
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertFalse(report["surface"]["matches"])
        self.assertTrue(report["surface"]["matches_after_whitespace_normalization"])

    def test_opaque_lexical_name_inside_nominalization_is_preserved(self):
        # Araújo 79 enters Santa Madre Igreja as one lexical noun. Its unchanged
        # root span is distinct from flattening a subject plus verbal root.
        expression = Literal("Santa Madre Igrej[ROOT]a[SUBSTANTIVE_SUFFIX] x[ROOT]")
        expression.verbete = expression.annotated_output
        expression._nominalization_source = Joined(
            Noun("Santa Madre Igreja"), Literal("x[ROOT]")
        )
        expression._nominalization_operation = "base_nominal"
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])

    def test_repeated_witnesses_stay_ambiguous(self):
        report = audit_annotation(Joined(Literal("x[ROOT]"), Literal("x[ROOT]")))
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertEqual(report["metrics"]["ambiguous_child_event_witness_tags"], 2)
        self.assertEqual(report["metrics"]["unique_child_event_witness_tags"], 0)
        json.dumps(report)

    def test_root_only_is_not_counted_as_independent_origin(self):
        report = audit_annotation(Literal("x[ROOT]"))
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertEqual(report["metrics"]["root_output_only_tags"], 1)
        self.assertEqual(report["metrics"]["unique_child_event_witness_tags"], 0)

    def test_copied_nids_keep_distinct_evaluation_events(self):
        first = Literal("x[ROOT]")
        second = first.copy()
        second.annotated_output = "y[ROOT]"
        report = audit_annotation(Joined(first, second))
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertEqual(report["metrics"]["shared_nids_with_distinct_outputs"], 1)
        outputs = [
            event["output"]
            for event in report["evaluation_events"]
            if event["nid"] == first.nid
        ]
        self.assertEqual(outputs, ["x[ROOT]", "y[ROOT]"])

    def test_missing_trace_and_fabricated_metrics_fail(self):
        report = audit_annotation(Literal("x[ROOT]"))
        corrupt = deepcopy(report)
        corrupt["evaluation_events"] = []
        self.assertIn("missing_evaluation_trace", validate_audit_report(corrupt))
        report["metrics"]["unique_child_event_witness_tags"] = 100
        self.assertIn("metric_mismatch", validate_audit_report(report))

    def test_invented_witness_and_missing_tree_path_fail(self):
        report = audit_annotation(Joined(Literal("x[ROOT]")))
        corrupt = deepcopy(report)
        corrupt["pieces"][0]["tag_evidence"][0]["witnesses"][0]["event_id"] = 999
        self.assertIn("tag_witness_mismatch", validate_audit_report(corrupt))
        corrupt = deepcopy(report)
        corrupt["tree"] = [
            node for node in corrupt["tree"] if node["path"] != "root.arguments[0]"
        ]
        self.assertIn("legacy_tree_identity", validate_audit_report(corrupt))

    def test_coordination_scope_cannot_be_deleted_or_invented(self):
        report = audit_annotation(Conjunction("") + Noun("aûsub") + Noun("potar"))
        corrupt = deepcopy(report)
        corrupt["constructions"] = []
        self.assertIn("construction_scope_mismatch", validate_audit_report(corrupt))
        report["constructions"][0]["scope"] = ["root.missing"]
        self.assertIn("construction_scope_mismatch", validate_audit_report(report))

    def test_nominalization_source_path_is_required(self):
        expression = Literal("x[ROOT]")
        expression._nominalization_source = Literal("x[ROOT]")
        expression._nominalization_operation = "base_nominal"
        expression._nominalization_annotated_argument = False
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertIs(report["constructions"][0]["annotated_argument"], False)
        report["tree"] = [
            n for n in report["tree"] if n["path"] != "root._nominalization_source"
        ]
        self.assertIn("nominalization_source_missing", validate_audit_report(report))

    def test_principal_backlink_is_finite_explicit_graph_reference(self):
        child = Literal("x[ROOT]")
        expression = Joined(child)
        child.principal = expression
        report = audit_annotation(expression)
        self.assertTrue(report["passed"], report["hard_failures"])
        self.assertEqual(report["metrics"]["cycle_count"], 1)
        backlink = next(n for n in report["tree"] if n["cycle_to"])
        self.assertEqual(backlink["path"], "root.arguments[0].principal")
        self.assertEqual(backlink["cycle_to"], "root")

    def test_event_tree_reference_and_piece_offsets_are_checked(self):
        report = audit_annotation(Literal("x[ROOT]"))
        corrupt = deepcopy(report)
        corrupt["evaluation_events"][0]["tree_paths"] = ["invented"]
        self.assertIn("event_tree_path_mismatch", validate_audit_report(corrupt))
        report["pieces"][0]["surface_start"] = 100
        self.assertIn("piece_offset_mismatch", validate_audit_report(report))


if __name__ == "__main__":
    unittest.main()
