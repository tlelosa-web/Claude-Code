from datetime import datetime
from models import db, Item, WorksOrder, BOMLine, SalesOrder

def generate_wo_number():
    """
    Generates a Works Order number in format: WO-YYYYMMDD-NNN
    """
    today_str = datetime.utcnow().strftime('%Y%m%d')
    prefix = f"WO-{today_str}-"
    
    # Query works orders created today matching this prefix pattern
    today_wos = WorksOrder.query.filter(WorksOrder.wo_number.like(f"{prefix}%")).all()
    
    # Extract numbers and find max
    max_num = 0
    for wo in today_wos:
        try:
            num_part = int(wo.wo_number.split('-')[-1])
            if num_part > max_num:
                max_num = num_part
        except (ValueError, IndexError):
            continue
            
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"

def create_works_order_or_picking_list(so_id, order_type, items_list, issued_by="System"):
    """
    Creates a WorksOrder (ASSEMBLY or STOCK) and associated BOMLines.
    
    items_list supports two formats:
    1. Flat: [{'item_id': int, 'qty_required': float, 'notes': str}]
    2. Nested: [{'item_id': int, 'qty_required': float, 'line_type': 'ASSEMBLY_ITEM', 
                 'notes': str, 'components': [...]}]
    """
    so = SalesOrder.query.get(so_id)
    if not so:
        raise ValueError(f"Sales Order with id {so_id} not found.")

    wo_number = generate_wo_number()
    
    wo = WorksOrder(
        wo_number=wo_number,
        so_id=so_id,
        order_type=order_type, # 'ASSEMBLY' or 'STOCK'
        status='Open',
        issued_by=issued_by,
        created_at=datetime.utcnow()
    )
    
    db.session.add(wo)
    db.session.flush() # Populate wo.id
    
    for item_data in items_list:
        item_id = item_data['item_id']
        qty_required = float(item_data['qty_required'])
        notes = item_data.get('notes', '')
        line_type = item_data.get('line_type', 'COMPONENT')
        components = item_data.get('components', [])
        
        item = Item.query.get(item_id)
        if not item:
            raise ValueError(f"Item with id {item_id} not found.")
            
        # Unit cost is average cost if set, else last cost
        unit_cost = item.avg_cost if item.avg_cost > 0 else item.last_cost
        
        # Create parent line (ASSEMBLY_ITEM or COMPONENT)
        bom_line = BOMLine(
            wo_id=wo.id,
            item_id=item_id,
            qty_required=qty_required,
            qty_issued=0.0,
            unit_cost=unit_cost,
            notes=notes,
            line_type=line_type
        )
        db.session.add(bom_line)
        db.session.flush()  # Get bom_line.id
        
        # If this is an assembly item with components, create child lines
        if line_type == 'ASSEMBLY_ITEM' and components:
            for comp_data in components:
                comp_item = Item.query.get(comp_data['item_id'])
                if not comp_item:
                    raise ValueError(f"Component item with id {comp_data['item_id']} not found.")
                
                comp_unit_cost = comp_item.avg_cost if comp_item.avg_cost > 0 else comp_item.last_cost
                
                comp_line = BOMLine(
                    wo_id=wo.id,
                    item_id=comp_data['item_id'],
                    qty_required=float(comp_data['qty_required']),
                    qty_issued=0.0,
                    unit_cost=comp_unit_cost,
                    notes=comp_data.get('notes', ''),
                    line_type='COMPONENT',
                    parent_line_id=bom_line.id
                )
                db.session.add(comp_line)
    
    db.session.commit()
    return wo
