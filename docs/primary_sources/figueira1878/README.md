# Luís Figueira — Grammatica da lingua do Brasil (1878)

These 200 progressive JPEGs reproduce the complete PDF scan of Julius
Platzmann's 1878 facsimile of the 1687 Lisbon edition specified in Navarro's
bibliography. The PDF itself remains at the source library and is not stored
in Git.

The exact PDF is 1,936,830 bytes, has 200 pages, and has SHA-256
`a48d22961a385c3d0cc55bada47bb6e61af85ca3a2d6e20e3102fdb2a881cb57`.
Its title page at zero-based PDF index 10 says *Fac-simile da edição de 1687*,
Leipzig, B. G. Teubner, 1878. See [source.json](source.json) for the URL,
complete provenance, render settings, and verified citation-page list.

Printed pages 1–167 occupy PDF indices 24–190, so printed page `p` maps to
image `p + 23.jpg` and one-based PDF page `p + 24`. All 117 distinct pages
currently cited by the served dictionary have verified headers. The complete
scan is navigable, but that does not claim that all uncited leaves or every
quoted passage were visually collated.

The dictionary's `Fig., Arte, 1686, 64` is preserved verbatim and linked with
a visible warning. Navarro's bibliography and authoritative catalogs identify
the relevant second edition as 1687, no separate 1686 edition was found, and
page 64 contains the exact statement behind the entry: “Çoába, o fim para que,
o instrumento em que, o lugar por onde se vai.”

To reproduce the images, download the PDF outside the repository and run:

```bash
python scripts/data/render_source_pages.py \
  --pdf /path/to/figueira_1878_grammatica.pdf \
  --manifest docs/primary_sources/figueira1878/source.json
```

The renderer validates the PDF before writing 1400-pixel-wide, quality-82
JPEGs. The source image set measures about 50.0 MiB.
