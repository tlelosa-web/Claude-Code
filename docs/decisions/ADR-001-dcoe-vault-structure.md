# ADR-001: DCOE Vault Structure

## Status

Accepted.

## Decision

Use `AGENTS.md` as the canonical project brain and `.Codex/agents/` as the active agent roster for this vault.

## Context

The workspace had a Claude-oriented project brain with encoding damage and a cleaner Codex-oriented `AGENTS.md` containing the same DCOE architecture.

## Consequences

- Other assistant-specific files should point back to `AGENTS.md`.
- DCOE state lives in `docs/domain-brief.md`, `docs/todo.md`, and `docs/session-log.md`.
- Project-specific context stays in the relevant project folder, especially `TebelloReborn/`.
