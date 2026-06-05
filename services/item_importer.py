import os
import pandas as pd
from datetime import datetime
from models import db, Item, StockMovement

def clean_currency(val):
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).replace('R', '').replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def clean_qty(val):
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def import_items_from_csv(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    # Read CSV skipping the first row (sep=,)
    df = pd.read_csv(csv_path, skiprows=1)

    updated_count = 0
    inserted_count = 0
    skipped_count = 0

    for _, row in df.iterrows():
        active_val = str(row.get('Active', '')).strip().lower()
        if active_val != 'yes':
            skipped_count += 1
            continue

        code = str(row.get('Code', '')).strip()
        if not code:
            skipped_count += 1
            continue

        desc = str(row.get('Description', '')).strip()
        category = str(row.get('Category', '')).strip()
        if pd.isna(row.get('Category')):
            category = None

        last_cost = clean_currency(row.get('Last Cost', 0.0))
        avg_cost = clean_currency(row.get('Avg. Cost', 0.0))
        excl_price = clean_currency(row.get('Excl. Price', 0.0))
        incl_price = clean_currency(row.get('Incl. Price', 0.0))
        qty_on_hand = clean_qty(row.get('Qty on Hand', 0.0))

        # Check if item already exists
        item = Item.query.filter_by(code=code).first()
        
        if item:
            old_qty = item.qty_on_hand
            qty_diff = qty_on_hand - old_qty
            
            # Update fields
            item.description = desc
            item.category = category
            item.last_cost = last_cost
            item.avg_cost = avg_cost
            item.excl_price = excl_price
            item.incl_price = incl_price
            item.qty_on_hand = qty_on_hand
            item.active = True
            
            if qty_diff != 0:
                # Record OPENING movement
                movement = StockMovement(
                    item_id=item.id,
                    movement_type='OPENING',
                    reference='System Import',
                    qty_change=qty_diff,
                    qty_after=qty_on_hand,
                    notes=f"Stock updated via CSV import from {old_qty} to {qty_on_hand}",
                    created_by='System',
                    created_at=datetime.utcnow()
                )
                db.session.add(movement)
            
            updated_count += 1
        else:
            # Create new item
            new_item = Item(
                code=code,
                description=desc,
                category=category,
                last_cost=last_cost,
                avg_cost=avg_cost,
                excl_price=excl_price,
                incl_price=incl_price,
                qty_on_hand=qty_on_hand,
                active=True,
                updated_at=datetime.utcnow()
            )
            db.session.add(new_item)
            db.session.flush()  # Get new_item.id

            # Record OPENING movement if quantity is not zero
            if qty_on_hand != 0:
                movement = StockMovement(
                    item_id=new_item.id,
                    movement_type='OPENING',
                    reference='System Import',
                    qty_change=qty_on_hand,
                    qty_after=qty_on_hand,
                    notes=f"Initial import of item with quantity {qty_on_hand}",
                    created_by='System',
                    created_at=datetime.utcnow()
                )
                db.session.add(movement)

            inserted_count += 1

        if (inserted_count + updated_count) % 100 == 0:
            db.session.commit()

    db.session.commit()
    return updated_count, inserted_count, skipped_count
