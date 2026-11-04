# Current State

## 2026-11-04 — Shared VLB line links focus under normal motion

- The deployed `?page=I-055&line=1131` route correctly resolved and selected
  §1131, but normal smooth scrolling was interrupted when continuous mode
  prepended its neighboring page. The selected transcription could remain
  completely offscreen and the facsimile highlight could remain below center.
  The deployed and local `vlb/app.js` bytes matched; this was not stale data or
  an invalid line locator.
- URL-routed and other `loadPage`-driven selections now center instantly, so
  continuous page insertion and image geometry preservation retain the final
  position. Ordinary transcript/facsimile clicks still use the reader's smooth
  behavior. A pending image load also completes its requested focus instantly
  once the real dimensions are available.
- The browser regression now exercises the exact I-055 §1131 link with normal
  motion in continuous and page modes, after the previous page is inserted.
  It checks the exact text, selected/pressed state, explicit line actions, URL
  conversion, centered transcription, and centered OCR highlight. CI includes
  the page-55 scan fixture.
- Local Chrome verification passes at 1440×1080 and 390×844 in fresh continuous
  and saved page modes. The complete browser suite passes every result flag
  with `javascript_errors: []`; its result data and corrected-link screenshot
  are under `/tmp/vlb-shared-focus-final.TA4Srq`. All 31 focused VLB Node tests
  pass. A fresh 813 MiB Pages artifact at
  `/tmp/nhe-pages-shared-focus.OhvyoL` contains 2,787 files and byte-identical
  application/page data. Work is on `fix/vlb-shared-line-focus`; no deployment
  was run. See the
  [handoff](session-handoffs/2026-11-04-vlb-shared-line-focus.md).

## 2026-11-04 — VLB entry point and semantic continuous reading

- The root navigation now has the short label **VLB**. The unfinished direct
  **Gramática** item is hidden from that navigation, while the grammar build
  and the separate **Playground** link remain available.
- A reader without a saved reading-mode preference starts in **Rolagem
  contínua**. A valid saved `page` or `continuous` choice is still honored, and
  an explicit `mode=` URL remains authoritative without overwriting that saved
  choice.
- Search selections retain their query and results on desktop and mobile, mark
  the open source, and remain available until the explicit close action.
- With no line selected, continuous panes map visible transcript boundaries to
  OCR-box unions and interpolate between those landmarks, falling back to page
  fractions only without usable OCR. This replaces equal percentage scrolling
  between differently spaced scan and transcription pages.
- Selecting one line temporarily unlocks the facsimile and transcription so
  either can be explored independently without losing the selected line or its
  URL. Tapping that same transcript or facsimile line again clears the line
  focus and immediately relocks the panes from the surface the reader tapped.
  Correction drafts stay open across this visual deselection.
- The complete Chrome regression passes with persistent-search, fresh-default,
  selected-pane independence, same-line toggle, bidirectional OCR-boundary
  synchronization, responsive geometry, correction, and sharing checks all
  true and `javascript_errors: []`. Screenshots and `result.json` are under
  `/tmp/vlb-followup-qa.bTDUph`. A fresh 813 MiB Pages artifact at
  `/tmp/nhe-pages-vlb-followup.DRGw6a` contains 2,787 files; its homepage and
  VLB JavaScript/CSS are byte-identical to source. This is source-branch work;
  no deploy command was run. Repository-wide `make lint` still reports 24
  pre-existing Black formatting failures outside this diff. See the
  [handoff](session-handoffs/2026-11-04-vlb-continuous-search-navigation.md).

## 2026-11-03 — VLB study-reader controls and source-only search

- Started `fix/vlb-study-reader-controls` from merged `main` at `976ed343`
  after the unified reader was deployed. This follow-up remains source-branch
  work: it builds locally but does not deploy a Pages artifact.
