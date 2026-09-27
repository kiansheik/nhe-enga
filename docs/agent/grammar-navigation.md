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

The initial qualification grammar notes are now mirrored as `# @grammar[id]`
comments immediately above five implemented methods: general argument insertion
(`Predicate.__mul__`), nominal base realization (`Noun.noun_function`), locative
and dative realization (`Locative.morphology`, `Dative.morphology`), and named
orthographic mapping (`TupiAntigo.map_orthography`). The qualification generator
checks each comment against its reviewed explanation and method-body SHA. These
comments document existing behavior; they do not claim that every construction
or every lexical declaration has an approved grammatical analysis.

| Phenomenon | Where it lives | Gotcha | Detail |
|---|---|---|---|
| Ordinary and annotated finite verbs differ after a phonetic rewrite | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`Verb.preval`) | Normalize the annotated finite result with `fix_phonetics_annotated`; keep the explicit `base_nominal(True)` compatibility path separate. | [2026-09-25 handoff](session-handoffs/2026-09-25-historic-surface-consistency.md) |
| A proper noun nested in a direct argument is rewritten as a common word | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`_contains_proper_noun`, `_eval_argument`) | Preserve tags for the whole argument only when its stored subtree contains a `proper_noun`; the ordinary renderer needs that tag to protect the name while still rewriting common nouns. | [2026-09-25 handoff](session-handoffs/2026-09-25-historic-surface-consistency.md) |
| Past classifier loses the word boundary between third-person `i` and reflexive `îe` | `pydicate/pydicate/lang/tupilang/pos/deverbal.py` (`pûer_morphology`) | Do not delete spaces after annotation groups: `i` is the nominal possessor and `îe-` begins the following reflexive nominal. | [2026-09-25 handoff](session-handoffs/2026-09-25-historic-surface-consistency.md) |
| Left operand flattened to one `[ROOT]` in plain noun `/` composition | `pydicate/pydicate/predicate.py` (`_compose_modifier_base`, `compose`) | Preserve only a simple operand's existing lexical base. Explicit `noroot`, tagged, multiword and already composed values must not acquire inferred boundaries. | [2026-09-25 handoff](session-handoffs/2026-09-25-composed-noun-roots.md) |
| Pluriform possessor of a pluriform noun | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Noun.__mul__`) | After `possessive(...)`, suppress the possessed noun’s later absolute class; otherwise it prefixes the entire phrase a second time (`tt-`). | Studio correction 2026-09-20 |
| Explicit nasal `nhe`/`nho` variants of `îe`/`îo` | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Pronoun.noun_function`, `nhe`, `nho`); `pydicate/pydicate/lang/tupilang/pos/verb.py` (`Verb._pronominal_variant`); `tupi/tupi/verb.py` (`Verb.conjugate`) | Source choices are editorial; nested Araujo/Bettendorff record 29 still detaches `nhe` during composition. | `AGENT_NOTES.md` (2026-09-16, "Explicit nasal reflexive and reciprocal variants") |
| Explicit causative `mbo-` as `mo.var(1)` | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`VerbAugmentor._prefix_form`, `__mul__`, `preval`; `mbo`) | Root nasality alone cannot choose the form: approved nonnasal `mo * îaok` stays `mo-`. | `AGENT_NOTES.md` (2026-09-16, "Explicit mbo variant of mo") |
| `(m)` pluriform nouns: absolute `m-`, possessed `p-`, including verb objects | `tupi/tupi/noun.py` (`Noun.pluriform_prefix`, `Noun.possessive`) | The general explicit-possessor `r-` branch must not override `(m)`; the noun is already wrong before verb attachment. | `AGENT_NOTES.md` (2026-09-16, "Possessed m-class nouns as verb objects") |
| `emi` before a nasal stem and referential `og` before the resulting noun | `tupi/tupi/noun.py` (`Noun.emi`); `pydicate/pydicate/lang/tupilang/pos/deverbal.py` (`emi_morphology`) | An initial `t` with a nasal later in the stem must still receive `emi-`; `og` must replace the absolute `t-` on the derived noun. | `AGENT_NOTES.md` (2026-09-16, "Nasally stemmed emi nouns with og") |
| Raw-number nominalization and number adjunct order | `pydicate/pydicate/lang/tupilang/pos/number.py` (`Number.base_nominal`, `Number.preval`) | `n(number)` needs a noun wrapper; `+` stores preceding phrases in `pre_adjuncts`, which Number must render in reverse attachment order. | `AGENT_NOTES.md` (2026-09-16, "Raw numbers as nominals and number adjuncts") |
| Nominal variation 1 of a transitive verb with only `îe` or `îo` | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`Verb.base_nominal`); `tupi/tupi/verb.py` (`Verb.conjugate`, nominal branch) | The sole argument is stored as an object; only variation 1 may use the short intransitive-style form without changing approved default nominals. | `AGENT_NOTES.md` (2026-09-16, "Single reflexive object in nominal variation 1") |
| `og` before a pluriform noun suppresses the absolute prefix and joins the stem | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Noun.__mul__`, `Noun.preval`) | `MAIN_CLAUSE_SUBJECT` also contains `SUBJECT`; the generic subject branch otherwise leaves the noun absolute. | `AGENT_NOTES.md` (2026-09-16, "Referential `og` and pluriform nouns") |
| `/` composition against classifier/deverbal chains (compose the realized surface, not the bare verbete) | `pydicate/pydicate/predicate.py` (`Predicate.compose`, `_resolve_compose_surface`); `pydicate/pydicate/lang/tupilang/pos/deverbal.py` (`Deverbal._apply_compositions`, `Classifier.noun`) | Eval-surface composition is intentionally allowed only for `{classifier_noun, deadverbal_noun}` categories — extending it to plain nouns breaks demonstratives/pronouns. | `AGENT_NOTES.md` (2026-04-05, "Fix `/` composition..." and its "Follow-up Fix (classifier stacking)") |

| Lost `[ROOT]` on a lexical noun modifier in `/` composition | `pydicate/pydicate/predicate.py` (`_compose_modifier_base`, `compose`); `pydicate/pydicate/lang/tupilang/pos/deverbal.py` (`_apply_compositions`) | Preserve the matching stored lexical stem; evaluating a plain noun here introduces unwanted absolute/possessive inflection. No inferred tags for composite, multiword or explicit `noroot` forms. | [2026-09-17 handoff](session-handoffs/2026-09-17-compound-annotations.md) |
| Noun `/` transitive verb incorporation, with `.var(1)` possessor object | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Noun.__truediv__`); `pydicate/pydicate/lang/tupilang/pos/verb.py` (`IncorporatedObjectVerb`, `IncorporatedVerbNominal`) | Reuse `tupi.Noun.compose` before inflecting the left noun; attaching its possessor before `/` loses the intended argument role. | `AGENT_NOTES.md` (2026-09-17, "Noun-object incorporation") |
| Size suffixes composed with `/` | `pydicate/pydicate/lang/tupilang/pos/suffix.py` (`SizeSuffix.attach`); `pydicate/pydicate/predicate.py` (`Predicate.compose`) | Keep the selected suffix spelling explicit; generic noun composition drops the final vowel in `pira / gûasu`. | `AGENT_NOTES.md` (2026-09-17, "Size suffix pieces") |
| Null conjunction scoping over a lexical coordinator | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Conjunction.__mul__`, `Conjunction.preval`) | Treat whitespace-only values as null; suppress the lexical coordinator only under the null wrapper, never for ordinary `abé`. | Studio correction 2026-09-19 |
| Negation of short reflexive/reciprocal verb nominals | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`Verb.base_nominal`) | For a negated transitive `.var(1)` with sole `îe`/`îo` object, derive the short nominal affirmatively, then negate the noun; retaining verbal negation loses it. | `AGENT_NOTES.md` (2026-09-20) |
| Nominalized coordinated phrase as possessor | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Conjunction.base_nominal`, `Conjunction.__mul__`) | Only explicit `.base_nominal()` changes a following `*` from coordination to possession; ordinary `abé * A * B` remains coordinate. | Studio correction 2026-09-20 |
| Medial `memẽ` in a coordinated phrase | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Conjunction.preval`) | Insert `memẽ` before the last coordinated argument; keep `abé`/`bé` postposed. | Studio correction 2026-09-21 |

| Nominalized construction loses internal annotations | `pydicate/pydicate/lang/tupilang/pos/verb.py` (`Verb.base_nominal`, `_base_nominal_annotated`) | Preserve the source construction and tags; `annotated=False` versus explicit `True` still selects the historical spelling-normalization path. Do not relabel an opaque stored multiword noun as a newly inferred construction. | [2026-09-24 applied repair](session-handoffs/2026-09-24-annotation-accountability.md) |
| Repeated spellings exchange tags; subtree evaluation adds contextual roles | `pydicate/pydicate/predicate.py` (`emit`, `hierarchical_representation_v4`, `EvalCtx`); `annotation_audit.py` | Match ordered occurrences, not a dictionary keyed by spelling. An independent subtree realization cannot supply the sentence's contextual tags; copied `nid` values can have different evaluation events. | [2026-09-24 applied repair](session-handoffs/2026-09-24-annotation-accountability.md) |
| Null coordination leaks `CONJUNCTION` onto a nominal suffix | `pydicate/pydicate/lang/tupilang/pos/noun.py` (`Conjunction.preval`); `annotation_audit.py` | A zero-surface coordinator retains its construction scope without tagging the last child's suffix. Overt conjunctions retain their own annotations. | [2026-09-24 applied repair](session-handoffs/2026-09-24-annotation-accountability.md) |
| Checking annotation/tree accountability during generation | `pydicate/pydicate/annotation_audit.py` (`audit_annotation`, `validate_audit_report`); `pydicate/tests/test_annotation_audit.py` | Applied locally; LaTeX schema-3 generation and offline checks enforce integrity. Legacy IDs remain heuristic; complete paths include nominalization sources. The 654 root-only and 1,962 ambiguous tag witnesses receive no unique-origin claim. | [2026-09-24 applied repair](session-handoffs/2026-09-24-annotation-accountability.md) |

_(Add new phenomena above this line, most-specific first.)_

## Open items

Phenomena reported by a linguist correction but not yet localized or fixed.
Remove a row once it moves to the phenomenon map above.
