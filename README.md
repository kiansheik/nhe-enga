# nhe-enga

Digital field notes, datasets, and tooling focused on Tupi Antigo (Old Tupi) and related Tupi-Guarani languages. This repository mixes linguistic research, data extraction pipelines, a Python morphology engine, a predicate-logic DSL, and the static sites that expose the material to learners.

## Table of contents

- [Project goals](#project-goals)
- [Repository tour](#repository-tour)
- [Datasets and generated artifacts](#datasets-and-generated-artifacts)
- [Python toolkits](#python-toolkits)
- [Web experiences](#web-experiences)
- [Development environment](#development-environment)
- [Common workflows](#common-workflows)
- [Testing and QA](#testing-and-qa)
- [Data provenance](#data-provenance)
- [Contributing and next steps](#contributing-and-next-steps)

## Project goals

- Preserve and make searchable Eduardo de Almeida Navarro’s *Dicionário de Tupi Antigo* and other primary sources (Anchieta, Bettendorff, Dooley, Nheengatu corpora, etc.).
- Offer a programmable morphology/conjugation engine (`tupi/`) that understands pluriform verbs, nasal harmony, object incorporation, orthographic variants, and irregular paradigms.
- Provide a composable predicate calculus (`pydicate/`) for building interlinear glosses, syntactic trees, and annotated sentences that plug into the dictionary data.
- Publish learner-facing material (dictionary viewer, conjugation quiz, VuePress grammar, Pyodide playgrounds) as static pages that can be hosted anywhere.
- Experiment with translation and lexicography workflows (LLM prompts, automatic glossing, tokenizer experiments, custom models).

## Repository tour

| Path | Purpose |
| --- | --- |
| `docs/` | Canonical data dumps: Navarro dictionary JSON/JS, conjugations (`dict-conjugated*.json*`), extracted sources, neologism exports, and supporting CSV/JSON artifacts. |
| `tupi/` | Installable Python package exposing `TupiAntigo`, `Verb`, `Noun`, `AnnotatedString`, orthography maps, and irregular paradigms plus bundled resources (`alt_ort`, `irregular`). |
| `pydicate/` | Installable Python package that layers a predicate DSL (`Predicate`, `Trackable`) with Tupi-specific POS implementations (`lang/tupilang/pos/*`) and a SQLite-backed lexeme explorer. |
| `gramatica/` | VuePress documentation site (guide + playground). Builds wheel files into `docs/src/.vuepress/public/pylibs/` so Pyodide can import `tupi`/`pydicate` inside the browser. |
| `index.html`, `sentence-builder.html`, `styles.css`, `js/` | Main dictionary UI and Pyodide-powered sentence builder that load `docs/dict-conjugated.json(.gz)` straight from the repo. |
| `quiz/` | Interactive conjugation quiz that reads the same conjugation dataset and drills moods/arguments. |
| `katu/`, `mbya/` | Parallel dictionary viewers for Nheengatu and Mbyá Guarani built from the extracted datasets under `docs/`. |
| `translate/` | Prompt templates, batching scripts, and a tiny UI for LLM-assisted translation. Requires API keys (`google_api_keys.json`) and logs usage in `api_usage_log.json`. |
| `tests/`, `test_pydicate.py` | Manual/interactive harnesses for validating noun transformations and predicate composition logic. |
| `docs/primary_sources/` | OCR inputs (PDFs, bibliography, output pngs) used by the extraction scripts (`mbya_dooley_miner.py`, `nheengatu_dict_miner.py`, `source_extraction.py`). |
| `Makefile` | Helper targets for rebuilding wheels, copying them into the docs site, building VuePress, and refreshing the Google Sheets driven neologism CSV. |

The root also keeps scratch scripts (`gen_data.py`, `verbs.py`, `gen_tokenizer.py`, `nheengatu_pluriforme_fix.py`, etc.), charts in `imgs/`, and prototype notebooks under `models/`.

## Datasets and generated artifacts

Most front ends read straight from the JSON blobs inside `docs/`. Key files:

- `docs/tupi_dict_navarro.json` / `docs/tupi_dict_navarro.js`: dictionary entries parsed from Navarro’s DOCX via `gen_data.py`. The JS exports `window.jsonData` for the static site.
- `docs/dict-conjugated.json.gz`: main dataset produced by `verbs.py`. Each record has the lemma (`f`), optional numeric suffix (`o`), definition (`d`), verb metadata (`v`, `i`), and—when applicable—`c`, a list of conjugated forms annotated with subject/object prefixes, moods, and negative stems.
- `docs/extracted_entries_nheengatu.json` / `.tar.gz`, `docs/dooley_2006_mbya_dic.json(.gz)`: parsed outputs from the mining scripts for other Tupian dictionaries.
- `docs/primary_sources/*`: bibliography, PDFs, and derived page images to trace every citation back to Anchieta (Arte/Teatro), Bettendorff, VLB, etc.

Rebuild the Navarro data and conjugation tables when the source DOCX changes:

```bash
python3.11 gen_data.py              # updates docs/tupi_dict_navarro.{json,js}
python3.11 verbs.py                 # recomputes conjugations and dict-conjugated.json(.gz)
cp docs/dict-conjugated.json.gz pydicate/pydicate/lang/tupilang/data/
```

The `make gen_data` target wraps those commands and keeps `pydicate`’s bundled data in sync.

## Python toolkits

### `tupi`

`tupi/` exposes the morphology engine used everywhere else. Highlights:

- `tupi.tupi.TupiAntigo`: phonology helpers, orthography conversion, nasal harmony, personal inflections, gerund/permissive maps, etc.
- `tupi.noun.Noun`: agglutination/composition helpers, possessives, vocative/absolutive derivations, noun→verb transformations, and annotated-string aware mutation utilities.
- `tupi.verb.Verb`: smart conjugator that understands pluriform classes, irregular paradigms stored under `tupi/irregular/`, negation rules, circumstantial moods, reduplication, and object incorporation.
- `tupi.annotated_string.AnnotatedString`: low-level helper for mutating text that interleaves bracketed morphology tags with clean orthography.
- `tupi.orth`: alternate orthography tables (Anchieta, etc.) and heuristics for nasalization probability.

Example:

```python
from tupi import Verb

ver = Verb("epîak", "(v.tr.)", "to see")
# ixé osé epîak - "I see myself" (reflexive)
print(ver.conjugate(subject_tense="1ps", object_tense="refl", mode="indicativo"))
# 'a'e oseepîak? -> toggling negation or other moods is just extra flags:
print(ver.conjugate(subject_tense="3p", mode="circunstancial", negative=True))
```

### `pydicate`

`pydicate/` adds a predicate-logic surface over the morphology engine.

- `Predicate` (`pydicate/predicate.py`): stores arguments, adjuncts, negation, variable tracking, and evaluation hooks.
- `pydicate/lang/tupilang/pos/*`: concrete POS classes (`Noun`, `Verb`, `Adverb`, `Postposition`, `Deverbal`, `Classifier`, demonstratives, numbers, particles, interjections) with rich operator overloading (`*` for arguments, `/` for composition, `+` for adjuncts, unary `-` for negation, etc.).
- `pydicate/dbexplorer.NavarroDB`: wrapper around `pydicate/tupi_only.db` so predicates can pull glosses, definitions, and bilingual citations from the SQLite cache.
- `pydicate/lang/tupilang/data/dict-conjugated.json.gz`: bundled conjugation dataset consumed by the POS classes so they can lazily hydrate definitions and irregular forms.

Example sentence:

```python
from pydicate.lang.tupilang import abá, ixé
from pydicate.lang.tupilang.pos import Verb, Adverb

só = Verb("só", definition="to go")
koritei = Adverb("koritei", definition="quickly")

clause = koritei + só * ixé
print(clause.eval())           # koritei ixé asó
print(clause.eval(True))       # koritei[ADVERB] ixé[SUBJECT:1ps] asó[MAIN_VERB]
```

`test_pydicate.py` also shows how to render syntax trees with Graphviz via the `build_graphviz` helper.

## Web experiences

- **Dictionary + conjugation UI (`index.html` / `sentence-builder.html`)**: vanilla JS app that reads `docs/dict-conjugated.json(.gz)` and optionally spins up Pyodide to call the `tupi` wheel in-browser for on-the-fly conjugations and noun derivations.
- **Grammar site (`gramatica/`)**: VuePress 1.x site that mirrors the research write-up. It embeds a Pyodide `<iframe>` (`gramatica/iframe_pyodide.html`) so code fences tagged as exercises can be executed with the real `tupi` package. Build output lives in `gramatica/docs/src/.vuepress/dist/` and is copied into `gramatica/` for GitHub Pages.
- **Quiz (`quiz/`)**: replicates conjugation drills by randomly sampling the conjugation dataset and asking for mood, subject, and object. Good regression test for dataset sanity.
- **Other dictionaries (`katu/`, `mbya/`)**: share the same UI shell but load Nheengatu and Mbyá datasets generated by their respective mining scripts.
- **Playground (`gramatica/guide/tools/playground.md`)**: uses Vue components to ask morphology questions and checks answers through Pyodide.
- **Translation experiments (`translate/`)**: batch scripts (`batch_translate.py`, `generate_glosses.py`) rotate through Google/Anthropic API keys, parse annotated sentences, and hydrate `tupi_to_eng*.csv`. `translate/index.html` is a tiny front end that hits a local Gradio endpoint for human-in-the-loop annotation.

## Development environment

Core tooling:

- Python 3.11 (some scripts rely on pattern matching and standard-library behavior added after 3.9).
- Node 16+ (VuePress 1.5.3 and legacy plugins expect CommonJS/webpack 4 behavior).
- Yarn or npm (VuePress build), `black` (optional formatting), and `graphviz` (if you want to render trees from `test_pydicate.py`).
- System libs for PDF/OCR tooling if you plan to rerun extraction scripts (`poppler`, `tesseract`, `pdfminer.six`, `pdfplumber`, `pdf2image`).

Suggested setup:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt          # only python-docx is pinned, install extras as needed:
pip install tqdm pdfminer.six pdfplumber anthropic requests ratelimit graphviz pdf2image

cd gramatica/docs
npm install
```

When building Pyodide wheels, the Makefile assumes `python3.11` and a working `npm` plus `curl` on macOS/Linux.

## Common workflows

### Preview the static dictionary

```bash
python3 -m http.server 8000
# open http://localhost:8000/index.html and try queries (supports URL ?query=foo)
```

The same server will expose `/quiz`, `/katu`, `/mbya`, `/sentence-builder.html`, etc.

### Build the VuePress grammar

```bash
cd gramatica/docs
NODE_OPTIONS=--openssl-legacy-provider npm run dev     # hot reload
NODE_OPTIONS=--openssl-legacy-provider npm run build   # emits dist/
cd ../..
cp -r gramatica/docs/src/.vuepress/dist/* gramatica/
```

The `Makefile lint` target automates wheel builds, copies them to `gramatica/docs/src/.vuepress/public/pylibs/`, builds the docs, publishes to `gramatica/`, and refreshes the neologism CSV from Google Sheets.

### Package the Python libs

```bash
cd tupi
python3.11 setup.py sdist bdist_wheel
cd ../pydicate
python3.11 setup.py sdist bdist_wheel
```

These wheels are the ones copied into `gramatica/` and `tupi-annotation-suite`, and they are what Pyodide installs at runtime.

### Run translation/glossing experiments

1. Populate `translate/google_api_keys.json` with API keys (`["key1", "key2", ...]`).
2. Activate the virtualenv and install `requests`, `ratelimit`, `anthropic`, etc.
3. Run `python translate/generate_glosses.py` or `python translate/batch_translate.py`. Outputs land in `translate/tupi_to_eng*.csv` and usage is tracked in `translate/api_usage_log.json`.
4. Fire up a Gradio service (outside this repo) and open `translate/index.html` to test a prompt end-to-end.

### Mining new dictionaries

- Nheengatu: adjust `docs/primary_sources/2021_MarcelTwardowskyAvila_VCorr_dic.pdf` and run `python nheengatu_dict_miner.py`, then `python nheengatu_pluriforme_fix.py`.
- Mbyá: drop the Dooley PDF in `docs/primary_sources/GNDicLex.pdf` and run `python mbya_dooley_miner.py`.
- Citations: use `python source_extraction.py` to rebuild the author reference counters and per-page PNGs.

## Testing and QA

- `python test_pydicate.py`: exercises sentence construction, negation, adjacency, and Graphviz rendering of predicate trees. Requires `graphviz` installed on the system.
- `python tests/build_tests_cases.py`: REPL that walks noun entries (`tests/cases.csv`) and lets you codify transformations into `tests/new_cases.csv`.
- Manual smoke tests: load `/index.html`, `/quiz/`, and `/gramatica/guide/` via `python -m http.server`, toggle “Mostrar Conjugações,” and try a few irregular verbs.

Because many scripts operate on large PDFs and external APIs, there is no single `pytest` suite. Prefer running the smallest script that touches the component you are modifying.

## Data provenance

- **Navarro dictionary**: Eduardo de Almeida Navarro, *Dicionário de Tupi Antigo*, 2007. The DOCX is not redistributed here; only derived JSON/JS needed for the UI.
- **Anchieta/Artes, VLB, Bettendorff**: stored as PDFs/images under `docs/primary_sources/` solely for research and citation. Respect the copyrights of the original works.
- **Nheengatu dataset**: parsed from Marcel Twardowsky Avila’s 2021 dissertation (*Proposta de dicionário nheengatu-português*).
- **Mbyá dataset**: parsed from Robert A. Dooley’s *Léxico Guarani, Dialeto Mbyá* (SIL, 2006).
- **Neologisms**: pulled from the Google Sheet referenced inside the Makefile (`neologisms.csv`).
- **LLM outputs**: `translate/tupi_to_eng*.csv` contains model suggestions. Treat them as drafts that still need human review.

If you publish derivatives, cite the original authors and this toolkit.

## Contributing and next steps

This codebase has grown organically; expect rough edges. Ideas that would add immediate value:

1. Automate a leaner build pipeline (`make lint` currently does many unrelated tasks).
2. Replace the ad-hoc HTTP calls in the static UIs with a small build step that precomputes search indexes and conjugation tables.
3. Expand the test coverage around `tupi.noun` transformations (the REPL only writes CSVs today).
4. Document the translation prompts and APIs inside `translate/` so others can reproduce the experiments safely.
5. Split large datasets into a separate storage bucket/Git LFS to keep clone sizes manageable.

Feel free to open issues or drafts describing what you are trying to clean up; even partial notes are useful when dealing with historical linguistic material.
