from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import nullslast
from models import db, WorksOrder, BOMLine, Item, SalesOrder, StockOrder
from routes.sales_orders import can_close_sales_order
from services.doc_generator import get_works_order_print_context
from services.stock_service import issue, reverse_issue, produce, reverse_production
from services.order_filters import WO_ACTIVE
from services.status_change_log import log_change, track_report_status

works_orders_bp = Blueprint('works_orders', __name__)

@works_orders_bp.route('/works-orders')
def list_orders():
    view = request.args.get('view', 'open')
    query = (WorksOrder.query
             .join(SalesOrder, WorksOrder.so_id == SalesOrder.id, isouter=True))
    if view == 'open':
        query = query.filter(WorksOrder.status.in_(WO_ACTIVE))
    elif view == 'closed':
        query = query.filter(~WorksOrder.status.in_(WO_ACTIVE))
    orders = query.order_by(nullslast(SalesOrder.delivery_date.asc())).all()
    return render_template('works_orders/list.html', orders=orders, view=view)

@works_orders_bp.route('/works-orders/<int:order_id>')
def view_order(order_id):
    wo = WorksOrder.query.get_or_404(order_id)
    context = get_works_order_print_context(order_id)
    return render_template('works_orders/detail.html', **context)

@works_orders_bp.route('/works-orders/<int:order_id>/print')
def print_order(order_id):
    """Render print-friendly Works Order or Picking List page."""
    wo = WorksOrder.query.get_or_404(order_id)

    # First print flips Open -> Released (guarded to fire once — reprinting
    # an already-Released-or-later WO must not re-trigger or downgrade
    # anything). See docs/specs/sales-order-report-excel-export-2026-07-17.md
    # Decision 1.
    if wo.status == 'Open':
        with track_report_status(wo.sales_order):
            wo.status = 'Released'
            log_change('WO', wo.id, wo.wo_number, 'status', 'Open', 'Released')
        db.session.commit()

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
        old_status = wo.status
        with track_report_status(wo.sales_order):
            # Issue stock for each BOM line (only deduct qty_issued)
            for bom_line in wo.bom_lines:
                # Assembly header lines represent the finished product, not a stored
                # component, so they must never be issued from stores.
                if bom_line.line_type == 'ASSEMBLY_ITEM':
                    if bom_line.item.is_stocked_finished_good:
                        produce(
                            item_id=bom_line.item_id,
                            qty=bom_line.qty_required,
                            reference=wo.wo_number,
                            notes=f"Produced by {wo.wo_number} ({wo.sales_order.job_reference if wo.sales_order else ''})",
                            created_by=request.form.get('completed_by', 'System').strip() or 'System'
                        )
                        bom_line.qty_issued = bom_line.qty_required
                    continue
                qty_to_issue = (bom_line.qty_required or 0.0) - bom_line.qty_issued
                if qty_to_issue > 0:
                    issue(
                        item_id=bom_line.item_id,
                        qty=qty_to_issue,
                        reference=wo.wo_number,
                        notes=f"Issued for {wo.wo_number} ({wo.sales_order.job_reference if wo.sales_order else ''})",
                        created_by=request.form.get('completed_by', 'System').strip() or 'System'
                    )
                    bom_line.qty_issued = bom_line.qty_required

            wo.status = 'Complete'
            wo.completed_at = datetime.now()
            log_change('WO', wo.id, wo.wo_number, 'status', old_status, 'Complete')
            db.session.flush()  # Flush to save before checking related WOs

            # Check if the Sales Order can be closed — all WOs and STOs must be Complete/Cancelled
            if wo.sales_order:
                can_close, _ = can_close_sales_order(wo.sales_order.id)
                if can_close:
                    wo.sales_order.status = 'Closed'
                    db.session.flush()

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

    old_status = wo.status
    with track_report_status(wo.sales_order):
        wo.status = 'Cancelled'
        # Guard against logging a no-op (already-Cancelled) transition —
        # this route has no guard preventing a re-POST on an already
        # cancelled WO, so old_status could already be 'Cancelled'.
        if old_status != 'Cancelled':
            log_change('WO', wo.id, wo.wo_number, 'status', old_status, 'Cancelled')
    db.session.commit()

    flash(f"Works Order {wo.wo_number} has been cancelled.", "success")
    return redirect(url_for('works_orders.view_order', order_id=order_id))

