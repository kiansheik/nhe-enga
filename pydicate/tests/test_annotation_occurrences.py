"""Occurrence identity and construction scope; Araújo73 is the source contrast.

Annotations must retain each emitted occurrence's contextual tags. A repeated
spelling cannot donate its grammatical role to another occurrence. Null
coordination belongs to its tree node, never to a neighboring substantive -a.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "pydicate"), str(ROOT / "tupi")]
from pydicate import Predicate
from pydicate.predicate import EvalCtx
from pydicate.lang.tupilang.pos import (
    Noun,
    ProperNoun,
    Conjunction,
    Verb,
    asé,
    sosé,
    opakatu,
    tetiruã,
)


class Literal(Predicate):
    def __init__(self, annotated):
        super().__init__("fixture", "fixture", 0)
        self.output = annotated

    def preval(self, annotated=False):
        import re

        return self.output if annotated else re.sub(r"\[[^\]]*\]", "", self.output)


class AnnotationOccurrenceTests(unittest.TestCase):
    def test_identical_spelling_retains_distinct_occurrence_tags(self):
        e = Literal("a[SUBJECT]î[OBJECT_MARKER]a[SUBSTANTIVE_SUFFIX]")
        self.assertEqual(
            e.emit(),
            [
                ("a", {"SUBJECT"}),
                ("î", {"OBJECT_MARKER"}),
                ("a", {"SUBSTANTIVE_SUFFIX"}),
            ],
        )

    def test_bare_and_tagged_same_spelling_do_not_share_tags(self):
        e = Literal("x[ROOT]x")
        self.assertEqual(e.emit(), [("x", {"ROOT"}), ("x", set())])

    def test_hierarchy_never_imports_independent_child_roles(self):
        e = Literal("x[OBJECT]")
        e.arguments = [Literal("x[SUBJECT]")]
        self.assertNotIn("SUBJECT", e.hierarchical_representation_v4())
        self.assertIn("OBJECT", e.hierarchical_representation_v4())

    def test_multiword_proper_name_is_not_split(self):
        e = Literal("Espírito Santo[PROPER_NOUN]")
        self.assertEqual(e.emit(), [("Espírito Santo", {"PROPER_NOUN"})])

    def test_null_coordination_does_not_label_a_substantive_suffix_and(self):
        e = Noun("abá") + Noun("pira")
        self.assertEqual(e.eval(), "abá pira")
        self.assertNotIn("CONJUNCTION", e.eval(True))
        self.assertEqual(e.tag, "[CONJUNCTION:AND]")

    def test_lexical_coordinator_keeps_its_own_annotation(self):
        e = Conjunction("abé", tag="[CONJUNCTION:AND]") * Noun("abá") * Noun("pira")
        self.assertEqual(e.eval(), "abá pira abé")
        self.assertTrue(e.eval(True).endswith("abé[CONJUNCTION:AND]"))

    def test_eval_context_retains_distinct_calls_of_copied_node(self):
        a = Literal("x[ROOT]")
        b = a.copy()
        b.output = "y[ROOT]"
        ctx = EvalCtx()
        a.eval(True, ctx=ctx)
        b.eval(True, ctx=ctx)
        self.assertEqual(a.nid, b.nid)
        self.assertEqual([e["output"] for e in ctx.events], ["x[ROOT]", "y[ROOT]"])
        self.assertEqual(len({e["event_id"] for e in ctx.events}), 2)

    def test_nested_events_keep_the_actual_call_parent(self):
        e = Noun("abá") + Noun("pira")
        ctx = EvalCtx()
        e.eval(True, ctx=ctx)
        self.assertIsNone(ctx.events[0]["parent_event_id"])
        self.assertTrue(
            any(
                ev["parent_event_id"] == ctx.events[0]["event_id"]
                for ev in ctx.events[1:]
            )
        )
        self.assertEqual(ctx._event_stack, [])


if __name__ == "__main__":
    unittest.main()
