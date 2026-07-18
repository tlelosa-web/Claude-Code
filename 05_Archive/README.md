# 05_Archive

Purpose: store inactive, superseded, or “parked” materials so the active vault stays clean while nothing important is lost.

## What goes in here
- Old versions of documents (e.g., prior CVs, drafts, exports).
- Completed project snapshots you want to keep for reference but not actively edit.
- One-off experiments/prototypes that are not currently maintained.
- Logs, debug outputs, and generated artifacts that you don’t need day-to-day (unless another project explicitly treats them as “live reports”).

## What should NOT go in here
- Current “source of truth” documents you actively maintain.
- Current scripts that run your pipelines.
- Current “live reports” folders for active projects.
- Secrets/credentials (keep those in env/config patterns, never in plaintext files).

## Naming convention (recommended)
Use a date prefix so the archive stays sortable:
- `YYYY-MM-DD__<topic>__<short-note>/`
  - Example: `2026-06-03__cv__pre-rewrite/`

For single files:
- `YYYY-MM-DD__<topic>__<filename>`

## Minimal workflow
1. Copy the item into `05_Archive/`.
2. If you moved it from somewhere active, leave a short pointer note in the original location (or in `docs/session-log.md`) stating where it went and why.

