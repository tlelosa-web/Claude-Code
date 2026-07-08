import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import nullslast
from models import db, PurchaseOrder, POLine, Item
from services.po_parser import parse_purchase_order_pdf, split_item_code
from services.stock_service import receipt as stock_receipt
from services.order_filters import PO_ACTIVE

purchase_orders_bp = Blueprint('purchase_orders', __name__)


@purchase_orders_bp.route('/purchase-orders')
def list_orders():
    view = request.args.get('view', 'all')
    query = PurchaseOrder.query
    if view == 'open':
        query = query.filter(PurchaseOrder.status.in_(PO_ACTIVE))
    orders = query.order_by(nullslast(PurchaseOrder.due_date.asc())).all()
    return render_template('purchase_orders/list.html', orders=orders, view=view)


def _match_lines_to_items(line_items):
    """Auto-match each parsed line's item code against the catalogue.

    Returns a new list of line dicts with item_code/matched_item_id/
    matched_item_code added, plus the count of lines that couldn't be
    matched (surfaced as a warning, never blocks saving).
    """
    matched_lines = []
    unmatched_count = 0
    for li in line_items:
        code, desc = split_item_code(li['description'])
        item = Item.query.filter_by(code=code).first() if code else None
        if not item:
            unmatched_count += 1
        matched_lines.append({
            **li,
            'item_code': code,
            'description': desc,
            'matched_item_id': item.id if item else None,
            'matched_item_code': item.code if item else None,
        })
    return matched_lines, unmatched_count


@purchase_orders_bp.route('/purchase-orders/upload', methods=['GET', 'POST'])
def upload_order():
    if request.method == 'POST':
        uploaded_file = request.files.get('pdf_file')

        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a PDF file to upload.", "error")
            return redirect(url_for('purchase_orders.upload_order'))

        if not uploaded_file.filename.lower().endswith('.pdf'):
            flash("Only PDF files are accepted.", "error")
            return redirect(url_for('purchase_orders.upload_order'))

        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(upload_dir, filename)
        uploaded_file.save(filepath)

        try:
            parsed = parse_purchase_order_pdf(filepath)

            if parsed['parse_errors']:
                flash("Some fields could not be parsed automatically. Please review and correct below.", "warning")

            existing_po = None
            if parsed['po_number']:
                existing_po = PurchaseOrder.query.filter_by(po_number=parsed['po_number']).first()
                if existing_po:
                    flash(f"Purchase Order {parsed['po_number']} already exists. You can overwrite below.", "warning")

            matched_lines, unmatched_count = _match_lines_to_items(parsed['line_items'])
            if unmatched_count:
                flash(
                    f"{unmatched_count} line item(s) could not be auto-matched to a catalogue item code. "
                    "They will be saved unlinked — link them from the Purchase Order detail page before receiving.",
                    "warning"
                )

            return render_template('purchase_orders/upload.html',
                                   parsed=parsed,
                                   matched_lines=matched_lines,
                                   existing_po=existing_po)

        except Exception as e:
            flash(f"Error processing PDF: {str(e)}", "error")
            return redirect(url_for('purchase_orders.upload_order'))

    return render_template('purchase_orders/upload.html')


