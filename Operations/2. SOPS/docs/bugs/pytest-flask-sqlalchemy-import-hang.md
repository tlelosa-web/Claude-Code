# pytest / flask_sqlalchemy Import Hang

## Status

Open

## Observed

During the project reorganisation verification pass on 2026-05-21:

- `tests/test_pdf_parser.py` passed: 2 tests.
- `tests/test_item_importer.py` passed: 4 tests.
- `tests/test_bom_builder.py` passed: 4 tests.
- `rg "cdn\\." templates` returned no matches.
- `rg "fonts\\.googleapis" static` returned no matches.
- Full `pytest -q` exceeded the timeout.
- Isolated `tests/test_stock_service.py` also exceeded the timeout after repeated runs.
- A direct `python -c "import flask_sqlalchemy"` later hung in the local `venv`.

An earlier stock-service run exposed a Windows console encoding failure from Unicode status glyphs printed in `app.py`; those prints were changed to ASCII.

## Impact

Full test-suite status cannot be marked green until the import hang is reproduced and resolved cleanly.

## Next Checks

- Recreate or repair the local virtual environment.
- Verify `flask_sqlalchemy` and SQLAlchemy versions against `requirements.txt`.
- Re-run `python -c "import flask_sqlalchemy; print('ok')"`.
- Re-run `python -m pytest -q`.

