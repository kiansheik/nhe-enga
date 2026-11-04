# Agent Log

## 2026-11-04 — Repaired normal-motion focus for shared VLB lines

Reproduced the reported live I-055 §1131 link in fresh Chrome. The route and
source ID were correct, but the selected transcript stayed offscreen under
normal motion because continuous-mode neighbor insertion interrupted its smooth
scroll. The prior full-browser suite globally reduced motion and therefore
masked the race.

Routed/programmatic selections now use deterministic instant centering while
ordinary line clicks remain smooth. Pending scan-image focus also completes
instantly after the image supplies its final geometry. Added an exact
normal-motion regression for the reported line in continuous and page modes,
plus the page-55 scan in CI's sparse checkout.

The exact link passes locally on desktop and mobile with both saved modes; the
complete Chrome reader suite has zero JavaScript errors and all 31 focused VLB
Node tests pass. No deployment ran. See the
[handoff](session-handoffs/2026-11-04-vlb-shared-line-focus.md).

## 2026-11-04 — Kept VLB search open and made continuous reading semantic

Added the short root **VLB** link and removed only the unfinished direct
**Gramática** navigation item; the grammar build and **Playground** remain.
Fresh readers now start in continuous mode unless a valid mode was already
saved, and explicit URL modes still win for that visit.

Search selections retain their query and results on desktop and mobile, mark
the open source, and remain available until the explicit close action. In
continuous mode the two panes now synchronize through paired transcript and
OCR-box boundaries instead of applying one page percentage to both layouts.
A selected line suspends joined scrolling while preserving the selection and
URL; tapping that same transcript or facsimile line clears it and relocks from
the tapped surface. Independent scan hydration follows the scan being viewed,
and correction drafts survive visual deselection.

The full Chrome regression passes every desktop/mobile/search/continuous/
correction/share flag with zero JavaScript errors. Static VLB navigation tests
and JavaScript syntax checks also pass. A fresh Pages artifact builds at
`/tmp/nhe-pages-vlb-followup.DRGw6a`, and its homepage plus VLB application
assets match source bytes. No deploy ran. See the
[handoff](session-handoffs/2026-11-04-vlb-continuous-search-navigation.md).

## 2026-11-03 — Refined the VLB study reader and replaced mixed search

Followed the deployed unified-reader work on `fix/vlb-study-reader-controls`.
The search path no longer loads or renders Navarro dictionary rows: it searches
Emerson source records only, preserves orthographic marks, ranks exact whole
forms before exact substrings inside larger words, and labels Portuguese versus
VLB-side matches. A byte-identical served copy of the frozen directional
orthography model supplies bounded Navarro-to-VLB retrieval candidates with
explicit probable/non-identity wording. The reported `biã` query now produces
the expected exact §4770 line first and only the three exact compounds after it.

Condensed phone navigation to one row with a collapsed search magnifier, made
both study panes minimizable, and added a drag/keyboard separator on mobile and
desktop. Two-touch gestures zoom the facsimile while preserving the gesture
centroid; selecting or restoring a line recenters both surfaces at the current
zoom. View zoom, split, minimized panes, OCR visibility, and mode survive reload
through guarded localStorage. Per-line OCR-reading disclosures and the duplicate
**Citar verbete** action are gone. The remaining **Compartilhar** action uses
Web Share and retains clipboard/manual-copy fallbacks for the exact line,
citation, and compact deep link. Navarro remains contextual and explicitly
opened; raw transcript/facsimile clicks remain navigation-only.

Added search/data/browser regressions, Pages/CI inclusion, and documentation.
All 60 VLB Python tests, five source-search tests, the correction gate, and the
full headless Chrome reader suite pass with zero JavaScript errors. The manifest
change required only a correction-evaluation provenance-hash refresh; all
metrics remain unchanged. The complete local Pages artifact at
`/tmp/nhe-pages-vlb-study-reader` built successfully, and the emitted VLB
JavaScript, CSS, manifest, and model are byte-identical to source. Synthetic
TouchEvents cover pinch behavior, but physical touch hardware was not tested.
No deploy ran. See the
[handoff](session-handoffs/2026-11-03-vlb-study-reader-controls.md).

## 2026-11-03 — Unified the VLB mobile reader around the facsimile