- Search now reads only Emerson VLB source records. Literal VLB and Portuguese
  forms preserve diacritics and nasalization, with whole-word/phrase matches
  before the same spelling inside a larger word. A checked exact copy of the
  frozen Navarro-to-Emerson orthography model adds bounded, explicitly
  probable retrieval matches; its costs are not probabilities or evidence of
  lexical identity. `biã` now returns §4770 first, followed by its three exact
  inside-word occurrences, without Navarro dictionary result rows.
- Mobile navigation is one low-profile row: search stays behind a magnifier
  until requested, the facsimile remains the primary surface, and either the
  facsimile or transcription can minimize. A pointer- and keyboard-adjustable
  separator changes pane proportions on mobile and desktop. Pinch gestures
  zoom inside the facsimile, selected lines recenter at the active zoom, and
  zoom, split, pane, OCR, and reading-mode preferences persist in localStorage.
- Plain line selection remains bidirectional navigation only. Restoring a
  minimized pane recenters the active line, including in continuous mode.
  Navarro stays contextual and requires explicit actions. The per-line UI now
  exposes one **Compartilhar** action; Web Share falls back to copying the line,
  citation, and compact deep link, then to a manual-copy prompt if necessary.
  The obsolete per-line **Ver leitura OCR** disclosure is gone.
- The data projection, Pages allowlist, and CI now include `vlb/search.js`, the
  served orthography-model copy, and focused source-only search tests. The
  correction evaluation changed only its viewer-manifest checksum after that
  manifest gained the new model pointer; its counts, rates, and zero-false-
  positive gate are unchanged.
- Validation passes 60 VLB Python tests, five search tests, the correction
  evaluation gate, and the complete Chrome reader regression with every flag
  true and zero JavaScript errors. A full Pages build at
  `/tmp/nhe-pages-vlb-study-reader` succeeds; emitted VLB JavaScript, CSS,
  manifest, and orthography model match source bytes. Actual two-finger use on
  physical touch hardware remains unverified. See the
  [handoff](session-handoffs/2026-11-03-vlb-study-reader-controls.md).

## 2026-11-03 — Unified mobile VLB reader follow-up

- Started `fix/vlb-mobile-unified-reader` from merged `main` at `a65dbb8e`
  after the user reported deploying PR #38. This change does not publish a new
  Pages artifact.
- Replaced the narrow-screen single-surface switch with one bounded reader:
  the facsimile remains visible as the larger upper pane and a compact
  transcription tray occupies about the lower third. The tray can collapse to
  its 41 px tab bar and restore without losing either pane's scroll position,
  selected source, or OCR highlight.
- Search is always visible above the mobile reader. Reading mode and copy-link
  controls remain in a separate disclosure. Ordinary transcription lines use
  15 px type with denser spacing (14 px on short landscape screens); desktop
  remains the existing side-by-side layout.
- Legacy `surface=text|scan` links remain compatible as focus hints, but no
  longer hide a pane or defer the facsimile. Both continuous stacks synchronize
  while visible. Correction editing automatically restores and temporarily
  enlarges the lower tray while retaining a substantial facsimile area.
- Plain transcription clicks now only select the line, update the URL, and
  center its OCR boxes in the facsimile. Tapping an aligned facsimile line
  performs the reverse navigation and restores the mobile tray. Neither path
  opens Navarro detail; background resize no longer reuses the broad selection
  path.
- Navarro is contextual to the selected line. The tab is empty before a line
  selection, old ambiguous-entry filters are cleared by direct line navigation,
  and selecting an unrelated line clears stale citation/detail identity before
  updating URLs or notes. Opening a headword detail requires a separate explicit
  click. Page and dictionary routes may still select a high-precision target but
  do not open the detail panel automatically.
- Selected lines expose **Citar verbete** and **Compartilhar**. Copy produces
  the exact transcription, a minimal VLB volume/page/paragraph locator, and a
  compact `page=I-017&line=13` link. Native Web Share receives the same content;
  unsupported sharing falls back to the clipboard, and clipboard denial opens
  the complete block for manual copy. Compact links reopen with the line
  selected and both surfaces centered.
