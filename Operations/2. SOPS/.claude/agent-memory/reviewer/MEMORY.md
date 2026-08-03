# Reviewer Memory Index

- [Shortfall calc duplication](pattern_shortfall_duplication.md) — availability/shortfall math is copy-pasted across many call sites; each new feature tends to add another un-netted copy.
- [STO item_code join pattern](pattern_sto_item_code_join.md) — StockOrderLine keys by item_code (string), not item_id; recurring join/lookup pattern to verify each time.
- [qty_on_hand None-guard drift](pattern_qty_on_hand_none_guard.md) — inline availability calcs skip the `or 0.0` guard that the service layer uses; latent crash on NULL qty_on_hand.
- [Handler/template guard drift](pattern_handler_guard_drift.md) — sibling order-transition handlers guard status inconsistently; shared templates miss context vars on one render path.
