# Agent Log

## 2026-09-02

- Created branch `cleanup-public-assets-kian`.
- Confirmed `docs/agent/index.md`, `current-state.md`, `repo-map.md`, and `open-questions.md` were missing at session start.
- Identified static served assets for the root dictionary, quiz, grammar site, Nheengatu/Mbya pages, neologisms page, legacy sentence builder, translate prototype, and citation viewer.
- Split mutating `Makefile lint` behavior into check-only lint, explicit formatting, wheel build, grammar build, Pages build, and gh-pages deploy targets.
- Added `scripts/build_pages.sh` and `scripts/deploy_gh_pages.sh`.
- Removed tracked generated VuePress publish output, Transcrypt `__target__` output, generated grammar public wheels, duplicate nested VuePress config, and `.DS_Store` files from the source branch index.
- Moved grammar favicon/icon assets into the active VuePress public directory.
- Updated `sentence-builder.html` to use the generated Pages wheel path under `/nhe-enga/gramatica/pylibs/`.
- Guarded grammar dictionary loading during VuePress SSR so the static build no longer tries to fetch `/nhe-enga/docs/dict-conjugated.json.gz` while rendering on Node.
- Verified `make pages-build` and `make lint` pass.
- Verified `.pages-build` includes required runtime assets and excludes local translate key/log files and local DOCX exports.

## 2026-09-04

- Fixed `make gen_data` after bare `python3.11` failed to import `docx`.
- Added a repo-local `.venv`/requirements stamp target so `make gen_data` installs declared Python dependencies before running data generators.
- Added `tqdm` to `requirements.txt` because `verbs.py` uses it.
- Removed unused `matplotlib.pyplot` import from `verbs.py` instead of adding a plotting dependency.
- Verified `make gen_data` completes after installing dependencies.
- Added `make help`, `make setup`, and `make node-deps` so the build/deploy path is discoverable from the Makefile.
- Documented the full flow as `make setup`, `make gen_data`, `make pages-build`, then `make deploy-gh-pages`.
- Verified `make help`, `make setup`, `make node-deps`, and `make lint`.
