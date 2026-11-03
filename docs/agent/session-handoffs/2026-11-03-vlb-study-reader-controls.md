# VLB study-reader controls and source-only search

## Goal

Refine the deployed unified VLB reader on phone and desktop: remove the
per-line OCR-reading disclosure, replace the unusable mixed dictionary search
with source-only VLB retrieval, collapse mobile search and navigation chrome,
let either study pane minimize and resize, support pinch zoom and persistent
view preferences, and retain one explicit share action. Plain transcript and
facsimile line clicks must remain tied, navigation-only actions; Navarro detail
must require an explicit request.

## Files inspected

- `docs/agent/index.md`, `current-state.md`, `repo-map.md`,
  `open-questions.md`, and the November 2–3 VLB handoffs
- `vlb/index.html`, `vlb/styles.css`, `vlb/app.js`, `vlb/search.js`,
  `vlb/README.md`, and representative generated source/page data
- `vlb/build_data.py`, `vlb/mining/orthography.py`, and the frozen
  `vlb/mining/output-v3/orthography-model.json`
- `scripts/build_pages.sh`, `.github/workflows/dictionary-formatting.yml`,
  and the VLB Python, Node, and browser regressions
- Final Chrome captures and result data under
  `/tmp/vlb-study-reader-final-browser/`

## Files changed

- Reader and search: `vlb/index.html`, `vlb/styles.css`, `vlb/app.js`, and new
  `vlb/search.js`
- Projection: `vlb/build_data.py`, `vlb/data/manifest.json`, new
  `vlb/data/orthography-model.json`, and the manifest-hash-only refresh in
  `vlb/mining/correction-regressions/evaluation.json`
- Tests and integration: new `tests/vlb_search.test.cjs`,
  `tests/test_vlb_viewer_data.py`, `tests/vlb_viewer_browser.cjs`,
  `scripts/build_pages.sh`, and `.github/workflows/dictionary-formatting.yml`
- Documentation: `README.md`, `vlb/README.md`, `docs/agent/repo-map.md`,
  `docs/agent/current-state.md`, `docs/agent/log.md`, and this handoff

## Commands run

- `python3 vlb/build_data.py`
- `python3 tests/test_vlb_citation_inventory.py`
- `python3 tests/test_vlb_viewer_data.py`
- `python3 -m unittest discover -s tests -p 'test_vlb_orthography.py' -v`
- `python3 -m unittest discover -s tests -p 'test_vlb_mining*.py' -v`
- `python3 -m unittest tests.test_vlb_reverse_concordance -v`
- `python3 -m unittest tests.test_vlb_corrections -v`
- `node --test tests/vlb_search.test.cjs`
- `node --check vlb/app.js`, `node --check vlb/search.js`, and
  `node --check tests/vlb_viewer_browser.cjs`
- `node vlb/evaluate_corrections.cjs --check`
- `VLB_PLAYWRIGHT_MODULE=/Users/kian/code/pydicate-studio/node_modules/playwright VLB_CHROMIUM_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' VLB_QA_DIR=/tmp/vlb-study-reader-final-browser node tests/vlb_viewer_browser.cjs`
- `PAGES_BUILD_DIR=/tmp/nhe-pages-vlb-study-reader make pages-build`
- `cmp` and `shasum -a 256` checks for emitted VLB JavaScript, CSS, manifest,
  and orthography-model assets
- `git diff --check`

## What worked

- Search builds only from the VLB source index and never fetches the legacy
  Navarro citation index. NFC/case normalization retains diacritics and
  nasalization. Literal whole words or phrases sort before the same exact
  spelling inside a longer token. At the same scope, entry-head matches sort
  first, then VLB-side before Portuguese-side matches, with stable line ties.
- `biã` returns §4770 (`Mas ... — Biã.`) first, then exactly §1039, §3134, and
  §5140 as inside-word matches. Portuguese query `era`, continuation phrase
  `Cetigmã cangupiara`, and the bounded Navarro spelling `akyrara` have focused
  navigation regressions.
- The served orthography model is copied byte for byte from the frozen V3
  artifact and hash-pinned in the manifest. Its directional edit costs add only
  bounded, visibly probable retrieval results after literal matches. The UI and
  docs state that costs are neither probabilities nor lexical-identity claims;
  no unsupported general alias system was invented.
- At narrow widths search collapses behind a 34 px magnifier and page/options
  controls share one low-profile row. The facsimile defaults to the larger
  upper area and the transcription to roughly the lower third. Either pane can
  minimize, but the reader prevents both from being minimized at once.
