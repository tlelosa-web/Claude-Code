"""Tests for services/po_by_item_importer.py — Supplier + Lead Time import
from Sage's OutstandingPOByItemReport.csv.

See docs/specs/supplier-lead-time-import-2026-07-17.md.
"""
import csv
import os

from models import Item


def _write_po_by_item_csv(tmp_path, blocks, filename='OutstandingPOByItemReport.csv'):
    """Write a fixture CSV mirroring the real Sage export format: a title
    row, three metadata rows, then per-item blocks of an item-name row
    followed by transaction rows and a "Total for Item:" row.

    `blocks` is a list of (item_name_row, [transaction_rows]) tuples, where
    each transaction row is (date, reference, order_no, supplier,
    delivery_date, status, qty).
    """
    filepath = os.path.join(tmp_path, filename)
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Outstanding PO by Item Report'])  # title row
        writer.writerow(['Company: Fan Movement'])           # metadata row 1
        writer.writerow(['Printed: 01/01/2026'])              # metadata row 2
        writer.writerow([])                                    # metadata row 3

        for item_name, transactions in blocks:
            writer.writerow([item_name])
            for txn in transactions:
                writer.writerow(list(txn))
            writer.writerow(['Total for Item:', '', '', '', '', '', str(len(transactions))])

    return filepath


class TestImportSupplierLeadTimeFromCsv:

    def test_most_frequent_supplier_wins(self, app, db, session, tmp_path):
        """Supplier appearing in the most transaction rows for an item wins,
        matching AvgMovement's top_supplier logic (mode by transaction
        count)."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        item = Item(code='PO-ITEM-001', description='Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('PO-ITEM-001 - Widget', [
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '15/01/2026', 'Pending', '10'),
                ('01/02/2026', 'REF2', 'PO002', 'Supplier B', '20/02/2026', 'Pending', '5'),
                ('01/03/2026', 'REF3', 'PO003', 'Supplier A', '10/03/2026', 'Pending', '8'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        updated, unmatched = import_supplier_lead_time_from_csv(filepath)

        assert updated == 1
        assert unmatched == 0

        db.session.refresh(item)
        assert item.supplier == 'Supplier A'

    def test_tie_breakable_case_first_seen_supplier_wins(self, app, db, session, tmp_path):
        """When two suppliers tie on transaction count, the first-encountered
        supplier wins (Counter.most_common is stable on insertion order)."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        item = Item(code='PO-ITEM-TIE', description='Tie Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('PO-ITEM-TIE - Tie Widget', [
                ('01/01/2026', 'REF1', 'PO001', 'Supplier X', '15/01/2026', 'Pending', '10'),
                ('01/02/2026', 'REF2', 'PO002', 'Supplier Y', '20/02/2026', 'Pending', '5'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        import_supplier_lead_time_from_csv(filepath)

        db.session.refresh(item)
        assert item.supplier == 'Supplier X'

    def test_lead_time_averaging(self, app, db, session, tmp_path):
        """lead_time_weeks is the average of (Delivery Date - Date) in
        weeks across rows with a valid delivery date."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        item = Item(code='PO-ITEM-LT', description='Lead Time Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('PO-ITEM-LT - Lead Time Widget', [
                # 14 days -> 2.0 weeks
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '15/01/2026', 'Pending', '10'),
                # 28 days -> 4.0 weeks
                ('01/02/2026', 'REF2', 'PO002', 'Supplier A', '01/03/2026', 'Pending', '5'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        import_supplier_lead_time_from_csv(filepath)

        db.session.refresh(item)
        assert item.lead_time_weeks == 3.0

    def test_missing_and_malformed_delivery_dates_excluded_from_average(self, app, db, session, tmp_path):
        """Rows with a missing or malformed Delivery Date are excluded from
        the lead time average, not treated as zero."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        item = Item(code='PO-ITEM-BADDATE', description='Bad Date Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('PO-ITEM-BADDATE - Bad Date Widget', [
                # Valid: 7 days -> 1.0 week
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '08/01/2026', 'Pending', '10'),
                # Missing delivery date
                ('01/02/2026', 'REF2', 'PO002', 'Supplier A', '', 'Pending', '5'),
                # Malformed delivery date
                ('01/03/2026', 'REF3', 'PO003', 'Supplier A', 'not-a-date', 'Pending', '8'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        import_supplier_lead_time_from_csv(filepath)

        db.session.refresh(item)
        assert item.lead_time_weeks == 1.0

    def test_unmatched_item_codes_skipped_not_created(self, app, db, session, tmp_path):
        """Item codes with no matching Item.code in SOPS are counted as
        unmatched and never created."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        blocks = [
            ('NO-SUCH-CODE - Ghost Item', [
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '15/01/2026', 'Pending', '10'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        updated, unmatched = import_supplier_lead_time_from_csv(filepath)

        assert updated == 0
        assert unmatched == 1
        assert Item.query.filter_by(code='NO-SUCH-CODE').first() is None

    def test_qty_on_hand_and_qty_on_order_fields_untouched(self, app, db, session, tmp_path):
        """This importer must never write qty_on_hand, or import/derive an
        on-order figure from the CSV - SOPS already computes qty_on_order
        live from internal PurchaseOrders."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        item = Item(code='PO-ITEM-QTY', description='Qty Widget', active=True,
                     qty_on_hand=123.0)
        session.add(item)
        session.commit()

        blocks = [
            ('PO-ITEM-QTY - Qty Widget', [
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '15/01/2026', 'Pending', '999'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        import_supplier_lead_time_from_csv(filepath)

        db.session.refresh(item)
        assert item.qty_on_hand == 123.0
        assert not hasattr(item, 'qty_on_order')

    def test_mixed_matched_and_unmatched_codes(self, app, db, session, tmp_path):
        """Multiple item blocks: matched codes updated, unmatched codes
        counted separately, both correctly reported."""
        from services.po_by_item_importer import import_supplier_lead_time_from_csv

        matched = Item(code='PO-ITEM-MATCHED', description='Matched Widget', active=True)
        session.add(matched)
        session.commit()

        blocks = [
            ('PO-ITEM-MATCHED - Matched Widget', [
                ('01/01/2026', 'REF1', 'PO001', 'Supplier A', '15/01/2026', 'Pending', '10'),
            ]),
            ('PO-ITEM-UNMATCHED - Unmatched Widget', [
                ('01/01/2026', 'REF2', 'PO002', 'Supplier B', '15/01/2026', 'Pending', '10'),
            ]),
        ]
        filepath = _write_po_by_item_csv(str(tmp_path), blocks)

        updated, unmatched = import_supplier_lead_time_from_csv(filepath)

        assert updated == 1
        assert unmatched == 1

        db.session.refresh(matched)
        assert matched.supplier == 'Supplier A'

    def test_raises_file_not_found_for_missing_csv(self, app, db, session, tmp_path):
        from services.po_by_item_importer import import_supplier_lead_time_from_csv
        import pytest

        with pytest.raises(FileNotFoundError):
            import_supplier_lead_time_from_csv(os.path.join(str(tmp_path), 'does-not-exist.csv'))
