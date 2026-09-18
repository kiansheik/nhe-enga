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

# 2026-09-16: Referential `og` and pluriform nouns

Historic attestation: `oldtupicorpus/historic/araujo_catecismo_1686.tu.py`,
record `araujo_catecismo_1686:0074` (source line 223). Its unchanged
expression contains `og * apixara`; the editor-approved target is
`oîeaûsuba îabé asé oapixararaûsuba no`. This is a rule proposed by the
human editor; a matching render does not independently prove the historical
analysis.

`og` has tag `[PRONOUN:MAIN_CLAUSE_SUBJECT:3p]`. In Pydicate
`Noun.__mul__`, the broad `"SUBJECT" in tag` branch had treated it as an
ordinary subject adjunct. The pluriform noun then underwent `absoluta()`
during `Noun.preval`, adding `t[PLURIFORM_PREFIX:T:ABSOLUTE]` despite the
referential pronoun already occupying that prefix position. The annotated
space between `og` and the noun also led the enclosing nominal verb form
to keep them as separate words.

The dedicated `MAIN_CLAUSE_SUBJECT` branch now suppresses the absolute
pluriform prefix on the copied noun. `Noun.preval` joins this pronoun to
the stem in both plain and annotated renderings. The contrast
`nde * apixara -> nde rapixara` remains unchanged; standalone `apixara`
remains `tapixara`. The pluriform verb nominal `(og * aûsub).base_nominal()`
already renders `ogaûsuba` and is unchanged. Regression:
`oldtupicorpus/tests/og_pluriform_prefix_test.py`.

# 2026-09-16: Single reflexive object in nominal variation 1

Historic attestation: `oldtupicorpus/historic/araujo_catecismo_1686.tu.py`,
record `araujo_catecismo_1686:0079`. The human editor rewrote its first
clause to `îe * (smi * (kuakub/puai))`; no engine change is needed for that
clause. The agreed full surface is
`Santa Madre Igreja îekuakupûaîa îabi'õ îekuakuba`.

`kuakub` is transitive. In `îe * kuakub`, its one argument is the object,
so `Verb.base_nominal()` takes the transitive branch. The Tupi nominal
`variation_id == 1` short-prefix rule applies only in the intransitive
branch; the transitive branch therefore produces `oîekuakuba` even when
the editor explicitly selects variation 1. For a transitive verb with
exactly one reflexive or reciprocal argument and variation 1,
`Verb.base_nominal()` now uses a copied verb with intransitive nominal
conjugation. The source expression and stored argument remain intact.

This scope preserves the approved default nominal
`oîepe'asagûera` in Araujo and Bettendorff record 23. Applying
intransitive behavior to every single reflexive object would change both
approved lines to `oîo pe'asagûera`. The two-argument case retains its
subject/object order. Regression:
`oldtupicorpus/tests/reflexive_nominal_variation_test.py`.

The corrected render demonstrates the engine behavior requested by the
editor; it is not independent proof of the historical analysis.

# 2026-09-16: Raw numbers as nominals and number adjuncts

Historic attestation: `oldtupicorpus/historic/araujo_catecismo_1686.tu.py`,
record `araujo_catecismo_1686:0080`. The unchanged expression begins
`iabiõ * n(opakombó)` and the editor's target is
`opakombó îabi'õ Tupã supé oîepé asé mba'e moîa'oka` (spacing ignored).
The runtime lexicon labels `opakombó` as `[NUMBER:TEN]`; its citation also
quotes the corresponding Araujo phrase.

The corpus helper `n` calls `base_nominal(True)`. `Number` lacked that
method, so the entire source failed to load. `Number.base_nominal` now
wraps a raw number as a noun without changing its surface and preserves
its number tag. The expression also builds a `Number` with two preceding
phrases attached through `+`. `Predicate.__addpre__` stores those phrases
in `pre_adjuncts`, but `Number.preval` previously ignored them. It now
renders them in reverse attachment order before the numbered phrase and
renders any post-adjuncts afterward.

