# VLB alignment mining: first frozen experiment

**Result:** a page-constrained, orthography-aware pipeline retrieves the correct
Emerson paragraph first in **21 of 25 clear held-out cases**, compared with
**14 of 25** using the existing candidate ranking. All 25 correct paragraphs
appear in its top three. Exact first-choice text spans are correct in **19 of
25**. The result is useful for review; it does not yet justify automatically
accepting its strongest proposals or driving exact highlights from them.

This experiment was frozen on **2026-11-03 at 02:36:23 UTC**, before the test
labels were released. The [freeze record](output/model-freeze.json) pins the
algorithm files, thresholds, models, predictions, and preregistration. Neither
the algorithm nor the labels was retuned after the test results were inspected.

## What was computed

The inputs are the existing pinned Navarro dictionary JSON, Emerson revision
568, the estimated printed-page boundaries, citation occurrence inventory, and
the official PDF's OCR layout. The pipeline searches each cited page's actual
text, records up to three candidate source paragraphs, and preserves the exact
historical form with global source offsets. A separate compact index groups the
top-ranked proposals by dictionary row and historical form.

| Full-corpus inventory | Count |
| --- | ---: |
| Valid citation/page memberships processed | 6,164 |
| Dictionary rows in the historical-form index | 4,146 |
| Selected silver training records | 613 |
| Accepted unique modern/historical surface pairs | 566 |
| Top result passes all proposal gates (`suggested`) | 2,885 |
| Other candidates requiring review | 3,136 |
| Weak candidate sets | 138 |
| No generated candidate | 5 |
| Unresolved original citation locators, retained separately | 2 |

These inventory counts are not counts of correct matches. In particular, a
historical form exists at the saved offsets even when its proposed association
with the dictionary citation is wrong. `suggested` remains unreviewed.

The two unresolved citations retain their original problems: **aeté**, row
2451, cites `VLB, I, 1390`; **hegûy**, row 4595, cites `VLB, I` without a page.
They were not silently corrected or forced onto a source page.

## Orthography and learning

The model permits several directional alternatives rather than producing one
normalized historical spelling. Examples include `potyra → Potigra`,
`akyrara → Aquîrara`, and `ybyraypy → Ybiraigpig`. It treats historical `ig` as a
multigraph, conditions `c/qu` alternatives on the historical environment, and
retains nasal and glottal information with nonzero mismatch costs.
See [ORTHOGRAPHY.md](ORTHOGRAPHY.md) and the
[18 development evidence cases](development_evidence.json) for source
references, literal forms, and the limits of each correspondence.

Morphological surfaces are a separate input layer: an explicit dictionary
example, an explicitly supplied adjective form, or a bounded and labeled
`a-`, `aî-`, or `xe-` hypothesis. The learner does not treat arbitrary prefix
insertion or nominal `-a` deletion as spelling rules. No morphology-engine code
was invoked or changed.

The silver pairs are selected by the existing spelling aliases plus agreement
with the Portuguese entry heading and page uniqueness. This is deliberately
biased evidence. It supplies support counts for admitted spellings but cannot
independently validate those spellings or discover every missing alternative.
The especially useful `y → ig` correspondence remains a documented prior,
rather than a discovery from these seeds.

The learned model contains 24 sufficiently supported observations: ten can
lower an edit cost, while fourteen are retained only for audit because they
cannot beat the existing fallback. The ten effective additions are `i → j`
and nine cautious nasal-notation alternatives. Learned weights are heuristic
retrieval costs, not estimated probabilities.

## Independent evaluation design

An assistant reviewer selected **48 citation/page cases before seeing the new
rankings**. The sample balances both volumes and three existing-retrieval
strata: a baseline target, unresolved existing candidates, and no existing
candidate. It deliberately includes short headwords, longer forms, and adapted
citations. The earlier pilot examples were excluded.

A deterministic split allocated **20 development cases and 28 test cases**,
grouping shared headwords and pages together. The split used metadata only; it
was registered after sixteen passages had already been inspected, a timing
detail preserved in the preregistration. The full test labels were withheld
until the model and all predictions were frozen.

All 48 sampled headwords, 45 selected printed pages, and 1,327 source paragraphs
were excluded from spelling-seed training. Source exclusions also cover
continuations onto three neighboring pages. An independent check found zero
headword, page, or paragraph overlaps among the 613 seeds.

The review identifies citation-specific paragraphs and literal spans using
both spelling and the quoted example or sense. Labels are **assistant-reviewed,
not human-verified**. The 28 test cases contain 25 clear paragraph matches,
two genuinely ambiguous cases, and one case not identified on the cited page.
The balanced sample is too small and deliberately too selective for its raw
percentages to estimate accuracy across the full corpus.

## Held-out results

The baseline is the ranking already saved in the viewer's page data, not the
separate continuous-reader automatic-target policy. Uniform, prior-only, and
learned models use the same new page search, shortlist, surface hypotheses,
Portuguese context, quotation features, and thresholds. The uniform comparison
replaces only the final edit weights with ordinary unit costs. Thus the entire
baseline-to-new gain must not be attributed solely to orthography.

