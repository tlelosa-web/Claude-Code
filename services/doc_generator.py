from models import db, WorksOrder, BOMLine, Item, SalesOrder
from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk

def get_works_order_print_context(wo_id):
    """
    Assembles information for printing Works Order with nested BOM structure.

    Shortfall is demand-netted (Enhancement 3): qty_on_hand is netted against
    qty_on_order (inbound POs) and qty_committed (outstanding demand from
    other open Works/Stock Orders) before comparing against qty_required.
    See docs/specs/demand-netted-shortfall.md.
    """
    wo = db.session.get(WorksOrder, wo_id)
    if not wo:
        raise ValueError(f"Works Order with id {wo_id} not found.")

    so = db.session.get(SalesOrder, wo.so_id)

    # Query top-level lines only (parent_line_id IS NULL)
    top_lines = BOMLine.query.filter_by(wo_id=wo_id, parent_line_id=None).all()

    # Pre-fetch children for every top-level line so we can collect all item
    # ids up front and run the demand-netting aggregates once for the whole
    # WO, rather than per-line in the loop below.
    children_by_line_id = {
        line.id: BOMLine.query.filter_by(parent_line_id=line.id).all()
        for line in top_lines
        if line.line_type == 'ASSEMBLY_ITEM'
    }

    item_ids = {line.item_id for line in top_lines}
    for children in children_by_line_id.values():
        item_ids.update(child.item_id for child in children)

    qty_on_order = get_qty_on_order_bulk(item_ids=item_ids)
    qty_committed = get_qty_committed_bulk(item_ids=item_ids, exclude_wo_id=wo_id)

    assembly_items = []
    flat_lines = []

    for line in top_lines:
        item = line.item
        available_qty = (
            (item.qty_on_hand or 0.0)
            + qty_on_order.get(item.id, 0.0)
            - qty_committed.get(item.id, 0.0)
        )
        shortfall = max(0.0, line.qty_required - available_qty)

        line_dict = {
            'id': line.id,
            'item_code': item.code,
            'description': item.description,
            'category': item.category,
            'qty_required': line.qty_required,
            'qty_issued': line.qty_issued,
            'qty_on_hand': item.qty_on_hand,
            'qty_on_order': qty_on_order.get(item.id, 0.0),
            'qty_committed': qty_committed.get(item.id, 0.0),
            'available_qty': available_qty,
            'shortfall': shortfall,
            'notes': line.notes,
            'line_type': line.line_type
        }

        if line.line_type == 'ASSEMBLY_ITEM':
            children = children_by_line_id.get(line.id, [])
            components = []
            for child in children:
                child_item = child.item
                child_available_qty = (
                    (child_item.qty_on_hand or 0.0)
                    + qty_on_order.get(child_item.id, 0.0)
                    - qty_committed.get(child_item.id, 0.0)
                )
                child_shortfall = max(0.0, child.qty_required - child_available_qty)
                components.append({
                    'id': child.id,
                    'item_code': child_item.code,
                    'description': child_item.description,
                    'category': child_item.category,
                    'qty_required': child.qty_required,
                    'qty_issued': child.qty_issued,
                    'qty_on_hand': child_item.qty_on_hand,
                    'qty_on_order': qty_on_order.get(child_item.id, 0.0),
                    'qty_committed': qty_committed.get(child_item.id, 0.0),
                    'available_qty': child_available_qty,
                    'shortfall': child_shortfall,
                    'notes': child.notes,
                    'line_type': child.line_type
                })
            line_dict['components'] = components
            assembly_items.append(line_dict)
        else:
            flat_lines.append(line_dict)

    return {
        'wo': wo,
        'so': so,
        'assembly_items': assembly_items,
        'flat_lines': flat_lines
    }
