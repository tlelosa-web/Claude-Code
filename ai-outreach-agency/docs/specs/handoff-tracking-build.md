# Spec: Claude Code Headless Handoff — Build Plan (adapted)

**Project:** ai-outreach-agency
**Owner:** Tebello Lelosa
**Status:** Ready for Executor (pending one open decision — see §6)
**Pattern:** DCOE Pattern 1 (New Feature)
**Supersedes:** `docs/specs/drafts/handoff-tracking.md` (kept as-is for reference; this
document is the buildable version, adapted to this project's real conventions).

---

## 1. Goal

Replace the OpenRouter-based Claude inference call in `asset_gen` with a headless
Claude Code invocation (`claude -p ...`) running under Tebello's existing Claude
subscription instead of pay-per-token billing, at $0 marginal cost. Add tracking
(`handoff_log`), a hot-reloadable volume-control settings file, and a weekly
usage/cost report, so the trial (5 leads/week) can be run and monitored safely.

`research/claude_summariser.py` keeps using OpenRouter — untouched, out of scope
(see Non-goals). See §5 for why `email_draft` is *not* touched by default,
contrary to the original framing of this feature.

---

## 2. Source materials

- `docs/specs/drafts/handoff-tracking.md` — original spec (problem, schema, settings, mechanics, acceptance criteria). Left in place, unmodified.
- `docs/specs/drafts/handoff_scheduler.py`, `weekly_report.py`, `handoff_template.md`, `run_handoff.bat`, `handoff_settings.json`, `001_create_handoff_log.sql` — drafted companion files, used as a starting point and adapted below.
- Real code read to verify conventions: `src/lead_import/db.py`, `src/lead_import/migrations.py`, `src/approval/db.py`, `src/approval/cli.py`, `src/config.py`, `src/asset_gen/generator.py`, `src/asset_gen/pipeline.py`, `src/asset_gen/prompt_builder.py`, `src/asset_gen/schema.py`, `src/email_draft/composer.py`, `src/email_draft/pipeline.py`, `src/shared/rate_limiter.py`, `src/shared/openrouter_client.py`, `src/main.py`, `tests/unit/conftest.py`, `tests/integration/test_full_pipeline.py`.

---

## 3. Convention adaptations (read this before building)

### 3.1 Migration convention — no standalone `.sql` file

The draft's `migrations/001_create_handoff_log.sql` assumes a `migrations/*.sql`
folder. **That convention does not exist in this project.** The real, established
pattern (verified in `lead_import/db.py` + `lead_import/migrations.py`, and
`approval/db.py`) is:

- The table's **baseline shape** is created with `CREATE TABLE IF NOT EXISTS`
  written directly in Python, inline in a `db.py`. This is how `leads`
  (`lead_import/db.py::init_db`) and `approvals` (`approval/db.py::init_approvals_table`)
  were created. Baseline `CREATE TABLE` is *not* itself a numbered migration.
- A **separate `migrations.py`** (`MIGRATIONS: list[tuple[int, str]]`, applied
  via `PRAGMA user_version` in `apply_migrations()`) exists *only* in
  `lead_import/`, and only tracks *post-baseline* `ALTER TABLE` changes (its one
  entry adds the `campaign` column). `approval/` has no `migrations.py` because
  it has never needed to alter `approvals` after creation.

**Adaptation:** `src/handoff/db.py` gets a baseline `CREATE TABLE IF NOT EXISTS
handoff_log` (from the draft's SQL, ported to Python), plus an empty-stub
`src/handoff/migrations.py` (`MIGRATIONS: list[tuple[int, str]] = []` +
`apply_migrations()`) ready for future column additions (e.g. token-usage
tracking) without needing a new spec cycle. This satisfies CLAUDE.md's hard
rule *"No schema changes without a migration file. Ever"* the same way `leads`
and `approvals` satisfy it today: baseline creation is inline, and the
migrations file is the mechanism for every change *after* baseline.

**One nuance flagged to Architect:** unlike `lead_import/db.py::init_db()`
(which opens a brand-new SQLite file and owns `PRAGMA journal_mode=WAL`),
`handoff_log` lives inside the *existing* `leads`/`approvals` database (per
ADR-001, single source of truth — this is also true in the draft). So
`src/handoff/db.py::init_db()` takes an **existing `sqlite3.Connection`**
rather than a path, and is called lazily right before a write — mirroring
`approval/db.py::init_approvals_table()` + `approval/cli.py::_persist_approval()`,
*not* `lead_import`'s eager, `main.py`-threaded `_get_db()` pattern. This avoids
touching `main.py::_get_db()` / the `DB_PATH`-threading logic that CLAUDE.md's
own "DB_PATH gotcha" note warns is fragile. Architect should confirm this
reading of the hard rule is acceptable before Phase 1 lands (flagged, not
blocking — same precedent already exists twice in this codebase).

### 3.2 Config location — JSON file stays, but its path is a `Settings` field

`src/config.py` has one existing config mechanism: a `Settings` dataclass
populated entirely from environment variables via `python-dotenv`. There is no
existing `config/` directory or JSON-config convention anywhere in the project.

The draft's stated reason for a standalone `config/handoff_settings.json` is
that volume caps (`weekly_lead_cap`, `daily_lead_cap`, `run_days`, etc.) need to
be hand-editable and take effect on the *next scheduled run* with **no code
redeploy** — the scheduler re-reads the file fresh before every run. Folding
these values into `.env` (parsed once per process start via `Settings`) doesn't
break that requirement, but it does make the values look like every other
env-driven setting, when in practice they're meant to be tweaked far more often
and by hand, mid-week, without touching `.env`.

**Adaptation:** keep the standalone JSON file (preserves the hot-reload intent
verbatim), but make its *location* configurable through the existing
`Settings`/env-var convention instead of a hardcoded module-level `Path`
constant (as the draft's `handoff_scheduler.py` has). Add
`Settings.HANDOFF_SETTINGS_PATH: str = "config/handoff_settings.json"` (env
override `HANDOFF_SETTINGS_PATH`), same pattern as `EXPORTS_DIR`/`DASHBOARD_PATH`.
`src/handoff/settings.py::load_handoff_settings(path)` still re-reads the file
from disk on every call — no caching, so hand-edits take effect on the next
scheduled run exactly as the draft intended.

`config/handoff_settings.json` is committed to the repo with the draft's
starting values (it is not a secret — same reasoning as `.env.example`, except
this file has real, non-placeholder starting values because it's not secret
material).

### 3.3 Template field mismatch — draft's placeholders don't exist on real schemas

The draft's `handoff_template.md` uses `{{signals}}`, `{{pain_points}}`, and
`{{research_notes}}`. Neither `Lead` (`lead_import/schema.py`) nor
`ResearchResult` (`research/schema.py`, fields: `summary: str`, `raw_data: dict`)
has those fields. The real available data is `research.summary` (the only
Claude-generated field) and `research.raw_data` (raw scrape dict, shape not
guaranteed). **Adaptation:** the ported template (`src/handoff/templates/handoff_template.md`)
uses `{{company_name}}`, `{{industry}}`, `{{contact_name}}`, `{{contact_title}}`,
`{{region}}`, and `{{research_summary}}` (→ `research.summary`) only — matching
`asset_gen/prompt_builder.py::build_prompt()`'s existing field usage, which is
the closest real precedent for "what a Claude prompt for this pipeline is
allowed to reference."

### 3.4 Runner mechanism — Python `subprocess`, not `run_handoff.bat`

The project has zero `.bat` files today; every automation path is Python and
covered by pytest with `OFFLINE_MODE`. A `.bat` file cannot be unit-tested or
mocked the way `subprocess.run` can. **Decision:** `src/handoff/runner.py`
invokes `claude -p ...` via `subprocess.run(..., capture_output=True, text=True)`
directly — this is the code path the pipeline actually calls, and it's what
gets mocked in tests (consistent with how `OFFLINE_MODE` branches happen in the
*calling* module, e.g. `asset_gen/generator.py`, not inside the client itself).
`docs/specs/drafts/run_handoff.bat` is copied to `scripts/run_handoff.bat`
unchanged, kept only as an optional manual/ad-hoc convenience for Tebello to
run a single lead outside the Python pipeline — it is never imported or shelled
out to by `src/`.

---

## 4. Schema (adapted)

```sql
CREATE TABLE IF NOT EXISTS handoff_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id         INTEGER NOT NULL REFERENCES leads(id),
    session_id      TEXT,
    started_at      TEXT NOT NULL,
    duration_ms     INTEGER,
    cost_usd        REAL,
    status          TEXT NOT NULL CHECK (status IN ('success','throttled','error')),
    quality_flag    TEXT CHECK (quality_flag IN ('pass','edit_heavy','reject')) DEFAULT NULL,
    error_message   TEXT
);
CREATE INDEX IF NOT EXISTS idx_handoff_log_lead_id ON handoff_log(lead_id);
CREATE INDEX IF NOT EXISTS idx_handoff_log_started_at ON handoff_log(started_at);
```

Written inline in `src/handoff/db.py::init_db(conn)`, unchanged from the draft's
SQL other than syntax (Python string, not a `.sql` file). Column names/types/
CHECK constraints kept identical to the draft — no reason to diverge.

Unlike the draft's raw strings, `status` and `quality_flag` get Python `Enum`
wrappers (`HandoffStatus`, `QualityFlag` in `src/handoff/schema.py`) so callers
don't pass free-text — matching `approval/schema.py::Decision` and
`asset_gen/schema.py::AssetType`, the two existing status-enum precedents in
this codebase.

---

## 5. `email_draft` scope — open decision, flagged, not auto-resolved

The task framing (and the draft spec's title) assumes **both** `asset_gen`
*and* `email_draft` currently call OpenRouter. That's only half true:

- `asset_gen/generator.py::generate_asset()` **does** call `call_openrouter(prompt)`
  when not in `OFFLINE_MODE`. This is a real, unambiguous call site to replace.
- `email_draft/composer.py::compose_email()` is a **pure Python string
  template** — it has never called an LLM. `email_draft/pipeline.py::run_email_draft()`
  calls `compose_email()`, not any inference client. There is no OpenRouter
  call site in `email_draft` to replace.

The draft's own `handoff_template.md`, however, is written to produce **both**
an `## ASSET` and an `## EMAIL` section from a single `claude -p` call —
implying a combined-call design where the same headless invocation would also
replace `compose_email()`'s static template with LLM-drafted copy. That is a
materially bigger change than "replace an existing call": it means adding new
fields to `AssetResult`/`DraftResult` to carry the drafted email through the
approval gate, and changing what the human reviewer sees at the approval step
(currently asset-only) to include a proposed email body — i.e. it **touches the
approval-gate interaction**, which is one of the categories this plan treats as
requiring mandatory Reviewer sign-off *before* any executor starts (see §9).

**Recommendation (default path, Option A):** ship this feature scoped to
`asset_gen` only. `email_draft` is untouched — there is nothing to replace
there today, and touching it pulls in an approval-gate redesign that's out of
proportion to "stop paying OpenRouter for two calls that are currently one
call." This keeps the change inside the draft's own Non-goals ("No change to
... approval-gate ... Gmail send logic").

**Option B (deferred):** combine asset+email generation into one handoff call
per the draft's template, redesign `AssetResult`/approval display accordingly.
Not built here. If Tebello wants this, it should be scoped as its own spec
after Option A ships and the trial proves out, not bundled into this build.

This is recorded in ADR-003 (§10) as the accepted decision, but is called out
here explicitly per the instruction not to silently deviate from the original
framing.

---

## 6. Settings & scheduler (adapted from draft)

`config/handoff_settings.json` (committed, starting values from the draft):

```json
{
  "weekly_lead_cap": 5,
  "daily_lead_cap": 2,
  "min_interval_minutes": 60,
  "run_days": ["Mon", "Wed", "Fri"],
  "use_bare_mode": false
}
```

`src/handoff/settings.py::load_handoff_settings(path: str) -> HandoffSettings`
— reads fresh every call (no caching), returns a small dataclass (not a raw
dict, unlike the draft) so callers get attribute access + type checking.
Raises a clear `FileNotFoundError`-derived error if the file is missing —
callers (scheduler) must not silently proceed with defaults.

`src/handoff/scheduler.py::can_run_now(db_path, settings_path) -> tuple[bool, str]`
— same five checks as the draft (`run_days`, weekly cap, daily cap, min
interval, then allow), rewritten to call `handoff/db.py` query helpers
(`count_success_since`, `get_last_success_started_at`) instead of inline SQL,
and to take `settings_path` explicitly (testability — no hardcoded module-level
`Path`). Counts only `status = 'success'` rows against caps, matching the draft.

`src/handoff/scheduler.py::log_result(...)` — same shape as the draft, delegates
to `handoff/db.py::log_result(conn, ...)`.

---

## 7. Runner (adapted from draft)

`src/handoff/runner.py::run_headless_handoff(lead_id, prompt_path, output_path,
use_bare_mode=False) -> HandoffRunResult` —

1. Renders `src/handoff/templates/handoff_template.md` with the lead + research
   fields listed in §3.3, writes it to `handoff/lead_<id>.md`.
2. Shells out via `subprocess.run(["claude", "-p", <instruction>,
   "--allowedTools", "Read,Write", "--output-format", "json"] + (["--bare"] if
   use_bare_mode else []), capture_output=True, text=True, timeout=<configurable>)`.
3. Parses stdout as JSON → `session_id`, `duration_ms`, `cost_usd`.
4. Non-zero exit code, timeout, or a rate-limit indicator in stderr →
   `HandoffRunResult(status=THROTTLED or ERROR, error_message=...)` instead of
   raising — the caller decides what to do (see §8).
5. Never raises for a "normal" failure (throttle/error are data, not
   exceptions) — only raises for genuinely unexpected conditions (e.g.
   `claude` binary not found at all), so pipeline code can't accidentally let
   an uncaught exception crash `run-all` mid-batch.

`handoff/` (the per-lead scratch dir: `lead_<id>.md`, `output_<id>.md`,
`result_<id>.json`) is added to `.gitignore` — transient run artifacts, same
treatment as `exports/`/`data/`/`dashboard.html`.

---

## 8. Pipeline wiring (adapted)

`asset_gen/generator.py::generate_asset()` — the `OFFLINE_MODE` branch is
**unchanged** (`_stub_text(lead)`). Only the `else` branch changes:

```python
# before
text = call_openrouter(prompt)

# after
allowed, reason = scheduler.can_run_now(db_path, settings_path)
if not allowed:
    raise HandoffBlockedError(reason)
result = runner.run_headless_handoff(lead.id, ...)
scheduler.log_result(db_path, lead_id=lead.id, session_id=result.session_id, ...)
if result.status != HandoffStatus.SUCCESS:
    raise HandoffCallError(result.error_message)
text = result.asset_text
```

`asset_gen/pipeline.py::run_asset_gen()` catches `HandoffBlockedError` /
`HandoffCallError`, does **not** call `update_lead_status` (lead stays at
`researched`, eligible for a later `run-all`), and re-raises a single shared
`HandoffSkipped` signal.

`main.py::cmd_run_all()`'s loop catches `HandoffSkipped` (alongside the
existing `SystemExit` catch for the approval gate's quit path), prints a
"skipped — <reason>" line, and **continues to the next lead** instead of
crashing the batch — this is the acceptance-criterion behavior ("throttled/
error runs do not crash the pipeline — logged and skipped").

`email_draft/*` — no changes (see §5, Option A).

---

## 9. Mandatory pre-execution Reviewer sign-off

Per CLAUDE.md: *"Reviewer agent runs on all auth, file-write, and data-export
code"* (baseline — before merge, always). The following steps go further and
require Reviewer sign-off **before the executor starts work**, because they sit
on the path that could let unreviewed content reach the human approval queue,
or because they directly touch the approval-gate interaction:

- **Step 16/17** (`src/handoff/runner.py` + its RED test) — parses the `claude
  -p` subprocess JSON output; a parsing bug here is exactly the "unreviewed
  output reaches the pipeline" risk.
- **Step 19/20** (`asset_gen/generator.py` + `asset_gen/pipeline.py` wiring) —
  this is the code path that takes the runner's output and feeds it into
  `AssetResult.asset_text`, which the approval gate (`approval/cli.py::_print_review`)
  displays and a human decides on. This is the literal "reach the approval
  queue via an unreviewed path" case.
- **Step 26/27** (`approval/cli.py` — `quality_flag` capture) — directly
  modifies the approval-gate CLI flow itself.

All other steps follow the normal rule: Reviewer approves before merge, not
before the executor starts.

---

## 10. ADR

`docs/decisions/ADR-003-headless-claude-handoff.md` (Step 1, Architect) records:
the OpenRouter → headless-Claude-Code decision, the migration adaptation
(§3.1), the config-location adaptation (§3.2), and the `email_draft` scope
decision (§5, Option A accepted / Option B deferred).

---

## 11. Acceptance criteria (mapped from the draft, verified in Step 28)

- [ ] `src/handoff/db.py::init_db(conn)` runs cleanly against a copy of a real
      `outreach.db` with existing `leads`/`approvals` data — no data loss,
      `handoff_log` created alongside.
- [ ] Editing `config/handoff_settings.json` by hand changes scheduler
      behavior on the next `can_run_now()` call, with no process restart
      required beyond the next CLI invocation (no caching in `load_handoff_settings`).
- [ ] A full offline trial lead run produces exactly one `handoff_log` row.
- [ ] `scripts/weekly_report.py` generates correctly on an empty week (zero
      `handoff_log` rows) without erroring.
- [ ] Throttled/error runs do not crash `run-all` — logged, lead left at
      `researched`, loop continues to the next lead.
- [ ] Zero `call_openrouter` references remain in `asset_gen/generator.py`'s
      non-offline path.
- [ ] `email_draft/*` unmodified (confirms Option A scope was respected).
- [ ] Full existing suite (129 tests) plus all new tests pass; `OFFLINE_MODE`
      autouse fixture never triggers a real `subprocess.run` to `claude` or a
      real network call.

---

## 12. Risks / operational notes (not tasks — context for Tebello)

- `claude -p` requires the `claude` CLI on `PATH` and an authenticated session
  on whatever machine runs the scheduled handoff — this is a local desktop
  dependency, not something the pipeline can verify at import time.
- Headless handoff runs will consume the same Claude subscription
  usage/rate-limit pool as interactive sessions on that machine. The
  `min_interval_minutes`/daily/weekly caps in `handoff_settings.json` exist
  specifically to keep this trial's footprint small and observable via the
  weekly report — raise them deliberately, not by accident.
- `research/claude_summariser.py` still uses OpenRouter and is still blocked
  on the existing HTTP 402 (out of credits) issue tracked in `docs/todo.md`
  under Known Issues — this feature does not resolve that; a lead still can't
  reach `asset_gen` without a working `research` stage first, so OpenRouter
  credits still need topping up to run the pipeline end-to-end on new leads.

---

## 13. Ordered atomic task list

Executor agent legend: **architect**, **tester**, **executor**, **doc-writer**,
**reviewer** (per this project's `CLAUDE.md` roster; note `.claude/agents/*.md`
files for this project are currently placeholders — see the summary note at
the end of this document).

| # | Description | Executor | Input files | Expected output | Verification |
|---|---|---|---|---|---|
| 1 | Write ADR-003 (decision + all adaptations from §3, §5) | architect | `docs/specs/drafts/handoff-tracking.md`, this spec | `docs/decisions/ADR-003-headless-claude-handoff.md` | Read-through: covers OpenRouter→headless decision, migration adaptation, config adaptation, email_draft Option A/B |
| 2 | Package marker for new module | executor | — | `src/handoff/__init__.py` | Imports cleanly (`python -c "import src.handoff"`) |
| 3 | RED: schema tests | tester | — | `tests/unit/test_handoff_schema.py` | `pytest` fails (module doesn't exist yet) |
| 4 | GREEN: schema (`HandoffStatus`, `QualityFlag` enums, `HandoffLogEntry` dataclass) | executor | Step 3 test | `src/handoff/schema.py` | Step 3 test passes |
| 5 | RED: db layer tests (`init_db`, `log_result`, `count_success_since`, `get_last_success_started_at`, `get_rows_since`, migrations no-op) | tester | Step 4 schema | `tests/unit/test_handoff_db.py` | `pytest` fails |
| 6 | GREEN: db layer + migrations stub | executor | Step 5 test | `src/handoff/db.py`, `src/handoff/migrations.py` | Step 5 tests pass; run against a copied real `outreach.db` fixture with existing `leads` rows — confirms no data loss (acceptance criterion 1) |
| 7 | RED: `Settings.HANDOFF_SETTINGS_PATH` test | tester | — | `tests/unit/test_config.py` (new) | `pytest` fails |
| 8 | GREEN: add `HANDOFF_SETTINGS_PATH` field + env mapping | executor | Step 7 test | `src/config.py` | Step 7 test passes; existing `test_main.py`/CLI tests still pass |
| 9 | RED: handoff settings loader tests (fresh-read, missing-file error, hot-reload-on-second-call) | tester | — | `tests/unit/test_handoff_settings.py` | `pytest` fails |
| 10 | GREEN: settings loader | executor | Step 9 test, Step 8 config | `src/handoff/settings.py` | Step 9 tests pass |
| 11 | Starting config file + `.env.example` entry | executor | Draft `handoff_settings.json` | `config/handoff_settings.json`, `.env.example` (add `HANDOFF_SETTINGS_PATH=config/handoff_settings.json`) | Valid JSON; `load_handoff_settings()` reads it in a manual check |
| 12 | RED: scheduler tests (weekly/daily cap, min interval, run_days, all-clear) | tester | Draft `handoff_scheduler.py` | `tests/unit/test_handoff_scheduler.py` | `pytest` fails |
| 13 | GREEN: scheduler (`can_run_now`, `log_result` passthrough, `HandoffBlockedError`) | executor | Step 12 test, Step 6 db, Step 10 settings | `src/handoff/scheduler.py` | Step 12 tests pass |
| 14 | Port prompt template with real field names (§3.3) | doc-writer | Draft `handoff_template.md`, `asset_gen/prompt_builder.py`, `research/schema.py` | `src/handoff/templates/handoff_template.md` | Manual read-through: no `{{...}}` placeholder references a field that doesn't exist on `Lead`/`ResearchResult` |
| 15 | **[Reviewer sign-off required before start — §9]** RED: runner tests (mocked `subprocess.run`: success/JSON-parse, non-zero exit, timeout, stderr rate-limit → throttled, `use_bare_mode` flag) | tester | Draft `handoff_scheduler.py`/`run_handoff.bat` for shape reference | `tests/unit/test_handoff_runner.py` | `pytest` fails; Reviewer has read and approved the test's behavioral contract before Step 16 starts |
| 16 | **[Reviewer sign-off required before start — §9]** GREEN: runner (`run_headless_handoff`, `HandoffRunResult`, `HandoffCallError`) | executor | Step 15 test, Step 14 template | `src/handoff/runner.py` | Step 15 tests pass; zero real `subprocess.run` to `claude` in test run |
| 17 | Manual-convenience script + gitignore entry | executor | Draft `run_handoff.bat` | `scripts/run_handoff.bat` (adapted paths only), `.gitignore` (add `handoff/`) | Not imported/called anywhere in `src/` (grep confirms) |
| 18 | **[Reviewer sign-off required before start — §9]** RED: `asset_gen` non-offline call-site swap + block-propagation tests | tester | `tests/unit/test_asset_gen.py` (existing) | Same file, extended | `pytest` fails |
| 19 | **[Reviewer sign-off required before start — §9]** GREEN: wire scheduler+runner into `generate_asset()`; propagate `HandoffSkipped` from `run_asset_gen()` | executor | Step 18 test, Step 13 scheduler, Step 16 runner | `src/asset_gen/generator.py`, `src/asset_gen/pipeline.py` | Step 18 tests pass; zero `call_openrouter` references remain in `generator.py`'s non-offline path (acceptance criterion) |
| 20 | RED: `run-all` continues past a blocked/skipped lead instead of crashing | tester | `tests/unit/test_main.py` (existing) | Same file, extended | `pytest` fails |
| 21 | GREEN: `main.py` catches `HandoffSkipped` in the `run-all` loop, prints + continues | executor | Step 20 test, Step 19 pipeline | `src/main.py` | Step 20 tests pass |
| 22 | **Decision checkpoint (no code)** — confirm Option A (§5) with Tebello before any `email_draft/*` file is touched | planner/architect | §5 of this spec | Decision recorded (ADR-003 addendum if it changes) | Explicit go/no-go from Tebello, not inferred |
| 23 | RED: weekly report tests (empty week, cap %, quality breakdown, throttled/error listing) | tester | Draft `weekly_report.py` | `tests/unit/test_weekly_report.py` | `pytest` fails |
| 24 | GREEN: weekly report script | executor | Step 23 test, Step 6 db, Step 10 settings | `scripts/weekly_report.py` | Step 23 tests pass; manual run on an empty test DB produces a report with no exception |
| 25 | **[Reviewer sign-off required before start — §9]** RED: approval-gate `quality_flag` capture tests | tester | `tests/unit/test_approval.py` (existing) | Same file, extended | `pytest` fails |
| 26 | **[Reviewer sign-off required before start — §9]** GREEN: `approval/cli.py` prompts for optional `quality_flag` on approve/edit, persists via `handoff/db.py` | executor | Step 25 test, Step 6 db | `src/approval/cli.py` | Step 25 tests pass; existing approve/reject/edit/quit choices unchanged |
| 27 | RED: integration test — full offline pipeline reaches `drafted` with exactly one `handoff_log` row, zero real subprocess/network calls | tester | `tests/integration/test_full_pipeline.py` (existing) | Same file, extended | `pytest` fails |
| 28 | GREEN: fix any gaps surfaced by Step 27 | executor | Step 27 test | Whichever of the above files needs a small fix | Step 27 passes; full suite (129 + new) green |
| 29 | Acceptance-criteria verification pass | tester + reviewer | §11 checklist | Checklist ticked in this spec (edit) | Every box in §11 independently re-verified, not just assumed from earlier steps |
| 30 | Update `docs/architecture.md` + `CLAUDE.md` pipeline/stack description | doc-writer | This spec | `docs/architecture.md`, `CLAUDE.md` (both ai-outreach-agency copies) | Read-through: no longer implies `email_draft` calls OpenRouter; notes asset_gen's dual invocation paths |
| 31 | Add "Claude Code Headless Invocation" section | doc-writer | This spec | `docs/api-patterns.md` | Mirrors existing OpenRouter/Apify/Gmail section format |
| 32 | Final `docs/todo.md` update | doc-writer | All of the above | `docs/todo.md` | Build Queue cleared to done; Known Issues still lists OpenRouter credits (research stage); Option B noted as deferred/future |

### Dependency ordering

- Steps 2–6 (module scaffold) must land before anything else — everything
  downstream imports `src.handoff`.
- Steps 7–11 (config) must land before Step 13 (scheduler) and Step 16 (runner).
- Step 13 (scheduler) and Step 16 (runner) must both land before Step 19
  (pipeline wiring).
- Step 14 (template) must land before Step 16 (runner GREEN).
- Step 19 must land before Step 21 (main.py loop handling depends on the
  `HandoffSkipped` exception existing).
- Step 22 (decision checkpoint) has no file dependency but gates whether any
  future `email_draft` work is scheduled at all — it can happen any time before
  Step 32, but should happen early so it doesn't block a final report.
- Steps 23–24 (weekly report) only need Step 6 (db) + Step 10 (settings) — can
  run in parallel with Steps 12–21 in a separate worktree.
- Steps 25–26 (quality_flag) only need Step 6 (db) — can also run in parallel
  with Steps 12–21.
- Step 27–28 (integration test) needs Steps 19, 21, and 26 all landed first.
- Step 29 (acceptance pass) needs everything above.
- Steps 30–32 (docs) last, after 29 confirms behavior matches what's documented.

### Note on the referenced planner agent file

The task brief referenced `.claude/agents/planner.md` as "this project's own
tailored planner definition." As of this build, `.claude/agents/` in
`ai-outreach-agency` contains only a `.gitkeep` — no agent files are actually
checked in, despite `CLAUDE.md`'s Sub-Agent Roster table listing one file per
role. This mirrors the doc-vs-reality drift CLAUDE.md's hub root already notes
for the default roster path. Not fixed here (out of scope for this feature);
this plan's task-table format instead follows the shape described in this
project's own `CLAUDE.md` (step → executor → verification) and the vault-level
`.Codex/agents/planner.md` ("Spec or task plan, dependency order,
parallelization notes, acceptance criteria — do not do heavy implementation").

---

## 14. Rollback

Unchanged from the draft's framing: additive only. Rollback = stop calling
`src.handoff` from `asset_gen/generator.py` (revert Step 19), drop
`handoff_log` (manual `DROP TABLE IF EXISTS handoff_log`), remove
`config/handoff_settings.json`. No existing table or approval-gate logic is
altered by Steps 1–24; only Steps 25–26 (`quality_flag` capture) touch
`approval/cli.py` and would need their own targeted revert if rolled back
independently of the rest.