| Method | Correct paragraph first | Correct paragraph in top three | Exact form span first |
| --- | ---: | ---: | ---: |
| Existing saved candidate ranking | 14/25 (56%) | 16/25 (64%) | Not measured |
| New retrieval, uniform final edit costs | 20/25 (80%) | 24/25 (96%) | 19/25 (76%) |
| New retrieval, documented spelling priors | 21/25 (84%) | 25/25 (100%) | 19/25 (76%) |
| New retrieval, priors plus silver observations | **21/25 (84%)** | **25/25 (100%)** | **19/25 (76%)** |

The exact annotated span occurs among the learned model's top three candidates
in **22/25** cases. Among the eight clear test cases with no previous candidate,
the new model gets **7/8** first paragraphs and **8/8** within the top three.

The priors help compared with uniform final edit costs in this sample. The
additional learned observations show **no measured improvement over the
priors** on these metrics. More independent reviewed pairs are needed before
claiming that learned weights outperform the documented mapping.

On the development set, the final ranker gets **19/19 clear paragraphs** first,
with **18/19 exact spans**. Development examples informed changes to the
Portuguese context retrieval and quotation handling, so those results are
development feedback and must not be presented as independent validation.

The frozen full, prior-only, and uniform predictions were reproduced with
identical hashes. The full model, seeds, compact index, and summary also
reproduced byte-for-byte. Per-case results are in
[the evaluation JSON](output/test_labels-evaluation.json), with a separate
[independent audit](output/independent-test-audit.json).

## Why this version remains a review tool

Ten of the 28 test cases pass all proposal gates. **Nine of those ten identify
the correct paragraph; one does not.** None of the two ambiguous or one
not-found test cases is marked suggested. The error nevertheless rules out
treating `suggested` as a reliable automatic acceptance policy.

| Case | What the frozen model chooses | What the citation-specific review identifies | Consequence |
| --- | --- | --- | --- |
| `putuna`, II, 50 | Standalone `Putuna`, §5223; marked suggested | Navarro quotes `Pytũ 'ã / Pytun iã`, corresponding to `Pigtuã / Pigtuniã` in §5224 | An exact lemma match can be the wrong cited passage. The current quotation heuristic skips parenthesized alternatives. |
| `so'o`, I, 62 | Standalone `Çoo`, §1341 | The cited compound `so'o-kugûaba`, represented by `Xeçoocuguab` in §1349 | Whole quoted compounds need priority over a bare lemma. Correct paragraph is second; review flag is present. |
| `esaraî`, I, 127 | `Xereçarai` in the neighboring `rece` construction, §3339 | `Xereçaray. çuî.` in §3340, matching Navarro's `suí` | Postpositions and argument structure can identify the citation more precisely than the main form. Correct paragraph is second; review flags are present. |
| `îuká`, II, 33 | General `Ajuca`, §4779 | Intensified `Ajucamatutenhe`, §4778 | The long cited compound falls outside the current relevant-form heuristic. Correct paragraph is third; review flags are present. |
| `'a`, I, 137 | Portuguese article `A` inside the correct paragraph §3612 | Compound `Apixapaba` | Correct paragraph does not establish a correct token highlight. Review flags are present. |
| `sosé`, II, 67 | First standalone `Çoce` in §5589 | Quoted occurrence `Uinte çoce` later in that paragraph | Repeated forms require occurrence-level context. Review flags are present. |

These cases were not patched into the frozen model after test release. They
provide concrete requirements for a subsequent experiment: preserve and parse
parenthesized example alternatives, retrieve whole compounds even for very
short headwords, align accompanying constructions, and distinguish repeated
occurrences within a paragraph. A new evaluation sample should accompany any
threshold or ranking changes informed by these failures.

## OCR location evidence

Across all 6,164 records, the first-ranked candidate has a narrowed form-token
OCR line set in 5,305 cases, an approximate paragraph region in 815, and no
usable OCR region in 39. Five records have no generated candidate. Among the
2,885 `suggested` records, 2,548 have a form-token OCR target.

Those numbers measure availability of OCR evidence for the chosen candidate,
not correct citation alignment. The algorithm prefers exact case-folded
historical token matches, discloses diacritic folding, does not join across
skipped lines, and preserves counts when several matching runs share one line
set. It never labels the boxes exact glyph regions. Physical scan-line accuracy
has not been independently measured by this paragraph/form benchmark.

## Scope for dictionary expansion

This pass starts from VLB citations already in the dictionary. It establishes
a reusable candidate map and a review queue; it does not establish that every
uncited VLB form is absent from Navarro. A dictionary entry may cover the form
without citing this page, and a source paragraph may contain several forms or
senses even when one association is reviewed.

The next coverage layer should record accepted **citation/form/sense** links,
then inspect remaining source forms against the whole dictionary, including
entries without VLB citations. New verbetes require that source and lexical
review. No new dictionary entry or broad coverage claim was generated here.

Source attribution and the full reproducible workflow are in
[README.md](README.md). Emerson's original transcription and blog credit remain
attached to the data and documentation.
