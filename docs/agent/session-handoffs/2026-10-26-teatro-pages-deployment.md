# Teatro and Castilho Pages deployment handoff

## Goal

Deploy the merged Anchieta Teatro and Castilho source work from current `main`
to GitHub Pages.

## Files inspected

- `Makefile`
- `scripts/deploy_gh_pages.sh`
- The merged PR #34 and current `main`/`gh-pages` revisions
- The live Teatro linker, manifest, and page-36 image

## Files changed

- `docs/agent/current-state.md`
- `docs/agent/log.md`
- This handoff

The deployment itself changed only the generated `gh-pages` branch.

## Commands run

- `gh pr view 34 --json ...`
- `git fetch origin`
- `git switch main`
- `git merge --ff-only origin/main`
- `make deploy-gh-pages`
- GitHub Pages build-status checks through `gh api`
- Live `curl` checks against `kiansheik.io`

## What worked

- PR #34 was already merged as `e78abbc8`; local `main` fast-forwarded cleanly.
- The maintained deployment pipeline optimized 2,300 source images from
  2,736.3 MiB to 744.2 MiB, generated 13 signed offline packs, built the
  grammar, committed `d8b48140`, and pushed `gh-pages`.
- GitHub Pages reported that exact commit `built` after 95.69 seconds.
- The live JavaScript contains both Castilho and expanded Teatro linkers. The
  live manifest has 75 images, maps Navarro 1999 page 36 to scan 757, and maps
  Navarro 2006 page 176 to scan 682. The live `757.jpg` returns HTTP 200.

## What failed

- The first live-domain check was denied by sandbox DNS restrictions. The
  approved network check succeeded immediately afterward.

## Remaining questions

- None for this deployment. Browser service-worker clients may need their
  normal catalog refresh cycle before adopting the new snapshot.

## Suggested next prompt

“Spot-check the live `îambé` and one explicit 2006 Teatro citation in a normal
browser, including navigation between adjacent mapped citations.”
