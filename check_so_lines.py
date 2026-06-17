from sops.app import create_app
from models import db, SalesOrder, SOLineItem

app = create_app()
with app.app_context():
    so = SalesOrder.query.filter_by(so_number='SO4652').first()
    if so:
        print(f"SO4652 ID: {so.id}")
        print(f"Line items:")
        for line in so.line_items:
            print(f"  Line ID {line.id}: {line.description[:50]}...")
    else:
        print("SO4652 not found")
