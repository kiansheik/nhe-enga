# Top-Level Script Cleanup

## Goal

Make the repository root presentable after the Pages migration by classifying scripts, removing provably generated clutter, and preserving all maintained build and runtime behavior.

## Files Inspected

- All tracked top-level files and their sizes, types, references, and latest history
- `Makefile`
- `README.md`
- `.gitignore`
- `scripts/build_pages.sh`
- Root Python, shell, and JavaScript scripts
- Public `katu/index.html` and `mbya/index.html` asset references
- `docs/agent/` repository and served-asset maps
- The rebuilt `.pages-build` artifact and currently deployed `.gh-pages-worktree`

## Files Changed

- Moved maintained data pipelines from the root to `scripts/data/`
- Moved optional PDF/audio utilities from the root to `scripts/media/`
- Moved historical scratchpads from the root to `misc/experiments/`
- Added ownership READMEs under `scripts/data/`, `scripts/media/`, and `misc/`
- Updated `Makefile`, `README.md`, `.gitignore`, `scripts/build_pages.sh`, `katu/index.html`, and `mbya/index.html`
- Updated `docs/agent/current-state.md`, `repo-map.md`, `open-questions.md`, `served-assets.md`, and `log.md`
- Removed `.nojekyll` from the source root because the Pages builder generates it in `.pages-build`
- Removed generated root PDFs, DOCX, and Graphviz files

## Commands Run

- Targeted `git`, `find`, `rg`, `file`, `wc`, `shasum`, and source reads to classify root files and trace references
- `make -n gen_data`
- `.venv/bin/python scripts/data/gen_data.py`
- `make lint`
- `bash -n scripts/build_pages.sh scripts/deploy_gh_pages.sh scripts/media/audio_compress.sh`
- `.venv/bin/python -m py_compile scripts/data/*.py scripts/media/add_bookmarks.py misc/experiments/*.py`
- `node --check misc/experiments/dl_src.js`
- `make pages-build`
- Pages artifact size, excluded-format, maximum-file-size, calendar-icon, and live-tree comparison checks
- `git diff --check`

## What Worked

- The root no longer contains standalone scripts; maintained automation is under `scripts/` and retained experiments are explicitly under `misc/`.
- `make gen_data` resolves the relocated Navarro and conjugation generators, and the relocated Navarro generator runs successfully from the repository root.
- The media helper shell syntax passes; its stale empty Ogg-directory handling was removed and argument validation was added.
- Repository-wide Black, moved Python compilation, legacy JavaScript parsing, shell syntax, and whitespace checks pass.
- The full Pages build still completes at about 477 MB with 1,407 optimized images and no file over 100 MB.
- The Pages artifact includes `ical.png`, and both secondary dictionaries now resolve it from their parent directory.
- Removed artifacts were absent from the Pages allowlist and had no runtime or build consumers.

## What Failed

- A first metadata loop accidentally used zsh's special lowercase `path` variable, which temporarily hid commands from `PATH`; rerunning with a neutral loop variable completed the inventory.
- `py_compile` exposed an existing invalid `\s` string escape in the machine-local model experiment; it was changed to the equivalent raw regex string.
- The full Pages build still emits existing setuptools package-discovery/deprecation and VuePress update-check warnings, but exits successfully.

## Remaining Questions

- The remaining root-level annotation/training JSON and text files need provenance review before moving; no consumer was found, but their intended regeneration contract is unclear.
- `AGENT_NOTES.md` appears to be a stale historical handoff but was retained until its unique content is reconciled with `docs/agent/`.
- Legacy public HTML prototypes remain in the root because the Pages allowlist still publishes them and support status is unresolved.

## Suggested Next Prompt

Trace the remaining root-level research data files and either move them into a documented data directory with producer paths updated or remove them if they are reproducible and unused.
