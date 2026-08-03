"""Tests for the Purchase Order PDF parser (services/po_parser.py)."""
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


class TestPOParser:

    def test_parse_luft_po(self):
        """PO4088 - LUFT: 5 line items, multi-degree impellers, header fields."""
        from services.po_parser import parse_purchase_order_pdf

        pdf_path = os.path.join(FIXTURES_DIR, 'FM4167-4171 - LUFT - Supplier Purchase Order - PO4088.pdf')
        if not os.path.exists(pdf_path):
            pytest.skip(f"Fixture PDF not found at {pdf_path}")

        result = parse_purchase_order_pdf(pdf_path)

        assert result['parse_errors'] == []
        assert result['po_number'] == 'PO4088'
        assert result['reference'] == 'FM4167-4171'
        assert result['supplier_name'] == 'LUFT INDUSTRIES NATAL (PTY) LTD'
        assert result['supplier_vat'] == '4050151630'
        assert result['po_date'].isoformat() == '2026-06-26'
        assert result['due_date'].isoformat() == '2026-06-30'
        assert result['overall_discount_pct'] == 0.0
        assert len(result['line_items']) == 5

        total_excl = sum(li['excl_total'] for li in result['line_items'])
        assert total_excl == pytest.approx(35076.60)

    def test_parse_attenutec_po(self):
        """PO4106 - ATTENU-TEC: single line item, single-word supplier name."""
        from services.po_parser import parse_purchase_order_pdf

        pdf_path = os.path.join(FIXTURES_DIR, 'FM4171 - ATTENU-TEC - Supplier Purchase Order - PO4106.pdf')
        if not os.path.exists(pdf_path):
            pytest.skip(f"Fixture PDF not found at {pdf_path}")

        result = parse_purchase_order_pdf(pdf_path)

        assert result['parse_errors'] == []
        assert result['po_number'] == 'PO4106'
        assert result['reference'] == 'FM4171'
        assert result['supplier_name'] == 'ATTENU-TEC'
        assert result['supplier_vat'] == '4690241338'
        assert result['po_date'].isoformat() == '2026-07-06'
        assert result['due_date'].isoformat() == '2026-07-20'
        assert len(result['line_items']) == 1
        assert result['line_items'][0]['qty'] == 4.0
        assert result['line_items'][0]['excl_total'] == pytest.approx(17692.00)

    def test_parse_error_handling(self):
        """Parser must never crash - returns partial results with parse_errors."""
        from services.po_parser import parse_purchase_order_pdf

        result = parse_purchase_order_pdf('/nonexistent/file.pdf')

        assert result is not None
        assert len(result['parse_errors']) > 0
        assert result['po_number'] == ''
        assert result['line_items'] == []


class TestSplitItemCode:

    def test_splits_on_first_separator_only(self):
        from services.po_parser import split_item_code

        code, desc = split_item_code(
            "IMP0560B150A10AR19080 - Impeller 0560mm 'B' 150A10AR 19mm 080Frame Deg00 - 15 DEG"
        )
        assert code == 'IMP0560B150A10AR19080'
        assert desc == "Impeller 0560mm 'B' 150A10AR 19mm 080Frame Deg00 - 15 DEG"

    def test_no_separator_returns_empty_code(self):
        from services.po_parser import split_item_code

        code, desc = split_item_code("No separator here")
        assert code == ''
        assert desc == 'No separator here'

    def test_empty_description(self):
        from services.po_parser import split_item_code

        code, desc = split_item_code('')
        assert code == ''
        assert desc == ''
