# ADR-001: Vacancy & Profile Store Format

**Status:** Accepted — documents the convention already established and built in Phases 2–3 (Build Queue steps 10–21); filed retroactively per `docs/todo.md`'s Phase 3.5 note.
**Date:** 2026-07-21
**Decider:** Tebello Lelosa
**Related:** Mirrors the *pattern* of `ai-outreach-agency`'s ADR-001 (lead store). ADR-003 (inference provider split) later confirms `generation_log` and the review `approvals` table also live in this same database.

## Context

The Career Engine pipeline needs a central data store for the candidate profile, fetched vacancies, generation events, and human review decisions. Every pipeline stage (profile import, vacancy fetch, AI matching, document generation, human review) reads from and writes to this store. Options considered, mirroring the sibling project's ADR-001:

- **A. A remote/hosted store** (e.g. a spreadsheet or cloud DB) — visible and shareable, but network-dependent and weak on schema/constraints.
- **B. SQLite only** — offline-first, proper schema with `CHECK`/`FOREIGN KEY` constraints, fast, no rate limits, no external dependency.
- **C. Hybrid** — SQLite as source of truth with a sync layer to something else.

## Decision

**SQLite (`career.db`) is the pipeline's single source of truth**, for every table the pipeline owns:

- `candidate_profile` (Phase 2, `src/profile/db.py`)
- `vacancies` (Phase 3, `src/vacancy_search/db.py`)
- `generation_log` (Phase 5, `src/doc_gen/db.py`, added by ADR-003 §4)
- `approvals` (Phase 6, `src/review/db.py`)

All four tables live in the same `career.db` file — there is no per-module database file and no external store. This was already the operating assumption behind every `db.py` module built so far (each defaults to `Path(__file__).parent.parent.parent / "career.db"`); this ADR makes it explicit.

**Established `db.py` convention** (confirmed across `profile/`, `vacancy_search/`, `doc_gen/`, `review/`):

- Each module exposes `init_db(db_path: Optional[Path] = None) -> sqlite3.Connection`, defaulting to the shared `career.db` path, setting `row_factory = sqlite3.Row` and `PRAGMA journal_mode=WAL`, then creating its own table(s) via an idempotent `CREATE TABLE IF NOT EXISTS` and calling `apply_migrations(conn)`.
- A table's **baseline** shape is that inline `CREATE TABLE IF NOT EXISTS` — the tracked, reviewable record of its initial shape. **Every change after baseline** goes through that module's own `migrations.py` (`MIGRATIONS: list[tuple[int, str]] = []` + `apply_migrations()`, applied via `PRAGMA user_version`). This satisfies the "no schema changes without a migration file" hard rule in the form this project actually uses — there is no standalone `migrations/*.sql` file convention here.
- Vacancy status is an enforced state machine (`VALID_TRANSITIONS` in `vacancy_search/db.py`): `new → scored → asset_ready → {approved, rejected}`. No stage may skip ahead; `update_vacancy_status()` raises `ValueError` on an invalid transition.

There is no live external API (Google Sheets, a hosted dashboard, etc.) as a data layer anywhere in this pipeline. Vacancies enter the system through the Apify-backed `fetch_vacancies()` (see ADR-002); the candidate profile enters through `data/profile_seed.json` (Phase 2).

## Consequences

- All pipeline modules read/write the same local SQLite file — no cross-service sync logic, no OAuth for the data layer itself.
- The pipeline works fully offline for every stage except vacancy fetch (Apify), AI matching (local Ollama), and document generation (headless Claude Code) — each gated by its own `OFFLINE_MODE` branch, independent of the storage decision here.
- If a visual dashboard is ever wanted (tracking applications, match-score distribution — see `docs/todo.md`'s "Future" section), it is a read-only SQLite viewer built on top of this store, not a reason to introduce a second source of truth.
- `PRAGMA user_version` is shared per-file across all four modules' `migrations.py` scripts. Because each module's `MIGRATIONS` list is independently numbered from 1, two modules adding a migration at the same version number in parallel could silently collide (the second one to run would see `current >= its own version` and skip). Not a problem yet — `vacancy_search/migrations.py` is the only module with entries (versions 1–4) as of this ADR — but flagged here as a sizing judgment for the Planner if a second module ever needs a real migration: either keep versions globally coordinated across modules by convention, or move to a per-module `user_version`-equivalent (e.g. a `schema_migrations` tracking table keyed by module name) if a collision is ever hit in practice.
