# Next primary sources: groundwork for the local agent

The D’Evreux pilot is merged in [PR #25](https://github.com/kiansheik/nhe-enga/pull/25).
This follow-up prepares **Figueira, Castilho, Sousa, and D’Abbeville** for local
implementation. It supplies exact-edition acquisition records, PDF checksums,
page/folio research, cited targets, unresolved references, and storage checks.
It adds no new book images or live citation links.

Research starts from main commit `81c21de3f444983630a06ffc252e821c03dffb35`.
Read `AGENTS.md` and `CLAUDE.md` before implementing. This task concerns source
assets and citation display; dictionary definitions, corpus ground truth, and
morphology are not inputs to rewrite to make a citation fit a scan.

## Start here

> Read `docs/primary_sources/plans/README.md` and the four source-plan JSON
> files beside it. Implement Figueira and Castilho first, using the merged
> D’Evreux code as the baseline. Download each pinned PDF outside the repo,
> verify its checksum, use the verified locator maps, and prepare readable
> web images with per-book render settings. Extend the existing viewer,
> linker, and Pages copy pipeline, run the size preflight on the complete
> optimized artifact, and open a reviewable implementation PR. Keep Sousa
> and D’Abbeville as the next stages: resolve their explicitly pending
> mappings/content discrepancies and measure storage before adding assets.
> Preserve the original citation text and keep every unresolved case visible.
> Do not merge or deploy the implementation PR as part of this task.

### Plans and expected coverage

Counts come from the served `docs/dict-conjugated.json.gz` and the existing
[citation audit](../source_inventory.md). They count explicit occurrences,
including repetitions within one dictionary record. Recompute if the input
checksum changes; these counts are not a license to force ambiguous matches.

| Order | Plan | Edition Navarro specifies | Explicit citations / records | Main implementation issue |
| --- | --- | --- | ---: | --- |
| 1 | [figueira1878.json](figueira1878.json) | Lisbon 1687, in Platzmann’s Leipzig 1878 facsimile | 622 / 455 | 117 unambiguous cited printed pages checked; one `1686, 64` citation remains unresolved. |
| 2 | [castilho1937.json](castilho1937.json) | Plínio Ayrosa’s 1937 edition of Castilho’s *Nomes* | 215 / 162 | All 16 cited page/side targets checked; inserted facsimiles break a constant spread offset. |
| 3 | [sousa1987.json](sousa1987.json) | Fifth edition, Companhia Editora Nacional, 1987 | 394 / 389 | Two-page spreads, 18 chapter/Roman-numeral references, and sampled quotation/page discrepancies. |
| 4 | [abbeville1614.json](abbeville1614.json) | Paris, François Huby, 1614 | 449 / 439 | Recto/verso folios, numbering errors, and PDF indices differing from catalog scan counts. |

The first pair accounts for 837 explicit citations. An edition-qualified or
otherwise unresolved occurrence must remain unresolved until its evidence is
established; do not claim every occurrence produces a verified link merely
because its regex matches.

## What the JSON files mean

These are **research plans**, identified by `status: "research_plan"`, not
the current renderer’s production `source.json` schema. Do not pass them
directly to `render_source_pages.py`, copy them into a live source registry,
or enable a source just because its plan exists.

Each plan carries:

- `navarro_bibliography`: the bibliography path, line references, exact entry,
  and edition identity. Preserve the distinction between an original edition
  and the facsimile/translation Navarro actually used.
- `pdf`: catalog and download URLs, the downloaded file’s SHA-256, byte count,
  and **actual PDF page count**. Other scans of the same edition can have
  different covers, omissions, or offsets.
- `mapping`: locator units, a proposed rule where useful, checked anchors,
  per-locator targets and verification status, and unresolved cases.
- `citation_baseline`: source input identity and counts from this snapshot.
- `render_plan`: per-book pixel/quality considerations and sample size
  estimates where measured. An estimate is not a completed full-book render.
- `local_agent_actions`: the book-specific work still needed.

**`pdf_index` is zero-based.** An external PDF link uses `#page=pdf_index+1`.
`scan_side` identifies the full page or the left/right side of a spread.
Keep the raw citation locator separate from the scan index and filename.
An unverified or null target is not a link-ready mapping. A proposed formula
does not upgrade the verification status of every locator it could generate.

Page-header verification establishes where a printed locator appears in
this PDF. Quotation matching establishes whether Navarro’s cited passage is
actually on that printed page. Preserve that distinction in implementation
notes, tests, and any final manifest.

## Book-specific findings

### Figueira: ordinary pages, but choose the render scale independently

The exact [1878 PDF](https://www.etnolinguistica.org/biblio:figueira-1878-grammatica)
contains 200 PDF pages and reproduces the 1687 edition. The title and page
headers support **printed `p` → `pdf_index = p + 23`**. All 117 unambiguous
cited printed-page targets have been checked, using header OCR with a visual
check where OCR split the digits on p. 133. This does not claim that all 200
leaves or every quotation have been visually examined.

Keep `Fig., Arte, 1686, 64` in the unresolved list; it cannot be silently
reinterpreted as an ordinary 1687 citation just because p. 64 exists. Page
ranges and the inherited numeric continuation are separate parsing cases.

The scan’s roughly 2264 × 3256 pixel body images are embedded on physically
small PDF pages. D’Evreux’s 120 dpi would render this book at only about 452
pixels wide. Support a target pixel width or compute the scale per page,
preserving aspect ratio. Start by reviewing approximately 1400-pixel-wide
images and increase only if the small text needs it. The existing optimizer
caps height at 2400 pixels; account for its final output when comparing
quality. The PDF’s compact download size is not the projected JPEG total.

### Castilho: a small explicit spread map

Use the exact [1937 edition](https://bibliotecadigital.mj.gov.br/handle/1/7907)
pinned in the plan. It has 70 landscape PDF pages containing spreads.
The dictionary cites printed pages **27–41 and 45**. All 16 are checked:

| Printed locator | Zero-based PDF index | Side |
| --- | ---: | --- |
| 27 | 15 | right |
| 28 / 29 | 16 | left / right |
| 30 / 31 | 17 | left / right |
| 32 / 33 | 18 | left / right |
| 34 / 35 | 19 | left / right |
| 36 / 37 | 20 | left / right |
| 38 | 21 | left |
| 39 | 22 | right |
| 40 / 41 | 23 | left / right |
| 45 | 26 | right |

The spread at index 21 pairs p. 38 with a manuscript facsimile; index 22 has
a blank left side and p. 39 on the right. A generic formula would misroute
the later citations. Printed p. 45 contains the arm-base entry behind the
dictionary’s `îybaypy` citation.

The plan describes page crops. A complete-spread viewer with an explicit
target-side focus is also acceptable if it is readable on mobile. Choose
one delivered image representation; do not retain duplicate full-spread and
cropped JPEG collections just to support both approaches. Preserve scan
provenance and access to the complete original PDF in either case.

### Sousa: page location and citation correctness are separate

The [1987 fifth-edition scan](https://www.etnolinguistica.org/biblio:sousa-1987-tratado)
contains **201 PDF pages of spreads**. The sampled page headers support the
candidate rule `pdf_index = floor(p / 2) + 4`, even page left and odd page
right. Only targets marked checked in the plan are established by inspection;
the rest still need verification.

Of 394 explicit references, 376 contain numeric page locators and 18 use
Roman numerals or chapter notation. The work has parts with restarted
chapter numbering: chapter LIII is not a globally unique page label. Keep
part, chapter, printed page, PDF index, and spread side as different fields.

Sampled quotation checks exposed exceptions, including `abaîeru` citing
p. 188 while its quoted wording appears at p. 196. Other references do match
their cited page, so this is not a reason to apply an eight-page correction
to the book. Consult the plan’s full evidence and unresolved cases. Preserve
Navarro’s citation text and prepare editorial discrepancies for review;
do not rewrite the dictionary or silently substitute the located page.

### D’Abbeville: retain folio sides and scan identity

Use the [John Carter Brown scan of Paris 1614](https://archive.org/details/histoiredelamiss00clau).
The catalog reports 848 scanned pages, but the downloadable PDF checked here
has **846 PDF pages**. All plan indices refer to that exact PDF, identified
by its checksum. Do not copy a BookReader scan index straight into a PDF URL.

The volume has 395 numbered leaves. A reference such as `186v` needs the
verso of leaf 186; it is not printed page 186. Sampled anchors suggest
`pdf_index = 2*n + 16` for recto and `2*n + 17` for verso, but the catalog
flags numbering errors and the formula remains provisional outside checked
targets. Logical folio 362 is visibly misprinted as 392 at PDF index 740;
its *Itapoucou* passage supports the logical locator. Keep logical locators,
observed headers, and exceptions explicit.

## Storage: check the delivered site as well as the repository

The [measured baseline](storage-baseline.json) records complete Git Trees
responses for the merged main branch and the current `gh-pages` artifact.
These are different quantities:

| Measurement, 2026-10-06 | Bytes / reported units | Meaning |
| --- | ---: | --- |
| Current main files | 4,637,613,470 bytes | Sum of file sizes in main, without Git history. |
| Current `gh-pages` files | 720,136,184 bytes | Committed optimized publish artifact, including grammar and other assets. |
| GitHub repository metadata | 5,815,646 KiB | GitHub’s repository-size estimate; not the published-site size. |

[GitHub Pages documents a 1 GB published-site limit](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).
Using a conservative decimal 1,000,000,000-byte interpretation leaves
**279,863,816 bytes** above this artifact. The preflight uses a **900,000,000-byte
project budget**, leaving a 100 MB reserve below that limit; this budget is
our planning choice, not a separate GitHub rule. There are 179,863,816 bytes
of room within that project budget at this snapshot.

The build already excludes source PDFs and optimizes a copy of the page
images. It still commits the source images in main and the optimized images
on `gh-pages`. For example, D’Evreux accounts for about 272 MB in main and
222 MB in the publish artifact. Large legacy image sets dominate main:
`bettvulg` alone is about 1.82 GB and is not in the current publish artifact.
Do not accidentally add it to the image-copy list while extending the build.

The plans include these representative image samples. All totals below are
linear projections from selected pages, **not measured complete outputs**.

| Candidate image set | Sample settings | Projected image bytes, decimal MB |
| --- | --- | ---: |
| Figueira, all 200 PDF pages | 1400 px wide, JPEG 82; 5 samples | 54.4 MB |
| Castilho, 16 cited page crops | 1200 px wide, JPEG 85; 4 samples | 5.3 MB |
| Castilho, all 70 spreads, alternative | 2400 px/JPEG 90 inputs through the current optimizer to 1800 px/JPEG 82; 3 samples | 25.7 MB |
| Sousa, 389 numbered pages | 1600 px wide, JPEG 85; 7 samples | 276.8 MB |
| D’Abbeville, all 846 PDF pages | 1600 px wide, JPEG 85; 4 samples | 497.0 MB |

Only the Castilho full-spread alternative in this table has gone through the
current deployment optimizer; the plans record additional sample variants.
Sousa’s estimate covers its 389 numbered pages and omits front matter.
None of these estimates include extra metadata or other
site changes. The larger-book settings are diagnostic, not selected
production defaults. The first pair looks feasible within the current
budget, but complete Sousa and D’Abbeville images at these settings do not.
Measure real optimized output before selecting full-book or cited-target
coverage.

For the first pair, the current static architecture is a reasonable starting
point. The groundwork does **not** establish that complete images for every
remaining book will fit. Keep the PDF downloads, scratch renders, previews,
and duplicate quality experiments outside Git. Do not rewrite repository
history or migrate storage as part of this groundwork.

### Read-only size preflight

After creating the complete optimized local build:

```bash
python3 scripts/check_pages_size.py .pages-build
python3 scripts/check_pages_size.py .pages-build --json
```

The checker exits 0 within budget, 1 over the total/per-file budget, and 2
when it cannot establish a complete measurement. It includes all files,
including non-source site assets, and counts the same content at two public
paths twice. It rejects incomplete/truncated tree metadata rather than
presenting an underestimate as a pass. It performs no network or Git writes.

To inspect a committed artifact without downloading its images, save a
complete recursive Git Trees response using the GitHub CLI, then measure it:

```bash
gh api 'repos/kiansheik/nhe-enga/git/trees/gh-pages?recursive=1' > /tmp/nhe-enga-pages-tree.json
python3 scripts/check_pages_size.py --tree-json /tmp/nhe-enga-pages-tree.json
```

The snapshot in this PR is reproducible with that method. Before each book’s
implementation PR, record the actual main asset delta, optimized artifact
delta, full site total, image dimensions/quality, and any unrendered targets.
If the measured candidate exceeds the project budget, first avoid duplicate
images and compare readable compression settings. A cited-target-only set
requires availability-aware navigation; it must not expose broken next-page
buttons. Keep an original-PDF link for wider context.

If satisfactory complete-book images still cannot fit, prepare an explicit
follow-up design for externally hosted image assets with per-source base URLs,
while preserving citation URLs, manifests, and checksums in this repository.
Do not assume Git LFS alone removes the Pages artifact limit. Creating paid
storage, changing hosting, and rewriting old history are separate decisions.
[GitHub’s repository guidance](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)
also recommends keeping generated assets outside Git as repositories grow.

## Implementation contract

1. **Verify the input.** Download the plan’s exact URL outside the checkout.
   Check SHA-256, byte count, actual PDF page count, edition/title evidence,
   and digitizer attribution. A replacement PDF requires a new mapping audit.
2. **Convert a reviewed plan into a production manifest.** Keep source ID,
   raw citation locator, printed label, PDF index, spread side/crop, output
   image path, and verification state separate. Store the page-to-image
   mapping in one place rather than applying one offset in `linkSources()`
   and another in the viewer. Plans are not automatically registered sources.
3. **Extend the existing renderer.** The current
   [`render_source_pages.py`](../../../scripts/data/render_source_pages.py)
   supports fixed-dpi full-page JPEGs only. Add explicit target-width and
   spread/crop support where needed; preserve complete PDF rendering within
   the selected area so visible annotations are retained. Keep D’Evreux’s
   existing manifest and output behavior compatible. Use atomic writes.
4. **Resolve citations conservatively.** Extend the real `linkSources()` in
   [`js/index.js`](../../../js/index.js), preserve displayed text, support
   observed author/work spellings and ranges, and keep source/edition
   qualifiers. An inherited continuation, Roman chapter, or folio suffix
   must not become an unrelated numeric page. Keep ambiguous and disproven
   quotation matches in an explicit unresolved report.
5. **Extend the existing viewer.** Retain the source citation URL shape and
   display the printed locator independently of the image filename. Provide
   edition/credit details, correct PDF ordinals, readable fit/zoom, and
   navigation that follows the actual available scan/crop map. An unresolved
   target must not silently fall back to a plausible but unverified image.
6. **Add only final assets to the copy list.** Update
   [`build_pages.sh`](../../../scripts/build_pages.sh) with the implemented
   book directory and its provenance. The copy helper only includes images;
   nested `source.json` files need an explicit copy. Keep the bibliography
   link available. The `plans/` research directory is not a public asset
   collection and should stay out of the publish artifact.
7. **Validate the actual result.** Re-run the inventory, compare citation
   counts/targets, decode every delivered image, test the real dictionary
   → viewer → PDF flow, and check desktop/mobile navigation. Run the existing
   focused source tests plus new per-source cases. Build the full optimized
   artifact and run the size preflight before opening the implementation PR.

If unrelated build prerequisites block a full build, record that limitation
and measure a faithful complete artifact assembled from known published
assets plus the candidate changes. A partial source directory is not a full
site size measurement. Do not claim a full VuePress/Pyodide build passed
based on the source tests alone.

### Review evidence to include

- Exact source URL/checksum and edition match, plus the mapping’s verification
  scope and any unresolved editorial references.
- A coverage table distinguishing explicit occurrences, successful links,
  distinct image targets, and unresolved cases.
- Representative source and optimized images at reading size, including
  small type, page numbers, gutter/crop edges, and diacritics.
- Real browser checks, existing-source regressions, and the complete Pages
  size report with actual byte counts.
- Separate, reviewable source additions. Finish Figueira and Castilho before
  expanding implementation to the larger or less-settled books.

## Later sources

Marcgrave’s 1942 Portuguese translation (651 explicit citations) remains a
high-value acquisition task; this pass has not pinned a verified download
of that exact edition. Do not substitute the 1648 Latin PDF without mapping
its text and pagination separately. Anchieta’s *Teatro* (1431) and *Poemas*
(700) are also valuable, but need exact edition files, including resolution
of the *Teatro* 1999/2006 distinction. Other bibliography families remain in
the existing inventory; they are not implicitly covered by these four plans.
