# Anchieta — *Teatro*, page 176 (documentary cross-check)

This directory serves one explicitly verified `Anch., Teatro` locator. The
dictionary cites Eduardo de Almeida Navarro's 1999 *Teatro de Anchieta*, page
176. The available local scan is **not** that edition: it is Maria de Lourdes
de Paula Martins's 1954 documentary and critical *Poesias*.

The exact passage was visually verified on Martins printed page 632,
zero-based PDF index 683 (PDF ordinal 684): `Tupansý, nde maenduá xe ri!`,
translated there as `Nossa Senhora, lembra-te de mim!`. That page also contains
the other quotations behind all nine unsuffixed `Anch., Teatro, 176` records in
the served dictionary.

This is an explicit quotation-level crosswalk, not a page offset. Martins
printed page 176 is unrelated. Citations that say `Anch., Teatro, 176, 2006`
and every other Teatro locator therefore remain unlinked until their passages
are independently aligned.

The 105,331,955-byte source PDF is not copied into the Pages artifact. Its
Internet Archive URL, identity, checksum, page count, exact mapping, and
verification boundary are in [source.json](source.json). To reproduce the one
derived image from a verified local copy:

```bash
python scripts/data/render_source_pages.py \
  --pdf docs/primary_sources/anchieta_teatro_1954.pdf \
  --manifest docs/primary_sources/anchteatro1954/source.json \
  --page 683
```

Review URL:
`/nhe-enga/docs/primary_sources/?book_name=anchteatro1954&page_number=176`.
