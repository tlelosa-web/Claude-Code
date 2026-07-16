"""Tests for services/settings_service.py - the generic key/value Setting
table backing the Settings module (currency symbol first use case).

See docs/specs/po-price-date-columns-currency-settings-2026-07-16.md.
"""
import pytest
from models import Setting
from services.settings_service import get_setting, set_setting, get_currency_symbol


@pytest.fixture
def restore_currency_symbol(session):
    """The Setting table is shared/cumulative across the whole pytest
    session (same convention as test_dashboard.py's shared-DB note) - always
    put currency_symbol back to 'R' after a test that changes it, so later
    tests/pages aren't affected."""
    yield
    set_setting('currency_symbol', 'R')


class TestGetSetting:
    def test_get_setting_returns_default_when_key_missing(self, app, db, session):
        assert Setting.query.filter_by(key='does_not_exist').first() is None
        assert get_setting('does_not_exist', 'fallback') == 'fallback'

    def test_get_setting_returns_seeded_currency_default_when_row_absent(self, app, db, session, restore_currency_symbol):
        # Delete the seeded row (created by app bootstrap / migration script)
        # to exercise the "unset" path explicitly.
        Setting.query.filter_by(key='currency_symbol').delete()
        session.commit()

        assert get_setting('currency_symbol') == 'R'  # falls back to DEFAULT_SETTINGS
        assert get_currency_symbol() == 'R'


class TestSetSetting:
    def test_set_setting_persists_and_is_read_back(self, app, db, session, restore_currency_symbol):
        set_setting('currency_symbol', '$')
        assert get_setting('currency_symbol') == '$'
        assert get_currency_symbol() == '$'

    def test_set_setting_updates_existing_key_without_creating_duplicate(self, app, db, session, restore_currency_symbol):
        set_setting('currency_symbol', '$')
        set_setting('currency_symbol', '€')  # Euro sign

        rows = Setting.query.filter_by(key='currency_symbol').all()
        assert len(rows) == 1
        assert rows[0].value == '€'