Followed merged PR #38 with a narrow mobile-layout correction on
`fix/vlb-mobile-unified-reader`. Search now stays above one viewport-filling
reader; the facsimile is the larger upper pane and a denser 15 px transcription
tray uses roughly the lower third. The tray minimizes to its tab bar and restores
without losing scroll, source selection, or OCR highlighting. Old `surface`
URLs remain safe but no longer hide a pane or defer scans. Correction editing
restores and temporarily enlarges the tray, and continuous mode synchronizes
both visible panes. Desktop remains side by side.

Separated source navigation from Navarro review. Transcript clicks only select
and center OCR evidence, while facsimile-line taps perform the reverse jump.
Navarro is empty before selection, contextual afterward, and its entry detail
requires a separate explicit headword action. Direct line navigation clears
stale ambiguous-entry filters and unrelated citation/detail identity before
URLs or notes update. A selected line also exposes citation-copy and native-share
actions with exact text, a minimal VLB locator, and a compact page-plus-line deep
link; unsupported Web Share falls back to the clipboard, with a manual-copy
prompt if clipboard access is denied.

The browser regression now asserts actual geometry, search placement, compact
type, minimization, bidirectional navigation, explicit Navarro behavior,
copy/share payloads and fallback, compact-link restoration, correction
reachability, and portrait/landscape/tablet behavior. Fresh Chrome QA passed
every result flag with zero JavaScript errors; the VLB Python, inventory, and
focused Node suites also passed. A complete local Pages artifact built
successfully, and no deployment was run. See the
[handoff](session-handoffs/2026-11-03-vlb-unified-mobile-reader.md).

## 2026-11-03 — Integrated VLB V3 review and correction workflow

Reconstructed the requested work after confirming that no unpublished
interrupted implementation could be recovered. Added a frozen V3 ranker and
24-case blind assistant evaluation, a complete 7,534-record reverse
concordance, and an append-only correction ledger with exact provenance,
revision history, idempotent validation, issue-form submission, and a
review-PR import workflow. Projected only compact page-scoped candidates and
reviewed decisions into the static reader; the full audit and reverse artifact
stay out of browser/offline downloads. The eight initial correction decisions
are assistant-reviewed rather than human-verified and are not training data.
The import workflow now rebuilds and commits the reader projection and dynamic
correction-regression report with each ledger append; untrusted issues cannot
self-approve regression or training use.

The live reader now marks exact source spans, preserves manual alternatives,
supports structured local correction export/import, and uses a one-surface
mobile text/scan design with deferred scans and preserved scroll state.
Chromium covered desktop, responsive viewports, continuous reading, exact
marks, alternative-route reloads, correction save/submission/export/import,
strict dry-run validation, and mobile correction geometry with no JavaScript
errors. Reload and page/continuous-mode regressions retain exact automatic and
manual targets. The frozen ranker reached 20/21 clear-case top-one paragraphs
and 19/21 offered exact spans; the release-time ambiguous false positive remains
disclosed, and its post-release safety gate is development evidence only.
Against the eight approved correction regressions, V3 retrieves the correct
top paragraph and exact span for all six accepted records and offers all seven
accepted spans; the production gate makes 2/2 exact automatic targets, zero
false positives, and abstains on both uncertain decisions.
Milestone commits `d1eea0c4` and `5ce484c3` were pushed to
`feat/vlb-review-learning`; nothing was merged or deployed. See the
[handoff](session-handoffs/2026-11-03-vlb-v3-corrections-mobile.md).

## 2026-11-03 — Froze independent VLB benchmark V3 annotations

Annotated the 24-case frozen review packet without reading mining outputs,
rankings, pipeline/model/index/freeze material, or prior predictions and
evaluations. Used only the packet's citation context and page fragments, the
pinned Emerson text for exact Unicode code-point spans, and the pinned
dictionary rows for sense context. Recorded 21 clear and three ambiguous
cases, with zero not-found cases; every label is explicitly assistant-reviewed
and not human-verified. Added a freeze manifest and a standalone validator that
rechecks both file hashes, packet blindness, exact case coverage, fragment
integrity, and all 27 source spans. Validation passes. See the
[handoff](session-handoffs/2026-11-03-vlb-benchmark-v3-blind-annotation.md).

## 2026-11-02 — Scoped inline VLB links for continuous reading

