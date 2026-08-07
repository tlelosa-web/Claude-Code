"""Site-specific submit adapters.

The only package in this project that may import `playwright` (alongside
`src/submission/browser.py`). Adapters never touch the database and never
transition vacancy status — `pipeline.py` and `prep.py` own all persistence,
which is what makes it impossible for an adapter to route around the human
approval gate.
"""
