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
- Fixed `scripts/build_pages.sh` to copy only derived image files from primary-source folders, excluding raw PDFs and extraction/source files from `.pages-build`.
- Added a `scripts/deploy_gh_pages.sh` preflight that fails before commit/push if any Pages artifact file exceeds 100 MB.
- Fixed `scripts/deploy_gh_pages.sh` worktree detection so an existing Git worktree with a `.git` file is accepted.
- Verified `make pages-build` creates an artifact with no PDFs/source formats and no files over 100 MB.
- Added build-only primary-source image optimization with Pillow and generated `image-formats.json` support in the citation viewer.
- Excluded `bettvulg` from the Pages artifact because no runtime references were found and it was about 1.7 GB of page images.
- Verified the optimized Pages artifact is about 477 MB, with primary-source images reduced to about 432 MB.

## 2026-09-12

- Refreshed `origin` and confirmed the large source cleanup commit was already published on `cleanup-public-assets-kian`.
- Rebuilt the optimized Pages artifact successfully and reran lint, shell syntax, Python compilation, and whitespace checks.
- Confirmed the remote still has no `gh-pages` branch, while the local Pages worktree retains the failed 4.1 GB root commit.
- Kept site publication separate from the source-branch push because the unpublished local Pages branch must first be recreated without its oversized history.
