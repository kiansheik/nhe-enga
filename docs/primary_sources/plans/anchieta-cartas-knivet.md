# Anchieta's Cartas and Knivet: capybara attestation groundwork

Status: **research handoff, not a production source import**. Researched 2026-10-13 against main `462567e609eaf3915d6263c3b458c17dab18c62e`.

The immediate question is the documentary basis of `kapi'iûara` / `kapibara`, following a request for an accessible Anchieta or Knivet witness beyond Marcgrave. This note identifies Navarro's specified editions, supplies a visually checked passage in a comparison edition, and records the remaining verification gates. It does not change dictionary text, morphology, citation links, production manifests, or source images.

## 1. Existing work and scope

The D'Evreux pilot is merged in [PR #25](https://github.com/kiansheik/nhe-enga/pull/25). [PR #26](https://github.com/kiansheik/nhe-enga/pull/26), branch `docs/next-primary-source-groundwork`, remains the integration work for the next batch. Its [README](https://github.com/kiansheik/nhe-enga/blob/docs/next-primary-source-groundwork/docs/primary_sources/plans/README.md) says Figueira and Castilho are implemented for review; Sousa and D'Abbeville remain research plans. The README's boundary is to review that first pair before another production import. This document prepares the next research task without changing that branch or bypassing review.

The baseline below comes from the existing [inventory](../source_inventory.md), not a fresh extraction in this session:

| Work family | Explicit citations | Dictionary records | Current research/integration position |
| --- | ---: | ---: | --- |
| Anchieta, Cartas | 29 | 27 | Exact edition located; capybara passage found in OCR; scan-page verification pending. |
| Knivet, The admirable adventures | 19 | 19 | Exact cited publication identified; a later English reprint located; precise capybara passage unresolved. |
| Figueira, Arte | 622 | 455 | Implemented for review in PR #26. |
| Castilho, Nomes | 215 | 162 | Implemented for review in PR #26. |
| Sousa, Tratado | 394 | 389 | Existing plan; mapping and citation discrepancies still need resolution. |
| D'Abbeville, Histoire | 449 | 439 | Existing plan; folio/image verification still needs completion. |
| Marcgrave, História Natural | 651 | 636 | High coverage, but Portuguese pagination and Latin spelling collation must be distinguished. |
| Carder, Relation | 2 | 2 | Possible additional benefit from researching the Purchas compilation; do not assume the same volume or page map. |

These counts are occurrences, not verified destinations. Records can overlap between work families. The inventory's served input is `docs/dict-conjugated.json.gz`, with decompressed SHA-256 `8906cb4ddd292db7d67901ec9fb3c288d94b9baf9ae9cb35cb1d8a4a30e8e02e`. The similarly named `dict-conjugated.json` is a different gzip dataset and must not be substituted. Regenerate the inventory if the served input changes.

## 2. What Navarro's bibliography specifies

Source: [DTAbib.txt](../DTAbib.txt), lines 3, 37 and 48.

### Anchieta: the 1933 collection, not the 1900 standalone translation

> Cartas, Informações, Fragmentos Históricos e Sermões. Publicação da Academia Brasileira de Letras, Livraria Civilização Brasileira, S.A., Rio de Janeiro, 1933.

Acquisition candidates for that edition:

