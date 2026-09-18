# Current State

- Active branch: `main`; the public-assets cleanup was merged in pull request 18.
- The source branch now separates VuePress build output from source files. The generated GitHub Pages artifact is assembled in `.pages-build` from a runtime allowlist.
- Maintained extraction/generation programs live under `scripts/data/`; optional PDF/audio helpers live under `scripts/media/`; historical scratchpads live under `misc/experiments/`.
- The repository root is reserved for project configuration, public static-site entrypoints, and the remaining research datasets whose ownership still needs classification.
- `make lint` is check-only. Use `make format` for intentional formatter writes.
- `make pages-build` builds the local Pages artifact. `make deploy-gh-pages` builds and publishes it through a local `.gh-pages-worktree`; it will create an orphan `gh-pages` branch if none exists.
- `make gen_data` bootstraps `.venv` from `requirements.txt` and then runs `scripts/data/gen_data.py` plus `scripts/data/verbs.py`.
- `make help` prints the current start-to-finish build/deploy sequence: `make setup`, `make gen_data`, `make pages-build`, then `make deploy-gh-pages`.
- Source of truth remains code, package configs, datasets, and checked-in source docs. Runtime data under `docs/` is still tracked because current static apps read it directly.
- GitHub Pages now publishes `gh-pages` from `/`. The first optimized deployment is root commit `ff3b1f5b`; the live build completed on 2026-09-12.
- The Pages allowlist preserves the three legacy tracked HTML routes that are not otherwise produced by the app or grammar builds: the Anchieta transcription, the irregular-verb editor, and the former source-path alias for the Pyodide iframe. Compatibility deployment `8fbaf447` restored all three live on 2026-09-14.

## Current Cautions

- Do not delete `docs/dict-conjugated.json`, `docs/dict-conjugated.json.gz`, `docs/extracted_entries_nheengatu.tar.gz`, `docs/dooley_2006_mbya_dic.json.gz`, `docs/primary_sources/index.html`, `docs/primary_sources/emerson_arte_anchieta.html`, or the cited primary-source page images unless the deployment flow is changed to preserve or regenerate them.
- `sentence-builder.html` still reads `docs/dict-conjugated.json` and now installs the generated Pages wheel at `/nhe-enga/gramatica/pylibs/tupi-0.1.2-py3-none-any.whl`.
- The Pages artifact intentionally copies only `translate/index.html`, not local translate scripts, key files, or logs.
- The shared calendar icon is published at `/nhe-enga/ical.png`; the `katu/` and `mbya/` pages reference it through `../ical.png`.
- The Pages artifact intentionally copies only derived primary-source page images from citation folders, not raw PDFs, EPUBs, MOBIs, OPFs, TXT files, or extraction scripts.
- `make pages-build` optimizes copied primary-source images inside `.pages-build` only. Source scans are left untouched; generated `image-formats.json` lets the citation viewer load optimized `.jpg` files.
- `bettvulg` is excluded from the Pages artifact for now because no runtime references were found and it dominates artifact size.
- Latest measured optimized `.pages-build` size is about 477 MB with primary-source images at about 432 MB.
- The failed 4.1 GB deployment history is preserved locally as `gh-pages-oversized-backup-20260912`; it is not reachable from the published `gh-pages` branch and must not be pushed.
- Root-level PDFs, DOCX output, and Graphviz renderings removed in the 2026-09-12 cleanup were generated and unreferenced. They remain recoverable from Git history and are now covered by ignore rules where needed.
- `make gen_data` is noisy and can take over a minute; it updates generated dictionary/conjugation data. Keep those outputs separate from source-only cleanup changes unless intentionally refreshing data.
- `make deploy-gh-pages` pushes to the configured remote branch; do not run it unless publishing the current Pages artifact is intended.

## 2026-09-17 — Compound modifier annotations

- Pydicate composition preserves a simple lexical noun modifier's existing `[ROOT]` metadata in both `Predicate.compose` and `Deverbal._apply_compositions`. Araújo 81 now retains `ypy[ROOT]`; spelling and analysis are unchanged.
- Five focused engine tests and six existing corpus contrasts pass; all 122 historical surfaces remain identical. The strict source/JSONL audit still finds pre-existing missing location metadata at Araújo 74, and 81–82 remain unsaved. See [handoff](session-handoffs/2026-09-17-compound-annotations.md).
