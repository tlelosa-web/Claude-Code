import sys
sys.path.insert(0, '.')
from app import create_app
from models import db, SalesOrder, WorksOrder, BOMLine, StockOrder, StockOrderLine, SOLineItem, Item

app = create_app()
with app.app_context():
    so = SalesOrder.query.get(5)
    print("SO: {} | Status: {} | Customer: {}".format(so.so_number, so.status, so.customer_name))

    wos = WorksOrder.query.filter_by(so_id=5).all()
    print("\nWorks Orders for SO5 ({} total):".format(len(wos)))
    for wo in wos:
        bom_lines = BOMLine.query.filter_by(wo_id=wo.id).all()
        print("  WO id={} | {} | status={}".format(wo.id, wo.wo_number, wo.status))
        for bl in bom_lines:
            item = Item.query.get(bl.item_id)
            code = item.code if item else "MISSING"
            print("    BOM line: item_id={} | code={} | qty={}".format(bl.item_id, code, bl.qty_required))

    stos = StockOrder.query.filter_by(so_id=5).all()
    print("\nStock Orders for SO5 ({} total):".format(len(stos)))
    for sto in stos:
        lines = StockOrderLine.query.filter_by(stock_order_id=sto.id).all()
        print("  STO id={} | {} | status={} | lines={}".format(sto.id, sto.stock_order_number, sto.status, len(lines)))
        for sl in lines:
            print("    Line: {} | {} | qty={}".format(sl.item_code, sl.description[:50], sl.qty))

    print("\nSO5 line items:")
    items = SOLineItem.query.filter_by(so_id=5).order_by(SOLineItem.id).all()
    for li in items:
        print("  line_id={} | {}".format(li.id, li.description[:70]))
