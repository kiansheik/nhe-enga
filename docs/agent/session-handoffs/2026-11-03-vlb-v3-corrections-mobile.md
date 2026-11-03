# VLB V3 alignment, corrections, and mobile reader handoff

## Goal

Complete the interrupted VLB alignment work without changing the pinned
Navarro dictionary or Emerson transcription: recover any unpublished work if
possible, evaluate a frozen V3 matcher on fresh blind material, add a durable
human-reviewable correction path, build the source-to-dictionary reverse
inventory, integrate bounded candidates into the live static reader, and make
the review flow practical on phones. Commit and push reviewable milestones,
but do not merge or deploy them.

Recovery found the requested base at `b5df369af6a7d2db72f933746ca6b5c13a44310d`
on `feat/vlb-review-learning`, but no dangling commit or usable unpublished
session artifact containing the missing implementation. The work below was
therefore reconstructed from the frozen inputs and repository contracts rather
than described as recovered.

## Files inspected

- `docs/agent/index.md`, `current-state.md`, `repo-map.md`,
  `open-questions.md`, `grammar-navigation.md`, and the November 2–3 VLB
  handoffs
- `docs/dict-conjugated.json.gz`, `vlb/source/emerson_vlb.txt`, the pinned
  citation/page/OCR inputs, and the existing V1/V2 model freezes and reports
- `vlb/mining/pipeline.py`, benchmark fixtures, development evidence, candidate
  artifacts, and the sealed V3 review packet and annotations
- `vlb/app.js`, `vlb/index.html`, `vlb/styles.css`, `vlb/build_data.py`,
  `vlb/citation-targets.js`, and representative compressed page projections
- Existing VLB Python, Node, and real-browser tests, the Pages/offline builders,
  and `.github/workflows/dictionary-formatting.yml`

The blind annotator did not inspect rankings or mining output before sealing
the V3 labels; its narrower inspection boundary is recorded separately in
`2026-11-03-vlb-benchmark-v3-blind-annotation.md`.

## Files changed

- Added the correction contract and history under `vlb/corrections/`, the
  `vlb/manage_corrections.py` CLI, a GitHub issue form, and a manually
  dispatched workflow that validates issue content before opening a review PR.
- Added the V3 sample, freeze, evaluator, candidate artifacts, reports, and
  focused tests under `vlb/mining/benchmark-v3/` and `vlb/mining/output-v3/`.
  V1 and V2 artifacts remain frozen.
- Added a frozen pre-V3 reader-ranking comparison and a dynamic
  `vlb/evaluate_corrections.cjs` development-regression report. The former no
  longer reads mutable live data; the latter strips ledger overrides and calls
  the production target resolver.
- Added `vlb/build_reverse_concordance.py`,
  `vlb/mining/reverse_concordance.py`, and the checked-in offline reverse
  artifact/report.
- Updated `vlb/build_data.py` and all 279 `vlb/data/pages/*.json.gz` projections
  to carry bounded V3 candidates and validated correction decisions. Updated
  `vlb/data/manifest.json` with proposal, policy, ledger, and source hashes.
- Updated `vlb/app.js`, `vlb/citation-targets.js`, `vlb/index.html`, and
  `vlb/styles.css` for exact-span navigation, manual alternatives, structured
  corrections, and the responsive single-surface reader.
- Expanded the Python, Node, browser, deterministic-data, and workflow coverage;
  updated the VLB/mining/correction READMEs and the required agent documents.

## Commands run

- `python3 vlb/manage_corrections.py validate`
- `python3 vlb/mining/benchmark-v3/validate_fixture.py`
- `python3 vlb/mining/benchmark-v3/validate_annotations.py`
- `python3 vlb/mining/evaluate_v3.py`
- `node vlb/evaluate_corrections.cjs --check`
- `python3 vlb/build_reverse_concordance.py`
- `python3 vlb/build_data.py`
- `python3 -m unittest discover -s tests -p 'test_vlb_*.py' -v`
- `python3 tests/test_vlb_citation_inventory.py`
- `python3 tests/test_vlb_viewer_data.py`
- `node --test tests/vlb_dictionary_links.test.cjs tests/vlb_citation_targets.test.cjs tests/vlb_correction_regressions.test.cjs tests/dictionary_formatting.test.cjs`
- `node --check vlb/app.js` and `node --check vlb/citation-targets.js`
- `VLB_PLAYWRIGHT_MODULE=/Users/kian/code/pydicate-studio/node_modules/playwright VLB_CHROMIUM_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' VLB_QA_DIR=/tmp/vlb-final-qa3 node tests/vlb_viewer_browser.cjs`
- `PAGES_BUILD_DIR=/tmp/nhe-pages-vlb-final2 make pages-build` for a local
  artifact only; no deploy target was invoked
- `git diff --check`

## What worked

- The correction ledger strictly validates source/page/OCR identity, pinned
  hashes, exact global half-open spans, deterministic event IDs, monotonically
  chained revisions, and reviewer provenance. Import is idempotent and treats
  issue bodies as untrusted data. Eight first revisions validate: six accepted,
  one ambiguous, and one not found. They are assistant-reviewed, not
  human-verified; all eight are regression evidence and none is approved for
  training. Public issue imports must set both approval flags false, and the
  import PR includes regenerated reader data plus the checked regression report.
