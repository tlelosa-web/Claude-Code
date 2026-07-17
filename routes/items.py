import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from models import db, Item, StockMovement
from services.item_importer import import_items_from_csv
from services.po_by_item_importer import import_supplier_lead_time_from_csv
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
            'last_cost': f"R {item.last_cost or 0:,.2f}",
            'avg_cost': f"R {item.avg_cost or 0:,.2f}",
            'excl_price': f"R {item.excl_price or 0:,.2f}",
            'incl_price': f"R {item.incl_price or 0:,.2f}",
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
    item = db.session.get(Item, item_id)
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

@items_bp.route('/items/<int:item_id>/reorder-settings', methods=['POST'])
def update_reorder_settings(item_id):
    """Set Item.reorder_point/reorder_qty/max_level (Enhancement 2 - reorder
    point signals). Left at 0.0 by default, meaning 'not set' / never
    flagged. reorder_qty is auto-filled client-side from max_level minus
    reorder_point as a convenience only - the server saves whatever three
    numbers it's given, with no recomputation."""
    item = db.session.get(Item, item_id)
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for('items.catalogue'))

    try:
        item.reorder_point = float(request.form.get('reorder_point', 0) or 0)
        item.reorder_qty = float(request.form.get('reorder_qty', 0) or 0)
        item.max_level = float(request.form.get('max_level', 0) or 0)
        db.session.commit()
        flash(f"Reorder settings updated for {item.code}.", "success")
    except ValueError:
        flash("Reorder point and quantity must be numbers.", "error")

    return redirect(url_for('items.detail', item_id=item_id))


@items_bp.route('/items/<int:item_id>/edit', methods=['POST'])
def update_item(item_id):
    """Edit an item's identity/pricing fields only (code, description,
    category, active, last_cost, avg_cost, excl_price, incl_price).
    Qty on Hand is deliberately excluded - it must keep going through the
    audited stock_service.adjust() path via adjust_stock(), never a
    free-text field here."""
    item = db.session.get(Item, item_id)
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for('items.catalogue'))

    code = request.form.get('code', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    active = request.form.get('active') == 'on'
    is_stocked_finished_good = request.form.get('is_stocked_finished_good') == 'on'

    if not code:
        flash("Item code cannot be blank.", "error")
        return redirect(url_for('items.detail', item_id=item_id))

    duplicate = Item.query.filter(Item.code == code, Item.id != item_id).first()
    if duplicate:
        flash(f"Item code '{code}' is already in use by another item.", "error")
        return redirect(url_for('items.detail', item_id=item_id))

    try:
        last_cost = float(request.form.get('last_cost', 0) or 0)
        avg_cost = float(request.form.get('avg_cost', 0) or 0)
        excl_price = float(request.form.get('excl_price', 0) or 0)
        incl_price = float(request.form.get('incl_price', 0) or 0)
    except ValueError:
        flash("Last Cost, Avg Cost, Excl. Price and Incl. Price must be numbers.", "error")
        return redirect(url_for('items.detail', item_id=item_id))

    item.code = code
    item.description = description
    item.category = category
    item.active = active
    item.is_stocked_finished_good = is_stocked_finished_good
    item.last_cost = last_cost
    item.avg_cost = avg_cost
    item.excl_price = excl_price
    item.incl_price = incl_price

    try:
        db.session.commit()
        flash(f"Item {item.code} updated.", "success")
    except IntegrityError:
        # Belt-and-suspenders against the code's unique=True DB constraint -
        # the pre-check above should already catch this, but never let a
        # duplicate code 500 the request.
        db.session.rollback()
        flash(f"Item code '{code}' is already in use by another item.", "error")

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
            default_path = os.path.join(current_app.config['BASE_DIR'], 'data', 'ItemListingReport.csv')
            if not os.path.exists(default_path):
                # Fallback check
                default_path = os.path.join('data', 'ItemListingReport.csv')
                
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


@items_bp.route('/items/import-supplier-leadtime', methods=['GET', 'POST'])
def import_supplier_leadtime():
    """Upload-only import of Supplier + Lead Time (weeks) from Sage's
    OutstandingPOByItemReport.csv. Only enriches existing catalogue items
    matched by code - never creates new items, never touches qty_on_hand
    or the qty_on_order figure computed live from internal POs.
    See docs/specs/supplier-lead-time-import-2026-07-17.md."""
    if request.method == 'POST':
        uploaded_file = request.files.get('csv_file')

        if uploaded_file and uploaded_file.filename:
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(file_path)

            try:
                updated_count, unmatched_count = import_supplier_lead_time_from_csv(file_path)
                flash(f"{updated_count} items updated, {unmatched_count} item codes not found in catalogue.", "success")
                return redirect(url_for('items.catalogue'))
            except Exception as e:
                flash(f"Error importing CSV: {str(e)}", "error")
                return redirect(url_for('items.import_supplier_leadtime'))
        else:
            flash("Please choose a CSV file to import.", "error")

    return render_template('items/import_supplier_leadtime.html')
