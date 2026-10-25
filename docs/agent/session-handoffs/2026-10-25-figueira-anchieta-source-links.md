# Figueira and Anchieta source-link handoff

## Goal

Restore clickable primary-source links for the reported `ma'enduar` entry:
`Anch., Teatro, 176`, `Fig., Arte, 95`, and `Fig., Arte, 40`, after reviewing
the earlier source-link work and preserving edition boundaries.

## Files inspected

- Required `docs/agent/{index,current-state,repo-map,open-questions}.md` and
  related source/build handoffs
- Prior Figueira work in commits `db76f045`, `24acbc68`, `f1c749c5`, and
  `1ba8d246`
- Served `docs/dict-conjugated.json.gz` and `docs/primary_sources/DTAbib.txt`
- `js/index.js`, `docs/primary_sources/index.html`
- Source manifests, READMEs, scans, and local source PDFs under
  `docs/primary_sources/`
- `scripts/{build_pages.sh,build_offline.py,optimize_pages_images.py}` and
  `scripts/data/{README.md,render_source_pages.py,source_inventory.py}`
- `tests/primary_sources.test.cjs` and `tests/offline/`

## Files changed

- Citation/runtime: `js/index.js`, `docs/primary_sources/index.html`
- Figueira source: `docs/primary_sources/figueira1878/` (`0.jpg` through
  `199.jpg`, `README.md`, and `source.json`)
- Anchieta witness: `docs/primary_sources/anchteatro1954/683.jpg`, `README.md`,
  and `source.json`
- Reproduction/build/offline: `scripts/data/render_source_pages.py`,
  `scripts/data/README.md`, `scripts/build_pages.sh`, and
  `scripts/build_offline.py`
- Regression coverage: `tests/primary_sources.test.cjs` and
  `tests/offline/test_catalog.py`
- Documentation: `README.md`, `docs/agent/{current-state,repo-map,served-assets,open-questions,log}.md`,
  and this handoff

The raw source PDFs remain ignored/local inputs and are not copied into the
Pages artifact. No morphology module, corpus expression, ground truth, or
generated source-inventory artifact was changed.

## Commands run

- Targeted `rg`, `git log`, `git show`, gzip/JSON inspection, and provenance
  comparisons against the earlier Figueira implementation
- PyMuPDF/Pillow inspection and rerender of the Anchieta witness
- `node --test tests/primary_sources.test.cjs`
- `.venv/bin/python -m unittest discover -s tests/offline -p 'test_catalog.py'`
- `node tests/offline/service_worker_smoke.cjs`
- `node --check js/index.js`
- `.venv/bin/python -m py_compile scripts/data/render_source_pages.py scripts/build_offline.py`
- `bash -n scripts/build_pages.sh`
- `make lint`
- `git diff --check`
- `scripts/data/source_inventory.py --output-dir /tmp/nhe-enga-source-inventory`
- `OFFLINE_SKIP_APK=1 PAGES_BUILD_DIR=/tmp/nhe-enga-pages-build make pages-build`
- Artifact image/manifest/offline-pack counts and raw-publication-format checks
- Temporary local HTTP server plus real Chrome search and link clicks

## What worked

- Figueira's complete 200-image source set and manifest are byte-identical to
  the earlier reviewed implementation. All 622 explicit `Fig., Arte`
  citations in 455 records link without changing displayed text; lists,
  ranges, and the `1686, 64` warning retain their reviewed behavior.
- Printed page 95 maps to image/PDF index 118 (ordinal 119), and printed page
  40 maps to index 63 (ordinal 64). Both requested quotations are visible on
  those scans.
- All nine unsuffixed `Anch., Teatro, 176` records were visually located on
  Martins 1954 printed p. 632, PDF index 683 (ordinal 684). The reported
  `nde maenduá xe ri` passage is line 655. Internet Archive's leaf map also
  identifies `n683` as printed p. 632.
- The Anchieta linker is exact: `176, 2006`, another year, a range, a list, or
  another page does not acquire the documentary-witness link. The two 2006
  quotations occur on a different Martins page and remain unlinked.
- All 18 source/viewer tests and 11 offline catalog tests pass. The full build
  is 809,800 KiB (about 791 MiB), contains both manifests and exactly 200/1
  optimized source images in named offline packs, and contains no PDF, EPUB,
  MOBI, or OPF.
- Real Chrome showed all three anchors in the built `ma'enduar` result. Each
  target opened in a new tab, loaded the expected image, exposed the correct
  printed/PDF page label, and retained its external source link.

## Publication

- Source commit `31194fd4` was pushed to `origin/main`.
- Static-site commit `2333ed15` was pushed to `origin/gh-pages`; GitHub Pages
  reported `built` with no error after 84,063 ms.
- The custom-domain JavaScript contains the new `anchteatro1954` and
  `figueira1878` routes. The live Anchieta 683, Figueira 118, and Figueira 63
  JPEGs match the deployed worktree SHA-256 values byte for byte.
- A real Chrome search for `ma'enduar` exposed all three links. The deployed
  viewers opened in separate tabs and loaded the expected 1400-pixel-wide
  images with the correct page labels.

## What failed

- The local scan available for Anchieta is Martins's 1954 *Poesias*, not
  Navarro's cited 1999/2006 *Teatro*. Cross-page samples proved there is no
  safe global offset, so only the independently collated unsuffixed page-176
  quotations were linked.
- The sandbox initially denied binding a localhost preview server. The
  approved temporary server succeeded, and Chrome validation passed.
- The first new offline-pack test required Black formatting; formatting the
  one edited test file restored `make lint`.
- The checked-in generated source inventory remains an older snapshot. A
  `/tmp` regeneration reports 622 Figueira and nine Anchieta links, but the
  generated files were left untouched under the repository rule.

## Remaining questions

- A complete Anchieta Teatro implementation needs quotation-aware mappings or
  the exact cited editions. Do not extrapolate from this page-176 witness.
- Refresh the checked-in generated source inventory only when generated audit
  outputs are explicitly in scope.

## Suggested next prompt

“Choose the next unresolved primary source, verify its exact edition and
locator system, and propose a bounded mapping without extrapolating the
Anchieta page-176 concordance.”
