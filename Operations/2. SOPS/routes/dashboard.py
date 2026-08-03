from datetime import date, timedelta
from sqlalchemy import func, nullslast
from flask import Blueprint, render_template
from models import db, Item, SalesOrder, WorksOrder
from services.order_filters import SO_ACTIVE, WO_ACTIVE
from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk

dashboard_bp = Blueprint('dashboard', __name__)

# Works Orders created per day, last 7 days (oldest to newest) - feeds the
# dashboard's trend area chart. Geometry is precomputed here rather than in
# the template since there's no JS charting library (SOPS is 100% offline).
_TREND_DAYS = 7
_TREND_WIDTH = 640
_TREND_HEIGHT = 180
_TREND_PAD_TOP = 16
_TREND_PAD_BOTTOM = 28
# Horizontal inset so the first/last day labels and point circles sit fully
# inside the chart card - the card's overflow:hidden clips anything flush
# against x=0 or x=width.
_TREND_PAD_X = 20


def _build_wo_trend_chart():
    start_day = date.today() - timedelta(days=_TREND_DAYS - 1)
    rows = (
        db.session.query(WorksOrder.created_at)
        .filter(WorksOrder.created_at >= start_day)
        .all()
    )
    day_counts = {start_day + timedelta(days=i): 0 for i in range(_TREND_DAYS)}
    for (created_at,) in rows:
        day = created_at.date()
        if day in day_counts:
            day_counts[day] += 1

    days = sorted(day_counts.keys())
    counts = [day_counts[d] for d in days]
    max_count = max(counts)
    # 20% headroom so a peak point isn't flush against the top edge; falls
    # back to 1 when every day is zero so the chart still renders a flat
    # baseline instead of dividing by zero.
    scale_max = max_count * 1.2 if max_count > 0 else 1

    chart_h = _TREND_HEIGHT - _TREND_PAD_TOP - _TREND_PAD_BOTTOM
    baseline = _TREND_PAD_TOP + chart_h
    x_step = (_TREND_WIDTH - 2 * _TREND_PAD_X) / (_TREND_DAYS - 1)

    points = []
    for i, (day, count) in enumerate(zip(days, counts)):
        x = round(_TREND_PAD_X + i * x_step, 1)
        y = round(_TREND_PAD_TOP + chart_h * (1 - count / scale_max), 1)
        points.append({'x': x, 'y': y, 'label': day.strftime('%a'), 'count': count})

    line_path = 'M ' + ' L '.join(f"{p['x']},{p['y']}" for p in points)
    area_path = (
        f"M {points[0]['x']},{baseline} "
        + ' '.join(f"L {p['x']},{p['y']}" for p in points)
        + f" L {points[-1]['x']},{baseline} Z"
    )
    gridlines = [round(_TREND_PAD_TOP + chart_h * frac, 1) for frac in (0.0, 0.5, 1.0)]

    return {
        'points': points,
        'line_path': line_path,
        'area_path': area_path,
        'width': _TREND_WIDTH,
        'height': _TREND_HEIGHT,
        'baseline': baseline,
        'gridlines': gridlines,
        'total': sum(counts),
    }


# Works Order status breakdown - feeds the dashboard's concentric status
# rings. Ordered outer-to-inner from most-complete to least, reusing the
# same badge colors already used everywhere else a WO status renders
# (routes/dashboard.py stays consistent with .badge-{status} in main.css).
_WO_STATUS_RINGS = [
    {'status': 'Complete', 'color': 'var(--fm-green)', 'radius': 70},
    {'status': 'In Progress', 'color': 'var(--fm-orange)', 'radius': 56},
    {'status': 'Released', 'color': 'var(--fm-teal)', 'radius': 42},
    {'status': 'Open', 'color': 'var(--fm-blue)', 'radius': 28},
    {'status': 'Cancelled', 'color': '#9CA3AF', 'radius': 14},
]


def _build_wo_status_rings():
    counts = dict(
        db.session.query(WorksOrder.status, func.count(WorksOrder.id))
        .group_by(WorksOrder.status)
        .all()
    )
    total = sum(counts.values())
    rings = []
    for spec in _WO_STATUS_RINGS:
        count = counts.get(spec['status'], 0)
        pct = round((count / total) * 100, 1) if total else 0
        rings.append({**spec, 'count': count, 'pct': pct})
    return {'rings': rings, 'total': total}

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
        account_value=account_value,
        wo_trend=_build_wo_trend_chart(),
        wo_status_rings=_build_wo_status_rings()
    )
