from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.settings_service import get_currency_symbol, set_setting

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings', methods=['GET'])
def index():
    return render_template('settings/index.html', currency_symbol=get_currency_symbol())


@settings_bp.route('/settings', methods=['POST'])
def update():
    currency_symbol = request.form.get('currency_symbol', '').strip()
    if not currency_symbol:
        flash("Currency symbol cannot be blank.", "error")
        return redirect(url_for('settings.index'))

    set_setting('currency_symbol', currency_symbol)
    flash("Settings updated.", "success")
    return redirect(url_for('settings.index'))
