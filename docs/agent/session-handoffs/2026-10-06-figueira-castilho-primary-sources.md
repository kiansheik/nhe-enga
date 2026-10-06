# Figueira and Castilho primary-source implementation handoff

## Goal

Complete the first implementation stage from PR #26: add the verified Figueira
and Castilho source pages, link their current dictionary citations, extend the
shared viewer/renderer/Pages build, keep the year-qualified Figueira citation
linked with an honest warning, and stop for review before Sousa or D’Abbeville.

Implementation branch: `feat/figueira-castilho-primary-sources`, based on
`docs/next-primary-source-groundwork` (PR #26). The implementation PR link is
added after it is opened. Nothing was merged or deployed.

## Files inspected

- `AGENTS.md`, `CLAUDE.md`, and the required `docs/agent/` entry pages
- PR #26 and all four plans under `docs/primary_sources/plans/`
- D’Evreux production manifest, renderer, linker, viewer, Pages build and tests
- `docs/dict-conjugated.json.gz` and the generated citation inventory/audit
- The exact downloaded Figueira and Castilho PDFs, title pages, cited-page
  headers, the Figueira p. 64 passage, and all Castilho crop targets
- Brazilian National Library and CEDOCH catalog records for Figueira's edition

## Files changed

- Source assets and provenance:
  `docs/primary_sources/figueira1878/{0..199}.jpg`, `source.json`, `README.md`;
  `docs/primary_sources/castilho1937/p27.jpg` through `p41.jpg` plus `p45.jpg`,
  `source.json`, `README.md`
- Citation/runtime: `js/index.js`, `docs/primary_sources/index.html`
- Renderer/build: `scripts/data/render_source_pages.py`,
  `scripts/build_pages.sh`, `scripts/check_pages_size.py`
- Audit/tests: `scripts/data/source_inventory.py`, generated inventory/audit
  files, `tests/primary_sources.test.cjs`, `tests/test_pages_size.py`
- Documentation: `README.md`, `scripts/data/README.md`, the Figueira research
  plan, and the required `docs/agent/` updates

No PDF, dictionary definition, morphology code or corpus ground truth changed.

## Commands run

- Download/checksum/page-count inspection for both pinned PDFs outside Git
- `python scripts/data/render_source_pages.py --pdf ... --manifest ...`
  for each source, plus independent output directories and full byte comparisons
- Full image decoding, dimension, progressive-JPEG and filename checks
- `python3 scripts/data/source_inventory.py`
- `node --test tests/primary_sources.test.cjs`
- `python3 -m unittest tests/test_pages_size.py`
- `python3 -m py_compile scripts/check_pages_size.py scripts/data/render_source_pages.py scripts/data/source_inventory.py`
- `node --check js/index.js`; `bash -n scripts/build_pages.sh`; `make lint`
- `make pages-build` with an isolated build directory/virtualenv and the
  checkout's existing untracked baseline dictionary/`cartas_portiguara` inputs
- Local `python3 -m http.server` and real-Chromium desktop/400px review

## What worked

- Figueira PDF: 1,936,830 bytes, 200 pages, SHA-256
  `a48d22961a385c3d0cc55bada47bb6e61af85ca3a2d6e20e3102fdb2a881cb57`.
  The 200 progressive 1400px JPEGs occupy about 50.0 MiB. Printed page `p`
  maps to zero-based PDF index `p + 23`; all 117 currently cited pages have
  verified headers.
- Castilho PDF: 11,660,598 bytes, 70 pages, SHA-256
  `7e2f9dc0323e4ef1a7bbc82a6dcd3b687f93457e780fecb868c8841389fe1519`.
  The 16 progressive 1200px page-side crops occupy about 5.1 MiB and follow an
  explicit map that handles the inserted facsimile between pp. 38 and 39.
- The exact Figueira p. 64 wording matches the dictionary's `soaba` definition.
  `Fig., Arte, 1686, 64` therefore remains verbatim, links to image `87.jpg` /
  PDF page 88, and shows a visible warning that the identified edition is 1687.
- Coverage: 622 Figueira citation occurrences in 455 records and 215 Castilho
  occurrences in 162 records; 837 links total. Ranges, observed comma variants
  and the inherited Figueira page continuation are covered. Unmapped requested
  pages show an error instead of silently redirecting.
- All 216 generated JPEGs matched an independent rerender byte for byte. All
  source and optimized images decode.
- Tests: 12/12 Node source/viewer regressions, 6/6 Pages-size tests, Black via
  `make lint`, JavaScript/Python/shell syntax and whitespace checks pass.
- Full Pages artifact: 2,229 files, 777,563,987 bytes, 122,436,013 bytes below
  the 900,000,000-byte project budget; no PDFs or files over 100 MB. Figueira
  contributes 52,356,852 built bytes and Castilho 5,156,363 built bytes.
- Real Chromium: the dictionary visibly renders the year-qualified citation as
  a link; Figueira p. 64 and Castilho pp. 38/39/45 display correct page/PDF
  labels, readable scans and bounded navigation on desktop and at 400 CSS px.

## What failed or needed adaptation

- The first full build used a temporary venv without `pip`; recreating the
  isolated environment with Python 3.11 and the declared requirements fixed it.
- The bare worktree lacks the ignored generated Navarro dictionary files and
  `cartas_portiguara` baseline assets required by the existing build. They were
  copied into this isolated worktree for verification only and remain untracked.
- The source-tree viewer requests `image-formats.json`, which exists only in a
  Pages build; local preview reports that optional request as 404 and correctly
  falls back to the manifest/default `.jpg` format.
- A generic spread formula was unsuitable for Castilho because the inserted
  facsimile moves p. 39; the production manifest uses explicit crop targets.

## Remaining questions

- Human review is still needed for scan/crop legibility, viewer wording, the
  visible Figueira year warning and the roughly 57.4 MB optimized artifact
  increase relative to the PR #26 baseline.
- PR #26 must land before, or together with, the dependent implementation PR.
- Sousa and D’Abbeville remain research-only. Their unresolved locator/content
  discrepancies and storage costs must be addressed before implementation.
- Publication remains separate; do not run `make deploy-gh-pages` as part of
  review or merge unless explicitly authorized.

## Suggested next prompt

> Review the Figueira/Castilho implementation PR. Check the `só` entry's
> `Fig., Arte, 1686, 64` click-through and warning, Figueira range/navigation
> behavior, Castilho pp. 38/39 and 45 crop mapping, mobile readability, source
> checksums and the complete Pages-size report. If acceptable, merge PR #26
> before the dependent implementation PR. Do not start Sousa or D’Abbeville
> until that review is complete.
