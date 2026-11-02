# Pinned inputs for the VLB viewer

`../build_data.py` rebuilds the page files and search indexes without network access:

```sh
python vlb/build_data.py
```

The generator uses the Python standard library. Its gzip output has a fixed timestamp,
so rebuilding unchanged inputs produces identical files.

## Sources

- `emerson_vlb.txt`: Emerson José Silveira da Costa's transcription, document revision
  568, preserved exactly. `source_metadata.json` records its source URL, retrieval
  timestamp and SHA-256. The public Google Docs page contained 115 contiguous text
  payloads; the original text was recovered without changing spelling or punctuation.
- `page_alignment.json.gz`: original-print pagination associated with exact character
  offsets in the transcription. The evidence includes estimated boundaries and bounded
  uncertainty. A paragraph can continue on the following page.
- `page_map.json`: the physical PDF/scan sequence, including front matter, the manuscript
  plate at scan 25, and its blank verso at scan 26. There are 279 lexical text pages.
- `ocr_layout.json.gz`: OCR text runs and their original PDF bounding boxes, sufficient
  to reproduce approximate highlighting. The viewer reuses the repository's existing
  facsimile images; neither images nor the large original PDF are copied here.
- `pdf_source_metadata.json`: edition, PDF source and checksum evidence.
- `citation_links.json.gz`: every extracted Navarro citation occurrence, with original
  offsets and local context, proposed source-paragraph associations, and unresolved
  references. Dictionary row locators apply only to the pinned dictionary snapshot.
- `reviewed_examples.json`: the initial exploratory review; its candidate judgments
  are not automatically promoted to reviewed links in the viewer.
- `verified_citation_associations.json`: only specific citation occurrences independently
  checked against the source and dictionary context. Each records its reviewer and
  restricted scope. It never declares an entire source paragraph fully accounted for.

The transcription is available on [Google Docs](https://docs.google.com/document/d/1oNYyk0gHjtP4Rm_Auemt-63DYMXLY9GgFtQ2OE2H6Ek/edit),
with provenance on Emerson's [VLB site](https://sites.google.com/site/vocabularionalinguabrasilica/)
and his [Tupi resource page](https://abanheenga.blogspot.com/p/como-aprender-tupi.html).

## Three separate relationships

1. **Print page to transcription:** established by OCR alignment and selected visual
   checks. The original uncertainty intervals remain available in the page data.
2. **Transcription to OCR boxes:** an approximate, monotonic spelling alignment. The
   score is the fraction of matched source tokens; it is not a probability.
3. **Navarro occurrence to source entry:** proposed unless explicitly reviewed for that
   exact occurrence. Similar words or a common page number do not confirm equivalence.

`source_line` numbers identify paragraphs in the saved transcription, not lines on the
printed page. Source intervals use zero-based, half-open character offsets. All source
characters are within the BMP, so adding one gives the original one-based UTF-16 index.

The complete transcription and unresolved citations are retained. Changing the
transcription without updating its checksum or page alignment causes validation to
fail, rather than silently moving previously established links.
