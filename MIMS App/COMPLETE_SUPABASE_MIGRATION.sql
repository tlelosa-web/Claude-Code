-- MIMS ERP v2 — Complete Initial Schema & RPC Migration (Unified Items & Traceability)
-- Copy this ENTIRE FILE and run it in your Supabase SQL Editor

-- ==========================================
-- PART 0: TYPES & ENUMS
-- ==========================================
DO $$ BEGIN
    CREATE TYPE item_type AS ENUM ('Material', 'Sub-Assembly', 'Product');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ==========================================
-- PART 1: CORE INFRASTRUCTURE
-- ==========================================

-- ── 1. Suppliers ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  contact    TEXT,
  email      TEXT,
  phone      TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_suppliers" ON suppliers;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_suppliers" ON suppliers
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 2. Customers ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  contact    TEXT,
  email      TEXT,
  city       TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_customers" ON customers;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_customers" ON customers
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 3. Locations ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS locations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  address    TEXT,
  is_default BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_locations" ON locations;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_locations" ON locations
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- PART 2: UNIFIED ITEMS & INVENTORY
-- ==========================================

-- ── 1. Unified Items ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS items (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  code          TEXT NOT NULL,
  description   TEXT NOT NULL,
  category      TEXT DEFAULT 'Default',
  type          item_type NOT NULL DEFAULT 'Product',
  uom           TEXT DEFAULT 'pcs',
  min_stock     NUMERIC(15,4) DEFAULT 0,
  on_order      NUMERIC(15,4) DEFAULT 0,
  demand        NUMERIC(15,4) DEFAULT 0,
  stock         NUMERIC(15,4) DEFAULT 0,
  lead_days     INT DEFAULT 0,
  avg_cost      NUMERIC(15,4) DEFAULT 0,
  sales_price   NUMERIC(15,4) DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, code)
);
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_items" ON items;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_items" ON items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 2. Inventory Batches ────────────────────────────────────────
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
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_inventory_batches" ON inventory_batches;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_inventory_batches" ON inventory_batches
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 3. Recursive BOMs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom_items (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  parent_item_id   UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  component_item_id UUID NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  qty_per_unit     NUMERIC(15,4) NOT NULL DEFAULT 1,
  CHECK (parent_item_id <> component_item_id)
);
ALTER TABLE bom_items ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_bom_items" ON bom_items;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_bom_items" ON bom_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- PART 3: ORDERS & SHOP FLOOR
-- ==========================================

