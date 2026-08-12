#!/bin/bash
set -euo pipefail

# Populates ~/.claude/agents/ on a Claude Code cloud/web session, where the
# dcoe-roster plugin's own SessionStart hook never fires (a cloud session
# clones the target repo without installing the marketplace). Operations
# and Pappa T get the roster via that plugin hook instead — this script is a
# no-op there.
#
# Missing-only, same as bootstrap.mjs: never overwrites a locally-edited
# agent file, only fills in what's absent.
#
# Spec: docs/specs/2026-08-12-roster-cloud-sessions.md in tlelosa-claude-config.

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

EXPECTED_COUNT=10
AGENTS_DIR="$HOME/.claude/agents"

if [ -d "$AGENTS_DIR" ]; then
  ACTUAL_COUNT=$(find "$AGENTS_DIR" -maxdepth 1 -name '*.md' | wc -l)
  if [ "$ACTUAL_COUNT" -ge "$EXPECTED_COUNT" ]; then
    exit 0
  fi
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

if git clone --quiet --depth 1 https://github.com/tlelosa-web/tlelosa-claude-config.git "$TMPDIR/roster-source" >/dev/null 2>&1; then
  node "$TMPDIR/roster-source/agent-bodies-reference/bootstrap.mjs"
else
  echo "cloud-roster-bootstrap: could not clone tlelosa-claude-config — ~/.claude/agents/ not populated this session, delegations will fall back to Claude Code's built-in agents" >&2
fi