- [Nimuendajú catalogue and two scan downloads](https://www.etnolinguistica.org/biblio:anchieta-1933-cartas).
- [Mindlin scan PDF](https://etnolinguistica.wdfiles.com/local--files/biblio%3Aanchieta-1933-cartas/anchieta_1933_cartas_mindlin.pdf). The browser fetch reported a 19,190,193-byte object exceeding its parsing limit. The file was **not** downloaded into the working environment or checksummed.
- [Internet Archive scan](https://archive.org/details/r-19794-v_0000_grav-569_t24-C-R0150/page/122/mode/1up?view=theater), item `r-19794-v_0000_grav-569_t24-C-R0150`. This is the actual discovery URL, **not a verified capybara page link**; its `/page/122` suffix came from a secondary reference. The catalogue identifies the 1933 Civilização Brasileira edition.
- [Internet Archive full OCR](https://archive.org/stream/r-19794-v_0000_grav-569_t24-C-R0150/r-19794-v_0000_grav-569_t24-C-R0150_djvu.txt). The title-page transcription also identifies the 1933 edition.

Keep the Mindlin and BNP-derived/Archive copies separate: covers, page omissions and scan offsets can differ even when the printed edition is the same. No exact-edition PDF checksum, physical page count, global offset or per-citation image map was established in this session.

### Knivet: Purchas, London 1625

> KNIVET, Antonie, “The admirable adventures and strange fortunes of Master Antonie Knivet which went with Master Thomas Candish in his second Voyage in the South Sea”. [1591]. In Purchas, Samuel, His Pilgrimes, London, 1625.

The bracketed 1591 is not the publication date of the cited printed book. Target the English narrative as published in Purchas in 1625; do not silently route those locators to a Portuguese translation or to a differently paginated English reprint.

A useful search/comparison edition is available through [Nimuendajú's Knivet 1906 catalogue](https://www.etnolinguistica.org/biblio:knivet-1906-admirable): *Hakluytus Posthumus or Purchas His Pilgrimes*, Glasgow, James McLehose and Sons, **volume XVI, chapter VII, pp. 177–289**. The catalogue lists a 2.71 MB PDF attachment, `knivet_1906_admirable.pdf`.

This establishes a practical acquisition lead, not an attestation. **The capybara wording and page in Knivet were not located/verified during this session.** No 1625-to-1906 page concordance was established. Leave both the original target and any alternative-edition mapping unresolved until the text is collated.

### Marcgrave: 1942 translation, collated with 1648 Latin

The bibliography specifies the 1942 São Paulo Portuguese translation by José Procópio de Magalhães and says it was collated with the 1648 Latin edition at IEB-USP for Tupi spellings. This distinction matters for the request about `kapibara`: a freely available 1648 scan is valuable evidence, but it is not automatically the correct destination for a page locator belonging to the 1942 translation.

## 3. Anchieta passage: what is actually established

### A. Visually verified, immediately shareable comparison witness

[BBM-USP PDF, printed page 19 / PDF page 31](https://digital.bbm.usp.br/bitstream/bbm/4683/1/000600_COMPLETO.pdf#page=31)

This is the **1900 Portuguese translation by João Vieira de Almeida**, with a preface by Augusto César de Miranda Azevedo, of the natural-history letter. It is **not** Navarro's 1933 collection and is not a photograph of Anchieta's autograph.

The image of printed p. 19 was inspected. Section X is headed **“Do arganaz Capyvára.”** The body uses **Capyvára** and supplies the explanation **“que pastam hervas”**. It goes on to describe the animal's appearance, lack of a tail, herbivory and domestication. The edition's note 19 separately discusses the form *Capivára*; do not conflate the note with the body text.

| Field | Verified value / status |
| --- | --- |
| PDF | `https://digital.bbm.usp.br/bitstream/bbm/4683/1/000600_COMPLETO.pdf` |
| Edition | São Paulo, 1900; João Vieira de Almeida translation |
| Printed page | 19 |
| Zero-based PDF index | 30 |
| External PDF fragment | `#page=31` |
| Image inspection | Header, spelling and passage visually checked |
| Whole-PDF page count | Browser parser reports 87; not independently checked from local bytes |
| SHA-256 / local bytes | Not acquired |
| Whole-book offset | Not established; this is a single checked target |
| Role | Comparison witness only, not an automatic target for `Anch., Cartas` |

The letter's closing dateline appears on printed p. 50 / PDF page 62 and dates it to the end of May 1560 in São Vicente. Distinguish the date of the letter from the date and orthography of this printed translation.

### B. Exact 1933 edition: passage found in OCR, image check still needed

In the Archive OCR, find the paragraph beginning `Ha tambem outros animais do genero anfíbio`. The word is broken over a line as `ca-` / `piyúára` in that OCR output, followed by the same explanation about grazing herbs. **Do not promote the OCR's accent or letter sequence to a diplomatic transcription.**

There is a pagination trap. A secondary reference led to p. **122**, but in the actual OCR stream the capybara paragraph lies between the printed 110 and 112 headers, apparently on **p. 111**. The OCR's p. 122 section concerns insects. The apparent p. 111 location is an inference from surrounding headers, not a visually verified printed label or PDF index. Do not put either 111 or 122 into a live capybara mapping until a scan image resolves it. Do not attribute this discrepancy to Navarro without inspecting the actual dictionary citation.

The raw capybara dictionary record itself was not recovered from the served gzip in this session. The bibliography identity is established from the repository's bibliography; the entry's exact citation string, any locator, and its editorial spelling remain a mandatory extraction step.

This is sufficient to supply Gabriel with a real, readable Anchieta witness now, but not to claim that the modern normalized spelling `kapi'iûara` occurs literally in that witness.

## 4. Implementation handoff and acceptance gates

1. Read `AGENTS.md`, `CLAUDE.md`, and PR #26's current plan/implementation. Keep this task separate from morphology and corpus ground truth. Do not merge or deploy without review.
2. Run `python scripts/data/source_inventory.py` against the served dictionary. Extract the raw capybara entry and every Anchieta-Cartas / Knivet occurrence from the existing audit; preserve entry indices, citation text, inherited locators and character offsets. The audit file is `docs/primary_sources/source_citation_audit.jsonl.gz`.
3. Download and pin one exact 1933 scan and the relevant 1625 Purchas scan. Record acquisition URLs, byte sizes, SHA-256 digests and actual PDF page counts. Keep alternate editions as separate witnesses. Never substitute a catalogue page-count field for inspected PDF structure.
4. Resolve the 1933 capybara page and its spelling on the image. Separately locate Knivet's actual passage, including its printed page and spelling. An OCR match is only a search aid. Preserve original citation text if its locator proves mistaken and expose a documented correction/warning rather than rewriting the dictionary.
5. Build an explicit printed-locator-to-image map for the 29 and 19 citation families, distinguishing page-header verification from quotation matching. Cover all unambiguous targets; leave unsupported references unlinked. Record gaps and edition-qualified exceptions. Do not infer a whole-book offset from the single 1900 target above.
6. Only then create production `source.json` manifests and render with the existing `scripts/data/render_source_pages.py` workflow. Research notes are not renderer manifests. Select a readable per-book render scale and run the PR #26 storage check before committing image collections.
7. Extend the actual `linkSources()` implementation in `js/index.js` conservatively, preserving the visible citation text. Test exact-edition links, alternate editions, page ranges, malformed references, ambiguous labels and missing targets. Confirm that every generated link has a real image and that source navigation works on mobile.
8. Re-run the inventory and report measured coverage and asset size. Do not report the 48 potential occurrences as 48 verified working links until the rendered destinations and references are checked.

## 5. Next-source priority

The first low-effort step is reviewing the already-implemented Figueira/Castilho pair, not reimplementing it. For this specific request, Anchieta's 1933 *Cartas* should be the next targeted acquisition: the correct edition and the relevant paragraph have now been found. Knivet should follow after the exact 1625 passage is established; the compact 1906 extract is an aid to finding it, not a substitute edition.

Marcgrave has substantially greater potential coverage, but its translation/original distinction makes it a separate collation project. Sousa and D'Abbeville already have plans; finish those rather than constructing competing source registries. Carder is worth checking while acquiring Purchas, but its volume and page map must be independently identified.

## Verification performed / not performed

Performed: repository rules, bibliography, inventory and next-source plan inspected; 1900 p. 19 image checked; 1933 catalogue/title OCR and capybara paragraph located; Knivet 1906 catalogue inspected; edition and pagination conflicts recorded.

Not performed: local primary-source PDF acquisition/checksums, 1933 capybara image verification, Knivet attestation verification, raw capybara dictionary-entry extraction, full citation maps, renderer execution, link tests, production import, merge or deployment.
