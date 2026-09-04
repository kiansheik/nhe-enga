# Public Assets Gh-Pages Cleanup

## Goal

Identify every asset the repository expects GitHub Pages to serve, then separate generated public output from the source branch by building a reviewable Pages artifact and deploying it through `gh-pages`.

## Files Inspected

- `AGENTS.md`
- `tupi/AGENTS.md`
- `README.md`
- `Makefile`
- `.gitignore`
- `index.html`
- `js/index.js`
- `quiz/index.html`
- `quiz/quiz.js`
- `katu/index.html`
- `mbya/index.html`
- `neologisms/index.html`
- `sentence-builder.html`
- `translate/index.html`
- `docs/primary_sources/index.html`
- `gramatica/docs/package.json`
- `gramatica/docs/src/.vuepress/config.js`
- `gramatica/docs/src/.vuepress/components/PyodideLoader.vue`
- `gramatica/docs/src/guide/.vuepress/`

## Files Changed

- `.gitignore`
- `Makefile`
- `README.md`
- `requirements.txt`
- `verbs.py`
- `sentence-builder.html`
- `gramatica/docs/src/.vuepress/components/PyodideLoader.vue`
- `gramatica/docs/src/.vuepress/public/favicon.ico`
- `gramatica/docs/src/.vuepress/public/icon.png`
- `scripts/build_pages.sh`
- `scripts/deploy_gh_pages.sh`
- `docs/agent/index.md`
- `docs/agent/current-state.md`
- `docs/agent/repo-map.md`
- `docs/agent/open-questions.md`
- `docs/agent/served-assets.md`
- `docs/agent/log.md`
- Removed from source branch index: generated VuePress publish output under `gramatica/`, generated grammar public wheels, Transcrypt `__target__` output, duplicate nested VuePress source under `gramatica/docs/src/guide/.vuepress/`, and tracked `.DS_Store` files.

## Commands Run

- `rg` and targeted `find`/`sed` reads to map runtime references.
- `git switch -c cleanup-public-assets-kian`
- `git ls-remote --heads origin gh-pages`
- `git mv` for the grammar favicon/icon move.
- `git rm -r --ignore-unmatch ...` for generated output removals.
- `chmod +x scripts/build_pages.sh scripts/deploy_gh_pages.sh`
- `make pages-build`
- `find .pages-build -name 'google_api_keys.json' -o -name 'api_usage_log.json' -o -name 'tupi-dic-cop*.docx'`
- Required artifact checks with `test -f` and `test -d`.
- `make lint`
- Follow-up on 2026-09-04: `make gen_data`
- Follow-up on 2026-09-04: `make help`, `make setup`, `make node-deps`

## What Worked

- Created cleanup branch `cleanup-public-assets-kian`.
- Confirmed no remote `gh-pages` branch existed at inspection time.
- Documented the served/runtime asset set in `docs/agent/served-assets.md`.
- Added a Pages build artifact flow that assembles `.pages-build` from an allowlist.
- Added a deploy flow that can publish `.pages-build` through a local `.gh-pages-worktree` and create an orphan `gh-pages` branch if needed.
- Moved grammar favicon/icon assets from the duplicate nested VuePress tree into the active VuePress public directory.
- Updated `sentence-builder.html` to install the generated wheel from `/nhe-enga/gramatica/pylibs/`.
- Guarded grammar dictionary loading during VuePress SSR; `make pages-build` no longer emits the previous server-side fetch error for `/nhe-enga/docs/dict-conjugated.json.gz`.
- Verified `.pages-build` contains required app, docs, primary-source, and grammar assets.
- Verified `.pages-build` does not include local translate key/log files or local DOCX exports.
- Verified `make pages-build` and `make lint` pass.
- Follow-up on 2026-09-04: `make gen_data` now bootstraps `.venv` from `requirements.txt` and completed successfully after adding the missing `tqdm` dependency.
- Follow-up on 2026-09-04: `make help` now prints the start-to-finish flow: `make setup`, `make gen_data`, `make pages-build`, then `make deploy-gh-pages`.

## What Failed

- The first broad `git rm` attempt failed because one named build path was not tracked; reran with the tracked/removable paths and `--ignore-unmatch`.
- `make pages-build` still emits packaging deprecation/package-discovery warnings and VuePress plugin/update-check warnings, but exits 0.
- Follow-up on 2026-09-04: initial `make gen_data` failed because bare `python3.11` lacked `python-docx`; the first venv target used `.venv/bin/python` directly, which could appear complete after a failed install. It was replaced with a `.venv/.requirements-installed` stamp written only after pip succeeds.

## Remaining Questions

- Should generated dictionary/data files under `docs/` move out of the source branch too, once there is a reliable data-generation or artifact-preservation step?
- Should primary-source page images move out of the source branch after adding a reliable regeneration or external artifact sync?
- Is `sentence-builder.html` still a supported public page, and should it get a browser-level smoke test?
- Are root-level legacy static/prototype pages such as `full.html`, `orthography_mapper_live_csv_learner_mvp.html`, and `translate/index.html` still intended to be public?
- Are `gramatica/package.json` and `gramatica/package-lock.json` leftovers now that `gramatica/docs/package.json` is the active VuePress package?
- Should `make deploy-gh-pages` become part of CI/release automation, or remain a manual publish command?

## Suggested Next Prompt

Review the cleanup diff and decide whether to keep all runtime data in `main` for now or add a second pass that regenerates/preserves `docs/` data and primary-source images outside the source branch.
