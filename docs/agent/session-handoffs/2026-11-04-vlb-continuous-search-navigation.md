# VLB continuous search and navigation follow-up

## Goal

Add a concise VLB entry point on the homepage while hiding only the unfinished
grammar navigation item; keep VLB search results available after navigation;
default new readers to continuous mode; and make continuous facsimile/text
scrolling follow OCR-aligned visible content except while a line is selected.

## Files inspected

- `docs/agent/index.md`, `current-state.md`, `repo-map.md`, and
  `open-questions.md`
- `index.html`
- `vlb/app.js`, `vlb/styles.css`, `vlb/index.html`, and representative
  page/source data under `vlb/data/`
- `tests/vlb_dictionary_links.test.cjs` and
  `tests/vlb_viewer_browser.cjs`
- `scripts/build_pages.sh` and the local-preview instructions used for browser
  verification

## Files changed

- Navigation: `index.html`
- Reader behavior and presentation: `vlb/app.js`, `vlb/styles.css`
- Regression coverage: `tests/vlb_dictionary_links.test.cjs`,
  `tests/vlb_viewer_browser.cjs`
- Agent documentation: `docs/agent/current-state.md`, `docs/agent/repo-map.md`,
  `docs/agent/log.md`, and this handoff

## Commands run

- `node --test tests/vlb_dictionary_links.test.cjs`
- `node --check vlb/app.js`
- `node --check tests/vlb_viewer_browser.cjs`
- `git diff --check`
- `make lint`
- `VLB_PLAYWRIGHT_MODULE=/Users/kian/code/pydicate-studio/node_modules/playwright VLB_CHROMIUM_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' VLB_QA_DIR=/tmp/vlb-followup-qa.bTDUph node tests/vlb_viewer_browser.cjs`
- `PAGES_BUILD_DIR=/tmp/nhe-pages-vlb-followup.DRGw6a make pages-build`

## What worked

- The homepage exposes one short `/nhe-enga/vlb/` link and no direct
  `/nhe-enga/gramatica` link. The grammar files and Playground link were not
  removed.
- A fresh preference store selects continuous mode. Valid saved page or
  continuous preferences persist, while an explicit URL can override the mode
  without changing the saved preference.
- Search result clicks keep the query and complete result list visible, mark
  the current result, navigate/select/center normally, and close only through
  an explicit search control.
- Continuous synchronization builds paired start/end landmarks for each
  transcript source and the union of its OCR boxes. It interpolates between
  those landmarks in either direction and falls back to page-relative position
  when a page has no usable alignment.
- While a source is selected, text and scan scroll events update their own
  positions and lazy-loading edges without activating another page or moving
  the other pane. Tapping the same line on either surface clears the selection
  and relocks from that surface's semantic position.
- Search selection state is cleared when line selection is cleared by another
  navigation path. Independent scan scrolling retains its own image-hydration
  anchor, and selecting a new transcript source rehydrates its active scan
  before centering.
- The full Chrome regression completed with every result flag true and
  `javascript_errors: []`. Representative desktop and mobile captures are in
  `/tmp/vlb-followup-qa.bTDUph`.
- The fresh Pages build produced 2,787 files (813 MiB) under
  `/tmp/nhe-pages-vlb-followup.DRGw6a`. Its `index.html`, `vlb/app.js`, and
  `vlb/styles.css` are byte-identical to source. No deploy command ran.

## What failed

- The first full browser pass used a continuous-only selector in a mobile
  scenario that intentionally retained a saved page-mode preference. The
  assertion was changed to identify the selected source independently of DOM
  mode.
- A later responsive assertion ran before the browser had delivered its media
  query change event. It now waits for the compact search disclosure state
  before checking the mobile reader.
- The Pages build emitted existing nonfatal setuptools, Browserslist, VuePress,
  update-check, and unavailable-`/dev/tty` warnings; the artifact completed and
  all requested emitted-file checks passed.
- `make lint` remains red before this UI slice: Black reports 24 existing VLB
  mining, projection, inventory, and test files that it would reformat. None is
  changed by this diff, and no formatting rewrite was applied.

## Remaining questions

- Physical phone gestures and the subjective feel of semantic relocking still
  need user validation; headless Chrome covers the interaction contract and
  geometry, not tactile quality.
- Legacy localStorage cannot distinguish an old explicit page-mode selection
  from a page value incidentally saved with another viewer preference, so valid
  existing modes are preserved conservatively.

## Suggested next prompt

Review PR 40 on a physical phone, especially retained mobile search, selected
line independent scrolling, and relocking from both transcript and facsimile;
then merge and deploy only if those interactions feel right.
