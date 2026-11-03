# VLB citation mining V2: frozen review proposals

The V2 ranker improves citation-specific examples, compounds, postpositions and
repeated occurrences while preserving original dictionary and transcription
text. All new results remain **unreviewed proposals**. The fresh evaluation
still contains a wrong high-scoring suggestion, so these outputs do not justify
automatic acceptance or a claim of 100% accurate coverage.

## Frozen experiment

The algorithm, configuration and all 6,164 predictions were frozen at
**2026-11-03 03:08:51 UTC**, before the implementation agent received the fresh
test labels. [model-freeze.json](model-freeze.json) records their hashes.
The fresh 24-case annotation was sealed independently at 03:05:33 UTC, with
SHA256 `6e7a04b9e44d432edd574cc516d7cdb17285ac7d003fba46696efa7cbad3645b`.
See the [annotation freeze](../benchmark-v2/annotation-freeze.json) and
[registered sample](../benchmark-v2/preregistered_sample.json).

The 48 previously released V1 cases were used as development regressions. The
24 new cases were not inspected while implementing or tuning V2. The frozen
model uses the documented spelling **priors**, with no learned silver weights.
V1's learned observations had shown no held-out gain over those priors.

The 540 silver records are retained as an audit artifact. The registered
exclusions contain 72 headwords, 69 printed pages and 2,048 source paragraphs.
There is no page or paragraph overlap. A stricter audit did identify **five
unused silver records for `'anga`** that survive the preregistration's normalized
`anga` exclusion: the legacy seed selector preserves phonological marks while
the benchmark grouping folds them. The chosen prior model uses none of these
observations, so this discrepancy does not affect its frozen predictions or
test metrics. A future learned-model run must correct the normalization first;
this experiment must not be described as having zero headword overlap in its
unused silver artifact. Exact affected records appear in the metric audit.

No parameter, label, or ranker code was changed after fresh test release. Review
ledger decisions were not applied to model predictions during evaluation.

## What changed

- Parse literal examples before translation separators, including parenthesized
  and slash-separated alternatives. Keep optional argument spans and parse
  failures visible instead of silently discarding examples with parentheses.
- Admit complete explicit compounds independently of lemma length. Keep
  literal citation offsets and bounded morphological search hypotheses
  separate. The existing entry-label prefix hypotheses can also apply to a
  quoted compound, with their own review flag; no morphology engine was changed.
- Match ordered companion words on the appropriate side of an exact source
  occurrence. Postpositions and nearby example words can disambiguate adjacent
  constructions and repeated tokens.
- Preserve up to three additional exact `span_alternatives` per paragraph.
  `candidates` still contains at most three distinct paragraphs, and each
  paragraph's best span remains in the existing fields. Alternatives have the
  same evidence fields without recursive alternatives.
- Retain stronger review reasons for partial quotation parsing, incomplete
  local construction evidence and speculative compound prefixes. Tiny lemmas
  matching common Portuguese or grammatical tokens receive a larger penalty.
- Default the CLI to `output-v2` and the V2 preregistration; refuse writes to
  the frozen V1 output directory. `--freeze` records code/config/output hashes
  for a full run before labels are supplied.

These are bounded retrieval heuristics, not full syntactic or morphological
analysis. Search surfaces have at most four words and 80 characters; local
companion matching considers up to eight neighboring tokens within 90
characters. Unresolved shared material in parenthesized alternatives remains
flagged for review. Scores are not probabilities.

## Complete processing inventory

| Inventory | Count |
| --- | ---: |
| Valid citation/page memberships processed | 6,164 |
| `suggested`, still unreviewed | 3,201 |
| `needs_review` | 2,888 |
| `weak_candidates` | 73 |
| `no_candidate` | 2 |
| Records with a recorded quotation parse issue | 78 |
| Saved best/alternative literal spans validated against source and page | 39,406 |
| First candidate with narrowed form-token OCR lines | 5,297 |
| First candidate with approximate paragraph OCR only | 848 |
| First candidate without usable OCR evidence | 17 |

The two no-candidate records are `Cupim,` on I-142 and `y` on I-154. The two
original malformed citation locators are also retained separately in the
summary. Processing and OCR availability counts do not establish correct
lexical or citation alignment. The full run took approximately 67 seconds of
ranking in this environment.

## Fresh held-out evaluation

