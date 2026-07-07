"""Tests for the purchase_orders blueprint: upload/match, save, receive, cancel, link-item."""
import os
import pytest
from models import db, Item, PurchaseOrder, POLine, StockMovement

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


class TestPurchaseOrderUpload:

    def test_upload_matches_known_item_code(self, client, session):
        """PO4106 (ATTENU-TEC, 1 line, code 800S1.5DP) should auto-match when
        the item already exists in the catalogue."""
        item = Item(code="800S1.5DP", description="800 Diam Silencer 1.5D Podded", qty_on_hand=0, active=True)
        session.add(item)
        session.commit()

        pdf_path = os.path.join(FIXTURES_DIR, 'FM4171 - ATTENU-TEC - Supplier Purchase Order - PO4106.pdf')
        with open(pdf_path, "rb") as pdf_file:
            response = client.post(
                "/purchase-orders/upload",
                data={"pdf_file": (pdf_file, "PO4106.pdf")},
                content_type="multipart/form-data",
            )

        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Step 2: Review & Save" in body
        assert "badge-complete" in body  # "Matched" badge rendered
        assert "badge-cancelled" not in body  # no "Unmatched" badge rendered

    def test_upload_flags_unmatched_item_code(self, client, session):
        """PO4088 (LUFT) line codes don't exist in an empty test catalogue -
        every line should be flagged Unmatched, not crash."""
        pdf_path = os.path.join(FIXTURES_DIR, 'FM4167-4171 - LUFT - Supplier Purchase Order - PO4088.pdf')
        with open(pdf_path, "rb") as pdf_file:
            response = client.post(
                "/purchase-orders/upload",
                data={"pdf_file": (pdf_file, "PO4088.pdf")},
                content_type="multipart/form-data",
            )

        body = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Step 2: Review & Save" in body
        assert "Unmatched" in body
        assert "could not be auto-matched" in body


