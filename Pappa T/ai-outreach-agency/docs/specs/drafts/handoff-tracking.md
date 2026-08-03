# Spec: Claude Code Headless Handoff — Tracking & Volume Controls

**Project:** ai-outreach-agency
**Owner:** Tebello Lelosa
**Status:** Draft — ready for Executor
**Pattern:** DCOE Pattern 1 (New Feature)

## Problem

`asset_gen` and `email_draft` currently assume OpenRouter API calls. OpenRouter is
not affordable right now. Replace those two calls with a headless Claude Code
invocation (`claude -p`), running under the existing Claude subscription rather
than pay-per-token billing. Add tracking, weekly reporting, and adjustable
volume controls so the trial (5 leads/week) can be monitored and scaled safely.

## Non-goals

- No change to `lead_import`, `research`, approval-gate, or Gmail send logic.
- No change to the SO/WO split logic elsewhere in the project.
- Not building a UI — settings are edited via JSON file, reports are markdown.

## Schema change

New table `handoff_log` in the existing SQLite DB (per ADR-001, single source
of truth). Separate table, not merged into `leads`.

```sql
CREATE TABLE handoff_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id         INTEGER NOT NULL REFERENCES leads(id),
    session_id      TEXT,
    started_at      TEXT NOT NULL,       -- ISO 8601
    duration_ms     INTEGER,
    cost_usd        REAL,
    status          TEXT NOT NULL CHECK (status IN
                     ('success','throttled','error')),
    quality_flag    TEXT CHECK (quality_flag IN
                     ('pass','edit_heavy','reject')) DEFAULT NULL,
    error_message   TEXT
);

CREATE INDEX idx_handoff_log_lead_id ON handoff_log(lead_id);
CREATE INDEX idx_handoff_log_started_at ON handoff_log(started_at);
```

Migration file: `migrations/0xx_create_handoff_log.sql` (see companion file).
`quality_flag` is set manually at the existing human approval step — no new
UI, just an extra prompt/field in that step.

## Settings file

`config/handoff_settings.json` — read fresh before every scheduled run, no
code changes needed to adjust volume.

```json
{
  "weekly_lead_cap": 5,
  "daily_lead_cap": 2,
  "min_interval_minutes": 60,
  "run_days": ["Mon", "Wed", "Fri"],
  "use_bare_mode": false
}
```

Scheduler logic before each run:
1. Count `handoff_log` rows where `started_at >= start_of_week` → compare to
   `weekly_lead_cap`. Stop if at/over.
2. Count rows where `started_at >= start_of_day` → compare to
   `daily_lead_cap`. Stop if at/over.
3. Check `min_interval_minutes` since last successful row. Stop if too soon.
4. Check today's weekday is in `run_days`. Stop if not.
5. If all checks pass → proceed to handoff.

## Handoff mechanics

1. Pipeline writes `handoff/lead_<id>.md` — research data + asset_gen/email_draft
   instructions (template: see companion `handoff_template.md`).
2. `run_handoff.bat` invokes:
   ```
   claude -p "Read handoff/lead_<id>.md and follow its instructions exactly.
   Write output to handoff/output_<id>.md" --allowedTools "Read,Write"
   --output-format json > handoff/result_<id>.json
   ```
   (`--bare` appended only if `use_bare_mode: true` in settings.)
3. Python parses `result_<id>.json` → writes `handoff_log` row
   (`cost_usd`, `duration_ms`, `session_id`, `status`).
4. If exit code non-zero or stderr contains a rate-limit indicator → row
   logged with `status: throttled` or `error`, `error_message` populated.
5. `output_<id>.md` content feeds into the existing approval queue as before.

## Weekly report

`scripts/weekly_report.py` — run manually or via a Sunday scheduled task.
Queries `handoff_log` for the past 7 days, writes
`docs/reports/handoff-week-<YYYY-MM-DD>.md` containing:

- Leads processed vs. `weekly_lead_cap`
- Total `cost_usd` (expected $0 — confirms subscription coverage)
- Total `duration_ms`, average per lead
- `quality_flag` breakdown (% pass / edit_heavy / reject)
- Any `throttled`/`error` rows with timestamps and messages
- Recommendation line: "cap headroom used: X%" (simple flag if consistently
  hitting the cap, signal to consider raising it)

## Acceptance criteria

- [ ] Migration runs cleanly against existing DB, no data loss
- [ ] Settings changes take effect without code redeploy
- [ ] A full trial lead run produces exactly one `handoff_log` row
- [ ] Weekly report generates correctly on an empty week (zero leads) without erroring
- [ ] Throttled/error runs do not crash the pipeline — logged and skipped
- [ ] No OpenRouter calls remain in `asset_gen`/`email_draft` code path

## Rollback

Feature is additive — new table, new files, no changes to existing tables or
approval logic. Rollback = drop `handoff_log` table + remove scheduler check
(pipeline reverts to manual/no-op for those two stages).
