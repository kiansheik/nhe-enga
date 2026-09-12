# Gh-Pages Deployment Recovery

## Goal

Recover the repeatedly failing GitHub Pages push, publish the optimized artifact from `gh-pages`, and verify the live site.

## Files Inspected

- `Makefile`
- `scripts/build_pages.sh`
- `scripts/deploy_gh_pages.sh`
- `.pages-build`
- `.gh-pages-worktree`
- Local and remote `gh-pages` refs and commit trees
- GitHub Pages repository configuration and build status
- Live root, grammar, and image-manifest URLs

## Files Changed

- `docs/agent/current-state.md`
- `docs/agent/log.md`
- `docs/agent/session-handoffs/2026-09-12-gh-pages-deployment-recovery.md`

Remote state changed as authorized: `gh-pages` was created, GitHub Pages was switched from `main:/` to `gh-pages:/`, and a Pages build was queued.

## Commands Run

- Git status, branch, ref, parent, tree-size, and worktree checks
- `git fetch origin --prune`
- `git branch gh-pages-oversized-backup-20260912 7a50960c...`
- `git commit-tree a5e275a1... -m "Deploy static site"`
- Atomic `git update-ref` from `7a50960c...` to parentless commit `ff3b1f5b...`
- `git push -u origin gh-pages`
- GitHub API checks and Pages source update/build request
- Live HTTP checks for the root, grammar route, and generated image manifest

## What Worked

- Preserved both failed local deployment commits under `gh-pages-oversized-backup-20260912`.
- Reused the exact validated optimized tree while removing the unreachable 4.1 GB ancestor from the published branch.
- Pushed 1,582 objects in a 449.10 MiB pack; GitHub accepted the new `gh-pages` branch.
- Confirmed local, remote-tracking, and fetched remote refs all resolve to `ff3b1f5b2b76c276335f1bbd351dfe8e937d2a27`.
- Confirmed GitHub Pages is configured for `gh-pages:/` and built that exact commit successfully.
- Confirmed the live root and `/gramatica/` return HTTP 200 with the new deployment timestamp.
- Confirmed the live image manifest reports 1,407 JPEGs reduced from 2,481,418,431 bytes to 449,476,728 bytes.

## What Failed

- The user's initial deploy attempt pushed a child of the oversized failed root. GitHub rejected the resulting pack with `pack exceeds maximum allowed size (2.00 GiB)`.
- The live site initially remained on the old build because GitHub Pages was configured for `main:/`; switching the source after the branch push did not enqueue a new build automatically, so a build was requested explicitly.

## Remaining Questions

- Should `scripts/deploy_gh_pages.sh` automatically replace unpublished local-only Pages history with a fresh root snapshot after a failed first deployment?
- Once the backup is no longer useful, should `gh-pages-oversized-backup-20260912` be deleted locally and unreachable Git objects pruned to reclaim disk space?

## Suggested Next Prompt

Harden the first-time `gh-pages` deployment path so a corrected artifact cannot retain an earlier rejected oversized commit.
