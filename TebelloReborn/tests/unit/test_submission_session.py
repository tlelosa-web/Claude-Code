"""Where the saved authenticated browser session lives.

This module resolves the session path and reports whether a saved session
exists. It deliberately imports nothing from playwright, so the submission core
stays runnable with no browser installed (docs/specs/submission-core.md
§Session state).

**Rewritten 2026-08-08: the session is a Chrome profile directory, not a
`storageState` JSON file.** Indeed refuses an automated sign-in, so the login
moved out of automation entirely — Tebello signs in with ordinary Chrome pointed
at a dedicated profile, and Playwright reuses it. See session.py's own docstring
for the full reasoning.

The .gitignore test is still the point of this file, and matters more now than
it did: a profile directory holds the same session cookies as the JSON file did,
plus browsing state.
"""

from pathlib import Path

from src.submission.session import (
    DEFAULT_PROFILE_DIR,
    resolve_session_profile_dir,
    session_state_available,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def make_profile(root: Path) -> Path:
    """A directory shaped like one Chrome has actually opened."""
    (root / "Default").mkdir(parents=True, exist_ok=True)
    return root


class TestResolveSessionProfileDir:
    def test_defaults_to_dot_session_dir(self, monkeypatch):
        monkeypatch.delenv("SESSION_STATE_PATH", raising=False)

        path = resolve_session_profile_dir()

        assert Path(path).parts[-2:] == (".session", "chrome-profile")

    def test_env_override_is_honoured(self, monkeypatch, tmp_path):
        override = tmp_path / "elsewhere" / "profile"
        monkeypatch.setenv("SESSION_STATE_PATH", str(override))

        assert resolve_session_profile_dir() == override

    def test_returns_a_path_object(self, monkeypatch):
        monkeypatch.delenv("SESSION_STATE_PATH", raising=False)

        assert isinstance(resolve_session_profile_dir(), Path)


class TestSessionStateAvailable:
    def test_false_when_nothing_is_there(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SESSION_STATE_PATH", str(tmp_path / "missing"))

        assert session_state_available() is False

    def test_true_for_a_profile_chrome_has_opened(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SESSION_STATE_PATH", str(make_profile(tmp_path / "p")))

        assert session_state_available() is True

    def test_false_for_an_empty_directory(self, monkeypatch, tmp_path):
        # The failure this exists to prevent: the login script creates the
        # directory, Chrome never actually runs, and every later command reports
        # "session expired" against a profile that was never a session. Chrome
        # writes Default/ on first run, so its absence is the signal.
        empty = tmp_path / "made-but-never-used"
        empty.mkdir()
        monkeypatch.setenv("SESSION_STATE_PATH", str(empty))

        assert session_state_available() is False

    def test_false_when_the_path_is_a_file(self, monkeypatch, tmp_path):
        # Catches a stale storage_state.json left over from the pre-2026-08-08
        # design sitting at an overridden path.
        stale = tmp_path / "storage_state.json"
        stale.write_text("{}", encoding="utf-8")
        monkeypatch.setenv("SESSION_STATE_PATH", str(stale))

        assert session_state_available() is False


class TestGitignoreCoversTheSession:
    def test_default_session_dir_is_gitignored(self):
        """Guards the credential, not the code. If someone changes the default
        path or trims .gitignore, this fails before a live session can reach git
        history."""
        entries = {
            line.strip()
            for line in (PROJECT_ROOT / ".gitignore")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.strip().startswith("#")
        }

        assert ".session/" in entries or ".session" in entries

    def test_default_path_lives_under_the_ignored_dir(self):
        """The ignore entry above only protects the default path if the default
        path is actually inside it."""
        assert DEFAULT_PROFILE_DIR.parts[0] == ".session"

    def test_the_whole_profile_tree_is_covered(self):
        """`.session/` ignores the directory and everything under it. A profile
        is thousands of files, so a rule that only covered a single named file
        would leak the rest."""
        assert not DEFAULT_PROFILE_DIR.is_absolute()