- The accessible separator supports pointer drag, keyboard arrows/Home/End,
  mobile horizontal and desktop vertical orientation, ARIA values, and a
  double-click reset. Mobile and desktop proportions persist across reloads.
- Two-touch gestures zoom from 100% through the same bounded 100–400% scale as
  the buttons, preserve the gesture midpoint, suppress the synthetic follow-up
  click, and save zoom when the gesture ends. Source selection centers the
  union of its OCR boxes at the active zoom. Restoring either minimized pane
  recenters its selected line, including in continuous mode.
- Guarded localStorage restores zoom, mobile/desktop split, minimized pane,
  OCR highlight visibility, and reading mode without allowing corrupt data or
  an impossible both-minimized state to break the reader. Selection may
  temporarily restore a pane without overwriting the reader's saved preference.
- Transcript-line and facsimile-line clicks navigate, select, highlight, and
  center only. Navarro starts empty, is scoped to the selected line, and its
  large detail requires an explicit headword click. The obsolete **Ver leitura
  OCR** disclosure is absent.
- A selected line exposes only **Compartilhar**. Native Web Share receives the
  line, VLB volume/page/paragraph citation, and compact page-plus-line URL;
  unsupported sharing copies the complete block, and clipboard denial opens a
  prompt for manual copy. Opening the compact link restores and centers the
  selection without opening Navarro.
- The deterministic projection copies the frozen model and records its hash,
  direction, and non-probability status. Pages and CI include both new assets
  and focused tests. Refreshing the correction evaluation changed only
  `viewer_manifest_sha256`; counts, rates, and the zero-false-positive gate are
  unchanged.
- All 60 VLB Python tests passed (2 citation inventory, 6 viewer data, 9
  orthography, 29 mining, 5 reverse-concordance, and 9 correction tests). All
  five search tests passed. The correction evaluation gate passed.
- The full headless Chrome regression passed every desktop, responsive,
  search, share, splitter, minimization, continuous-mode, correction, and
  synthetic-pinch flag with `javascript_errors: []`. Screenshots and
  `result.json` are in `/tmp/vlb-study-reader-final-browser/`.
- The complete local Pages build succeeded at
  `/tmp/nhe-pages-vlb-study-reader`. Its VLB `app.js`, `search.js`, `styles.css`,
  manifest, and orthography-model bytes match the source files. No deployment
  command was run.

## What failed

- The first direct browser-regression run inside the restricted sandbox could
  not bind its loopback server (`listen EPERM`). The same documented command
  passed with the required local-browser permission.
- The first hosted Linux browser run raced the responsive `matchMedia` change:
  its assertion inspected the search disclosure before the mobile state event
  ran. The regression now waits for the mobile search ARIA state rather than an
  already-true desktop transcription attribute; the complete local rerun passes.
- Adding the model pointer changed the whole-manifest checksum and initially
  made the checked correction evaluation stale. Regeneration changed only its
  `viewer_manifest_sha256`; no correction metric or policy outcome moved.
- Audit found a fallback call to the removed `ocrLinesFor()` helper. Current
  generated data did not reach it, but legacy/malformed fragments could throw;
  the fallback now resolves `ocr.line_ids` safely or returns no boxes.
- The expanded browser regression found that restoring transcription in
  continuous mode resumed only the flow anchor and could leave the selected
  row off-screen. Restore now recenters `state.selectedSource` first and uses
  the flow anchor only when there is no active selection.
- The initial synthetic-pinch check measured only the first of a source's two
  OCR rectangles even though the product deliberately centers their union.
  The regression now measures the same union as the reader.
- The successful Pages build emitted pre-existing setuptools package-discovery,
  VuePress plugin/update-check, and stale Browserslist warnings. It exited zero
  and produced the complete artifact.

## Remaining questions

- Synthetic `Touch`/`TouchEvent` coverage verifies the browser logic, saved
  zoom, accidental-click suppression, and post-zoom centering. A physical
  phone/tablet two-finger gesture has not yet been tested.
- The frozen orthography model is intentionally directional and bounded; it
  does not cover every lexical or morphological alternative (for example,
  `ixé` to `Yxe`). Broader aliases need reviewed linguistic evidence rather
  than an ad hoc search exception.
- The branch has not been deployed. Review the final PR/CI and physical-device
  interaction before merging and using the normal Pages deployment flow.

## Suggested next prompt

Review the source-only search labels and final mobile screenshots, test pinch
and divider drag on one physical phone, then merge the follow-up PR and run the
normal Pages deployment only if those checks match the intended study flow.
