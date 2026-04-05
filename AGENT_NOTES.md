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
