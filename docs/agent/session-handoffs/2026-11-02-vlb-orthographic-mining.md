# VLB orthographic mining — 2026-11-02 São Paulo / 2026-11-03 UTC

## User intent and branch

Build an offline, precomputed map from Navarro headwords/citation contexts to
the most plausible actual forms and passages in Emerson's VLB transcription.
Use historical spelling correspondences and page constraints; preserve enough
evidence to support precise future text/OCR highlighting and coverage review.

Branch: `feat/vlb-orthographic-alignment`, directly from `main`
`ef6a586c5d13733537480048924de1776662c70c`. The separate continuous-reader work
remains in draft PR #36, `feat/vlb-continuous-reader`; this branch neither
depends on nor changes that reader implementation.

## Deliverables

- `vlb/mine_alignment.py`: standard-library-only offline CLI.
- `vlb/mining/orthography.py`: weighted directional grapheme/multigraph model,
  preserved marks, contextual alternatives, auditable operations.
- `vlb/mining/seeds.py`: conservative silver pair selection with explicit
  surface provenance and held-out headword/page/source exclusions.
- `vlb/mining/pipeline.py`: actual page-fragment spans, bounded surface
  hypotheses, context-aware ranking, uncertainty gates, OCR line evidence,
  and independent evaluation.
- `vlb/mining/form_index.py`: compact per-headword/row index derived from the
  frozen citation/page candidates.
- `vlb/mining/output`: complete candidates, compact index, seeds, learned
  model, freeze hashes, evaluation, independent audit, and ablations.
- `vlb/mining/benchmark`: preregistration, dev/test labels, portable validator.
- `vlb/mining/development_evidence.json`: 18 exact source examples informing
  the spelling priors; separate from evaluation.
- `README.md`, `ORTHOGRAPHY.md`, `REPORT.md` inside `vlb/mining` explain usage,
  sources, evidence, results, and limitations.

## Frozen results and constraints

All 6,164 valid citation/page memberships were processed; the compact index
contains 4,146 dictionary rows. The two original malformed/missing-page
citations remain unresolved. Every original source span is preserved and
checked against the pinned Emerson text and the current page fragment.

Training: 613 silver records, 566 unique accepted surface pairs. All 48
benchmark headwords, 45 pages, and 1,327 source paragraphs are excluded. There
are ten effective learned additions, mostly cautious nasal-notation changes;
the useful `y → ig` mapping remains a documented prior, not an independent
silver-data discovery.

Test labels were released only after `output/model-freeze.json` recorded the
algorithm/configuration/prediction hashes at 02:36:23 UTC. Test fixture hash:
`9127cf95329f476df3c61df81eab69acc7f6094fe8a2b6d021d571482dce846a`.
Full prediction hash:
`84e9928cca755c6d78a4d4cb201555549ddbc80f0f5cbfb9506953e8bafd368e`.

Held-out test: 25 clear, 2 ambiguous, 1 not found on the cited page.

- Paragraph top one: 21/25, versus existing ranking 14/25.
- Paragraph top three: 25/25, versus existing ranking 16/25.
- Exact text span top one: 19/25; exact span top three: 22/25.
- Ten suggested cases; nine paragraph-correct. The false suggestion is
  `putuna`, where the exact lemma is adjacent to the actual quoted predicate.
- Prior-only and learned models have identical test metrics. Uniform final
  edit weights with the same new retrieval/context get 20/25 and 24/25.

These are assistant-reviewed, difficulty-balanced sample results. They are not
human verification, corpus accuracy, or a precision guarantee. `suggested`
does not mean approved. The report explicitly recommends review-only use and
does not promote any new production links. No dictionary, transcription,
reviewed-association file, morphology engine, or UI was changed.

## Known next research work

Read the frozen failure analysis before altering ranking. Short heads,
compounds, parenthesized quotation alternatives, postpositions, and repeated
occurrences remain the important errors. For example, `putuna` selects
`Putuna` but the citation is to `Pigtuã / Pigtuniã`; `sosé` finds the right
paragraph but the wrong occurrence. Do not silently patch these cases and
keep reporting the same held-out numbers. A subsequent model needs a new
evaluation sample or an explicit development treatment of this test set.

The next coverage pass should map accepted forms/senses, then inspect
uncovered source forms against the entire dictionary, including entries
without VLB citations. A paragraph with one match is not fully covered, and
an unsuccessful retrieval does not justify creating a verbete.

## Verification

Passed 9 orthography/seed tests, 7 pipeline regressions, 2 citation inventory
checks, 4 viewer-data checks, and 6 existing dictionary-link checks. Both label
fixtures validate. Independently rebuilt model, seeds, full candidates,
compact index, and summary match byte-for-byte; prior/uniform predictions
match their pre-release hashes. A separate assistant audited all holdout
exclusions and test counts. CI includes the new tests and fixture validator.

The new offline directory is outside the website's explicit build allowlist;
it adds no current browser payload. No UI/browser rebuild was needed for this
data-only change. Emerson's project, Google document, Abanhe'enga resource page,
and the Curt Nimuendajú facsimile are credited in the documentation.
