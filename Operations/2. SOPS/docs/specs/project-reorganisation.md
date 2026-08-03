## Task: Project Reorganisation To AGENTS.md
**Domain:** Software
**Goal:** Bring the repository structure in line with AGENTS.md while preserving the working Flask application layout.
**Inputs:** AGENTS.md, README.md, docs/todo.md, existing project tree, git status.
**Outputs:** DCOE support directories, executor manifests, documentation scaffolding, and an updated task queue.
**Constraints:** Do not break existing Flask imports, route paths, templates, static paths, or tests. Do not delete production files. Keep app code at the root unless a later approved migration spec moves it.
**Acceptance Criteria:** Required AGENTS.md directories exist; spec template exists; `.Codex/agents` contains the named executor manifests; docs folders have index files; todo reflects the reorganisation status; tests can be run or any failures are reported.
**Out of Scope:** Refactoring Flask modules, changing business logic, fixing failing feature tests, or committing changes.

