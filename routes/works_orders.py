from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, WorksOrder, BOMLine, Item, SalesOrder
from services.doc_generator import get_works_order_print_context
from services.stock_service import issue

works_orders_bp = Blueprint('works_orders', __name__)

@works_orders_bp.route('/works-orders')
def list_orders():
    orders = WorksOrder.query.order_by(WorksOrder.created_at.desc()).all()
    return render_template('works_orders/list.html', orders=orders)

@works_orders_bp.route('/works-orders/<int:order_id>')
def view_order(order_id):
    wo = WorksOrder.query.get_or_404(order_id)
    context = get_works_order_print_context(order_id)
    return render_template('works_orders/detail.html', **context)

@works_orders_bp.route('/works-orders/<int:order_id>/print')
def print_order(order_id):
    """Render print-friendly Works Order or Picking List page."""
    wo = WorksOrder.query.get_or_404(order_id)
    context = get_works_order_print_context(order_id)
    
    if wo.order_type == 'ASSEMBLY':
        return render_template('works_orders/works_order_print.html', **context)
    else:
        return render_template('works_orders/picking_list_print.html', **context)

@works_orders_bp.route('/works-orders/<int:order_id>/complete', methods=['POST'])
def mark_complete(order_id):
    """Mark a Works Order as Complete and issue all stock."""
    wo = WorksOrder.query.get_or_404(order_id)
    
    if wo.status == 'Complete':
        flash(f"Works Order {wo.wo_number} is already complete.", "warning")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    if wo.status == 'Cancelled':
        flash(f"Works Order {wo.wo_number} is cancelled and cannot be completed.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    try:
        # Issue stock for each BOM line (only deduct qty_issued)
        for bom_line in wo.bom_lines:
            qty_to_issue = bom_line.qty_required - bom_line.qty_issued
            if qty_to_issue > 0:
                issue(
                    item_id=bom_line.item_id,
                    qty=qty_to_issue,
                    reference=wo.wo_number,
                    notes=f"Issued for {wo.wo_number} ({wo.sales_order.so_number if wo.sales_order else ''})",
                    created_by=request.form.get('completed_by', 'System').strip() or 'System'
                )
                bom_line.qty_issued = bom_line.qty_required
        
        wo.status = 'Complete'
        wo.completed_at = datetime.utcnow()
        db.session.commit()
        
        flash(f"Works Order {wo.wo_number} marked as Complete. Stock deducted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error completing Works Order: {str(e)}", "error")
    
    return redirect(url_for('works_orders.view_order', order_id=order_id))

@works_orders_bp.route('/works-orders/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel a Works Order."""
    wo = WorksOrder.query.get_or_404(order_id)
    
    if wo.status == 'Complete':
        flash(f"Works Order {wo.wo_number} is already complete and cannot be cancelled.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    wo.status = 'Cancelled'
    db.session.commit()
    
    flash(f"Works Order {wo.wo_number} has been cancelled.", "success")
    return redirect(url_for('works_orders.view_order', order_id=order_id))

@works_orders_bp.route('/works-orders/<int:order_id>/confirm-pick', methods=['POST'])
def confirm_pick(order_id):
    """Confirm picking for Stock Orders — issue stock."""
    wo = WorksOrder.query.get_or_404(order_id)
    
    if wo.order_type != 'STOCK':
        flash("This action is only for Stock Orders / Picking Lists.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    if wo.status == 'Complete':
        flash(f"Picking List {wo.wo_number} is already completed.", "warning")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    try:
        for bom_line in wo.bom_lines:
            qty_to_pick = bom_line.qty_required - bom_line.qty_issued
            if qty_to_pick > 0:
                issue(
                    item_id=bom_line.item_id,
                    qty=qty_to_pick,
                    reference=wo.wo_number,
                    notes=f"Picked for {wo.wo_number} ({wo.sales_order.so_number if wo.sales_order else ''})",
                    created_by=request.form.get('picked_by', 'System').strip() or 'System'
                )
                bom_line.qty_issued = bom_line.qty_required
        
        wo.status = 'Complete'
        wo.completed_at = datetime.utcnow()
        db.session.commit()
        
        flash(f"Picking List {wo.wo_number} confirmed. Stock deducted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error confirming pick: {str(e)}", "error")
    
    return redirect(url_for('works_orders.view_order', order_id=order_id))