"""RED: src/submission/browser.py doesn't exist yet — these imports must fail
first.

Phase D of docs/specs/indeed-submit-adapter.md: the browser helpers shared by
`prep-submission` (Phase E) and `submit` (Phase G) — session load,
expiry detection (A18), CAPTCHA detection (A7), the combined navigation-state
check (A17), and the plain-text step log (C3).

**Every test in this file runs with no browser installed**, which is the whole
design constraint. `playwright` is not a dependency until Phase H, so the module
must import cleanly without it and all of its *decisions* must be pure functions
over small structural inputs. Only the one function that actually drives a
browser imports playwright, and it does so lazily inside its own body.

The CAPTCHA tests carry the most weight here. Recon established that a
reCAPTCHA *notice* is on every healthy run, so a detector that treats "protected
by reCAPTCHA" as "a challenge is showing" aborts 100% of runs — the never-abort
cases below are as load-bearing as the abort ones, and neither is a formality.
"""

import importlib
from pathlib import Path

import pytest

from src.submission.browser import (
    INDEED_AUTH_MARKERS,
    WIZARD_STEPS,
    BrowserDependencyMissing,
    BrowserError,
    FrameView,
    NavVerdict,
    SessionStateMissing,
    StepLog,
    WizardStep,
    authenticated_page,
    captcha_detail,
    captcha_reason,
    failure_detail,
    check_navigation_state,
    prep_status_for,
    require_session_state,
    resolve_log_dir,
)
from src.submission.schema import PrepStatus

RESUME_STEP = WIZARD_STEPS["resume_selection"]
QUESTIONS_STEP = WIZARD_STEPS["questions"]

SMARTAPPLY = "https://smartapply.indeed.com/beta/indeedapply/form"
RESUME_URL = f"{SMARTAPPLY}/resume-selection-module/resume-selection"
QUESTIONS_URL = f"{SMARTAPPLY}/questions-module/questions/1"


