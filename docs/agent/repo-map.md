# Repo Map

## Runtime Static Site

- Root dictionary: `index.html`, `styles.css`, `manifest.json`, `favicon.ico`, `js/index.js`, `js/pako.min.js`, `js/papaparse.min.js`.
- Dictionary data: `docs/dict-conjugated.json.gz`; legacy `sentence-builder.html` also reads `docs/dict-conjugated.json`.
- Neologisms: `neologisms.csv` and `neologisms/index.html`.
- VLB reader: `vlb/`, linked from the root navigation and VLB dictionary
  citations. `vlb/data/` contains generated page and citation indexes;
  `vlb/source/` pins the compact transcription/alignment inputs and
  `vlb/build_data.py` regenerates the projection without network access.
  `?volume=I&page=17&entry=<row>` opens the printed page and scopes its Navarro
  citations to the originating dictionary row. Associations distinguish
  reviewed links from unreviewed suggestions; page alignment alone does not
  establish lexical identity. Both viewers reuse the original scan URLs and
  `image-formats.json`, so no second scan collection is added.
- Quiz: `quiz/index.html`, `quiz/quiz.js`, `quiz/styles.css`; loads `../docs/dict-conjugated.json.gz`.
- Nheengatu and Mbya pages: `katu/index.html`, `mbya/index.html`; load `docs/extracted_entries_nheengatu.tar.gz` and `docs/dooley_2006_mbya_dic.json.gz`.
- Citation viewer: `docs/primary_sources/index.html`; opens page images under
  `docs/primary_sources/{vlb,ancharte,anchteatro1954,arcat1618,arcat1686,betcomp,castilho1937,evreux1929,figueira1878,lerhist}`.
  The 1686 Araújo directory is intentionally sparse: all currently cited
  printed pages plus a two-page context buffer, not the complete scan.
  `figueira1878` is a complete scan with a constant printed-page map;
  `anchteatro1954` is a sparse 75-page quotation-level cross-edition map for
  every current 1999/2006 citation locator, not a general pagination map.
  `castilho1937` stores 16 verified page-side crops behind an explicit
  non-linear map. D’Evreux, Figueira, Anchieta, and
  Castilho provenance and page mappings live beside their images in
  `source.json` and `README.md`. The
  `cartas_portiguara` image folder is preserved in the Pages artifact for now;
  `bettvulg` is excluded because no runtime references were found.
- Grammar site: source is `gramatica/docs/src`; built output belongs in the Pages artifact under `gramatica/`, not tracked on the source branch.

## Generated Or Reproducible Outputs

- VuePress publish output: `gramatica/assets/`, `gramatica/guide/`, `gramatica/index.html`, `gramatica/404.html`, copied public files, copied `pylibs/`, and Pages metadata.
- Python packaging output: `tupi/build/`, `tupi/dist/`, `tupi/tupi.egg-info/`, `pydicate/build/`, `pydicate/dist/`, `pydicate/pydicate.egg-info/`.
- Transcrypt output: `__target__/`, `tupi/**/__target__/`, `pydicate/**/__target__/`.

## Script Layout

- `scripts/data/`: maintained Navarro, conjugation, Nheengatu, Mbyá, and
  primary-source data pipelines. `source_inventory.py` audits the served
  dictionary and production citation linker; `render_source_pages.py` renders
  checksum-verified source PDFs. Run from the repository root because their
  data paths are checkout-relative.
- `scripts/qa/`: optional real-browser audit tools. The dictionary entry
  sampler selects reproducible long-entry samples and captures the production
  `.entry` DOM plus initial/expanded page geometry for qualitative formatting
  and footer review; its Playwright dependency is intentionally audit-only.
- `tests/dictionary_formatting.test.cjs`: dependency-free corpus structural
  and source-token-preservation invariants executed directly against the
  production formatter and served gzip. `tests/dictionary_formatting_browser.py`
  holds focused semantic and layout regressions against the real
  search/render/highlight path in Chromium.
- `tests/test_vlb_viewer_data.py`: offline VLB projection and source-accounting
  checks. `tests/vlb_viewer_browser.cjs` exercises the reader's responsive panes,
  citation/source navigation, OCR overlays, search, and exported review notes.
- `.github/workflows/dictionary-formatting.yml`: path-filtered pull-request CI
  for the dictionary and VLB regressions, with Python and Node Playwright both
  pinned to 1.55.0 and sharing one Chromium installation. Its sparse checkout
  includes seven existing VLB scans; browser screenshots and result JSON are
  retained as a CI artifact.
- `scripts/media/`: optional PDF-bookmark and WAV-to-Opus utilities; generated outputs are not versioned.
- `scripts/build_pages.sh`, `scripts/deploy_gh_pages.sh`, `scripts/optimize_pages_images.py`: maintained Pages build and deployment tooling.
- `misc/experiments/`: retained historical research scratchpads, machine-local model experiments, and the manual Pydicate/Graphviz story harness. Nothing under `misc/` is a build or deployment dependency.

## Build Entrypoints

- `make lint`: check formatting only.
- `make format`: run Black.
- `make help`: print the start-to-finish setup, data generation, Pages build, and deploy flow.
- `make setup`: install Python dependencies and ensure VuePress Node dependencies exist.
- `make build-wheels`: build `tupi` and `pydicate` wheels and copy them into VuePress public assets.
- `make grammar-build`: build the VuePress grammar.
- `make pages-build`: assemble `.pages-build` from a static allowlist, copy only derived primary-source images, optimize those copied images for web delivery, then add the built grammar site under `gramatica/`.
- The static allowlist includes the `vlb/` frontend, generated data, and linked
  PDF provenance; rebuild scripts and compact intermediate inputs stay on the
  source branch. Reader/data assets join the core
  offline pack, while VLB scan images remain in the existing `source-vlb` pack.
- `make deploy-gh-pages`: publish `.pages-build` to `gh-pages`.
- `make gen_data`: create/update `.venv`, install `requirements.txt`, run `scripts/data/gen_data.py` and `scripts/data/verbs.py`, and copy the bundled conjugation gzip into `pydicate`.
