import time


class GmailClient:
    # TODO: replace with Gmail API call using OAuth credentials
    def create_draft(self, to: str, subject: str, body: str) -> str:
        return f"draft_{int(time.time())}"