- Fresh Chrome QA passes every desktop/mobile/continuous/correction/share flag
  with zero JavaScript errors at 360×800, 390×844, 844×390, 768×1024, and
  desktop sizes. The VLB Python, citation-inventory, and focused Node suites
  also pass. A complete local Pages artifact builds successfully; no deploy
  target was invoked. See the
  [handoff](session-handoffs/2026-11-03-vlb-unified-mobile-reader.md).

## 2026-11-03 — VLB V3 alignment, durable corrections, and mobile review

- Continued `feat/vlb-review-learning` from frozen V2 commit `b5df369a`.
  No unpublished interrupted implementation was recoverable, so the requested
  work was reconstructed and preserved in reviewable milestones
  `d1eea0c4` and `5ce484c3` before the live-reader integration.
- Frozen V3 against a fresh 24-case blind assistant review: 20/21 clear cases
  rank the correct paragraph first, 21/21 within three, and 19/21 offer the
  exact source span. The release-time navigation policy also targeted one
  ambiguous case; the subsequent development-only prefix-hypothesis gate is
  explicitly not a new held-out result. Labels are not human-verified, and
  OCR-line availability is not exact glyph-box accuracy.
- Added an append-only, hash-pinned correction ledger and untrusted issue-import
  workflow. Its eight assistant-reviewed first revisions contain six accepted,
  one ambiguous, and one not-found decision; none is training-approved. The
  static reader saves locally, imports/exports the same schema, and opens a
  prefilled GitHub issue without frontend credentials.
- The correction loop now regenerates both reader data and a checked
  ledger-versus-V3 development report. All six accepted regressions retrieve
  the right first paragraph and exact span, all seven accepted spans are
  offered, and the production policy has 2/2 exact automatic targets with zero
  false positives while abstaining on the ambiguous and not-found records.
  Public issue payloads cannot self-grant regression or training approval.
- The reader now loads compact page-scoped V3 candidates, marks exact source
  spans, preserves manual alternatives in shared URLs, and exposes a bounded
  correction editor. Phones and portrait tablets use one switchable text/scan
  surface with independent scroll state, deferred scans, and a sticky mobile
  correction action bar; desktop remains side by side.
- A separate offline reverse concordance covers all 7,534 VLB records: 3,771
  have a separated candidate, 2,949 remain ambiguous, and 814 are unmatched.
  It claims zero fully covered records and is excluded from browser/offline
  payloads. Fresh Chromium QA passed all functional checks with no JavaScript
  errors, including automatic/manual target persistence across reload and mode
  changes; this branch has not been merged or deployed. See the
  [handoff](session-handoffs/2026-11-03-vlb-v3-corrections-mobile.md).

## 2026-11-03 — Frozen VLB benchmark V3 blind assistant annotation

- Independently reviewed all 24 cases in
  `vlb/mining/benchmark-v3/review_material.json` using only its citation
  context/page fragments, the checksum-pinned Emerson transcription for exact
  global offsets, and the matching pinned dictionary row when sense context
  was needed.
- Froze 21 `clear`, three `ambiguous`, and zero `not_found` labels. The three
  ambiguous decisions preserve a form/sense conflict or an unsupported part
  of the dictionary claim; none is presented as human-verified.
- `annotation-freeze.json` pins packet hash `a64adf52...1d31` and labels hash
  `ab73a469...2685`, records `reviewer_type: assistant`,
  `human_verified: false`, and states that rankings and mining outputs were
  not inspected.
- The standalone validator checks blindness flags, pinned input hashes, exact
  case coverage, reviewer metadata, source-fragment integrity, and every
  global half-open target span. It passes with 24 labels and 27 targets. See
  the [handoff](session-handoffs/2026-11-03-vlb-benchmark-v3-blind-annotation.md).

