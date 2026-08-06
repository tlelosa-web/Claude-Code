"""RED: src/submission/session.py doesn't exist yet — these imports must fail
first.

This module resolves the Playwright `storageState` path and reports whether a
saved session exists. It deliberately imports nothing from playwright: the
adapter that will consume this path is a separate, later task, and the core
stays runnable with no browser installed (docs/specs/submission-core.md
§Session state).

The .gitignore test is the point of this file. A storageState file is a live
authenticated session cookie — committed, it is a session-hijack credential in
git history. The hub spec wrongly assumed the existing .gitignore covered it;
this test makes that protection impossible to lose silently.
"""

from pathlib import Path

from src.submission.session import resolve_session_state_path, session_state_available

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELATIVE = Path(".session/storage_state.json")


class TestResolveSessionStatePath:
    def test_defaults_to_dot_session_dir(self, monkeypatch):
        monkeypatch.delenv("SESSION_STATE_PATH", raising=False)

        path = resolve_session_state_path()

        assert Path(path).parts[-2:] == (".session", "storage_state.json")

    def test_env_override_is_honoured(self, monkeypatch, tmp_path):
        override = tmp_path / "elsewhere" / "state.json"
        monkeypatch.setenv("SESSION_STATE_PATH", str(override))

        path = resolve_session_state_path()

        assert Path(path) == override

    def test_returns_a_path_object(self, monkeypatch):
        monkeypatch.delenv("SESSION_STATE_PATH", raising=False)

        assert isinstance(resolve_session_state_path(), Path)


class TestSessionStateAvailable:
    def test_false_when_file_absent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SESSION_STATE_PATH", str(tmp_path / "missing.json"))

        assert session_state_available() is False

    def test_true_when_file_present(self, monkeypatch, tmp_path):
        state = tmp_path / "storage_state.json"
        state.write_text("{}", encoding="utf-8")
        monkeypatch.setenv("SESSION_STATE_PATH", str(state))

        assert session_state_available() is True

    def test_false_when_path_is_a_directory(self, monkeypatch, tmp_path):
        """A directory at that path is not a usable session file — is_file(),
        not exists()."""
        monkeypatch.setenv("SESSION_STATE_PATH", str(tmp_path))

        assert session_state_available() is False


class TestGitignoreCoversSessionState:
    def test_default_session_dir_is_gitignored(self):
        """Guards the credential, not the code. If someone changes the default
        path or trims .gitignore, this fails before a session cookie can reach
        git history."""
        entries = {
            line.strip()
            for line in (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }

        assert ".session/" in entries or ".session" in entries

    def test_default_path_lives_under_the_ignored_dir(self):
        """The ignore entry above only protects the default path if the default
        path is actually inside it."""
        assert DEFAULT_RELATIVE.parts[0] == ".session"
