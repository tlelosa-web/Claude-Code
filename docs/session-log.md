# Session Log

## 2026-05-21 - Project Reorganisation

- Domain classified as Software/AI.
- Checked project tree, git status, README, AGENTS.md, and docs/todo.md.
- Added DCOE support structure required by AGENTS.md.
- Preserved the current Flask app layout at the repository root to avoid breaking imports and runtime paths.
- Moved the SOPS product brief into `docs/specs/sops-product-spec.md`.
- Verified no CDN references in templates and no Google Fonts references in static assets.
- Fixed Windows console encoding risk in `app.py` by replacing Unicode status glyphs with ASCII output.
- Logged remaining pytest/import hang under `docs/bugs/pytest-flask-sqlalchemy-import-hang.md`.
