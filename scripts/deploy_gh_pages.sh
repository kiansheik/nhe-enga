#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PAGES_BUILD_DIR:-$ROOT_DIR/.pages-build}"
WORKTREE="${GH_PAGES_WORKTREE:-$ROOT_DIR/.gh-pages-worktree}"
REMOTE="${REMOTE:-origin}"
BRANCH="${GH_PAGES_BRANCH:-gh-pages}"

"$ROOT_DIR/scripts/build_pages.sh"

if find "$BUILD_DIR" -type f -size +100M -print -quit | grep -q .; then
  echo "GitHub Pages artifact contains files larger than 100 MB:" >&2
  find "$BUILD_DIR" -type f -size +100M -print >&2
  exit 1
fi

is_git_worktree() {
  git -C "$1" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

if [[ -e "$WORKTREE" ]] && ! is_git_worktree "$WORKTREE"; then
  echo "$WORKTREE exists but is not a Git worktree" >&2
  exit 1
fi

if ! is_git_worktree "$WORKTREE"; then
  if git -C "$ROOT_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$ROOT_DIR" worktree add "$WORKTREE" "$BRANCH"
  else
    git -C "$ROOT_DIR" worktree add --detach "$WORKTREE"
    git -C "$WORKTREE" switch --orphan "$BRANCH"
    git -C "$WORKTREE" rm -rf . >/dev/null 2>&1 || true
  fi
else
  current_branch="$(git -C "$WORKTREE" symbolic-ref --quiet --short HEAD || true)"
  if [[ "$current_branch" != "$BRANCH" ]]; then
    git -C "$WORKTREE" switch "$BRANCH"
  fi
fi

find "$WORKTREE" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$BUILD_DIR/." "$WORKTREE/"

git -C "$WORKTREE" add -A
if git -C "$WORKTREE" diff --cached --quiet; then
  echo "No gh-pages changes to deploy."
  exit 0
fi

git -C "$WORKTREE" commit -m "Deploy static site"
git -C "$WORKTREE" push "$REMOTE" "$BRANCH"
