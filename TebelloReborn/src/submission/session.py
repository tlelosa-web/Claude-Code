"""Playwright session-state (`storageState`) path resolution.

Imports nothing from playwright, on purpose. The browser adapter that will
consume this path is a separate, later task; keeping the resolution here means
the submission core stays runnable and fully testable with no browser installed,
which is what keeps CLAUDE.md's Offline-First Rule intact for this stage.

The file this points at is a live authenticated session — treat it like a
credential, never like config. `.session/` is gitignored, and a test asserts
that entry still exists.
"""

import os
from pathlib import Path


def resolve_session_state_path() -> Path:
    """Where the saved browser session lives. `SESSION_STATE_PATH` overrides.

    Read from the environment rather than taking a Settings object so the future
    adapter receives just this path and never the whole config surface.
    """
    return Path(os.environ.get("SESSION_STATE_PATH", ".session/storage_state.json"))


def session_state_available() -> bool:
    """True only if a usable session file is actually there.

    `is_file()`, not `exists()` — a directory at that path is not a session, and
    the caller's next move would fail confusingly rather than with the clear
    "run the one-time login setup" message this exists to enable.
    """
    return resolve_session_state_path().is_file()