-- ── 1. Purchase Orders ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS purchase_orders (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  order_number TEXT NOT NULL,
  supplier_id  UUID REFERENCES suppliers(id) ON DELETE SET NULL,
  status       TEXT NOT NULL DEFAULT 'Ordered',
  delivery_date DATE,
  total        NUMERIC(15,2) DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_purchase_orders" ON purchase_orders;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_purchase_orders" ON purchase_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS po_items (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
  item_id           UUID REFERENCES items(id) ON DELETE SET NULL, -- Upgraded from raw_material_id
  quantity          NUMERIC(15,4) NOT NULL,
  unit_cost         NUMERIC(15,4) NOT NULL DEFAULT 0
);
ALTER TABLE po_items ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_po_items" ON po_items;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_po_items" ON po_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 2. Production Orders ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS production_orders (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  order_number     TEXT NOT NULL,
  item_id          UUID REFERENCES items(id) ON DELETE SET NULL, -- Upgraded from finished_good_id
  quantity         NUMERIC(15,4) NOT NULL,
  status           TEXT NOT NULL DEFAULT 'Pending',
  due_date         DATE,
  created_at       TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE production_orders ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_production_orders" ON production_orders;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_production_orders" ON production_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 3. Work Centers & Routings ──────────────────────────────────
CREATE TABLE IF NOT EXISTS work_centers (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  hourly_rate   NUMERIC(15,2) DEFAULT 0,
  capacity_hours NUMERIC(15,2) DEFAULT 8,
  created_at    TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE work_centers ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_work_centers" ON work_centers;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_work_centers" ON work_centers
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

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
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_routings" ON routings;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_routings" ON routings
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 4. Production Tasks (Execution) ─────────────────────────────
CREATE TABLE IF NOT EXISTS production_tasks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  production_order_id UUID NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
  work_center_id      UUID REFERENCES work_centers(id) ON DELETE SET NULL,
  operation_name      TEXT NOT NULL,
  sequence_order      INT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'Pending',
  started_at          TIMESTAMPTZ,
  completed_at        TIMESTAMPTZ,
  actual_time_mins    NUMERIC(15,2) DEFAULT 0,
  labor_cost          NUMERIC(15,2) DEFAULT 0
);
ALTER TABLE production_tasks ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_production_tasks" ON production_tasks;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_production_tasks" ON production_tasks
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 5. Sales Orders ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales_orders (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  order_number  TEXT NOT NULL,
  customer_id   UUID REFERENCES customers(id) ON DELETE SET NULL,
  status        TEXT NOT NULL DEFAULT 'Confirmed',
  delivery_date DATE,
  created_at    TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE sales_orders ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_sales_orders" ON sales_orders;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_sales_orders" ON sales_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS so_items (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sales_order_id   UUID NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
  item_id          UUID REFERENCES items(id) ON DELETE SET NULL, -- Upgraded
  quantity         NUMERIC(15,4) NOT NULL,
  unit_price       NUMERIC(15,4) NOT NULL DEFAULT 0
);
ALTER TABLE so_items ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    DROP POLICY IF EXISTS "user_so_items" ON so_items;
EXCEPTION WHEN undefined_object THEN null; END $$;
CREATE POLICY "user_so_items" ON so_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ==========================================
-- PART 4: RPC FUNCTIONS
-- ==========================================

-- ── Recursive BOM Cost ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_bom_cost(p_item_id UUID)
RETURNS NUMERIC LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_total_cost NUMERIC := 0;
  v_row RECORD;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM bom_items WHERE parent_item_id = p_item_id) THEN
    SELECT avg_cost INTO v_total_cost FROM items WHERE id = p_item_id;
    RETURN COALESCE(v_total_cost, 0);
  END IF;
  FOR v_row IN SELECT component_item_id, qty_per_unit FROM bom_items WHERE parent_item_id = p_item_id LOOP
    v_total_cost := v_total_cost + (get_bom_cost(v_row.component_item_id) * v_row.qty_per_unit);
  END LOOP;
  RETURN v_total_cost;
END;$$;

-- ── Inventory Adjustment (Batch-Aware) ──────────────────────────
CREATE OR REPLACE FUNCTION adjust_inventory(
  p_item_id UUID, 
  p_location_id UUID, 
  p_batch_number TEXT, 
  p_qty NUMERIC, 
  p_cost NUMERIC,
  p_user_id UUID
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO inventory_batches (user_id, item_id, location_id, batch_number, quantity, cost_per_unit)
  VALUES (p_user_id, p_item_id, p_location_id, p_batch_number, p_qty, p_cost)
  ON CONFLICT (id) DO UPDATE SET 
    quantity = inventory_batches.quantity + p_qty,
    cost_per_unit = CASE WHEN (inventory_batches.quantity + p_qty) <= 0 THEN p_cost 
                         ELSE (inventory_batches.quantity * inventory_batches.cost_per_unit + p_qty * p_cost) / (inventory_batches.quantity + p_qty) END;

  UPDATE items SET 
    stock    = (SELECT SUM(quantity) FROM inventory_batches WHERE item_id = p_item_id AND user_id = p_user_id),
    avg_cost = (SELECT SUM(quantity * cost_per_unit) / NULLIF(SUM(quantity), 0) 
                FROM inventory_batches 
                WHERE item_id = p_item_id AND user_id = p_user_id)
  WHERE id = p_item_id AND user_id = p_user_id;
END;$$;

-- ── Create Production Tasks ──────────────────────────────────────
CREATE OR REPLACE FUNCTION create_production_tasks(p_production_order_id UUID, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_item_id UUID;
BEGIN
  SELECT item_id INTO v_item_id FROM production_orders WHERE id = p_production_order_id AND user_id = p_user_id;
  INSERT INTO production_tasks (user_id, production_order_id, work_center_id, operation_name, sequence_order)
  SELECT p_user_id, p_production_order_id, work_center_id, operation_name, sequence_order
  FROM routings
  WHERE item_id = v_item_id AND user_id = p_user_id;
END;$$;

-- ── Complete Task ────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION complete_production_task(p_task_id UUID, p_actual_mins NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_wc_id UUID;
  v_rate NUMERIC;
BEGIN
  SELECT work_center_id INTO v_wc_id FROM production_tasks WHERE id = p_task_id AND user_id = p_user_id;
  SELECT hourly_rate INTO v_rate FROM work_centers WHERE id = v_wc_id AND user_id = p_user_id;
  UPDATE production_tasks SET
    status = 'Completed',
    actual_time_mins = p_actual_mins,
    labor_cost = (p_actual_mins / 60) * COALESCE(v_rate, 0),
    completed_at = now()
  WHERE id = p_task_id AND user_id = p_user_id;
END;$$;

-- ── Modify Item Stats (Demand/Order) ─────────────────────────────
CREATE OR REPLACE FUNCTION modify_item_stats(
  p_item_id UUID,
  p_demand_delta NUMERIC DEFAULT 0,
  p_order_delta NUMERIC DEFAULT 0
)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE items SET 
    demand = GREATEST(0, demand + p_demand_delta),
    on_order = GREATEST(0, on_order + p_order_delta)
  WHERE id = p_item_id;
END;$$;
