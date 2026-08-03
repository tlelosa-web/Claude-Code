# 0001 - Keep Flask App At Repository Root

## Status

Accepted

## Context

AGENTS.md defines domain folders such as `tools/`, `engineering/`, and `trading/`. The current SOPS application already uses a flat Flask layout with `app.py`, `models.py`, `routes/`, `services/`, `templates/`, `static/`, and `tests/` at the repository root.

## Decision

Keep the SOPS Flask application at the repository root during this reorganisation.

## Consequences

- Existing imports, templates, static asset paths, test discovery, and `python app.py` remain stable.
- `tools/` is reserved for future software/AI tooling or a later approved migration.
- Any future move into `tools/sops/` must be handled as a separate implementation task with its own spec, import updates, and verification pass.

