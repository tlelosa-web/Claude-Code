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