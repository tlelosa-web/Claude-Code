from src.config import Settings, load_settings


class TestOllamaSettings:
    def test_settings_defaults(self):
        settings = Settings()
        assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
        assert settings.OLLAMA_MODEL == "qwen3:8b"

    def test_load_settings_defaults(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)

        settings = load_settings(tmp_path / "nonexistent.env")

        assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
        assert settings.OLLAMA_MODEL == "qwen3:8b"

    def test_load_settings_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:9999")
        monkeypatch.setenv("OLLAMA_MODEL", "llama3:8b")

        settings = load_settings(tmp_path / "nonexistent.env")

        assert settings.OLLAMA_BASE_URL == "http://localhost:9999"
        assert settings.OLLAMA_MODEL == "llama3:8b"
