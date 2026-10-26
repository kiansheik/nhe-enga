# Dictionary formatting audit handoff

## Goal

Build a reproducible way to sample the same top-level dictionary `.entry`
elements users see, bias the sample toward long verbetes, qualitatively review
every selected record, and identify bounded formatter changes for a later PR.

## Files inspected

- Required `docs/agent/{index,current-state,repo-map,open-questions}.md`
- `index.html`, `styles.css`, and `js/index.js`
- Served `docs/dict-conjugated.json.gz`
- Existing browser and VM test conventions in `tests/offline/browser_smoke.py`,
  `tests/primary_sources.test.cjs`, and `scripts/data/source_inventory.py`
- Formatter history in commits `f0f3916f`, `76f9c0c4`, `891540ef`, and
  `eb6ddbde`

## Files changed

- `scripts/qa/sample_dictionary_entries.py`
- `docs/agent/dictionary-formatting-audit-2026-10-25.md`
- `docs/agent/current-state.md`
- `docs/agent/repo-map.md`
- `docs/agent/log.md`
- This handoff

No production JavaScript, CSS, dictionary data, generated artifact, morphology
code, ground truth, or deployment branch was changed.

## Commands run

- Targeted `rg`, `git log`, `git show`, gzip/JSON inspection, and line-numbered
  reads of the formatter and renderer
- `.venv/bin/python -m py_compile scripts/qa/sample_dictionary_entries.py`
- `black --check scripts/qa/sample_dictionary_entries.py`
- Two identical real-Chromium sampler runs using:

  ```sh
  .venv/bin/python scripts/qa/sample_dictionary_entries.py \
    --seed format-audit-2026-10-25 \
    --sample-size 24 \
    --longest-percent 10 \
    --include-index 9405 \
    --output /tmp/nhe-enga-entry-sample.json \
    --gallery /tmp/nhe-enga-entry-sample.html
  ```

- A screenshot run adding
  `--screenshots /tmp/nhe-enga-entry-screenshots`
- SHA-256 and byte comparison of the repeated JSON/gallery outputs
- Full production-formatter scan of all 8,293 Tupi–Portuguese records
- `git diff --check`

## What worked

- The sampler reads the real served gzip, deterministically selects from the
  longest-entry pool, intercepts only the dictionary payload to isolate the
  chosen source records, and exercises the production search, formatter,
  citation linker, highlighter, browser parser, and CSS.
- Repeated runs selected the same 25 records and produced byte-identical JSON
  and HTML gallery output after omitting unrelated hidden conjugation controls.
  Their SHA-256 values are `68d027fc...f7ecfb` and
  `1b022522...1e0133`, respectively.
- The reviewed sample found 16 coherent entries and nine boundary defects:
  `ranhẽ²`, `pupé`, `-'ĩ²`, `-ne³`, `îoesé`, `kakuab¹`, `ambyasy`,
  `(e)mbetara`, and `moanhẽ`.
- The reported bolding was localized exactly: generated `Advérbio:` or
  `Adjetivo:` markup is reparsed, its colon wins over the real example colon,
  and the browser repairs the malformed nesting under the bold title.
- The exact signature occurs 274 times in 270 records (178 adverb and 96
  adjective occurrences). Empty `.quote-tupi` has the same exact count and no
  occurrence outside this defect.

## What failed

- The sandbox initially denied binding the loopback audit server. The approved
  loopback/headless-Chromium run succeeded.
- Automatic DOM flags caught only `ranhẽ²` and `ambyasy`. Seven other defects
  are valid HTML but semantically wrong, confirming that detectors cannot
  replace comparison with the raw definition.
- Initial output included random conjugation-control IDs and was not
  byte-identical. Removing those hidden, out-of-scope controls from the saved
  clone made repeated captures deterministic while leaving the live rendering
  path intact.

## Remaining questions

- Whether the first implementation PR should contain only the generated-title
  and square-bracket fixes, or also the broader adjacent-pair and compact-dash
  heuristics. The audit recommends the smaller first slice.
- Whether highlighting should remain global across definition/example text.
  It is working as currently designed and is independent of the bolding bug.
- Some source records omit semicolons between examples. Their UI repair should
  be based on conservative citation/pair boundaries, not dictionary rewrites.

## Suggested next prompt

“Implement the first formatting PR slice: protect generated Adjetivo/Advérbio
headings and square-bracket notes from quote parsing, add the `ranhẽ²` and
`kakuab¹` regressions plus corpus DOM invariants, and show the before/after
impact without changing dictionary data.”
