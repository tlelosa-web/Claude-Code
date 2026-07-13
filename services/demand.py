"""Demand-netting service.

Computes `qty_on_order` (inbound from open Purchase Orders) and
`qty_committed` (outstanding demand from open Works/Stock Orders) so
callers can net these against `Item.qty_on_hand` to get a true
`available_qty` for shortfall checks.

See docs/specs/demand-netted-shortfall.md for the formula and rationale.

Bulk (`*_bulk`) variants are the primary API — they run one grouped query
per aggregate and return a `{item_id: qty}` dict, so a caller rendering a
full catalogue page (BOM Builder, Stock Report) can compute this for every
item without N+1 per-item queries. The single-item convenience functions
are built on top of the bulk variants for callers that only need one item.

`get_qty_committed_bulk()` / `get_qty_committed()` accept optional
`exclude_wo_id` / `exclude_sto_id` params so a single order's own
outstanding demand doesn't get counted as "committed" against itself when
computing that same order's shortfall (BOM Builder edit page, WO
print/detail). Catalogue-wide views (Stock Report) leave these unset.
"""
from sqlalchemy import func

from models import (
    db,
    Item,
    PurchaseOrder,
    POLine,
    WorksOrder,
    BOMLine,
    StockOrder,
    StockOrderLine,
)

# PurchaseOrder statuses that no longer represent inbound stock.
_PO_STATUSES_EXCLUDED_FROM_ON_ORDER = ('Received', 'Cancelled')

# PurchaseOrder statuses that still represent an open/inbound order, used
# for the "next PO due" hint (narrower than the on-order exclusion above —
# a Draft PO isn't a committed due date yet).
_PO_STATUSES_OPEN_OR_PARTIAL = ('Open', 'Partially Received')

# WorksOrder statuses that still represent outstanding demand.
_WO_STATUSES_OPEN = ('Open', 'In Progress')

# StockOrder status that still represents outstanding demand.
_STO_STATUS_OPEN = 'Open'


def get_qty_on_order_bulk(item_ids=None):
    """Return {item_id: qty_on_order} across open Purchase Order lines.

    qty_on_order per line = qty_ordered - qty_received, summed per item,
    for PO lines linked to a catalogue item (POLine.item_id is not null)
    whose parent PurchaseOrder is not Received/Cancelled.

    If `item_ids` is given, restricts the query to those items. Items with
    no open PO lines are simply absent from the returned dict (treat as 0).
    """
    query = (
        db.session.query(
            POLine.item_id,
            func.sum(POLine.qty_ordered - POLine.qty_received),
        )
        .join(PurchaseOrder, POLine.po_id == PurchaseOrder.id)
        .filter(POLine.item_id.isnot(None))
        .filter(PurchaseOrder.status.notin_(_PO_STATUSES_EXCLUDED_FROM_ON_ORDER))
    )
    if item_ids is not None:
        query = query.filter(POLine.item_id.in_(item_ids))
    query = query.group_by(POLine.item_id)

    return {item_id: float(qty or 0.0) for item_id, qty in query.all()}


def get_qty_on_order(item_id):
    """Single-item convenience wrapper around get_qty_on_order_bulk().

    Prefer get_qty_on_order_bulk() when computing this for many items
    (e.g. a catalogue page) to avoid N+1 queries.
    """
    return get_qty_on_order_bulk(item_ids=[item_id]).get(item_id, 0.0)


def get_next_po_due_bulk(item_ids=None):
    """Return {item_id: date} of the earliest due_date among that item's
    open/partially-received Purchase Order lines.

    Backs the "on order, due <date>" hint. Items with no open/partial PO
    lines, or whose matching PurchaseOrder.due_date is unset, are absent
    from the returned dict (treat as no known due date).

    If `item_ids` is given, restricts the query to those items.
    """
    query = (
        db.session.query(
            POLine.item_id,
            func.min(PurchaseOrder.due_date),
        )
        .join(PurchaseOrder, POLine.po_id == PurchaseOrder.id)
        .filter(POLine.item_id.isnot(None))
        .filter(PurchaseOrder.status.in_(_PO_STATUSES_OPEN_OR_PARTIAL))
    )
    if item_ids is not None:
        query = query.filter(POLine.item_id.in_(item_ids))
    query = query.group_by(POLine.item_id)

    return {
        item_id: due_date
        for item_id, due_date in query.all()
        if due_date is not None
    }