class TestPurchaseOrderSaveReceiveCancel:
    _counter = 0

    def _next_po_number(self):
        TestPurchaseOrderSaveReceiveCancel._counter += 1
        return f"PO-TEST-{TestPurchaseOrderSaveReceiveCancel._counter:03d}"

    def _save_po(self, client, po_number, item_id, item_code, qty=4.0, excl_price=20.0):
        import json
        lines = [{
            'item_code': item_code,
            'matched_item_id': item_id,
            'description': 'Test line',
            'qty': qty,
            'excl_price': excl_price,
            'disc_pct': 0,
            'vat_pct': 15,
            'excl_total': qty * excl_price,
            'incl_total': qty * excl_price * 1.15,
        }]
        return client.post('/purchase-orders/save', data={
            'po_number': po_number,
            'reference': 'FM-TEST',
            'supplier_name': 'Test Supplier',
            'supplier_vat': '1234567890',
            'po_date': '2026-07-01',
            'due_date': '2026-07-15',
            'overall_discount_pct': '0',
            'raw_pdf_text': '',
            'lines_json': json.dumps(lines),
        }, follow_redirects=True)

    def test_save_requires_po_number(self, client):
        response = client.post('/purchase-orders/save', data={}, follow_redirects=True)
        assert response.status_code == 200
        assert "Purchase Order number is required" in response.get_data(as_text=True)

    def test_full_receive_updates_stock_and_status(self, app, db, session, client):
        item = Item(code=self._next_po_number(), description="Test Item", qty_on_hand=10.0,
                    last_cost=0.0, active=True)
        session.add(item)
        session.commit()

        po_number = self._next_po_number()
        response = self._save_po(client, po_number, item.id, item.code, qty=4.0, excl_price=25.0)
        assert response.status_code == 200
        assert f"Purchase Order {po_number} saved successfully" in response.get_data(as_text=True)

        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        assert po is not None
        assert po.status == 'Open'
        line = po.lines[0]
        assert line.item_id == item.id

        response = client.post(f'/purchase-orders/{po.id}/receive',
                               data={f'receive_qty_{line.id}': '4'},
                               follow_redirects=True)
        assert response.status_code == 200
        assert "receipt recorded" in response.get_data(as_text=True)

        db.session.refresh(item)
        db.session.refresh(po)
        assert item.qty_on_hand == 14.0
        assert item.last_cost == 25.0
        assert po.status == 'Received'

        movement = StockMovement.query.filter_by(item_id=item.id, movement_type='RECEIPT').first()
        assert movement is not None
        assert movement.reference == po_number
        assert movement.qty_change == 4.0

    def test_partial_receive_then_complete(self, app, db, session, client):
        item = Item(code=self._next_po_number(), description="Test Item", qty_on_hand=0.0, active=True)
        session.add(item)
        session.commit()

        po_number = self._next_po_number()
        self._save_po(client, po_number, item.id, item.code, qty=10.0, excl_price=5.0)
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        line = po.lines[0]

        client.post(f'/purchase-orders/{po.id}/receive', data={f'receive_qty_{line.id}': '6'},
                   follow_redirects=True)
        db.session.refresh(po)
        assert po.status == 'Partially Received'

        client.post(f'/purchase-orders/{po.id}/receive', data={f'receive_qty_{line.id}': '4'},
                   follow_redirects=True)
        db.session.refresh(po)
        db.session.refresh(item)
        assert po.status == 'Received'
        assert item.qty_on_hand == 10.0

    def test_receive_blocked_when_line_unlinked(self, app, db, session, client):
        po_number = self._next_po_number()
        po = PurchaseOrder(po_number=po_number, supplier_name="Test Supplier", status='Open')
        session.add(po)
        session.flush()
        line = POLine(po_id=po.id, item_id=None, item_code_raw='NOPE-CODE',
                     description='Unlinked line', qty_ordered=5.0, qty_received=0.0,
                     excl_price=10.0, excl_total=50.0, incl_total=57.5)
        session.add(line)
        session.commit()

        response = client.post(f'/purchase-orders/{po.id}/receive',
                               data={f'receive_qty_{line.id}': '5'}, follow_redirects=True)
        assert "not linked to a catalogue item" in response.get_data(as_text=True)
        db.session.refresh(po)
        assert po.status == 'Open'

    def test_link_item_then_receive_succeeds(self, app, db, session, client):
        po_number = self._next_po_number()
        po = PurchaseOrder(po_number=po_number, supplier_name="Test Supplier", status='Open')
        session.add(po)
        session.flush()
        line = POLine(po_id=po.id, item_id=None, item_code_raw='LINK-ME',
                     description='Needs linking', qty_ordered=3.0, qty_received=0.0,
                     excl_price=10.0, excl_total=30.0, incl_total=34.5)
        session.add(line)
        item = Item(code='LINK-ME', description="Linkable item", qty_on_hand=0.0, active=True)
        session.add(item)
        session.commit()

        response = client.post(f'/purchase-orders/{po.id}/link-item',
                               data={'line_id': line.id, 'item_code': 'LINK-ME'},
                               follow_redirects=True)
        assert "Line linked to LINK-ME" in response.get_data(as_text=True)
        db.session.refresh(line)
        assert line.item_id == item.id

        response = client.post(f'/purchase-orders/{po.id}/receive',
                               data={f'receive_qty_{line.id}': '3'}, follow_redirects=True)
        assert "receipt recorded" in response.get_data(as_text=True)

    def test_cancel_blocked_after_receipt(self, app, db, session, client):
        item = Item(code=self._next_po_number(), description="Test Item", qty_on_hand=0.0, active=True)
        session.add(item)
        session.commit()

        po_number = self._next_po_number()
        self._save_po(client, po_number, item.id, item.code, qty=2.0, excl_price=10.0)
        po = PurchaseOrder.query.filter_by(po_number=po_number).first()
        line = po.lines[0]

        client.post(f'/purchase-orders/{po.id}/receive', data={f'receive_qty_{line.id}': '2'},
                   follow_redirects=True)
        db.session.refresh(po)
        assert po.status == 'Received'

        response = client.post(f'/purchase-orders/{po.id}/cancel', follow_redirects=True)
        assert "already has receipts recorded" in response.get_data(as_text=True)
        db.session.refresh(po)
        assert po.status == 'Received'


