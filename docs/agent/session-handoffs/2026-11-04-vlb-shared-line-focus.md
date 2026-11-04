# VLB shared-line focus under normal motion

## Goal

Make the shared URL
`https://kiansheik.io/nhe-enga/vlb/?page=I-055&line=1131` behave like the
line was selected in the reader: select §1131, expose its actions, and center
both its transcription and OCR highlight in the facsimile.

## Files inspected

- `docs/agent/index.md`, `current-state.md`, `repo-map.md`, and
  `open-questions.md`
- The deployed shared URL and deployed `vlb/app.js`
- `vlb/app.js`, `vlb/styles.css`, `vlb/index.html`, and
  `vlb/data/pages/I-055.json.gz`
- `tests/vlb_viewer_browser.cjs`
- `.github/workflows/dictionary-formatting.yml`
- The prior November 3–4 VLB handoffs

## Files changed

- Reader behavior: `vlb/app.js`
- Browser regression: `tests/vlb_viewer_browser.cjs`
- CI scan fixture: `.github/workflows/dictionary-formatting.yml`
- Agent documentation: `docs/agent/current-state.md`, `docs/agent/repo-map.md`,
  `docs/agent/log.md`, and this handoff

## Commands run

- Live and local Playwright probes at 1440×1080 and 390×844 with normal and
  reduced motion, fresh preferences, and saved page mode
- `python3 -m http.server 8765 --bind 127.0.0.1`
- `curl -I 'http://127.0.0.1:8765/vlb/?page=I-055&line=1131'`
- `VLB_PLAYWRIGHT_MODULE=/Users/kian/code/pydicate-studio/node_modules/playwright VLB_CHROMIUM_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' VLB_QA_DIR=/tmp/vlb-shared-focus-final.TA4Srq node tests/vlb_viewer_browser.cjs`
- `node --test tests/vlb_citation_targets.test.cjs tests/vlb_correction_regressions.test.cjs tests/vlb_dictionary_links.test.cjs tests/vlb_search.test.cjs`
- `node --check vlb/app.js`
- `node --check tests/vlb_viewer_browser.cjs`
- `git diff --check`
- `PAGES_BUILD_DIR=/tmp/nhe-pages-shared-focus.OhvyoL make pages-build`

## What worked

- Live reproduction proved that the route already resolved the exact
  `vlb-emerson-r568-p01131` record and applied selected DOM state. Deployed and
  local application bytes matched.
- With normal motion, the initial smooth scroll was interrupted when
  `extendFlow(-1)` inserted I-054 above I-055 and anchor preservation adjusted
  the viewport. Reduced motion made the same path instant, explaining why the
  existing regression passed.
- Scroll helpers now accept an explicit behavior. `loadPage` routes pass
  `instant` through source and citation selection, while direct user clicks
  retain their existing smooth default.
- Image-onload recovery uses instant focus after the real image geometry is
  known, preventing a second animation from being displaced by layout work.
- The exact reported link now selects the correct text and centers both panes
  in fresh continuous and saved page modes on desktop and mobile.
- The regression switches to normal motion, waits for I-054 and the current
  image, and verifies text, source ID, pressed state, line actions, URL,
  transcription geometry, and OCR-highlight geometry. The suite then restores
  its prior reduced-motion and desktop state.
- The full Chrome suite passes every result flag with
  `javascript_errors: []`. All 31 focused VLB Node tests and syntax/diff checks
  pass. `vlb-shared-line-focus.png` under
  `/tmp/vlb-shared-focus-final.TA4Srq` shows the corrected mobile focus state.
- The fresh Pages artifact contains 2,787 files (813 MiB). Its `vlb/app.js` and
  `vlb/data/pages/I-055.json.gz` are byte-identical to source; line 1131 and its
  OCR box are present, and the optimized `55.jpg` is mapped by the generated
  image manifest. No deployment command ran.

## What failed

- Direct web extraction could not open the reported page, and the available
  computer-use inventory exposed no controllable browser surface. The same URL
  was reproduced with local Chrome through Playwright instead.
- The earlier compact-link regression used I-017 §13, where there is no prior
  lexical page to prepend, and globally forced reduced motion. It therefore
  did not exercise the failing layout/animation combination.
- The Pages build completed with existing nonfatal setuptools, VuePress layout,
  unavailable-`/dev/tty`, and update-check warnings.

## Remaining questions

- The fix is locally and browser-regression verified but not deployed. The
  exact public URL should be rechecked after its source PR is merged and Pages
  is deliberately deployed.

## Suggested next prompt

Merge the focused shared-line PR, deploy the resulting clean `main` Pages
artifact, and verify the exact I-055 §1131 URL on the public custom domain.