@works_orders_bp.route('/works-orders/<int:order_id>/reopen', methods=['POST'])
def reopen_order(order_id):
    """Reopen a Complete or Cancelled Works Order, reversing any issued stock."""
    wo = WorksOrder.query.get_or_404(order_id)

    if wo.status not in ('Complete', 'Cancelled'):
        flash(f"Works Order {wo.wo_number} is not Complete or Cancelled — nothing to reopen.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))

    try:
        old_status = wo.status
        with track_report_status(wo.sales_order):
            if wo.status == 'Complete':
                for bom_line in wo.bom_lines:
                    if bom_line.line_type == 'ASSEMBLY_ITEM':
                        if bom_line.qty_issued > 0:
                            reverse_production(
                                item_id=bom_line.item_id,
                                qty=bom_line.qty_issued,
                                reference=wo.wo_number,
                                notes=f"Production reversed on reopen of {wo.wo_number}",
                                created_by=request.form.get('reopened_by', 'System').strip() or 'System'
                            )
                            bom_line.qty_issued = 0.0
                        continue
                    if bom_line.qty_issued > 0:
                        reverse_issue(
                            item_id=bom_line.item_id,
                            qty=bom_line.qty_issued,
                            reference=wo.wo_number,
                            notes=f"Reversed on reopen of {wo.wo_number}",
                            created_by=request.form.get('reopened_by', 'System').strip() or 'System'
                        )
                        bom_line.qty_issued = 0.0

            wo.status = 'Open'
            wo.completed_at = None
            log_change('WO', wo.id, wo.wo_number, 'status', old_status, 'Open')
            db.session.flush()

            # Cascade: if the parent SO was auto-closed because this WO completed, reopen it too.
            if wo.sales_order and wo.sales_order.status == 'Closed':
                wo.sales_order.status = 'Open'
                db.session.flush()

        db.session.commit()
        flash(f"Works Order {wo.wo_number} has been reopened.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error reopening Works Order: {str(e)}", "error")

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

    if wo.status == 'Cancelled':
        flash(f"Picking List {wo.wo_number} is cancelled and cannot be picked.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))

    try:
        for bom_line in wo.bom_lines:
            qty_to_pick = (bom_line.qty_required or 0.0) - bom_line.qty_issued
            if qty_to_pick > 0:
                issue(
                    item_id=bom_line.item_id,
                    qty=qty_to_pick,
                    reference=wo.wo_number,
                    notes=f"Picked for {wo.wo_number} ({wo.sales_order.job_reference if wo.sales_order else ''})",
                    created_by=request.form.get('picked_by', 'System').strip() or 'System'
                )
                bom_line.qty_issued = bom_line.qty_required
        
        wo.status = 'Complete'
        wo.completed_at = datetime.now()
        db.session.flush()  # Flush to save before checking related WOs
        
        # Check if the Sales Order can be closed — all WOs and STOs must be Complete/Cancelled
        if wo.sales_order:
            can_close, _ = can_close_sales_order(wo.sales_order.id)
            if can_close:
                wo.sales_order.status = 'Closed'
                db.session.flush()
        
        db.session.commit()
        
        flash(f"Picking List {wo.wo_number} confirmed. Stock deducted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error confirming pick: {str(e)}", "error")
    
    return redirect(url_for('works_orders.view_order', order_id=order_id))

@works_orders_bp.route('/works-orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    """Delete a Works Order or Picking List. Only allowed for Open, Released, or In Progress status."""
    wo = WorksOrder.query.get_or_404(order_id)
    
    if wo.status in ('Complete', 'Cancelled'):
        flash(f"Cannot delete a completed or cancelled Works Order.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    wo_number = wo.wo_number
    
    # Delete all BOMLine records for this WO
    BOMLine.query.filter_by(wo_id=wo.id).delete()
    
    # Delete the WO record
    db.session.delete(wo)
    db.session.commit()
    
    flash(f"Works Order {wo_number} deleted successfully.", "success")
    return redirect(url_for('works_orders.list_orders'))


@works_orders_bp.route('/works-orders/<int:order_id>/edit', methods=['GET'])
def edit_order(order_id):
    """Render edit form pre-populated with existing BOM lines."""
    wo = WorksOrder.query.get_or_404(order_id)

    if wo.status not in ['Open', 'Released', 'In Progress']:
        flash(f"Cannot edit Works Order {wo.wo_number}. Status is {wo.status}.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))

    # Load existing BOM lines structured for edit UI
    from services.doc_generator import get_works_order_print_context
    context = get_works_order_print_context(order_id)
    
    # Also load catalogue for adding new items
    items = Item.query.filter_by(active=True).order_by(Item.category, Item.code).all()
    from routes.sales_orders import item_to_bom_json
    from services.demand import get_qty_on_order_bulk, get_qty_committed_bulk, get_next_po_due_bulk
    item_ids = [item.id for item in items]
    qty_on_order_map = get_qty_on_order_bulk(item_ids=item_ids)
    qty_committed_map = get_qty_committed_bulk(item_ids=item_ids, exclude_wo_id=order_id)
    next_po_due_map = get_next_po_due_bulk(item_ids=item_ids)
    item_payload = [
        item_to_bom_json(
            item,
            qty_on_order=qty_on_order_map.get(item.id, 0.0),
            qty_committed=qty_committed_map.get(item.id, 0.0),
            next_po_due=next_po_due_map.get(item.id),
        )
        for item in items
    ]
    categories = db.session.query(Item.category).filter(
        Item.active == True, Item.category != None
    ).distinct().order_by(Item.category).all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('works_orders/edit.html', 
                          **context,
                          items=item_payload,
                          categories=categories)


@works_orders_bp.route('/works-orders/<int:order_id>/edit', methods=['POST'])
def update_order(order_id):
    """Receive updated BOM lines JSON, replace BOMLines, redirect to detail."""
    import json
    wo = WorksOrder.query.get_or_404(order_id)

    if wo.status not in ['Open', 'Released', 'In Progress']:
        flash(f"Cannot edit Works Order {wo.wo_number}. Status is {wo.status}.", "error")
        return redirect(url_for('works_orders.view_order', order_id=order_id))

    try:
        # Parse updated BOM items
        items_json = request.form.get('bom_items_json', '[]')
        try:
            items_data = json.loads(items_json)
        except json.JSONDecodeError:
            flash("Invalid BOM data.", "error")
            return redirect(url_for('works_orders.edit_order', order_id=order_id))
        
        if not items_data:
            flash("At least one item is required.", "error")
            return redirect(url_for('works_orders.edit_order', order_id=order_id))
        
        # Delete all existing BOM lines (cascade handles this)
        BOMLine.query.filter_by(wo_id=wo.id).delete()
        db.session.flush()
        
        # Re-create BOM lines using same logic as bom_builder
        for item_data in items_data:
            item_id = item_data['item_id']
            qty_required = float(item_data['qty_required'])
            notes = item_data.get('notes', '')
            line_type = item_data.get('line_type', 'COMPONENT')
            components = item_data.get('components', [])
            
            item = db.session.get(Item, item_id)
            if not item:
                raise ValueError(f"Item with id {item_id} not found.")
            
            unit_cost = item.avg_cost if item.avg_cost > 0 else item.last_cost
            
            bom_line = BOMLine(
                wo_id=wo.id,
                item_id=item_id,
                qty_required=qty_required,
                qty_issued=0.0,  # Reset issued qty on edit
                unit_cost=unit_cost,
                notes=notes,
                line_type=line_type
            )
            db.session.add(bom_line)
            db.session.flush()
            
            # Handle nested components
            if line_type == 'ASSEMBLY_ITEM' and components:
                for comp_data in components:
                    comp_item = db.session.get(Item, comp_data['item_id'])
                    if not comp_item:
                        raise ValueError(f"Component item with id {comp_data['item_id']} not found.")
                    
                    comp_unit_cost = comp_item.avg_cost if comp_item.avg_cost > 0 else comp_item.last_cost
                    
                    comp_line = BOMLine(
                        wo_id=wo.id,
                        item_id=comp_data['item_id'],
                        qty_required=float(comp_data['qty_required']),
                        qty_issued=0.0,
                        unit_cost=comp_unit_cost,
                        notes=comp_data.get('notes', ''),
                        line_type='COMPONENT',
                        parent_line_id=bom_line.id
                    )
                    db.session.add(comp_line)
        
        db.session.commit()
        flash(f"Works Order {wo.wo_number} updated successfully.", "success")
        return redirect(url_for('works_orders.view_order', order_id=order_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating Works Order: {str(e)}", "error")
        return redirect(url_for('works_orders.edit_order', order_id=order_id))