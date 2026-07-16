"""Small service layer for the generic key/value Setting table.

See docs/specs/po-price-date-columns-currency-settings-2026-07-16.md
(Part C) - a Settings module with a system currency setting, extensible
for future settings, not a single-purpose currency column.
"""
from models import db, Setting

DEFAULT_SETTINGS = {'currency_symbol': 'R'}


def get_setting(key, default=None):
    row = Setting.query.filter_by(key=key).first()
    return row.value if row else DEFAULT_SETTINGS.get(key, default)


def set_setting(key, value):
    row = Setting.query.filter_by(key=key).first()
    if row:
        row.value = value
    else:
        row = Setting(key=key, value=value)
        db.session.add(row)
    db.session.commit()


def get_currency_symbol():
    return get_setting('currency_symbol', 'R')
