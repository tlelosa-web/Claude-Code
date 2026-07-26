"""RED: src/vacancy_search/apify_client.py doesn't exist yet — these imports
must fail first."""

from unittest.mock import MagicMock, patch

import pytest

from src.vacancy_search.apify_client import (
    FIXTURE_VACANCIES,
    SEARCH_TITLES,
    fetch_vacancies,
)
from src.vacancy_search.schema import Vacancy


def _mock_response(json_data):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status.side_effect = None
    return resp


class TestOfflineMode:
    def test_offline_mode_returns_fixture_vacancies(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        results = fetch_vacancies(limit=25)

        assert 2 <= len(results) <= 3
        assert all(isinstance(v, Vacancy) for v in results)
        platforms = {v.platform for v in results}
        assert platforms <= {"indeed", "linkedin"}

    def test_offline_mode_respects_limit(self, monkeypatch):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        results = fetch_vacancies(limit=1)

        assert len(results) == 1


class TestMissingApiKey:
    def test_missing_api_key_falls_back_to_fixture_with_warning(self, monkeypatch):
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.delenv("APIFY_API_KEY", raising=False)

        with pytest.warns(UserWarning, match="APIFY_API_KEY"):
            results = fetch_vacancies(limit=25)

        assert len(results) == len(FIXTURE_VACANCIES)


class TestRealCallPath:
    @patch("src.vacancy_search.apify_client.requests.post")
    def test_calls_rate_limiter_before_each_real_request(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        mock_post.return_value = _mock_response([])

        with patch("src.vacancy_search.apify_client._limiter.acquire") as mock_acquire:
            fetch_vacancies(limit=25)

        # one Indeed + one LinkedIn call per search title
        assert mock_acquire.call_count == len(SEARCH_TITLES) * 2

    @patch("src.vacancy_search.apify_client.requests.post")
    def test_sends_correct_actor_payload_fields(self, mock_post, monkeypatch):
        """Regression test: fetch_vacancies() used to send {"maxItems": limit}
        to both actors, which isn't a valid field for either — Indeed needs
        position/location/maxItemsPerSearch, LinkedIn requires
        title/location/rows. HTTP errors from the wrong payload were being
        silently swallowed, so a real run returned zero results with no
        visible failure."""
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )
        mock_post.return_value = _mock_response([])

        fetch_vacancies(limit=10)

        indeed_call, linkedin_call = mock_post.call_args_list
        indeed_payload = indeed_call.kwargs["json"]
        linkedin_payload = linkedin_call.kwargs["json"]

        assert indeed_payload["position"] == "Operations Foreman"
        assert indeed_payload["location"]
        assert indeed_payload["maxItemsPerSearch"] == 10
        assert "maxItems" not in indeed_payload

        assert linkedin_payload["title"] == "Operations Foreman"
        assert linkedin_payload["location"]
        assert linkedin_payload["rows"] == 10
        assert "maxItems" not in linkedin_payload

    @patch("src.vacancy_search.apify_client.requests.post")
    def test_normalizes_indeed_and_linkedin_results(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )

        indeed_items = [
            {
                "company": "Acme Engineering",
                "positionName": "Operations Foreman",
                "url": "https://za.indeed.com/viewjob?jk=1",
                "description": "Run the workshop.",
                "salary": "R50,000 CTC",
            }
        ]
        linkedin_items = [
            {
                "companyName": "Beta Power",
                "title": "Project Engineer",
                "link": "https://www.linkedin.com/jobs/view/2",
                "description": "Manage projects.",
                "expireAt": "2026-09-01",
            }
        ]
        mock_post.side_effect = [
            _mock_response(indeed_items),
            _mock_response(linkedin_items),
        ]

        results = fetch_vacancies(limit=25)

        assert len(results) == 2
        indeed_result = next(v for v in results if v.platform == "indeed")
        linkedin_result = next(v for v in results if v.platform == "linkedin")
        assert indeed_result.company == "Acme Engineering"
        assert indeed_result.title == "Operations Foreman"
        assert linkedin_result.company == "Beta Power"
        assert linkedin_result.deadline == "2026-09-01"

    @patch("src.vacancy_search.apify_client.requests.post")
    def test_dedupes_by_company_title_url(self, mock_post, monkeypatch):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )

        duplicate_item = {
            "company": "Acme Engineering",
            "positionName": "Operations Foreman",
            "url": "https://za.indeed.com/viewjob?jk=1",
            "description": "Run the workshop.",
        }
        mock_post.side_effect = [
            _mock_response([duplicate_item, duplicate_item]),
            _mock_response([]),
        ]

        results = fetch_vacancies(limit=25)

        assert len(results) == 1

    @patch("src.vacancy_search.apify_client.requests.post")
    def test_request_error_on_one_actor_still_returns_other(
        self, mock_post, monkeypatch
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )

        import requests as _requests

        linkedin_items = [
            {
                "companyName": "Beta Power",
                "title": "Project Engineer",
                "link": "https://www.linkedin.com/jobs/view/2",
            }
        ]
        mock_post.side_effect = [
            _requests.ConnectionError("indeed actor unreachable"),
            _mock_response(linkedin_items),
        ]

        results = fetch_vacancies(limit=25)

        assert len(results) == 1
        assert results[0].company == "Beta Power"
