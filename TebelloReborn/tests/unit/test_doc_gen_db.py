"""RED: src/doc_gen/db.py doesn't exist yet — these imports must fail first."""

import sqlite3

import pytest

from src.doc_gen.db import get_by_vacancy_id, init_db, insert_generation_log
from src.doc_gen.schema import GenerationLogEntry, GenerationStatus
from src.vacancy_search.db import init_db as init_vacancy_db, insert_vacancy
from src.vacancy_search.schema import Vacancy


def _vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="FanMovement (Pty) Ltd",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=abc123",
    )
    defaults.update(overrides)
    return Vacancy(**defaults)


def _seed_vacancy(db_path) -> int:
    conn = init_vacancy_db(db_path)
    vacancy_id = insert_vacancy(conn, _vacancy())
    conn.close()
    return vacancy_id


class TestInitDb:
    def test_creates_generation_log_table(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_log'"
        ).fetchall()
        assert len(tables) == 1
        conn.close()

    def test_no_quality_flag_column(self, tmp_path):
        db_path = tmp_path / "career.db"
        _seed_vacancy(db_path)

        conn = init_db(db_path)

        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(generation_log)")
        }
        assert "quality_flag" not in columns
        conn.close()

    def test_doc_type_check_constraint_rejects_bogus_value(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        conn = init_db(db_path)

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO generation_log
                    (vacancy_id, doc_type, started_at, status)
                VALUES (?, ?, ?, ?)
                """,
                (vacancy_id, "resume_bogus", "2026-07-21T10:00:00+00:00", "success"),
            )
        conn.close()


class TestInsertAndGet:
    def test_insert_and_get_by_vacancy_id_round_trips(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        conn = init_db(db_path)

        insert_generation_log(
            conn,
            vacancy_id=vacancy_id,
            doc_type="cv",
            session_id="sess-123",
            started_at="2026-07-21T10:00:00+00:00",
            duration_ms=1500,
            cost_usd=0.0,
            status=GenerationStatus.SUCCESS,
        )

        results = get_by_vacancy_id(conn, vacancy_id)

        assert len(results) == 1
        entry = results[0]
        assert isinstance(entry, GenerationLogEntry)
        assert entry.doc_type == "cv"
        assert entry.status == GenerationStatus.SUCCESS
        assert entry.error_message is None
        conn.close()

    def test_error_status_carries_error_message(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        conn = init_db(db_path)

        insert_generation_log(
            conn,
            vacancy_id=vacancy_id,
            doc_type="cover_letter",
            session_id=None,
            started_at="2026-07-21T10:05:00+00:00",
            duration_ms=None,
            cost_usd=None,
            status=GenerationStatus.ERROR,
            error_message="claude binary not found",
        )

        results = get_by_vacancy_id(conn, vacancy_id)

        assert results[0].status == GenerationStatus.ERROR
        assert results[0].error_message == "claude binary not found"
        conn.close()

    def test_get_by_vacancy_id_empty_when_none_logged(self, tmp_path):
        db_path = tmp_path / "career.db"
        vacancy_id = _seed_vacancy(db_path)
        conn = init_db(db_path)

        assert get_by_vacancy_id(conn, vacancy_id) == []
        conn.close()