The engine renders `... asé mba'emoîa'oka`, which has the same sequence
of characters as the editor's `... asé mba'e moîa'oka` when whitespace
is ignored. Regression: `oldtupicorpus/tests/number_nominalization_test.py`.
The matching render does not establish the historical analysis.

# 2026-09-16: Nasally stemmed emi nouns with og

The editor supplied the minimal construction `og * (emi * tym)` and
specified `oemityma`. The editor subsequently added it in Araujo record
81, which remains unaccounted. Historic `emi` constructions already occur
in `oldtupicorpus/historic/araujo_catecismo_1686.tu.py` (for example
`emi * (potar * nde)`), so ordinary possessed forms must remain stable.

`tupi/tupi/noun.py` (`Noun.emi`) has an initial-consonant branch for
`p/k/t/s`. When that branch found a nasal consonant anywhere in `tym`,
it performed no insertion, dropping `emi-` completely. The nasal branch
now inserts unaltered `emi-`. Thus the absolute form is `temityma` and
`nde * (emi * tym)` is `nde remityma`.

`pydicate/pydicate/lang/tupilang/pos/noun.py` already recognizes `og`
before a pluriform noun, but `Deverbal.noun` is a computed property and
the generic prefix mutation does not persist. `emi_morphology` now sees
the referential pronoun attached to the `Deverbal`, skips the absolute
`t-` choice, and joins `o-` to the bare `emi` noun. Its annotated result
is `o[PRONOUN:MAIN_CLAUSE_SUBJECT:3p]emi[PATIENT_PREFIX]tym...`.

Regression: `oldtupicorpus/tests/emi_referential_test.py`. All saved
historic targets were unchanged. A matching render, including record 81,
does not establish the historical analysis.

# 2026-09-16: Possessed m-class nouns as verb objects

Historic source: `oldtupicorpus/historic/araujo_catecismo_1686.tu.py`,
record `araujo_catecismo_1686:0081`. The editor's unchanged expression
contains `tupapotaba * meeng`; the requested full surface is
`oemitymbûerypy pupé Tupã potabame'engi no`.

`potaba` is marked `(m)`. Its absolute form correctly used `m-`, but
`Noun.pluriform_prefix` tested the general pluriform cases first and
therefore chose `r-` or `s-` for possessed forms. Separately,
`Noun.possessive` forced `r-` whenever an explicit possessor accompanied
any pluriform noun. Thus even `tupan * potaba` rendered `Tupã rotaba`
before the noun became a verb object. The verb preserved that wrong form.

The `(m)` case now takes priority: absolute `motaba`, possessed `Tupã
potaba` and `nde potaba`. The explicit-possessor `r-` branch still applies
to other pluriform classes. The unchanged record 81 expression renders
the requested form with annotated `p[PLURIFORM_PREFIX:P]` on the direct
object. Regression: `oldtupicorpus/tests/m_pluriform_possession_test.py`.
All 80 saved Araujo and 40 Bettendorff targets remain verified; record 81
is unaccounted until the human editor commits its ground truth. A matching
render does not independently establish the historical analysis.

# 2026-09-16: Explicit mbo variant of mo

Historic source: `oldtupicorpus/historic/araujo_catecismo_1686.tu.py`,
record `araujo_catecismo_1686:0082`. Its unchanged expression uses the
shared `moîasuk` helper and the editor specifies
`i karaíba pupé îemboîasuka`. Before this change, `moîasuk = mo * îasuk`
and `VerbAugmentor.__mul__` always concatenated the literal `mo-`, so
the line rendered `îemoîasuka`.

Selecting `mbo-` for every nonnasal root would change approved Araujo
and Bettendorff examples with `mo * îaok` and `mo * (ar / ukar)`.
The editor chose an explicit variation: `mbo = mo.var(1)`. The bare
augmentor renders `mbo`, and composition contributes the annotated
`mbo[CAUSATIVE_PREFIX:MBO]`; default `mo` remains `mo-`. The shared
lexicon helper is now `moîasuk = mbo * îasuk`, leaving record 82's
expression untouched. Variation 1 on this bare augmentor selects an
allomorph; variation 1 applied later to the formed verb still controls
its nominal form.

