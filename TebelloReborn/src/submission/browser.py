"""Browser helpers shared by `prep-submission` (Phase E) and `submit` (Phase G).

Phase D of docs/specs/indeed-submit-adapter.md: session load, expiry detection
(A18), CAPTCHA detection (A7), the combined navigation-state check (A17), and
the plain-text step log (C3).

**This module is split into a pure decision layer and one live shim, and the
split is the design, not tidiness.** Everything that *decides* — is this a
CAPTCHA challenge, what step are we on, has the session expired — is a pure
function over small structural inputs (`FrameView`, a URL, a list of landmark
names). It runs with no browser installed, which is what keeps Phase D offline
while `playwright` stays undeclared until Phase H. Only `authenticated_page()`
drives a real browser, and it imports playwright lazily inside its own body so
importing this module never requires one. `session.py` set the same precedent
for the same reason.

The consequence worth stating: the adapter is responsible for *observing* the
page (which frames exist, which landmarks it found) and this module is
responsible for *judging* what it observed. Nothing here queries a DOM.
"""

import importlib
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional, Sequence
from urllib.parse import urlparse

from src.submission.schema import PrepStatus
from src.submission.session import resolve_session_state_path


class BrowserError(Exception):
    """Anything that stops a browser run before it can reach the site."""


class SessionStateMissing(BrowserError):
    """No saved authenticated session — the one-time login setup never ran."""


class BrowserDependencyMissing(BrowserError):
    """`playwright` isn't installed, or its browser binary isn't."""


# --------------------------------------------------------------------------
# CAPTCHA detection (A7)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FrameView:
    """The only three things about an iframe that A7 needs.

    Deliberately not a Playwright `Frame`: the judgment below must be testable
    with no browser, and a structural view keeps every abort/never-abort rule
    exercisable from a plain unit test.

    `visible` means a real, non-zero bounding box that isn't
    `visibility:hidden`/`display:none` — the adapter computes it; this module
    only trusts it.
    """

    src: str
    title: str = ""
    visible: bool = False


# The challenge frame, distinct from the anchor. Enterprise and api2 render the
# same puzzle under different paths.
_CHALLENGE_FRAME_FRAGMENTS = (
    "recaptcha/api2/bframe",
    "recaptcha/enterprise/bframe",
)

# The "I'm not a robot" checkbox. Invisible v3 never renders this interactively,
# so on screen it means the flow escalated to v2. A7 rule 5 names only
# api2/anchor; enterprise/anchor is included deliberately — rule 1 already pairs
# the two bframe paths and the escalation reasoning is identical.
_ANCHOR_FRAME_FRAGMENTS = (
    "recaptcha/api2/anchor",
    "recaptcha/enterprise/anchor",
)


