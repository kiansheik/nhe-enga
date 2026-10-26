# Araújo — Catecismo Brasílico (1686)

This directory serves the second edition cited by Navarro as
`Ar., Cat., {page}, 1686`. It intentionally contains only the 58 printed pages
explicitly cited by the served dictionary and two pages of context on either
side: 158 images in 16 contiguous ranges. It is not a complete online copy.

## Pagination and provenance

- **Edition:** Antônio de Araújo, *Catecismo Brasílico da Doutrina Cristã*,
  second edition emended by Bartolomeu de Leão (Lisboa: Officina de Miguel
  Deslandes, 1686).
- **Digitization:** Biblioteca Nacional de Portugal.
- [Catalog record](https://www.etnolinguistica.org/biblio:araujo-1686-catecismo)
- [BNP persistent record](https://purl.pt/14250)

Image filenames use zero-based PDF indices. Printed page `p` is image
`p + 35.jpg` and PDF ordinal `p + 36`: printed page 1 is image `36.jpg`, and
the cited page 241 is image `276.jpg`. Page 241 was visually checked against
the dictionary quotation for `emo'emyîara`.

The source itself misnumbers printed page 137 as 237. This does not change the
sequential mapping. Printed page 371 is image `406.jpg`; the remaining PDF
pages are tables, manuscript leaves, and blanks.

## Reproduce the selected images

Keep the source PDF at `docs/primary_sources/ar.Cat.1686.pdf`, then run:

```bash
python scripts/data/render_source_pages.py \
  --pdf docs/primary_sources/ar.Cat.1686.pdf \
  --manifest docs/primary_sources/arcat1686/source.json
```

The renderer verifies the PDF checksum and page count, derives the 158-image
selection from `all_cited_pages` plus the two-page buffer, and writes only
those JPEGs. Complete checksums, cited pages, ranges, and rendering settings
are recorded in [source.json](source.json).

## Review examples

- Dictionary: `/nhe-enga/?query=emo%27emy%C3%AEara`
- Source page: `/nhe-enga/docs/primary_sources/?book_name=arcat1686&page_number=241`
- Range citation: dictionary query `-tene` links printed pages 11 and 12.
