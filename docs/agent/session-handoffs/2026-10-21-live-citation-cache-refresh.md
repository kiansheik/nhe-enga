# Live citation cache-refresh handoff

## Goal

Make the corrected Araújo 1686 citation target appear on ordinary production
navigations even when the browser previously saved the site's older offline
core, without weakening offline integrity or per-document release coherence.

## Files inspected

- `docs/agent/{index,current-state,repo-map,open-questions,log}.md`
- `js/index.js`
- `offline/{sw.js,register.js,README.md}`
- `scripts/{build_offline.py,build_pages.sh,deploy_gh_pages.sh}`
- `tests/offline/{service_worker_smoke.cjs,browser_smoke.py,test_catalog.py}`
- The deployed `js/index.js` and `offline/catalog.json`
- The exact production dictionary query in real Chrome

## Files changed

- `offline/sw.js`
- `tests/offline/service_worker_smoke.cjs`
- `tests/offline/browser_smoke.py`
- `docs/agent/current-state.md`
- `docs/agent/log.md`
- This handoff

## Commands run

- SHA-256 comparison of local and deployed `js/index.js`
- Exact production-query inspection in real Chrome
- `node tests/offline/service_worker_smoke.cjs`
- `make offline-test`
- `make offline-browser-test`
- `git diff --check`

## What worked

- The live origin's `js/index.js` exactly matched the corrected local file, and
  a clean browser rendered `book_name=arcat1686&page_number=241` for the user's
  exact query. This isolated the stale result to the offline cache layer.
- A new document now revalidates the signed catalog without using the browser's
  HTTP cache, pins that catalog for its subresources, and considers its current
  file hashes before older installed/saved hashes.
- If the latest manifest or file is unavailable or corrupt, lookup continues
  to the older verified copies. Already-open clients retain their prior pinned
  catalog.
- The protocol test covers fresh-navigation activation and old-client pinning.
  Real Chromium covers online stale-catalog activation, cold offline use,
  selective source packs, coherent updates, corruption fallback, saved-source
  removal, and the Android install surface.

## What failed

- The first real-browser run was blocked by sandbox restrictions on binding a
  localhost port; rerunning the same test with the required permission passed.
- An intermediate browser fixture used the already rewritten `v2` string as if
  it still contained `v1`, so its synthetic `v3` build did not actually change
  the core hash. Correcting the fixture replacement made the intended browser
  regression pass.

## Publication

Pending source push, Pages deployment, and a final uncached production-browser
check of the exact reported query.

## Remaining questions

- Browsers still need to install the changed service-worker script once. After
  that update, subsequent navigations revalidate the catalog immediately; an
  already-open pre-update tab may require one reload.

## Suggested next prompt

“Verify that a previously offline-enabled browser receives a new dictionary
deployment on its next navigation while an already-open page stays pinned.”
