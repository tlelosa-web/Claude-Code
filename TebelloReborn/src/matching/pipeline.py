from pathlib import Path
from typing import Optional

from src.matching.scorer import score_vacancy
from src.profile.schema import CandidateProfile
from src.vacancy_search.db import init_db, save_match_result, update_vacancy_status
from src.vacancy_search.schema import Vacancy


def run_matching(
    vacancy: Vacancy,
    profile: CandidateProfile,
    db_path: Optional[Path] = None,
) -> Vacancy:
    """Score `vacancy` against `profile`, persist the result, and
    transition status new -> scored. Raises on an invalid transition
    (e.g. the vacancy isn't currently `new`) before any write happens —
    no half-applied state."""
    score, strengths, weaknesses, recommendation = score_vacancy(profile, vacancy)

    conn = init_db(db_path)
    try:
        update_vacancy_status(conn, vacancy.id, "scored")
        save_match_result(conn, vacancy.id, score, strengths, weaknesses, recommendation)
    finally:
        conn.close()

    vacancy.score = score
    vacancy.strengths = strengths
    vacancy.weaknesses = weaknesses
    vacancy.recommendation = recommendation
    vacancy.status = "scored"
    return vacancy
