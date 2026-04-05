# Agent Notes (2026-04-05)

## Goal
Fix `/` composition so classifier/deverbal chains like:
`rama * (pyra * Verb("erokûab")) / Noun("eté", ...)`
produce `serokûapyrameté` instead of `rametérama` (i.e., compose the realized surface of noun-like predicates rather than the bare verbete).

## Root Cause
`Predicate.compose()` always composed using `self.verbete` and `modifier.verbete`. For classifier/deadverbal nouns, the real surface is produced by `.eval()` (with internal morphology), so composing on the verbete lost the derived surface and re-applied morphology, yielding wrong outputs.

## Changes
### 1) `Predicate.compose()` (pydicate/pydicate/predicate.py)
- Added a helper `_resolve_compose_surface()` to optionally use a predicate’s *evaluated* single-token surface.
- This is now **allowed only for** categories `{classifier_noun, deadverbal_noun}` to avoid changing general noun behavior.
- If the evaluated surface is used for the *original* predicate, the composed predicate is **frozen** (clears arguments/adjuncts and sets `_compositions_frozen = True`) so the internal morphology isn’t re-applied later.
- For the **modifier**, we still allow evaluated surface when its category is `{deverbal_noun, classifier_noun, deadverbal_noun}` (same intent as before).

Key behaviors:
- Classifier chain now composes from the realized surface:
  - `rama * (pyra * Verb("erokûab")) / eté` -> `serokûapyrameté`.
- Deverbal as modifier still uses evaluated surface (single-token) to capture derived morphology.
- Regular nouns (including demonstratives, pronouns, etc.) remain unchanged.

### 2) `Deverbal._apply_compositions()` (pydicate/pydicate/lang/tupilang/pos/deverbal.py)
- If `_compositions_frozen` is set, skip composition re-application.
- Modifier surface resolution for compositions remains limited to derived categories (deverbal/classifier/deadverbal) to avoid pulling in noun inflection (e.g., absolute `t-` prefix) unexpectedly.

## Tests
Ran in `../oldtupicorpus` (read-only as requested):
```
make test
```
All tests OK.

## Notes/Assumptions
- The new “eval surface” path is **intentionally limited** to `{classifier_noun, deadverbal_noun}` for the left-hand side to avoid unexpected changes in noun inflection or demonstratives.
- If future subclasses should use evaluated surfaces for `/`, extend `allow_eval_categories` in `Predicate.compose()`.

## Files Touched
- `pydicate/pydicate/predicate.py`
- `pydicate/pydicate/lang/tupilang/pos/deverbal.py`

## Follow-up Fix (classifier stacking)
User reported stacked classifiers with `/` still wrong:
Expected `mba'ererokûakatuoryparametépûerama`, got `...parambûerameté`.

### Root Cause
Classifier stacking dropped inner classifier surfaces because `Classifier.noun` used the argument’s *noun base* instead of its realized surface when the argument itself was a classifier. `/` applied to the outer classifier, so the modifier landed after the outermost suffix rather than before the remaining classifier chain.

### Changes
1) **Classifier.noun** now preserves stacked classifier surfaces:
- If argument category is `classifier_noun`, build a `TupiNoun` from `arg.eval(annotated=True)` (single-token only) so suffixes are retained.
- Otherwise keep the previous behavior (operate on noun base).
File: `pydicate/pydicate/lang/tupilang/pos/deverbal.py`

2) **Predicate.compose** now descends into classifier chains:
- If `self.category == classifier_noun` and `self.arguments[0]` is also a classifier, then apply `compose` to the innermost classifier and reattach, preserving temporal ordering.
- This yields `/` attaching to the innermost classifier in a chain while outer classifiers stay outside.
File: `pydicate/pydicate/predicate.py`

### Result
Expression:
`rama * (pûera * (rama * (sara * (...) ))) / eté`
Now returns:
`mba'ererokûakatuoryparametépûerama`.

### Tests
`make test` in `../oldtupicorpus` passed after the change.