Regression: `oldtupicorpus/tests/mo_mbo_variation_test.py`. All 80
saved Araujo and 40 Bettendorff targets remain verified. Araujo records
81 and 82 are unaccounted pending the human editor's Commit ground truth
action. A matching render does not establish the historical analysis.

# 2026-09-16: Explicit nasal reflexive and reciprocal variants

`nhe = îe.var(1)` and `nho = îo.var(1)` name optional nasal forms.
`Pronoun.noun_function` renders the standalone form; Pydicate `Verb`
passes the attached pronoun's variation to `TupiVerb.conjugate`, which
replaces only tagged reflexive/reciprocal morphemes. Default `îe`/`îo`
expressions keep their earlier rendering. Araujo record 77 is a default
contrast: `seîxu îabi'õ îemombe'u`; the explicit variant of its final
construction evaluates as `nhemombe'u`.

The editor reported that previous normalization may have hidden nasal
forms. `oldtupicorpus/docs/agent/reflexive-nasal-review.md` inventories
the 20 direct historic `îe` occurrences (13 in Araujo, 7 in Bettendorff)
and two shared-lexicon uses for line-by-line witness review. No historic
expression or approved target was changed. There are no direct historic
`îo` occurrences. One nested construction, record 29 in both sources,
still detaches a substituted `nhe` as a separate object; it needs a
separate engine fix if the editor selects the nasal form there.

Regression: `oldtupicorpus/tests/reflexive_nasal_variation_test.py`.
Matching candidate renders are implementation evidence, not historical
approval.

# 2026-09-17: Noun-object incorporation

The editor selected an incorporated-object analysis for Araujo Catecismo 1686
record 81. `potaba` is `(m)` pluriform and `me'eng` is transitive. Previously
`potaba / meeng` returned a `Noun`, so its `.var(1)` could neither change
valency nor identify Tupã's role; a superficially matching nominal compound
would omit the proposed verbal analysis.

`Noun.__truediv__` now returns `IncorporatedObjectVerb` for a bare noun and
bare transitive verb. It calls the existing `tupi.Noun.compose` before
inflection, retaining its elision, accent and nasal behavior. The default is
intransitive with a generic incorporated object. `.var(1)` is transitive:
the external object denotes the incorporated noun's possessor; with one
argument it is the object, and with two the first is subject. The resulting
stem uses the left noun's pluriform inflection, so `potaba / meeng` gives
absolute `motame'enga`, while the overt possessor in
`(tupan * (potaba / meeng).var(1)).base_nominal()` gives
`Tupã potame'enga`, annotated with `p[PLURIFORM_PREFIX:P]` and an
incorporated-object boundary. `IncorporatedVerbNominal` keeps external
adjuncts before the complete Tupã phrase.

Contrast: ordinary `potaba / ypy` remains a noun compound, and direct-object
`potaba * meeng` remains distinct. Tests are in
`pydicate/tests/test_incorporated_object_verb.py` and
`oldtupicorpus/tests/incorporated_object_verb_test.py`. The historical witness
prints `Tupã potâ meengano`; this implementation represents the editor's
analysis and matching spelling does not independently prove incorporation.
## 2026-09-17 — Size suffix pieces

Navarro's size suffix senses can be selected as `SizeSuffix` and composed with
`/`: `Noun("pira") / SizeSuffix("-gûasu")` gives `piragûasu`, whereas ordinary
noun composition drops the last vowel. The selected spelling stays explicit:
`-ûasu`, `-gûasu`, and `-usu` are not silently substituted for one another.
`-'ĩ` loses its glottal stop after a consonant; a final `a` is elided before
this diminutive, as in `membyrĩ`. The independent adjective `mirĩ` can also
be explicitly selected for composition, while retaining its noun analysis.
The dictionary picker distinguishes the
size senses from the homographic lusivo `-'ĩ` and quantifying `-usu` senses.
Tests: `pydicate/tests/test_size_suffix.py` and
`pydicate-studio/python/tests/test_dictionary_authoring.py`. This covers the
cited examples, not every historical stem or a decision about their analysis.
