from models import WorksOrder, BOMLine, Item, SalesOrder

def get_works_order_print_context(wo_id):
    """
    Assembles information for printing Works Order with nested BOM structure.
    """
    wo = WorksOrder.query.get(wo_id)
    if not wo:
        raise ValueError(f"Works Order with id {wo_id} not found.")
    
    so = SalesOrder.query.get(wo.so_id)
    
    # Query top-level lines only (parent_line_id IS NULL)
    top_lines = BOMLine.query.filter_by(wo_id=wo_id, parent_line_id=None).all()
    
    assembly_items = []
    flat_lines = []
    
    for line in top_lines:
        item = line.item
        shortfall = max(0.0, line.qty_required - item.qty_on_hand)
        
        line_dict = {
            'id': line.id,
            'item_code': item.code,
            'description': item.description,
            'category': item.category,
            'qty_required': line.qty_required,
            'qty_issued': line.qty_issued,
            'qty_on_hand': item.qty_on_hand,
            'shortfall': shortfall,
            'notes': line.notes,
            'line_type': line.line_type
        }
        
        if line.line_type == 'ASSEMBLY_ITEM':
            # Fetch children
            children = BOMLine.query.filter_by(parent_line_id=line.id).all()
            components = []
            for child in children:
                child_item = child.item
                child_shortfall = max(0.0, child.qty_required - child_item.qty_on_hand)
                components.append({
                    'id': child.id,
                    'item_code': child_item.code,
                    'description': child_item.description,
                    'category': child_item.category,
                    'qty_required': child.qty_required,
                    'qty_issued': child.qty_issued,
                    'qty_on_hand': child_item.qty_on_hand,
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
