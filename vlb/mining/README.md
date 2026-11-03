# Precomputed Navarro → VLB alignment

This offline pass searches the **actual text on each cited VLB page**, using a
directional spelling model, explicitly recorded surface-form hypotheses, and
citation context. It writes auditable proposals with original text offsets and
available OCR line boxes. It does not change the dictionary, Emerson's text,
the morphology engine, or the reader's reviewed associations.

The first complete result covers **6,164 valid citation/page memberships** and
builds a compact historical-form index for **4,146 dictionary snapshot rows**.
The independent test improves first-ranked paragraph retrieval from **14/25 to
21/25 clear cases**; the correct paragraph is within the first three in **25/25**.
Exact first-ranked form spans match the annotations in **19/25**. These are
assistant-reviewed results on a small, difficulty-balanced test sample, not
human verification or corpus-wide accuracy estimates.

**Use this version for review and candidate retrieval.** One of its ten test
cases labeled `suggested` selects the wrong passage. That status means the
frozen ranking heuristics were satisfied; it does not authorize an automatic
production highlight or an accepted lexical association.

Read [REPORT.md](REPORT.md) for measured results and failure analysis, and
[ORTHOGRAPHY.md](ORTHOGRAPHY.md) for the spelling analysis, examples, weights,
and training limitations.

## Live V3 projection and fresh evaluation

The reader now projects frozen `output-v3/candidates.json.gz` into compact
page-scoped associations during `python3 vlb/build_data.py`; browsers never
download the full audit file. V1 and V2 outputs remain unchanged experiment
records. V3 adds construction-level quotation weight, a bounded complete-
question fusion hypothesis, and a form-only abstention reason. Released V2
failures are development regressions rather than new test evidence.

Before V3 labels existed, a fixed 24-case review packet excluded every V1/V2
case, prior correction, source record, and page used for development. An
independent assistant annotated only the blind packet and pinned sources, then
sealed 21 clear and three ambiguous cases. On those clear cases the frozen
ranker finds the correct first paragraph in 20/21, the correct paragraph within
three in 21/21, and an exact literal span among offered alternatives in 19/21.
This is not human verification or a corpus-wide accuracy estimate.

The navigation policy present at label release automatically targeted one of
the ambiguous cases. That failure is retained in the evaluation. A subsequent
development-only safety gate makes inferred prefix hypotheses manual, yielding
9/21 clear-case automatic coverage, 9/9 correct paragraphs, 8/9 exact spans,
and 3/3 ambiguous abstentions on the now-reused sample. Those post-release
figures are explicitly not a new held-out result. OCR-line availability was
measured; exact scan-glyph box accuracy was not.

```sh
python3 vlb/mining/benchmark-v3/validate_fixture.py
python3 vlb/mining/benchmark-v3/validate_annotations.py
python3 vlb/mining/evaluate_v3.py
```

See `output-v3/REPORT.md` and `output-v3/test_labels-evaluation.json` for the
bounded metrics, per-case results, freeze hashes, and disclosure boundaries.
The report's pre-V3 reader comparison comes from the fixed ranking captured in
`benchmark-v3/pre-v3-reader-ranking.json` at recovery commit `b5df369a`; it
does not read the mutable live reader projection.

The separate `correction-regressions/` report follows every latest ledger
revision explicitly approved for regression. Reproduce it with
`node vlb/evaluate_corrections.cjs --write` or verify it with `--check`. It
removes correction overrides, calls the same production target resolver as the
reader, and reports exact-span precision, paragraph recall, coverage,
abstentions, and false-positive automatic targets. It is development evidence,
not a new held-out evaluation, and the initial corrections are not claimed as
human-verified.

## Reproduce

Python 3.10+ and the standard library are sufficient. All inputs are pinned in
the repository. Neither a network connection nor the original large PDF is
required. Run from the repository root:

```sh
python vlb/mine_alignment.py
python vlb/mine_alignment.py --evaluate-only \
  --labels vlb/mining/benchmark/dev_labels.json
python vlb/mine_alignment.py --evaluate-only \
  --labels vlb/mining/benchmark/test_labels.json
```

