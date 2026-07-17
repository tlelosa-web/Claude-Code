"""Tests for routes/items.py — Import Supplier/Lead Time route.

See docs/specs/supplier-lead-time-import-2026-07-17.md.
"""
import csv
import io

from models import Item


def _build_po_by_item_csv_bytes():
    """Build an in-memory CSV mirroring the real Sage export format, for
    upload via the test client."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Outstanding PO by Item Report'])
    writer.writerow(['Company: Fan Movement'])
    writer.writerow(['Printed: 01/01/2026'])
    writer.writerow([])
    writer.writerow(['ROUTE-ITEM-001 - Route Test Widget'])
    writer.writerow(['01/01/2026', 'REF1', 'PO001', 'Supplier Route', '15/01/2026', 'Pending', '10'])
    writer.writerow(['Total for Item:', '', '', '', '', '', '1'])
    return io.BytesIO(buf.getvalue().encode('utf-8'))


class TestImportSupplierLeadtimeRoute:

    def test_get_renders_form(self, app, db, session, client):
        response = client.get('/items/import-supplier-leadtime')
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert 'Import' in body

    def test_post_with_valid_file_updates_matching_items_and_flashes_summary(self, app, db, session, client):
        item = Item(code='ROUTE-ITEM-001', description='Route Test Widget', active=True)
        session.add(item)
        session.commit()

        data = {
            'csv_file': (_build_po_by_item_csv_bytes(), 'OutstandingPOByItemReport.csv'),
        }
        response = client.post(
            '/items/import-supplier-leadtime',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert '1 items updated' in body
        assert '0 item codes not found in catalogue' in body

        db.session.refresh(item)
        assert item.supplier == 'Supplier Route'
        assert item.lead_time_weeks == 2.0

    def test_post_without_file_flashes_error(self, app, db, session, client):
        response = client.post(
            '/items/import-supplier-leadtime',
            data={},
            content_type='multipart/form-data',
            follow_redirects=True,
        )

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert 'Please choose a CSV file' in body
