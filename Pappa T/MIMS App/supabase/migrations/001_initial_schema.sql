-- MIMS ERP v2 — Initial Schema Migration
-- Run this in your Supabase SQL Editor

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
CREATE POLICY "user_customers" ON customers
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 3. Raw Materials ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw_materials (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  code        TEXT NOT NULL,
  description TEXT NOT NULL,
  category    TEXT DEFAULT 'Default',
  supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
  stock       NUMERIC(15,4) DEFAULT 0,
  demand      NUMERIC(15,4) DEFAULT 0,
  min_stock   NUMERIC(15,4) DEFAULT 0,
  on_order    NUMERIC(15,4) DEFAULT 0,
  lead_days   INT DEFAULT 0,
  avg_cost    NUMERIC(15,4) DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE raw_materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_raw_materials" ON raw_materials
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 4. Finished Goods ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS finished_goods (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  code          TEXT NOT NULL,
  description   TEXT NOT NULL,
  category      TEXT DEFAULT 'Default',
  stock         NUMERIC(15,4) DEFAULT 0,
  demand        NUMERIC(15,4) DEFAULT 0,
  min_stock     NUMERIC(15,4) DEFAULT 0,
  in_production NUMERIC(15,4) DEFAULT 0,
  lead_days     INT DEFAULT 0,
  sales_price   NUMERIC(15,4) DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE finished_goods ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_finished_goods" ON finished_goods
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 5. BOM Items ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom_items (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  finished_good_id UUID NOT NULL REFERENCES finished_goods(id) ON DELETE CASCADE,
  raw_material_id  UUID NOT NULL REFERENCES raw_materials(id) ON DELETE RESTRICT,
  qty_per_unit     NUMERIC(15,4) NOT NULL DEFAULT 1
);
ALTER TABLE bom_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_bom_items" ON bom_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 6. Purchase Orders ──────────────────────────────────────────
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
CREATE POLICY "user_purchase_orders" ON purchase_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 7. PO Items ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS po_items (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
  raw_material_id   UUID REFERENCES raw_materials(id) ON DELETE SET NULL,
  quantity          NUMERIC(15,4) NOT NULL,
  unit_cost         NUMERIC(15,4) NOT NULL DEFAULT 0
);
ALTER TABLE po_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_po_items" ON po_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 8. Production Orders ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS production_orders (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  order_number     TEXT NOT NULL,
  finished_good_id UUID REFERENCES finished_goods(id) ON DELETE SET NULL,
  quantity         NUMERIC(15,4) NOT NULL,
  status           TEXT NOT NULL DEFAULT 'Pending',
  due_date         DATE,
  created_at       TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE production_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_production_orders" ON production_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 9. Sales Orders ─────────────────────────────────────────────
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
CREATE POLICY "user_sales_orders" ON sales_orders
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- ── 10. SO Items ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS so_items (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sales_order_id   UUID NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
  finished_good_id UUID REFERENCES finished_goods(id) ON DELETE SET NULL,
  quantity         NUMERIC(15,4) NOT NULL,
  unit_price       NUMERIC(15,4) NOT NULL DEFAULT 0
);
ALTER TABLE so_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_so_items" ON so_items
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
