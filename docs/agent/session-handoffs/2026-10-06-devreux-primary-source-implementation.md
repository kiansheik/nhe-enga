# D’Evreux primary-source implementation handoff

## Goal

Finish the D’Evreux pilot from PR #24: verify and render the exact 1929
Portuguese edition, link the dictionary’s explicit `D'Evreux, Viagem`
citations, extend the primary-source viewer and Pages build, produce a
repeatable source inventory, validate the real workflow, and stop for review.

No other source, dictionary definition, morphology code, corpus ground truth,
deployment, or merge was authorized.

## Files inspected

- `AGENTS.md`, `CLAUDE.md`, and the required `docs/agent/` entry pages
- PR #24 handoff and frozen prototype commit `61cd1d0c`
- `js/index.js`
- `docs/dict-conjugated.json.gz`
- `docs/primary_sources/DTAbib.txt`
- `docs/primary_sources/index.html`
- `scripts/build_pages.sh`
- `scripts/optimize_pages_images.py`
- `scripts/data/source_extraction.py`
- The downloaded 1929 PDF and rendered/optimized pages 3, 7, and 293

## Files changed

- Citation/runtime: `js/index.js`, `docs/primary_sources/index.html`
- Source assets: `docs/primary_sources/evreux1929/0.jpg` through `443.jpg`,
  `source.json`, `README.md`, and `evreux1929-viewer-preview.png`
- Reproducibility/audit: `scripts/data/render_source_pages.py`,
  `scripts/data/source_inventory.py`, `docs/primary_sources/source_inventory.*`,
  `source_citation_audit.jsonl.gz`, and `devreux_citations.csv`
- Build/tests/docs: `scripts/build_pages.sh`,
  `tests/primary_sources.test.cjs`, `README.md`, `scripts/data/README.md`, and
  the required `docs/agent/` updates

The inventory writer normalizes the gzip OS header byte so regeneration is
byte-for-byte stable across Python/zlib versions.

## Commands run

- `node --test tests/primary_sources.test.cjs`
- `python3 scripts/data/source_inventory.py` (repeated to verify byte stability)
- `bash -n scripts/build_pages.sh`
- `git diff --check`
- `curl --fail --location --retry 3 <verified Archive PDF URL>`
- `uv run --with pymupdf==1.26.6 --with pillow==12.3.0 ...`
- `python scripts/data/render_source_pages.py --pdf ... --manifest ... --output-dir ...`
- Full image decode/hash comparisons for source, rerendered, and optimized JPEGs
- `make pages-build` with a temporary build environment and the checkout’s
  baseline untracked generated dictionary/`cartas_portiguara` assets
- Local `python3 -m http.server` plus real-Chromium desktop/narrow-window review

## What worked

- Exact PDF: 121,180,986 bytes, 444 pages, SHA-256
  `1e6c7d93aa7e49f6cf76dd5ae84384e71ab40de592495f21b5708e4cdab61864`.
- Independent full rerender: 444/444 files byte-identical to the committed
  source JPEGs; 259.3 MiB total; all progressive JPEGs fully decode.
- Inventory: 120 explicit citations in 113 records, 121 anchors, 42 printed
  pages. The complete audit reports 47 bibliography labels, 69 work-family
  rows, and 11 unresolved bibliography matches.
- Focused tests: 8/8 pass, including citation variants/ranges, out-of-range
  rejection, viewer bounds/URL/zoom/failure state, and legacy source mappings.
- Full Pages build: 1,851 optimized primary-source images, 2,625.7 MiB to
  640.6 MiB; final artifact 691 MiB. D’Evreux contributes 444 pages and about
  212.0 MiB. `source.json`, `DTAbib.txt`, and the `evreux1929: .jpg` format map
  are present; no PDF is copied.
- Browser: the `so'o-Îurupari` citation opens printed p. 293 and displays the
  attested `Soo-Jeropary` passage; the PDF link ends `#page=294`; next, reload,
  and previous preserve the page URL. `Marabá` links 142 and 143 separately;
  `tiá` shows the spaced `D' Evreux` citation linked to 143; Caruaru’s
  contextual `op. cit.` remains unlinked. Desktop and approximately 500-CSS-px
  layouts keep controls and the full fitted page usable; zoom toggles.

## What failed or needed adaptation

- Sandboxed DNS initially blocked the PDF and package downloads; approved
  network access resolved both.
- The bare checkout lacked tracked `docs/tupi_dict_navarro.*` and
  `cartas_portiguara`, which the existing Pages build requires. Temporary
  copies from the baseline checkout were supplied only for build verification.
- The existing project virtualenv lacked `setuptools`; a temporary uv-managed
  environment with the declared requirements, `setuptools`, and `wheel`
  allowed the full build to complete.
- Repository-wide `make lint` remains red on four pre-existing baseline files:
  `pydicate/pydicate/lang/tupilang/pos/{deverbal,verb}.py` and
  `pydicate/tests/{test_compound_annotations,test_nominal_annotation_preservation}.py`.
  Black passes for both new data scripts; those unrelated files were not
  reformatted in this pilot.
- The first inventory regeneration differed only in gzip header byte 9 across
  Python/zlib versions. The writer now normalizes that byte; two consecutive
  runs produced the same SHA-256
  `f76645151b083b83fa89efa96d96f2f452ec6cddddb4bb9a8fc73f29105a1be3`.

## Remaining questions

- Human review is still needed for scan legibility, alignment, viewer wording,
  and the repository-size tradeoff of adding 259.3 MiB of source JPEGs.
- The inventory’s unresolved work/edition/locator rows remain a research queue,
  not authority to digitize or link another source.
- The implementation must not be merged or deployed, and no next book should
  be started, until Kian approves this pilot.

## Suggested next prompt

> Review the D’Evreux implementation PR. Check the p. 293 click-through,
> title-page/1874-edition caveat, neighboring-page navigation, mobile fit,
> source inventory, and Pages artifact size. If it is acceptable, explicitly
> authorize the next source or request focused revisions; do not broaden the
> work implicitly.
