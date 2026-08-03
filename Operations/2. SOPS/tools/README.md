# Software / AI Tooling Domain

This repository currently hosts SOPS, a Flask-based operations tool, at the project root.

The app remains at the root for now because `app.py`, `models.py`, `routes/`, `services/`, `templates/`, `static/`, and `tests/` are already wired together in that layout. A future migration into `tools/` should start with an approved spec and update imports, tests, docs, and runtime commands together.

