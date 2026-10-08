# Agent Log

## 2026-10-06 — Figueira and Castilho primary-source implementation

Implemented the first two books from PR #26's verified research plan in
[PR #27](https://github.com/kiansheik/nhe-enga/pull/27), a dependent review
branch. Added the complete 200-image Figueira scan and 16
Castilho page-side crops, production manifests, reproducible target-width/crop
rendering, citation links, manifest-driven viewer behavior, Pages inclusion,
inventory coverage and regression tests. All 622 Figueira citations and 215
Castilho citations link without changing displayed text. The lone
`Fig., Arte, 1686, 64` label stays verbatim and now opens the exact *çoába*
passage with a visible 1687-edition warning. Independent rerendering matched
all 216 JPEGs byte for byte; 12 Node tests, six Pages-size tests, lint, syntax
checks and the full 777,563,987-byte Pages build pass. Real Chromium desktop
and 400px checks covered both books, mapping labels, sparse navigation and
readability. PDFs remain outside Git; nothing was deployed or merged. Sousa
and D’Abbeville remain explicitly deferred for mapping/content/storage review.

## 2026-10-06 — D’Evreux 1929 primary-source pilot

Implemented the reviewed D’Evreux pilot without changing dictionary data,
morphology, corpus ground truth, deployment, or any other cited book. Added the
verified 444-page 1929 scan and provenance, a reproducible renderer and citation
inventory, production citation links, viewer metadata/navigation/zoom/error
handling, Pages asset inclusion, and focused production-code tests. The exact
PDF checksum/page count passed and an independent full rerender matched every
checked-in JPEG byte for byte. All eight Node tests pass; the inventory is
stable at 120 explicit citations, 113 records, 121 anchors and 42 printed
pages; a full 691 MiB Pages build passes; all source and optimized D’Evreux
JPEGs decode. Real Chromium desktop and narrow-window checks covered page 293,
PDF page 294, navigation/reload, range endpoints, the spaced author variant,
the unresolved `op. cit.` case, legacy links, fit and native-size zoom. Work is
on the implementation branch for review and has not been deployed or merged.

## 2026-09-25 — Historic surface consistency

Repaired three rendering paths exposed by the qualification appendix. Finite
annotated verbs now receive tag-preserving phonetic normalization; composite
direct arguments retain the tags needed to protect nested proper nouns; and the
past-classifier special case keeps the space between possessive `i` and
reflexive `îe-`. Three focused historic regressions and all 65 engine tests
pass, all 145 annotation audits pass, and ordinary/annotated surfaces agree for
145/145 current expressions.
The only saved-target changes are Araújo and Bettendorff 0028
`JesusChrixtoabé` to `JesusChristoabé`; their JSONL rows were not edited here.
The 112-test corpus suite consequently has those two expected failures, and
strict ground-truth verification still also reports the pre-existing Araújo
record-2 metadata drift. Work remains local.

## 2026-09-25 — Plain noun composition keeps both component roots

`Predicate.compose` now sends its simple left noun through the same guarded
lexical-base preservation already used for the right modifier. In Araújo and
Bettendorff record 22, `esá / poraûsubara` therefore yields
`esa[ROOT]poraûsubar[ROOT]` instead of one flattened root, without changing
`nde resaporaûsubara`. An explicit-`noroot` contrast prevents inferred tags.
Seven focused tests, all 62 engine tests and all 112 corpus tests pass; 145/145
ordinary outputs match ground truth and 145/145 annotation audits pass. Fifteen
records gain only the stored component boundaries. Work remains local.

## 2026-09-24 — Annotation accountability applied locally

Final coordinating verification built400/98/79-page PDFs and froze doctoral
SHA256 `109e465ed9985cc2f5fe654fe72dd87280fa7285202107a7ffd0494a097c3b08`.
Two bounded unscored round22 rechecks found no blocking repair defect. They confirm
Araújo73's occurrence segmentation; an unrelated Araújo79 crop was excluded from
the LaTeX export after source-page/pixel verification, without changing this
engine, the corpus or Studio data. Structural witnesses remain evidence candidates,
not linguistic adjudication. Nothing was committed or published.

- Repaired Araújo 73's flattened `asé saûsub[ROOT]`, cross-occurrence tag contamination and conjunction labels on nominal suffixes. Applied the reviewed 12-file engine/test/documentation patch with hash guards; the author's dirty `deverbal.py` and all corpus source/target records remain unchanged.
- Added a complete stored-Predicate graph and evaluation-event ledger alongside the existing numeric hierarchy. The LaTeX generator now enforces occurrence/tree integrity during live generation and offline schema-3 snapshot checks; no unique linguistic origin is claimed for 654 root-only or 1,962 ambiguous tag witnesses.
- Passed 60 engine and 179 LaTeX pipeline tests; preserved all 144 ordinary outputs. The 102-test original/repaired corpus runs have the same Araújo 55 failure, and strict verification has the same pre-existing record-2 metadata difference. Local PDFs build at 398/98/79 pages; independent doctoral PDF review is pending.
- Kept all 25 exact/six normalized ordinary-versus-annotated differences visible. No source interpretation was rewritten to make the gate pass, and nothing was committed or published. Evidence and next steps: [handoff](session-handoffs/2026-09-24-annotation-accountability.md).

## 2026-09-16

- Added `docs/agent/grammar-navigation.md`: a living map from grammatical phenomenon to where it's implemented in `pydicate`/`tupi`, meant to be read before searching for an engine bug and updated after every fix. Seeded from the existing `/`-composition fix in `AGENT_NOTES.md`, plus an "Open items" entry for a reflexive/absolute-`t-`-prefix bug reproduced against `oldtupicorpus` record `araujo_catecismo_1686:0074` (not yet localized).
- Registered it in `docs/agent/index.md` and added "check it before / update it after an engine edit" rules to `AGENTS.md`, plus an explicit rule against fixing a corpus-line mismatch by fabricating a new inline lexicon entry in the `oldtupicorpus` expression just to force a render match — driven by the `vscodetupy` "Correct ground truth" workflow, which now treats this repo as the required fix location for linguist-reported grammar corrections rather than an expression-level workaround.

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
- A subsequent `make deploy-gh-pages` committed the 477 MB artifact on top of the failed 4.1 GB root, so GitHub rejected the 3,287-object pack at its 2 GiB limit.
- Preserved the failed local history as `gh-pages-oversized-backup-20260912` and recreated `gh-pages` as parentless commit `ff3b1f5b` with the same optimized 474 MiB tree.
- Pushed the resulting 1,582-object, 449 MiB pack successfully and set `gh-pages` to track `origin/gh-pages`.
- Changed the GitHub Pages source from `main:/` to `gh-pages:/`, explicitly queued the build, and verified GitHub built `ff3b1f5b` without error.
- Verified the live root, grammar route, and generated image manifest; the manifest reports 1,407 optimized images and 449,476,728 bytes after optimization.
- After pull request 18 was merged, moved six maintained data pipelines into `scripts/data/`, two optional media helpers into `scripts/media/`, and ten historical scratchpads into `misc/experiments/`.
- Removed four generated PDFs, one generated DOCX, and four Graphviz source/render pairs from the source tree, reducing the checked-out root by about 124 MB; the artifacts were unreferenced and remain recoverable from Git history.
- Updated the Makefile, README, and script references for the new paths; added concise ownership READMEs under `scripts/data/`, `scripts/media/`, and `misc/`.
- Preserved `ical.png` as a public asset, added it to the Pages allowlist, and fixed the `katu/` and `mbya/` relative references.
- Verified Black, shell/JavaScript/Python syntax, `git diff --check`, the moved Navarro generator, and a full 477 MB Pages build.

## 2026-09-14

- Confirmed the optimized Pages allowlist had regressed the tracked `/docs/primary_sources/emerson_arte_anchieta.html` route to HTTP 404.
- Audited every tracked HTML file against `.pages-build` and found three missing legacy paths: the Anchieta transcription, `tupi/editirreg.html`, and the old source-path alias for the Pyodide iframe.
- Updated the Pages builder to preserve those explicit routes and all top-level primary-source HTML sidecars without reopening raw primary-source formats.
- Rebuilt the full 478 MB artifact, confirmed all tracked HTML paths are present, found no raw primary-source formats or files over 100 MB, and reran check-only lint successfully.
- Published only the three missing files to `gh-pages` as commit `8fbaf447`, leaving the unrelated source cleanup undeployed.
- Confirmed GitHub Pages built that exact commit and all three restored URLs return HTTP 200; the Anchieta page serves the expected title and 203,056-byte document.

## 2026-09-17 — Compound modifier annotations

Restored existing lexical root metadata lost by `noroot=True` when a compound modifier was rebuilt from its bare verbete. The guard reads stored lexical state without evaluating inflection and leaves ambiguous/already annotated/composite forms alone. Added a standalone five-test regression. Verified six existing contrasts, all 122 historic surfaces, and unchanged corpus/reference hashes. No source analysis, ground truth, commit or push was changed.
