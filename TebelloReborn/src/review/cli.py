# HARD RULE: run_review_gate() is the mandatory human checkpoint.
# The output of run_doc_gen() must pass through this function before
# any future submission stage is ever built. No code path may bypass
# save_approval() — and the decision is always persisted (committed)
# BEFORE the vacancy status advances, so a failure after persistence
# still leaves a recorded decision (fails closed), never an "approved"
# vacancy with no decision on file (fails open). Design reviewed and
# signed off per docs/todo.md's Phase 6 mandatory Reviewer gate before
# this file was written.

import os
import subprocess
import sys
import tempfile
from typing import Optional

from src.vacancy_search.db import (
    VALID_TRANSITIONS,
    get_by_id,
    init_db as init_vacancy_db,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy

from .db import init_db as init_review_db, save_approval
from .schema import Decision, ReviewResult

VALID_CHOICES = {"a", "r", "e", "q"}

_DECISION_STATUS = {
    Decision.APPROVED: "approved",
    Decision.REJECTED: "rejected",
    Decision.EDITED: "approved",
}


def _print_review(vacancy: Vacancy, cv_text: str, cover_letter_text: str) -> None:
    print("\n--- VACANCY ---")
    print(f"  Company:  {vacancy.company}")
    print(f"  Title:    {vacancy.title}")
    print(f"  URL:      {vacancy.url}")
    print(f"  Score:    {vacancy.score}")
    print("\n--- CV ---")
    print(cv_text)
    print("\n--- COVER LETTER ---")
    print(cover_letter_text)
    print("\n--- DECISION ---")
    print("  [A] Approve  [R] Reject  [E] Edit  [Q] Quit")


def _get_choice(input_fn=input) -> str:
    while True:
        choice = input_fn("\n> ").strip().lower()
        if choice in VALID_CHOICES:
            return choice
        print(f"Invalid choice '{choice}'. Enter A, R, E, or Q.")


def _edit_text(text: str) -> str:
    editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "vi")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        with open(tmp_path, encoding="utf-8") as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


def run_review_gate(
    vacancy: Vacancy,
    cv_text: str,
    cover_letter_text: str,
    input_fn=input,
    db_path: Optional[str] = None,
) -> ReviewResult:
    _print_review(vacancy, cv_text, cover_letter_text)
    choice = _get_choice(input_fn=input_fn)

    if choice == "q":
        raise SystemExit(0)

    if choice == "a":
        decision, edited_cv_text, edited_cover_letter_text = Decision.APPROVED, None, None
    elif choice == "r":
        decision, edited_cv_text, edited_cover_letter_text = Decision.REJECTED, None, None
    else:  # "e"
        edited_cv_text = _edit_text(cv_text)
        edited_cover_letter_text = _edit_text(cover_letter_text)
        decision = Decision.EDITED

    new_status = _DECISION_STATUS[decision]

    vacancy_conn = init_vacancy_db(db_path)
    try:
        current = get_by_id(vacancy_conn, vacancy.id)
        if current is None:
            raise ValueError(f"Vacancy {vacancy.id} not found")
        if new_status not in VALID_TRANSITIONS.get(current.status, set()):
            raise ValueError(f"Invalid transition: {current.status} → {new_status}")

        result = ReviewResult(
            vacancy_id=vacancy.id,
            decision=decision,
            edited_cv_text=edited_cv_text,
            edited_cover_letter_text=edited_cover_letter_text,
        )

        review_conn = init_review_db(db_path)
        try:
            save_approval(review_conn, result)  # committed first — decision now durable
        finally:
            review_conn.close()

        # If this raises, the decision above is already committed — a
        # recovery re-run inserts a second approval row before retrying
        # the transition (benign: get_approval_by_vacancy_id returns the
        # most recent row). Any future submission stage must gate on
        # vacancy.status == "approved", never on mere presence of an
        # approval row.
        update_vacancy_status(vacancy_conn, vacancy.id, new_status)
        return result
    finally:
        vacancy_conn.close()
