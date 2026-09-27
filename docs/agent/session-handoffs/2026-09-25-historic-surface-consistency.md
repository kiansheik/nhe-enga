# Historic ordinary and annotated surface consistency

## Goal

Repair three engine defects identified from the generated qualification
appendix: the missing phonetic pass in finite annotated verbs, rewriting of a
nested proper noun in an ordinary direct object, and loss of the `i îe-` word
boundary in reflexive past-classifier nominals. Preserve source expressions and
all unrelated dirty work.

## Files inspected

- `AGENTS.md` and `docs/agent/{index,current-state,repo-map,open-questions,grammar-navigation}.md`
- `pydicate/pydicate/lang/tupilang/pos/{verb,deverbal,noun}.py`
- `tupi/tupi/{tupi,verb,noun}.py`
- the Araújo and Bettendorff source expressions and saved records for 0020 and
  0028, plus Araújo 0055 and 0060 in `../oldtupicorpus`
- existing proper-name, nominalization, composition and annotation-audit tests

## Files changed

- `pydicate/pydicate/lang/tupilang/pos/verb.py`
- `pydicate/pydicate/lang/tupilang/pos/deverbal.py`
- `pydicate/tests/test_historic_surface_consistency.py`
- `docs/agent/current-state.md`
- `docs/agent/grammar-navigation.md`
- `docs/agent/log.md`
- this handoff

No historic expression, target, generated corpus record or unrelated dirty file
was edited.

## Commands run

- Focused engine discovery for `test_historic_surface_consistency.py`: 3 tests
  pass.
- Focused nominal-annotation, compound-annotation and annotation-audit suites:
  15, 7 and 25 tests pass.
- Full Pydicate discovery: 65 tests pass.
- Read-only rendering of all historic expressions: ordinary output equals the
  tag-stripped annotated output for all 105 Araújo and 40 Bettendorff records.
- Read-only annotation audits: all 145 reports pass their structural checks.
- In `../oldtupicorpus`, `make test ARGS="--skip-tokenizer"`: 112 tests run;
  only Araújo 0028 and Bettendorff 0028 fail because the repaired engine emits
  source-authored `JesusChristoabé` while saved JSONL still says
  `JesusChrixtoabé`.
- In `../oldtupicorpus`, `make verify-ground-truth`: expected failure reporting
  pre-existing Araújo record-2 metadata drift and the Bettendorff 0028 surface
  change.
- Direct saved-surface comparison: exactly the two record-28 rows differ; the
  other 143 saved surfaces are unchanged.
- Black check of the three changed Python files and `git diff --check`: pass.

## What worked

`Verb.preval` now applies `fix_phonetics_annotated` only to finite forms after
conjugation. The separate explicit nominal normalization choice remains intact.
This maps annotated `îase'ûa` to `îasegûa` without losing `[ROOT]` or suffix
tags.

Argument evaluation now detects a proper noun anywhere in the stored subtree
and keeps annotations until the ordinary low-level renderer has protected that
span. The historical composite `Jesus / Christo / abé` therefore remains
`JesusChristoabé`; a structurally parallel common `Christo` still exercises the
general `is` to `ix` rule.

The reflexive `pûera` branch already builds two words:
`i[POSSESSIVE_PRONOUN:3p] îe[SUBJECT:refl]...`. Removing its blanket
`replace("] ", "]")` preserves that authored boundary in annotated output and
leaves the ordinary form unchanged.

## What failed

The first combined `python3 -m unittest pydicate.tests...` invocation imported
the repository directory as a namespace package and could not find
`pydicate.lang`. Discovery with `PYTHONPATH=pydicate:tupi` is the correct local
invocation and passes.

`python3 -m black` was unavailable under the system Python. The installed
`black` executable is the repository's usable check path and passes all three
changed Python files.

The full sibling corpus suite and strict ground-truth check cannot pass until
the two approved record-28 surfaces are regenerated. No JSONL was hand-edited.
Strict verification also encounters the unrelated, pre-existing Araújo
record-2 source-metadata difference.

## Remaining questions

- Regenerate only the source-derived historic ground truth after protecting the
  sibling corpus checkout's unrelated dirty changes. Confirm Araújo and
  Bettendorff 0028 become `JesusChristoabé` and separately reconcile the
  existing Araújo record-2 metadata drift.
- Regenerate the qualification appendix and enforce zero ordinary/annotated
  surface discrepancies as a build invariant.

## Suggested next prompt

Safely regenerate the two affected record-28 historic targets in
`oldtupicorpus`, preserving all other dirty corpus edits; verify all 145 saved
surfaces against the repaired engine, then rebuild the qualification appendix
and assert that no ordinary/annotated surface-difference cards remain.
