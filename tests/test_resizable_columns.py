"""Wiring checks for the resizable-column enhancement on the 4 list pages.

See docs/specs/payment-status-delivery-date-reopen-columns.md (Part D).
Drag-resize interaction itself isn't exercised here (no browser in this
suite) -- these confirm each list page loads the shared JS module,
initializes it against the right table id, and that the table itself
carries that id (i.e. at least one row renders).
"""
from datetime import datetime, timezone
from models import db, SalesOrder, WorksOrder, StockOrder, PurchaseOrder


def test_sales_orders_list_wires_resizable_columns(client, session):
    session.add(SalesOrder(so_number="RESIZE-SO-001", customer_name="Resize Test Co",
                           status="Open", created_at=datetime.now(timezone.utc)))
    session.commit()

    resp = client.get("/sales-orders?view=all")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "resizable_columns.js" in body
    assert "makeColumnsResizable('so-list-table')" in body
    assert 'id="so-list-table"' in body


def test_works_orders_list_wires_resizable_columns(client, session):
    so = SalesOrder(so_number="RESIZE-SO-002", customer_name="Resize Test Co",
                    status="Open", created_at=datetime.now(timezone.utc))
    session.add(so)
    session.flush()
    session.add(WorksOrder(wo_number="RESIZE-WO-001", so_id=so.id, order_type="ASSEMBLY",
                           status="Open", created_at=datetime.now(timezone.utc)))
    session.commit()

    resp = client.get("/works-orders?view=all")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "resizable_columns.js" in body
    assert "makeColumnsResizable('orders-table')" in body
    assert 'id="orders-table"' in body


def test_stock_orders_list_wires_resizable_columns(client, session):
    so = SalesOrder(so_number="RESIZE-SO-003", customer_name="Resize Test Co",
                    status="Open", created_at=datetime.now(timezone.utc))
    session.add(so)
    session.flush()
    session.add(StockOrder(stock_order_number="RESIZE-STO-001", so_id=so.id, status="Open",
                           created_at=datetime.now(timezone.utc)))
    session.commit()

    resp = client.get("/stock-orders?view=all")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "resizable_columns.js" in body
    assert "makeColumnsResizable('sto-list-table')" in body
    assert 'id="sto-list-table"' in body


def test_purchase_orders_list_wires_resizable_columns(client, session):
    session.add(PurchaseOrder(po_number="RESIZE-PO-001", supplier_name="Resize Supplier",
                              status="Draft", created_at=datetime.now(timezone.utc)))
    session.commit()

    resp = client.get("/purchase-orders?view=all")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "resizable_columns.js" in body
    assert "makeColumnsResizable('po-list-table')" in body
    assert 'id="po-list-table"' in body
