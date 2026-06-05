"""Regression tests for sales order upload flow."""
import os


def test_upload_pdf_with_line_items_renders_review(client):
    """A parsed PDF with line items should render review instead of failing to JSON."""
    pdf_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf",
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
