-- MIMS ERP v2 — RPC Functions for atomic stock mutations
-- Run this AFTER 001_initial_schema.sql in your Supabase SQL Editor

-- ── Increment RM on_order ────────────────────────────────────────
CREATE OR REPLACE FUNCTION increment_raw_material_on_order(p_rm_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE raw_materials SET on_order = on_order + p_qty
  WHERE id = p_rm_id AND user_id = p_user_id;
END;$$;

-- ── Receive PO item (weighted avg cost + stock) ──────────────────
CREATE OR REPLACE FUNCTION receive_po_item(p_rm_id UUID, p_qty NUMERIC, p_unit_cost NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_stock NUMERIC; v_cost NUMERIC;
BEGIN
  SELECT stock, avg_cost INTO v_stock, v_cost FROM raw_materials WHERE id = p_rm_id AND user_id = p_user_id;
  UPDATE raw_materials SET
    stock    = v_stock + p_qty,
    avg_cost = CASE WHEN (v_stock + p_qty) = 0 THEN 0
                    ELSE (v_stock * v_cost + p_qty * p_unit_cost) / (v_stock + p_qty) END,
    on_order = GREATEST(on_order - p_qty, 0)
  WHERE id = p_rm_id AND user_id = p_user_id;
END;$$;

-- ── Deduct RM stock ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION deduct_raw_material_stock(p_rm_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE raw_materials SET stock = GREATEST(stock - p_qty, 0)
  WHERE id = p_rm_id AND user_id = p_user_id;
END;$$;

-- ── Increment RM demand ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION increment_raw_material_demand(p_rm_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE raw_materials SET demand = demand + p_qty WHERE id = p_rm_id AND user_id = p_user_id;
END;$$;

-- ── Decrement RM demand ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION decrement_raw_material_demand(p_rm_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE raw_materials SET demand = GREATEST(demand - p_qty, 0) WHERE id = p_rm_id AND user_id = p_user_id;
END;$$;

-- ── Increment FG in_production ───────────────────────────────────
CREATE OR REPLACE FUNCTION increment_fg_in_production(p_fg_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE finished_goods SET in_production = in_production + p_qty WHERE id = p_fg_id AND user_id = p_user_id;
END;$$;

-- ── Complete production order (add FG stock, decrement in_production) ─
CREATE OR REPLACE FUNCTION complete_production_order(p_fg_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE finished_goods SET
    stock         = stock + p_qty,
    in_production = GREATEST(in_production - p_qty, 0)
  WHERE id = p_fg_id AND user_id = p_user_id;
END;$$;

-- ── Increment FG demand ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION increment_fg_demand(p_fg_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE finished_goods SET demand = demand + p_qty WHERE id = p_fg_id AND user_id = p_user_id;
END;$$;

-- ── Dispatch FG (deduct stock + demand) ─────────────────────────
CREATE OR REPLACE FUNCTION dispatch_fg(p_fg_id UUID, p_qty NUMERIC, p_user_id UUID)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  UPDATE finished_goods SET
    stock  = GREATEST(stock - p_qty, 0),
    demand = GREATEST(demand - p_qty, 0)
  WHERE id = p_fg_id AND user_id = p_user_id;
END;$$;
