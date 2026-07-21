import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _parse_bool(value: str) -> bool:
    """Env vars arrive as strings — "true"/"1"/"yes" (any case) mean on."""
    return value.strip().lower() in ("true", "1", "yes")


@dataclass
class Settings:
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    APIFY_API_KEY: str = ""
    DB_PATH: str = "career.db"
    OFFLINE_MODE: bool = False
    EXPORTS_DIR: str = "exports"
    OLLAMA_RATE_LIMIT_PER_MIN: int = 120
    APIFY_RATE_LIMIT_PER_MIN: int = 30


def load_settings(env_path: str | Path | None = None) -> Settings:
    """Load Settings from environment, optionally seeded from a .env file.

    `env_path` lets tests point at a nonexistent file so a real developer
    .env on disk never leaks into an assertion about defaults.
    """
    if load_dotenv is not None:
        load_dotenv(env_path or ".env")

    return Settings(
        OLLAMA_BASE_URL=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        OLLAMA_MODEL=os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
        APIFY_API_KEY=os.environ.get("APIFY_API_KEY", ""),
        DB_PATH=os.environ.get("DB_PATH", "career.db"),
        OFFLINE_MODE=_parse_bool(os.environ.get("OFFLINE_MODE", "false")),
        EXPORTS_DIR=os.environ.get("EXPORTS_DIR", "exports"),
        OLLAMA_RATE_LIMIT_PER_MIN=int(
            os.environ.get("OLLAMA_RATE_LIMIT_PER_MIN", "120")
        ),
        APIFY_RATE_LIMIT_PER_MIN=int(os.environ.get("APIFY_RATE_LIMIT_PER_MIN", "30")),
    )
