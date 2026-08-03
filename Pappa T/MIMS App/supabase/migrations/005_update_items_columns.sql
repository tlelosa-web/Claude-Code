-- Add on_order and demand to items for easier tracking
ALTER TABLE items ADD COLUMN IF NOT EXISTS on_order NUMERIC(15,4) DEFAULT 0;
ALTER TABLE items ADD COLUMN IF NOT EXISTS demand NUMERIC(15,4) DEFAULT 0;
