"""One-time interactive Indeed login. Creates the saved browser session.

    python tools/indeed_login_setup.py

Phase E of docs/specs/indeed-submit-adapter.md, §Session setup — **rewritten
2026-08-08 after the original design failed against the real site.**

The original plan launched a Playwright-driven window and exported
`context.storage_state()` once Tebello had signed in. Indeed refuses that
sign-in: three attempts, "Something went wrong. Refresh the page and try again",
at the email step, in a browser that works normally otherwise.

**Defeating that detection is out of scope and stays out of scope** — same hard
line as the CAPTCHA rule in the spec, and for the same reason: the ToS and
account risk already on record covers Indeed *noticing* automation, not hiding
it from them, and evasion is the thing most likely to get a real account
actioned. So the login moved out of automation altogether:

1. This script starts **ordinary Chrome** — a plain subprocess, no Playwright,
   no CDP, no automation flags — pointed at a dedicated profile directory.
2. Tebello signs in there by hand. Nothing is driving that browser.
3. Playwright reuses the profile afterwards (`launch_persistent_context`).

The profile is **dedicated, never a copy of his real Chrome profile.** Copying
that would pull every site's cookies and his saved passwords into the project
directory — far more exposure than the single-site session this replaces. This
one only ever sees Indeed.

What it creates is a live authenticated session. `.session/` is gitignored and a
test guards that entry; treat the directory like a password.

Nothing here reads or writes `career.db`, and nothing submits anything.
"""

import os
import subprocess
import sys
from pathlib import Path

# Import path fix: this script is run directly (`python tools/...`), not as a
# module, so the project root isn't on sys.path the way it is under pytest.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.submission.adapters.indeed import is_indeed_host  # noqa: E402
from src.submission.browser import (  # noqa: E402
    BrowserDependencyMissing,
    _load_playwright,
)
from src.submission.session import resolve_session_profile_dir  # noqa: E402

START_URL = "https://za.indeed.com/"

# Real Chrome, not Playwright's Chrome for Testing: browser.py opens the profile
# with channel="chrome", so the build that writes it should be the build that
# reads it. CHROME_PATH overrides for a non-standard install.
_CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
)


def find_chrome() -> Path | None:
    override = os.environ.get("CHROME_PATH")
    if override:
        path = Path(override)
        return path if path.is_file() else None

    for candidate in _CHROME_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return path
    return None


def indeed_cookie_count(storage_state: dict) -> int:
    """How many cookies in this state belong to Indeed.

    The check that stops the most confusing possible failure: a profile created
    but never signed into looks like a session to every later command, which
    then reports `session_expired` against something that was never a session.

    Reuses the adapter's host judgment rather than repeating it. A cookie domain
    carries a leading dot for host-wildcard cookies, which is the only
    difference from a URL host.
    """
    cookies = storage_state.get("cookies") or []
    return sum(
        1
        for cookie in cookies
        if is_indeed_host(str(cookie.get("domain", "")).lstrip("."))
    )


def describe_state(storage_state: dict) -> str:
    """A one-line summary that names no cookie and no value.

    Counts only. The whole point of this profile is that its contents are
    credentials, and a script that prints them to a terminal defeats the
    `.session/` gitignore entry it exists to feed.
    """
    origins = storage_state.get("origins") or []
    return (
        f"{indeed_cookie_count(storage_state)} Indeed cookies, "
        f"{len(storage_state.get('cookies') or [])} cookies total, "
        f"{len(origins)} origins with local storage"
    )


def _confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}


def _read_saved_state(profile_dir: Path) -> dict:
    """Open the profile with Playwright just long enough to read its cookies.

    Chrome must already be closed — it holds an exclusive lock on a profile, so
    this doubles as the check that he actually shut the window.
    """
    sync_api = _load_playwright()
    with sync_api.sync_playwright() as driver:
        context = driver.chromium.launch_persistent_context(
            str(profile_dir), headless=True, channel="chrome"
        )
        try:
            return context.storage_state()
        finally:
            context.close()


def main() -> int:
    profile_dir = resolve_session_profile_dir().resolve()

    if (profile_dir / "Default").is_dir():
        print(f"A saved session already exists at {profile_dir}")
        if not _confirm("Sign in again into the same profile?"):
            print("Left the existing session alone. Nothing was changed.")
            return 0

    chrome = find_chrome()
    if chrome is None:
        print(
            "Error: couldn't find Chrome. Set CHROME_PATH to its full path and "
            "run this again."
        )
        return 2

    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProfile: {profile_dir}")
    print(f"Chrome:  {chrome}\n")
    print("Opening ordinary Chrome — nothing is automating this window.")
    print("  1. Sign in to Indeed.")
    print("  2. CLOSE the Chrome window completely.")
    print("  3. Come back here and press Enter.\n")
    print("Nothing is typed for you, and nothing is submitted or applied to.\n")

    process = subprocess.Popen(
        [
            str(chrome),
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            START_URL,
        ]
    )

    input("Press Enter once you are signed in AND the Chrome window is closed...\n")

    if process.poll() is None:
        print(
            "Chrome still looks like it's running. Close that window, then press "
            "Enter again — the profile can't be read while Chrome holds it."
        )
        input()

    try:
        storage_state = _read_saved_state(profile_dir)
    except BrowserDependencyMissing as exc:
        print(f"Error: {exc}")
        return 2
    except Exception as exc:
        print(f"\nCouldn't read the profile: {type(exc).__name__}: {exc}")
        print("If Chrome is still open, close it and run this script again.")
        return 1

    if indeed_cookie_count(storage_state) == 0:
        print(
            "\nNo Indeed cookies in that profile, so the sign-in didn't take.\n"
            "The profile directory exists but is not a session. Run this script "
            "again and complete the sign-in before closing Chrome."
        )
        return 1

    print(f"\nSaved: {profile_dir}")
    print(f"  {describe_state(storage_state)}")
    print(
        "\nThis directory is a live authenticated session — treat it like a "
        "password. It is gitignored.\n"
        "Re-run this script whenever prep-submission or submit reports the "
        "session expired."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