def _is_google_block_page(url: str) -> bool:
    """Google's `/sorry/` block interstitial.

    Host and path are checked separately via `urlparse` rather than pattern-
    matched over the whole URL: an Indeed route containing "/sorry/" is not a
    block page, and a regex loose enough to span both parts is exactly how it
    would become one.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower().partition(":")[0]
    is_google = host == "google.com" or host.endswith(".google.com")
    return is_google and "/sorry/" in parsed.path


def captcha_reason(url: str, frames: Sequence[FrameView]) -> Optional[str]:
    """Why this page is showing a CAPTCHA *challenge*, or None if it isn't.

    The never-abort half of A7 matters as much as the abort half. Recon found a
    "protected by reCAPTCHA" notice and a hidden invisible-v3 anchor frame on a
    perfectly healthy run — a detector that treats either as a challenge aborts
    every run this adapter will ever make. Only a *visible* challenge surface,
    or Google's own block interstitial, counts.
    """
    if _is_google_block_page(url):
        return "google block interstitial (/sorry/)"

    for frame in frames:
        if not frame.visible:
            # The normal invisible-v3 case: the frames exist, sized zero.
            continue

        src = frame.src.lower()
        title = frame.title.lower()

        if any(fragment in src for fragment in _CHALLENGE_FRAME_FRAGMENTS):
            return "visible reCAPTCHA challenge frame"

        if "recaptcha" in title and "challenge" in title:
            return "visible frame titled as a reCAPTCHA challenge"

        if "hcaptcha.com" in src and "challenge" in src:
            return "visible hCaptcha challenge frame"

        if any(fragment in src for fragment in _ANCHOR_FRAME_FRAGMENTS):
            return "visible reCAPTCHA checkbox — flow escalated to v2"

    return None


def captcha_detail(url: str, reason: str) -> str:
    """The `detail` recorded on a CAPTCHA abort.

    Says where it stopped and what was seen, and deliberately suggests nothing
    else: there is no retry, reload, or wait-and-see path anywhere in this
    adapter, and a detail hinting at one invites the operator to build the loop
    by hand.
    """
    return f"captcha challenge detected at {url} ({reason})"


# --------------------------------------------------------------------------
# Navigation state (A17) and session expiry (A18)
# --------------------------------------------------------------------------


class NavVerdict(Enum):
    OK = "ok"
    # URL matched but no landmark did, or neither did. Indeed A/B-testing a
    # route degrades to an honest abort, never to filling the wrong step.
    UNRECOGNIZED = "unrecognized"
    # Landed on an auth route, or the login form rendered in place (A18).
    SESSION_EXPIRED = "session_expired"


@dataclass(frozen=True)
class WizardStep:
    """One step of Indeed's SmartApply wizard.

    `landmarks` are opaque names, not selectors. The adapter maps a name to a
    real selector from live recon and reports which ones it found; keeping the
    selectors out of here is what lets Phase D ship without guessing DOM that
    nobody has looked at yet.
    """

    name: str
    url_segment: str
    landmarks: tuple[str, ...]

    def __post_init__(self):
        # A step with no landmarks silently degrades A17's two-signal check back
        # to the URL contract it exists to replace.
        if not self.landmarks:
            raise ValueError(
                f"step {self.name!r} needs at least one landmark — a URL segment "
                f"alone is the contract A17 replaced"
            )


# Only the two segments live recon actually observed (spec §Findings 1). The
# review step's segment was never reached — the walkthrough stopped at the
# questions step deliberately — so Phase E adds it from real observation rather
# than a plausible guess. Same empty-until-known discipline as
# `eligibility.ADAPTERS`.
WIZARD_STEPS: dict[str, WizardStep] = {
    "resume_selection": WizardStep(
        name="resume_selection",
        url_segment="resume-selection-module/resume-selection",
        landmarks=("resume-list", "step-heading"),
    ),
    "questions": WizardStep(
        name="questions",
        url_segment="questions-module/questions",
        landmarks=("question-fieldset", "step-heading"),
    ),
}

# Hosts and paths that mean "Indeed is asking us to log in", matched anywhere
# in the URL.
#
# Deliberately short. Recon never saw an expired session — it ran signed in —
# so every entry here is inferred, and a false positive tells Tebello to re-run
# a login setup that was fine. A broad marker like "/auth" was dropped for
# exactly that reason. `login_form_present` is the signal that doesn't depend
# on guessing a route at all, and Phase E confirms these two against the real
# expired-session behavior.
INDEED_AUTH_MARKERS = frozenset(
    {
        "secure.indeed.com",
        "/account/login",
    }
)


def _looks_like_auth(url: str) -> bool:
    lowered = url.lower()
    return any(marker in lowered for marker in INDEED_AUTH_MARKERS)


def check_navigation_state(
    url: str,
    step: WizardStep,
    landmarks_found: Sequence[str],
    login_form_present: bool = False,
) -> NavVerdict:
    """Where the browser actually is, judged from the URL *and* the page (A17).

    Expiry is tested first, and that order is load-bearing rather than
    incidental: an auth page fails the landmark check too, so a check-expiry-last
    implementation reports `unsupported_form` for an expired session and sends
    the operator to debug a form that is fine. Its own test pins this.
    """
    if login_form_present or _looks_like_auth(url):
        return NavVerdict.SESSION_EXPIRED

    if step.url_segment not in url:
        return NavVerdict.UNRECOGNIZED

    if not any(landmark in step.landmarks for landmark in landmarks_found):
        return NavVerdict.UNRECOGNIZED

    return NavVerdict.OK


def prep_status_for(verdict: NavVerdict) -> Optional[PrepStatus]:
    """What `prep-submission` records for a verdict. None means "carry on"."""
    return {
        NavVerdict.OK: None,
        NavVerdict.SESSION_EXPIRED: PrepStatus.SESSION_EXPIRED,
        NavVerdict.UNRECOGNIZED: PrepStatus.UNSUPPORTED_FORM,
    }[verdict]


def failure_detail(verdict: NavVerdict, url: str) -> str:
    """The `detail` text for a failing verdict — identical on both paths.

    Prep and submit differ in the *status* they record (A18: `session_expired`
    vs `failed`), never in what they tell Tebello happened. One string keeps the
    two from drifting into two accounts of the same event.
    """
    if verdict is NavVerdict.SESSION_EXPIRED:
        return (
            f"session expired mid-flow at {url} — re-run the login setup "
            f"(python tools/indeed_login_setup.py)"
        )

    if verdict is NavVerdict.UNRECOGNIZED:
        return (
            f"unrecognized application step at {url} — the form's structure "
            f"changed; re-run prep-submission"
        )

    raise ValueError(f"{verdict.value} is not a failure — nothing to report")


# --------------------------------------------------------------------------
# Step log (C3)
# --------------------------------------------------------------------------

_WHITESPACE_RUN = re.compile(r"\s+")


def resolve_log_dir() -> Path:
    """`.session/logs/` — beside the session credential, inside the same
    gitignored directory, following any `SESSION_STATE_PATH` override for free.

    Derived rather than given its own env var: two independently-settable paths
    is how one of them ends up outside `.gitignore`'s coverage.
    """
    return resolve_session_state_path().parent / "logs"


class StepLog:
    """A plain-text record of where a browser run went, one line per step.

    C3 chose this over Playwright's trace/video capture, and the reason is
    exposure rather than cost: an application page carries Tebello's contact
    details, his CV content and employer-authored text, and a trace is a rich
    artifact of all of it that is easy to forget on disk. **This log takes no
    field values — there is no parameter to pass one through**, so the
    guarantee is structural rather than a rule someone has to remember at each
    call site.
    """

    def __init__(self, run_label: str, log_dir: Optional[Path] = None):
        directory = Path(log_dir) if log_dir is not None else resolve_log_dir()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        # Nothing is written or created here: a run that aborts before its first
        # step should leave no trace behind at all.
        self.path = directory / f"{stamp}-{run_label}.log"

    def record(self, action: str, url: str) -> None:
        """Append one step. `action` is a description, never a value."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Collapsed, not rejected: a tab or newline in a description is a
        # formatting accident, and losing the whole log line over it would cost
        # more than it protects.
        safe_action = _WHITESPACE_RUN.sub(" ", action).strip()
        timestamp = datetime.now(timezone.utc).isoformat()

        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp}\t{safe_action}\t{url}\n")


