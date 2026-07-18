import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import nullslast
from models import db, SalesOrder, SOLineItem, Item, WorksOrder, BOMLine, StockMovement, StockOrder, StockOrderLine, PAYMENT_STATUS_OPTIONS
from services.pdf_parser import parse_sales_order_pdf
from services.order_filters import SO_ACTIVE
from services.invoice_importer import import_invoices_from_csv
from services.status_change_log import log_change, track_report_status

sales_orders_bp = Blueprint('sales_orders', __name__)

@sales_orders_bp.route('/sales-orders')
def list_orders():
    view = request.args.get('view', 'open')
    query = SalesOrder.query
    if view == 'open':
        query = query.filter(SalesOrder.status.in_(SO_ACTIVE))
    elif view == 'closed':
        query = query.filter(~SalesOrder.status.in_(SO_ACTIVE))
    orders = query.order_by(nullslast(SalesOrder.delivery_date.asc())).all()
    return render_template('sales_orders/list.html', orders=orders, view=view)

def item_to_bom_json(item, qty_on_order=0.0, qty_committed=0.0, next_po_due=None):
    """Return the plain JSON shape consumed by the BOM builder UI.

    qty_on_order / qty_committed / next_po_due are demand-netting figures
    (see services/demand.py). Callers rendering many items should bulk-fetch
    these once via get_qty_on_order_bulk() / get_qty_committed_bulk() /
    get_next_po_due_bulk() and pass the per-item values in here, rather than
    querying per item in a loop. Defaults keep this safe for any caller that
    doesn't need demand-netting (available_qty then just equals qty_on_hand).
    """
    qty_on_hand = item.qty_on_hand or 0.0
    return {
        'id': item.id,
        'code': item.code,
        'description': item.description,
        'category': item.category,
        'last_cost': item.last_cost or 0.0,
        'avg_cost': item.avg_cost or 0.0,
        'excl_price': item.excl_price or 0.0,
        'incl_price': item.incl_price or 0.0,
        'qty_on_hand': qty_on_hand,
        'qty_on_order': qty_on_order,
        'qty_committed': qty_committed,
        'available_qty': qty_on_hand + qty_on_order - qty_committed,
        'next_po_due': next_po_due.isoformat() if next_po_due else None,
    }

@sales_orders_bp.route('/sales-orders/upload', methods=['GET', 'POST'])
def upload_order():
    if request.method == 'POST':
        uploaded_file = request.files.get('pdf_file')
        
        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a PDF file to upload.", "error")
            return redirect(url_for('sales_orders.upload_order'))
        
        if not uploaded_file.filename.lower().endswith('.pdf'):
            flash("Only PDF files are accepted.", "error")
            return redirect(url_for('sales_orders.upload_order'))
        
        # Save PDF temporarily
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(upload_dir, filename)
        uploaded_file.save(filepath)
        
        try:
            # Parse PDF
            parsed = parse_sales_order_pdf(filepath)
            
            if parsed['parse_errors']:
                flash(f"Some fields could not be parsed automatically. Please review and correct below.", "warning")
            
            # Check for duplicate SO number
            existing_so = None
            if parsed['so_number']:
                existing_so = SalesOrder.query.filter_by(so_number=parsed['so_number']).first()
                if existing_so:
                    flash(f"Sales Order {parsed['so_number']} already exists. You can overwrite or modify below.", "warning")
            
            return render_template('sales_orders/upload.html',
                                   parsed=parsed,
                                   existing_so=existing_so,
                                   json_parsed=json.dumps(parsed, default=str),
                                   payment_status_options=PAYMENT_STATUS_OPTIONS)

        except Exception as e:
            flash(f"Error processing PDF: {str(e)}", "error")
            return redirect(url_for('sales_orders.upload_order'))

    return render_template('sales_orders/upload.html', payment_status_options=PAYMENT_STATUS_OPTIONS)