## 2026-11-02 — VLB continuous reader and inline entry points

- Started `feat/vlb-continuous-reader` from current `main`
  `ef6a586c5d13733537480048924de1776662c70c`, after PR #35 merged.
- Removed the standalone VLB homepage navigation item. Dictionary inline
  references open the reader with `mode=continuous&focus=auto`, preserving
  printed volume/page and the originating dictionary row.
- `citation_pos` identifies the clicked page token in the original dictionary
  definition, in Unicode code points. It resolves the exact citation span
  independently of formatter-inserted HTML or inherited-reference whitespace.
- Every one of the 6,164 raw page links has an exact occurrence position.
  Existing formatting produces 6,323 displayed copies; 6,225 retain an exact
  position, while 98 ambiguous copies deliberately require a citation choice.
  No source association is approved by this routing step.
- The Pages allowlist and CI include `vlb/citation-targets.js` and its focused
  tests. See the [routing handoff](session-handoffs/2026-11-02-vlb-continuous-reader.md).

## 2026-11-02 — VLB transcription reader branch

- Prepared `/nhe-enga/vlb/` for the main navigation, with Navarro VLB citations
  preserving printed volume/page and their originating served-dictionary row.
- The pinned Emerson transcription is aligned to 279 lexical printed pages;
  the unnumbered manuscript plate and blank verso at scan positions 25 and 26
  are retained as nontext scan material.
  Page-boundary uncertainty remains explicit. Source-entry suggestions remain
  distinct from reviewed associations.
- All 6,124 VLB citation occurrences are retained, including the inherited
  `II, 109, adapt.` citation in `nhe'ẽporangaíba` that the previous audit missed.
  The data provides 6,164 valid page links; `VLB, I, 1390` and page-less `VLB, I`
  remain unresolved. Existing citation wording and dictionary bytes are kept.
- Pages includes the VLB frontend/data and linked provenance; existing PNG scans are reused through the image-format
  manifest after JPEG/WebP conversion. Reader/data assets are in the core
  offline pack; scans remain in `source-vlb`.
- Real-browser checks passed for desktop/mobile layouts, OCR highlighting,
  citation deep links, notes export/persistence, and split-page navigation.
  The dictionary-formatting CI also runs the VLB data and browser regressions.
- This is source-branch work; production deployment is a separate step. See
  the [integration handoff](session-handoffs/2026-11-02-vlb-reader-integration.md).

## 2026-10-26 — Teatro/Castilho Pages deployment

- Merged source revision `e78abbc8` was built from clean `main` and deployed as
  `gh-pages` commit `d8b48140`.
- GitHub Pages reported the exact commit `built` in 95.69 seconds. The live
  custom domain serves the expanded Teatro linker, its 75-page manifest, the
  page-36 to scan-757 mapping, the distinct 2006 page-176 to scan-682 mapping,
  and the new Castilho source route.
- The optimized artifact contains 2,300 primary-source images and 13 signed
  offline packs. The raw source PDFs remain excluded. See the
  [deployment handoff](session-handoffs/2026-10-26-teatro-pages-deployment.md).

## 2026-10-26 — All current Anchieta Teatro citations linked

- All 1,431 current `Anch., Teatro` citations in 882 served dictionary records
  now link without changing their displayed text. The linker covers 72
  unsuffixed Navarro 1999 locators and 35 explicit Navarro 2006 locators,
  including ranges and the three observed `Anch. Teatro` punctuation variants.
- The cited Navarro page stays in the URL. An edition-aware explicit map opens
  the corresponding quotation or headword passage in Martins's public 1954
  documentary edition. The map stores 75 sparse documentary scan pages for
  107 edition-and-locator keys; it is not a numeric page offset or a claim that
  the editions have interchangeable pagination.
