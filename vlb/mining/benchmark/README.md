# Independent VLB alignment evaluation fixture

This fixture evaluates **a particular Navarro citation occurrence on its cited printed page against a literal form in Emerson's transcription**. It was reviewed by an assistant; it is not a human-verified philological gold standard.

## Files and separation

- `preregistered_sample.json` records the selected citation/page IDs, selection seed, source hashes, normalized headwords, and development/test assignments. It also provides every excluded headword and printed page for training.
- `dev_labels.json` contains 20 development cases. It may inform implementation and threshold decisions, but its literal pairs must not become learned spelling-rule seeds.
- `test_labels.json` contains 28 frozen test cases, released after the candidate-generation rules, scoring, thresholds, and predictions were frozen on 2026-11-03 at 02:36:23 UTC. Its original annotation hash is unchanged.
- `evaluation_labels.json` is the combined annotation workfile. Do not load it while developing the matcher.
- `review_material.json` preserves the supplied context and complete cited-page fragments used for manual review, without baseline candidate rankings or future model output.
- `select.cjs`, `split.py`, and `annotate.py` document selection and annotation. `validate_fixture.py` checks the completed fixture against the pinned local data.

The original 48-case sample was registered before reviewing passages. A later, label-independent development/test split was registered after the first 16 passages had been inspected, and before any new matcher output had been viewed. This timing is disclosed in the preregistration. The split code reads selection metadata only, not annotation outcomes.

The release follows the protocol recorded in `freeze.json`; `../output/model-freeze.json` records the model and prediction hashes before release. `../output/independent-test-audit.json` records a separate assistant check of the frozen results, exact-span scores, failure explanations, hash verification, and training exclusions. Test labels were not revised after predictions were inspected, and the matcher was not retuned for that audit. These released cases must not be represented as unseen tests for future changes developed from their results.

## Validate a released fixture

From the repository root, run:

```sh
python vlb/mining/benchmark/validate_fixture.py
```

The default reads **only `dev_labels.json`**, although test labels are now released. The repository root is inferred from the script's location, so invoking the script by its absolute path also works from another directory. An optional positional repository path overrides that location.

To validate a specific released file, use `--labels`:

```sh
python vlb/mining/benchmark/validate_fixture.py --labels vlb/mining/benchmark/dev_labels.json
```

Relative `--labels` paths are resolved from the current working directory. The validator uses the file's declared development/test split; an explicit `--split` must agree. A combined file without a declared split requires `--split all`. Use `--split test` to select the released `test_labels.json` explicitly. Validation checks the pinned dictionary and transcription hashes, preregistered case IDs, citation/page membership, and exact literal offsets without loading matcher predictions.

## Sampling

The sample has eight citation/page cases in each cell of volume I/II crossed with three statuses from the old viewer heuristic: automatic baseline target, unresolved candidate set, and no candidate. Each cell prioritizes one adapted citation, two short headwords, and two long headwords, then fills its quota by a fixed SHA256 ordering. Headwords are unique across the sample. Headwords involved in the previous exploratory pilot and printed pages I-17 and I-18 are excluded.

The 20 development cases use cell quotas 3/3/4 for volume I and 3/4/3 for volume II. The remaining 28 are test cases. Connected cases sharing a normalized headword **or a printed page** stay in the same partition. There are 45 distinct held-out printed pages.

Exclude all 48 sampled headwords and all 45 pages from spelling-rule seed training. `holdout_source_ids` also lists every paragraph represented on those pages, including paragraphs whose continuation appears on an adjacent page. Filter by these IDs to prevent a split paragraph from entering training through its other page fragment. For headword grouping, normalization means lowercase, Unicode NFD decomposition, removal of combining marks, and retention of letters only. Do not treat the fixture's old baseline stratum as a gold label.

Because difficulty strata and word lengths are deliberately balanced, an overall percentage on this fixture is not an unbiased estimate of coverage or precision across all VLB citations. Report volume/stratum counts alongside any aggregate.

## Labels and evidence

Each case retains citation ID, page ID, dictionary row and homonym, source paragraph IDs, literal historical forms, global source offsets, offsets within the page fragment, citation context, and a short explanation relating the form to the Portuguese gloss or example. Original spelling is preserved. A literal form may be a conjugated predicate, compound, or example phrase rather than the dictionary's bare headword.

The statuses mean:

| Status | Meaning | Evaluation use |
| --- | --- | --- |
| `clear` | The assistant identifies a particular paragraph and literal form corresponding to this citation. | Positive paragraph-ranking label. Multiple literal variants in the same paragraph can be acceptable. |
| `ambiguous` | More than one location is plausible, or the page only supports a related parent lemma. | Evaluate uncertainty handling separately; do not silently count it as a confirmed unique positive. |
| `not_found` | A correspondence was not identified on the complete cited page. | A page-specific unresolved case, not evidence of absence from the VLB. |

`source_line` is Emerson's paragraph number. It is **not a physical printed or OCR line number**. This benchmark does not establish scan bounding-box accuracy. Character offsets are zero-based, half-open Unicode code-point intervals in the saved source snapshot; the current source contains BMP characters, so these also agree with JavaScript string offsets.

The review distinguishes common traps: a short lemma appearing inside a specific cited compound; neighboring noun and predicate entries; a repeated form under two Portuguese headings; a quotation continued from the previous page; and an apparent page-reference mismatch. A paragraph correspondence does not validate all modern glosses, etymologies, or morphological claims in the dictionary.

## Suggested evaluation

Freeze the model configuration before opening the test file and record its hash. Evaluate paragraph top-one accuracy and candidate recall at a specified rank on `clear` test cases. A prediction is paragraph-correct if its source ID matches the case's accepted source ID. Check literal form spans separately; this is stricter than identifying the right paragraph and should not be conflated with paragraph accuracy.

For automatic links, report both the count/coverage of decisions and accuracy among decisions. Include counts, not only percentages. Analyze `ambiguous` and `not_found` cases separately as uncertainty cases, and retain their evidence when interpreting whether an automatic link was justified. A high heuristic score is not a calibrated probability.

Do not revise gold labels merely to agree with predictions. Any post-freeze correction requires an explicit evidence-based annotation change and a new fixture version.
