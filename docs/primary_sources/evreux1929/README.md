# D’Evreux — Viagem ao Norte do Brasil (1929)

These 444 JPEGs reproduce the complete scan used for `D'Evreux, Viagem`
citations in the dictionary, including the cover, preliminaries, notes, index,
and final blank leaf. The edition is the one specified in Navarro’s
[bibliography](../DTAbib.txt): César Augusto Marques’s Portuguese translation,
Rio de Janeiro, 1929, collated by Navarro with the French edition of 1864
annotated by Ferdinand Denis.

## Edition and scan provenance

- **Author:** Yves d’Evreux; the title page names him Ivo d’Evreux.
- **Title:** *Viagem ao Norte do Brasil*.
- **Translation:** César Augusto Marques; introduction and notes by Ferdinand Denis.
- **1929 imprint:** “Depositarios — Freitas Bastos & Cia. / Livraria Leite
  Ribeiro / Rio de Janeiro / 1929”; both bookseller names appear on the same
  title page, at PDF page 4 (image `3.jpg`).
- **Series:** *Bibliotheca de Escriptores Maranhenses*, II.
- **Digitization:** Biblioteca Digital Curt Nimuendajú — Coleção Nicolai.
- [Library catalog](https://www.etnolinguistica.org/biblio:evreux-1929-viagem)
- [Internet Archive item](https://archive.org/details/evreux-1929-viagem-ao-norte-do-brasil)
- [Original PDF](https://archive.org/download/evreux-1929-viagem-ao-norte-do-brasil/Evreux_1929_ViagemAoNorteDoBrasil.pdf)

The volume includes a reproduced **1874** title page at PDF page 8. This is
part of the 1929 edition, not a different scan: the *Advertencia*, printed
p. 438, explains the reproduction of Marques’s 1874 translation. Do not
substitute another edition without checking its pagination.

## Printed pages and PDF pages

Image filenames use **zero-based PDF indices**. For this scan, a numbered
printed page `p` is image `p.jpg` and PDF page `p + 1` (counting the cover as
PDF page 1). The viewer’s `page_number` is the printed number, not the PDF
ordinal.

| Content | Image | PDF page (1-based) |
| --- | --- | ---: |
| Cover | `0.jpg` | 1 |
| 1929 title page | `3.jpg` | 4 |
| Numbered introduction p. 14 | `14.jpg` | 15 |
| *so'o-Îurupari*, p. 293 | `293.jpg` | 294 |
| Last printed page, p. 442 | `442.jpg` | 443 |
| Final blank leaf | `443.jpg` | 444 |

Front matter includes unnumbered leaves. Their scan indices must not be
represented as visible printed numbers. Page 144 has a corrected leading
“1”; its position between pages 143 and 145 confirms the mapping.

All **42 distinct printed pages** explicitly cited by the currently served
dictionary were checked: 36 by exact OCR header match and six by visual
inspection (88, 129, 137, 143, 144, 157). Additional anchors at 14, 50, 100,
150, 200, 250, 300, 350, 400, and 442 agree. The Internet Archive page-number
index supports the same mapping throughout, but every page of the volume
has not been visually inspected.

The requested example was checked directly: image `293.jpg` contains
**Soo-Jeropary** and the passage describing the nocturnal animals behind
Navarro’s *so'o-Îurupari* entry. The scan retains the source’s spelling.

## Reproduce the images

Install `PyMuPDF` and `Pillow` in the Python environment used for source
processing. Download the original PDF to a temporary directory outside the
repository. From the repository root:

```bash
python scripts/data/render_source_pages.py \
  --pdf /path/to/Evreux_1929_ViagemAoNorteDoBrasil.pdf \
  --manifest docs/primary_sources/evreux1929/source.json
```

The script validates the PDF’s SHA-256 and its 444-page count before writing
any images. Use `--page 293 --output-dir /tmp/evreux-preview` to render just
the example. Complete provenance, checksum, page mapping, and settings are
in [source.json](source.json).

Pages are rendered at **120 dpi** (approximately the scan’s native
1200 × 1740 pixel resolution), as progressive JPEGs at quality 90. Rendering
the whole PDF page preserves the digitizing library’s visible attribution
overlays on the title and final printed pages. Extracting only embedded
bitmap images would omit those credits. A higher dpi would mostly upscale
the scan rather than recover detail.

The existing Pages build copies these images and applies its usual image
optimizer to the deployment copy. Source PDFs remain available through the
original library/Archive links instead of being duplicated in the Git tree.

## Review examples

- Dictionary: `/nhe-enga/?query=so%27o-%C3%8Eurupari`
- Source page: `/nhe-enga/docs/primary_sources/?book_name=evreux1929&page_number=293`
- Spaced author prefix: dictionary query `tiá!` → printed page 143.
- Page range: dictionary query `Marabá` → printed pages 142–143.
- Last cited page: printed page 364.

The pilot links explicit `D'Evreux, Viagem` citations. Context-dependent
`op. cit.` references remain in the source inventory for manual resolution.
