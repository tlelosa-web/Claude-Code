-- Add stock column to items for easier KPI reporting
ALTER TABLE items ADD COLUMN IF NOT EXISTS stock NUMERIC(15,4) DEFAULT 0;
