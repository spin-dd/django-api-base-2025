#!/usr/bin/env bash
set -euo pipefail

# Commit only the results of formatting. Fails if there are staged/unstaged changes.
# Usage: scripts/fmt-commit.sh

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a Git repository" >&2
  exit 1
fi

# Ensure working tree is clean before formatting
git update-index -q --refresh
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree not clean. Commit or stash non-format changes first." >&2
  exit 2
fi

root=$(git rev-parse --show-toplevel)
cd "$root"

# Prefer uvx ruff; fall back to ruff on PATH
run_ruff() {
  if command -v uvx >/dev/null 2>&1; then
    uvx ruff check --fix "$@"
    uvx ruff format "$@"
  else
    ruff check --fix "$@"
    ruff format "$@"
  fi
}

# Run formatter on the repo; scope can be narrowed if needed
run_ruff . || true

# Stage only files modified by formatter
changed=$(git ls-files -m)
if [ -z "$changed" ]; then
  echo "No formatting changes to commit."
  exit 0
fi

git add $changed
git commit -m "style: format via ruff (format-only commit)"
echo "Committed format-only changes." 

