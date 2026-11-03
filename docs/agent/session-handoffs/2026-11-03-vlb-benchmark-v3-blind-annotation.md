# VLB benchmark V3 blind assistant annotation

## Goal

Independently annotate the frozen 24-case V3 review packet while preserving
blindness to mining outputs, rankings, implementation details, and prior
predictions or evaluations. Record exact global half-open source spans, freeze
the artifacts by hash, and leave uncertainty explicit.

## Files inspected

- `docs/agent/index.md`
- `docs/agent/current-state.md`
- `docs/agent/repo-map.md`
- `docs/agent/open-questions.md`
- `docs/agent/log.md`
- `vlb/mining/benchmark-v3/review_material.json`
- `vlb/source/emerson_vlb.txt`
- `docs/dict-conjugated.json.gz`, limited to the 24 pinned dictionary rows and
  their cited sense context

No mining output directory, including `output-v3`, was inspected. Neither
`pipeline.py`, model code, candidate rankings, a form index, a model freeze,
nor any prior prediction/evaluation file was read.

## Files changed

- `vlb/mining/benchmark-v3/test_labels.json`
- `vlb/mining/benchmark-v3/annotation-freeze.json`
- `vlb/mining/benchmark-v3/validate_annotations.py`
- `docs/agent/current-state.md`
- `docs/agent/log.md`
- `docs/agent/session-handoffs/2026-11-03-vlb-benchmark-v3-blind-annotation.md`

## Commands run

- Targeted `jq` reads of packet metadata, citation context, and supplied page
  fragments
- `shasum -a 256` for the packet, pinned source, dictionary, and labels
- Targeted `gzip -dc ... | jq ...` reads of the 24 pinned dictionary rows
- A read-only Python Unicode-offset check against the pinned Emerson text
- `python3 vlb/mining/benchmark-v3/validate_annotations.py`
- `python3 -m json.tool` on both JSON artifacts
- `python3 -m py_compile` on the validator; its generated `__pycache__` was
  moved out of the checkout to `/tmp/nhe-enga-v3-validator-pycache-20261103-1519`

## What worked

- All 24 packet cases received exactly one status in packet order: 21 clear,
  three ambiguous, and zero not-found.
- Clear and ambiguous cases contain 27 defensible targets total. Every
  `form_start0:form_end0` slice exactly equals `form_text` in the checksum-pinned
  Emerson source and falls inside the named packet fragment.
- The ambiguous labels preserve three bounded problems instead of resolving
  them speculatively: `enena` versus source `Enẽma` plus unsupported taxonomy;
  the unsupported second sense of `moapyr`; and the specific river-boa claim
  not established by source `Drago, ou dragão` for `Giboyuçû`.
- The freeze records packet SHA-256
  `a64adf5225b2477773089c4b9543c1c92b070475d44c341831e3e2cfc0ba1d31`
  and labels SHA-256
  `ab73a469e445b722a4f55479daf513731a13b1d7cb5a30ec7988439eff422685`.
- The standalone validator passes and imports nothing from the mining
  implementation.

## What failed

Nothing failed. No ranking or evaluation metrics were computed because doing
so before the annotation freeze would have broken the requested blindness.

## Remaining questions

- A human editor still needs to review the three ambiguous cases; all current
  labels deliberately say `human_verified: false`.
- A human may also wish to decide whether the broader coercive glosses for
  `gûebirãîari` go beyond the source's explicit `pollos cabelos` wording. The
  source association itself was labeled clear because its form, adverb label,
  example, and situational note align.
- Any comparison with rankings or prediction/evaluation artifacts must happen
  only after accepting this hash-pinned freeze as the blind assistant review.

## Suggested next prompt

Review the three ambiguous V3 labels against only the frozen packet and pinned
source as a human editor, record any human decisions separately, then accept
the annotation freeze before running a post-freeze evaluator against model
rankings.