To keep the committed artifacts untouched while reproducing them:

```sh
python vlb/mine_alignment.py --output /tmp/vlb-mining-rebuild
```

For the comparison with uniform edit costs and the documented prior model:

```sh
python vlb/mine_alignment.py --subset benchmark --model uniform \
  --labels vlb/mining/benchmark/test_labels.json \
  --output /tmp/vlb-mining-uniform
python vlb/mine_alignment.py --subset benchmark --model prior \
  --labels vlb/mining/benchmark/test_labels.json \
  --output /tmp/vlb-mining-prior
```

Labels are read only for evaluation, after prediction generation. They never
enter the seed extractor, spelling learner, or ranker. `--subset dev` and
`--subset test` select preregistered IDs without using their judgments.

Focused verification:

```sh
python -m unittest discover -s tests -p 'test_vlb_orthography.py' -v
python -m unittest discover -s tests -p 'test_vlb_mining_pipeline.py' -v
python vlb/mining/benchmark/validate_fixture.py
python vlb/mining/benchmark/validate_fixture.py \
  --labels vlb/mining/benchmark/test_labels.json
```

The committed full output was rebuilt independently and matched byte-for-byte
for the model, seeds, candidates, headword index, and summary. JSON keys are
stable and gzip timestamps are fixed. The manually recorded freeze and
independent audit are experiment records, not regenerated by the mining command.

## Files and consumers

| File | Purpose |
| --- | --- |
| [output/headword-form-index.json.gz](output/headword-form-index.json.gz) | Compact index by dictionary row and headword; actual historical forms, citation/page IDs, source offsets, proposal status, and OCR line IDs. About 267 KiB. |
| [output/candidates.json.gz](output/candidates.json.gz) | Full audit data, up to three source paragraphs per citation/page, literal spans, competing scores, supplied modern forms, spelling-operation traces, uncertainty, and OCR targets. About 3.53 MiB. |
| [output/orthography-model.json](output/orthography-model.json) | Documented priors and learned observations with support counts and examples. |
| [output/seeds.json.gz](output/seeds.json.gz) | 613 selected silver pairs, preserving source offsets and morphology provenance. |
| [output/summary.json](output/summary.json) | Counts, immutable input hashes, configuration, and the two unresolved citations. |
| [output/model-freeze.json](output/model-freeze.json) | Algorithm, configuration, prediction, model, and fixture hashes frozen before test-label release. |
| [output/test_labels-evaluation.json](output/test_labels-evaluation.json) | Per-case held-out results, separate paragraph and literal-span metrics. |
| [output/independent-test-audit.json](output/independent-test-audit.json) | Independent assistant check, including failure explanations and exclusion checks. |
| [output/ablations](output/ablations) | Reproducible uniform-cost and prior-only comparisons. |
| [benchmark](benchmark) | Preregistered sample, development/test labels, review scope, and fixture validator. |
| [development_evidence.json](development_evidence.json) | 18 source-inspected development examples that informed the priors, separate from evaluation. |

These V1 files are outside the website build's explicit VLB asset allowlist and
add no download to the dictionary or reader. The live V3 integration likewise
keeps its full audit and reverse inventory offline; `build_data.py` copies only
bounded page associations. Every ranked candidate remains distinct from a
reviewed ledger decision.

## Record identity and offsets

The matching unit is `(citation_id, page_id)`, not a bare headword. Homonyms,
several citations in one definition, and different senses on the same page
must remain distinct. `entry_index` identifies a row in the pinned dictionary
snapshot, not a permanent lexical identifier.

Every candidate has a `source_id`, for example `vlb-emerson-r568-p00022`, and an
`attested_span` with the exact historical `text`, `start0`, and `end0`.
The interval is zero-based and half-open in the unchanged, decoded Emerson
snapshot. All characters in this snapshot are BMP characters, but a consumer
should still honor the recorded offset convention instead of assuming byte
offsets. The source number denotes a transcription paragraph, not a physical
printed line.