class TestCaptchaAbortStates:
    """A7's five abort states. Each is one visible challenge surface."""

    def test_visible_api2_bframe_is_a_challenge(self):
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/api2/bframe?k=x", visible=True
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None

    def test_visible_enterprise_bframe_is_a_challenge(self):
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/enterprise/bframe?k=x",
                visible=True,
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None

    def test_visible_recaptcha_challenge_title_is_a_challenge(self):
        # Matched on title alone: the src is deliberately unrecognised here, so
        # this can only pass via the title rule.
        frames = [
            FrameView(
                src="https://example.invalid/widget",
                title="reCAPTCHA challenge expires in two minutes",
                visible=True,
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None

    def test_visible_hcaptcha_challenge_is_a_challenge(self):
        frames = [
            FrameView(
                src="https://newassets.hcaptcha.com/captcha/v1/challenge", visible=True
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None

    def test_hcaptcha_without_challenge_in_src_is_not_a_challenge(self):
        # A7 requires hcaptcha.com *and* 'challenge' — the bare host is the
        # equivalent of Google's badge, not a rendered puzzle.
        frames = [
            FrameView(src="https://newassets.hcaptcha.com/c/1234/static", visible=True)
        ]

        assert captcha_reason(RESUME_URL, frames) is None

    def test_google_sorry_interstitial_is_a_challenge(self):
        assert (
            captcha_reason("https://www.google.com/sorry/index?continue=x", [])
            is not None
        )

    def test_visible_anchor_means_the_flow_escalated_to_v2(self):
        # Invisible v3 never renders an interactive checkbox. On screen, it
        # means the flow escalated — abort rather than click it.
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/api2/anchor?k=x", visible=True
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None

    def test_visible_enterprise_anchor_escalated_too(self):
        # Deliberate extension of A7 rule 5, which names only api2/anchor: rule 1
        # already pairs api2/bframe with enterprise/bframe, and the escalation
        # reasoning is identical for the enterprise anchor.
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/enterprise/anchor?k=x",
                visible=True,
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is not None


class TestCaptchaNeverAbortStates:
    """A7's never-abort list. Recon saw all of these on a healthy run — a
    detector that trips on them aborts every run this adapter will ever make."""

    def test_hidden_anchor_is_the_normal_invisible_v3_case(self):
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/api2/anchor?k=x", visible=False
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is None

    def test_hidden_bframe_is_not_a_challenge(self):
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/api2/bframe?k=x", visible=False
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is None

    def test_grecaptcha_badge_frame_is_not_a_challenge(self):
        frames = [
            FrameView(
                src="https://www.google.com/recaptcha/api2/aframe",
                title="reCAPTCHA",
                visible=True,
            )
        ]

        assert captcha_reason(RESUME_URL, frames) is None

    def test_no_frames_at_all_is_not_a_challenge(self):
        assert captcha_reason(RESUME_URL, []) is None

    def test_a_recaptcha_title_without_challenge_is_not_enough(self):
        # The badge's own iframe is titled "reCAPTCHA". Only the challenge frame
        # says so in its title.
        frames = [
            FrameView(src="https://example.invalid/x", title="reCAPTCHA", visible=True)
        ]

        assert captcha_reason(RESUME_URL, frames) is None

    def test_ordinary_indeed_url_is_not_a_google_sorry_page(self):
        assert captcha_reason(RESUME_URL, []) is None

    def test_indeed_url_containing_the_word_sorry_is_not_a_block_page(self):
        # /sorry/ is only a block when it is Google's. An Indeed route that
        # happens to contain the word must not abort the run.
        assert captcha_reason("https://za.indeed.com/sorry/viewjob", []) is None


class TestCaptchaDetail:
    def test_detail_leads_with_the_spec_wording_and_the_step_url(self):
        reason = captcha_reason(
            RESUME_URL, [FrameView(src="recaptcha/api2/bframe", visible=True)]
        )

        detail = captcha_detail(RESUME_URL, reason)

        assert detail.startswith(f"captcha challenge detected at {RESUME_URL}")
        assert reason in detail

    def test_detail_carries_no_retry_instruction(self):
        # There is no retry path anywhere in this adapter (A7). A detail that
        # suggests one would invite the operator to build the loop by hand.
        reason = captcha_reason(
            RESUME_URL, [FrameView(src="recaptcha/api2/bframe", visible=True)]
        )

        detail = captcha_detail(RESUME_URL, reason).lower()

        assert "retry" not in detail
        assert "try again" not in detail


class TestWizardSteps:
    def test_only_recon_verified_url_segments_are_registered(self):
        # Phase E fills the rest from live recon. Guessing a segment here would
        # be the same mistake the Apify payload-shape bug taught this project.
        assert set(WIZARD_STEPS) == {"resume_selection", "questions"}

    def test_segments_match_what_recon_actually_saw(self):
        assert RESUME_STEP.url_segment == "resume-selection-module/resume-selection"
        assert QUESTIONS_STEP.url_segment == "questions-module/questions"

    def test_a_step_cannot_be_registered_without_a_landmark(self):
        # A17 is a two-signal check. A step with no landmarks degrades it to the
        # URL contract Codex specifically objected to.
        with pytest.raises(ValueError, match="landmark"):
            WizardStep(name="review", url_segment="review-module/review", landmarks=())


class TestNavigationState:
    """A17: URL segment *and* at least one structural landmark."""

    def test_url_and_landmark_together_are_ok(self):
        verdict = check_navigation_state(RESUME_URL, RESUME_STEP, ["resume-list"])

        assert verdict is NavVerdict.OK

    def test_any_one_landmark_is_enough(self):
        verdict = check_navigation_state(RESUME_URL, RESUME_STEP, ["step-heading"])

        assert verdict is NavVerdict.OK

    def test_url_match_with_no_landmark_is_unrecognized(self):
        # Indeed A/B-testing a route degrades to an honest abort, never to
        # filling the wrong step.
        verdict = check_navigation_state(RESUME_URL, RESUME_STEP, [])

        assert verdict is NavVerdict.UNRECOGNIZED

    def test_landmark_present_on_the_wrong_url_is_unrecognized(self):
        verdict = check_navigation_state(QUESTIONS_URL, RESUME_STEP, ["resume-list"])

        assert verdict is NavVerdict.UNRECOGNIZED

    def test_unknown_landmark_names_do_not_satisfy_the_step(self):
        verdict = check_navigation_state(RESUME_URL, RESUME_STEP, ["question-fieldset"])

        assert verdict is NavVerdict.UNRECOGNIZED


class TestSessionExpiry:
    """A18: expiry is a continuous check, not a startup one."""

    @pytest.mark.parametrize("marker", sorted(INDEED_AUTH_MARKERS))
    def test_every_auth_marker_reads_as_expired(self, marker):
        verdict = check_navigation_state(
            f"https://{marker}" if "." in marker else f"https://za.indeed.com{marker}",
            RESUME_STEP,
            [],
        )

        assert verdict is NavVerdict.SESSION_EXPIRED

    def test_a_visible_login_form_reads_as_expired_even_on_a_wizard_url(self):
        # Indeed can render the login form in place without changing the route.
        verdict = check_navigation_state(
            RESUME_URL, RESUME_STEP, [], login_form_present=True
        )

        assert verdict is NavVerdict.SESSION_EXPIRED

    def test_expiry_is_decided_before_unrecognized(self):
        # ORDERING TEST — the reason this is pinned rather than left to
        # implementation order. An auth page also fails the landmark check, so
        # whichever branch runs first decides what Tebello is told. Wrong order
        # reports "unsupported form" for an expired session and sends him to fix
        # a form that is fine. Same silent-failure class as Phase C's two
        # orderings.
        verdict = check_navigation_state(
            "https://secure.indeed.com/account/login", RESUME_STEP, []
        )

        assert verdict is NavVerdict.SESSION_EXPIRED
        assert verdict is not NavVerdict.UNRECOGNIZED


class TestVerdictMapping:
    def test_ok_has_no_prep_status(self):
        assert prep_status_for(NavVerdict.OK) is None

    def test_expired_maps_to_session_expired(self):
        assert prep_status_for(NavVerdict.SESSION_EXPIRED) is PrepStatus.SESSION_EXPIRED

    def test_unrecognized_maps_to_unsupported_form(self):
        assert prep_status_for(NavVerdict.UNRECOGNIZED) is PrepStatus.UNSUPPORTED_FORM

    def test_expiry_detail_is_the_spec_wording_and_names_the_setup_script(self):
        detail = failure_detail(NavVerdict.SESSION_EXPIRED, QUESTIONS_URL)

        assert detail.startswith(f"session expired mid-flow at {QUESTIONS_URL}")
        assert "indeed_login_setup" in detail

    def test_unrecognized_detail_records_where_it_stopped(self):
        detail = failure_detail(NavVerdict.UNRECOGNIZED, QUESTIONS_URL)

        assert QUESTIONS_URL in detail

    def test_ok_has_no_failure_detail(self):
        with pytest.raises(ValueError):
            failure_detail(NavVerdict.OK, QUESTIONS_URL)


class TestStepLog:
    """C3: a plain-text step log, not a Playwright trace. A trace is a rich,
    easily-forgotten artifact of Tebello's contact details and employer text
    sitting on disk; this carries nothing that would hurt if it leaked."""

    def test_logs_live_beside_the_session_credential(self, monkeypatch, tmp_path):
        monkeypatch.setenv(
            "SESSION_STATE_PATH", str(tmp_path / ".session" / "state.json")
        )

        assert resolve_log_dir() == tmp_path / ".session" / "logs"

    def test_log_dir_follows_the_session_path_override(self, monkeypatch):
        # One env var, not two: the log directory is derived from the session
        # path so an override can't move one without the other.
        monkeypatch.delenv("SESSION_STATE_PATH", raising=False)

        assert resolve_log_dir().parts[-2:] == (".session", "logs")

    def test_records_are_timestamp_action_url(self, tmp_path):
        log = StepLog("vacancy-7", log_dir=tmp_path)

        log.record("navigated to resume selection", RESUME_URL)

        line = log.path.read_text(encoding="utf-8").strip()
        stamp, action, url = line.split("\t")
        assert action == "navigated to resume selection"
        assert url == RESUME_URL
        assert stamp.startswith("20")

    def test_appends_rather_than_overwrites(self, tmp_path):
        log = StepLog("vacancy-7", log_dir=tmp_path)

        log.record("opened", RESUME_URL)
        log.record("reached questions", QUESTIONS_URL)

        assert len(log.path.read_text(encoding="utf-8").strip().splitlines()) == 2

    def test_creates_its_directory_on_first_record(self, tmp_path):
        nested = tmp_path / "does" / "not" / "exist"
        log = StepLog("vacancy-7", log_dir=nested)

        log.record("opened", RESUME_URL)

        assert log.path.is_file()

    def test_constructing_a_log_writes_nothing(self, tmp_path):
        nested = tmp_path / "untouched"

        StepLog("vacancy-7", log_dir=nested)

        assert not nested.exists()

    def test_tabs_and_newlines_in_an_action_cannot_break_the_format(self, tmp_path):
        log = StepLog("vacancy-7", log_dir=tmp_path)

        log.record("clicked\tcontinue\nthen waited", RESUME_URL)

        line = log.path.read_text(encoding="utf-8").strip()
        assert len(line.split("\t")) == 3

    def test_run_label_appears_in_the_filename(self, tmp_path):
        log = StepLog("vacancy-7", log_dir=tmp_path)

        assert "vacancy-7" in log.path.name


class TestSessionStateGuard:
    def test_missing_session_raises_with_the_setup_script_named(self, tmp_path):
        missing = tmp_path / ".session" / "storage_state.json"

        with pytest.raises(SessionStateMissing, match="indeed_login_setup"):
            require_session_state(missing)

    def test_a_directory_is_not_a_session(self, tmp_path):
        directory = tmp_path / ".session"
        directory.mkdir()

        with pytest.raises(SessionStateMissing):
            require_session_state(directory)

    def test_an_existing_file_is_returned_unchanged(self, tmp_path):
        state = tmp_path / "storage_state.json"
        state.write_text("{}", encoding="utf-8")

        assert require_session_state(state) == state

    def test_defaults_to_the_resolved_session_path(self, monkeypatch, tmp_path):
        state = tmp_path / "state.json"
        state.write_text("{}", encoding="utf-8")
        monkeypatch.setenv("SESSION_STATE_PATH", str(state))

        assert require_session_state() == state

    def test_session_errors_are_browser_errors(self):
        assert issubclass(SessionStateMissing, BrowserError)
        assert issubclass(BrowserDependencyMissing, BrowserError)


class TestPlaywrightIsOptionalUntilPhaseH:
    def test_importing_this_module_needs_no_browser(self):
        # The whole point of Phase D being offline. `playwright` is not a
        # dependency until Phase H and is not installed on this machine.
        module = importlib.import_module("src.submission.browser")

        assert not hasattr(module, "sync_playwright")

    def test_a_missing_session_is_reported_before_a_missing_dependency(
        self, monkeypatch, tmp_path
    ):
        # ORDERING TEST. Both are true on a fresh machine. "install playwright"
        # is the wrong first instruction for someone who has simply never run
        # the login setup — and it is the harder of the two to act on.
        monkeypatch.setenv("SESSION_STATE_PATH", str(tmp_path / "absent.json"))

        with pytest.raises(SessionStateMissing):
            with authenticated_page():
                pass  # pragma: no cover — the guard fires first

    def test_missing_playwright_names_both_install_steps(self, monkeypatch, tmp_path):
        # Monkeypatched rather than relying on playwright being absent, so this
        # test still asserts the message once Phase H installs it.
        state = tmp_path / "state.json"
        state.write_text("{}", encoding="utf-8")
        monkeypatch.setenv("SESSION_STATE_PATH", str(state))

        def _refuse(name, *args, **kwargs):
            raise ImportError(f"No module named {name!r}")

        monkeypatch.setattr(importlib, "import_module", _refuse)

        with pytest.raises(BrowserDependencyMissing) as excinfo:
            with authenticated_page():
                pass  # pragma: no cover — the import fails first

        message = str(excinfo.value)
        assert "pip install playwright" in message
        assert "playwright install chromium" in message


class TestNoBrowserImportLeaks:
    def test_browser_py_is_the_only_submission_module_naming_playwright(self):
        # Acceptance criterion: no module outside adapters/ and browser.py
        # imports playwright. Matched on import statements, not on the word —
        # session.py's docstring mentions playwright precisely to explain why it
        # doesn't import it, and that sentence is worth keeping.
        package = Path(__file__).resolve().parents[2] / "src" / "submission"
        offenders = [
            path.name
            for path in package.glob("*.py")
            if path.name != "browser.py"
            and any(
                line.strip().startswith(("import playwright", "from playwright"))
                for line in path.read_text(encoding="utf-8").splitlines()
            )
        ]

        assert offenders == []

    def test_browser_py_defers_its_playwright_import(self):
        source = (
            Path(__file__).resolve().parents[2] / "src" / "submission" / "browser.py"
        ).read_text(encoding="utf-8")

        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import playwright", "from playwright")):
                pytest.fail(f"module-level playwright import: {stripped!r}")
