# VLB reader integration handoff

## Goal and base

Expose Emerson Costa's VLB transcription beside the existing scans at
`/nhe-enga/vlb/`, link it from the main navigation, and connect Navarro citations
to their printed pages and source-entry association records. The work started
from `1d36bc8ebbb72806c6d6bd1773669481d5b910fd` in a shallow, sparse checkout.

## Integration decisions

- `index.html` adds the VLB link beside the grammar navigation.
- `js/index.js` keeps `dictionary_index` when mapping the compressed dictionary.
  The citation linker passes that snapshot row as `entry`, including records
  without a legacy `i` field. It does not manufacture a citation ID from
  formatted HTML or imply a reviewed source association.
- The canonical route is `/nhe-enga/vlb/?volume=I&page=17&entry=<row>`.
  VLB lists, ranges, inherited volumes and the source's VBL spelling preserve
  their exact displayed wording. Invalid or absent page numbers remain text.
- `scripts/build_pages.sh` includes the VLB HTML/CSS/JavaScript, `vlb/data/`,
  and linked PDF provenance in the explicit static allowlist. Rebuild scripts
  and compact intermediate inputs stay on the source branch.
  `scripts/build_offline.py` includes its reader/data assets in the core pack;
  original scan images retain the existing `source-vlb` pack.
- The source checkout uses `docs/primary_sources/vlb/<scan>.png`. The current
  Pages optimizer emits JPEGs and writes `image-formats.json`; the reader must
  honor this manifest, including WebP declarations, and default to PNG for
  source checkouts. Existing scan-only viewer URLs remain valid.

## Data and interpretation

The served dictionary remains unchanged. Its SHA256 is
`d235a7961961b58fcfbb93362bc3acb9b7f7b7e823196dca5763ef3e7fd16f53`.
The source data retains the transcription's original text and UTF-16 offsets,
279 lexical page alignments and boundary uncertainty. Scan positions 25 and 26
contain an unnumbered manuscript plate and its blank verso; neither represents
missing transcription or a numbered printed page.

The citation inventory contains **6,124 occurrences**, of which **6,122** have
all cited pages linked, yielding **6,164 individual page links** across **277**
cited pages. Page-level availability is independent of candidate quality.
The `aeté` citation `VLB, I, 1390` and `hegûy` citation `VLB, I` remain unresolved.
Source-entry suggestions retain their review status; pagination does not prove
lexical equivalence.

The older source audit missed `II, 109, adapt.` after `VLB, I, 34` in
`nhe'ẽporangaíba` (row 7915). The inherited-locator parser now accepts its
adaptation suffix while preserving the original offsets and text. The source
inventory also recognizes the new VLB route and can still execute the production
linker with no dictionary-row argument.

`vlb/build_data.py` regenerates the compact reader projection from pinned
`vlb/source/` inputs. It does not refetch or change the shared Google Doc.

## Verification performed

- `node --test tests/vlb_dictionary_links.test.cjs tests/dictionary_formatting.test.cjs tests/dictionary_apostrophes.test.cjs`
- `python tests/test_vlb_citation_inventory.py`
- `python tests/test_vlb_viewer_data.py` (four tests passed)
- `node --test --test-name-pattern='existing source URLs' tests/primary_sources.test.cjs`
- `bash -n scripts/build_pages.sh`

These verify exact token preservation across the served dictionary, all 6,164
valid VLB links and their snapshot-row query, the recovered inherited adapted
citation, independent legacy scan URLs, and the image-format manifest fallback.
The focused checks passed. The existing dictionary-formatting CI also runs
`tests/test_vlb_viewer_data.py` and `tests/vlb_viewer_browser.cjs`. It checks out
`vlb/` and the seven original scan fixtures at positions 17, 25, 26, 161, 232,
292 and 303. Python and Node Playwright are both pinned to 1.55.0 and reuse
one Chromium installation. The workflow retains the VLB screenshots and
`result.json` as the `vlb-browser-qa` artifact.

The reader's local Chromium run returned `true` for every reported functional
check and an empty JavaScript-error array in `vlb_viewer_qa/result.json` outside
the repository. It covered desktop/mobile layouts, OCR highlighting and zoom,
citation deep links without silently accepting proposed associations,
review-note export and persistence, the unnumbered scan inserts, the volume-II
scan offset, split paragraphs and their search/deep-link navigation, and the
optimized image-format manifest. The browser suite starts its own local server;
run it with `node tests/vlb_viewer_browser.cjs` after installing Playwright and
Chromium, or set `VLB_CHROMIUM_PATH` to an existing browser executable.

The full Pages/grammar build requires the complete source assets and existing
local generator inputs; it was not run from this deliberately sparse checkout.
The final source-data manifest is retained with the reader data. No production
deployment was performed here.

## Continuing the work

Review the VLB branch, inspect explicit and proposed associations in the viewer,
and use the persisted source/citation IDs when recording further editorial
decisions. Keep reviewed associations separate from retrieval suggestions.
Regenerate `vlb/data/` after changing its pinned compact inputs. Deploy through
the existing Pages pipeline only after the branch is reviewed and merged.
