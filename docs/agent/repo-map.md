# Repo Map

## Runtime Static Site

- Root dictionary: `index.html`, `styles.css`, `manifest.json`, `favicon.ico`, `js/index.js`, `js/pako.min.js`, `js/papaparse.min.js`.
- Dictionary data: `docs/dict-conjugated.json.gz`; legacy `sentence-builder.html` also reads `docs/dict-conjugated.json`.
- Neologisms: `neologisms.csv` and `neologisms/index.html`.
- Quiz: `quiz/index.html`, `quiz/quiz.js`, `quiz/styles.css`; loads `../docs/dict-conjugated.json.gz`.
- Nheengatu and Mbya pages: `katu/index.html`, `mbya/index.html`; load `docs/extracted_entries_nheengatu.tar.gz` and `docs/dooley_2006_mbya_dic.json.gz`.
- Citation viewer: `docs/primary_sources/index.html`; opens page images under `docs/primary_sources/{vlb,ancharte,arcat1618,betcomp,lerhist}`. Existing sibling source folders `bettvulg` and `cartas_portiguara` are also preserved in the Pages artifact.
- Grammar site: source is `gramatica/docs/src`; built output belongs in the Pages artifact under `gramatica/`, not tracked on the source branch.

## Generated Or Reproducible Outputs

- VuePress publish output: `gramatica/assets/`, `gramatica/guide/`, `gramatica/index.html`, `gramatica/404.html`, copied public files, copied `pylibs/`, and Pages metadata.
- Python packaging output: `tupi/build/`, `tupi/dist/`, `tupi/tupi.egg-info/`, `pydicate/build/`, `pydicate/dist/`, `pydicate/pydicate.egg-info/`.
- Transcrypt output: `__target__/`, `tupi/**/__target__/`, `pydicate/**/__target__/`.

## Build Entrypoints

- `make lint`: check formatting only.
- `make format`: run Black.
- `make help`: print the start-to-finish setup, data generation, Pages build, and deploy flow.
- `make setup`: install Python dependencies and ensure VuePress Node dependencies exist.
- `make build-wheels`: build `tupi` and `pydicate` wheels and copy them into VuePress public assets.
- `make grammar-build`: build the VuePress grammar.
- `make pages-build`: assemble `.pages-build` from a static allowlist, then add the built grammar site under `gramatica/`.
- `make deploy-gh-pages`: publish `.pages-build` to `gh-pages`.
- `make gen_data`: create/update `.venv`, install `requirements.txt`, regenerate Navarro-derived dictionary data, regenerate conjugation data, and copy the bundled gzip into `pydicate`.
