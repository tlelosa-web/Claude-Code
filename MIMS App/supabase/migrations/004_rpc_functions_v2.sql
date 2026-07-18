-- MIMS ERP v2 — RPC Functions (v2 - Lite)
-- migration: 004_rpc_functions_v2.sql

-- ── 1. Recursive BOM Cost Calculation ──────────────────────────
CREATE OR REPLACE FUNCTION get_bom_cost(p_item_id UUID)
RETURNS NUMERIC LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  v_total_cost NUMERIC := 0;
  v_row RECORD;
BEGIN
  -- If the item has no components, return its own avg_cost
  IF NOT EXISTS (SELECT 1 FROM bom_items WHERE parent_item_id = p_item_id) THEN
    SELECT avg_cost INTO v_total_cost FROM items WHERE id = p_item_id;
    RETURN COALESCE(v_total_cost, 0);
  END IF;

  -- Sum up the cost of all components
  FOR v_row IN SELECT component_item_id, qty_per_unit FROM bom_items WHERE parent_item_id = p_item_id LOOP
    v_total_cost := v_total_cost + (get_bom_cost(v_row.component_item_id) * v_row.qty_per_unit);
  END LOOP;

  RETURN v_total_cost;
END;$$;

-- ── 2. Unified Inventory Adjustment (Batch-Aware) ────────────────
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
  -- Upsert batch information
  INSERT INTO inventory_batches (user_id, item_id, location_id, batch_number, quantity, cost_per_unit)
  VALUES (p_user_id, p_item_id, p_location_id, p_batch_number, p_qty, p_cost)
  ON CONFLICT (id) DO UPDATE SET 
    quantity = inventory_batches.quantity + p_qty,
    cost_per_unit = CASE WHEN (inventory_batches.quantity + p_qty) <= 0 THEN p_cost 
                         ELSE (inventory_batches.quantity * inventory_batches.cost_per_unit + p_qty * p_cost) / (inventory_batches.quantity + p_qty) END;

  -- Update global item avg cost (weighted average across all batches)
  UPDATE items SET 
    avg_cost = (SELECT SUM(quantity * cost_per_unit) / NULLIF(SUM(quantity), 0) 
                FROM inventory_batches 
                WHERE item_id = p_item_id AND user_id = p_user_id)
  WHERE id = p_item_id AND user_id = p_user_id;
END;$$;

-- ── 3. Create Production Tasks from Routings ───────────────────
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

-- ── 4. Complete Task & Calculate Labor Cost ────────────────────
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
