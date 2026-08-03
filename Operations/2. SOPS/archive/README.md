# Archive

Superseded or orphaned files kept for reference instead of deleted outright.
Nothing here is imported or run by the live app — if you're looking for
current source, it's at the repository root (`app.py`, `models.py`,
`routes/`, `services/`, `templates/`).

## `pre-adr-sops-package/`

An early `sops/` package scaffold (`__init__.py`, `app.py`, `config.py`,
`models.py`, dated 2026-06-12) that duplicated the app factory, config, and
models under a `sops/` namespace. Superseded by
[`docs/decisions/0001-keep-flask-app-at-root.md`](../docs/decisions/0001-keep-flask-app-at-root.md),
which decided to keep the Flask app flat at the repo root. Nothing in the
live app imports from `sops.*`. Includes `instance/sops.db` — a 53KB SQLite
file left behind from a test run of this abandoned package; disconnected
from the real `instance/sops.db` at repo root and not the production
database.

## `2026-06-debug-scripts/`

One-off ad-hoc debugging scripts from the 2026-06-17 "Works Pack Debug
Session" (`check_db_state.py`, `check_so_lines.py`, `find_item.py`,
`fix_bom_line.py`, `test_render.py`) plus `quick_update_items.py`, which
imported from the dead `sops` package above and was non-functional as a
result. Sibling files from the same session (`test_build_bom_post.py`,
`test_build_bom_with_correct_ids.py`) were already removed in commit
`f54d4e9` (2026-06-24) — these were missed at the time.

## `logs-2026-05-to-07/`

Historical `python app.py` stdout/stderr captures (2026-05 through
2026-07) that had been committed to git instead of gitignored. `logs/` is
now gitignored going forward (see root `.gitignore`) so run output stops
accumulating in version control. One of these
(`startup.err.log`) contains a traceback referencing the project's old
folder name (`3. Works Order & B.O.M`, pre-rename) — harmless since it's
just historical log text, not something the app reads.

## Also removed in this cleanup (not archived — confirmed pure duplicates/empty)

- `sops.db` (repo root) — 0-byte stub, already flagged stale in
  `docs/bugs/health-screen-2026-06-24.md` and never cleaned up. The real
  database is `instance/sops.db`.
- `startup_test.log` (repo root) — 0 bytes, superseded by `logs/`.
- `FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf` (repo root) — byte-identical
  duplicate of `data/FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf`, the
  canonical location referenced by README and tests.

## `AGENT_build_bom_works_pack.md` (removed, not archived)

The original v1.0 (2026-06-12) spec for the Build BOM / Works Pack feature.
Deleted rather than archived because it's fully superseded and its
learnings are already captured in current, actively-maintained docs:
- Multi-fan-line support (the doc's core "only one Fan line" assumption is
  gone) — see [`docs/specs/multi-fan-build-bom.md`](../docs/specs/multi-fan-build-bom.md)
  and `docs/session-log.md` (2026-07-01 entry).
- Per-line job numbers (a concept this doc never had) — see
  [`docs/specs/sales-order-job-numbers.md`](../docs/specs/sales-order-job-numbers.md)
  and `docs/session-log.md` (2026-07-06, Batch 11).
- It also described a `sops/` package layout (`sops/routes/`, `sops/models.py`)
  that never matched the real repo structure — see `pre-adr-sops-package/`
  above.

Still recoverable via git history (`git log --all --full-history -- AGENT_build_bom_works_pack.md`)
if ever needed.
