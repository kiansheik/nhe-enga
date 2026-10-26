# Anchieta Teatro all-citation handoff

## Goal

Make every current `Anch., Teatro` citation clickable, including the reported
`îambé` entry at page 36, without treating Navarro and Martins pagination as
interchangeable.

## Files inspected

- Required `docs/agent/{index,current-state,repo-map,open-questions}.md`
- Served `docs/dict-conjugated.json.gz` and `docs/primary_sources/DTAbib.txt`
- `js/index.js`, `docs/primary_sources/index.html`, and source-link tests
- Existing `anchteatro1954` manifest, witness, and local 905-page source PDF
- Internet Archive DjVu OCR for `anchieta-poesisas`
- Pages/offline build scripts and generated source-inventory tooling

## Files changed

- Runtime/linking: `js/index.js`, `docs/primary_sources/index.html`
- Source witness: `docs/primary_sources/anchteatro1954/{README.md,source.json}`
  and 74 additional sparse JPEGs (75 total)
- Alignment/reproduction: `scripts/data/align_anchieta_teatro.py`
- Catalog/build: `scripts/build_offline.py`,
  `scripts/data/source_inventory.py`, and regenerated
  `docs/primary_sources/source_inventory.*` / citation audit
- CI: `.github/workflows/offline.yml`
- Tests: `tests/primary_sources.test.cjs`, `tests/offline/test_catalog.py`
- Documentation: root `README.md`, agent state/map/assets/questions/log, and
  this handoff

No dictionary data, morphology engine, corpus expression, or ground truth was
changed. The raw 105 MB source PDF remains outside the Pages artifact.

## Commands run

- Targeted `rg`, Git/status/diff, gzip/JSON, OCR XML, and source-manifest
  inspection
- `.venv/bin/python scripts/data/align_anchieta_teatro.py --ocr ...`
- `scripts/data/render_source_pages.py` with all 75 unique mapped PDF indices
- `node --test tests/primary_sources.test.cjs`
- `node --test tests/dictionary_formatting.test.cjs tests/dictionary_apostrophes.test.cjs`
- `.venv/bin/python tests/dictionary_formatting_browser.py`
- `../../.venv/bin/python -m unittest test_catalog.py`
- `node --test tests/offline/service_worker_smoke.cjs`
- JPEG decode verification and Python compilation
- `.venv/bin/python scripts/data/source_inventory.py`
- `make pages-build`
- `git diff --check`
- Isolated Chromium inspection of the exact localhost `îambé` result

## What worked

- All 1,431 current citations in 882 records produce Teatro links while every
  visible source token remains unchanged. This includes 1,326 default 1999
  citations, 105 explicit 2006 citations, two ranges, and punctuation variants.
- The 72 distinct 1999 and 35 distinct 2006 locators have separate mappings.
  Their union uses 75 documentary pages. The viewer requires the edition and
  page together, so identical page numbers in the two editions cannot collide.
- `îambé` exposes `Anch., Teatro, 36` on localhost and routes to PDF index
  757. Pages 176 in the 1999 and 2006 editions route to 683 and 682 respectively.
- The OCR helper ranks candidates but does not mutate the map. Sequence review
  prevents the repeated later *Na festa do Natal* adaptation from replacing
  the cited *São Lourenço* sequence.
- The 804 MiB Pages artifact contains all 75 optimized JPEGs and no raw source
  PDF. Focused, corpus-wide, Chromium, offline, and packaging checks pass.

## What failed

- No openly accessible scan of Navarro's exact 1999/2006 editions was found.
  The implementation therefore links explicitly labeled Martins documentary
  witnesses and makes no general pagination-equivalence claim.
- The sandbox denied Chromium startup and localhost binding until the approved
  test command ran outside it.
- The first PR Android job failed before checkout code ran because
  `android-actions/setup-android` requested Google's retired SDK package
  `tools`. The workflow now requests `platform-tools` explicitly.
- One ad-hoc popup script subscribed after the new tab opened and missed its
  event; the exact anchor was still observed in the localhost DOM, while the
  source viewer and image selection are covered by focused executable tests.

## Remaining questions

- If a lawful public digitization of either Navarro edition becomes available,
  should these documentary targets be replaced with exact-edition page scans?
- The checked-in maps should be extended only when new citation locators enter
  the served dictionary; unsupported pages and other edition years are
  deliberately left unlinked.

## Suggested next prompt

“Review the Anchieta Teatro PR, spot-check several 1999 and 2006 viewer links,
then merge and deploy the Pages artifact if the edition labels are acceptable.”
