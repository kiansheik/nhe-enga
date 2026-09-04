# Current State

- Active cleanup branch: `cleanup-public-assets-kian`.
- The source branch now separates VuePress build output from source files. The generated GitHub Pages artifact is assembled in `.pages-build` from a runtime allowlist.
- `make lint` is check-only. Use `make format` for intentional formatter writes.
- `make pages-build` builds the local Pages artifact. `make deploy-gh-pages` builds and publishes it through a local `.gh-pages-worktree`; it will create an orphan `gh-pages` branch if none exists.
- `make gen_data` bootstraps `.venv` from `requirements.txt` and then runs `gen_data.py` plus `verbs.py`.
- `make help` prints the current start-to-finish build/deploy sequence: `make setup`, `make gen_data`, `make pages-build`, then `make deploy-gh-pages`.
- Source of truth remains code, package configs, datasets, and checked-in source docs. Runtime data under `docs/` is still tracked because current static apps read it directly.
- The remote did not have a `gh-pages` branch when checked on 2026-09-02.

## Current Cautions

- Do not delete `docs/dict-conjugated.json`, `docs/dict-conjugated.json.gz`, `docs/extracted_entries_nheengatu.tar.gz`, `docs/dooley_2006_mbya_dic.json.gz`, `docs/primary_sources/index.html`, or the cited primary-source page images unless the deployment flow is changed to preserve or regenerate them.
- `sentence-builder.html` still reads `docs/dict-conjugated.json` and now installs the generated Pages wheel at `/nhe-enga/gramatica/pylibs/tupi-0.1.2-py3-none-any.whl`.
- The Pages artifact intentionally copies only `translate/index.html`, not local translate scripts, key files, or logs.
- `make gen_data` is noisy and can take over a minute; it updates generated dictionary/conjugation data. Keep those outputs separate from source-only cleanup changes unless intentionally refreshing data.
- `make deploy-gh-pages` pushes to the configured remote branch; do not run it unless publishing the current Pages artifact is intended.
