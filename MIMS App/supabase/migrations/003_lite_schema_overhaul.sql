-- MIMS ERP v2 — Phase 1: Lite Schema Overhaul
-- Migration: 003_lite_schema_overhaul.sql

-- ==========================================
-- 1. TYPES & ENUMS
-- ==========================================
DO $$ BEGIN
    CREATE TYPE item_type AS ENUM ('Material', 'Sub-Assembly', 'Product');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ==========================================
-- 2. UNIFIED ITEMS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS items (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  code          TEXT NOT NULL,
  description   TEXT NOT NULL,
  category      TEXT DEFAULT 'Default',
  type          item_type NOT NULL DEFAULT 'Product',
  uom           TEXT DEFAULT 'pcs', -- Unit of Measure
  min_stock     NUMERIC(15,4) DEFAULT 0,
  lead_days     INT DEFAULT 0,
  avg_cost      NUMERIC(15,4) DEFAULT 0, -- Dynamic Material Cost
  sales_price   NUMERIC(15,4) DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, code)
);

ALTER TABLE items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_items" ON items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- 3. LOCATIONS & BATCHES
-- ==========================================
CREATE TABLE IF NOT EXISTS locations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  address    TEXT,
  is_default BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_locations" ON locations
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS inventory_batches (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  item_id      UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  location_id  UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
  batch_number TEXT,
  expiry_date  DATE,
  quantity     NUMERIC(15,4) NOT NULL DEFAULT 0,
  cost_per_unit NUMERIC(15,4) DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE inventory_batches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_inventory_batches" ON inventory_batches
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- 4. RECURSIVE BOMs
-- ==========================================
CREATE TABLE IF NOT EXISTS bom_items (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  parent_item_id   UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  component_item_id UUID NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  qty_per_unit     NUMERIC(15,4) NOT NULL DEFAULT 1,
  CHECK (parent_item_id <> component_item_id)
);

ALTER TABLE bom_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_bom_items_v2" ON bom_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- 5. SHOP FLOOR: WORK CENTERS & TASKS
-- ==========================================
CREATE TABLE IF NOT EXISTS work_centers (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  hourly_rate   NUMERIC(15,2) DEFAULT 0,
  capacity_hours NUMERIC(15,2) DEFAULT 8,
  created_at    TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE work_centers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_work_centers" ON work_centers
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Routings (Template Operations)
CREATE TABLE IF NOT EXISTS routings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  item_id       UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  work_center_id UUID REFERENCES work_centers(id) ON DELETE SET NULL,
  operation_name TEXT NOT NULL,
  sequence_order INT NOT NULL DEFAULT 1,
  standard_time_mins NUMERIC(15,2) DEFAULT 0
);

ALTER TABLE routings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_routings" ON routings
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Production Tasks (Execution)
CREATE TABLE IF NOT EXISTS production_tasks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  production_order_id UUID NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
  work_center_id      UUID REFERENCES work_centers(id) ON DELETE SET NULL,
  operation_name      TEXT NOT NULL,
  sequence_order      INT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'Pending', -- Pending, In Progress, Completed, Paused
  started_at          TIMESTAMPTZ,
  completed_at        TIMESTAMPTZ,
  actual_time_mins    NUMERIC(15,2) DEFAULT 0,
  labor_cost          NUMERIC(15,2) DEFAULT 0
);

ALTER TABLE production_tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_production_tasks" ON production_tasks
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- 6. DATA MIGRATION SCRIPTS (Optional/Temporary)
-- ==========================================
-- Note: This migration assumes a clean start or that we will manually 
-- migrate raw_materials/finished_goods to items. 
-- For v2, we will keep the old tables for compatibility during development 
-- but mark them for deprecation.

-- ==========================================
-- 7. UPDATE PRODUCTION ORDERS
-- ==========================================
-- Add item_id to production_orders to replace finished_good_id
DO $$ BEGIN
    ALTER TABLE production_orders ADD COLUMN item_id UUID REFERENCES items(id);
EXCEPTION
    WHEN duplicate_column THEN null;
END $$;
