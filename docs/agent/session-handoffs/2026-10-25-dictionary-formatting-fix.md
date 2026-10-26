# Dictionary formatting repair handoff

## Goal

Repair the autoformatter defects identified by the long-entry audit, verify the
result across the complete served dictionary, and package the change as a
reviewable pull request without changing linguistic data.

## Files inspected

- Required `docs/agent/{index,current-state,repo-map,open-questions}.md`
- `js/index.js`, `styles.css`, and `index.html`
- Served `docs/dict-conjugated.json.gz`
- `tests/primary_sources.test.cjs`, `tests/dictionary_apostrophes.test.cjs`,
  and the offline browser-test conventions
- All records surfaced by the deterministic sampler, corpus heuristics, and
  repeated real-Chromium sweeps

## Files changed

- `js/index.js`
- `styles.css`
- `scripts/qa/sample_dictionary_entries.py`
- `tests/dictionary_formatting.test.cjs`
- `tests/dictionary_formatting_browser.py`
- `.github/workflows/dictionary-formatting.yml`
- `docs/agent/dictionary-formatting-audit-2026-10-25.md`
- `docs/agent/{current-state,repo-map,log}.md`
- The audit handoff and this handoff

The compressed dictionary, generated assets, morphology engine, and ground
truth were not modified.

## Commands run

- Targeted `rg`, `git diff`, `git log`, gzip/JSON inspection, and formatter
  debug runs
- `node --check js/index.js`
- `node --test tests/dictionary_formatting.test.cjs`
- `node --test tests/dictionary_formatting.test.cjs tests/primary_sources.test.cjs tests/dictionary_apostrophes.test.cjs`
- `.venv/bin/python -m py_compile scripts/qa/sample_dictionary_entries.py tests/dictionary_formatting_browser.py`
- `.venv/bin/python tests/dictionary_formatting_browser.py`
- `black tests/dictionary_formatting_browser.py scripts/qa/sample_dictionary_entries.py`
- `make lint`
- Multiple corpus-wide real-Chromium audit sweeps, with the final persisted
  sweep covering all 8,293 Tupi–Portuguese records
- A final 31-entry sampler run with screenshots under `/tmp`
- `git diff --check`

## What worked

- The original `ranhẽ²` heading bug and all 274 occurrences of its exact
  signature now produce valid sibling title, definition, and quote elements.
- Conservative parsing repairs compact dashes, missing delimiters, adjacent
  cited pairs, shared citations/translations, malformed brackets, dialogues,
  editorial leads/tails, annotated grammatical preambles, Unicode related
  headwords, and inline gloss variants. Separately cited source variants retain
  the visible `ou` that connects them.
- Related-entry lemmas and glosses remain clickable prose while genuine cited
  examples remain bilingual cards. The two dash-leading related heads in the
  corpus, `-sûerĩ` and `-te nakó`, retain their morphological hyphens.
- The final full-corpus Chromium sweep reported zero credible structural or
  semantic defects. The two Portuguese-only cards at indices 6248 and 9091
  were reviewed and retained as intentional prose quotations. Its temporary
  JSON evidence has SHA-256 `b55390ff9c1553c67e526a23c578bf5042677d5f861a29f23b0c7b88f0f259bd`
  and records the unchanged formatter SHA-256
  `00eeea510cbc8ad1b1a27ee42edc888136b878b060425ab64ad5eae1b6ac8442`.
- The dependency-free corpus suite also proves that every lexical source token
  remains visible after formatting, guarding against silent prose loss.
- The maintained browser suite passes 53/53 tests; the combined Node suite
  passes 22/22; Black and JavaScript syntax checks pass.
- The sticky footer reaches the viewport bottom on the short initial page and
  stays below the document-flow content for expanded long entries.
- The final deterministic sample captured 31 long/sentinel entries with zero
  warnings, and every screenshot was reviewed as visually coherent.

## What failed

- The sandbox initially blocked the sampler's temporary loopback server; the
  approved localhost Chromium run succeeded.
- One newly added Python fixture initially used an unescaped apostrophe; it was
  corrected before the maintained browser suite ran.
- Two older browser expectations described the buggy grouping for
  `marangoty?` and `tĩ⁴`; both were updated to assert the improved semantic
  boundaries.
- The first final corpus sweep found one remaining shared-translation variant
  at `na`; the formatter was corrected and the second complete sweep passed.
- A separate final code review found that two dash-leading related suffixes
  could lose their hyphen and become cards. Their recognizer and browser
  regressions were corrected, and another complete Chromium sweep passed.
- The annotated-prefix fallback initially consumed six top-level `1)` sense
  markers and one well-formed bracketed label. Depth-aware number and bracket
  guards restored those controls; the fallback now changes exactly the 30
  intended corpus records.
- The full-corpus token audit caught a dropped literal `ou` between the two
  source variants of `tĩ⁴`; a visible separator and browser regression fixed
  it.
- Making the footer merely static removed overlap but left it mid-page on
  short views. The final flex ordering accounts for the dynamically appended
  offline link and is covered by real geometry assertions.

## Remaining questions

- No formatter or test blocker remains. The pull-request CI result and remote
  review status should be checked after the branch is pushed.
- Deployment is intentionally outside this handoff; merge and Pages deployment
  are separate actions.

## Suggested next prompt

“Review and merge the dictionary-formatting PR after CI passes, then deploy the
Pages build and verify `ranhẽ²`, `kanga³`, and `na` in the live browser.”
