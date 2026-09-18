# Preserve lexical annotations in compound modifiers

## Goal
Repair the annotation loss reported through Pydicate Studio for Araújo 81 without changing the existing source expression, spelling or analysis.

## Files inspected
AGENTS and agent index/state/map/questions/grammar-navigation; Predicate.compose, Deverbal._apply_compositions, Classifier, TupiNoun.compose and AnnotatedString; Araújo source line235, lexical ypy/tym declarations and existing emi/m-pluriform tests; Studio runtime graph labels and authoring evaluation.

## Files changed
`pydicate/pydicate/predicate.py`, `pydicate/pydicate/lang/tupilang/pos/deverbal.py`, `pydicate/tests/test_compound_annotations.py`, agent current-state/log/grammar-navigation and this handoff. Existing dirty morphology changes were preserved.

## Commands run
- `python3 -B pydicate/tests/test_compound_annotations.py -v`: two output assertions fail before repair; five tests pass afterward.
- In oldtupicorpus: `python3 -B -m unittest tests.emi_referential_test tests.m_pluriform_possession_test -v`: six pass.
- Read-only before/after rendering of both historic sources: all122 surfaces identical; all120 saved surfaces still match. Araújo81–82 remain unsaved.
- `python3 -B -m authoring.ground_truth_cli verify --source araujo_catecismo_1686 --source bettendorff_compendio --json`: Bettendorff passes; Araújo reports pre-existing stale record74, whose saved JSONL lacks source-inherited location metadata. Source/reference hashes remained unchanged.
- `git diff --check`. Black is not installed in the active interpreter or repository virtualenv; no formatter was installed.

## What worked
The existing `ypy` lexical noun has `ypy[ROOT]` in its stored morphology, but both composition paths rebuilt it from bare `verbete` with `noroot=True`. `_compose_modifier_base` retains this existing metadata only when it exactly matches the normalized single-word stem. It does not evaluate a plain noun or infer new boundaries. Already annotated, explicitly untagged, multiword and composed modifiers preserve the prior path.

The existing expression `(pûera * (og * (emi * tym))) / ypy` still renders `oemitymbûerypy`. Its annotated output now ends `bûer[PRETERITE_SUFFIX]ypy[ROOT][CLASSIFIER:PAST]`. TupiNoun already joins supplied annotations correctly, so the low-level engine needed no edit. Existing absolute, referential and possessed emi forms remain distinct.

Studio separately strips inline annotation metadata from graph display labels while retaining the original verbete in evidence. A temporary-profile native test confirms the title `oemitymbûerypy` on actual passage81 with no renderer errors.

## What failed
The first probe used an incorrect context keyword (`window` rather than `radius`); corrected. Ground-truth context cannot resolve unsaved ordinal81, so source entries and the existing focused regression supplied the evidence. The strict JSONL audit is not fully clean because of the pre-existing record74 metadata mismatch; no regeneration was performed.

## Remaining questions
The user supplied an internal annotated stem, without an alternative expected spelling. This change fixes confirmed metadata/display defects and makes no new linguistic judgment. Classifier composition's existing freezing of internal arguments remains outside this repair. Studio's older dependency baseline is historical; this engine change is an additional local patch, not a regenerated baseline.

## Suggested next prompt
If the intended spelling or analysis differs, provide the expected form and source evidence for Araújo81 so it can be evaluated separately from annotation preservation.
