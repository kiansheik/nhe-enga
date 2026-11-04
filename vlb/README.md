# VLB comparison reader

The public route is `/nhe-enga/vlb/`. It compares the existing facsimile images
with Emerson José Silveira da Costa's unchanged transcription and the VLB
citation occurrences in Nhe'enga's pinned Navarro dictionary snapshot.

Inline VLB citations in the dictionary open continuous mode with printed
locators and the original citation occurrence, for example:

```text
/nhe-enga/vlb/?volume=I&page=17&mode=continuous&focus=auto&entry=7210&citation_pos=86
/nhe-enga/vlb/?volume=II&page=78&source=vlb-emerson-r568-p05859
```

`entry` is a dictionary array row in the recorded snapshot. `citation` can
identify an exact citation occurrence. `citation_pos` is the clicked page
token's Unicode code-point offset in the untouched dictionary definition;
the reader resolves it within the saved citation interval. `source` selects
a transcription paragraph. Compact citation links use `page=II-078&line=5859`
to select the same paragraph without exposing its internal source ID.

`mode=continuous` enables the two synchronized page stacks; `mode=page` retains
the original single-page view. `focus=auto` asks for an evidence-supported OCR
target. Selecting a proposed target does not accept the lexical association.
Routes may select and align a supported target, but they do not open the
Navarro entry detail. Repeated references that cannot be distinguished safely
prepare citation choices behind the explicit Navarro tab.
Older narrow-screen links with `surface=text` or `surface=scan` remain valid as
focus hints, but both surfaces are now visible in one mobile reader. A manual
candidate alternative also records `target_start` and `target_end`, so reloading
a shared link cannot silently replace it with the automatic top span. There is
no standalone VLB link in the homepage navigation.

## Reading and reviewing

- Choose **Rolagem contínua** to scroll through adjacent pages in either pane.
  The other pane follows the same page and approximate relative reading position.
  Pages load as needed; prepending preserves the visible page, and distant scan
  images are released. The URL tracks the current page without filling browser
  history with scroll events. Switch back to **Página a página** at any point.
- Phones and portrait tablets keep one unified reader with the facsimile as the
  primary upper surface and the compact transcription tray at roughly the lower
  third. Search collapses to a small magnifier until requested, and the compact
  page controls leave the reading surfaces most of the viewport. Either pane can
  be minimized without losing its scroll position or selection. Drag the divider
  to change their proportions; the same separator is keyboard adjustable.
  Pinching inside the facsimile changes its zoom, and selecting a line recenters
  the current zoom on its OCR boxes. Zoom, pane proportions, minimized panes,
  OCR visibility, and reading mode are restored from localStorage. Landscape
  retains the same relationship with less secondary chrome, and legacy
  `surface` links no longer defer the scan.
- Select a transcription paragraph to highlight its approximate OCR lines on
  the scan and center the union of those OCR boxes. Tapping an aligned line in
  the facsimile performs the reverse navigation, restoring the mobile tray when
  needed and centering its transcription paragraph. Neither direction opens a
  Navarro entry. Exact supported expressions are marked in the source text and
  use narrowed OCR lines where available; an accepted text span without a safe
  OCR target remains navigable without fabricating a whole-paragraph scan box.
- A selected line exposes a single **Compartilhar** action. It sends the exact
  transcription text, a compact VLB volume/page/paragraph citation, and a direct
  selection link to the platform share sheet for apps such as WhatsApp or email.
  When native sharing is unavailable it copies the same block; if clipboard
  access is denied, the complete block opens for manual copy. Opening that link
  restores the line selection and centers both reading surfaces without opening
  Navarro.
- Navarro is contextual rather than page-wide: before a transcription line is
  selected, its tab contains no headword list. Select a line, then use **Ver no
  Navarro** (or open the Navarro tab) to see only that line's associated
  citations. Opening the larger entry detail requires a separate click on a
  headword. Candidate details disclose exact alternatives, evidence, review
  reasons, and ranking scores as non-probabilities. Six accepted correction
  decisions project seven exact spans; ambiguous and not-found decisions retain
  their uncertainty.
- Dictionary links automatically select a line only under the high-precision
  V3 policy: a frozen `suggested` candidate needs an exact source span, narrowed
  OCR lines, independent quotation or sense context, a stable page boundary,
  and a non-common form. Inferred prefix hypotheses remain manual after the
  fresh blind review exposed an ambiguous false positive.
- **Corrigir correspondência** preserves existing spans or accepts a new exact
  source selection. Saving is explicitly browser-local. Submission opens a
  prefilled GitHub issue without frontend credentials; export/import remains a
  fallback, and a manually dispatched workflow validates the untrusted payload
  before opening a review PR. The append-only ledger keeps revision history and
  multiple accepted spans.
