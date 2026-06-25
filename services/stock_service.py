from datetime import datetime, timezone
from models import db, Item, StockMovement

def issue(item_id, qty, reference, notes="", created_by="System"):
    """
    Deducts stock and records an ISSUE stock movement.
    qty should be positive; it is stored as a negative qty_change.
    """
    item = db.session.get(Item, item_id)
    if not item:
        raise ValueError(f"Item with id {item_id} not found.")

    item.qty_on_hand -= qty
    
    movement = StockMovement(
        item_id=item_id,
        movement_type='ISSUE',
        reference=reference,
        qty_change=-float(qty),
        qty_after=float(item.qty_on_hand),
        notes=notes,
        created_by=created_by,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(movement)
    return item

def receipt(item_id, qty, reference, notes="", created_by="System"):
    """
    Adds stock and records a RECEIPT stock movement.
    """
    item = db.session.get(Item, item_id)
    if not item:
        raise ValueError(f"Item with id {item_id} not found.")

    item.qty_on_hand += qty
    
    movement = StockMovement(
        item_id=item_id,
        movement_type='RECEIPT',
        reference=reference,
        qty_change=float(qty),
        qty_after=float(item.qty_on_hand),
        notes=notes,
        created_by=created_by,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(movement)
    return item

def adjust(item_id, new_qty, reason, adjusted_by="System"):
    """
    Adjusts stock directly to a new quantity and records an ADJUSTMENT stock movement.
    """
    item = db.session.get(Item, item_id)
    if not item:
        raise ValueError(f"Item with id {item_id} not found.")

    old_qty = item.qty_on_hand
    qty_change = new_qty - old_qty
    
    item.qty_on_hand = new_qty
    
    movement = StockMovement(
        item_id=item_id,
        movement_type='ADJUSTMENT',
        reference='Adjustment',
        qty_change=float(qty_change),
        qty_after=float(new_qty),
        notes=reason,
        created_by=adjusted_by,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(movement)
    return item