- The reported `îambé` citation, Navarro 1999 p. 36, now links to PDF index
  757. Navarro 1999 p. 176 remains at index 683, while Navarro 2006 p. 176 is
  separately routed to index 682.
- The viewer selects targets by both cited page and edition, carries the 2006
  discriminator through navigation, and identifies the Martins witness and
  edition boundary. Unsupported pages and years remain unlinked.
- `scripts/data/align_anchieta_teatro.py` records the reproducible OCR-ranking
  step used during alignment. The checked-in source inventory was regenerated
  and now reports all 1,431 Teatro citations as linked.
- Validation passes: 20 source/viewer tests, four corpus formatting/link-token
  tests, 53 real-Chromium formatting tests, 11 offline-catalog tests, the
  service-worker smoke test, 75 JPEG decode checks, and an 804 MiB Pages build
  containing all 75 optimized images and no raw Teatro PDF. The Android CI
  setup now requests `platform-tools` explicitly instead of the retired SDK
  package `tools`. See the
  [handoff](session-handoffs/2026-10-26-anchieta-teatro-all-citations.md).

## 2026-10-26 — PR #26 refreshed against main

- The older Figueira/Castilho source branch now incorporates current `main`.
  Its duplicate Figueira implementation was resolved in favor of the deployed
  October 25 implementation and the Figueira Wikisource snapshot subsequently
  merged through PR #33; the still-unique Castilho source remains in the PR
  with 16 verified page-side crops covering 215 citations in 162 records.
- Castilho is integrated with the current manifest viewer, Pages image
  optimizer, offline source packs, and renderer. The renderer retains current
  selected-page behavior while adding manifest-defined page-side crops.
- This is still review work in PR #26. It has not been merged into `main` or
  deployed. PR #26 subsequently merged into `main`; its Castilho source is now
  part of the baseline retained by later source-link branches.

## 2026-10-25 — Dictionary-entry boundary repair

- The production formatter now keeps generated part-of-speech headings,
  definitions, editorial notes, related-entry glosses, dialogues, examples,
  translations, and source citations in separate semantic containers. It also
  recovers conservative source variations such as compact translation dashes,
  omitted delimiters, shared citations/translations, malformed category
  brackets, annotated grammatical preambles, adjacent citation-delimited
  pairs, and related suffix headwords whose morphological hyphen must be
  preserved. Source-variant cards retain their visible `ou` separator.
- `ranhẽ²` now renders `Advérbio:` and its gloss as siblings of the first
  bilingual example. The same repair covers all 274 occurrences of the
  original generated-heading signature, rather than special-casing that entry.
- The formatter was checked against all 8,293 served Tupi–Portuguese records in
  real Chromium: no structural defects, dialogue mismatches, separator-prefixed
  definitions, editorial-note source lines, or source citations stranded in
  Tupi remain. The only one-sided cards are two intentional Portuguese prose
  quotations. A corpus-wide source-token multiset check also confirms that the
  formatter no longer silently drops visible dictionary prose.
- Regression coverage consists of corpus-wide Node structural, citation, and
  source-token invariants plus 53 real-browser semantic/layout tests. A
  dedicated pull-request workflow installs the pinned Playwright version and
  runs both suites.
- A final deterministic 31-entry sample (long entries plus boundary sentinels)
  produced no automatic warnings; every screenshot was reviewed
  qualitatively. The footer now stays at the viewport bottom on short pages
  and remains below expanded long entries. Dictionary data and morphology code
  were not changed. See the
  [audit](dictionary-formatting-audit-2026-10-25.md) and
  [implementation handoff](session-handoffs/2026-10-25-dictionary-formatting-fix.md).

## 2026-10-25 — Dictionary-entry formatting audit (pre-fix)

- `scripts/qa/sample_dictionary_entries.py` now captures a deterministic,
  long-entry-biased sample of actual browser-rendered `.entry` elements. It
  uses the served gzip and production UI, emits JSON plus a standalone gallery,
  and records structural warnings without treating them as correctness
  verdicts.
