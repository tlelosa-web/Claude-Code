"""RED: src/config.py doesn't exist yet — these imports must fail first."""

from src.config import Settings, load_settings


class TestSettingsDefaults:
    """Settings dataclass exposes the fields every later phase depends on,
    with defaults that keep the pipeline offline-safe out of the box."""

    def test_default_field_values(self):
        settings = Settings()

        assert settings.OPENROUTER_API_KEY == ""
        assert settings.APIFY_API_KEY == ""
        assert settings.DB_PATH == "career.db"
        assert settings.OFFLINE_MODE is False
        assert settings.EXPORTS_DIR == "exports"
        assert settings.OPENROUTER_RATE_LIMIT_PER_MIN == 60
        assert settings.APIFY_RATE_LIMIT_PER_MIN == 30


class TestLoadSettingsDefaults:
    """load_settings() must return sane defaults when no env vars are set,
    without ever touching a real .env file on disk."""

    def test_reads_defaults_when_env_unset(self, monkeypatch, tmp_path):
        for var in (
            "OPENROUTER_API_KEY",
            "APIFY_API_KEY",
            "DB_PATH",
            "OFFLINE_MODE",
            "EXPORTS_DIR",
            "OPENROUTER_RATE_LIMIT_PER_MIN",
            "APIFY_RATE_LIMIT_PER_MIN",
        ):
            monkeypatch.delenv(var, raising=False)

        # Point at a nonexistent .env so load_settings() can't pick up
        # leftover values from a real developer .env file.
        settings = load_settings(env_path=tmp_path / "does-not-exist.env")

        assert settings.OPENROUTER_API_KEY == ""
        assert settings.APIFY_API_KEY == ""
        assert settings.DB_PATH == "career.db"
        assert settings.OFFLINE_MODE is False
        assert settings.EXPORTS_DIR == "exports"
        assert settings.OPENROUTER_RATE_LIMIT_PER_MIN == 60
        assert settings.APIFY_RATE_LIMIT_PER_MIN == 30


class TestLoadSettingsFromEnv:
    """load_settings() must read real overrides from the environment,
    including correct type coercion for OFFLINE_MODE and the rate limits."""

    def test_reads_overrides_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")
        monkeypatch.setenv("APIFY_API_KEY", "apify-test-key")
        monkeypatch.setenv("DB_PATH", "test_career.db")
        monkeypatch.setenv("OFFLINE_MODE", "true")
        monkeypatch.setenv("EXPORTS_DIR", "test_exports")
        monkeypatch.setenv("OPENROUTER_RATE_LIMIT_PER_MIN", "120")
        monkeypatch.setenv("APIFY_RATE_LIMIT_PER_MIN", "15")

        settings = load_settings(env_path=tmp_path / "does-not-exist.env")

        assert settings.OPENROUTER_API_KEY == "sk-or-test-key"
        assert settings.APIFY_API_KEY == "apify-test-key"
        assert settings.DB_PATH == "test_career.db"
        assert settings.OFFLINE_MODE is True
        assert settings.EXPORTS_DIR == "test_exports"
        assert settings.OPENROUTER_RATE_LIMIT_PER_MIN == 120
        assert settings.APIFY_RATE_LIMIT_PER_MIN == 15

    def test_offline_mode_false_variants(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OFFLINE_MODE", "false")

        settings = load_settings(env_path=tmp_path / "does-not-exist.env")

        assert settings.OFFLINE_MODE is False
