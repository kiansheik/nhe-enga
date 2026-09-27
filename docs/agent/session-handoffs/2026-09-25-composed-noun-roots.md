# Plain noun composition retains both component roots

## Goal

Repair the generated analysis of `esá / poraûsubara`, which exposed only the
right operand as one root, without changing the approved expression or surface.
Keep the change general only for simple lexical nouns whose stored bases already
contain the boundary.

## Files inspected

`AGENTS.md`; agent state/map/questions and grammar navigation;
`pydicate/pydicate/predicate.py`; compound regressions; Araújo and Bettendorff
record 22 source expressions and ground truth; all 145 current historic
expressions and their annotation audits.

## Files changed

- `pydicate/pydicate/predicate.py`
- `pydicate/tests/test_compound_annotations.py`
- `docs/agent/current-state.md`
- `docs/agent/grammar-navigation.md`
- `docs/agent/log.md`
- this handoff

## Commands run

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=pydicate:tupi python3 -B
  pydicate/tests/test_compound_annotations.py -v`: 7 tests pass.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=pydicate:tupi python3 -B -m unittest
  discover -s pydicate/tests -p 'test_*.py'`: 62 tests pass.
- In `oldtupicorpus`, with this checkout first on `PYTHONPATH`, `python3 -B
  tests/run_tests.py --skip-tokenizer`: 112 tests pass.
- A read-only all-record comparison: all 145 ordinary outputs equal checked-in
  ground truth and all 145 annotation audits pass.

## What worked

The left operand now passes through `_compose_modifier_base` before the low-level
noun composition. That helper only returns an annotated lexical base when it is
the exact stored base for a simple noun. Both record-22 expressions retain the
ordinary output `eboûing nde resaporaûsubara erobak oré koty` and now emit
`r[PLURIFORM_PREFIX:R]esa[ROOT]poraûsubar[ROOT]a[...]`.

Exactly 15 current records change their annotations. Each change splits a former
single root into roots already represented by the source composition; no ordinary
surface changes. The regression includes an explicit `noroot=True` left operand
which remains unannotated.

## What failed

The first temporary patch had an incorrect hunk count and `git apply` rejected it
without changing the checkout. Applying the same reviewed patch with recount
succeeded. No test failed after the repair.

## Remaining questions

A stored composition boundary is implementation evidence, not independent
linguistic adjudication. The qualification exporter separately needs to expose
the stored `/` child while preserving its legacy `DEEPEST_NODE` numbering; this
engine change supplies the two emitted roots but does not redefine that legacy
partial hierarchy.

## Suggested next prompt

Regenerate the qualification appendix from the current engine, verify separate
`esa` and `poraûsubar` root rows plus the `/ poraûsubara` composition child in
Araújo and Bettendorff 0022, and confirm all saved targets remain unchanged.
