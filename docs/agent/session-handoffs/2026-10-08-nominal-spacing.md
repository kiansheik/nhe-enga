# Nominal preverbal-adjunct spacing — 2026-10-08

Goal: explain the qualification mismatch and fix the extra space without changing
Araújo 1686:118's approved linguistic construction. User explicitly requested the
engine fix; no lexical, inflectional, or source-expression change was needed.

Inspected: source expression and record 118 in oldtupicorpus, Studio approval
normalization, LaTeX surface_consistency.py and corpus_appendices.py, dictionary
utils.py and tokenizer/build_corpus_json.py, nominal/conjugation and classifier
paths, engine AGENTS files and grammar-navigation.md.

Cause: conjugate pads vadjs_pre with leading/trailing spaces, then the nominal
branch adds a second subject joiner. The saved reference and ordinary output have
two spaces; the annotation-derived dictionary export strips tags and collapses
whitespace. LaTeX compares these independently and exactly, correctly rejecting
that one record. Browser normal whitespace rendering conceals the doubled space.

Changed: tupi/tupi/verb.py omits the nominal joiner when vadjs_pre already supplies
it; pydicate/tests/test_historic_surface_consistency.py covers the complete historic
expression, overt/pronominal nominal subjects, no adjunct, and existing i/îe
word-boundary contrasts. Updated navigation and this handoff.

Commands/results: unittest discover pydicate/tests (82 passed), focused historic
surface tests (5 passed), qualification test_surface_consistency.py (4 passed).
Fresh dictionary + ordinary + annotated comparison of all 160 local historic
expressions before/after: only Araújo118 changes, deleting exactly one space in
plain and annotated output; dictionary output unchanged. The unchanged qualification
gate passes all 160 when that single saved reference is corrected IN MEMORY ONLY.
No source/corpus/reference file was written. Raw snapshots/script are private in
pydicate-studio/.local/spacing-fix-20261008. Initial regression failed as expected;
contrast expectations were aligned with the existing nominal (sekó/rekó) and
pronominal-subject behavior before validating the fix.

Remaining: local uncommitted engine fix, not deployed. The actual approved record
still contains two spaces, so the qualification gate continues to reject it until
it is explicitly re-saved/corrected using the fixed engine. Do not weaken the gate
or claim a full qualification PDF build. Suggested next prompt: deploy/review the
engine fix and re-save Araújo1686:118's single-space approved reference, then run
make qualification. No other passage or spelling changed.
