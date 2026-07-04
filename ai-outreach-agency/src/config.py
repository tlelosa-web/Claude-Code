import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass
class Settings:
    OPENROUTER_API_KEY: str = ""
    APIFY_API_KEY: str = ""
    GMAIL_CREDENTIALS_PATH: str = ""
    DB_PATH: str = "outreach.db"
    SENDER_NAME: str = "Tebello Lelosa"
    SENDER_TITLE: str = "AI Automation Consultant"
    SENDER_EMAIL: str = "tlelosa@gmail.com"
    DEFAULT_ASSET_TYPE: str = "INSIGHT_DOC"
    EXPORTS_DIR: str = "exports"


def load_settings(env_path: str | Path | None = None) -> Settings:
    if load_dotenv is not None:
        load_dotenv(env_path or ".env")

    return Settings(
        OPENROUTER_API_KEY=os.environ.get("OPENROUTER_API_KEY", ""),
        APIFY_API_KEY=os.environ.get("APIFY_API_KEY", ""),
        GMAIL_CREDENTIALS_PATH=os.environ.get("GMAIL_CREDENTIALS_PATH", ""),
        DB_PATH=os.environ.get("DB_PATH", "outreach.db"),
        SENDER_NAME=os.environ.get("SENDER_NAME", "Tebello Lelosa"),
        SENDER_TITLE=os.environ.get("SENDER_TITLE", "AI Automation Consultant"),
        SENDER_EMAIL=os.environ.get("SENDER_EMAIL", "tlelosa@gmail.com"),
        DEFAULT_ASSET_TYPE=os.environ.get("DEFAULT_ASSET_TYPE", "INSIGHT_DOC"),
        EXPORTS_DIR=os.environ.get("EXPORTS_DIR", "exports"),
    )
