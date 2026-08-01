"""Local dev server exposing career.db's vacancy pipeline state as JSON,
plus an approve/reject action on asset_ready vacancies.

Not part of the production pipeline's own entry points — a visualization
and control aid. The decision endpoint calls the *same* review-gate
functions the CLI (`src/review/cli.py::run_review_gate`) uses — save the
approval row, then transition status — so a click here is a second front
end onto the real human-approval gate, never a bypass of it (CLAUDE.md
Hard Rule #1).
"""

import http.server
import json
import re
import sqlite3
import socketserver
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
PROJECT_ROOT = TOOLS_DIR.parent
DB_PATH = PROJECT_ROOT / "career.db"
PORT = 8420

sys.path.insert(0, str(PROJECT_ROOT))

from src.review.db import init_db as init_review_db, save_approval  # noqa: E402
from src.review.schema import Decision, ReviewResult  # noqa: E402
from src.vacancy_search.db import (  # noqa: E402
    VALID_TRANSITIONS,
    get_by_id,
    init_db as init_vacancy_db,
    update_vacancy_status,
)

STATUS_ORDER = ["new", "scored", "asset_ready", "approved", "rejected"]
DECISION_TO_STATUS = {"approved": "approved", "rejected": "rejected"}


def fetch_vacancies() -> list[dict]:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT id, company, title, platform, status, score, url, "
            "scraped_at FROM vacancies ORDER BY scraped_at DESC"
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def apply_decision(vacancy_id: int, decision: str) -> None:
    """Approve or reject a vacancy via the real review-gate DB functions.

    Mirrors src/review/cli.py::run_review_gate's ordering exactly: the
    approval row is committed before the status transition, so a failure
    after persistence still leaves a recorded decision (fails closed).
    Raises ValueError/LookupError on bad input, an unknown vacancy id, or
    an invalid state transition (e.g. double-submit racing a poll) — the
    caller translates those into HTTP error responses.
    """
    if decision not in DECISION_TO_STATUS:
        raise ValueError(f"Unknown decision '{decision}'")

    vacancy_conn = init_vacancy_db(DB_PATH)
    try:
        current = get_by_id(vacancy_conn, vacancy_id)
        if current is None:
            raise LookupError(f"Vacancy {vacancy_id} not found")

        new_status = DECISION_TO_STATUS[decision]
        if new_status not in VALID_TRANSITIONS.get(current.status, set()):
            raise ValueError(f"Invalid transition: {current.status} -> {new_status}")

        result = ReviewResult(
            vacancy_id=vacancy_id,
            decision=Decision.APPROVED if decision == "approved" else Decision.REJECTED,
        )
        review_conn = init_review_db(DB_PATH)
        try:
            save_approval(review_conn, result)  # committed first — decision now durable
        finally:
            review_conn.close()

        update_vacancy_status(vacancy_conn, vacancy_id, new_status)
    finally:
        vacancy_conn.close()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TOOLS_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/vacancies":
            try:
                vacancies = fetch_vacancies()
                counts = {s: 0 for s in STATUS_ORDER}
                for v in vacancies:
                    counts[v["status"]] = counts.get(v["status"], 0) + 1
                body = json.dumps(
                    {"vacancies": vacancies, "counts": counts}
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except sqlite3.OperationalError as exc:
                body = json.dumps({"error": str(exc)}).encode("utf-8")
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return
        if self.path == "/":
            self.path = "/dashboard.html"
        return super().do_GET()

    def do_POST(self):
        match = re.fullmatch(r"/api/vacancies/(\d+)/decision", self.path)
        if not match:
            self.send_response(404)
            self.end_headers()
            return

        vacancy_id = int(match.group(1))
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(raw)
            decision = payload.get("decision", "")
            apply_decision(vacancy_id, decision)
            status_code, body = 200, {"ok": True}
        except LookupError as exc:
            status_code, body = 404, {"ok": False, "error": str(exc)}
        except (ValueError, json.JSONDecodeError) as exc:
            status_code, body = 409, {"ok": False, "error": str(exc)}

        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Vacancy dashboard: http://127.0.0.1:{PORT}/")
        httpd.serve_forever()
