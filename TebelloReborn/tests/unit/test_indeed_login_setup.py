"""The two pure helpers in tools/indeed_login_setup.py.

The script itself is interactive and browser-driven, so it is exercised by
actually running it (A19 exempts playwright-driven paths from the coverage
gate). These two functions are not: one decides whether a captured state is a
real signed-in session, and the other decides what may be printed about it.
Both are worth pinning, because getting either wrong fails in a way that only
shows up much later.
"""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "indeed_login_setup.py"
_spec = importlib.util.spec_from_file_location("indeed_login_setup", _SCRIPT)
login_setup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(login_setup)


def cookie(domain: str, name: str = "SESSION", value: str = "s3cr3t") -> dict:
    return {"domain": domain, "name": name, "value": value}


class TestIndeedCookieCount:
    """The guard against saving a state captured before signing in."""

    def test_counts_the_apex_and_dot_prefixed_domains(self):
        state = {
            "cookies": [
                cookie(".indeed.com"),
                cookie("indeed.com"),
                cookie("za.indeed.com"),
                cookie(".za.indeed.com"),
            ]
        }
        assert login_setup.indeed_cookie_count(state) == 4

    def test_ignores_other_sites(self):
        state = {"cookies": [cookie("google.com"), cookie(".doubleclick.net")]}
        assert login_setup.indeed_cookie_count(state) == 0

    def test_ignores_a_lookalike_domain(self):
        # Same suffix-match trap the adapter's host check avoids: a cookie on
        # notindeed.com must not make an anonymous state look signed in.
        assert (
            login_setup.indeed_cookie_count({"cookies": [cookie("notindeed.com")]}) == 0
        )

    @pytest.mark.parametrize("state", [{}, {"cookies": None}, {"cookies": []}])
    def test_an_empty_state_counts_zero(self, state):
        # A fresh context that never signed in produces exactly this, and it is
        # the case the whole check exists for.
        assert login_setup.indeed_cookie_count(state) == 0


class TestDescribeState:
    """What the script is allowed to print about a credential."""

    def test_reports_counts(self):
        state = {
            "cookies": [cookie(".indeed.com"), cookie("google.com")],
            "origins": [{"origin": "https://za.indeed.com", "localStorage": []}],
        }
        summary = login_setup.describe_state(state)
        assert "1 Indeed cookies" in summary
        assert "2 cookies total" in summary
        assert "1 origins" in summary

    def test_leaks_no_cookie_name_or_value(self):
        # The file this summarises is gitignored precisely because its contents
        # are credentials. A summary that echoes them to a terminal — and into
        # scrollback, and into any session transcript — undoes that.
        state = {
            "cookies": [cookie(".indeed.com", name="CTK", value="super-secret-token")],
            "origins": [],
        }
        summary = login_setup.describe_state(state)
        assert "super-secret-token" not in summary
        assert "CTK" not in summary

    def test_handles_a_state_with_no_origins_key(self):
        assert "0 origins" in login_setup.describe_state({"cookies": []})
