import base64
import os
import time
from email.mime.text import MIMEText
from pathlib import Path

from src.shared.rate_limiter import RateLimiter

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
DEFAULT_TOKEN_PATH = Path(__file__).parent.parent.parent / "token.json"

RATE_LIMIT_PER_MIN = int(os.environ.get("GMAIL_RATE_LIMIT_PER_MIN", "20"))
_limiter = RateLimiter(rate=RATE_LIMIT_PER_MIN, period=60.0)


class GmailClient:
    def __init__(
        self,
        credentials_path: str | None = None,
        token_path: str | Path | None = None,
    ):
        self.credentials_path = credentials_path or os.environ.get(
            "GMAIL_CREDENTIALS_PATH", "credentials.json"
        )
        self.token_path = Path(token_path) if token_path else DEFAULT_TOKEN_PATH

    def create_draft(self, to: str, subject: str, body: str) -> str:
        if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
            return f"draft_{int(time.time())}"

        service = self._get_service()

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        _limiter.acquire()
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        return draft["id"]

    def _get_service(self):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(
                        f"Gmail OAuth credentials not found at {self.credentials_path}. "
                        "Download an OAuth 2.0 client secret JSON from Google Cloud Console "
                        "(APIs & Services > Credentials) and set GMAIL_CREDENTIALS_PATH."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            self.token_path.write_text(creds.to_json())

        return build("gmail", "v1", credentials=creds)
