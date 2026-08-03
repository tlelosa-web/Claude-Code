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
        # The line matched, so no unmatched-lines warning flash is emitted.
        # (The picker's JS references the badge class names unconditionally,
        # so a raw "badge-cancelled" substring check is no longer meaningful.)
        assert "could not be auto-matched" not in body

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

    def test_matched_line_item_code_links_to_item(self, app, db, session, client):
        """A matched PO line's item code links to /items/<id> (see
        docs/specs/item-links-and-so-search-2026-07-15.md); an unmatched
        line does not."""
        item = Item(code="PO-LINK-TEST", description="Linked Item", qty_on_hand=0, active=True)
        session.add(item)
        session.flush()

        po = PurchaseOrder(po_number="PO-VIEW-TEST-002", supplier_name="Link Test Supplier", status='Open')
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, item_code_raw='PO-LINK-TEST',
                            description='Linked line', qty_ordered=1.0, qty_received=0.0))
        session.add(POLine(po_id=po.id, item_id=None, item_code_raw='UNMATCHED-CODE',
                            description='Unmatched line', qty_ordered=1.0, qty_received=0.0))
        session.commit()

        resp = client.get(f'/purchase-orders/{po.id}')
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert f'href="/items/{item.id}"' in body
        assert "Unmatched" in body


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

        lines_match = re.search(r'name="lines_json"[^>]*?value=\'(.*?)\'', body, re.DOTALL)
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


class TestPurchaseOrderEdit:
    """Edit screen: editability guard + delete-recreate line replacement."""
    _counter = 0

    def _next(self):
        TestPurchaseOrderEdit._counter += 1
        return f"PO-EDIT-{TestPurchaseOrderEdit._counter:03d}"

    def _edit_post(self, client, po_id, lines, **header):
        import json
        data = {
            'reference': header.get('reference', 'FM-EDIT'),
            'supplier_name': header.get('supplier_name', 'Edited Supplier'),
            'supplier_vat': header.get('supplier_vat', '9999999999'),
            'po_date': header.get('po_date', '2026-08-01'),
            'due_date': header.get('due_date', '2026-08-15'),
            'overall_discount_pct': header.get('overall_discount_pct', '0'),
            'lines_json': json.dumps(lines),
        }
        return client.post(f'/purchase-orders/{po_id}/edit', data=data, follow_redirects=True)

    def _line(self, item_id, item_code, qty=2.0, price=10.0):
        return {
            'item_code': item_code, 'matched_item_id': item_id, 'description': 'Edited line',
            'qty': qty, 'excl_price': price, 'disc_pct': 0, 'vat_pct': 15,
            'excl_total': qty * price, 'incl_total': qty * price * 1.15,
        }

    def _open_po_with_line(self, session, item, status='Open', qty_received=0.0):
        po = PurchaseOrder(po_number=self._next(), supplier_name="Orig Supplier", status=status)
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=item.id, item_code_raw=item.code,
                           description='Orig line', qty_ordered=5.0, qty_received=qty_received,
                           excl_price=10.0, excl_total=50.0, incl_total=57.5))
        session.commit()
        return po

    def test_editable_po_shows_edit_action_and_renders_form(self, app, db, session, client):
        item = Item(code=self._next(), description="Edit Item", qty_on_hand=0, active=True)
        session.add(item)
        session.commit()
        po = self._open_po_with_line(session, item)

        detail = client.get(f'/purchase-orders/{po.id}').get_data(as_text=True)
        assert f'/purchase-orders/{po.id}/edit' in detail

        edit = client.get(f'/purchase-orders/{po.id}/edit')
        assert edit.status_code == 200
        body = edit.get_data(as_text=True)
        assert "Save Changes" in body
        assert po.po_number in body

    def test_received_po_hides_edit_and_blocks_route(self, app, db, session, client):
        item = Item(code=self._next(), description="Recv Item", qty_on_hand=0, active=True)
        session.add(item)
        session.commit()
        po = self._open_po_with_line(session, item, status='Received', qty_received=5.0)

        detail = client.get(f'/purchase-orders/{po.id}').get_data(as_text=True)
        assert f'/purchase-orders/{po.id}/edit' not in detail

        blocked = client.get(f'/purchase-orders/{po.id}/edit', follow_redirects=True)
        assert "Cannot edit" in blocked.get_data(as_text=True)

    def test_open_po_with_receipt_blocks_edit(self, app, db, session, client):
        """An Open PO that already has a partial receipt is not editable."""
        item = Item(code=self._next(), description="Partial Item", qty_on_hand=0, active=True)
        session.add(item)
        session.commit()
        po = self._open_po_with_line(session, item, status='Open', qty_received=2.0)

        blocked = client.post(f'/purchase-orders/{po.id}/edit',
                              data={'lines_json': '[]'}, follow_redirects=True)
        assert "Cannot edit" in blocked.get_data(as_text=True)
        db.session.refresh(po)
        assert len(po.lines) == 1  # unchanged

    def test_edit_updates_header_and_replaces_lines(self, app, db, session, client):
        item_a = Item(code=self._next(), description="Item A", qty_on_hand=0, active=True)
        item_b = Item(code=self._next(), description="Item B", qty_on_hand=0, active=True)
        session.add_all([item_a, item_b])
        session.commit()
        po = self._open_po_with_line(session, item_a)

        resp = self._edit_post(client, po.id,
                               [self._line(item_a.id, item_a.code, qty=3.0),
                                self._line(item_b.id, item_b.code, qty=7.0)],
                               reference='FM-NEW', supplier_name='New Supplier')
        assert "updated successfully" in resp.get_data(as_text=True)

        db.session.refresh(po)
        assert po.reference == 'FM-NEW'
        assert po.supplier_name == 'New Supplier'
        assert len(po.lines) == 2
        qtys = sorted(line.qty_ordered for line in po.lines)
        assert qtys == [3.0, 7.0]
        assert {line.item_id for line in po.lines} == {item_a.id, item_b.id}

    def test_edit_draft_promotes_to_open(self, app, db, session, client):
        item = Item(code=self._next(), description="Draft Item", qty_on_hand=0, active=True)
        session.add(item)
        session.commit()
        po = self._open_po_with_line(session, item, status='Draft')
        assert po.status == 'Draft'

        self._edit_post(client, po.id, [self._line(item.id, item.code)])
        db.session.refresh(po)
        assert po.status == 'Open'

    def test_edit_links_previously_unmatched_line(self, app, db, session, client):
        item = Item(code=self._next(), description="Now Linked", qty_on_hand=0, active=True)
        session.add(item)
        session.flush()
        po = PurchaseOrder(po_number=self._next(), supplier_name="Orig", status='Open')
        session.add(po)
        session.flush()
        session.add(POLine(po_id=po.id, item_id=None, item_code_raw='RAW-CODE',
                           description='Unlinked', qty_ordered=1.0, qty_received=0.0,
                           excl_price=5.0, excl_total=5.0, incl_total=5.75))
        session.commit()

        self._edit_post(client, po.id, [self._line(item.id, item.code)])
        db.session.refresh(po)
        assert len(po.lines) == 1
        assert po.lines[0].item_id == item.id
