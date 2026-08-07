"""One-time interactive Indeed login. Writes the saved browser session.

    python tools/indeed_login_setup.py

Phase E of docs/specs/indeed-submit-adapter.md, §Session setup.

**Deliberately not a `career-engine` subcommand.** This opens a visible browser
window and waits for a human to type a password into it — there is no correct
way for `--all`, a batch run, or any agent to trigger that, and keeping it out of
the CLI's dispatch table is what makes it impossible. Tebello runs it himself,
on this machine, once, and again whenever the saved session expires.

What it writes is a live authenticated session, not config. `.session/` is
gitignored and a test guards that entry; treat the file like a password.

Nothing here reads or writes `career.db`, and nothing submits anything.
"""

import json
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
from src.submission.session import resolve_session_state_path  # noqa: E402

# Indeed's own landing page rather than the login form directly: if a valid
# session already exists in the fresh profile (it won't, but), landing here
# shows it immediately, and the sign-in button is one click away either way.
START_URL = "https://za.indeed.com/"


def indeed_cookie_count(storage_state: dict) -> int:
    """How many cookies in this state belong to Indeed.

    The check that stops the most confusing possible failure: a state captured
    before signing in saves cleanly, and then every future `prep-submission`
    reports `session_expired` against a file that was never a session at all.

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

    Counts only. The whole point of this file is that its contents are
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


def main() -> int:
    state_path = resolve_session_state_path()

    if state_path.exists():
        print(f"A saved session already exists at {state_path}")
        if not _confirm("Overwrite it?"):
            print("Left the existing session alone. Nothing was changed.")
            return 0

    try:
        sync_api = _load_playwright()
    except BrowserDependencyMissing as exc:
        # browser.py owns this message so the two paths can't drift into two
        # accounts of the same missing dependency.
        print(f"Error: {exc}")
        return 2

    print("\nOpening a browser window. Sign in to Indeed by hand in that window.")
    print("Nothing is typed for you, and nothing is submitted or applied to.\n")

    with sync_api.sync_playwright() as driver:
        browser = driver.chromium.launch(headless=False)
        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(START_URL)

            input(
                "Press Enter here once you are signed in and can see your "
                "Indeed account...\n"
            )

            storage_state = context.storage_state()
        finally:
            browser.close()

    if indeed_cookie_count(storage_state) == 0:
        print(
            "\nRefusing to save: this state carries no Indeed cookies, so it is "
            "not a signed-in session.\nNothing was written. Run the script again "
            "and complete the sign-in before pressing Enter."
        )
        return 1

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(storage_state), encoding="utf-8")

    print(f"\nSaved: {state_path}")
    print(f"  {describe_state(storage_state)}")
    print(
        "\nThis file is a live authenticated session — treat it like a "
        "password. It is gitignored.\n"
        "Re-run this script whenever prep-submission or submit reports the "
        "session expired."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
