import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from models import db, Item, StockMovement
from services.item_importer import import_items_from_csv
from services.stock_service import adjust

items_bp = Blueprint('items', __name__)

@items_bp.route('/items')
def catalogue():
    items = Item.query.all()
    # If ajax request for tabulator JSON data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify([{
            'id': item.id,
            'code': item.code,
            'description': item.description,
            'category': item.category,
            'qty_on_hand': item.qty_on_hand,
            'last_cost': f"R {item.last_cost:,.2f}",
            'avg_cost': f"R {item.avg_cost:,.2f}",
            'excl_price': f"R {item.excl_price:,.2f}",
            'incl_price': f"R {item.incl_price:,.2f}",
            'active': 'Yes' if item.active else 'No'
        } for item in items])
        
    return render_template('items/catalogue.html')

@items_bp.route('/items/<int:item_id>')
def detail(item_id):
    item = Item.query.get_or_404(item_id)
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for('items.catalogue'))
        
    # Get stock movements in reverse chronological order
    movements = StockMovement.query.filter_by(item_id=item_id).order_by(StockMovement.created_at.desc()).all()
    return render_template('items/detail.html', item=item, movements=movements)

@items_bp.route('/items/<int:item_id>/adjust', methods=['POST'])
def adjust_stock(item_id):
    item = Item.query.get(item_id)
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for('items.catalogue'))

    try:
        new_qty = float(request.form.get('new_qty', 0.0))
        reason = request.form.get('reason', '').strip()
        adjusted_by = request.form.get('adjusted_by', 'System User').strip() or 'System User'
        
        if not reason:
            flash("An adjustment reason is required.", "error")
            return redirect(url_for('items.detail', item_id=item_id))

        adjust(item_id, new_qty, reason, adjusted_by)
        db.session.commit()
        
        flash(f"Successfully adjusted stock for item {item.code} to {new_qty}.", "success")
    except ValueError as e:
        flash(f"Invalid input: {e}", "error")
    except Exception as e:
        flash(f"Error adjusting stock: {e}", "error")
        
    return redirect(url_for('items.detail', item_id=item_id))

@items_bp.route('/items/import', methods=['GET', 'POST'])
def import_csv():
    if request.method == 'POST':
        # Check if they uploaded a file
        uploaded_file = request.files.get('csv_file')
        
        if uploaded_file and uploaded_file.filename:
            # Save uploaded file
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(file_path)
            
            try:
                updated_count, inserted_count, skipped_count = import_items_from_csv(file_path)
                flash(f"Import complete! {inserted_count} items inserted, {updated_count} items updated, {skipped_count} items skipped (inactive or empty code).", "success")
                return redirect(url_for('items.catalogue'))
            except Exception as e:
                flash(f"Error importing CSV: {str(e)}", "error")
                return redirect(url_for('items.import_csv'))
                
        elif request.form.get('seed_default') == '1':
            # Seed from default file in project directory
            default_path = os.path.join(current_app.config['BASE_DIR'], 'ItemListingReport.csv')
            if not os.path.exists(default_path):
                # Fallback check
                default_path = 'ItemListingReport.csv'
                
            try:
                updated_count, inserted_count, skipped_count = import_items_from_csv(default_path)
                flash(f"Seed complete! {inserted_count} items inserted, {updated_count} items updated, {skipped_count} items skipped.", "success")
                return redirect(url_for('items.catalogue'))
            except Exception as e:
                flash(f"Error seeding default CSV: {str(e)}", "error")
                return redirect(url_for('items.import_csv'))
        else:
            flash("Please choose a file or select to seed the default file.", "error")
            
    return render_template('items/import.html')