- A fixed sample of 24 records from the longest 10%, plus `ranhẽ²`, was
  reviewed against the raw definitions: 16 looked coherent and nine have
  visible boundary defects. Only two of those nine are invalid-DOM signatures;
  the rest require semantic comparison of neighboring examples, notes, and
  citations.
- The reported bolding is a systemic generated-heading bug, not a search
  highlight bug. A full formatter pass finds 274 malformed Adjetivo/Advérbio
  heading-to-quote occurrences across 270 of 8,293 Tupi–Portuguese records;
  all 274 emit an empty `.quote-tupi`, and none occur outside that signature.
- Other sampled classes include square-bracket semicolons, compact translation
  dashes, post-dialogue examples, notes swallowed into translations, and
  adjacent citation-delimited pairs. See the
  [audit](dictionary-formatting-audit-2026-10-25.md) and
  [handoff](session-handoffs/2026-10-25-dictionary-formatting-audit.md).
- This initial phase changed only audit tooling and documentation. The
  production repair described above followed after review of the findings;
  the dictionary data and generated assets remain unchanged.

## 2026-10-25 — Figueira Arte and Anchieta Teatro source links

- All 622 explicit `Fig., Arte` citations in 455 served dictionary records now
  link to the complete 200-scan Platzmann 1878 facsimile of Figueira's 1687
  edition. Printed pages 1–167 map to zero-based image indices 24–190; the
  requested pages 95 and 40 open `118.jpg` and `63.jpg` respectively.
- The nine unsuffixed `Anch., Teatro, 176` records now link to one explicitly
  collated documentary witness: Navarro 1999 p. 176 corresponds to Martins
  1954 *Poesias* p. 632, PDF index 683. The viewer labels this cross-edition
  boundary. The two `176, 2006` records, every other Teatro locator, and any
  range/list/year suffix remain unlinked because no general page offset is
  valid.
- Source provenance, checksums, page mappings, and reproduction commands live
  beside the images in `figueira1878/` and `anchteatro1954/`. The raw PDFs stay
  outside the Pages artifact.
- Validation passes: 18 focused source/viewer tests, 11 offline catalog tests,
  the service-worker smoke suite, lint/syntax/diff checks, and a full 791 MiB
  local Pages build with no PDFs. The build publishes both manifests in core
  plus separate 200-image Figueira and one-image Anchieta offline packs. Real
  Chrome clicks from `ma'enduar` opened all three requested viewers and loaded
  the expected images.
- Source commit `31194fd4` is on `origin/main`. Pages commit `2333ed15` built
  successfully and is live on the custom domain. The deployed JavaScript has
  all three routes; the three deployed JPEGs match the artifact byte for byte,
  and real Chrome loaded them at 1400 pixels wide. See the
  [handoff](session-handoffs/2026-10-25-figueira-anchieta-source-links.md).

## 2026-10-21 — Live citation cache refresh

- The deployed citation formatter was correct, but browsers with an older
  service-worker snapshot could keep serving the former `arcat1618` link on
  ordinary online visits.
- New document navigations now bypass the HTTP cache when revalidating the
  signed offline catalog and prefer files from that pinned current catalog.
  If the network or a new asset fails verification, the worker falls back to
  the installed or previously saved verified copy.
- Existing documents remain pinned to one catalog; this does not mix releases
  mid-page or weaken corrupt-update rejection.
- All 10 offline unit tests, the Node service-worker protocol smoke test, and
  the real-Chromium offline/update suite pass, including a new stale-catalog
  navigation regression.
- Source commit `fda36aaf` is on `origin/main`; Pages commit `8460bbbf` built
  successfully. The live worker matches the artifact byte for byte, and the
  exact reported query now exposes an `arcat1686` page-241 link whose viewer
  loads image `276.jpg` at 786 by 1261 pixels.

