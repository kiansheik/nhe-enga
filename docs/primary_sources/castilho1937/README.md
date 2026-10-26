# Pero de Castilho — Nomes das Partes do Corpo Humano (1937)

These 16 progressive JPEGs are the complete set of printed pages currently
cited by the served dictionary. They come from Plínio Ayrosa's 1937 edition,
the edition specified by Navarro. The 70-page source PDF contains landscape
spreads; each delivered image is a full-height left/right page crop with its
printed label and margins preserved.

The exact PDF is 11,660,598 bytes, has 70 PDF pages, and has SHA-256
`7e2f9dc0323e4ef1a7bbc82a6dcd3b687f93457e780fecb868c8841389fe1519`.
See [source.json](source.json) for the institutional URL, provenance, explicit
16-target crop map, and render settings.

The mapping cannot use a constant offset: printed page 38 is the left side of
PDF index 21; an inserted manuscript facsimile and blank side intervene; page
39 is the right side of index 22. Page 45 is the right side of index 26.
Navigation therefore jumps only among the available cited pages 27–41 and 45,
while the original PDF link supplies the complete facing-page context.

To reproduce the crops, download the PDF outside the repository and run:

```bash
python scripts/data/render_source_pages.py \
  --pdf /path/to/ayrosa_1937_nomes.pdf \
  --manifest docs/primary_sources/castilho1937/source.json
```

The renderer validates the PDF and consumes the explicit crop boxes in the
manifest before writing 1200-pixel-wide, quality-85 JPEGs. The 16-image source
set measures about 5.1 MiB.
