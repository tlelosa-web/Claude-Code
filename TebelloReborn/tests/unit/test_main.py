"""RED: src/main.py doesn't exist yet — this import must fail first
(Build Queue step 50, Phase 7 — CLI Wiring & Integration).

This file only asserts CLI parsing + dispatch: every pipeline "stage
function" main.py calls is mocked, so nothing here exercises real
matching/doc-gen/review behaviour (that's already covered by each
stage's own unit/integration tests). Mirrors
ai-outreach-agency/src/main.py's argparse + dispatch-dict shape, adapted
to TebelloReborn's own pipeline stages and CLI names (already documented
in this project's CLAUDE.md under Essential Commands).

CLI contract under test (Executor implements src/main.py to satisfy
exactly these tests, TDD-style — no other spec for main.py exists yet):

  career-engine import-profile --file <path>      (--file required)
  career-engine fetch-vacancies [--limit <int>]    (default 25)
  career-engine list [--status <str>]              (default: None -> all statuses)
  career-engine run --vacancy-id <int>             (--vacancy-id required)
  career-engine run-all [--status <str>]           (default "new")

Expected src/main.py namespace — direct `from module import name` style
imports (mirrors ai-outreach-agency/src/main.py and this project's own
tests/unit/test_review_cli.py's @patch("src.review.cli.<name>")
convention), so tests can patch "src.main.<name>" and have it take
effect inside main()/cmd_*:

  from src.config import load_settings
  from src.profile.schema import CandidateProfile
  from src.profile.db import init_db as init_profile_db, upsert_profile, get_profile
  from src.vacancy_search.schema import VALID_STATUSES
  from src.vacancy_search.db import (
      init_db as init_vacancy_db, insert_vacancy, get_by_status, get_by_id,
  )
  from src.vacancy_search.apify_client import fetch_vacancies
  from src.matching.pipeline import run_matching
  from src.doc_gen.pipeline import run_doc_gen
  from src.review.cli import run_review_gate

Stage-function call contract enforced below (matches each stage's
already-implemented signature):

  run_matching(vacancy, profile, db_path=...)
  run_doc_gen(profile, vacancy, db_path=...)
  run_review_gate(vacancy, cv_text, cover_letter_text, db_path=...)   # first positional arg is the vacancy returned by run_doc_gen

`list` with no --status must cover every status in VALID_STATUSES (no
get_all() exists in vacancy_search/db.py, and none should be added for
this step) — implemented as one get_by_status() call per status.

`run-all` must catch a SystemExit raised by run_review_gate (the review
gate's "quit" choice, see src/review/cli.py) and stop the loop without
propagating it out of main() — mirrors
ai-outreach-agency/src/main.py's cmd_run_all.
"""

from unittest.mock import patch

import pytest

from src.main import main, build_parser
from src.profile.schema import CandidateProfile, ExperienceEntry, TitleLane
from src.submission.pipeline import SubmissionNotAllowedError, SubmissionStatusError
from src.submission.schema import (
    SubmissionAttempt,
    SubmissionMethod,
    SubmissionOutcome,
)
from src.vacancy_search.schema import Vacancy, VALID_STATUSES


