"""Tests for services/movement_history_importer.py — AMU + suggested
Min/Max reorder levels from Sage's ItemMovementReport.csv.

See docs/specs/amu-minmax-reorder-suggestion-2026-07-17.md.
"""
import csv
import os

import pytest

from models import Item
from services.movement_history_importer import (
    import_amu_minmax_from_csv,
    round_amu_half,
)


def _write_movement_csv(tmp_path, blocks, filename='ItemMovementReport.csv'):
    """Write a fixture CSV mirroring the real Sage export format: a title
    row, three metadata rows, then per-item blocks of an item-name row
    followed by transaction rows and a "Total for Item:" row.

    `blocks` is a list of (item_name_row, [transaction_rows]) tuples, where
    each transaction row is (date, reference, description, customer_supplier, qty).
    """
    filepath = os.path.join(tmp_path, filename)
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Item Movement Report'])   # title row
        writer.writerow(['Company: Fan Movement'])   # metadata row 1
        writer.writerow(['Printed: 01/01/2026'])      # metadata row 2
        writer.writerow([])                            # metadata row 3

        for item_name, transactions in blocks:
            writer.writerow([item_name])
            for txn in transactions:
                writer.writerow(list(txn))
            writer.writerow(['Total for Item:', '', '', '', str(len(transactions))])

    return filepath


class TestRoundAmuHalf:

    def test_zero_or_negative_floors_to_one(self):
        assert round_amu_half(0) == 1.0
        assert round_amu_half(-5) == 1.0

    def test_rounds_up_to_next_half(self):
        assert round_amu_half(1.1) == 1.5
        assert round_amu_half(2.0) == 2.0
        assert round_amu_half(2.01) == 2.5


class TestImportAmuMinmaxFromCsv:

    def test_purchased_and_sold_split_by_description(self, app, db, session, tmp_path):
        """Supplier Invoice rows count as purchased, Tax Invoice rows count
        as sold; other descriptions count as neither."""
        item = Item(code='MOVE-SPLIT', description='Split Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-SPLIT - Split Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '10'),
                ('01/01/2026', 'REF2', 'Tax Invoice', 'Customer B', '4'),
                ('01/01/2026', 'REF3', 'Journal Entry', 'Other', '99'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        # Single-month period -> period_months = 1, amu_raw = max(10, 4) / 1 = 10
        assert item.amu == round_amu_half(10.0)

    def test_period_months_single_month(self, app, db, session, tmp_path):
        """All transactions in the same month -> period_months = 1."""
        item = Item(code='MOVE-PERIOD1', description='Period Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-PERIOD1 - Period Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '6'),
                ('15/01/2026', 'REF2', 'Supplier Invoice', 'Supplier A', '6'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        # total_purchased = 12, period_months = 1 -> amu_raw = 12
        assert item.amu == round_amu_half(12.0)

    def test_period_months_multi_month(self, app, db, session, tmp_path):
        """Transactions spanning several months divides the total by the
        number of months between first and last transaction."""
        item = Item(code='MOVE-PERIOD3', description='Multi Period Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-PERIOD3 - Multi Period Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '30'),
                ('01/04/2026', 'REF2', 'Supplier Invoice', 'Supplier A', '0'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        # period_months = 3 (Jan -> Apr), total_purchased = 30, amu_raw = 10
        assert item.amu == round_amu_half(10.0)

    def test_minmax_formula_with_set_lead_time(self, app, db, session, tmp_path):
        """Min/Max reuses the already-stored Item.lead_time_weeks - not
        re-parsed from a PO report."""
        item = Item(code='MOVE-LT', description='Lead Time Widget', active=True,
                     lead_time_weeks=8.66)  # -> 2.0 months
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-LT - Lead Time Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '10'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        # amu_raw = 10 -> amu = round_amu_half(10.0) = 10.0
        # lead_time_months = round(8.66/4.33, 1) = 2.0
        # min_qty = round(10.0 * 2.0) = 20
        # max_qty = 20 + round(10.0 * 2) = 40
        assert item.amu == 10.0
        assert item.suggested_min == 20
        assert item.suggested_max == 40

    def test_minmax_formula_floors_to_half_month_when_lead_time_unset(self, app, db, session, tmp_path):
        """lead_time_weeks = 0 (not yet imported) floors lead_time_months
        to 0.5, matching AvgMovement's own floor behavior."""
        item = Item(code='MOVE-NOLT', description='No Lead Time Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-NOLT - No Lead Time Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '4'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        # amu_raw = 4 -> amu = round_amu_half(4.0) = 4.0
        # lead_time_months floors to 0.5
        # min_qty = round(4.0 * 0.5) = 2
        # max_qty = 2 + round(4.0 * 2) = 10
        assert item.amu == 4.0
        assert item.suggested_min == 2
        assert item.suggested_max == 10

    def test_zero_transaction_item_block_still_gets_floor_amu(self, app, db, session, tmp_path):
        """An item block present in the CSV with zero purchase/sale rows
        still gets the amu_raw <= 0 -> amu = 1.0 floor."""
        item = Item(code='MOVE-EMPTY', description='Empty Block Widget', active=True)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-EMPTY - Empty Block Widget', []),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        assert item.amu == 1.0

    def test_unmatched_item_codes_skipped_not_created(self, app, db, session, tmp_path):
        blocks = [
            ('NO-SUCH-CODE - Ghost Item', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '10'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        updated, unmatched = import_amu_minmax_from_csv(filepath)

        assert updated == 0
        assert unmatched == 1
        assert Item.query.filter_by(code='NO-SUCH-CODE').first() is None

    def test_items_absent_from_csv_left_untouched(self, app, db, session, tmp_path):
        """Items not present in the CSV at all keep their default 0.0 -
        never force-defaulted to the AMU floor."""
        present = Item(code='MOVE-PRESENT', description='Present Widget', active=True)
        absent = Item(code='MOVE-ABSENT', description='Absent Widget', active=True)
        session.add_all([present, absent])
        session.commit()

        blocks = [
            ('MOVE-PRESENT - Present Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '10'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(present)
        db.session.refresh(absent)
        assert present.amu != 0.0
        assert absent.amu == 0.0
        assert absent.suggested_min == 0.0
        assert absent.suggested_max == 0.0

    def test_qty_on_hand_qty_on_order_reorder_fields_untouched(self, app, db, session, tmp_path):
        """This importer must never write qty_on_hand, qty_on_order, or
        the manually-curated reorder_point/max_level fields."""
        item = Item(code='MOVE-QTY', description='Qty Widget', active=True,
                     qty_on_hand=123.0, reorder_point=5.0, max_level=50.0)
        session.add(item)
        session.commit()

        blocks = [
            ('MOVE-QTY - Qty Widget', [
                ('01/01/2026', 'REF1', 'Supplier Invoice', 'Supplier A', '999'),
            ]),
        ]
        filepath = _write_movement_csv(str(tmp_path), blocks)

        import_amu_minmax_from_csv(filepath)

        db.session.refresh(item)
        assert item.qty_on_hand == 123.0
        assert item.reorder_point == 5.0
        assert item.max_level == 50.0
        assert not hasattr(item, 'qty_on_order')

    def test_raises_file_not_found_for_missing_csv(self, app, db, session, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_amu_minmax_from_csv(os.path.join(str(tmp_path), 'does-not-exist.csv'))
