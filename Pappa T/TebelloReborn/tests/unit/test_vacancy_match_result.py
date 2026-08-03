"""RED: Vacancy doesn't carry match-result fields yet, and
save_match_result doesn't exist yet — these must fail first.

Corrective addendum ahead of Build Queue step 29: ADR-003 §2 says
"no migration required" for the match score, reasoning that it's "part
of the Phase 3 vacancy schema" — but the Phase 3 vacancy schema (as
actually built, steps 16-19) carries no score/rationale columns. Per
CLAUDE.md hard rule #6 ("No schema changes without a migration file.
Ever") and this project's own Resolved Items convention (baseline
CREATE TABLE + migrations.py for every change after), adding these
columns now is a migration, regardless of the ADR's informal phrasing.
"""

import json

import pytest

from src.vacancy_search.db import (
    get_by_id,
    init_db,
    insert_vacancy,
    save_match_result,
)
from src.vacancy_search.schema import Vacancy


def _vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="Acme Engineering",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=1",
    )
    defaults.update(overrides)
    return Vacancy(**defaults)


class TestVacancyMatchResultFields:
    def test_defaults_to_none(self):
        vacancy = _vacancy()

        assert vacancy.score is None
        assert vacancy.strengths is None
        assert vacancy.weaknesses is None
        assert vacancy.recommendation is None

    def test_accepts_match_result_fields(self):
        vacancy = _vacancy(
            score=72,
            strengths=["Strong ops background"],
            weaknesses=["No mining-sector experience"],
            recommendation="Worth applying.",
        )

        assert vacancy.score == 72
        assert vacancy.strengths == ["Strong ops background"]

    def test_score_out_of_range_raises(self):
        with pytest.raises(ValueError, match="score"):
            _vacancy(score=101)

    def test_negative_score_raises(self):
        with pytest.raises(ValueError, match="score"):
            _vacancy(score=-1)


class TestSaveMatchResult:
    def test_migration_adds_match_result_columns(self, tmp_path):
        conn = init_db(tmp_path / "career.db")

        columns = {row["name"] for row in conn.execute("PRAGMA table_info(vacancies)")}

        assert {"score", "strengths", "weaknesses", "recommendation"} <= columns
        conn.close()

    def test_save_then_get_round_trips(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())

        save_match_result(
            conn,
            vacancy_id,
            score=72,
            strengths=["Strong ops background", "Gauteng-based"],
            weaknesses=["No mining-sector experience"],
            recommendation="Worth applying.",
        )

        loaded = get_by_id(conn, vacancy_id)

        assert loaded.score == 72
        assert loaded.strengths == ["Strong ops background", "Gauteng-based"]
        assert loaded.weaknesses == ["No mining-sector experience"]
        assert loaded.recommendation == "Worth applying."
        conn.close()

    def test_unscored_vacancy_has_none_match_fields(self, tmp_path):
        conn = init_db(tmp_path / "career.db")
        vacancy_id = insert_vacancy(conn, _vacancy())

        loaded = get_by_id(conn, vacancy_id)

        assert loaded.score is None
        assert loaded.strengths is None
        conn.close()