class TestPurchaseOrderListDetailPrint:
    def test_list_detail_print_render(self, app, db, session, client):
        po = PurchaseOrder(po_number="PO-VIEW-TEST-001", supplier_name="View Test Supplier", status='Open')
        session.add(po)
        session.commit()

        list_resp = client.get('/purchase-orders')
        assert list_resp.status_code == 200
        assert "PO-VIEW-TEST-001" in list_resp.get_data(as_text=True)

        detail_resp = client.get(f'/purchase-orders/{po.id}')
        assert detail_resp.status_code == 200
        assert "PO-VIEW-TEST-001" in detail_resp.get_data(as_text=True)

        print_resp = client.get(f'/purchase-orders/{po.id}/print')
        assert print_resp.status_code == 200
        assert "PURCHASE ORDER" in print_resp.get_data(as_text=True)


class TestPurchaseOrderFullLifecycleFromRealPDF:
    """End-to-end: real PDF upload -> scrape the review form's hidden
    lines_json exactly as a browser would submit it -> save -> receive.
    Distinct from the synthetic-payload tests above, which don't exercise
    the actual upload->save HTML round trip."""

    def test_upload_save_receive_attenutec_po(self, app, db, session, client):
        import re
        import html
        import json

        # Reused across test methods in this file (same session-scoped
        # in-memory DB) - get-or-create avoids a UNIQUE constraint clash
        # with test_upload_matches_known_item_code, which needs the exact
        # same real fixture code to test auto-matching.
        item = Item.query.filter_by(code="800S1.5DP").first()
        if not item:
            item = Item(code="800S1.5DP", description="800 Diam Silencer 1.5D Podded",
                        qty_on_hand=0.0, last_cost=0.0, active=True)
            session.add(item)
            session.commit()
        else:
            item.qty_on_hand = 0.0
            item.last_cost = 0.0
            session.commit()

        pdf_path = os.path.join(FIXTURES_DIR, 'FM4171 - ATTENU-TEC - Supplier Purchase Order - PO4106.pdf')
        with open(pdf_path, "rb") as pdf_file:
            upload_resp = client.post(
                "/purchase-orders/upload",
                data={"pdf_file": (pdf_file, "PO4106.pdf")},
                content_type="multipart/form-data",
            )
        body = upload_resp.get_data(as_text=True)
        assert upload_resp.status_code == 200
        assert 'value="PO4106"' in body  # po_number pre-filled from the parser

        lines_match = re.search(r'name="lines_json" value=\'(.*?)\'', body, re.DOTALL)
        assert lines_match, "lines_json hidden field not found in rendered review page"
        lines_json_raw = html.unescape(lines_match.group(1))
        parsed_lines = json.loads(lines_json_raw)
        assert len(parsed_lines) == 1
        assert parsed_lines[0]['matched_item_id'] == item.id

        save_resp = client.post('/purchase-orders/save', data={
            'po_number': 'PO4106',
            'reference': 'FM4171',
            'supplier_name': 'ATTENU-TEC',
            'supplier_vat': '4690241338',
            'po_date': '2026-07-06',
            'due_date': '2026-07-20',
            'overall_discount_pct': '0',
            'raw_pdf_text': '',
            'lines_json': lines_json_raw,
        }, follow_redirects=True)
        assert save_resp.status_code == 200
        assert "Purchase Order PO4106 saved successfully" in save_resp.get_data(as_text=True)

        po = PurchaseOrder.query.filter_by(po_number='PO4106').first()
        assert po is not None
        assert len(po.lines) == 1
        line = po.lines[0]
        assert line.item_id == item.id
        assert line.qty_ordered == 4.0

        receive_resp = client.post(f'/purchase-orders/{po.id}/receive',
                                   data={f'receive_qty_{line.id}': '4'}, follow_redirects=True)
        assert "receipt recorded" in receive_resp.get_data(as_text=True)

        db.session.refresh(item)
        db.session.refresh(po)
        assert item.qty_on_hand == 4.0
        assert item.last_cost == pytest.approx(4423.00)
        assert po.status == 'Received'
