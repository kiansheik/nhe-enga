# Grammar Navigation Guide

A quick-reference map from a described grammatical phenomenon to where it is
implemented in `pydicate`/`tupi`. This exists so a fresh agent with no memory
of past sessions can start close to the right file instead of grepping blind,
and gets faster over time as this file accumulates entries.

## How to use this file

- **Before searching**: scan the phenomenon map below for something close to
  what you're fixing. Start there.
- **After a fix**: add a row, or correct an existing one that turned out to
  be wrong or incomplete. Keep entries short: phenomenon, exact
  file/class/function, and one gotcha. Put the full root-cause narrative in
  `AGENT_NOTES.md` or a `docs/agent/session-handoffs/` entry instead, and
  link to it from the `Detail` column — don't duplicate it here.
- **If you searched but couldn't pin it down**, still add a row: leave
  `Where it lives` as "not yet localized" and describe what you ruled out.
  A documented negative result saves the next agent from repeating the same
  dead ends.
- This file is for `pydicate`/`tupi` grammar only. Static-site/build/deploy
  topics belong in `repo-map.md` and `current-state.md`.

## Phenomenon map

| Phenomenon | Where it lives | Gotcha | Detail |
|---|---|---|---|
| `og` before a pluriform noun suppresses the absolute prefix and joins the stem | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Noun.__mul__`, `Noun.preval`) | `MAIN_CLAUSE_SUBJECT` also contains `SUBJECT`; the generic subject branch otherwise leaves the noun absolute. | `AGENT_NOTES.md` (2026-09-16, "Referential `og` and pluriform nouns") |
| `/` composition against classifier/deverbal chains (compose the realized surface, not the bare verbete) | `pydicate/pydicate/predicate.py` (`Predicate.compose`, `_resolve_compose_surface`); `pydicate/pydicate/lang/tupilang/pos/deverbal.py` (`Deverbal._apply_compositions`, `Classifier.noun`) | Eval-surface composition is intentionally allowed only for `{classifier_noun, deadverbal_noun}` categories — extending it to plain nouns breaks demonstratives/pronouns. | `AGENT_NOTES.md` (2026-04-05, "Fix `/` composition..." and its "Follow-up Fix (classifier stacking)") |

_(Add new phenomena above this line, most-specific first.)_

## Open items

Phenomena reported by a linguist correction but not yet localized or fixed.
Remove a row once it moves to the phenomenon map above.
