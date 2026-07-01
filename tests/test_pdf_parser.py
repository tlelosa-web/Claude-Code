"""Tests for pdf_parser module."""
import pytest
import os
import sys

class TestPDFParser:
    
    def test_parse_known_fields(self):
        """Test that pdf parser extracts fields from the SO4603 fixture."""
        from services.pdf_parser import parse_sales_order_pdf
        
        # Get the fixture PDF path
        pdf_path = os.path.join(os.path.dirname(__file__), 'fixtures',
                                'FM4087 - ARCTIC AIR - Sales Order - SO4603.pdf')
        
        if not os.path.exists(pdf_path):
            pytest.skip(f"Fixture PDF not found at {pdf_path}")
        
        result = parse_sales_order_pdf(pdf_path)
        
        # Verify basic structure
        assert result is not None
        assert 'so_number' in result
        assert 'customer_name' in result
        assert 'line_items' in result
        assert 'raw_pdf_text' in result
        assert 'parse_errors' in result
        
        # Check we got raw text
        assert len(result['raw_pdf_text']) > 0
        
        # SO number should contain SO
        if result['so_number']:
            assert result['so_number'].startswith('SO')
    
    def test_parse_multipage_captures_all_line_items(self):
        """Line items on page 2+ must be captured, not dropped at the page-1 footer.

        SO4684 spans 2 pages; the 'BANKING DETAILS'/'Total Discount:' footer is
        repeated on every page of the template, and the full header (title,
        FROM/TO blocks, column header) repeats before page 2's items resume.
        """
        from services.pdf_parser import parse_sales_order_pdf

        pdf_path = os.path.join(os.path.dirname(__file__), 'fixtures',
                                'FM4167-4771 - Vortron - Sales Order - SO4684.pdf')

        if not os.path.exists(pdf_path):
            pytest.skip(f"Fixture PDF not found at {pdf_path}")

        result = parse_sales_order_pdf(pdf_path)

        assert result['parse_errors'] == []
        assert result['so_number'] == 'SO4684'
        assert len(result['line_items']) == 16

        total_excl = sum(li['excl_total'] for li in result['line_items'])
        assert total_excl == pytest.approx(241125.00)

        # Last 4 items live on page 2 and must not be garbage/header noise
        page2_descriptions = [li['description'] for li in result['line_items'][-4:]]
        assert page2_descriptions == [
            '630-1000AVMS - 630 to 1000 NDB GREEN Neoprene Floor Mounts',
            '800CF - 800 Diam Counter Flange',
            '800MF - 800 Diam Mounting Feet',
            '800S1.5DP - 800 Diam Silencer 1.5D Podded',
        ]

    def test_parse_error_handling(self):
        """Test that parser returns partial results on error (not crash)."""
        from services.pdf_parser import parse_sales_order_pdf
        
        # Try parsing a file that doesn't exist
        result = parse_sales_order_pdf('/nonexistent/file.pdf')
        
        # Should return a dict with errors, not crash
        assert result is not None
        assert 'parse_errors' in result
        assert len(result['parse_errors']) > 0
        assert result['so_number'] == ''
        assert result['line_items'] == []