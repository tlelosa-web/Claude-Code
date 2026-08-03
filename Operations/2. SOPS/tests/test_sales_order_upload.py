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
    assert "Cash Sale - Partial" in body


def test_save_order_captures_payment_status(client):
    resp = client.post("/sales-orders/save", data={
        "so_number": "TEST-PAY-SAVE-001",
        "customer_name": "Test Co",
        "payment_status": "Cash Sale - Partial",
    })
    assert resp.status_code == 302

    so = SalesOrder.query.filter_by(so_number="TEST-PAY-SAVE-001").first()
    assert so.payment_status == "Cash Sale - Partial"


def test_save_order_defaults_payment_status_to_account_pending_when_omitted(client):
    resp = client.post("/sales-orders/save", data={
        "so_number": "TEST-PAY-SAVE-002",
        "customer_name": "Test Co",
    })
    assert resp.status_code == 302

    so = SalesOrder.query.filter_by(so_number="TEST-PAY-SAVE-002").first()
    assert so.payment_status == "Account - Pending"


def test_reupload_pdf_for_existing_so_renders_review(client, session):
    """Reupload POST branch must render 200 with payment status options, not 500
    (missing payment_status_options previously crashed Jinja's unconditional loop)."""
    so = SalesOrder(so_number="TEST-REUPLOAD-001", customer_name="Test Co", status="Draft")
    session.add(so)
    session.commit()

    pdf_path = os.path.join(
        os.path.dirname(__file__), 'fixtures', 'FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf'
    )

    with open(pdf_path, "rb") as pdf_file:
        response = client.post(
            f"/sales-orders/{so.id}/reupload",
            data={"pdf_file": (pdf_file, "SO4603.pdf")},
            content_type="multipart/form-data",
        )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="payment_status"' in body
    assert "Cash Sale - Partial" in body
