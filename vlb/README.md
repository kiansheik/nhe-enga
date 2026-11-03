# VLB comparison reader

The public route is `/nhe-enga/vlb/`. It compares the existing facsimile images
with Emerson José Silveira da Costa's unchanged transcription and the VLB
citation occurrences in Nhe'enga's pinned Navarro dictionary snapshot.

The main dictionary links here with printed locators, for example:

```text
/nhe-enga/vlb/?volume=I&page=17&entry=7210
/nhe-enga/vlb/?volume=II&page=78&source=vlb-emerson-r568-p05859
```

`entry` is a dictionary array row in the recorded snapshot. `citation` can
identify an exact citation occurrence. `source` selects a transcription
paragraph. The reader also accepts `page=II-078`. An entry link selects its
citation; it does not silently accept any suggested source association.

## Reading and reviewing

- Select a transcription paragraph to highlight its approximate OCR lines on
  the scan. Open the OCR reading to compare the recognition with the image.
- Open the Navarro tab to inspect citations to the current page. Proposed
  source associations remain visibly labeled. The two assisted reviews name
  the specific source form and do not claim that a whole paragraph is covered.
- Search across the transcription and cited dictionary headwords. For split
  paragraphs, a match within a continuation opens the page containing the words.
- Record observations in the Anotações tab. Notes stay in browser localStorage;
  export JSON to preserve or share them. Each note carries its own source and
  dictionary hashes. There is no remote submission or modification of the
  Google Doc or dictionary.

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

`python vlb/build_data.py` deterministically rebuilds the compressed page files
and search indexes from `source/`, without network access or the full PDF.
See [the source documentation](source/README.md) for provenance, coordinate
conventions and the separate pagination, OCR and lexical evidence layers.
The reader loads only the current page; search indexes load on first search.

The Pages allowlist publishes the HTML, CSS, JavaScript, `data/`, and referenced
PDF metadata. Original image assets remain under `docs/primary_sources/vlb/`;
the reader honors the build's `image-formats.json` and defaults to PNG in a
source checkout. Viewer assets belong to the offline core pack, and scans
remain in the existing `source-vlb` pack.

Changes to `docs/dict-conjugated.json.gz` must update this pinned concordance
before its row deep links can be trusted; the data regression checks the hash.

## Verification

```sh
node --test tests/vlb_dictionary_links.test.cjs tests/dictionary_formatting.test.cjs
python tests/test_vlb_citation_inventory.py
python tests/test_vlb_viewer_data.py
node tests/vlb_viewer_browser.cjs
```

The browser test requires Playwright plus Chromium. Set `VLB_PLAYWRIGHT_MODULE`
and `VLB_CHROMIUM_PATH` to use an existing installation. It serves the checkout
locally, tests desktop and mobile layouts, source and citation navigation,
OCR overlays, split-paragraph search, notes and exports, and optimized image
extensions. Only scans 17, 25, 26, 161, 232, 292 and 303 are needed in a sparse
checkout. `VLB_QA_DIR` optionally selects a folder for screenshots and results.

The dictionary-formatting workflow runs the data, link and browser regressions.
This branch does not merge or deploy itself.
