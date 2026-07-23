#!/bin/bash
# SessionStart hook for Claude Code on the web.
# Installs project dependencies so tests and linters work in remote sessions.
#
# This repository currently has no dependency manifest, so there is nothing to
# install yet. When you add tooling (e.g. package.json, requirements.txt,
# pyproject.toml, go.mod, Cargo.toml), add the corresponding install step below.
# Keep steps idempotent and non-interactive.
set -euo pipefail

# Only run in the remote (Claude Code on the web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# --- Add dependency installation steps here, e.g.: ---
# npm install
# pip install -r requirements.txt

echo "session-start: no dependencies to install yet"
