# Current State

## 2026-10-06 — D’Evreux 1929 primary-source pilot

- The implementation branch `devreux-primary-source` adds the complete
  444-page 1929 *Viagem ao Norte do Brasil* scan under
  `docs/primary_sources/evreux1929/`, with checksum-validated provenance and a
  reproducible whole-page renderer. The PDF itself remains outside Git.
- `linkSources()` now links all 120 explicit `D'Evreux, Viagem` citations in
  113 dictionary records. The 121 anchors cover the 42 verified printed pages;
  range endpoints remain separate, displayed citation text is unchanged, and
  contextual `op. cit.` text remains unresolved.
- The viewer distinguishes scan positions from printed pages, provides bounded
  navigation, shareable URLs, direct image/PDF links, fit/native-size zoom, and
  a visible failure state. Existing Anchieta, Araújo, Bettendorff, Léry, and VLB
  viewer behavior has focused regression coverage.
- The exact 121,180,986-byte PDF has SHA-256
  `1e6c7d93aa7e49f6cf76dd5ae84384e71ab40de592495f21b5708e4cdab61864`
  and 444 pages. A clean PyMuPDF 1.26.6/Pillow 12.3.0 rerender matched all 444
  checked-in JPEGs byte for byte. Source images occupy 259.3 MiB; the Pages
  optimizer reduces the D’Evreux copy to 212.0 MiB.
- `make pages-build` passes with the baseline generated dictionary assets
  supplied locally. The resulting artifact is 691 MiB, includes all D’Evreux
  pages, metadata and `DTAbib.txt`, and contains no PDF. Real Chromium checks
  passed on desktop and at about 500 CSS pixels wide. Nothing was deployed or
  merged; review is required before any other source is digitized.
- The repeatable inventory currently reports 47 bibliography labels, 69
  work-family rows, and 11 rows without a resolved bibliography match. These
  are auditable parser groupings, not proof of edition or locator identity.
  See the [implementation handoff](session-handoffs/2026-10-06-devreux-primary-source-implementation.md).

## 2026-09-25 — Historic ordinary and annotated surfaces agree

- Finite `Verb.preval` applies the same named phonetic rewrites to annotated
  output while retaining its tags. Araújo and Bettendorff 0020 now give
  `oroîasegûabo` in both rendering modes.
- Direct-argument evaluation preserves annotations when a stored subtree
  contains a proper noun. The outer verb can therefore exempt nested
  `JesusChristoabé` from the general `is` to `ix` rewrite; a common
  `Christo` contrast still renders `Chrixto`.
- `pûer_morphology` retains the real word boundary between third-person
  possessive `i` and reflexive `îe-` in Araújo 0055 and 0060. It no longer
  removes every space following an annotation group.
- All 65 engine tests and all 145 annotation audits pass. Ordinary and
  tag-stripped annotated surfaces now agree for all 145 current historic
  expressions. The engine intentionally
  changes the ordinary surfaces of Araújo and Bettendorff 0028 from
  `JesusChrixtoabé` to source-authored `JesusChristoabé`; those two saved
  ground-truth rows require editorial regeneration. The pre-existing Araújo
  record-2 metadata drift also remains. See the
  [handoff](session-handoffs/2026-09-25-historic-surface-consistency.md).
  Nothing was committed or published.

## 2026-09-25 — Both roots retained in plain noun composition

- `Predicate.compose` now preserves the already stored lexical root metadata of
  both simple noun operands. The approved Araújo and Bettendorff record 22
  expression `nde * (esá / poraûsubara)` therefore emits separate
  `esa[ROOT]` and `poraûsubar[ROOT]` pieces while retaining the ordinary surface
  `nde resaporaûsubara`.
- The guard still declines explicit `noroot`, annotated, multiword and already
  composed forms. Exactly 15 of 145 current historic records gain component
  boundaries; all 145 ordinary outputs remain identical to ground truth and all
  annotation audits pass. Seven focused composition tests, the 62-test engine
  suite and the 112-test corpus suite pass. Nothing was committed or published.

## 2026-09-24 — Annotation accountability applied locally

- The reviewed 12-file repair is applied to the active Nhe'enga checkout. The author's existing dirty `deverbal.py` is unchanged by hash; source expressions, targets, saved records and ordinary outputs are preserved. See [handoff](session-handoffs/2026-09-24-annotation-accountability.md). Nothing was committed or published.
- Nominalization retains its internal annotations and source expression; `emit` preserves separate occurrences, hierarchy display uses actual sentence tags, and null coordination has construction scope. Legacy numeric hierarchy IDs remain compatible with dictionary consumers.
- The generation gate checks live reports and saved schema-3 LaTeX snapshots, including occurrence integrity, complete stored Predicate paths and evaluation-event references. Witnesses indicate possible origins, not linguistic correctness: 654 tags have only root-output evidence and 1,962 have ambiguous child-event witnesses.
- Validation: 60 engine tests and 179 LaTeX pipeline tests pass; all 144 ordinary corpus outputs are unchanged. Original and repaired engines each run 102 corpus tests with the same existing Araújo 55 failure. Strict source/JSONL verification has the same pre-existing Araújo record-2 metadata difference; Bettendorff passes all 40 records.
- Final local PDFs build at 400/98/79 pages (doctoral/historical qualification/master's). Two independent bounded round22 rechecks found no blocking defect in the repair scope: Araújo73 remains segmented, the unrelated Araújo79 crop is excluded with an explicit gap, and dictionary headings/label guidance are repaired. The doctoral SHA256 is `109e465ed9985cc2f5fe654fe72dd87280fa7285202107a7ffd0494a097c3b08`. The 25 exact and six whitespace-normalized ordinary/annotated differences remain visible and unchanged. This unscored review is not linguistic adjudication or a whole-document verdict.

## Repository and publication state

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
- Latest measured optimized `.pages-build` size with the D’Evreux pilot is
  about 691 MiB; its 444 optimized pages account for about 212 MiB. The prior
  artifact without D’Evreux measured about 477 MB.
- The failed 4.1 GB deployment history is preserved locally as `gh-pages-oversized-backup-20260912`; it is not reachable from the published `gh-pages` branch and must not be pushed.
- Root-level PDFs, DOCX output, and Graphviz renderings removed in the 2026-09-12 cleanup were generated and unreferenced. They remain recoverable from Git history and are now covered by ignore rules where needed.
- `make gen_data` is noisy and can take over a minute; it updates generated dictionary/conjugation data. Keep those outputs separate from source-only cleanup changes unless intentionally refreshing data.
- `make deploy-gh-pages` pushes to the configured remote branch; do not run it unless publishing the current Pages artifact is intended.

## 2026-09-17 — Compound modifier annotations

- Pydicate composition preserves a simple lexical noun modifier's existing `[ROOT]` metadata in both `Predicate.compose` and `Deverbal._apply_compositions`. Araújo 81 now retains `ypy[ROOT]`; spelling and analysis are unchanged.
- Five focused engine tests and six existing corpus contrasts pass; all 122 historical surfaces remain identical. The strict source/JSONL audit still finds pre-existing missing location metadata at Araújo 74, and 81–82 remain unsaved. See [handoff](session-handoffs/2026-09-17-compound-annotations.md).
