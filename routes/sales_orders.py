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
    # Also fetch related works orders if any
    wos = WorksOrder.query.filter_by(so_id=order_id).all()
    return render_template('sales_orders/detail.html', so=so, wos=wos)

@sales_orders_bp.route('/sales-orders/<int:order_id>/build-bom', methods=['GET', 'POST'])
def build_bom(order_id):
    """BOM Builder page — select items from catalogue to build Works Order or Picking List."""
    so = SalesOrder.query.get_or_404(order_id)
    
    if request.method == 'POST':
        order_type = request.form.get('order_type', '').strip()
        if order_type not in ('ASSEMBLY', 'STOCK'):
            flash("Please select an order type (Assembly Order or Stock Order).", "error")
            return redirect(url_for('sales_orders.build_bom', order_id=order_id))
        
        # Parse selected items from JSON
        items_json = request.form.get('bom_items_json', '[]')
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            flash("Invalid BOM data. Please try again.", "error")
            return redirect(url_for('sales_orders.build_bom', order_id=order_id))
        
        if not items_data:
            flash("Please select at least one item for the BOM.", "error")
            return redirect(url_for('sales_orders.build_bom', order_id=order_id))
        
        try:
            issued_by = request.form.get('issued_by', 'System').strip() or 'System'
            from services.bom_builder import create_works_order_or_picking_list
            wo = create_works_order_or_picking_list(so_id=order_id, order_type=order_type,
                                                     items_list=items_data, issued_by=issued_by)
            flash(f"{( 'Works Order' if order_type == 'ASSEMBLY' else 'Picking List' )} {wo.wo_number} created successfully.", "success")
            return redirect(url_for('works_orders.view_order', order_id=wo.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating order: {str(e)}", "error")
            return redirect(url_for('sales_orders.build_bom', order_id=order_id))
    
    # GET: show item catalogue for selection
    items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
    item_payload = [item_to_bom_json(item) for item in items]
    categories = db.session.query(Item.category).filter(Item.active == True, Item.category != None).distinct().order_by(Item.category).all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('sales_orders/bom_builder.html', so=so, items=item_payload, categories=categories)
