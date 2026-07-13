"""Regression tests for sales order upload flow."""
import os
from models import SalesOrder


def test_upload_pdf_with_line_items_renders_review(client):
    """A parsed PDF with line items should render review instead of failing to JSON."""
    pdf_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        os.path.join(os.path.dirname(__file__), 'fixtures', 'FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf'),
    )

    with open(pdf_path, "rb") as pdf_file:
        response = client.post(
            "/sales-orders/upload",
            data={"pdf_file": (pdf_file, "SO4603.pdf")},
            content_type="multipart/form-data",
        )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Step 2: Review & Save" in body
    assert "Object of type Undefined is not JSON serializable" not in body
    assert "Save Sales Order" in body


def test_upload_review_form_includes_payment_status_field(client):
    """The review/save form must let Payment Status be set before the first save."""
    pdf_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf'
    )

    with open(pdf_path, "rb") as pdf_file:
        response = client.post(
            "/sales-orders/upload",
            data={"pdf_file": (pdf_file, "SO4603.pdf")},
            content_type="multipart/form-data",
        )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="payment_status"' in body
    assert "Partially Paid" in body


def test_save_order_captures_payment_status(client):
    resp = client.post("/sales-orders/save", data={
        "so_number": "TEST-PAY-SAVE-001",
        "customer_name": "Test Co",
        "payment_status": "Partially Paid",
    })
    assert resp.status_code == 302

    so = SalesOrder.query.filter_by(so_number="TEST-PAY-SAVE-001").first()
    assert so.payment_status == "Partially Paid"


def test_save_order_defaults_payment_status_to_pending_when_omitted(client):
    resp = client.post("/sales-orders/save", data={
        "so_number": "TEST-PAY-SAVE-002",
        "customer_name": "Test Co",
    })
    assert resp.status_code == 302

    so = SalesOrder.query.filter_by(so_number="TEST-PAY-SAVE-002").first()
    assert so.payment_status == "Pending"
