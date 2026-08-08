"""Where the saved authenticated browser session lives.

Imports nothing from playwright, on purpose — the submission core stays runnable
and fully testable with no browser installed, which is what keeps CLAUDE.md's
Offline-First Rule intact for this stage.

**This is a persistent Chrome profile directory, not a `storageState` JSON file,
and the change was forced by evidence** (2026-08-08). The original design had
`tools/indeed_login_setup.py` drive a Playwright-launched window through Indeed's
sign-in and export `context.storage_state()`. Indeed refuses that sign-in — three
attempts, "Something went wrong", at the email step. Defeating that detection is
out of the question (same hard line as the CAPTCHA rule, and the ToS risk on
record covers Indeed *noticing* automation, not hiding from it), so the login
moved out of automation entirely: Tebello signs in using ordinary Chrome pointed
at a dedicated profile directory, and Playwright reuses that profile afterwards.

Two consequences worth stating:

- **The profile is dedicated, never a copy of his real Chrome profile.** Copying
  that would pull every site's cookies and his saved passwords into the project
  directory — far more exposure than the single-site session this replaces. This
  profile only ever sees Indeed.
- **It is still a live credential.** `.session/` is gitignored and a test guards
  that entry; a profile directory is if anything worse to commit than a JSON
  file, since it holds the same cookies plus browsing state.
"""

import os
from pathlib import Path

# Kept as the env var name so an existing override keeps working, and because
# what it names hasn't changed — where the saved session lives. Only its shape
# has.
_ENV_VAR = "SESSION_STATE_PATH"

DEFAULT_PROFILE_DIR = Path(".session/chrome-profile")


def resolve_session_profile_dir() -> Path:
    """The Chrome profile directory carrying the signed-in Indeed session.

    Read from the environment rather than taking a Settings object so the
    adapter receives just this path and never the whole config surface.
    """
    override = os.environ.get(_ENV_VAR)
    return Path(override) if override else DEFAULT_PROFILE_DIR


def session_state_available() -> bool:
    """True only if a usable profile is actually there.

    `is_dir()` on the profile plus a `Default` subdirectory: Chrome creates
    `Default/` the first time it runs against a user-data-dir, so an empty
    directory someone made by hand — or one this project created and Chrome
    never opened — is correctly not a session. The caller's next move would
    otherwise fail confusingly rather than with the clear "run the one-time
    login setup" message this exists to enable.
    """
    profile = resolve_session_profile_dir()
    return profile.is_dir() and (profile / "Default").is_dir()
