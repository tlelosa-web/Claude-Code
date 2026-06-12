import os
import sys
from flask import Flask
from sqlalchemy import text
from config import Config
from models import db

def ensure_schema_columns():
    """Apply tiny SQLite-compatible schema upgrades for existing local DBs."""
    inspector = db.inspect(db.engine)
    if 'sales_order' not in inspector.get_table_names():
        return

    columns = {column['name'] for column in inspector.get_columns('sales_order')}
    if 'job_numbers' not in columns:
        db.session.execute(text('ALTER TABLE sales_order ADD COLUMN job_numbers VARCHAR(255)'))
        db.session.commit()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure instance and upload folders exist
    os.makedirs(app.config['INSTANCE_DIR'] if hasattr(app.config, 'INSTANCE_DIR') else 
                os.path.join(Config.BASE_DIR, 'instance'), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.items import items_bp
    from routes.sales_orders import sales_orders_bp
    from routes.works_orders import works_orders_bp
    from routes.reports import reports_bp
    from routes.stock_orders import stock_orders_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(sales_orders_bp)
    app.register_blueprint(works_orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(stock_orders_bp)
    
    # Bootstrap database and seed data on first run
    with app.app_context():
        from models import Item
        db.create_all()
        ensure_schema_columns()
        
        if Item.query.count() == 0:
            # Auto-import from CSV if it exists
            csv_path = os.path.join(Config.BASE_DIR, 'data', 'ItemListingReport.csv')
            if os.path.exists(csv_path) and not app.config.get('TESTING'):
                try:
                    from services.item_importer import import_items_from_csv
                    updated, inserted, skipped = import_items_from_csv(csv_path)
                    print("OK Database initialised at instance/sops.db")
                    print(f"OK Imported {inserted + updated} items from ItemListingReport.csv ({inserted} new, {updated} updated, {skipped} skipped)")
                except Exception as e:
                    print(f"Warning: CSV import failed: {e}")
            else:
                print("No ItemListingReport.csv found. Run with sample data or import manually.")
        
        print("Running at http://127.0.0.1:5000")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
