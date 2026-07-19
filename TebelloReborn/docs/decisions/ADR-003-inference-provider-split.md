# ADR-003: Inference Provider Split — Drop OpenRouter, Route by Workload Shape

**Status:** Accepted — decision confirmed by Tebello (2026-07-19), before any Phase 4 / Phase 5 code exists. Build is the Planner's to sequence.
**Date:** 2026-07-19
**Decider:** Tebello Lelosa
**Author:** Architect (Opus, escalation tier — cross-cutting inference-backend change + schema addition)
**Related:** ADR-001 (SQLite is the single source of truth — documented in `CLAUDE.md`, ADR file itself queued as Build step 22), ADR-002 (Apify job scraping). Mirrors the *pattern* — not the code — of two sibling `ai-outreach-agency` decisions: ADR-004 (`research` → local Ollama) and its ADR-003 (`asset_gen` → headless Claude Code).

## Context

TebelloReborn's MVP plan (`docs/specs/mvp-pipeline-build.md`, `docs/todo.md` Build Queue) has two remaining planned OpenRouter call sites, **neither of which is built yet**:

- **AI Matching** — `src/matching/scorer.py` (Build Queue Phase 4, steps 24–28). Scores a candidate profile against a vacancy. A structured, low-stakes scoring/classification pass.
- **Document Generation** — `src/doc_gen/cv_generator.py` + `src/doc_gen/cover_letter_generator.py` (Build Queue Phase 5, steps 29–35). Produces a tailored CV and cover letter that a real human will review and submit. Client-facing, quality-sensitive generated content.

The whole project currently carries a Known Issue: `OPENROUTER_API_KEY` is out of credits (HTTP 402, shared blocker with `ai-outreach-agency`). Because no matching or doc-gen code exists yet, this is the ideal moment to change the backend decision — no call site has to be *migrated*, only *not written the OpenRouter way in the first place*.

The sibling `ai-outreach-agency` project already made exactly this move, and TebelloReborn's own `CLAUDE.md` states it "deliberately mirrors" that project's architecture and reuses working patterns rather than reinventing them. `ai-outreach` split its own two OpenRouter call sites by workload shape:

- The cheap, structured `research` summariser moved to a **local Ollama** daemon (`qwen3:8b`, native `/api/generate`, no API key) — ADR-004 there.
- The quality-sensitive, client-facing `asset_gen` moved to **headless Claude Code** (`claude -p ... --allowedTools "Read,Write" --output-format json`, a local subprocess under Tebello's already-paid Claude subscription — $0 marginal cost) — ADR-003 there.

Both run "as fast as the local resource allows" against local hardware / a flat-cost subscription, not against a metered remote quota. Tebello has confirmed TebelloReborn drops OpenRouter entirely and splits its two call sites the same way, by matching each to the sibling workload it resembles.

This is a *pattern* reuse across a separate codebase, not a code copy: the module names, schemas, and call sites differ, and TebelloReborn only adopts the machinery it has evidence it needs (see Decision §6).

## Decision

### 1. Drop OpenRouter entirely; route each call site by workload shape

TebelloReborn will not build `src/shared/openrouter_client.py` (currently Build Queue Phase 1, steps 8–9). OpenRouter is removed from the project's dependency surface. The two planned call sites are routed by analogy to the two sibling workloads:

| TebelloReborn stage | Resembles (`ai-outreach`) | Backend |
|---|---|---|
| AI Matching (`matching/scorer.py`) | `research` summariser | **Local Ollama** (`qwen3:8b`) |
| Document Generation (`doc_gen/*`) | `asset_gen` | **Headless Claude Code** (`claude -p`) |

`src/shared/rate_limiter.py` is still built and still needed (the Ollama client and the Apify client both use it). Only `openrouter_client.py` disappears.

### 2. AI Matching → local Ollama (`qwen3:8b`)

Matching is a structured scoring pass, the direct analogue of `research`'s summarisation. It routes to a local Ollama daemon.

- **New client: `src/matching/ollama_client.py`** — *not* `src/shared/`. Placement follows the precedent ADR-004 established and TebelloReborn's own `CLAUDE.md` already cites: a **single-consumer** client lives beside its consumer module. Matching is Ollama's only consumer here (doc-gen goes to Claude Code, not Ollama), so it belongs in `matching/`, exactly the `apify_client.py` case, not the shared `openrouter_client.py` case. If a second Ollama consumer ever appears, promoting to `shared/` is a trivial move-and-reimport — premature now.
- **Mirror the `ollama_client.py` shape:** a module-level `RateLimiter` acquired before the request (`OLLAMA_RATE_LIMIT_PER_MIN`, default `120` — a safety valve against a runaway loop, not a real throttle, since Ollama serialises generation locally); two distinct exception types, `OllamaError` (base — non-200, bad response shape, read-timeout) and `OllamaUnreachableError` (subclass — connection-refused / connect-timeout, "is it running?"); **no API key** and therefore no missing-key guard; a short connect timeout so a stopped daemon fails fast and clearly; native `POST {OLLAMA_BASE_URL}/api/generate` with `{"model": ..., "prompt": ..., "stream": false, "think": false}`, returning the `response` field with any surviving `<think>...</think>` block stripped.
- **`scorer.py` fails loud — no silent fallback.** If Ollama is unreachable the exception propagates; there is deliberately no fallback backend (and after this ADR there is no OpenRouter left to fall back to anyway). This matches ADR-004 §Decision.5.
- **No schema change from matching.** The match score is written onto the vacancy record, whose table is designed in Phase 3 (status `new → scored`) — analogous to `research` writing a `summary` string. Matching introduces no new table and no migration of its own. (The score column is part of the Phase 3 vacancy schema, not this ADR.)

### 3. Document Generation → headless Claude Code (`claude -p`)

CV + cover-letter generation is quality-sensitive, client-facing content a human submits — the direct analogue of `asset_gen`. It routes to a headless Claude Code subprocess under Tebello's Claude subscription ($0 marginal cost).

- **New runner in `src/doc_gen/`** shells out via `subprocess.run(["claude", "-p", <instruction>, "--allowedTools", "Read,Write", "--output-format", "json"], capture_output=True, text=True, timeout=<default constant>)`, mirroring `ai-outreach`'s `handoff/runner.py`. Prompt is rendered from a template using only fields that exist on the real profile/vacancy schemas.
- **`cv_generator.py` and `cover_letter_generator.py`** route their non-offline branch through the runner. Both get a fresh `OFFLINE_MODE` stub branch built RED/GREEN (see §7) — there is no existing offline stub to preserve here, unlike the sibling projects where the branch already existed.
- **Failures are data, not exceptions.** The runner returns `throttled` / `error` as fields on its result (throttle detected via rate-limit/quota indicators in stderr), so a throttle mid-`run-all` does not crash the batch — the vacancy is left at `scored` and the loop continues. Only a genuinely unexpected condition (the `claude` binary missing from `PATH`, i.e. `FileNotFoundError`) propagates. This mirrors `ai-outreach` ADR-003 §5.
- **New local desktop runtime dependency:** the `claude` binary must be on `PATH` and authenticated on whatever machine runs a real generation. Not pip-installable, not CI-verifiable; surfaces as a clear runtime error, not an import-time failure — the same class of dependency as the Ollama daemon in §2.

### 4. Schema — a `generation_log` table in `career.db`, created the project's own way

Document generation gets an audit/observability table. Per ADR-001 (SQLite is the single source of truth), it is added to the **existing** `career.db` — not a separate database file.

**Exact baseline schema, written inline in `src/doc_gen/db.py::init_db()`:**

```sql
CREATE TABLE IF NOT EXISTS generation_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id    INTEGER NOT NULL REFERENCES vacancies(id),
    doc_type      TEXT NOT NULL CHECK (doc_type IN ('cv','cover_letter')),
    session_id    TEXT,
    started_at    TEXT NOT NULL,
    duration_ms   INTEGER,
    cost_usd      REAL,
    status        TEXT NOT NULL CHECK (status IN ('success','throttled','error')),
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_generation_log_vacancy_id ON generation_log(vacancy_id);
CREATE INDEX IF NOT EXISTS idx_generation_log_started_at ON generation_log(started_at);
```

`status` gets a Python `Enum` wrapper (`GenerationStatus`, values `success`/`throttled`/`error`) in `src/doc_gen/schema.py`, so callers never pass free text — matching how `HandoffStatus` wraps the same values in the sibling. `doc_type` distinguishes the two documents generated per vacancy.

**On the "No schema changes without a migration file. Ever" hard rule — this is satisfied, exactly as `ai-outreach` ADR-003 §2 and TebelloReborn's own `docs/todo.md` "Resolved Items" establish.** TebelloReborn's confirmed convention (verified against `ai-outreach`'s `lead_import`/`approval` modules) is: a table's **baseline** shape is an idempotent `CREATE TABLE IF NOT EXISTS` checked into version control inside a `db.py` — this is the tracked, reviewable record of the initial shape, and is not itself a numbered migration; **every change after baseline** goes through a `migrations.py` (`MIGRATIONS: list[tuple[int, str]] = []` + `apply_migrations()`, applied via `PRAGMA user_version`). Therefore:

- The baseline `CREATE TABLE` above lives inline in `src/doc_gen/db.py`.
- An **empty-stub `src/doc_gen/migrations.py`** ships alongside it from day one, so the very first column ever added to `generation_log` (e.g. a future token-usage column) has a migration home waiting and cannot be done ad-hoc.

This is the migration artifact the hard rule requires, in the form this project actually uses. There is no standalone `migrations/*.sql` file — that convention does not exist in TebelloReborn.

**Scope of the table — record the generation *event*, not the human judgment.** Unlike `ai-outreach`'s `handoff_log`, `generation_log` carries **no `quality_flag`**. TebelloReborn has a dedicated Human Review stage (`src/review/`, Phase 6) that already records the human's approve/reject/edit decision. Duplicating a quality/approval signal into `doc_gen` would couple two modules that should stay separate: `generation_log` records *that a document was generated* (status, cost, timing, session, failure reason); `review/` records *what the human decided about it*. Keep them apart.

### 5. Config changes — remove OpenRouter fields, add Ollama fields

`src/config.py` and `.env.example` currently carry (committed in Phase 0, before this decision) `OPENROUTER_API_KEY` and `OPENROUTER_RATE_LIMIT_PER_MIN`. This ADR removes both and adds the Ollama fields, following the existing dataclass-field + `os.environ.get` pattern:

- **Remove:** `OPENROUTER_API_KEY`, `OPENROUTER_RATE_LIMIT_PER_MIN`.
- **Add:** `OLLAMA_BASE_URL: str = "http://localhost:11434"`, `OLLAMA_MODEL: str = "qwen3:8b"`, `OLLAMA_RATE_LIMIT_PER_MIN: int = 120`.
- **Keep:** `APIFY_API_KEY`, `APIFY_RATE_LIMIT_PER_MIN`, `DB_PATH`, `OFFLINE_MODE`, `EXPORTS_DIR`.

The three Ollama values are non-secret (a local URL, a model name, an integer) and go into `.env.example` as real defaults, same reasoning as the existing non-secret settings.

**This config change is a queued follow-up task, NOT part of this ADR.** It must be done by an Executor via TDD: update `tests/unit/test_config.py` first (RED — it currently asserts the OpenRouter fields), then `src/config.py` and `.env.example` (GREEN). The Architect does not make this code change. It is flagged here so the Planner sizes it as a discrete step.

### 6. Volume-cap / scheduler machinery — deliberately NOT included (judgment call)

`ai-outreach`'s headless-Claude track shipped a `settings.py` + `scheduler.py` with weekly/daily volume caps, a hot-reloadable `config/handoff_settings.json`, and a `weekly_report.py`. Those existed for a **documented** reason: a controlled 5-leads/week trial keeping the footprint on the shared Claude subscription small and observable.

TebelloReborn has **no such documented requirement.** Nothing in its `CLAUDE.md`, `docs/todo.md`, or `mvp-pipeline-build.md` calls for batch-volume throttling of document generation; the MVP simply generates a CV + cover letter per vacancy and stops at human review. TebelloReborn's own conventions (and the vault code-conventions doc) explicitly say not to add abstractions beyond what is needed. Therefore this ADR **does not** adopt the scheduler / volume-cap / weekly-report layer, the `handoff_settings.json` file, or a `HANDOFF_SETTINGS_PATH`-style config field. A simpler runner + the `generation_log` audit table is what the current evidence warrants.

The runner's subprocess timeout is a module-level default constant (mirroring the sibling runner's `DEFAULT_HANDOFF_TIMEOUT_SECONDS`), not a config field, unless a concrete need for tuning it emerges.

This is a sizing judgment, flagged for the Planner: if Tebello later wants controlled-volume batching of doc generation, that earns its own spec, its own `scheduler`/settings layer, and quite possibly a `PRAGMA user_version` migration to add the columns a report would need — at which point the empty `migrations.py` stub from §4 is exactly the seam that keeps it non-ad-hoc.

### 7. `OFFLINE_MODE` — the whole suite must stay green with zero real calls

TebelloReborn's `tests/unit/conftest.py` already forces `OFFLINE_MODE=true` as an autouse fixture (mirroring `ai-outreach` exactly). Both new backends must honour this the same way both sibling precedents do:

- `matching/scorer.py` and both `doc_gen` generators branch on `OFFLINE_MODE` **before** any client/subprocess call and return a deterministic stub. The Ollama HTTP call and the `claude -p` subprocess live only in the non-offline `else` branch.
- No test makes a real HTTP call to `localhost:11434` and no test spawns a real `claude` subprocess. Client/runner-level tests mock `requests.post` / `subprocess.run` directly.

This is a hard acceptance criterion: the full suite passes offline, with zero real network or subprocess calls, matching both `ai-outreach` precedents byte-for-byte in intent.

### 8. Rollback & blast radius

Blast radius is unusually small **because none of the affected code is built yet.** This decision changes what gets written in Phases 4–5, not the behaviour of existing code. The only already-committed artifacts it touches are `src/config.py`, `.env.example`, and `tests/unit/test_config.py` (the OpenRouter fields, per §5).

Rollback of the decision itself = keep the OpenRouter config fields and build `src/shared/openrouter_client.py` + OpenRouter-based `scorer.py`/`doc_gen` as the original plan had it. Rollback of the built feature later (once it exists) is mechanical and additive: revert the non-offline branches, `DROP TABLE IF EXISTS generation_log`, and remove the Ollama config fields. Because `generation_log` is a new secondary table and the offline paths are untouched, a rollback cannot cause data loss on `profiles`/`vacancies`/`review` tables.

## Consequences

- Combined, matching (local Ollama) and document generation (headless Claude subscription) run the pipeline's inference at **$0 marginal cost** on local resources — no per-token billing, no dependence on an OpenRouter credit balance.
- **The OpenRouter Known Issue is fully resolved for TebelloReborn.** The project no longer depends on OpenRouter credits at all; the `docs/todo.md` "Known Issues" line `OPENROUTER_API_KEY out of credits (shared blocker with ai-outreach-agency)` should be removed by the Planner in the follow-up doc pass. (The blocker may still exist for other projects — it is simply no longer TebelloReborn's.)
- **Two new local desktop runtime dependencies** replace one paid API: the Ollama daemon (`qwen3:8b` pulled, listening on `localhost:11434`) for matching, and the authenticated `claude` CLI on `PATH` for doc generation. Neither is verifiable at import time; each surfaces as a clear runtime error.
- Match-quality characteristics change: `qwen3:8b` is a smaller local model than Claude-via-OpenRouter. Acceptable, because matching is a low-stakes scoring pass gating which vacancies proceed, and everything downstream still passes through the mandatory human review gate before anything leaves the system.
- The pipeline gains `src/matching/ollama_client.py`, and a `src/doc_gen/` runner + `db.py` + `schema.py` + `migrations.py` stub + `generation_log` table. It loses the planned `src/shared/openrouter_client.py`.
- Build Queue changes for the Planner: Phase 1 steps 8–9 (openrouter_client RED/GREEN) are dropped; Phase 4 and Phase 5 steps are re-specified against Ollama / Claude Code; a new config-migration step (§5) is inserted; `docs/api-patterns.md` (Phase 8) documents Ollama + Claude Code instead of OpenRouter.
- Matching and document generation are **independent backends** — one being unavailable (Ollama down vs. `claude` not authenticated) does not implicate the other. A vacancy still cannot reach doc generation without first being scored, so both must work for a real end-to-end run, but their failure modes and remediation are separate.

## Alternatives considered

- **A. Keep OpenRouter, top up credits, change nothing.** Rejected: recurring per-token cost is exactly what this eliminates, and it leaves the pipeline dependent on a paid balance that has already hit HTTP 402. Local Ollama + the already-paid Claude subscription are $0 marginal.
- **B. Route both call sites to headless Claude Code** (skip Ollama entirely). Rejected as the default: matching is a high-frequency, low-stakes scoring pass; spending the Claude subscription's shared rate pool on it wastes that budget on the cheap step, whereas Ollama offloads it to local hardware for free. Deferred, not dismissed — if local hardware proves too slow for `qwen3:8b` scoring, moving matching onto the same Claude-Code mechanism is the natural fallback and would reuse the doc-gen runner. Mirrors ADR-004 §Alternatives.B.
- **C. Route both call sites to local Ollama** (skip Claude Code). Rejected: document generation is client-facing content a human submits to real employers; the quality gap between `qwen3:8b` and Claude matters here in a way it does not for a scoring integer. The two-backend split spends quality where it counts and saves it where it doesn't.
- **D. Put `ollama_client.py` in `src/shared/`** for symmetry. Rejected: `shared/` placement is earned by multiple consumers. Matching is Ollama's only consumer; single-consumer clients live beside their consumer module (the `apify_client.py` precedent, restated in ADR-004 §Alternatives.D). Promote later if a second consumer appears.
- **E. Ship the full `handoff/` machinery** (scheduler, volume caps, settings JSON, weekly report). Rejected: no documented volume-throttling requirement exists for TebelloReborn; copying that layer would be speculative infrastructure. Deferred to its own spec if a controlled-batch need is ever stated. (See Decision §6.)
- **F. Put a `quality_flag` on `generation_log`** (mirroring `handoff_log`). Rejected: TebelloReborn already has a dedicated `review/` module that records the human's decision. Generation-event data and human-judgment data stay in separate modules. (See Decision §4.)
- **G. A standalone `migrations/001_create_generation_log.sql` file** to satisfy the hard rule literally. Rejected: that convention does not exist in TebelloReborn. Baseline creation is inline `CREATE TABLE IF NOT EXISTS` in `db.py`; post-baseline changes go through `migrations.py` + `PRAGMA user_version`, per `docs/todo.md` "Resolved Items" and `ai-outreach` ADR-003 §2.

## Open judgment calls flagged for the Planner

1. **Volume-cap / scheduler layer (Decision §6):** deliberately excluded on current evidence. Confirm with Tebello whether controlled-batch document generation is wanted; if so it is a separate spec + ADR, not a bundle into this build.
2. **Runner subprocess timeout:** shipped as a module-level default constant, no config field, unless a tuning need emerges.
3. **`generation_log` connection convention:** none of TebelloReborn's `db.py` modules exist yet, so there is no established path-vs-`Connection` precedent to mirror (in `ai-outreach`, `handoff_log` took a `Connection` because a `leads` connection was already owned). The Planner should keep `doc_gen/db.py::init_db()` consistent with whatever convention Phase 2/3's `profile/db.py` and `vacancy_search/db.py` set first, since `generation_log` is a secondary table in the shared `career.db`.
4. **FK target name:** the `REFERENCES vacancies(id)` in §4 assumes the Phase 3 vacancy table is named `vacancies` with an `id` PK. Confirm and align once the Phase 3 schema (step 17) is written.
