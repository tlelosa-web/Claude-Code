"""
Quick update script: Update ItemListingReport.csv without affecting system quantities.
Run this to refresh item details (descriptions, prices, costs) while preserving stock levels.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sops import create_app, db
from sops.models import Item

def quick_update():
    app = create_app()
    
    with app.app_context():
        csv_path = os.path.join(app.config['BASE_DIR'], 'data', 'ItemListingReport.csv')
        
        if not os.path.exists(csv_path):
            print(f"ERROR: ItemListingReport.csv not found at {csv_path}")
            return
        
        print(f"Updating items from {csv_path}...")
        print("NOTE: Stock quantities will be PRESERVED (not updated from CSV)\n")
        
        from sops.services.item_importer import import_items_from_csv_skip_quantities
        
        try:
            updated_count, inserted_count, skipped_count = import_items_from_csv_skip_quantities(csv_path)
            
            print(f"\n✓ Update complete!")
            print(f"  - {inserted_count} new items inserted")
            print(f"  - {updated_count} existing items updated (quantities preserved)")
            print(f"  - {skipped_count} items skipped (inactive or empty code)")
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    quick_update()
