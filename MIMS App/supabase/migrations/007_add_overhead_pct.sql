-- Add overhead percentage for simple cost absorption in Lite
ALTER TABLE work_centers ADD COLUMN IF NOT EXISTS overhead_pct NUMERIC(15,2) DEFAULT 0;
