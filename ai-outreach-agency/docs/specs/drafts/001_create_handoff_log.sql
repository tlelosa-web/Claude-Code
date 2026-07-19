-- Migration: create handoff_log table
-- Purpose: track Claude Code headless handoff calls for asset_gen/email_draft
-- Owner: Tebello Lelosa | ai-outreach-agency
-- Apply: sqlite3 <db_path> < migrations/001_create_handoff_log.sql

BEGIN TRANSACTION;

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

COMMIT;

-- Rollback (manual, run separately if needed):
-- DROP TABLE IF EXISTS handoff_log;
