# VLB unified mobile reader

## Goal

Replace the deployed mobile VLB single-surface switch with a united reading
view: keep search above, make the facsimile primary, keep a compact
transcription tray in roughly the lower third, allow that tray to minimize, and
fit the transcription more comfortably without changing desktop behavior.
Then make line selection navigation-only in both directions, keep Navarro
contextual and explicitly opened, and add ready-to-copy/native-share citations
with compact deep links to the selected line.

## Files inspected

- `docs/agent/index.md`, `current-state.md`, `repo-map.md`, and
  `open-questions.md`
- `vlb/index.html`, `vlb/styles.css`, `vlb/app.js`, and `vlb/README.md`
- `tests/vlb_viewer_browser.cjs` and `tests/test_vlb_viewer_data.py`
- Prior mobile QA captures under `/tmp/vlb-final-qa3/`

## Files changed

- `vlb/index.html`
- `vlb/styles.css`
- `vlb/app.js`
- `vlb/README.md`
- `tests/vlb_viewer_browser.cjs`
- `tests/test_vlb_viewer_data.py`
- `docs/agent/current-state.md`
- `docs/agent/log.md`
- this handoff

## Commands run

- `git fetch origin main`
- `node --check vlb/app.js`
- `node --check tests/vlb_viewer_browser.cjs`
- `node --test tests/vlb_dictionary_links.test.cjs tests/vlb_citation_targets.test.cjs tests/vlb_correction_regressions.test.cjs tests/dictionary_formatting.test.cjs`
- `node vlb/evaluate_corrections.cjs --check`
- `python3 -m unittest discover -s tests -p 'test_vlb_*.py' -v`
- `python3 tests/test_vlb_citation_inventory.py`
- `VLB_PLAYWRIGHT_MODULE=/Users/kian/code/pydicate-studio/node_modules/playwright VLB_CHROMIUM_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' VLB_QA_DIR=/tmp/vlb-mobile-share-final5 node tests/vlb_viewer_browser.cjs`
- `PAGES_BUILD_DIR=/tmp/nhe-pages-vlb-mobile-share-final make pages-build`
- `git diff --check`

## What worked

- Mobile and portrait-tablet layouts now use one bounded grid instead of
  mutually exclusive panes. The facsimile is always the larger upper row; the
  transcription defaults to `clamp(170px, 31dvh, 290px)` and becomes a
  41 px restore bar when minimized.
- Search moved out of the collapsed reading-options disclosure and remains
  above the reader, including at 844×390 landscape size. Reading mode and copy
  link remain available under **Opções de leitura**.
- Normal transcription lines are 15 px at 1.46 line height, falling to 14 px
  at short landscape heights. The smaller gutter and padding preserve more
  text without changing desktop typography.
- The minimize control exposes `aria-expanded`/`aria-controls`, makes the hidden
  body inert, and returns focus safely. It preserves both internal scroll
  positions, the selected transcription span, and the facsimile OCR rectangle.
- Old `surface=text|scan` URLs still load. They can guide focus, but neither
  pane becomes hidden and continuous-mode scans hydrate immediately.
- Correction mode restores and temporarily enlarges the tray while leaving a
  substantial facsimile area. Background resize/flow synchronization does not
  reopen a tray the reader deliberately minimized.
- Transcript-line clicks now leave the active tab and transcription scroll
  alone, select only that source, and center the union of its OCR boxes in the
  facsimile. Tapping an OCR-aligned facsimile line performs the reverse jump,
  restores a minimized mobile tray, and centers the transcript row.
- Navarro starts with no page-wide headword list. Selecting a line prepares
  only its associated citations; **Ver no Navarro** or the tab reveals them,
  and a second explicit headword click opens the larger detail panel. Raw line
  clicks, shared routes, resize, and correction editing do not open that detail.
  Selecting an unrelated line also clears stale citation/entry identity,
  ambiguous-entry filters, notices, and the old detail before URLs or notes
  update; same-line correction work preserves its explicit citation context.
- **Citar verbete** copies the exact line, a minimal VLB volume/page/paragraph
  citation, and a compact `page=I-017&line=13` link. **Compartilhar** invokes
  Web Share with the same material and falls back to the clipboard; clipboard
  denial opens the complete block for manual copy. Compact links resolve against
  a page-unique source-line invariant, reopen the selected line, and center both
  surfaces without opening Navarro.
- Fresh Chrome QA passed every result flag with zero JavaScript errors. Final
  screenshots and `result.json` are in `/tmp/vlb-mobile-share-final5/`.
- The full VLB Python suite passed 59/59, citation inventory 2/2, and focused
  Node suite 29/29. The correction regression report remains current.
- A complete local Pages artifact built successfully at
  `/tmp/nhe-pages-vlb-mobile-share-final`. Its VLB JavaScript and CSS match the source
  bytes; HTML differs only by the expected offline registration injection.
  No deploy target was invoked.

## What failed

- The first browser run sampled the 24 px section heading instead of an
  ordinary transcription line for the compact-type assertion. The selector
  now explicitly excludes heading fragments.
- The next run exposed an old continuous-mode hydration guard keyed to the
  single-surface state. It now hydrates the always-visible scan pane.
- A later run exposed a resize callback that could reopen the tray after a
  reader minimized it. Auto-expansion is now limited to direct user actions,
  deep links/search, and correction editing.
- One rapidly resized landscape screenshot contained stale compositor pixels;
  final QA waits for settled paint before capture.
- Explicit-detail tests initially reset a manually selected candidate span;
  reopening the already-selected citation now preserves that exact target.
- Continuous raw selection initially allowed its scroll observer to reactivate
  the preceding page; the direct click now briefly locks that pane while the
  selected page becomes current.
- An audit found that direct line selection after an ambiguous entry retained
  the entry-wide Navarro filter. Direct selection now clears that filter, and a
  browser regression covers the transition to line-specific results.
- The final diff audit found that selecting an unrelated line after explicitly
  opening Navarro retained the old citation/detail in the URL and note target.
  Direct navigation now clears that mixed state while explicit same-line
  correction and association flows opt in to preserving citation context.
- The final landscape visual pass caught a page-mode resize that retained the
  portrait scroll offset and left the selected scan line off-screen. Resize now
  redraws and recenters the existing selection without reopening any UI.
- The successful Pages build emitted existing setuptools package-discovery,
  VuePress plugin/update-check, and outdated Browserslist warnings. It still
  exited zero and produced the complete local artifact; no deploy ran.

## Remaining questions

- The 31dvh default is deliberately approximate. If live-device feedback wants
  a different split, adjust only the mobile row clamp and retain the geometry
  regression bounds.
- The copied locator intentionally stays minimal rather than asserting
  bibliographic fields not present in the reader. If a formal house citation
  style is later chosen, change `sourceCitation()` and its payload regression
  together.
- The source change is not deployed by this session. The user reported the PR
  #38 baseline as deployed, but this follow-up still requires review, merge,
  and the normal Pages deployment flow.

## Suggested next prompt

Review the unified/mobile selected-line screenshots and copied citation format,
then merge the follow-up PR and run the normal Pages deployment if they match
the desired interaction.
