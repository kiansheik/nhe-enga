# Anchieta Teatro manuscript facsimiles

## Goal

Place the matching manuscript witnesses beneath every currently linked
`Anch., Teatro` critical/translated page, using the higher-resolution
searchable Martins 1954 upload supplied by the user.

## Files inspected

- `docs/primary_sources/anchieta_teatro_1954.pdf`
- Internet Archive metadata, page images, and DjVu OCR for both Martins scans
- `docs/primary_sources/anchteatro1954/{README.md,source.json}`
- `docs/primary_sources/index.html`
- `scripts/data/{align_anchieta_teatro.py,render_source_pages.py}`
- `scripts/{build_pages.sh,build_offline.py,optimize_pages_images.py}`
- `tests/primary_sources.test.cjs`
- `tests/offline/test_catalog.py`

## Files changed

- `docs/primary_sources/anchteatro1954/source.json`
- `docs/primary_sources/anchteatro1954/README.md`
- `docs/primary_sources/anchteatro1954/745.jpg` (removed as unreferenced after
  correcting Navarro 1999 p. 16)
- `docs/primary_sources/anchteatro1954/diplomatic-*.jpg` (61 new pages)
- `docs/primary_sources/index.html`
- `scripts/data/fetch_anchieta_manuscripts.py`
- `tests/primary_sources.test.cjs`
- `docs/agent/{current-state.md,log.md,repo-map.md,served-assets.md}`
- This handoff

## Commands run

- Internet Archive metadata queries and representative page downloads
- OCR alignment and visual checks for São Lourenço and Guaraparim
- `.venv/bin/python scripts/data/fetch_anchieta_manuscripts.py`
- `node --test tests/primary_sources.test.cjs`
- `.venv/bin/python tests/offline/test_catalog.py`
- `node tests/offline/service_worker_smoke.cjs`
- Python compilation, JSON parsing, and Pillow decode/dimension checks
- Headless Chrome screenshots at 1440×1000 and 390×844
- `make pages-build`
- `.venv/bin/python scripts/check_pages_size.py .pages-build`

## What worked

- The newer Archive item serves 2927×3925/3926 page images, materially larger
  than the older 1307×1753 derivative.
- Every selected critical page has one or two explicit diplomatic witnesses.
  Two-page lists cover real folio transitions instead of pretending there is
  a constant offset.
- The viewer retains the critical page first, exposes **Ver manuscrito**, then
  displays complete diplomatic pages with their original line numbers, folio
  labels, and manuscript photographs. Each has a direct Archive link.
- Navarro 1999 p. 16 now opens index 746, whose line 172 contains
  `Nasatangatúi Maíra!`; diplomatic pages 151–152 appear below it.
- The artifact contains all 61 diplomatic pages, no raw PDF, and passes the
  900 MB repository budget at 854,834,862 bytes.

## What failed

- Python `urllib` rejected the local machine's TLS certificate chain. The
  reproducible fetcher uses `curl -fsSL --retry 3`, which validates and works.
- One source derivative is 3925 rather than 3926 pixels high. The fetcher now
  accepts the observed one-pixel range while requiring the exact width.
- Waiting for every lazy image before jumping to the manuscript timed out in
  browser QA. The corrected check waits for the critical page first, follows
  **Ver manuscrito**, then validates the lazy witnesses.

## Remaining questions

- Whether Farias-Sabiá prefers a different public name or a fuller
  digitization-credit statement.
- Whether a later enhancement should add hand-reviewed manuscript-only crops;
  complete diplomatic pages were chosen here to preserve documentary context
  and avoid unreliable automatic cropping.
- The branch is not committed, pushed, opened as a PR, merged, or deployed.

## Suggested next prompt

Review the local Teatro manuscript viewer at page 36 and page 16; if the
pairing and credit are acceptable, commit the branch, push it, and open a PR.
