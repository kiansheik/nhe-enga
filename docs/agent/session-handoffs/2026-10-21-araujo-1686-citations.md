# Araújo 1686 citation-page handoff

## Goal

Repair production dictionary links such as `emo'emyîara` so explicit
`Ar., Cat., 241, 1686` citations open the referenced page of Araújo's 1686
*Catecismo*, while publishing only cited pages and a two-page buffer.

## Files inspected

- `docs/agent/{index,current-state,repo-map,open-questions,served-assets,log}.md`
- `js/index.js`
- `docs/primary_sources/index.html`, `DTAbib.txt`, `ar.Cat.1686.pdf`
- `docs/primary_sources/evreux1929/{README.md,source.json}`
- `scripts/{build_pages.sh,build_offline.py,optimize_pages_images.py}`
- `scripts/data/{render_source_pages.py,source_extraction.py,source_inventory.py,README.md}`
- `tests/primary_sources.test.cjs`
- Served `docs/dict-conjugated.json.gz`

## Files changed

- Citation/runtime: `js/index.js`, `docs/primary_sources/index.html`
- Source subset/provenance: `docs/primary_sources/arcat1686/` (158 JPEGs,
  `README.md`, `source.json`)
- Reproduction/build: `scripts/data/render_source_pages.py`,
  `scripts/build_pages.sh`, `scripts/build_offline.py`
- Regression coverage: `tests/primary_sources.test.cjs`
- Agent documentation: `docs/agent/current-state.md`, `repo-map.md`,
  `served-assets.md`, `log.md`, and this handoff

The raw `docs/primary_sources/ar.Cat.1686.pdf` remains an ignored local input
and is not added to the source commit or Pages artifact.

## Commands run

- `node --test tests/primary_sources.test.cjs`
- `make lint`
- `.venv/bin/python -m py_compile scripts/data/render_source_pages.py scripts/build_offline.py`
- `bash -n scripts/build_pages.sh`
- Pillow decode verification over all 158 source JPEGs
- `git diff --check`
- `make pages-build`
- Artifact counts for images, PDFs, files over 100 MiB, image formats, and the
  signed `source-arcat1686` offline pack
- Local HTTP server plus real Chrome navigation from the `emo'emyîara` result
  to the page-241 viewer
- Live pre-fix HTTP check showing the old 1618-derived image URL returned 404

## What worked

- The served gzip dictionary has 90 explicit 1686 citations covering 58
  distinct pages; the single 11-12 range produces two page links.
- Printed page 1 is zero-based PDF index 36, so the stable mapping is
  `image_index = printed_page + 35`. Printed page 371 is index 406; later
  leaves are unnumbered. Page 137 is misprinted as 237 in the source.
- Printed page 241 is image `276.jpg` and visibly contains the quoted
  `temo'emiára ... õanga recobecába ... mocanhemi` passage.
- The selected renderer verifies SHA-256 and the 420-page count, then derives
  exactly 158 pages from the cited-page list and a two-page buffer.
- The Pages build contains exactly 158 optimized 1686 JPEGs, no PDFs, no file
  over 100 MiB, and a 158-file offline source pack. Full artifact size is about
  741 MiB.
- All 12 focused Node tests and repository lint pass. Real Chrome showed the
  corrected dictionary anchor, edition metadata, printed-page label, external
  PDF link at ordinal 277, and readable image 276.

## Publication

- Source commit `cb4b3b87` was pushed to `origin/main`.
- Static-site commit `99fb18f3` was pushed to `origin/gh-pages`; GitHub Pages
  reported `built` with no error at 2026-10-21 16:50 America/Sao_Paulo.
- The live `arcat1686/276.jpg` returned HTTP 200 and matched the local artifact
  SHA-256 `f63fdc33a38773c1caba04c22d1a649388f1a778ee8793e197948acc1b86d4f4`.
- A real Chromium production click from the `emo'emyîara` entry opened the
  `arcat1686` page-241 viewer and displayed the scan successfully.

## What failed

- System Poppler tools were absent, so PyMuPDF/Pillow were used for PDF
  inspection and rendering.
- The first render included the unnumbered leaf before printed page 1 because
  the buffer was bounded only by PDF indices. The renderer now also clamps to
  the manifest's first/last printed pages; the extra image was moved out of the
  repository and the final set is exactly 158.
- The first local server omitted the `/nhe-enga/` path prefix, so absolute
  asset paths did not load. A temporary prefix directory reproduced the real
  hosting layout and the Chromium check passed.

## Remaining questions

- When new explicit 1686 citations enter `dict-conjugated.json.gz`, rerun the
  citation audit and selected renderer, then update the manifest ranges and
  viewer ranges together. The regression fails if source images no longer
  match the manifest selection.
- Context-free `Ar., Cat., 1686` citations have no locator and remain unlinked.

## Suggested next prompt

“Refresh the Araújo 1686 cited-page subset after dictionary data changes, run
the focused source-viewer tests and Pages build, then verify one new citation
in a real browser.”
