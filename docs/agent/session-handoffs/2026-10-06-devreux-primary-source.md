# Local agent task: D’Evreux primary-source pilot

**Status:** implemented and merged in [PR #25](https://github.com/kiansheik/nhe-enga/pull/25).
The pilot-only review boundary below records the original task. Continue with
the [next-source groundwork](../../primary_sources/plans/README.md) for the
subsequent source plans and current storage checks.

## Task and review boundary

Implement clickable source scans for the dictionary’s explicit `D'Evreux,
Viagem` citations, starting with **so'o-Îurupari → printed page 293**. Do the
PDF processing, implementation, and browser verification in a local checkout,
then open an implementation PR for Kian to review. Also produce an inventory
of the dictionary’s other cited sources and the editions Navarro specifies,
so the remaining books can be planned after the pilot.

**Stop after delivering the D’Evreux implementation PR.** Kian wants to check
the page images, alignment, and viewer before authorizing the other books.
Do not merge or deploy the implementation, digitize Figueira or other sources,
or change dictionary definitions, morphology code, or corpus ground truth as
part of this task.

This document is the deliverable of the instructions PR. The implementation
steps below are work for the local agent; they are not changes delivered by
this documentation PR. Earlier research and an implementation reference are
preserved in [PR #23](https://github.com/kiansheik/nhe-enga/pull/23). Use its
individual files as optional reference material after review; do not merge
that PR or blindly cherry-pick its complete image-bearing commit.

### Prompt to give the local agent

> Read `AGENTS.md`, `CLAUDE.md`, and
> `docs/agent/session-handoffs/2026-10-06-devreux-primary-source.md`.
> Carry out the D’Evreux pilot described here in a new implementation branch:
> verify the exact scan, render the page images locally, implement citation
> links and source-viewer support, include the assets in the Pages build,
> and validate the actual dictionary-to-scan workflow. Produce the source
> inventory and open an implementation PR with review evidence. Stop for
> Kian’s review before merging, deploying, or implementing any other book.

## Repository starting points

Read the current code before editing. Research below used main commit
`f901e24d83511f8c53ebcc6d292d1012df24a2f3` on 2026-10-06; refresh findings if
the dictionary, bibliography, or viewer has since changed.

| Path | What to inspect or change |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | Repository rules; no morphology-engine changes are needed here. |
| `js/index.js` | `linkSources()` and the actual dictionary data URL. Extend the existing citation path. |
| `docs/dict-conjugated.json.gz` | The served Navarro dataset. Read definitions from `d`, lemmas from `f`, and preserve record identifiers/indices. |
| `docs/primary_sources/DTAbib.txt` | Navarro’s primary-source bibliography; the D’Evreux entry was line 26. |
| `docs/primary_sources/index.html` | Existing image viewer, `book_name` / `page_number` parameters, image-format handling, and navigation. |
| `scripts/build_pages.sh` | Explicit image-directory and asset copy lists. Adding a directory alone does not publish it. |
| `scripts/optimize_pages_images.py` | Existing deployment-copy JPEG optimization and `image-formats.json` generation. |
| `scripts/data/source_extraction.py` | Historical extraction code with rendering side effects; inspect it rather than running it as a read-only inventory. |
| `scripts/data/`, `tests/` | Locations for maintainable rendering/inventory tools and focused regressions. |

Work from current main in a separate implementation branch or worktree and
preserve existing local work. The repository contains a large scan collection;
use a sparse/partial checkout if helpful. The prototype’s new renderer,
inventory script, tests, and `evreux1929` directory are **not present on the
main baseline above**. Create or deliberately port them before using the
commands later in this task.

## Verified edition and scan

Navarro names **Yves d’Evreux, _Viagem ao Norte do Brasil_, translation by
César Augusto Marques, Rio de Janeiro, 1929**, collated with the 1864 French
edition annotated by Ferdinand Denis. The Portuguese edition’s pagination
is the target for these citations.

The 1929 title page calls the author **Ivo d’Evreux**. Its imprint includes
both **Freitas Bastos & Cia.** and **Livraria Leite Ribeiro** as depositários;
the series is _Bibliotheca de Escriptores Maranhenses_, II. Preserve the
digitization credit **Biblioteca Digital Curt Nimuendajú — Coleção Nicolai**.

Sources:

- [Curator’s catalog](https://www.etnolinguistica.org/biblio:evreux-1929-viagem)
- [Internet Archive item](https://archive.org/details/evreux-1929-viagem-ao-norte-do-brasil)
- [Exact PDF](https://archive.org/download/evreux-1929-viagem-ao-norte-do-brasil/Evreux_1929_ViagemAoNorteDoBrasil.pdf)
- Repository evidence: `docs/primary_sources/DTAbib.txt` and the PDF’s title
  leaf at zero-based index 3, plus the editorial note at printed p. 438.

| PDF property | Expected value |
| --- | --- |
| Filename | `Evreux_1929_ViagemAoNorteDoBrasil.pdf` |
| Bytes | `121180986` |
| PDF pages, including cover and final blank | `444` |
| SHA-256 | `1e6c7d93aa7e49f6cf76dd5ae84384e71ab40de592495f21b5708e4cdab61864` |

**Edition trap:** PDF page 8, index 7, reproduces an **1874** title page inside
the 1929 volume. The outer title and _Advertencia_ at printed p. 438 establish
the edition. Do not substitute a separately available 1874 scan, a modern
reprint, or the French edition without a new pagination investigation.

### Printed-page mapping

Use the source slug **`evreux1929`** and zero-based PDF image filenames.
For the numbered printed pages of this scan:

**printed page `p` → image `p.jpg` → PDF ordinal `p + 1`.**

| Content | Image / PDF index | PDF page, counting from 1 |
| --- | --- | ---: |
| Cover | `0.jpg` | 1 |
| Actual 1929 title page | `3.jpg` | 4 |
| Reproduced 1874 title page | `7.jpg` | 8 |
| First visibly numbered introduction page, 14 | `14.jpg` | 15 |
| Requested printed page, 293 | `293.jpg` | 294 |
| Final printed page, 442 | `442.jpg` | 443 |
| Final blank leaf | `443.jpg` | 444 |

Indices 1–13 include unnumbered preliminary leaves; label these as scan
positions/preliminaries rather than claiming that a printed number is visible.
The cover and final blank also need distinct labels. Valid scan navigation is
0–443; explicit printed-page citations in this edition are within 14–442.

Prior research checked all 42 currently cited page mappings: 36 exact OCR
header matches and visual inspection of exceptions **88, 129, 137, 143, 144,
157**. Page 144 has a corrected leading “1”; its neighbors 143 and 145 confirm
the position. Additional anchors at 14, 50, 100, 150, 200, 250, 300, 350, 400,
and 442 and the Archive page-number index support the sequence. This is not
a claim that every leaf of the volume was visually inspected.

Page 293 was read directly: it contains **Soo-Jeropary** and the nocturnal
animal passage behind the dictionary’s **so'o-Îurupari** definition. Recheck
this correspondence in the locally generated image and the optimized copy.

## Implementation sequence

### 1. Inventory citations from the served dataset

Read `docs/dict-conjugated.json.gz` as gzip JSON and inspect the actual record
structure. Do not use the similarly named `.json` interchangeably: both files
were gzip-encoded at the research baseline, but contained different snapshots.
The served file had 13,922 records; the first 13,712 precede the
`BIBLIOGRAFIA` heading. Exclude the bibliography from lexical-citation counts.

The decompressed baseline SHA-256 was
`8906cb4ddd292db7d67901ec9fb3c288d94b9baf9ae9cb35cb1d8a4a30e8e02e`.
Record the checksum used for the new inventory; if it differs, investigate
changed counts rather than forcing output to match this snapshot.

Build a repeatable inventory, with a readable report and machine-readable
records, of unique **author/work/edition combinations**, observed spelling
variants, locator syntax, bibliography references, current link coverage,
and unresolved cases. Preserve raw citation text, lemma/record index, and
definition offsets so a reviewer can trace each result. Some requested
subentries, including `so'o-Îurupari`, occur inside a parent record’s definition;
do not require an exact match against its `f` field or deduplicate repeated
citations within one record. Extract bibliography labels from line-initial
labels, including the unlabelled _Denunciações de Pernambuco_ entry. Handle nested
parentheses, semicolon-separated citations, and inherited numeric
continuations without double-counting. Keep grammar annotations, author
mentions in prose, host authors after `in`, and unresolved `op. cit.` cases
visible in an audit instead of silently treating them as resolved sources.

The earlier audit found **47 bibliography labels**, **59 named work families**,
and **10 unresolved work-label groups**. These are research/parser counts,
not proof that every edition or page system is identified. A regex producing
a link does not prove the target scan exists or is correctly aligned.

For D’Evreux, the baseline expectations are:

| Measure | Expected result |
| --- | ---: |
| Explicit `D'Evreux, Viagem` citations | 120 |
| Dictionary records containing those citations | 113 |
| Distinct printed pages | 42 |
| Page anchors when the range endpoints link separately | 121 |

The 42 cited printed pages are:

```text
73, 77, 82, 84, 86, 88, 124, 126, 129, 130, 131, 133, 135, 136,
137, 142, 143, 144, 145, 146, 147, 148, 151, 152, 156, 157, 158,
159, 161, 173, 181, 207, 215, 216, 244, 245, 246, 250, 252, 276,
293, 364
```

Save a D’Evreux citation CSV with raw text and resolved printed-page targets.
Specific cases: `tiá!` contains the spaced prefix `D' Evreux, Viagem, 143`;
`Marabá` contains `D'Evreux, Viagem, pp. 142-143`. `Caruaru` has the contextual
`Yves D'Evreux, (op. cit., p. 157)`: retain it as unresolved and exclude it
from the 120 explicit citations until its work reference is established.

### 2. Download, identify, and render the PDF locally

Download the PDF outside the repository and verify its checksum and page
count before generating assets. For example, run this from the repository
root, keeping the shell variable for the later rendering command:

```bash
DEVREUX_WORKDIR="$(mktemp -d)"
curl --fail --location --retry 3 \
  'https://archive.org/download/evreux-1929-viagem-ao-norte-do-brasil/Evreux_1929_ViagemAoNorteDoBrasil.pdf' \
  --output "$DEVREUX_WORKDIR/Evreux_1929_ViagemAoNorteDoBrasil.pdf"
python3 - "$DEVREUX_WORKDIR/Evreux_1929_ViagemAoNorteDoBrasil.pdf" <<'PY'
import hashlib
import pathlib
import sys

pdf_bytes = pathlib.Path(sys.argv[1]).read_bytes()
assert len(pdf_bytes) == 121180986, "Unexpected PDF byte count"
assert hashlib.sha256(pdf_bytes).hexdigest() == (
    "1e6c7d93aa7e49f6cf76dd5ae84384e71ab40de592495f21b5708e4cdab61864"
), "Unexpected PDF checksum: investigate the download before rendering"
print("Exact source PDF verified")
PY
```

Create a reproducible renderer in `scripts/data/render_source_pages.py`, using
PyMuPDF and Pillow in a local Python environment. Validate the checksum and
444-page count before writing. Support rendering the whole book and selected
zero-based indices. Render the **complete PDF page** in RGB at **120 dpi**,
then save progressive JPEGs at **quality 90**. The tested reference versions
were PyMuPDF 1.26.6 and Pillow 12.3.0; record the versions actually used.

The underlying scan is roughly 1200 × 1740 pixels. Do not describe it as
600 dpi based on Archive metadata or upscale it to suggest extra detail.
Extracting only embedded bitmaps omits visible attribution overlays present
on the title and final printed pages; full-page rendering preserves them.
Write each image to a temporary file and replace its final path atomically
so interrupted runs do not leave a zero-byte image looking complete.

Add **all 444 images**, `0.jpg` through `443.jpg`, in
`docs/primary_sources/evreux1929/`, allowing readers to browse neighboring
pages. Add `source.json` and a concise book README recording the edition,
translator, imprint, digitization credit, source URLs, retrieval date, PDF
checksum and page count, rendering settings, page mapping, anchors, and
verification limits. Keep the downloaded original PDF outside the Git tree.

A suitable renderer CLI, to implement or port before executing, is:

```bash
python3 scripts/data/render_source_pages.py \
  --pdf "$DEVREUX_WORKDIR/Evreux_1929_ViagemAoNorteDoBrasil.pdf" \
  --manifest docs/primary_sources/evreux1929/source.json
```

The prior render occupied about **259 MiB** in source JPEGs and **212 MiB**
after the existing deployment optimizer. These are comparison points, not
exact-byte requirements. Verify legibility of diacritics, small text, page
numbers, and the requested passage in the optimized images.

### 3. Extend citation linking

Update the existing `linkSources()` path in `js/index.js`. Explicit D’Evreux
Viagem references should open:

```text
/nhe-enga/docs/primary_sources/?book_name=evreux1929&page_number=293
```

Preserve the citation’s displayed wording, punctuation, spacing, and accents.
Cover straight/curly apostrophes, observed author spacing, optional `p.` /
`pp.`, page lists, and hyphen/en-dash/em-dash range separators. Link the two
visible range endpoints individually. Prevent duplicate anchors, accidental
matching inside unrelated markup, and treating an edition year as a page.
Reject out-of-range or malformed page references; do not silently clamp a
bad citation to an unrelated scan. Leave contextual `op. cit.` unresolved.

Keep existing Anchieta, Araújo, Bettendorff, Léry, and VLB mapping behavior
working. Do not broaden another author’s parser or repair its edition mapping
within this pilot; record any discovered issue in the inventory instead.

### 4. Add source-viewer support and include it in the build

Extend the existing viewer in `docs/primary_sources/index.html` with JPEG
support for `evreux1929`, edition/translator metadata, digitization credit,
catalog link, direct-image access, and the original PDF. For printed p. 293,
the PDF URL must end in **`#page=294`**. Keep scan indices and printed-page
labels distinct for preliminaries and the final blank.

Provide previous/next controls bounded to scan indices 0–443, a URL that
survives reload/back navigation, readable fit-to-window and native-size zoom,
and a clear image-load failure state. Fit the whole page below the controls
on desktop and mobile; wrapping metadata must not push its bottom offscreen.
Load only the requested image rather than preloading the entire book.

In `scripts/build_pages.sh`, add `docs/primary_sources/evreux1929` to the
explicit image-copy list and copy its `source.json`. Copy
`docs/primary_sources/DTAbib.txt` if the source metadata links to it: the
existing image-copy helper and optional CSS/HTML/JS/JSON list do not copy TXT
files or nested provenance automatically.

Run the existing image optimizer on a **build/staging copy**, leaving the
source rendering intact. Verify that the resulting `image-formats.json`
includes `evreux1929` with the JPEG extension and that the viewer works both
with the deployment manifest and in a plain local checkout where that
generated manifest may be absent. Do not change quality defaults for the
other books just to add this source.

### 5. Verify the implementation and prepare its PR

Add focused executable tests in `tests/primary_sources.test.cjs` (Node’s
built-in test runner is sufficient). Exercise the actual production linker
and viewer logic; a duplicated test-only parser cannot establish coverage.
At the baseline dataset, all 120 explicit citations must retain their visible
text and yield the expected 121 page targets across 42 pages.

Useful commands after adding the corresponding files:

```bash
node --test tests/primary_sources.test.cjs
python3 scripts/data/source_inventory.py
bash -n scripts/build_pages.sh
git diff --check
```

Validate the deployment asset path with `make pages-build` in a configured
local environment, or exercise its source-copy and optimization stages in
isolation if unrelated generated grammar/data assets prevent a full build.
The earlier prototype did **not** run the full VuePress/Pyodide rebuild; do
not inherit a claim that it passed. Report exactly what ran and any blocker.
Do not run `make deploy-gh-pages` as part of this review task.

For a checkout directory named `nhe-enga`, serve its parent from the repo root
so existing absolute `/nhe-enga/` links work:

```bash
python3 -m http.server 8000 --directory ..
```

Open [the requested entry locally](http://localhost:8000/nhe-enga/?query=so%27o-%C3%8Eurupari).
If the checkout has another directory name, serve it under an equivalent
`/nhe-enga/` prefix. Opening a bare `file://` page does not test the real fetch
and routing behavior.

### Acceptance checklist for the implementation PR

- [ ] Exact 1929 PDF checksum and 444-page count recorded; title/1874 caveat
  and digitization credit preserved.
- [ ] Complete `0.jpg`–`443.jpg` filename sequence; every source and optimized
  JPEG fully decodes and has nonzero dimensions. All current cited targets exist.
- [ ] All 42 baseline cited mappings checked against the downloaded scan,
  with visual checks for OCR exceptions and the page-293 passage. Any changed
  dataset counts explained rather than hidden.
- [ ] Real browser: click the `so'o-Îurupari` citation, see printed 293 and
  **Soo-Jeropary**, open PDF page 294, navigate next → reload → previous, and
  open the direct image.
- [ ] `Marabá` opens both 142 and 143; `tiá!` opens 143 with its spaced prefix;
  `Caruaru`’s contextual reference is not misrepresented as resolved.
- [ ] Cover/preliminaries/end labels, navigation bounds, malformed parameters,
  image failures, desktop/mobile fit, zoom, and legacy source links checked.
- [ ] Built assets include the JPEGs, source metadata, and linked bibliography;
  the optimized images remain readable and the format manifest resolves them.
- [ ] Reproducible source inventory and D’Evreux CSV committed; unresolved
  edition/locator cases documented. Dictionary data and morphology unchanged.
- [ ] PR includes edition evidence, mapping table, actual test/build results,
  image sizes, desktop/mobile screenshots, and a short click-through review
  guide. No merge, deployment, or implementation of subsequent books.

## Research references and the queue after review

The prototype is frozen at commit
`61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e`. Its files can save investigation
time, but must be reviewed against the current checkout before reuse:

- [Rendering script](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/scripts/data/render_source_pages.py)
- [Inventory script](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/scripts/data/source_inventory.py)
- [Inventory report](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/docs/primary_sources/source_inventory.md)
- [D’Evreux citation CSV](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/docs/primary_sources/devreux_citations.csv)
- [Source manifest](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/docs/primary_sources/evreux1929/source.json)
- [Focused tests](https://github.com/kiansheik/nhe-enga/blob/61cd1d0ccd34eb254e8576b3df5c24bc23f42d4e/tests/primary_sources.test.cjs)

Keep these known questions in the inventory for a later authorized pass:

- **Figueira, Arte:** Navarro lists Lisbon 1687 and Platzmann’s 1878 facsimile;
  some citation strings say 1686. Establish the edition and folio/page system
  before importing scans or adapting the Anchieta linker.
- **Araújo:** distinguish 1618/1952 from 1686/1898. Some older 1686 citations
  currently match the 1618 formatter; an existing anchor is not edition proof.
- **Anchieta and Léry:** keep distinct works and editions separate; do not
  treat all Anchieta citations as Arte or Léry’s 1580 references as 1578.
- **Thevet and other locator systems:** the edition for _Les Singularités_
  needs resolution beyond the bibliography’s _Cosmographie_ entry. Manuscript
  lines, folios, books/chapters, and plates require their own mapping rules;
  a single numeric page offset is not universally valid.

Once Kian approves the D’Evreux result and authorizes further books, repeat
the edition → scan → locator mapping → rendering → linking → review process
one source/edition at a time.
