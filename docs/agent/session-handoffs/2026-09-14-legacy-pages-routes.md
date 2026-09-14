# Legacy Pages Route Recovery

## Goal

Restore the broken Anchieta transcription URL, audit comparable tracked HTML pages, and prevent the optimized Pages builder from dropping them again.

## Files Inspected

- `scripts/build_pages.sh`
- All tracked `*.html` paths
- `.pages-build`
- `.gh-pages-worktree`
- `docs/primary_sources/emerson_arte_anchieta.html`
- `tupi/editirreg.html`
- `gramatica/docs/src/.vuepress/public/iframe_pyodide.html`
- `docs/agent/served-assets.md`
- GitHub Pages build status and the three live compatibility URLs

## Files Changed

- `scripts/build_pages.sh`
- `docs/agent/current-state.md`
- `docs/agent/log.md`
- `docs/agent/served-assets.md`
- `docs/agent/session-handoffs/2026-09-14-legacy-pages-routes.md`
- The `gh-pages` artifact gained the three missing legacy HTML files in commit `8fbaf447`.

## Commands Run

- Tracked-HTML versus `.pages-build` path audit
- Targeted source/reference searches with `rg`
- `bash -n scripts/build_pages.sh`
- `git diff --check`
- `make pages-build`
- Artifact size, file-size, excluded-format, and SHA-256 checks
- `make lint`
- Targeted `gh-pages` add, commit, and push
- GitHub Pages build-status checks
- Live HTTPS status and content checks

## What Worked

- Identified all three tracked HTML paths omitted by the allowlisted build.
- Made the Anchieta page required, included current and future top-level primary-source HTML sidecars, and retained two other legacy routes explicitly.
- Confirmed every tracked HTML path now exists in the 478 MB local Pages artifact.
- Preserved the exclusion of raw PDFs, EPUBs, MOBIs, OPFs, TXT files, and extraction scripts; no artifact file exceeds 100 MB.
- Published only the compatibility files rather than the unrelated uncommitted root-reorganization changes.
- Confirmed Pages successfully built commit `8fbaf447`; all restored URLs return HTTP 200.

## What Failed

- Before the fix, the live Anchieta URL returned GitHub's HTTP 404 page because `scripts/build_pages.sh` copied its JSON companion but omitted the HTML document.
- One piped title check ended with curl code 56 when `rg -m1` closed the pipe after finding the title; the title and independent full-response HTTP checks succeeded.

## Remaining Questions

- The durable source-builder fix is intentionally still part of the existing uncommitted main-worktree cleanup and needs to be included when that cleanup is reviewed and committed.
- Decide later whether the old Pyodide source-path alias should remain indefinitely or become a redirect; it currently remains for backward compatibility.

## Suggested Next Prompt

Review the complete uncommitted main-branch cleanup, including the Pages legacy-route guard, and prepare it for a focused commit without changing the deployed artifact.
