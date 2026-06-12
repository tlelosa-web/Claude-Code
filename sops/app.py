import os
import sys
from flask import Flask
from sops.config import Config
from sops.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance and upload folders exist
    os.makedirs(app.config.get('INSTANCE_DIR', os.path.join(Config.BASE_DIR, 'instance')), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from sops.routes.dashboard import dashboard_bp
    from sops.routes.items import items_bp
    from sops.routes.sales_orders import sales_orders_bp
    from sops.routes.works_orders import works_orders_bp
    from sops.routes.reports import reports_bp
    from sops.routes.stock_orders import stock_orders_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(sales_orders_bp)
    app.register_blueprint(works_orders_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(stock_orders_bp)

    # Bootstrap database and seed data on first run
    with app.app_context():
        from sops.models import Item
        db.create_all()
        if Item.query.count() == 0:
            csv_path = os.path.join(Config.BASE_DIR, 'data', 'ItemListingReport.csv')
            if os.path.exists(csv_path):
                try:
                    from sops.services.item_importer import import_items_from_csv
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
    app.run(debug=True, host='127.0.0.1', port=5000)