Branched from merged main `ef6a586c` for continuous reading. Removed the VLB
homepage item and made inline citations request continuous mode and automatic
source focus. Preserved original page-token positions separately from formatted
HTML, including true Unicode code-point accounting and inherited references.
The formatter intentionally repeats some examples/citations: uniquely sourced
copies keep their original occurrence, equal counts preserve source order, and
98 ambiguous displayed copies omit a position instead of choosing the first
same-page occurrence. All 6,164 raw links remain exact; 6,225 of 6,323 displayed
copies are precise. Added corpus and repeated-occurrence regressions and wired
the OCR target helper into Pages and CI. The focused 11 linker tests and two
inventory tests passed. See the
[handoff](session-handoffs/2026-11-02-vlb-continuous-reader.md).

## 2026-11-02 — Added VLB reader navigation and source integration

Prepared the main VLB navigation link, Pages allowlist, offline asset grouping,
and volume/page/entry query links from the dictionary. Kept every displayed
citation token, added list/range/inherited-volume support and the preserved VBL
spelling, and left malformed locators unresolved. Repaired the citation audit's
adapted inherited-reference case at dictionary row 7915 and added focused
regressions. The reproducible reader data now retains 6,124 occurrences and
6,164 valid page links. Existing scan URLs still work and no scans are duplicated.
Focused linker, formatter, apostrophe, audit, legacy-viewer, and shell checks
passed. Reader browser checks also passed for responsive layouts, OCR,
citation deep links, notes export/persistence, and split-page navigation.
The existing formatter workflow now gates the VLB data/browser tests using
the pinned shared Playwright browser and seven original scan fixtures.
See the [handoff](session-handoffs/2026-11-02-vlb-reader-integration.md).

## 2026-10-26 — Deployed merged Teatro and Castilho sources

Fast-forwarded local `main` to merged PR #34 (`e78abbc8`), rebuilt the full
optimized static site, and pushed Pages commit `d8b48140`. GitHub reported the
deployment built successfully. Live checks confirmed the new Teatro linker,
the 75-page manifest including page 36 to scan 757 and 2006 page 176 to scan
682, the Castilho route, and a readable HTTP 200 page-36 JPEG.

## 2026-10-26 — Linked every current Anchieta Teatro citation

Replaced the one-page Anchieta Teatro exception with separate Navarro 1999
and 2006 locator maps covering all 1,431 current citations in 882 records.
Aligned 107 edition-and-page keys to 75 representative pages in Martins's 1954
documentary scan using dictionary quotation context, Internet Archive OCR, and
sequence review; preserved the cited wording and kept unsupported pages/years
unlinked. The reported `îambé` page 36 now routes to scan index 757, while
the two editions' page 176 routes remain distinct. Added an OCR candidate
helper, edition-aware viewer navigation, sparse images, provenance, offline
pack naming, refreshed source inventories, and corpus-wide regressions. All
20 source/viewer tests, four formatter invariants, 53 Chromium tests, 11
offline tests, the service-worker smoke test, JPEG verification, diff checks,
and an 804 MiB no-PDF Pages build pass. Also repaired the Android CI setup by
overriding its obsolete default `tools` package with `platform-tools`.

## 2026-10-26 — Refresh source-groundwork PR

Merged current `main` into PR #26 and resolved its obsolete Figueira overlap
in favor of the deployed implementation, then refreshed it again after PR #33
merged the Figueira Wikisource snapshot. Preserved the unique Castilho 1937
source: 16 verified page-side crops, all 215 current citation links, explicit
mapping/navigation, reproducible crop rendering, Pages/offline inclusion, and
focused regressions. PR #26 later merged into `main`; it was not deployed by
that branch-refresh session.

## 2026-10-25 — Repaired dictionary entry boundaries corpus-wide

Reworked the dictionary definition formatter around explicit semantic and
citation boundaries instead of the earlier single-dash/colon assumptions.
This fixes the reported `ranhẽ²` bolding and the full audit set: generated
headings, bracketed notes, compact and omitted translation delimiters,
post-dialogue examples, adjacent pairs, shared citations or translations,
editorial tails, Unicode related headwords, and related-entry glosses that
must remain prose, including `-sûerĩ` and `-te nakó`. Annotated definition
preambles now retain their gloss boundaries, source variants keep their
visible `ou`, and a document-flow sticky footer avoids both long-entry overlap
and short-page drift. Added a reproducible Chromium sampler, corpus-wide Node
structural and source-token invariants, 53 browser regressions, and a
path-filtered CI workflow. A real-Chromium pass over all 8,293 records and a
31-entry visual sample found no remaining credible formatter defect. No
dictionary or morphology data changed.