- Approved ledger revisions are also scored against the latest proposals and
  production navigation policy by `node vlb/evaluate_corrections.cjs`. The
  checked development report removes ledger overrides before scoring and fails
  its high-precision gate on any false-positive automatic target.
- Search returns VLB transcription records only, never Navarro dictionary rows.
  It preserves diacritics and nasalization, ranks an exact whole word or phrase
  before the same exact spelling inside a longer word, and labels direct VLB and
  Portuguese-side matches. A bounded frozen directional model can map a Navarro
  spelling to likely VLB spellings; these are visibly labeled as probable
  orthographic retrieval matches. Model costs are not probabilities or evidence
  that two forms are the same lexeme. For split paragraphs, a match within a
  continuation opens the page containing the words.
- Record observations in the Anotações tab. Notes stay in browser localStorage;
  export JSON to preserve or share them. Notes are distinct from structured
  corrections. Neither path modifies Emerson's transcription or Navarro's
  dictionary snapshot.

The 279 text pages yield 7,688 exact fragments, including 11 split paragraphs.
The inventory contains 6,124 citation occurrences, 6,164 valid page memberships,
and two unresolved references. Images 25 and 26 are an unnumbered manuscript
plate and its blank verso; both are available in navigation.

## Credits

Emerson's [original transcription project](https://sites.google.com/site/vocabularionalinguabrasilica/)
and his [Como aprender tupi resource page on Abanhe'enga](https://abanheenga.blogspot.com/p/como-aprender-tupi.html)
are linked prominently in the reader. The latter is a resource page, not an
asserted release announcement.

The facsimiles are the 1952–1953 second edition revised by Carlos Drumond,
digitized by Renato Nicolai and hosted by the
[Biblioteca Digital Curt Nimuendajú](https://www.etnolinguistica.org/biblio:drumond-1952-1953-vlb).

## Data and deployment

`python vlb/build_data.py` deterministically rebuilds the compressed page files,
source/citation indexes, and `data/orthography-model.json` from `source/`, the
frozen V3 candidates, the frozen Navarro→VLB model, and the validated correction
ledger, without network access or the full PDF. The served model is an exact
projection of its pinned mining artifact. The 6,164 proposal records become
compact page-scoped associations; the 8+ MiB audit output is not downloaded by
the reader, and every compressed page remains under 20 KiB.
See [the source documentation](source/README.md) for provenance, coordinate
conventions and the separate pagination, OCR and lexical evidence layers.
The reader loads only the current page. `search.js`, the source index, and the
orthography model provide source-only search; the data files load on first
search.

The Pages allowlist publishes the HTML, CSS, JavaScript, `data/`, and referenced
PDF metadata. Original image assets remain under `docs/primary_sources/vlb/`;
the reader honors the build's `image-formats.json` and defaults to PNG in a
source checkout. Viewer assets belong to the offline core pack, and scans
remain in the existing `source-vlb` pack.

The separate reverse concordance covers all 7,534 lexicographic source records
and stays outside browser/offline payloads. Rebuild it with
`python3 vlb/build_reverse_concordance.py`; recomputed counts and limitations
are in `mining/reverse-output/REPORT.md`.

Changes to `docs/dict-conjugated.json.gz` must update this pinned concordance
before its row deep links can be trusted; the data regression checks the hash.

## Verification

```sh
node --test tests/vlb_dictionary_links.test.cjs tests/dictionary_formatting.test.cjs
node --test tests/vlb_search.test.cjs
python tests/test_vlb_citation_inventory.py
python tests/test_vlb_viewer_data.py
python -m unittest discover -s tests -p 'test_vlb_mining*.py' -v
python -m unittest tests.test_vlb_corrections tests.test_vlb_reverse_concordance -v
python vlb/manage_corrections.py validate
node vlb/evaluate_corrections.cjs --check
python vlb/mining/benchmark-v3/validate_annotations.py
python vlb/mining/evaluate_v3.py
node --test tests/vlb_citation_targets.test.cjs
node tests/vlb_viewer_browser.cjs
```

The browser test requires Playwright plus Chromium. Set `VLB_PLAYWRIGHT_MODULE`
and `VLB_CHROMIUM_PATH` to use an existing installation. It serves the checkout
locally, tests desktop and mobile layouts, compact search, adjustable and
minimizable panes, persisted view preferences, source and citation navigation,
OCR overlays, source-only search, notes and exports, optimized image
extensions, continuous append/prepend and synchronization, occurrence targeting,
exact-span marks, manual-alternative links, correction save/submit/export/import,
strict correction dry runs, responsive correction geometry, and ambiguity
fallbacks. Scans 17, 18, 19, 25, 26, 161, 231, 232, 292 and 303
are used in a sparse checkout; other continuous neighbors use image-only test
fixtures with real page data. `VLB_QA_DIR` optionally selects a folder for
screenshots and results.

The dictionary-formatting workflow runs the data, link and browser regressions.
This branch does not merge or deploy itself.