def get_qty_committed_bulk(item_ids=None, exclude_wo_id=None, exclude_sto_id=None):
    """Return {item_id: qty_committed} across open Works/Stock Order demand.

    Sums two sources per item:
      - Open/In Progress Works Order BOM lines (excluding ASSEMBLY_ITEM
        rows, which are the parent line, not a component demand):
        qty_required - qty_issued.
      - Open Stock Order lines, resolved from item_code to item_id (STO
        lines key by code, matching the lookup pattern used in
        routes/stock_orders.py complete_order()): qty - qty_issued.

    If `item_ids` is given, restricts both queries to those items. Items
    with no open demand are absent from the returned dict (treat as 0).

    `exclude_wo_id` / `exclude_sto_id` omit that specific Works Order's /
    Stock Order's own lines from the sums. Pass these when computing
    committed demand for a SINGLE order's own shortfall (e.g. the BOM
    Builder edit page for that order, or that order's print/detail view) —
    otherwise an order's own outstanding demand for an item gets counted
    as "committed" against itself, producing a false shortfall. Leave both
    None (the default) for catalogue-wide views with no single "current
    order" to exclude (e.g. the Stock Report).
    """
    committed = {}

    # Each line's contribution is floored at 0 before summing (Python-side,
    # not func.sum() on the raw arithmetic) so a hand-edited or
    # partial-reversal row where qty_issued exceeds qty_required/qty can't
    # contribute negative outstanding demand and inflate available_qty.
    wo_query = (
        db.session.query(
            BOMLine.item_id,
            BOMLine.qty_required,
            BOMLine.qty_issued,
        )
        .join(WorksOrder, BOMLine.wo_id == WorksOrder.id)
        .filter(BOMLine.line_type != 'ASSEMBLY_ITEM')
        .filter(WorksOrder.status.in_(_WO_STATUSES_OPEN))
    )
    if item_ids is not None:
        wo_query = wo_query.filter(BOMLine.item_id.in_(item_ids))
    if exclude_wo_id is not None:
        wo_query = wo_query.filter(BOMLine.wo_id != exclude_wo_id)

    for item_id, qty_required, qty_issued in wo_query.all():
        line_qty = max(0.0, (qty_required or 0.0) - (qty_issued or 0.0))
        committed[item_id] = committed.get(item_id, 0.0) + line_qty

    sto_query = (
        db.session.query(
            Item.id,
            StockOrderLine.qty,
            StockOrderLine.qty_issued,
        )
        .select_from(StockOrderLine)
        .join(StockOrder, StockOrderLine.stock_order_id == StockOrder.id)
        .join(Item, Item.code == StockOrderLine.item_code)
        .filter(StockOrder.status == _STO_STATUS_OPEN)
    )
    if item_ids is not None:
        sto_query = sto_query.filter(Item.id.in_(item_ids))
    if exclude_sto_id is not None:
        sto_query = sto_query.filter(StockOrderLine.stock_order_id != exclude_sto_id)

    for item_id, qty, qty_issued in sto_query.all():
        line_qty = max(0.0, (qty or 0.0) - (qty_issued or 0.0))
        committed[item_id] = committed.get(item_id, 0.0) + line_qty

    return committed


def get_qty_committed(item_id, exclude_wo_id=None, exclude_sto_id=None):
    """Single-item convenience wrapper around get_qty_committed_bulk().

    Prefer get_qty_committed_bulk() when computing this for many items
    (e.g. a catalogue page) to avoid N+1 queries.

    See get_qty_committed_bulk() for when to pass exclude_wo_id /
    exclude_sto_id (single-order shortfall contexts).
    """
    return get_qty_committed_bulk(
        item_ids=[item_id],
        exclude_wo_id=exclude_wo_id,
        exclude_sto_id=exclude_sto_id,
    ).get(item_id, 0.0)


def get_available_qty(item_id, exclude_wo_id=None, exclude_sto_id=None):
    """qty_on_hand + qty_on_order - qty_committed for a single item.

    Raises ValueError if the item does not exist.

    `exclude_wo_id` / `exclude_sto_id` are passed straight through to
    get_qty_committed() — see get_qty_committed_bulk() for when to use
    them (single-order shortfall contexts, so an order's own outstanding
    demand isn't counted as committed against itself).
    """
    item = db.session.get(Item, item_id)
    if not item:
        raise ValueError(f"Item with id {item_id} not found.")

    return (
        (item.qty_on_hand or 0.0)
        + get_qty_on_order(item_id)
        - get_qty_committed(
            item_id, exclude_wo_id=exclude_wo_id, exclude_sto_id=exclude_sto_id
        )
    )
