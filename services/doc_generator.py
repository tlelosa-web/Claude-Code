from models import WorksOrder, BOMLine, Item, SalesOrder

def get_works_order_print_context(wo_id):
    """
    Assembles all information needed to print a Works Order or Picking List.
    """
    wo = WorksOrder.query.get(wo_id)
    if not wo:
        raise ValueError(f"Works Order with id {wo_id} not found.")
        
    so = SalesOrder.query.get(wo.so_id)
    
    lines_context = []
    total_excl_cost = 0.0
    
    for line in wo.bom_lines:
        item = line.item
        total_cost = line.qty_required * line.unit_cost
        total_excl_cost += total_cost
        
        # Shortfall calculation: qty_required > qty_on_hand
        shortfall = max(0.0, line.qty_required - item.qty_on_hand)
        
        lines_context.append({
            'id': line.id,
            'item_code': item.code,
            'description': item.description,
            'category': item.category,
            'qty_required': line.qty_required,
            'qty_issued': line.qty_issued,
            'unit_cost': line.unit_cost,
            'total_cost': total_cost,
            'qty_on_hand': item.qty_on_hand,
            'shortfall': shortfall,
            'notes': line.notes
        })
        
    return {
        'wo': wo,
        'so': so,
        'lines': lines_context,
        'total_excl_cost': total_excl_cost
    }
