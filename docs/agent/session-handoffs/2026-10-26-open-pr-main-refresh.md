# Open PR main refresh

## Goal

Merge current `origin/main` into every open pull-request branch, resolve any
conflicts without replacing newer source work, run focused checks, and push the
updated branches for review.

## Files inspected

- Open PR metadata and branch ancestry for PRs #26, #32, and #33.
- `js/index.js`, `docs/primary_sources/index.html`, source manifests, Pages and
  offline build scripts, source tests, and agent documentation.
- The older Figueira/Castilho implementation on PR #26 and the newer Figueira
  implementation already present on `main`.

## Files changed

- PR #33: merge commit only; no conflicts.
- PR #32: merge commit only; no conflicts.
- PR #26: conflict resolutions retain the current `main` implementations and
  add its unique Castilho manifest, 16 page crops, citation linking, explicit
  viewer map, crop renderer support, build integration, tests, and provenance.
- PR #33 merged while the refresh was in progress. PR #26 was refreshed a
  second time so its tests retain both the newly merged Figueira Wikisource
  snapshot coverage and the branch's Castilho coverage.
- PR #32 then merged while the second refresh was in progress. PR #26 was
  refreshed once more, retaining both documentation histories and combining
  the formatter implementation with its independent Castilho citation rules.
- Updated `docs/agent/current-state.md`, `docs/agent/log.md`,
  `docs/agent/repo-map.md`, and `docs/agent/served-assets.md` for the resolved
  Castilho scope.

## Commands run

- `git fetch origin`
- `gh pr list` and targeted `gh pr view` / `gh pr checks`
- `git merge --no-edit origin/main` on all three open PR branches
- `node --test tests/primary_sources.test.cjs`
- `node --test tests/dictionary_formatting.test.cjs tests/primary_sources.test.cjs tests/dictionary_apostrophes.test.cjs`
- `.venv/bin/python tests/dictionary_formatting_browser.py`
- `(cd tests/offline && ../../.venv/bin/python -m unittest test_catalog.py)`
- `.venv/bin/python -m unittest tests.test_pages_size`
- Focused Python compilation and an in-memory crop-render smoke check.

## What worked

- PRs #32 and #33 accepted the initial current `main` without conflicts and
  their focused test suites passed before push; PR #33 then merged.
- PR #26's obsolete Figueira overlap could be resolved in favor of `main`
  while retaining the distinct Castilho work.

## What failed

- The formatting browser test could not bind its local test server inside the
  restricted sandbox; rerunning it with the permitted local-browser execution
  path passed all 53 checks.
- Running the offline unittest by its root-relative module path could not import
  its sibling `fixture`; running it from `tests/offline` passed all 11 checks.

## Remaining questions

- PR #26 still needs human review of its source-plan scope and Castilho
  provenance before merge. PRs #32 and #33 are merged.
- The broader Anchieta Teatro mapping remains separate work; current `main`
  intentionally links only the nine verified unsuffixed page-176 citations.

## Suggested next prompt

Review PR #26, merge the desired changes, then ask for a fresh
inventory of unlinked source citations or a broader Anchieta Teatro mapping.