## 2026-10-21 — Araújo 1686 citation pages

- Explicit `Ar., Cat., {page}, 1686` citations now target a separate
  `arcat1686` viewer instead of being misrouted through the 1618 folio map.
- The served dictionary contains 90 explicit citations to 58 distinct printed
  pages. The source directory contains those pages plus a two-page context
  buffer: 158 JPEGs across 16 ranges, not the complete 420-page scan.
- Printed page `p` maps to zero-based PDF/image index `p + 35`; page 241 is
  image `276.jpg`, visually checked against the `emo'emyîara` quotation.
- The production artifact builds successfully at about 741 MiB, contains the
  158 optimized 1686 images as a separate offline pack, and contains no PDFs.
  Focused tests, lint, image decoding, and real-Chromium local navigation pass.
- Source commit `cb4b3b87` is on `origin/main`; Pages commit `99fb18f3` built
  successfully and was verified live on the custom domain, including the
  dictionary-generated page-241 link and the exact deployed JPEG bytes. See
  the [handoff](session-handoffs/2026-10-21-araujo-1686-citations.md).

## 2026-10-12 — Diffuse locative -bo and hyphenated postpositions

- `bo` (`Diffusive`, `tupi.Noun.bo`) implements Navarro's -bo2 diffuse
  locative; `Postposition("-bo")` and `Postposition("-pe")` from dictionary
  headwords now realize through `Diffusive`/`Locative` instead of `oka -bo`.
- 92 engine tests pass; all 160 historic plain/annotated renders unchanged.
  Consonant-final `okybo` is inferred, not attested. Under review on branch
  `feat/bound-postposition-bo`. See the
  [handoff](session-handoffs/2026-10-12-bound-postposition-bo.md).

## 2026-10-06 — D’Evreux 1929 primary-source pilot

- The implementation branch `devreux-primary-source` adds the complete
  444-page 1929 *Viagem ao Norte do Brasil* scan under
  `docs/primary_sources/evreux1929/`, with checksum-validated provenance and a
  reproducible whole-page renderer. The PDF itself remains outside Git. The
  implementation is awaiting review in
  [PR #25](https://github.com/kiansheik/nhe-enga/pull/25).
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
- Latest measured optimized local Pages artifact, including D’Evreux, sparse
  Araújo 1686, complete Figueira, and 75 sparse Anchieta Teatro witnesses, is
  about 804 MiB. The prior D’Evreux-only measurement was about 691 MiB.
- The checked-in generated `source_inventory.*` snapshot is current through
  the Figueira and all-locator Anchieta Teatro source-link additions.
- The failed 4.1 GB deployment history is preserved locally as `gh-pages-oversized-backup-20260912`; it is not reachable from the published `gh-pages` branch and must not be pushed.
- Root-level PDFs, DOCX output, and Graphviz renderings removed in the 2026-09-12 cleanup were generated and unreferenced. They remain recoverable from Git history and are now covered by ignore rules where needed.
- `make gen_data` is noisy and can take over a minute; it updates generated dictionary/conjugation data. Keep those outputs separate from source-only cleanup changes unless intentionally refreshing data.
- `make deploy-gh-pages` pushes to the configured remote branch; do not run it unless publishing the current Pages artifact is intended.

## 2026-09-17 — Compound modifier annotations

- Pydicate composition preserves a simple lexical noun modifier's existing `[ROOT]` metadata in both `Predicate.compose` and `Deverbal._apply_compositions`. Araújo 81 now retains `ypy[ROOT]`; spelling and analysis are unchanged.
- Five focused engine tests and six existing corpus contrasts pass; all 122 historical surfaces remain identical. The strict source/JSONL audit still finds pre-existing missing location metadata at Araújo 74, and 81–82 remain unsaved. See [handoff](session-handoffs/2026-09-17-compound-annotations.md).
