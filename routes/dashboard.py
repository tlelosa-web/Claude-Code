from sqlalchemy import nullslast
from flask import Blueprint, render_template
from models import Item, SalesOrder, WorksOrder
from services.order_filters import SO_ACTIVE, WO_ACTIVE
from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Gather statistics
    open_wos = WorksOrder.query.filter(WorksOrder.status.in_(WO_ACTIVE)).count()
    completed_wos = WorksOrder.query.filter_by(status='Complete').count()
    pending_sos = SalesOrder.query.filter_by(status='Draft').count()

    # Open Sales Orders (Draft + Open, excludes Closed) - shown as a
    # dedicated dashboard table so open work is visible at a glance.
    open_sales_orders = (SalesOrder.query
                          .filter(SalesOrder.status.in_(SO_ACTIVE))
                          .order_by(nullslast(SalesOrder.delivery_date.asc()))
                          .limit(10)
                          .all())
    
    # Low stock items: items with qty_on_hand <= 10
    low_stock_count = Item.query.filter(Item.qty_on_hand <= 10.0, Item.active == True).count()

    # Items below their reorder point (Enhancement 2 - reorder point
    # signals), netted against qty_on_order / qty_committed (Enhancement 3)
    # so this stat agrees with the Stock Report's below_reorder flag rather
    # than comparing raw qty_on_hand. reorder_point defaults to 0.0,
    # meaning "not set" - only items with an explicit reorder_point > 0 are
    # counted, otherwise every unconfigured item would falsely show as
    # below reorder. The reorder_point > 0 filter stays SQL-side as a cheap
    # pre-filter; netting happens in Python for just the narrowed-down set.
    reorder_candidates = Item.query.filter(
        Item.reorder_point > 0, Item.active == True
    ).all()
    candidate_ids = [item.id for item in reorder_candidates]
    qty_on_order_map = get_qty_on_order_bulk(item_ids=candidate_ids)
    qty_committed_map = get_qty_committed_bulk(item_ids=candidate_ids)
    reorder_count = sum(
        1
        for item in reorder_candidates
        if (item.qty_on_hand or 0.0)
        + qty_on_order_map.get(item.id, 0.0)
        - qty_committed_map.get(item.id, 0.0)
        <= item.reorder_point
    )

    # Recent works orders
    recent_wos = WorksOrder.query.order_by(WorksOrder.created_at.desc()).limit(5).all()

    # Total Sales Value card: Draft + Open SOs only (same SO_ACTIVE set as
    # the Open Sales Orders table above), split by payment_status prefix.
    active_sos = SalesOrder.query.filter(SalesOrder.status.in_(SO_ACTIVE)).all()
    total_value = sum(so.total_incl for so in active_sos)
    cash_sale_value = sum(
        so.total_incl for so in active_sos
        if so.payment_status and so.payment_status.startswith('Cash Sale')
    )
    account_value = sum(
        so.total_incl for so in active_sos
        if so.payment_status and so.payment_status.startswith('Account')
    )

    return render_template(
        'dashboard.html',
        open_wos=open_wos,
        completed_wos=completed_wos,
        pending_sos=pending_sos,
        low_stock_count=low_stock_count,
        reorder_count=reorder_count,
        recent_wos=recent_wos,
        open_sales_orders=open_sales_orders,
        total_value=total_value,
        cash_sale_value=cash_sale_value,
        account_value=account_value
    )
