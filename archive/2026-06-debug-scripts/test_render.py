import sys
sys.path.insert(0, '.')
from app import create_app
from models import db, Item
from routes.works_orders import works_orders_bp
from flask import render_template
from services.doc_generator import get_works_order_print_context
from routes.sales_orders import item_to_bom_json

app = create_app()
with app.app_context():
    context = get_works_order_print_context(9)
    items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
    item_payload = [item_to_bom_json(item) for item in items]
    categories = db.session.query(Item.category).filter(
        Item.active == True, Item.category != None
    ).distinct().order_by(Item.category).all()
    categories = [c[0] for c in categories if c[0]]
    
    print("context keys:", context.keys())
    try:
        render_template('works_orders/edit.html', 
                          **context,
                          items=item_payload,
                          categories=categories)
        print("Success!")
    except Exception as e:
        print("Error:", type(e), e)