The source span is always inside the fragment assigned to the cited page.
Estimated page boundaries retain their uncertainty. A paragraph that crosses
pages is searched only within the current page's fragment.

`query_surface` states whether the comparison used the dictionary headword, an
explicit adjective form, a quoted form, or a penalized prefix hypothesis.
Quotation and dictionary offsets retain the literal evidence. Spelling traces
use normalized grapheme offsets within the compared forms; those are different
from the original source-character offsets and are labeled in the model API.

## Ranking and review fields

The shortlisting key is deliberately lossy for recall. It never rewrites a
source or supplies the final spelling score. The final aligner retains marks,
allows documented multigraph correspondences, and records every operation.
The ranker combines that fit with Portuguese heading overlap, companion words
in examples, and a bounded bonus for an explicitly quoted surface. It does not
count the target form itself as independent quotation context.

| Status | Interpretation |
| --- | --- |
| `suggested` | The top result passed frozen similarity, margin, context, and uncertainty gates. Still unreviewed; the test contains a false suggestion. |
| `needs_review` | At least one gate failed, such as a close competitor, short word, unmatched quotation, adapted example, repeated form, or uncertain page boundary. |
| `weak_candidates` | Available ranked passages have weak form and contextual support. |
| `no_candidate` | No usable candidate passage was generated. This does not establish lexical absence. |

All new associations carry `review_status: unreviewed`, and every similarity or
ranking score is explicitly **not a probability**. Existing narrowly reviewed
source IDs are retained separately as provenance and are not broadened.

The source role `post_separator_text` means the text follows the entry dash;
it is not a Tupi language label. Such text can contain Portuguese explanations.
Pure `uide`/`vide` cross-references, common function-word spans, and unclassified
source zones receive review flags.

## OCR targets

The ranker first identifies a literal Emerson span. It then searches the
existing paragraph-to-OCR alignment for that actual historical form. Exact
case-folded matches are preferred; fallback diacritic folding is disclosed.
Token runs cannot cross skipped OCR lines. Repeated occurrences on the same
line retain a count, and the output claims only a unique line set where one
exists.

`form_token_match` identifies OCR lines containing the matched form;
`paragraph_only` retains approximate paragraph boxes when a narrower match is
unavailable; `unavailable` carries no usable OCR region. These statuses describe
location evidence for a candidate, not the correctness of its Navarro linkage.
Boxes are not exact glyph boxes, and scan-line accuracy has not been measured
by the paragraph benchmark.

## Reverse source inventory

`python3 vlb/build_reverse_concordance.py` builds the separate compressed
`reverse-output/source-dictionary-concordance.json.gz`. It starts from all
7,534 source records, inverts the frozen V2 citation proposals, and adds a
bounded search over the pinned dictionary headwords. The reverse inventory is
review material outside the browser payload; it does not alter the frozen
V1/V2 artifacts or treat a matched word as coverage of its source paragraph.
Current recomputed counts, artifact hash, and the exact reproduction command
are recorded in `reverse-output/REPORT.md`.

## Credit

Transcription: **Emerson José Silveira da Costa**, [VLB project][emerson] and
[original Google document][document]. Retain the link to his
[Abanhe'enga “Como aprender tupi” resource page][blog]. The facsimile is the
1952–1953 second edition revised by Carlos Drumond, digitized by Renato Nicolai
and hosted by the [Biblioteca Digital Curt Nimuendajú][facsimile]. Snapshot
hashes and source metadata remain in `vlb/source` and the generated provenance.

[emerson]: https://sites.google.com/site/vocabularionalinguabrasilica/
[document]: https://docs.google.com/document/d/1oNYyk0gHjtP4Rm_Auemt-63DYMXLY9GgFtQ2OE2H6Ek/edit
[blog]: https://abanheenga.blogspot.com/p/como-aprender-tupi.html
[facsimile]: https://www.etnolinguistica.org/biblio:drumond-1952-1953-vlb
