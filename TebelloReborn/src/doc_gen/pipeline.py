from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.profile.schema import CandidateProfile
from src.vacancy_search.db import (
    VALID_TRANSITIONS,
    get_by_id,
    init_db as init_vacancy_db,
    update_vacancy_status,
)
from src.vacancy_search.schema import Vacancy

from .cover_letter_generator import generate_cover_letter
from .cv_generator import generate_cv
from .db import init_db as init_doc_gen_db, insert_generation_log
from .pdf_export import export_cover_letter_pdf, export_cv_pdf
from .schema import GenerationResult, GenerationStatus


def _generate_and_log(
    conn,
    generate_fn,
    export_fn,
    doc_type: str,
    profile: CandidateProfile,
    vacancy: Vacancy,
) -> GenerationResult:
    started_at = datetime.now(timezone.utc).isoformat()
    result = generate_fn(profile, vacancy)

    if result.status == GenerationStatus.SUCCESS and result.content:
        export_fn(vacancy, result.content)

    insert_generation_log(
        conn,
        vacancy_id=vacancy.id,
        doc_type=doc_type,
        started_at=started_at,
        status=result.status,
        session_id=result.session_id,
        duration_ms=result.duration_ms,
        cost_usd=result.cost_usd,
        error_message=result.error_message,
    )
    return result


def run_doc_gen(
    profile: CandidateProfile,
    vacancy: Vacancy,
    db_path: Optional[Path] = None,
) -> Vacancy:
    """Generate a CV + cover letter for `vacancy`, export each to PDF on
    success, and log every attempt to generation_log. Only transitions
    status scored -> asset_ready if both documents succeed — a throttled
    or errored document leaves the vacancy at `scored` so a later run can
    retry (ADR-003 §3). Raises on an invalid starting status before any
    generation is attempted, since (unlike matching) a generation attempt
    has real subprocess cost."""
    vacancy_conn = init_vacancy_db(db_path)
    doc_gen_conn = init_doc_gen_db(db_path)
    try:
        current = get_by_id(vacancy_conn, vacancy.id)
        if current is None:
            raise ValueError(f"Vacancy {vacancy.id} not found")
        if "asset_ready" not in VALID_TRANSITIONS.get(current.status, set()):
            raise ValueError(f"Invalid transition: {current.status} → asset_ready")

        cv_result = _generate_and_log(
            doc_gen_conn, generate_cv, export_cv_pdf, "cv", profile, vacancy
        )
        cl_result = _generate_and_log(
            doc_gen_conn,
            generate_cover_letter,
            export_cover_letter_pdf,
            "cover_letter",
            profile,
            vacancy,
        )

        if (
            cv_result.status == GenerationStatus.SUCCESS
            and cl_result.status == GenerationStatus.SUCCESS
        ):
            update_vacancy_status(vacancy_conn, vacancy.id, "asset_ready")
            vacancy.status = "asset_ready"
            vacancy.cv_text = cv_result.content
            vacancy.cover_letter_text = cl_result.content
    finally:
        vacancy_conn.close()
        doc_gen_conn.close()

    return vacancy