# --------------------------------------------------------------------------
# Session load — the one live shim
# --------------------------------------------------------------------------


def require_session_state(session_state_path: Optional[Path] = None) -> Path:
    """The saved session file, or a `SessionStateMissing` naming the fix.

    `is_file()` via `session.py`'s own reasoning: a directory at that path is
    not a session, and letting it through fails later and more confusingly.
    """
    path = (
        Path(session_state_path)
        if session_state_path is not None
        else resolve_session_state_path()
    )

    if not path.is_file():
        raise SessionStateMissing(
            f"no saved Indeed session at {path} — run the one-time login setup "
            f"first (python tools/indeed_login_setup.py)"
        )

    return path


def _load_playwright():
    """Import playwright on demand.

    Deferred so this module imports with no browser installed, which is what
    keeps every decision above testable offline while `playwright` stays
    undeclared until Phase H. `importlib` rather than a bare `import` inside the
    function so the failure can be tested by monkeypatching it.
    """
    try:
        return importlib.import_module("playwright.sync_api")
    except ImportError as exc:
        raise BrowserDependencyMissing(
            "playwright isn't installed — run `pip install playwright` and then "
            "`playwright install chromium` (a one-time setup step, never run "
            "automatically by any pipeline command)"
        ) from exc


@contextmanager
def authenticated_page(
    session_state_path: Optional[Path] = None, headless: bool = True
) -> Iterator[object]:
    """A Playwright page carrying the saved Indeed session.

    The only function here that touches a browser, and the only one exercised
    live rather than by unit test (A19 omits this module from the coverage
    gate). Its two guards run in this order on purpose: both a missing session
    and a missing dependency are true on a fresh machine, and "install
    playwright" is the wrong first instruction for someone who has simply never
    run the login setup.
    """
    state_path = require_session_state(session_state_path)
    sync_api = _load_playwright()

    with sync_api.sync_playwright() as driver:
        browser = driver.chromium.launch(headless=headless)
        try:
            context = browser.new_context(storage_state=str(state_path))
            yield context.new_page()
        finally:
            browser.close()
