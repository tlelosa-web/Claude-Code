from flask import Blueprint, render_template
from models import Item, SalesOrder, WorksOrder

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Gather statistics
    open_wos = WorksOrder.query.filter(WorksOrder.status.in_(['Open', 'In Progress'])).count()
    completed_wos = WorksOrder.query.filter_by(status='Complete').count()
    pending_sos = SalesOrder.query.filter_by(status='Draft').count()
    
    # Low stock items: items with qty_on_hand <= 10
    low_stock_count = Item.query.filter(Item.qty_on_hand <= 10.0, Item.active == True).count()
    
    # Recent works orders
    recent_wos = WorksOrder.query.order_by(WorksOrder.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        open_wos=open_wos,
        completed_wos=completed_wos,
        pending_sos=pending_sos,
        low_stock_count=low_stock_count,
        recent_wos=recent_wos
    )
