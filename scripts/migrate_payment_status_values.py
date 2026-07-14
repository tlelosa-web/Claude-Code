"""One-off data migration: remap existing SalesOrder.payment_status values
from the old 6-value list ('Pending', 'Paid', 'Partially Paid', 'Unpaid',
'Account - Up to Date', 'On Hold') to the new 7-value Cash Sale / Account
list in PAYMENT_STATUS_OPTIONS.

See docs/specs/payment-status-cash-account-amount-paid.md
(section: "Data migration -- existing Sales Orders' payment_status values").

Mapping table (old -> new, confidence):
    Account - Up to Date -> Account - Up to Date   (direct match, unchanged)
    On Hold               -> Account - On Hold      (direct match, prefix added)
    Partially Paid        -> Cash Sale - Partial    (direct match -- only partial-payment
                                                      status in the new list)
    Pending                -> Account - Pending     (GUESS -- no record of whether it was
                                                      ever a cash sale)
    Paid                   -> Cash Sale - Paid      (GUESS -- could equally have been
                                                      Account - Up to Date)
    Unpaid                  -> Cash Sale - Unpaid   (GUESS -- could equally have been an
                                                      overdue/pending account)
    (anything else / null) -> Account - Pending     (fallback default)

Behaviour:
- Idempotent / safe to re-run: any SalesOrder whose payment_status is already
  one of the 7 new PAYMENT_STATUS_OPTIONS values is left untouched, so
  re-running after a manual correction to a guessed value won't clobber it.
- 'Partially Paid' -> 'Cash Sale - Partial' rows get amount_paid left at 0.0
  -- there is no historical record of how much was actually paid; fill in
  the real amount manually via the SO detail page for any that still matter.
- Prints a summary at the end: count mapped per old value, and an explicit
  list of SO numbers whose mapping fell into one of the three GUESS rows
  above, so they can be reviewed individually rather than the whole table.

Run once, manually, against instance/sops.db:
    python scripts/migrate_payment_status_values.py
This is a data transform, not a schema change, so it is intentionally NOT
part of ensure_schema_columns() self-heal -- it must be run deliberately.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, SalesOrder, PAYMENT_STATUS_OPTIONS

# old_value -> (new_value, is_guess)
MAPPING = {
    'Account - Up to Date': ('Account - Up to Date', False),
    'On Hold': ('Account - On Hold', False),
    'Partially Paid': ('Cash Sale - Partial', False),
    'Pending': ('Account - Pending', True),
    'Paid': ('Cash Sale - Paid', True),
    'Unpaid': ('Cash Sale - Unpaid', True),
}
FALLBACK = 'Account - Pending'


def migrate_payment_status_values(session=None):
    """Remap payment_status on every SalesOrder row per the mapping table.

    Rows already on one of the new PAYMENT_STATUS_OPTIONS values are left
    untouched (idempotency). Returns a summary dict:
        {
            'summary': {old_label: {'new_value': str, 'count': int}, ...},
            'guessed': [(so_number, old_value, new_value), ...],
            'skipped': int,  # rows already on a new-list value
        }
    """
    session = session or db.session
    summary = {}
    guessed = []
    skipped = 0

    orders = SalesOrder.query.all()
    for so in orders:
        old_value = so.payment_status

        if old_value in PAYMENT_STATUS_OPTIONS:
            skipped += 1
            continue

        if old_value in MAPPING:
            new_value, is_guess = MAPPING[old_value]
        else:
            new_value, is_guess = FALLBACK, False

        so.payment_status = new_value

        label = old_value if old_value else '(none)'
        entry = summary.setdefault(label, {'new_value': new_value, 'count': 0})
        entry['count'] += 1

        if is_guess:
            guessed.append((so.so_number, old_value, new_value))

    session.commit()
    return {'summary': summary, 'guessed': guessed, 'skipped': skipped}


def print_summary(result):
    summary = result['summary']
    guessed = result['guessed']
    skipped = result['skipped']

    print("Payment status data migration summary")
    print("======================================")
    if not summary and not skipped:
        print("No Sales Orders found.")
    else:
        for old_label in sorted(summary):
            info = summary[old_label]
            print(f"  {info['count']:4d}  {old_label!r:30s} -> {info['new_value']!r}")
        print(f"  {skipped:4d}  already on a new-list value (skipped, unchanged)")

    print()
    if guessed:
        print(f"{len(guessed)} row(s) mapped via a GUESS -- please review:")
        for so_number, old_value, new_value in guessed:
            print(f"  SO {so_number}: {old_value!r} -> {new_value!r}")
    else:
        print("No guessed mappings on this run (nothing flagged for review).")


def migrate():
    app = create_app()
    with app.app_context():
        result = migrate_payment_status_values()
        print_summary(result)


if __name__ == '__main__':
    migrate()