@sales_orders_bp.route('/sales-orders/save', methods=['POST'])
def save_order():
    """Save or update a sales order from form data."""
    so_number = request.form.get('so_number', '').strip()
    if not so_number:
        flash("Sales Order number is required.", "error")
        return redirect(url_for('sales_orders.upload_order'))
    
    # Check if overwriting existing
    existing = SalesOrder.query.filter_by(so_number=so_number).first()
    carry_forward = None
    if existing:
        # Block overwrite if a Works Order or Stock Order is already linked —
        # deleting the SO would orphan them (no cascade on those relationships).
        linked_wos = WorksOrder.query.filter_by(so_id=existing.id).count()
        linked_stos = StockOrder.query.filter_by(so_id=existing.id).count()
        if linked_wos or linked_stos:
            flash(
                f"Cannot overwrite {so_number}: it has {linked_wos} Works Order(s) and "
                f"{linked_stos} Stock Order(s) linked to it. "
                "Delete or reassign them before re-uploading.",
                "error"
            )
            return redirect(url_for('sales_orders.view_order', order_id=existing.id))
        # Manual/report-only fields have no competing automated writer, so
        # they must survive an overwrite rather than silently reset to
        # column defaults — see Decision 3 of docs/specs/
        # sales-order-report-excel-export-2026-07-17.md.
        carry_forward = {
            'report_notes': existing.report_notes,
            'on_hold': existing.on_hold,
            'on_hold_reason': existing.on_hold_reason,
            'amount_paid': existing.amount_paid,
        }
        # Safe to delete — only SOLineItems are linked (cascade handles them)
        db.session.delete(existing)
        db.session.flush()
    
    try:
        so_date = None
        delivery_date = None
        so_date_str = request.form.get('so_date', '').strip()
        delivery_date_str = request.form.get('delivery_date', '').strip()
        
        if so_date_str:
            so_date = datetime.strptime(so_date_str, '%Y-%m-%d').date()
        if delivery_date_str:
            delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d').date()
        
        so = SalesOrder(
            so_number=so_number,
            job_numbers=request.form.get('job_numbers', '').strip(),
            reference=request.form.get('reference', '').strip(),
            so_date=so_date,
            delivery_date=delivery_date,
            customer_name=request.form.get('customer_name', '').strip(),
            customer_vat=request.form.get('customer_vat', '').strip(),
            delivery_address=request.form.get('delivery_address', '').strip(),
            sales_rep=request.form.get('sales_rep', '').strip(),
            raw_pdf_text=request.form.get('raw_pdf_text', ''),
            status='Draft',
            payment_status=request.form.get('payment_status', 'Account - Pending').strip() or 'Account - Pending',
            created_at=datetime.now()
        )
        if carry_forward:
            so.report_notes = carry_forward['report_notes']
            so.on_hold = carry_forward['on_hold']
            so.on_hold_reason = carry_forward['on_hold_reason']
            so.amount_paid = carry_forward['amount_paid']
        db.session.add(so)
        db.session.flush()  # Get so.id
        
        # Parse and save line items from JSON
        line_items_json = request.form.get('line_items_json', '[]')
        try:
            items_data = json.loads(line_items_json)
            for item_data in items_data:
                line_item = SOLineItem(
                    so_id=so.id,
                    description=item_data.get('description', ''),
                    qty=float(item_data.get('qty', 0)),
                    excl_price=float(item_data.get('excl_price', 0)),
                    vat_pct=float(item_data.get('vat_pct', 0)),
                    excl_total=float(item_data.get('excl_total', 0)),
                    incl_total=float(item_data.get('incl_total', 0))
                )
                db.session.add(line_item)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            flash(f"Warning: Could not parse all line items: {str(e)}", "warning")
        
        db.session.commit()
        flash(f"Sales Order {so.so_number} saved successfully.", "success")
        return redirect(url_for('sales_orders.view_order', order_id=so.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving Sales Order: {str(e)}", "error")
        return redirect(url_for('sales_orders.upload_order'))

@sales_orders_bp.route('/sales-orders/<int:order_id>')
def view_order(order_id):
    so = SalesOrder.query.get_or_404(order_id)
    # Also fetch related works orders and stock orders if any
    from models import StockOrder
    wos = WorksOrder.query.filter_by(so_id=order_id).all()
    stock_orders = StockOrder.query.filter_by(so_id=order_id).all()
    return render_template('sales_orders/detail.html', so=so, wos=wos, stock_orders=stock_orders,
                           payment_status_options=PAYMENT_STATUS_OPTIONS)

@sales_orders_bp.route('/sales-orders/<int:order_id>/build-bom', methods=['GET', 'POST'])
def build_bom(order_id):
    """Build BOM / Works Pack — classify SO lines and create WorksOrder + StockOrder."""
    so = SalesOrder.query.get_or_404(order_id)

    # Guard: redirect if a WorksOrder already exists for this SO (GET only)
    if request.method == 'GET' and WorksOrder.query.filter_by(so_id=order_id).first():
        flash("A Works Order already exists for this Sales Order.", "warning")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

    if request.method == 'POST':
        try:
            # Parse form data
            line_items = SOLineItem.query.filter_by(so_id=order_id).all()
            fan_line_ids = []
            stock_line_ids = []

            # Classify lines — a Sales Order may have several distinct Fan
            # lines (e.g. multiple fan models on one order); each becomes its
            # own Works Order below.
            for line in line_items:
                role = request.form.get(f'line_role_{line.id}', 'ignore')
                if role == 'fan':
                    fan_line_ids.append(line.id)
                elif role == 'stock':
                    stock_line_ids.append(line.id)

            # Per-line FM number validation — each fan line must have its
            # own Job / FM number so the printed Works Order document can
            # reference it.
            collected_job_numbers = []
            missing_job_number_lines = []
            for line in line_items:
                # Read per-line job number from form
                line_job_number = request.form.get(f'line_job_number_{line.id}', '').strip()
                if line.id in fan_line_ids:
                    if not line_job_number:
                        missing_job_number_lines.append(line.description or f'Line {line.id}')
                    else:
                        collected_job_numbers.append(line_job_number)
                # Save job_number to the line item regardless of role
                line.job_number = line_job_number or None

            if missing_job_number_lines:
                flash(
                    f"FM / Job number is required for each Fan line. Missing for: "
                    f"{', '.join(missing_job_number_lines)}",
                    "error"
                )
                return redirect(url_for('sales_orders.build_bom', order_id=order_id))

            created_wos = []
            created_stock_order = None

            with track_report_status(so):
                # Create one WorksOrder per Fan line selected
                if fan_line_ids:
                    # Check if a WO already exists for this SO
                    existing_wo = WorksOrder.query.filter_by(so_id=order_id).first()
                    if existing_wo:
                        flash("A Works Order already exists for this Sales Order.", "warning")
                        return redirect(url_for('sales_orders.view_order', order_id=order_id))

                    # Group each submitted BOM component by the Fan line it was
                    # assigned to in the UI. When only one Fan line is selected,
                    # an unassigned component defaults to it (keeps old single-fan
                    # form payloads working without the new dropdown field).
                    component_item_ids = request.form.getlist('component_item_id[]')
                    component_qtys = request.form.getlist('component_qty[]')
                    component_fan_ids = request.form.getlist('component_fan_line_id[]')

                    components_by_fan_line = {}
                    unassigned_count = 0
                    for i, item_id_str in enumerate(component_item_ids):
                        if not item_id_str:
                            continue
                        try:
                            item_id = int(item_id_str)
                            qty = float(component_qtys[i]) if i < len(component_qtys) else 0
                            if qty <= 0:
                                continue
                        except (ValueError, IndexError):
                            continue

                        fan_id_str = component_fan_ids[i] if i < len(component_fan_ids) else ''
                        assigned_fan_line_id = None
                        if fan_id_str:
                            try:
                                assigned_fan_line_id = int(fan_id_str)
                            except ValueError:
                                assigned_fan_line_id = None
                        elif len(fan_line_ids) == 1:
                            assigned_fan_line_id = fan_line_ids[0]

                        if assigned_fan_line_id is None or assigned_fan_line_id not in fan_line_ids:
                            unassigned_count += 1
                            continue

                        components_by_fan_line.setdefault(assigned_fan_line_id, []).append((item_id, qty))

                    if unassigned_count:
                        flash(
                            f"{unassigned_count} component(s) had no matching Fan line selected and were skipped.",
                            "warning"
                        )

                    # Generate sequential WO numbers ("WO0042") for each fan line
                    last_wo = WorksOrder.query.order_by(WorksOrder.id.desc()).first()
                    try:
                        next_num = int(last_wo.wo_number.replace('WO', '')) + 1 if last_wo else 1
                    except ValueError:
                        next_num = 1

                    issued_by = request.form.get('issued_by', 'System').strip() or 'System'

                    for fan_line_id in fan_line_ids:
                        wo_number = f"WO{next_num:04d}"
                        next_num += 1

                        fan_line = db.session.get(SOLineItem, fan_line_id)

                        works_order = WorksOrder(
                            wo_number=wo_number,
                            so_id=order_id,
                            order_type='ASSEMBLY',
                            status='Open',
                            issued_by=issued_by,
                            job_number=fan_line.job_number if fan_line else None
                        )
                        db.session.add(works_order)
                        db.session.flush()  # Get wo.id

                        # Persist the fan line as the assembly parent so the
                        # printed Works Order shows it as a header row with its
                        # components nested beneath. Uses the existing
                        # line_type/parent_line_id columns (no schema change).
                        parent_line_id = None
                        fan_item = None
                        if fan_line and fan_line.description:
                            fan_code = fan_line.description.split(' - ', 1)[0].strip()
                            if fan_code:
                                fan_item = Item.query.filter_by(code=fan_code).first()
                        if fan_item:
                            assembly_line = BOMLine(
                                wo_id=works_order.id,
                                item_id=fan_item.id,
                                qty_required=fan_line.qty or 1.0,
                                unit_cost=fan_item.last_cost or 0.0,
                                line_type='ASSEMBLY_ITEM'
                            )
                            db.session.add(assembly_line)
                            db.session.flush()  # Get assembly_line.id for child parent_line_id
                            parent_line_id = assembly_line.id
                        else:
                            label = fan_line.description if fan_line else fan_line_id
                            flash(
                                f"Fan line '{label}' could not be matched to a catalogue item; "
                                "components saved without an assembly header.", "warning"
                            )

                        for item_id, qty in components_by_fan_line.get(fan_line_id, []):
                            item = db.session.get(Item, item_id)
                            if not item:
                                continue
                            bom_line = BOMLine(
                                wo_id=works_order.id,
                                item_id=item.id,
                                qty_required=qty,
                                unit_cost=item.last_cost or 0.0,
                                line_type='COMPONENT',
                                parent_line_id=parent_line_id
                            )
                            db.session.add(bom_line)

                        created_wos.append(works_order)

                # Create StockOrder if stock lines exist
                if stock_line_ids:
                    # Generate Stock Order number
                    last_so = StockOrder.query.order_by(StockOrder.id.desc()).first()
                    if last_so:
                        try:
                            last_num = int(last_so.stock_order_number.replace('STO', ''))
                            next_num = last_num + 1
                        except ValueError:
                            next_num = 1
                    else:
                        next_num = 1
                    stock_order_number = f"STO{next_num:04d}"

                    # Create StockOrder
                    stock_order = StockOrder(
                        stock_order_number=stock_order_number,
                        so_id=order_id,
                        status='Open'
                    )
                    db.session.add(stock_order)
                    db.session.flush()

                    # Create StockOrderLines
                    for line_id in stock_line_ids:
                        line = db.session.get(SOLineItem, line_id)
                        if not line:
                            continue

                        # Parse item_code from description (text before first " - ")
                        item_code = ''
                        if line.description:
                            parts = line.description.split(' - ', 1)
                            item_code = parts[0].strip() if parts else ''

                        stock_line = StockOrderLine(
                            stock_order_id=stock_order.id,
                            item_code=item_code,
                            description=line.description,
                            qty=line.qty,
                            job_number=line.job_number
                        )
                        db.session.add(stock_line)

                    created_stock_order = stock_order

            # Log initial status=Open creation event for each new WO/STO
            # (old_value=None represents 'did not exist before').
            for wo in created_wos:
                log_change('WO', wo.id, wo.wo_number, 'status', None, 'Open')
            if created_stock_order:
                log_change('STO', created_stock_order.id, created_stock_order.stock_order_number, 'status', None, 'Open')
            
            # Validate at least one order type was created
            if not created_wos and not created_stock_order:
                flash("Please select at least one Fan line or Stock Order line.", "warning")
                return redirect(url_for('sales_orders.build_bom', order_id=order_id))

            # Update SO status to Open
            so.status = 'Open'
            # Build SO-level summary from per-line job numbers
            if collected_job_numbers:
                so.job_numbers = ', '.join(collected_job_numbers)

            db.session.commit()

            # Flash success message
            messages = []
            if created_wos:
                wo_numbers = ', '.join(wo.wo_number for wo in created_wos)
                label = "Works Order" if len(created_wos) == 1 else "Works Orders"
                messages.append(f"{label} {wo_numbers}")
            if created_stock_order:
                messages.append(f"Stock Order {created_stock_order.stock_order_number}")
            flash(f"Works Pack created successfully: {', '.join(messages)}", "success")
            return redirect(url_for('sales_orders.view_order', order_id=order_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating Works Pack: {str(e)}", "error")
            # Re-render with current data
            catalogue_items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
            from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk, get_next_po_due_bulk
            item_ids = [i.id for i in catalogue_items]
            qty_on_order_map = get_qty_on_order_bulk(item_ids=item_ids)
            qty_committed_map = get_qty_committed_bulk(item_ids=item_ids)
            next_po_due_map = get_next_po_due_bulk(item_ids=item_ids)
            catalogue_json = [
                item_to_bom_json(
                    i,
                    qty_on_order=qty_on_order_map.get(i.id, 0.0),
                    qty_committed=qty_committed_map.get(i.id, 0.0),
                    next_po_due=next_po_due_map.get(i.id),
                )
                for i in catalogue_items
            ]
            return render_template('sales_orders/build_bom.html',
                                  so=so,
                                  line_items=line_items,
                                  catalogue_json=catalogue_json)

    # GET: Show build BOM form
    line_items = SOLineItem.query.filter_by(so_id=order_id).all()
    catalogue_items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()

    # Prepare JSON for JavaScript
    from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk, get_next_po_due_bulk
    item_ids = [i.id for i in catalogue_items]
    qty_on_order_map = get_qty_on_order_bulk(item_ids=item_ids)
    qty_committed_map = get_qty_committed_bulk(item_ids=item_ids)
    next_po_due_map = get_next_po_due_bulk(item_ids=item_ids)
    catalogue_json = [
        item_to_bom_json(
            i,
            qty_on_order=qty_on_order_map.get(i.id, 0.0),
            qty_committed=qty_committed_map.get(i.id, 0.0),
            next_po_due=next_po_due_map.get(i.id),
        )
        for i in catalogue_items
    ]

    return render_template('sales_orders/build_bom.html',
                          so=so, 
                          line_items=line_items,
                          catalogue_items=catalogue_items,
                          catalogue_json=catalogue_json)

def can_close_sales_order(so_id):
    """Check if a Sales Order can be closed — all WOs and STOs must be Complete or Cancelled.
    
    Returns (can_close: bool, reasons: list[str])
    """
    reasons = []
    
    wos = WorksOrder.query.filter_by(so_id=so_id).all()
    stos = StockOrder.query.filter_by(so_id=so_id).all()
    
    if not wos and not stos:
        return False, ["No Works Orders or Stock Orders have been created for this Sales Order."]
    
    # Check Works Orders
    if wos:
        open_wos = [wo for wo in wos if wo.status not in ('Complete', 'Cancelled')]
        if open_wos:
            wo_list = ', '.join(wo.wo_number for wo in open_wos)
            reasons.append(f"Works Order(s) still open: {wo_list}")
    
    # Check Stock Orders
    if stos:
        open_stos = [sto for sto in stos if sto.status not in ('Complete', 'Cancelled')]
        if open_stos:
            sto_list = ', '.join(sto.stock_order_number for sto in open_stos)
            reasons.append(f"Stock Order(s) still open: {sto_list}")
    
    return len(reasons) == 0, reasons


@sales_orders_bp.route('/sales-orders/<int:order_id>/close', methods=['POST'])
def close_order(order_id):
    """Close a Sales Order — requires all WOs and STOs to be Complete or Cancelled."""
    so = SalesOrder.query.get_or_404(order_id)
    
    if so.status in ('Closed', 'Cancelled'):
        flash(f"Sales Order {so.so_number} is already {so.status}.", "warning")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))
    
    can_close, reasons = can_close_sales_order(order_id)
    
    if not can_close:
        for reason in reasons:
            flash(reason, "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))
    
    so.status = 'Closed'
    db.session.commit()

    flash(f"Sales Order {so.so_number} has been closed.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/reopen', methods=['POST'])
def reopen_order(order_id):
    """Reopen a Closed Sales Order. Does not cascade down to its WOs/STOs —
    they may be Complete for good reason; reopening the SO itself just allows
    editing it again (e.g. adding a note or a line)."""
    so = SalesOrder.query.get_or_404(order_id)

    if so.status != 'Closed':
        flash(f"Sales Order {so.so_number} is not Closed — nothing to reopen.", "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

    so.status = 'Open'
    db.session.commit()

    flash(f"Sales Order {so.so_number} has been reopened.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/payment-status', methods=['POST'])
def update_payment_status(order_id):
    """Set the manually-tracked Payment Status (sourced from Sage/accounting, not the SO PDF)."""
    so = SalesOrder.query.get_or_404(order_id)
    new_status = request.form.get('payment_status', '').strip()

    if new_status not in PAYMENT_STATUS_OPTIONS:
        flash(f"Invalid payment status: {new_status}", "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

    if new_status == 'Cash Sale - Partial':
        amount_raw = request.form.get('amount_paid', '').strip()
        try:
            so.amount_paid = float(amount_raw) if amount_raw else (so.amount_paid or 0.0)
        except ValueError:
            flash("Amount Paid must be a number.", "error")
            return redirect(url_for('sales_orders.view_order', order_id=order_id))

    so.payment_status = new_status
    db.session.commit()

    flash(f"Payment status for {so.so_number} set to {new_status}.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/delivery-date', methods=['POST'])
def update_delivery_date(order_id):
    """Set Delivery Date after save — it was previously fixed at initial parse time."""
    so = SalesOrder.query.get_or_404(order_id)
    new_date_str = request.form.get('delivery_date', '').strip()

    if not new_date_str:
        flash("Delivery Date cannot be blank.", "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash(f"Invalid Delivery Date: {new_date_str}", "error")
        return redirect(url_for('sales_orders.view_order', order_id=order_id))

    so.delivery_date = new_date
    db.session.commit()

    flash(f"Delivery Date for {so.so_number} updated to {new_date.strftime('%d/%m/%Y')}.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/report-notes', methods=['POST'])
def update_report_notes(order_id):
    """Set the manual, carried-forward Notes column for the Sales Order
    Report export. See docs/specs/sales-order-report-excel-export-2026-07-17.md."""
    so = SalesOrder.query.get_or_404(order_id)
    new_notes = request.form.get('report_notes', '').strip()
    old_notes = so.report_notes or ''

    if new_notes != old_notes:
        log_change('SO', so.id, so.so_number, 'report_notes', so.report_notes, new_notes or None)
        so.report_notes = new_notes or None
        db.session.commit()

    flash(f"Notes updated for {so.so_number}.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/on-hold', methods=['POST'])
def update_on_hold(order_id):
    """Toggle the manual On Hold flag (SO-level only) and its optional
    reason. Overlaid on the computed report_status via
    SalesOrder.display_report_status -- see docs/specs/
    sales-order-report-excel-export-2026-07-17.md Decision 1.

    on_hold and on_hold_reason are logged as separate StatusChangeLog rows
    (each only when it actually changed) rather than one combined row --
    reads more sensibly in the eventual Change Log report, since a reason
    edit with no flag flip (or vice versa) is still one real, distinct
    change worth its own row."""
    so = SalesOrder.query.get_or_404(order_id)
    new_on_hold = request.form.get('on_hold') == 'on'
    new_reason = request.form.get('on_hold_reason', '').strip() or None

    if new_on_hold != so.on_hold:
        log_change('SO', so.id, so.so_number, 'on_hold', so.on_hold, new_on_hold)
    if new_reason != so.on_hold_reason:
        log_change('SO', so.id, so.so_number, 'on_hold_reason', so.on_hold_reason, new_reason)

    so.on_hold = new_on_hold
    so.on_hold_reason = new_reason
    db.session.commit()

    flash(f"On Hold status updated for {so.so_number}.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))


@sales_orders_bp.route('/sales-orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel a Sales Order."""
    so = SalesOrder.query.get_or_404(order_id)
    
    # Check if any works orders exist and their status
    wos = WorksOrder.query.filter_by(so_id=order_id).all()
    
    if wos:
        completed_wos = [wo for wo in wos if wo.status == 'Complete']
        if completed_wos:
            flash(f"Cannot cancel Sales Order {so.so_number}. {len(completed_wos)} Works Order(s) already completed.", "error")
            return redirect(url_for('sales_orders.view_order', order_id=order_id))
        
        # Cancel all open works orders first
        for wo in wos:
            if wo.status != 'Cancelled':
                wo.status = 'Cancelled'
    
    so.status = 'Cancelled'
    db.session.commit()
    
    flash(f"Sales Order {so.so_number} has been cancelled.", "success")
    return redirect(url_for('sales_orders.view_order', order_id=order_id))

@sales_orders_bp.route('/sales-orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    """Delete a Sales Order permanently."""
    so = SalesOrder.query.get_or_404(order_id)
    
    # Guard: cannot delete if linked Works Orders or Stock Orders exist
    wos = WorksOrder.query.filter_by(so_id=order_id).all()
    stos = StockOrder.query.filter_by(so_id=order_id).all()
    if wos or stos:
        parts = []
        if wos:
            parts.append(f"{len(wos)} Works Order(s)")
        if stos:
            parts.append(f"{len(stos)} Stock Order(s)")
        flash(
            f"Cannot delete Sales Order {so.so_number} — it has linked {' and '.join(parts)}. "
            "Delete them first.",
            "error"
        )
        return redirect(url_for('sales_orders.view_order', order_id=order_id))
    
    so_number = so.so_number
    db.session.delete(so)
    db.session.commit()
    
    flash(f"Sales Order {so_number} deleted permanently.", "success")
    return redirect(url_for('sales_orders.list_orders'))

@sales_orders_bp.route('/sales-orders/<int:order_id>/reupload', methods=['GET', 'POST'])
def reupload_order(order_id):
    """Re-upload a PDF for an existing Sales Order."""
    so = SalesOrder.query.get_or_404(order_id)
    
    if request.method == 'POST':
        uploaded_file = request.files.get('pdf_file')
        
        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a PDF file to upload.", "error")
            return redirect(url_for('sales_orders.reupload_order', order_id=order_id))
        
        if not uploaded_file.filename.lower().endswith('.pdf'):
            flash("Only PDF files are accepted.", "error")
            return redirect(url_for('sales_orders.reupload_order', order_id=order_id))
        
        # Save PDF temporarily
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(upload_dir, filename)
        uploaded_file.save(filepath)
        
        try:
            # Parse PDF
            parsed = parse_sales_order_pdf(filepath)
            
            if parsed['parse_errors']:
                flash(f"Some fields could not be parsed automatically. Please review and correct below.", "warning")
            
            # Pre-fill with existing SO data for editing
            return render_template('sales_orders/upload.html',
                                   parsed=parsed,
                                   existing_so=so,
                                   json_parsed=json.dumps(parsed, default=str),
                                   payment_status_options=PAYMENT_STATUS_OPTIONS,
                                   reupload_mode=True)
            
        except Exception as e:
            flash(f"Error processing PDF: {str(e)}", "error")
            return redirect(url_for('sales_orders.reupload_order', order_id=order_id))
    
    # GET: show upload form
    return render_template('sales_orders/upload.html', existing_so=so, reupload_mode=True)


@sales_orders_bp.route('/sales-orders/import-invoices', methods=['GET', 'POST'])
def import_invoices():
    """Upload-only import of Sage's CustomerInvoicesReport.csv (Monthly INV
    tab source). Full upsert by invoice_number - see
    services/invoice_importer.py. See docs/specs/
    sales-order-report-excel-export-2026-07-17.md Decision 4."""
    if request.method == 'POST':
        uploaded_file = request.files.get('csv_file')

        if uploaded_file and uploaded_file.filename:
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(file_path)

            try:
                created_count, updated_count, skipped_count = import_invoices_from_csv(file_path)
                flash(f"Import complete! {created_count} invoices created, {updated_count} updated, {skipped_count} skipped.", "success")
                return redirect(url_for('sales_orders.list_orders'))
            except Exception as e:
                flash(f"Error importing CSV: {str(e)}", "error")
                return redirect(url_for('sales_orders.import_invoices'))
        else:
            flash("Please choose a CSV file to import.", "error")

    return render_template('sales_orders/import_invoices.html')
