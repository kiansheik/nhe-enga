# Anchieta — *Teatro* (documentary cross-check)

This directory serves documentary witnesses for every `Anch., Teatro`
edition-and-page locator in the current dictionary: 1,431 citations in 882
records. The citations refer to Eduardo de Almeida Navarro's 1999 *Teatro de
Anchieta* or, when `2006` is written explicitly, its second edition. The
available public scan is **not** either Navarro edition: it is Maria de Lourdes
de Paula Martins's 1954 documentary and critical *Poesias*.

The map retains Navarro's cited page in the URL and selects a corresponding
Martins page by quotation or headword context. It covers 107 edition-and-page
keys with 75 stored scan pages. It is an explicit cross-edition alignment, not
a page offset; the same Navarro page may map differently in 1999 and 2006, and
nearby locators can share one documentary page.

## Alignment method and boundary

[`scripts/data/align_anchieta_teatro.py`](../../../scripts/data/align_anchieta_teatro.py)
compares the source/translation context immediately before each served
citation with the Internet Archive DjVu XML OCR and ranks candidate PDF pages.
Those candidates and the order of the two dramatic sequences were reviewed
before recording the map in [`source.json`](source.json). The later adaptation
*Na festa do Natal* repeats text from *Na festa de São Lourenço*; the map keeps
the São Lourenço sequence used by Navarro instead of silently jumping to the
duplicate later in Martins.

The result is a representative documentary witness for each cited locator,
not a claim that all content on a Navarro page is identical to one Martins
page. Unknown locators and edition years other than the explicit 2006 form
stay unlinked.

## Reproduction

The 105,331,955-byte source PDF is not copied into the Pages artifact. Its
Internet Archive identity, checksum, page count, complete maps, and
verification counts are in `source.json`. To reproduce the derived images,
collect the unique PDF indices from both `page_to_pdf_index` maps and pass each
as a repeated `--page` argument:

```bash
python scripts/data/render_source_pages.py \
  --pdf docs/primary_sources/anchieta_teatro_1954.pdf \
  --manifest docs/primary_sources/anchteatro1954/source.json \
  --page 655 --page 656 # ...all unique mapped indices
```

Review URLs:

- `/nhe-enga/docs/primary_sources/?book_name=anchteatro1954&page_number=36`
- `/nhe-enga/docs/primary_sources/?book_name=anchteatro1954&page_number=176`
- `/nhe-enga/docs/primary_sources/?book_name=anchteatro1954&page_number=176&citation_year=2006`