## 2026-10-25 — Dictionary-entry formatting audit

Added a deterministic Playwright sampler for the actual served dictionary UI
and reviewed 24 records from the longest 10% plus the reported `ranhẽ²`
sentinel. Sixteen entries were coherent and nine exposed five recurring
boundary classes. The supplied bolding is caused by an `Advérbio:` heading
being reparsed as a definition/example colon; highlighting is a separate,
intentional query-match layer. An exhaustive formatter pass finds this exact
heading defect 274 times in 270 records, with a one-to-one empty-`quote-tupi`
signature. Captures were stable across repeated browser runs. Recorded current
versus expected boundaries and staged PR-sized repair/test recommendations;
production JavaScript and dictionary data were deliberately left unchanged.

## 2026-10-25 — Figueira and Anchieta source click-throughs

Restored the reviewed Figueira implementation from the unmerged prior work,
including the complete 200-page 1878 facsimile, provenance, full-scan viewer,
all 622 explicit served-dictionary links, inherited list/range handling, and
the visible `1686` citation-discrepancy warning. Added a deliberately narrower
Anchieta mapping: all nine unsuffixed `Anch., Teatro, 176` attestations were
visually collated to Martins 1954 printed p. 632/PDF index 683, while `2006`,
ranges, lists, other years, and all other Teatro pages remain unlinked. Wired
both sources through Pages optimization and selective offline packs. All 18
source/viewer tests, 11 offline tests, the service-worker smoke suite, lint,
syntax, diff checks, a 791 MiB no-PDF Pages build, and real-Chrome clicks from
the reported `ma'enduar` entry pass. Pushed source commit `31194fd4` to `main`
and Pages commit `2333ed15` to `gh-pages`; GitHub reported the build successful.
The live JavaScript exposes all three routes, the deployed JPEG hashes match
the artifact, and real Chrome loaded each expected image from the custom
domain.

## 2026-10-21 — Refresh stale live citation snapshots

Reproduced the reported `arcat1618` target as an offline-service-worker
versioning problem: the origin and a clean browser already returned the fixed
`arcat1686` anchor, while an older pinned catalog could continue serving the
old JavaScript during online navigation. Changed new-document activation to
revalidate the catalog with `no-store`, prefer the current catalog's verified
file, and retain installed/saved files as failure fallbacks. Existing documents
remain version-pinned. All offline unit/protocol checks and the real-Chromium
offline/update suite pass, including immediate online activation without an
explicit sync. Pushed source commit `fda36aaf` and deployed Pages commit
`8460bbbf`; GitHub Pages built it successfully. The production worker matches
the artifact byte for byte, and the exact reported query now links to the live
1686 page-241 viewer and its loaded `276.jpg` scan.

## 2026-10-21 — Araújo 1686 citations

Separated explicit 1686 Araújo citations from the legacy 1618 folio route.
Derived 58 cited printed pages from the served dictionary and rendered only
those pages plus a two-page context buffer (158 JPEGs). Confirmed printed page
241 at image/PDF index 276 contains the `emo'emyîara` quotation. Added sparse
viewer navigation, range-citation handling, provenance, reproducible selected
rendering, Pages/offline inclusion, and focused coverage. All 12 source-viewer
tests, lint, image decoding, the 741 MiB Pages build, and a real-Chromium local
click from the dictionary entry to the readable scan pass. Pushed source commit
`cb4b3b87` to `main` and Pages commit `99fb18f3` to `gh-pages`; GitHub reported
the Pages build successful, the live image bytes match the artifact, and a
real-Chromium production click reaches the readable page-241 scan.

## 2026-10-12 — Diffuse locative -bo

Implemented `bo` (Navarro -bo2) beside `pe` and routed hyphenated dictionary
`Postposition` values `-bo`/`-pe` through their bound classes. Rejected the
`YFix` wrapper approach: it skips `Postposition.__mul__` and raises. 92 engine
tests and 113 corpus tests pass; all 160 historic renders are byte-identical.
The consonant-final `y` branch is an inference awaiting editorial confirmation.

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