The independent assistant annotation identifies 22 clear cases, one ambiguous
case and one case whose cited sense was not found. It is **not human verified**
and the deliberately balanced sample does not estimate corpus-wide accuracy.

| Measure | V2 frozen result |
| --- | ---: |
| Correct first paragraph, clear cases | 21/22 (95.5%) |
| Correct paragraph among first three, clear cases | 21/22 (95.5%) |
| Exact first literal span, clear cases | 20/22 (90.9%) |
| Exact best-per-paragraph span among first three | 20/22 (90.9%) |
| Exact span among all offered alternatives | 21/22 (95.5%) |
| Suggested decisions across all cases | 16/24 |
| Suggested decisions supported as clear/correct | 15/16 |
| Ambiguous or not-found cases incorrectly suggested | 1/2 |

The saved old viewer ranking identifies 9/22 paragraphs first and 14/22 within
its top three on these same labels. This is the old viewer ranking, not the V1
miner's score or the separate reader automatic-target policy.

The `suggested_correct: 15` and `suggested_clear_cases: 15` evaluator fields
must not be quoted as perfect overall suggestion precision: there is also a
suggested `not_found` case. The complete denominator is **16 suggestions**.
The [evaluation JSON](test_labels-evaluation.json) and
[direct metric recomputation](frozen-evaluation-audit.json) preserve all cases.

### Remaining fresh failures

| Citation | Frozen behavior | Independent annotation and consequence |
| --- | --- | --- |
| `esé`, II-82; quoted `mba'e resé?` | Ranks several standalone `rece` passages; the correct paragraph is absent from the top three. The decision is `needs_review`. | The source question is `Baerecepe` in paragraph 5968. Fused grammatical constructions and changed interrogative surface remain a retrieval gap. |
| `'ybapekanga`, II-62 | Marks `Gigbapecanga` in paragraph 5464 as `suggested`, based on spelling, without supporting sense evidence. | Navarro cites the botanical salsaparrilha/japecanga sense; this source passage concerns an animal bone. A long close spelling is insufficient to establish the cited sense. |
| `ikó`, I-99 | Finds the correct paragraph and later occurrence, selecting `Naicoŷ cece`. | The exact quoted expression is `Naicoŷ cece coigte`. It is preserved as a span alternative; the best span is incomplete. |
| `aembé`, I-83 | Retains competing noun/predicate passages under `needs_review`. | The independent annotation is ambiguous between `Çaẽbê` and `Xeraembê`; the model appropriately does not assert a unique verified answer. |

These cases were not patched into this frozen model. Future work should treat
them as development evidence and use a new independent sample before claiming
another accuracy gain. In particular, negative sense evidence and complete
construction matching deserve attention before increasing automatic coverage.

## Released V1 development regressions

Across the 48 already known V1 cases, 44 are clear. V2 retrieves all **44/44**
paragraphs first, gets **43/44** exact first spans, and offers all **44/44** exact
spans among alternatives. The remaining first-span difference is `sosé`: V2
selects the correct later `çoce` occurrence and offers the full `Uinte çoce`
phrase as an alternative. All 23 suggested development cases are paragraph
correct; the three ambiguous cases and one not-found case are not suggested.

These are development/regression results, not new independent validation.
The two evaluation files are explicitly named
`released-v1-dev_labels-as-development.json` and
`released-v1-test_labels-as-development.json`.

## Validation and reproduction

Twenty focused tests pass: the seven existing pipeline checks and thirteen new
quotation, occurrence, source-offset and released-failure regressions. Python
syntax and whitespace checks pass. Every one of the 39,406 saved literal spans
was separately checked against the unchanged transcription and current page
fragment. All frozen code/output hashes and held-out seed exclusions were
checked after test release.

From the repository root:

```sh
python -m unittest discover -s tests -p 'test_vlb_mining*.py'
python vlb/mine_alignment.py --output /tmp/vlb-v2-rebuild --freeze
python vlb/mine_alignment.py --output /tmp/vlb-v2-rebuild --evaluate-only --labels vlb/mining/benchmark-v2/test_labels.json
```

The frozen V1 outputs and labels remain unchanged. Reproduce the original V1
algorithm from repository commit `0d55ca9e6ef0cd060068ae1b0547882a5f1bf22d`;
the current `pipeline.py` and CLI now implement V2. Physical printed-line or
glyph-box accuracy remains unmeasured by this text benchmark. Emerson's
transcription, its attribution, and the scan provenance remain unchanged.
