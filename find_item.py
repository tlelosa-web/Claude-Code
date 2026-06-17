import sys
sys.path.insert(0, '.')
from app import create_app
from models import db, Item, BOMLine, WorksOrder

app = create_app()
with app.app_context():
    # Find all items whose code starts with C500x400
    items = Item.query.filter(Item.code.like('C500x400%')).order_by(Item.code).all()
    print("Items matching C500x400*:")
    for i in items:
        print("  id={} | code={} | description={} | active={}".format(i.id, i.code, i.description, i.active))

    print()
    # Also exact match
    exact = Item.query.filter_by(code='C500x400').first()
    if exact:
        print("Exact match C500x400: id={} | {}".format(exact.id, exact.description))
    else:
        print("No exact match for C500x400")

    print()
    # Show current BOM lines for WO id=9
    wo = WorksOrder.query.get(9)
    print("WO: {} | id={}".format(wo.wo_number, wo.id))
    bom_lines = BOMLine.query.filter_by(wo_id=9).all()
    for bl in bom_lines:
        item = Item.query.get(bl.item_id)
        print("  BOMLine id={} | item_id={} | code={} | qty={}".format(
            bl.id, bl.item_id, item.code if item else 'MISSING', bl.qty_required))
