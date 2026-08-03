"""Tests for routes/settings.py (GET/POST /settings) and the
app.context_processor that injects currency_symbol into every template.

See docs/specs/po-price-date-columns-currency-settings-2026-07-16.md.
"""
import pytest
from services.settings_service import set_setting, get_currency_symbol


@pytest.fixture
def restore_currency_symbol(session):
    """Setting rows persist across the whole pytest session (shared DB) -
    always restore currency_symbol to 'R' after a test changes it."""
    yield
    set_setting('currency_symbol', 'R')


class TestSettingsGet:
    def test_get_renders_current_value(self, client, restore_currency_symbol):
        set_setting('currency_symbol', '£')

        response = client.get('/settings')
        assert response.status_code == 200
        assert 'value="£"'.encode() in response.data


class TestSettingsPost:
    def test_post_updates_value_and_reflected_on_next_get(self, client, restore_currency_symbol):
        response = client.post('/settings', data={'currency_symbol': '$'}, follow_redirects=True)
        assert response.status_code == 200
        assert get_currency_symbol() == '$'

        response = client.get('/settings')
        assert 'value="$"'.encode() in response.data

    def test_post_blank_value_is_rejected(self, client, restore_currency_symbol):
        set_setting('currency_symbol', 'R')

        response = client.post('/settings', data={'currency_symbol': '   '}, follow_redirects=True)
        assert response.status_code == 200
        assert b'cannot be blank' in response.data
        # No change was made.
        assert get_currency_symbol() == 'R'


class TestCurrencyContextProcessor:
    def test_changed_currency_symbol_is_reflected_on_dashboard(self, client, restore_currency_symbol):
        set_setting('currency_symbol', '$')

        response = client.get('/')
        html = response.get_data(as_text=True)
        assert '$' in html
        # Proves the context processor is wired to the live Setting value,
        # not the literal old default hardcoded anywhere in the template.
        assert 'stat-val" style="--accent: var(--brand-primary); color: var(--accent);">R ' not in html
