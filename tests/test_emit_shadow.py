import os
import sys

# Ensure local editable packages are on sys.path (repo uses nested package layout)
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "pydicate"))
sys.path.insert(0, os.path.join(ROOT, "tupi"))

from pydicate.lang.tupilang.pos import Noun, Verb, Adverb, ixé, endé


def _assert_emit_matches_old(expr):
    old = expr.eval(annotated=False)
    em = expr.emit()
    assert em.surface == old
    assert em.morphs
    assert em.morphs[0].text == old


def test_emit_shadow_noun():
    _assert_emit_matches_old(Noun("taba", definition="village"))


def test_emit_structured_noun():
    noun = Noun("taba", definition="village")
    em = noun.emit()
    assert em.surface == noun.eval(annotated=False)
    assert em.morphs
    assert em.morphs[0].text.startswith("taba")


def test_emit_shadow_verb_intransitive():
    go = Verb("só", definition="to go")
    _assert_emit_matches_old(go * ixé)


def test_emit_shadow_verb_with_adjuncts():
    go = Verb("só", definition="to go")
    koritei = Adverb("koritei", definition="recently")
    expr = koritei + (go * endé)
    _assert_emit_matches_old(expr)
