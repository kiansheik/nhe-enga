# Annotation accountability applied locally

## Goal

Repair Araújo 73's annotation breakdown without changing its authored analysis,
and enforce occurrence, construction-scope and stored-tree integrity during PDF
generation. The reviewed 12-file repair is now applied to the active Nhe'enga
checkout; do not reapply it. Work remains local and uncommitted.

## Files inspected

Agent instructions/index/state/map/questions/grammar-navigation; `Predicate.emit`,
`hierarchical_representation_v4`, `EvalCtx`, nominalization and conjunction
realization; low-level phonetic/nominal handling; Araújo 73/79 and all 144 current
expressions; corpus dictionary traversal, historic tests and ground-truth
verifier; LaTeX generator, snapshot validator and generated maps.

## Files changed

- `pydicate/pydicate/{predicate,annotation_audit}.py` and
  `pydicate/pydicate/lang/tupilang/pos/{noun,verb}.py`.
- `tupi/tupi/tupi.py` and three focused suites:
  `test_annotation_occurrences.py`, `test_annotation_audit.py`,
  `test_nominal_annotation_preservation.py`.
- Agent state, log, grammar navigation and this handoff.

The coordinating LaTeX changes integrate the live/offline gate and improve the
rendered breakdown. The author's prior dirty `deverbal.py` is preserved by hash;
source expressions, targets, saved records, lexical definitions and crops remain
unchanged. Application evidence: `../latex/build/annotation-accountability/apply-manifest.json`.

## Commands run and results

- Engine `python -m unittest discover -s pydicate/tests -p 'test_*.py'`:
  **60 tests pass** on the applied checkout.
- Corpus `tests/run_tests.py --skip-tokenizer`, in separate original/candidate
  processes with explicit engine `PYTHONPATH`, disabled bytecode and the existing
  Nhe'enga virtualenv: **102 tests each; the same one Araújo 55 failure**.
- Corpus `python -m authoring.ground_truth_cli verify --json`: original and applied
  outputs are identical; Araújo has a pre-existing source/JSONL metadata difference
  at record 2, and Bettendorff passes 40 generated/40 rendered records.
- All 144 executable historic expressions: ordinary outputs remain byte-identical
  to the captured baseline. The baseline reconstruction verifies four original
  files against their pre-change hashes and preserves the dirty deverbal module.
- Coordinating LaTeX verification: **179 pipeline tests pass**; `make corpus-pdf`
  and `make review-pdfs` build/deliver **400/98/79 pages**. Two independent bounded
  round22 rechecks found no blocker in the repair scope; successful builds and
  these agent perspectives do not establish linguistic correctness.

Evidence is under `../latex/build/annotation-accountability/`: the combined
`historic-validation-comparison.json`, `baseline-engine-provenance.json`,
`nominal-corpus-compare.json`, `preservation.json`, `pipeline-tests-final.log` and
`review-pdfs.log`. Saved audit metrics are in the schema-3 LaTeX generated manifest.

## What worked

The gate rejects tag loss/addition, cross-occurrence contamination, malformed
tags, missing source/construction paths and fabricated references or metrics.
Both live generation and offline snapshot validation enforce it. Complete stored
paths include wrappers, adjuncts, compositions, nominalization sources and finite
principal backlinks; legacy dictionary hierarchy numbering is unchanged.

The current audit has 1,504 pieces, 3,218 tags, 1,929 stored paths and 1,047
evaluation events, with no unsupported Predicate relations. Witness categories
remain explicit: 602 tags have a unique matching child event, 1,962 have ambiguous
child witnesses and 654 have root-output evidence only. Six events lack a stored
node candidate and 385 have ambiguous candidates. These are reporting limits,
not proof that every annotation has a uniquely verified linguistic origin.

Nominalization preserves annotations for all argument modes while retaining the
legacy spelling distinction between False/default and explicit True. Proper-name
protection covers adjacent and colon-combined annotation groups. The literal
lexical name Santa Madre Igreja remains distinct from a newly flattened verbal
construction.

## What failed and was repaired

Regressions first reproduced nominal annotation loss and two proper-name
protection gaps. Full-graph review exposed omitted relation fields/backlinks and
Predicate references hidden inside containers; the guard now covers them and
rejects unknown nested relations. An overbroad multiword-root rule was corrected
using exact stored lexical evidence. The first full-suite interpreter lacked
`lxml`; the existing Nhe'enga virtualenv resolved that dependency without install.

Existing Araújo 55 rendering and record-2 metadata failures remain unchanged.
No ground truth was regenerated to conceal them. Black was unavailable in the
qualification interpreter; syntax, focused tests and integrated checks passed.

## Remaining questions

Structural integrity is not linguistic adjudication. Ordinary/annotated outputs
still differ in 25 records exactly and six after whitespace normalization; these
unchanged differences remain visible. Root-only/ambiguous witnesses require
further producer-level investigation before claiming stronger semantic origins.
The final doctoral SHA256 is
`109e465ed9985cc2f5fe654fe72dd87280fa7285202107a7ffd0494a097c3b08`.
Review confirmed the A73 display and found an unrelated A79 source crop; a separate
exact export exclusion preserves that saved region while the PDF states the gap.
No source interpretation, historic spelling or dictionary meaning has been newly
approved by these mechanical checks.

## Suggested next prompt

Review the applied annotation repair and round22 PDF findings. If authorized,
inspect the remaining ambiguous and root-only annotation origins using their
stored paths and evaluation events; add producer-level evidence and focused
regressions without changing source analyses or hiding unresolved distinctions.
Preserve the author's current edits and keep work local. Do not reapply the patch.