- The correction regression has 6/6 accepted top-one paragraphs, 6/6 top-one
  exact spans, and all 7/7 individual accepted spans among its alternatives.
  The live high-precision policy automatically targets 2/8 records, is exact
  on both, records zero false positives, and abstains on the ambiguous and
  not-found decisions. This is reused assistant-reviewed development evidence.
- The blind V3 packet excluded V1/V2 cases and correction/development sources
  and pages. Its hashes are `a64adf5225b2477773089c4b9543c1c92b070475d44c341831e3e2cfc0ba1d31`
  for the packet and `ab73a469e445b722a4f55479daf513731a13b1d7cb5a30ec7988439eff422685`
  for the 21-clear/3-ambiguous labels.
- On the 21 clear cases, the frozen ranker returns the right paragraph first in
  20, within three in all 21, the exact first span in 15, and an exact offered
  span in 19. The release-time automatic policy exposed one ambiguous false
  positive. The later prefix-hypothesis abstention gate yields 9/9 correct
  automatic paragraphs, 8/9 exact spans, and 3/3 ambiguous abstentions on the
  reused sample; these post-release numbers are development-only, not a second
  held-out evaluation.
- The reverse artifact covers all 7,534 lexicographic source records: 3,771
  candidate-linked, 2,949 ambiguous, 814 unmatched, and zero claimed fully
  covered. Its gzip SHA-256 is
  `62ef0dccae2c70e61bc65b4af8b7ca9adc304e9058d35385106cd6edd9baed51`.
- The reader projection retains 6,124 citation occurrences, 6,164 page
  memberships, 18,420 proposed associations, and seven reviewed exact spans.
  The compressed reader data is about 3.6 MB total, every page is below 20 KiB,
  and the 8+ MiB full candidate audit plus 1.4 MiB reverse artifact remain out
  of the website payload.
- Exact source marks, narrowed OCR, text-only accepted targets, manual target
  URL persistence, revision-chain submission, import/export, and continuous
  page cleanup have focused regressions. The fresh Chromium run reported every
  check true and zero JavaScript errors, including mobile viewports and
  correction geometry. Final evidence is under `/tmp/vlb-final-qa3/`; reviewed
  captures include `vlb-mobile-360-text.png`,
  `vlb-mobile-citation-scan.png`, `vlb-mobile-correction.png`, and
  `vlb-desktop.png`; `result.json` records the passing run.
  Before/after composites are `/tmp/vlb-mobile-comparison.png` and
  `/tmp/vlb-continuous-mobile-comparison.png`.
- Final broad checks passed 58 VLB Python tests, 29 focused Node tests, the
  two standalone citation-inventory tests, deterministic data/evaluation
  checks, and the real Chromium suite with every result flag true.
- The local Pages artifact contains the exact 288-file public VLB allowlist
  (apart from the expected offline-registration injection into HTML), excludes
  mining/reverse/ledger sources, and has 13 signed offline packs whose 2,763
  cataloged file sizes and hashes were all rechecked. Nothing was deployed.
- Milestone commits `d1eea0c4` (`Add durable VLB correction ledger`) and
  `5ce484c3` (`Freeze VLB V3 evaluation and reverse concordance`) were pushed to
  `origin/feat/vlb-review-learning` before the final reader integration.

## What failed

- No unpublished interrupted implementation could be recovered; rebuilding
  from the verified frozen V2 branch was necessary.
- Final audit initially exposed stale reverse provenance, a benchmark validator
  coupled to the mutable viewer manifest, correction-import PRs that omitted
  regenerated data, and exact marks lost on routed reload/mode changes. Each
  was repaired and given a regression. The first expanded Chromium run then
  found a stale mark retained on explicit continuous-page navigation; that
  cleanup path was fixed before the final passing run.
- The navigation policy present when blind V3 labels were released targeted
  one ambiguous prefix-hypothesis case. That failure is retained in the report
  rather than removed from the evaluation.
- The frozen ranker does not always choose the exact first span (15/21), and two
  clear cases lack an exact span even among offered alternatives. Automatic
  navigation therefore remains deliberately narrower than candidate display.
- OCR-line availability was validated, but exact scan-glyph box accuracy was
  not measured. OCR rectangles remain approximate line regions.
- Neither the V3 annotations nor the eight correction decisions have human
  editorial verification. No result should be described as programme,
  community, or human approval.

## Remaining questions

- A human editor should review the three ambiguous blind labels and all eight
  initial correction decisions, recording any decision as a new ledger
  revision rather than rewriting history.
- The reverse inventory still has 2,949 ambiguous and 814 unmatched records;
  candidate-linked does not mean semantically reviewed or paragraph-covered.
- Review the final pull request and CI results. Nothing in this session was
  merged or deployed; publication remains a separate, explicit action after
  review.

## Suggested next prompt

Review the VLB alignment pull request and its CI artifacts, then human-check the
three ambiguous blind labels and eight initial ledger decisions. Append any
editorial changes as new correction revisions; do not merge or deploy until
those review boundaries and the local mobile screenshots are accepted.
