import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from models import db, SalesOrder, WorksOrder

app = create_app()

with app.app_context():
    sales_orders = SalesOrder.query.all()
    updated_count = 0
    
    for so in sales_orders:
        wos = WorksOrder.query.filter_by(so_id=so.id).all()
        
        if wos:
            all_complete = all(wo.status in ['Complete', 'Cancelled'] for wo in wos)
            has_any_complete = any(wo.status == 'Complete' for wo in wos)
            
            if all_complete and has_any_complete and so.status != 'Complete':
                old_status = so.status
                so.status = 'Complete'
                updated_count += 1
                print(f'Updated SO {so.so_number}: {old_status} -> Complete')
    
    db.session.commit()
    print(f'\nFixed {updated_count} Sales Order(s)')
    print('Done!')