@purchase_orders_bp.route('/purchase-orders/save', methods=['POST'])
def save_order():
    """Save a Purchase Order from the reviewed upload form."""
    po_number = request.form.get('po_number', '').strip()
    if not po_number:
        flash("Purchase Order number is required.", "error")
        return redirect(url_for('purchase_orders.upload_order'))

    existing = PurchaseOrder.query.filter_by(po_number=po_number).first()
    if existing:
        # Block overwrite if receipts have already been recorded — deleting
        # would discard the audit trail of what stock actually moved.
        if any((line.qty_received or 0) > 0 for line in existing.lines):
            flash(
                f"Cannot overwrite {po_number}: it already has receipts recorded against it. "
                "Delete the receipts first if you need to re-import.",
                "error"
            )
            return redirect(url_for('purchase_orders.view_order', order_id=existing.id))
        db.session.delete(existing)
        db.session.flush()

    try:
        po_date = None
        due_date = None
        po_date_str = request.form.get('po_date', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        if po_date_str:
            po_date = datetime.strptime(po_date_str, '%Y-%m-%d').date()
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        po = PurchaseOrder(
            po_number=po_number,
            reference=request.form.get('reference', '').strip(),
            supplier_name=request.form.get('supplier_name', '').strip(),
            supplier_vat=request.form.get('supplier_vat', '').strip(),
            po_date=po_date,
            due_date=due_date,
            overall_discount_pct=float(request.form.get('overall_discount_pct') or 0),
            raw_pdf_text=request.form.get('raw_pdf_text', ''),
            status='Open',
            created_at=datetime.now()
        )
        db.session.add(po)
        db.session.flush()  # get po.id

        lines_json = request.form.get('lines_json', '[]')
        try:
            lines_data = json.loads(lines_json)
            for ld in lines_data:
                line = POLine(
                    po_id=po.id,
                    item_id=ld.get('matched_item_id'),
                    item_code_raw=ld.get('item_code', ''),
                    description=ld.get('description', ''),
                    qty_ordered=float(ld.get('qty', 0) or 0),
                    excl_price=float(ld.get('excl_price', 0) or 0),
                    disc_pct=float(ld.get('disc_pct', 0) or 0),
                    vat_pct=float(ld.get('vat_pct', 0) or 0),
                    excl_total=float(ld.get('excl_total', 0) or 0),
                    incl_total=float(ld.get('incl_total', 0) or 0),
                )
                db.session.add(line)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            flash(f"Warning: Could not parse all line items: {str(e)}", "warning")

        db.session.commit()
        flash(f"Purchase Order {po.po_number} saved successfully.", "success")
        return redirect(url_for('purchase_orders.view_order', order_id=po.id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving Purchase Order: {str(e)}", "error")
        return redirect(url_for('purchase_orders.upload_order'))


@purchase_orders_bp.route('/purchase-orders/<int:order_id>')
def view_order(order_id):
    po = PurchaseOrder.query.get_or_404(order_id)
    return render_template('purchase_orders/detail.html', po=po)


@purchase_orders_bp.route('/purchase-orders/<int:order_id>/print')
def print_order(order_id):
    po = PurchaseOrder.query.get_or_404(order_id)
    return render_template('purchase_orders/print.html', po=po)


@purchase_orders_bp.route('/purchase-orders/<int:order_id>/link-item', methods=['POST'])
def link_item(order_id):
    """Manually link an unmatched POLine to a catalogue Item by item code."""
    po = PurchaseOrder.query.get_or_404(order_id)
    line_id = request.form.get('line_id', type=int)
    item_code = request.form.get('item_code', '').strip()

    line = db.session.get(POLine, line_id) if line_id else None
    if not line or line.po_id != po.id:
        flash("Line item not found.", "error")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    item = Item.query.filter_by(code=item_code).first() if item_code else None
    if not item:
        flash(f"No catalogue item found with code '{item_code}'.", "error")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    line.item_id = item.id
    db.session.commit()
    flash(f"Line linked to {item.code}.", "success")
    return redirect(url_for('purchase_orders.view_order', order_id=order_id))


@purchase_orders_bp.route('/purchase-orders/<int:order_id>/receive', methods=['POST'])
def receive_order(order_id):
    """Receive a Purchase Order (full or partial).

    Posts a RECEIPT stock movement per line via services.stock_service and
    updates Item.last_cost from the PO line price. Blocked if any line
    still needs manual item-linking, since there'd be nowhere to post
    stock to.
    """
    po = PurchaseOrder.query.get_or_404(order_id)

    if po.status in ('Received', 'Cancelled'):
        flash(f"Purchase Order {po.po_number} is already {po.status} and cannot be received again.", "error")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    unlinked = [line for line in po.lines if line.item_id is None]
    if unlinked:
        flash(
            f"{len(unlinked)} line(s) are not linked to a catalogue item. Link them before receiving.",
            "error"
        )
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    try:
        received_any = False
        for line in po.lines:
            qty_str = request.form.get(f'receive_qty_{line.id}', '').strip()
            if not qty_str:
                continue

            qty = float(qty_str)
            remaining = (line.qty_ordered or 0) - (line.qty_received or 0)
            if qty <= 0 or remaining <= 0:
                continue
            qty = min(qty, remaining)  # cannot over-receive past what was ordered

            stock_receipt(line.item_id, qty, po.po_number,
                         notes=f"PO receipt: {line.description}", created_by="System")
            line.qty_received = (line.qty_received or 0) + qty
            item = db.session.get(Item, line.item_id)
            if item and line.excl_price:
                item.last_cost = line.excl_price
            received_any = True

        if not received_any:
            flash("No quantities were entered to receive.", "warning")
            return redirect(url_for('purchase_orders.view_order', order_id=order_id))

        all_received = all((line.qty_received or 0) >= (line.qty_ordered or 0) for line in po.lines)
        po.status = 'Received' if all_received else 'Partially Received'

        db.session.commit()
        flash(f"Purchase Order {po.po_number} receipt recorded. Status: {po.status}.", "success")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error receiving Purchase Order: {str(e)}", "error")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))


@purchase_orders_bp.route('/purchase-orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    po = PurchaseOrder.query.get_or_404(order_id)

    if any((line.qty_received or 0) > 0 for line in po.lines):
        flash(f"Cannot cancel {po.po_number}: it already has receipts recorded against it.", "error")
        return redirect(url_for('purchase_orders.view_order', order_id=order_id))

    po.status = 'Cancelled'
    db.session.commit()
    flash(f"Purchase Order {po.po_number} has been cancelled.", "success")
    return redirect(url_for('purchase_orders.view_order', order_id=order_id))


@purchase_orders_bp.route('/purchase-orders/create-from-shortfall', methods=['POST'])
def create_from_shortfall():
    """Enhancement 2 - pre-fill a Draft Purchase Order with one line per
    item currently below its reorder point, at reorder_qty. Supplier is
    left blank for manual fill-in (no supplier master table yet - see
    docs/specs/purchase-order-module-plan.md section 6)."""
    items = Item.query.filter(
        Item.reorder_point > 0,
        Item.qty_on_hand <= Item.reorder_point,
        Item.active == True
    ).order_by(Item.category, Item.code).all()

    eligible = [(item, item.reorder_qty or 0) for item in items if (item.reorder_qty or 0) > 0]

    if not eligible:
        flash("No items below their reorder point have a reorder quantity set.", "warning")
        return redirect(url_for('reports.stock'))

    last_draft = (PurchaseOrder.query
                  .filter(PurchaseOrder.po_number.like('PO-DRAFT-%'))
                  .order_by(PurchaseOrder.id.desc()).first())
    try:
        next_num = int(last_draft.po_number.replace('PO-DRAFT-', '')) + 1 if last_draft else 1
    except ValueError:
        next_num = 1
    po_number = f"PO-DRAFT-{next_num:04d}"

    po = PurchaseOrder(
        po_number=po_number,
        reference='Auto-generated from reorder shortfall',
        status='Draft',
        created_at=datetime.now()
    )
    db.session.add(po)
    db.session.flush()  # get po.id

    for item, qty in eligible:
        unit_cost = item.last_cost or 0.0
        line = POLine(
            po_id=po.id,
            item_id=item.id,
            item_code_raw=item.code,
            description=item.description,
            qty_ordered=qty,
            excl_price=unit_cost,
            excl_total=qty * unit_cost,
            incl_total=qty * unit_cost * 1.15,
        )
        db.session.add(line)

    db.session.commit()
    flash(
        f"Draft Purchase Order {po.po_number} created with {len(eligible)} shortfall item(s). "
        "Fill in the supplier and save.",
        "success"
    )
    return redirect(url_for('purchase_orders.view_order', order_id=po.id))
