import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename
from models import db, SalesOrder, SOLineItem, Item, WorksOrder, BOMLine, StockMovement
from services.pdf_parser import parse_sales_order_pdf

sales_orders_bp = Blueprint('sales_orders', __name__)

@sales_orders_bp.route('/sales-orders')
def list_orders():
    orders = SalesOrder.query.order_by(SalesOrder.created_at.desc()).all()
    return render_template('sales_orders/list.html', orders=orders)

def item_to_bom_json(item):
    """Return the plain JSON shape consumed by the BOM builder UI."""
    return {
        'id': item.id,
        'code': item.code,
        'description': item.description,
        'category': item.category,
        'last_cost': item.last_cost or 0.0,
        'avg_cost': item.avg_cost or 0.0,
        'excl_price': item.excl_price or 0.0,
        'incl_price': item.incl_price or 0.0,
        'qty_on_hand': item.qty_on_hand or 0.0,
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
                                   json_parsed=json.dumps(parsed, default=str))
            
        except Exception as e:
            flash(f"Error processing PDF: {str(e)}", "error")
            return redirect(url_for('sales_orders.upload_order'))
    
    return render_template('sales_orders/upload.html')

@sales_orders_bp.route('/sales-orders/save', methods=['POST'])
def save_order():
    """Save or update a sales order from form data."""
    so_number = request.form.get('so_number', '').strip()
    if not so_number:
        flash("Sales Order number is required.", "error")
        return redirect(url_for('sales_orders.upload_order'))
    
    # Check if overwriting existing
    existing = SalesOrder.query.filter_by(so_number=so_number).first()
    if existing:
        # Delete existing and its line items (cascade)
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
            created_at=datetime.utcnow()
        )
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
    return render_template('sales_orders/detail.html', so=so, wos=wos, stock_orders=stock_orders)

@sales_orders_bp.route('/sales-orders/<int:order_id>/build-bom', methods=['GET', 'POST'])
def build_bom(order_id):
    """Build BOM / Works Pack — classify SO lines and create WorksOrder + StockOrder."""
    so = SalesOrder.query.get_or_404(order_id)
    
    if request.method == 'POST':
        print("=" * 80)
        print("POST /build-bom reached!")
        print(f"Form data keys: {list(request.form.keys())}")
        print(f"Component IDs: {request.form.getlist('component_item_id[]')}")
        print(f"Component Qtys: {request.form.getlist('component_qty[]')}")
        print("=" * 80)
        try:
            # Parse form data
            line_items = SOLineItem.query.filter_by(so_id=order_id).all()
            fan_line_id = None
            stock_line_ids = []
            
            # Classify lines
            for line in line_items:
                role = request.form.get(f'line_role_{line.id}', 'ignore')
                if role == 'fan':
                    if fan_line_id is not None:
                        flash("Only one line can be marked as Fan.", "error")
                        return redirect(url_for('sales_orders.build_bom', order_id=order_id))
                    fan_line_id = line.id
                elif role == 'stock':
                    stock_line_ids.append(line.id)
            
            created_wo = None
            created_stock_order = None
            
            # Create WorksOrder if fan line selected
            if fan_line_id:
                # Check if WO already exists
                existing_wo = WorksOrder.query.filter_by(so_id=order_id).first()
                if existing_wo:
                    flash("A Works Order already exists for this Sales Order.", "warning")
                    return redirect(url_for('sales_orders.view_order', order_id=order_id))
                
                # Generate WO number
                last_wo = WorksOrder.query.order_by(WorksOrder.id.desc()).first()
                if last_wo:
                    # Extract number from format "WO0042"
                    try:
                        last_num = int(last_wo.wo_number.replace('WO', ''))
                        next_num = last_num + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                wo_number = f"WO{next_num:04d}"
                
                # Create WorksOrder
                works_order = WorksOrder(
                    wo_number=wo_number,
                    so_id=order_id,
                    order_type='ASSEMBLY',
                    status='Open',
                    issued_by=request.form.get('issued_by', 'System').strip() or 'System'
                )
                db.session.add(works_order)
                db.session.flush()  # Get wo.id
                
                # Parse BOM components
                component_item_ids = request.form.getlist('component_item_id[]')
                component_qtys = request.form.getlist('component_qty[]')
                
                for i, item_id_str in enumerate(component_item_ids):
                    if not item_id_str:
                        continue
                    try:
                        item_id = int(item_id_str)
                        qty = float(component_qtys[i]) if i < len(component_qtys) else 0
                        if qty <= 0:
                            continue
                        
                        # Load Item to get unit_cost
                        item = Item.query.get(item_id)
                        if not item:
                            continue
                        
                        bom_line = BOMLine(
                            wo_id=works_order.id,
                            item_id=item.id,
                            qty_required=qty,
                            unit_cost=item.last_cost or 0.0
                        )
                        db.session.add(bom_line)
                    except (ValueError, IndexError):
                        continue
                
                created_wo = works_order
            
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
                    line = SOLineItem.query.get(line_id)
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
                        qty=line.qty
                    )
                    db.session.add(stock_line)
                
                created_stock_order = stock_order
            
            # Validate at least one order type was created
            if not created_wo and not created_stock_order:
                flash("Please select at least one Fan line or Stock Order line.", "warning")
                return redirect(url_for('sales_orders.build_bom', order_id=order_id))
            
            # Update SO status to Open
            so.status = 'Open'
            
            db.session.commit()
            
            # Flash success message
            messages = []
            if created_wo:
                messages.append(f"Works Order {created_wo.wo_number}")
            if created_stock_order:
                messages.append(f"Stock Order {created_stock_order.stock_order_number}")
            flash(f"Works Pack created successfully: {', '.join(messages)}", "success")
            return redirect(url_for('sales_orders.view_order', order_id=order_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating Works Pack: {str(e)}", "error")
            # Re-render with current data
            catalogue_items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
            return render_template('sales_orders/build_bom.html', 
                                  so=so, 
                                  line_items=line_items,
                                  catalogue_items=catalogue_items)
    
    # GET: Show build BOM form
    line_items = SOLineItem.query.filter_by(so_id=order_id).all()
    catalogue_items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
    
    # Prepare JSON for JavaScript
    catalogue_json = [{'id': i.id, 'code': i.code, 'description': i.description} for i in catalogue_items]
    
    return render_template('sales_orders/build_bom.html', 
                          so=so, 
                          line_items=line_items,
                          catalogue_items=catalogue_items,
                          catalogue_json=catalogue_json)

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
    
    # Guard: cannot delete if linked Works Orders exist
    wos = WorksOrder.query.filter_by(so_id=order_id).all()
    if wos:
        flash(f"Cannot delete Sales Order {so.so_number} — it has linked Works Orders. Delete all Works Orders first.", "error")
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
                                   reupload_mode=True)
            
        except Exception as e:
            flash(f"Error processing PDF: {str(e)}", "error")
            return redirect(url_for('sales_orders.reupload_order', order_id=order_id))
    
    # GET: show upload form
    return render_template('sales_orders/upload.html', existing_so=so, reupload_mode=True)
