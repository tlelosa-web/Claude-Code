import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response
from models import db, Item, StockMovement

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/stock')
def stock():
    categories = db.session.query(Item.category).filter(Item.category != None).distinct().order_by(Item.category).all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('reports/stock.html', categories=categories)

@reports_bp.route('/reports/stock/data')
def stock_data():
    """JSON endpoint for Tabulator.js stock report table."""
    query = Item.query
    
    # Apply filters
    category = request.args.get('category', '').strip()
    active_only = request.args.get('active_only', 'true').strip().lower()
    zero_stock = request.args.get('zero_stock', '').strip().lower()
    
    if category:
        query = query.filter(Item.category == category)
    if active_only == 'true':
        query = query.filter(Item.active == True)
    if zero_stock == 'show':
        # Show items with qty_on_hand <= 0
        query = query.filter(Item.qty_on_hand <= 0)
    elif zero_stock == 'hide':
        query = query.filter(Item.qty_on_hand > 0)
    
    items = query.order_by(Item.category, Item.description).all()
    
    grand_total = 0.0
    items_data = []
    for item in items:
        stock_value = item.qty_on_hand * item.avg_cost
        grand_total += stock_value
        
        # Get last movement date
        last_movement = StockMovement.query.filter_by(item_id=item.id).order_by(StockMovement.created_at.desc()).first()
        last_movement_date = last_movement.created_at.strftime('%Y-%m-%d') if last_movement else '-'
        
        items_data.append({
            'code': item.code,
            'description': item.description[:80] + '...' if len(item.description) > 80 else item.description,
            'category': item.category or '-',
            'qty_on_hand': item.qty_on_hand,
            'avg_cost': round(item.avg_cost, 2),
            'stock_value': round(stock_value, 2),
            'last_movement_date': last_movement_date,
            'active': 'Yes' if item.active else 'No'
        })
    
    return jsonify({
        'items': items_data,
        'grand_total': round(grand_total, 2),
        'total_items': len(items_data)
    })

@reports_bp.route('/reports/stock/export-csv')
def stock_export_csv():
    """Export Stock Report as CSV."""
    items = Item.query.filter_by(active=True).order_by(Item.category, Item.description).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Code', 'Description', 'Category', 'Qty on Hand', 'Avg. Cost (R)', 'Stock Value (R)', 'Last Movement Date'])
    
    grand_total = 0.0
    for item in items:
        stock_value = item.qty_on_hand * item.avg_cost
        grand_total += stock_value
        
        last_movement = StockMovement.query.filter_by(item_id=item.id).order_by(StockMovement.created_at.desc()).first()
        last_movement_date = last_movement.created_at.strftime('%Y-%m-%d') if last_movement else ''
        
        writer.writerow([item.code, item.description, item.category or '',
                        item.qty_on_hand, round(item.avg_cost, 2),
                        round(stock_value, 2), last_movement_date])
    
    writer.writerow([])
    writer.writerow(['', '', '', '', 'Grand Total (R)', round(grand_total, 2), ''])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=stock_report.csv'}
    )

@reports_bp.route('/reports/movements')
def movements():
    items = Item.query.filter_by(active=True).order_by(Item.code).all()
    return render_template('reports/movements.html', items=items)

@reports_bp.route('/reports/movements/data')
def movements_data():
    """JSON endpoint for Movement Report table."""
    query = StockMovement.query
    
    # Apply filters
    item_code = request.args.get('item_code', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    movement_type = request.args.get('movement_type', '').strip()
    
    if item_code:
        item = Item.query.filter_by(code=item_code).first()
        if item:
            query = query.filter(StockMovement.item_id == item.id)
        else:
            return jsonify({'movements': [], 'net_movement': 0, 'total_count': 0})
    
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockMovement.created_at >= dt_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            dt_to = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(StockMovement.created_at <= dt_to)
        except ValueError:
            pass
    
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    movements = query.order_by(StockMovement.created_at.desc()).all()
    
    net_movement = 0.0
    movements_data = []
    for m in movements:
        net_movement += m.qty_change
        movements_data.append({
            'date': m.created_at.strftime('%Y-%m-%d %H:%M'),
            'item_code': m.item.code if m.item else '-',
            'description': m.item.description[:60] if m.item else '-',
            'type': m.movement_type,
            'reference': m.reference or '-',
            'qty_change': m.qty_change,
            'qty_after': m.qty_after,
            'notes': m.notes or '',
            'created_by': m.created_by or '-'
        })
    
    return jsonify({
        'movements': movements_data,
        'net_movement': round(net_movement, 2),
        'total_count': len(movements_data)
    })

@reports_bp.route('/reports/movements/export-csv')
def movements_export_csv():
    """Export Movement Report as CSV."""
    query = StockMovement.query.order_by(StockMovement.created_at.desc())
    
    # Apply same filters as data endpoint
    item_code = request.args.get('item_code', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    movement_type = request.args.get('movement_type', '').strip()
    
    if item_code:
        item = Item.query.filter_by(code=item_code).first()
        if item:
            query = query.filter(StockMovement.item_id == item.id)
    
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockMovement.created_at >= dt_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            dt_to = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            query = query.filter(StockMovement.created_at <= dt_to)
        except ValueError:
            pass
    
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    movements = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Item Code', 'Description', 'Type', 'Reference', 'Qty Change', 'Qty After', 'Notes', 'By'])
    
    net_movement = 0.0
    for m in movements:
        net_movement += m.qty_change
        writer.writerow([
            m.created_at.strftime('%Y-%m-%d %H:%M'),
            m.item.code if m.item else '',
            m.item.description[:60] if m.item else '',
            m.movement_type,
            m.reference or '',
            m.qty_change,
            m.qty_after,
            m.notes or '',
            m.created_by or ''
        ])
    
    writer.writerow([])
    writer.writerow(['', '', '', '', 'Net Movement:', round(net_movement, 2), '', '', ''])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=movement_report.csv'}
    )