@pytest.fixture(autouse=True)
def _tmp_db_path(tmp_path, monkeypatch):
    """No dispatch test may touch the real project career.db."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "career.db"))


def _profile_json_file(tmp_path, **overrides):
    import json

    data = {
        "name": "Tebello Lelosa",
        "region": "Gauteng, South Africa",
        "skills": ["Operations Management", "Lean Manufacturing"],
        "experience": [
            {
                "title": "Operations Foreman",
                "company": "Acme Engineering",
                "start_date": "2020-01",
            }
        ],
        "target_titles": [
            {"title": "Operations Foreman", "primary": True, "weight": 1.0}
        ],
        "industries": ["Manufacturing"],
    }
    data.update(overrides)
    path = tmp_path / "profile_seed.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _make_profile(**overrides) -> CandidateProfile:
    defaults = dict(
        name="Tebello Lelosa",
        region="Gauteng, South Africa",
        skills=["Operations Management"],
        experience=[
            ExperienceEntry(
                title="Operations Foreman",
                company="Acme Engineering",
                start_date="2020-01",
            )
        ],
        target_titles=[TitleLane(title="Operations Foreman", primary=True)],
        industries=["Manufacturing"],
    )
    defaults.update(overrides)
    return CandidateProfile(**defaults)


def _make_vacancy(**overrides) -> Vacancy:
    defaults = dict(
        company="Acme Engineering", title="Operations Foreman", url="https://x"
    )
    defaults.update(overrides)
    v = Vacancy(**defaults)
    v.id = overrides.get("id", 1)
    return v


def _attempt(outcome, vacancy_id=7, method=SubmissionMethod.AUTO) -> SubmissionAttempt:
    attempt = SubmissionAttempt(
        vacancy_id=vacancy_id, method=method, outcome=outcome, detail="detail"
    )
    attempt.id = 1
    return attempt


class TestArgParsing:
    def test_import_profile_requires_file(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["import-profile"])

    def test_import_profile_parses_file(self):
        parser = build_parser()
        args = parser.parse_args(["import-profile", "--file", "data/profile_seed.json"])
        assert args.command == "import-profile"
        assert args.file == "data/profile_seed.json"

    def test_fetch_vacancies_default_limit(self):
        parser = build_parser()
        args = parser.parse_args(["fetch-vacancies"])
        assert args.command == "fetch-vacancies"
        assert args.limit == 25

    def test_fetch_vacancies_parses_limit(self):
        parser = build_parser()
        args = parser.parse_args(["fetch-vacancies", "--limit", "10"])
        assert args.limit == 10

    def test_list_default_status_is_none(self):
        parser = build_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"
        assert args.status is None

    def test_list_parses_status(self):
        parser = build_parser()
        args = parser.parse_args(["list", "--status", "scored"])
        assert args.status == "scored"

    def test_run_requires_vacancy_id(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run"])

    def test_run_parses_vacancy_id(self):
        parser = build_parser()
        args = parser.parse_args(["run", "--vacancy-id", "42"])
        assert args.command == "run"
        assert args.vacancy_id == 42

    def test_run_rejects_non_integer_vacancy_id(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--vacancy-id", "not-a-number"])

    def test_run_all_default_status(self):
        parser = build_parser()
        args = parser.parse_args(["run-all"])
        assert args.command == "run-all"
        assert args.status == "new"

    def test_run_all_parses_status(self):
        parser = build_parser()
        args = parser.parse_args(["run-all", "--status", "asset_ready"])
        assert args.status == "asset_ready"

    def test_no_command_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_unknown_command_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["bogus-command"])


class TestDispatchImportProfile:
    @patch("src.main.upsert_profile")
    def test_dispatches_to_upsert_profile(self, mock_upsert, tmp_path):
        profile_file = _profile_json_file(tmp_path)

        main(["import-profile", "--file", str(profile_file)])

        mock_upsert.assert_called_once()
        _, profile_arg = mock_upsert.call_args.args
        assert isinstance(profile_arg, CandidateProfile)
        assert profile_arg.name == "Tebello Lelosa"

    @patch("src.main.upsert_profile")
    def test_missing_file_exits_without_dispatch(self, mock_upsert, tmp_path):
        missing = tmp_path / "does_not_exist.json"

        with pytest.raises(SystemExit):
            main(["import-profile", "--file", str(missing)])

        mock_upsert.assert_not_called()


class TestDispatchFetchVacancies:
    @patch("src.main.insert_vacancy")
    @patch("src.main.fetch_vacancies")
    def test_dispatches_to_fetch_vacancies_with_limit(
        self, mock_fetch, mock_insert, tmp_path
    ):
        mock_fetch.return_value = [_make_vacancy(), _make_vacancy(url="https://y")]

        main(["fetch-vacancies", "--limit", "10"])

        mock_fetch.assert_called_once_with(10)
        assert mock_insert.call_count == 2

    @patch("src.main.insert_vacancy")
    @patch("src.main.fetch_vacancies")
    def test_default_limit_used_when_omitted(self, mock_fetch, mock_insert):
        mock_fetch.return_value = []

        main(["fetch-vacancies"])

        mock_fetch.assert_called_once_with(25)
        mock_insert.assert_not_called()


class TestDispatchList:
    @patch("src.main.get_by_status")
    def test_no_status_queries_every_valid_status(self, mock_get_by_status):
        mock_get_by_status.return_value = []

        main(["list"])

        statuses_called = {c.args[1] for c in mock_get_by_status.call_args_list}
        assert statuses_called == VALID_STATUSES

    @patch("src.main.get_by_status")
    def test_status_filter_queries_only_that_status(self, mock_get_by_status):
        mock_get_by_status.return_value = [_make_vacancy()]

        main(["list", "--status", "scored"])

        mock_get_by_status.assert_called_once()
        assert mock_get_by_status.call_args.args[1] == "scored"


class TestDispatchRun:
    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_id")
    def test_dispatches_matching_docgen_review_in_order(
        self,
        mock_get_by_id,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        vacancy = _make_vacancy(id=7)
        profile = _make_profile()
        scored_vacancy = _make_vacancy(id=7)
        asset_ready_vacancy = _make_vacancy(id=7)
        asset_ready_vacancy.status = "asset_ready"

        mock_get_by_id.return_value = vacancy
        mock_get_profile.return_value = profile
        mock_run_matching.return_value = scored_vacancy
        mock_run_doc_gen.return_value = asset_ready_vacancy

        main(["run", "--vacancy-id", "7"])

        mock_get_by_id.assert_called_once()
        assert mock_get_by_id.call_args.args[1] == 7

        mock_run_matching.assert_called_once()
        assert mock_run_matching.call_args.args[0] is vacancy
        assert mock_run_matching.call_args.args[1] is profile

        mock_run_doc_gen.assert_called_once()
        assert mock_run_doc_gen.call_args.args[0] is profile
        assert mock_run_doc_gen.call_args.args[1] is scored_vacancy

        mock_run_review_gate.assert_called_once()
        assert mock_run_review_gate.call_args.args[0] is asset_ready_vacancy

    @patch("src.main.run_matching")
    @patch("src.main.get_by_id")
    def test_missing_vacancy_exits_without_dispatch(
        self, mock_get_by_id, mock_run_matching
    ):
        mock_get_by_id.return_value = None

        with pytest.raises(SystemExit):
            main(["run", "--vacancy-id", "999"])

        mock_run_matching.assert_not_called()

    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_id")
    def test_skips_review_gate_when_doc_gen_did_not_reach_asset_ready(
        self,
        mock_get_by_id,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        """Real go-live run (2026-08-01): a headless-Claude-Code CV
        generation timed out, so run_doc_gen left the vacancy at
        'scored' (not 'asset_ready') with cv_text/cover_letter_text still
        None. The pipeline called run_review_gate anyway, presenting a
        blank CV/cover letter for human approval — a real risk of
        approving an empty application. run_doc_gen returning a vacancy
        still at 'scored' (doc-gen's own documented failure signal, see
        its docstring) must skip the review gate entirely, not present it
        with nothing to review."""
        vacancy = _make_vacancy(id=7)
        profile = _make_profile()
        scored_vacancy = _make_vacancy(id=7)
        scored_vacancy.status = "scored"
        still_scored_vacancy = _make_vacancy(id=7)
        still_scored_vacancy.status = "scored"  # doc_gen did not advance it

        mock_get_by_id.return_value = vacancy
        mock_get_profile.return_value = profile
        mock_run_matching.return_value = scored_vacancy
        mock_run_doc_gen.return_value = still_scored_vacancy

        main(["run", "--vacancy-id", "7"])

        mock_run_doc_gen.assert_called_once()
        mock_run_review_gate.assert_not_called()


class TestDispatchRunAll:
    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_status")
    def test_processes_every_eligible_vacancy(
        self,
        mock_get_by_status,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        v1, v2 = _make_vacancy(id=1), _make_vacancy(id=2, url="https://y")
        mock_get_by_status.return_value = [v1, v2]
        mock_get_profile.return_value = _make_profile()
        mock_run_matching.side_effect = lambda vacancy, profile, **kw: vacancy

        def _doc_gen_side_effect(profile, vacancy, **kw):
            vacancy.status = "asset_ready"
            return vacancy

        mock_run_doc_gen.side_effect = _doc_gen_side_effect

        main(["run-all"])

        mock_get_by_status.assert_called_once()
        assert mock_get_by_status.call_args.args[1] == "new"
        assert mock_run_matching.call_count == 2
        assert mock_run_doc_gen.call_count == 2
        assert mock_run_review_gate.call_count == 2

    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_status")
    def test_status_override_is_passed_through(
        self,
        mock_get_by_status,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        mock_get_by_status.return_value = []

        main(["run-all", "--status", "asset_ready"])

        mock_get_by_status.assert_called_once()
        assert mock_get_by_status.call_args.args[1] == "asset_ready"
        mock_run_matching.assert_not_called()

    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_status")
    def test_quit_stops_the_loop_without_propagating(
        self,
        mock_get_by_status,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        v1, v2 = _make_vacancy(id=1), _make_vacancy(id=2, url="https://y")
        mock_get_by_status.return_value = [v1, v2]
        mock_get_profile.return_value = _make_profile()
        mock_run_matching.side_effect = lambda vacancy, profile, **kw: vacancy

        def _doc_gen_side_effect(profile, vacancy, **kw):
            vacancy.status = "asset_ready"
            return vacancy

        mock_run_doc_gen.side_effect = _doc_gen_side_effect
        mock_run_review_gate.side_effect = SystemExit(0)

        main(["run-all"])  # must not raise — the quit is swallowed, loop just stops

        assert mock_run_review_gate.call_count == 1

    @patch("src.main.run_review_gate")
    @patch("src.main.run_doc_gen")
    @patch("src.main.run_matching")
    @patch("src.main.get_profile")
    @patch("src.main.get_by_status")
    def test_one_failed_doc_gen_does_not_block_the_rest_of_the_batch(
        self,
        mock_get_by_status,
        mock_get_profile,
        mock_run_matching,
        mock_run_doc_gen,
        mock_run_review_gate,
    ):
        v1, v2 = _make_vacancy(id=1), _make_vacancy(id=2, url="https://y")
        mock_get_by_status.return_value = [v1, v2]
        mock_get_profile.return_value = _make_profile()
        mock_run_matching.side_effect = lambda vacancy, profile, **kw: vacancy

        def _doc_gen_side_effect(profile, vacancy, **kw):
            if vacancy.id == 1:
                vacancy.status = "scored"  # simulates a generation failure
            else:
                vacancy.status = "asset_ready"
            return vacancy

        mock_run_doc_gen.side_effect = _doc_gen_side_effect

        main(["run-all"])

        assert mock_run_doc_gen.call_count == 2
        mock_run_review_gate.assert_called_once()
        assert mock_run_review_gate.call_args.args[0].id == 2


class TestSubmitArgParsing:
    """Stage 6 CLI: career-engine submit --vacancy-id <int> | --all [--manual]"""

    def test_submit_parses_vacancy_id(self):
        parser = build_parser()
        args = parser.parse_args(["submit", "--vacancy-id", "7"])
        assert args.command == "submit"
        assert args.vacancy_id == 7
        assert args.all is False
        assert args.manual is False

    def test_submit_parses_all(self):
        parser = build_parser()
        args = parser.parse_args(["submit", "--all"])
        assert args.all is True
        assert args.vacancy_id is None

    def test_submit_parses_manual(self):
        parser = build_parser()
        args = parser.parse_args(["submit", "--vacancy-id", "7", "--manual"])
        assert args.manual is True

    def test_submit_requires_a_target(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["submit"])

    def test_submit_rejects_both_targets(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["submit", "--vacancy-id", "7", "--all"])


class TestDispatchSubmit:
    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_dispatches_to_run_submission(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])

        mock_run_submission.assert_called_once()
        assert mock_run_submission.call_args.kwargs["manual"] is False

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_manual_flag_is_passed_through(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(
            SubmissionOutcome.SUBMITTED, method=SubmissionMethod.MANUAL
        )

        main(["submit", "--vacancy-id", "7", "--manual"])

        assert mock_run_submission.call_args.kwargs["manual"] is True

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_missing_vacancy_exits_without_dispatch(
        self, mock_get_by_id, mock_run_submission
    ):
        mock_get_by_id.return_value = None

        with pytest.raises(SystemExit):
            main(["submit", "--vacancy-id", "99"])

        mock_run_submission.assert_not_called()

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_not_supported_output_tells_the_operator_what_to_do(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        """Stable substrings, asserted. "Clear message" is otherwise untestable
        and can regress silently (spec Amendment A5)."""
        mock_get_by_id.return_value = _make_vacancy(
            id=7, url="https://example.com/job/7", status="approved"
        )
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])

        out = capsys.readouterr().out
        assert "7" in out
        assert "https://example.com/job/7" in out
        assert "submit this one by hand" in out

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_not_supported_does_not_exit_non_zero(
        self, mock_get_by_id, mock_run_submission
    ):
        """Every vacancy is not_supported in this build — a non-zero exit would
        make normal operation look broken."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--vacancy-id", "7"])  # must not raise SystemExit

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_failed_outcome_exits_non_zero(self, mock_get_by_id, mock_run_submission):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.return_value = _attempt(SubmissionOutcome.FAILED)

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_gate_refusal_is_reported_not_traced(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        mock_get_by_id.return_value = _make_vacancy(id=7, status="asset_ready")
        mock_run_submission.side_effect = SubmissionNotAllowedError(
            "Vacancy 7 has status 'asset_ready'"
        )

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0
        assert "asset_ready" in capsys.readouterr().out

    @patch("src.main.run_submission")
    @patch("src.main.get_by_id")
    def test_status_error_reports_what_was_recorded(
        self, mock_get_by_id, mock_run_submission, capsys
    ):
        """The split-brain case: attempt on file, status not advanced. The
        operator has to be told that precisely (spec Amendment B5)."""
        mock_get_by_id.return_value = _make_vacancy(id=7, status="approved")
        mock_run_submission.side_effect = SubmissionStatusError(
            _attempt(SubmissionOutcome.SUBMITTED),
            "Attempt recorded for vacancy 7, but the status could not advance",
        )

        with pytest.raises(SystemExit) as exc_info:
            main(["submit", "--vacancy-id", "7"])

        assert exc_info.value.code != 0
        assert "Attempt recorded" in capsys.readouterr().out


class TestDispatchSubmitAll:
    @patch("src.main.run_submission")
    @patch("src.main.get_by_status")
    def test_processes_every_approved_vacancy(
        self, mock_get_by_status, mock_run_submission
    ):
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
        ]
        mock_run_submission.return_value = _attempt(SubmissionOutcome.NOT_SUPPORTED)

        main(["submit", "--all"])

        assert mock_get_by_status.call_args.args[1] == "approved"
        assert mock_run_submission.call_count == 2

    @patch("src.main.run_submission")
    @patch("src.main.get_by_status")
    def test_continues_past_a_failing_vacancy(
        self, mock_get_by_status, mock_run_submission
    ):
        """One bad posting must not abandon the rest of the batch."""
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
            _make_vacancy(id=3, url="https://z", status="approved"),
        ]
        mock_run_submission.side_effect = [
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
            SubmissionStatusError(_attempt(SubmissionOutcome.FAILED), "boom"),
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
        ]

        with pytest.raises(SystemExit):
            main(["submit", "--all"])

        assert mock_run_submission.call_count == 3

    @patch("src.main.run_submission")
    @patch("src.main.get_by_status")
    def test_prints_a_summary(self, mock_get_by_status, mock_run_submission, capsys):
        mock_get_by_status.return_value = [
            _make_vacancy(id=1, status="approved"),
            _make_vacancy(id=2, url="https://y", status="approved"),
        ]
        mock_run_submission.side_effect = [
            _attempt(SubmissionOutcome.SUBMITTED),
            _attempt(SubmissionOutcome.NOT_SUPPORTED),
        ]

        main(["submit", "--all"])

        out = capsys.readouterr().out
        assert "submitted: 1" in out
        assert "not supported: 1" in out

    @patch("src.main.run_submission")
    @patch("src.main.get_by_status")
    def test_all_with_no_approved_vacancies_is_not_an_error(
        self, mock_get_by_status, mock_run_submission
    ):
        mock_get_by_status.return_value = []

        main(["submit", "--all"])

        mock_run_submission.assert_not_called()
