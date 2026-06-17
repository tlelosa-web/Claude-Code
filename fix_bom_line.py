import sys
sys.path.insert(0, '.')
from app import create_app
from models import db, BOMLine, Item

app = create_app()
with app.app_context():
    # BOMLine id=32 currently has item_id=1290 (C500x400NH)
    # Correct item is id=1289 (C500x400 - Casing Size 500diamx400)
    bom_line = db.session.get(BOMLine, 32)
    if not bom_line:
        print("ERROR: BOMLine id=32 not found")
        sys.exit(1)

    old_item = db.session.get(Item, bom_line.item_id)
    new_item = db.session.get(Item, 1289)

    print("Before: BOMLine id={} | item_id={} | code={} | qty={}".format(
        bom_line.id, bom_line.item_id, old_item.code if old_item else '?', bom_line.qty_required))
    print("New item: id={} | code={} | description={}".format(
        new_item.id, new_item.code, new_item.description))

    # Apply the fix
    bom_line.item_id = 1289
    bom_line.unit_cost = new_item.last_cost or 0.0
    db.session.commit()

    # Verify
    db.session.refresh(bom_line)
    verify_item = db.session.get(Item, bom_line.item_id)
    print("After:  BOMLine id={} | item_id={} | code={} | unit_cost={} | qty={}".format(
        bom_line.id, bom_line.item_id, verify_item.code, bom_line.unit_cost, bom_line.qty_required))
    print("OK - BOM line corrected.")
