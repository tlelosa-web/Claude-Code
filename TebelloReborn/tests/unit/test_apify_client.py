"""RED: src/vacancy_search/apify_client.py doesn't exist yet — these imports
must fail first."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.vacancy_search.apify_client import (
    FIXTURE_VACANCIES,
    SEARCH_TITLES,
    fetch_vacancies,
    normalize_url,
)
from src.vacancy_search.extractor import VacancyExtractionError
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


class TestNormalizeUrl:
    def test_strips_query_string(self):
        assert normalize_url(
            "https://za.indeed.com/viewjob?jk=1&utm_source=x"
        ) == normalize_url("https://za.indeed.com/viewjob")

    def test_strips_trailing_slash(self):
        assert normalize_url("https://example.co.za/job1/") == normalize_url(
            "https://example.co.za/job1"
        )

    def test_strips_fragment(self):
        assert normalize_url("https://example.co.za/job1#section") == normalize_url(
            "https://example.co.za/job1"
        )


class TestDedupeUsesNormalizedUrl:
    @patch("src.vacancy_search.apify_client.requests.post")
    def test_dedupes_vacancies_differing_only_by_utm_query_string(
        self, mock_post, monkeypatch
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )

        indeed_item = {
            "company": "Acme Engineering",
            "positionName": "Operations Foreman",
            "url": "https://za.indeed.com/viewjob?jk=1",
            "description": "Run the workshop.",
        }
        linkedin_item = {
            "companyName": "Acme Engineering",
            "title": "Operations Foreman",
            "link": "https://za.indeed.com/viewjob?jk=1&utm_source=newsletter",
            "description": "Run the workshop.",
        }
        mock_post.side_effect = [
            _mock_response([indeed_item]),
            _mock_response([linkedin_item]),
        ]

        results = fetch_vacancies(limit=25)

        assert len(results) == 1

    @patch("src.vacancy_search.apify_client.requests.post")
    def test_dedupes_vacancies_differing_only_by_trailing_slash(
        self, mock_post, monkeypatch
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )

        indeed_item = {
            "company": "Acme Engineering",
            "positionName": "Operations Foreman",
            "url": "https://za.indeed.com/viewjob/1",
            "description": "Run the workshop.",
        }
        linkedin_item = {
            "companyName": "Acme Engineering",
            "title": "Operations Foreman",
            "link": "https://za.indeed.com/viewjob/1/",
            "description": "Run the workshop.",
        }
        mock_post.side_effect = [
            _mock_response([indeed_item]),
            _mock_response([linkedin_item]),
        ]

        results = fetch_vacancies(limit=25)

        assert len(results) == 1


class TestPnetCareers24DiscoveryIntegration:
    """fetch_vacancies() now folds pnet/careers24 in via
    discovery.get_job_urls() -> crawler_client.fetch_raw_page() ->
    extractor.extract_vacancy_fields(), combined with Indeed/LinkedIn before
    the single shared _dedupe(...)[:limit] call. No `if platform == "pnet"`
    branching exists in apify_client.py — both platforms go through the
    identical pipeline (Amendment, judgment call #3)."""

    @patch("src.vacancy_search.apify_client.extract_vacancy_fields")
    @patch("src.vacancy_search.apify_client.fetch_raw_page")
    @patch("src.vacancy_search.apify_client.get_job_urls")
    @patch("src.vacancy_search.apify_client.requests.post")
    def test_folds_pnet_and_careers24_into_combined_results(
        self,
        mock_post,
        mock_get_job_urls,
        mock_fetch_raw_page,
        mock_extract_vacancy_fields,
        monkeypatch,
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )
        mock_post.return_value = _mock_response([])

        def _get_job_urls_side_effect(platform, limit):
            if platform == "pnet":
                return ["https://example.co.za/pnet-job-1"]
            if platform == "careers24":
                return ["https://example.co.za/careers24-job-1"]
            raise AssertionError(f"unexpected platform {platform}")

        mock_get_job_urls.side_effect = _get_job_urls_side_effect
        mock_fetch_raw_page.side_effect = [
            {
                "url": "https://example.co.za/pnet-job-1",
                "title": "t",
                "text_content": "body",
                "_source_mode": "live",
            },
            {
                "url": "https://example.co.za/careers24-job-1",
                "title": "t",
                "text_content": "body",
                "_source_mode": "live",
            },
        ]
        mock_extract_vacancy_fields.side_effect = [
            {
                "company": "PNet Employer",
                "title": "Operations Foreman",
                "description": "desc",
                "url": "https://example.co.za/pnet-job-1",
                "salary": None,
                "deadline": None,
            },
            {
                "company": "Careers24 Employer",
                "title": "Operations Foreman",
                "description": "desc",
                "url": "https://example.co.za/careers24-job-1",
                "salary": None,
                "deadline": None,
            },
        ]

        results = fetch_vacancies(limit=25)

        companies = {v.company for v in results}
        platforms = {v.platform for v in results}
        assert "PNet Employer" in companies
        assert "Careers24 Employer" in companies
        assert "pnet" in platforms
        assert "careers24" in platforms
        assert mock_get_job_urls.call_args_list[0].args[0] in ("pnet", "careers24")

    @patch("src.vacancy_search.apify_client.extract_vacancy_fields")
    @patch("src.vacancy_search.apify_client.fetch_raw_page")
    @patch("src.vacancy_search.apify_client.get_job_urls")
    @patch("src.vacancy_search.apify_client.requests.post")
    def test_extraction_error_on_one_page_is_skipped_not_fatal(
        self,
        mock_post,
        mock_get_job_urls,
        mock_fetch_raw_page,
        mock_extract_vacancy_fields,
        monkeypatch,
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )
        mock_post.return_value = _mock_response([])

        def _get_job_urls_side_effect(platform, limit):
            if platform == "pnet":
                return [
                    "https://example.co.za/pnet-job-1",
                    "https://example.co.za/pnet-job-2",
                ]
            return []

        mock_get_job_urls.side_effect = _get_job_urls_side_effect
        mock_fetch_raw_page.side_effect = [
            {
                "url": "https://example.co.za/pnet-job-1",
                "title": "t1",
                "text_content": "body1",
                "_source_mode": "live",
            },
            {
                "url": "https://example.co.za/pnet-job-2",
                "title": "t2",
                "text_content": "body2",
                "_source_mode": "live",
            },
        ]
        mock_extract_vacancy_fields.side_effect = [
            VacancyExtractionError("malformed output"),
            {
                "company": "PNet Employer 2",
                "title": "Operations Foreman",
                "description": "desc",
                "url": "https://example.co.za/pnet-job-2",
                "salary": None,
                "deadline": None,
            },
        ]

        results = fetch_vacancies(limit=25)

        companies = {v.company for v in results}
        assert companies == {"PNet Employer 2"}

    def test_pnet_fallback_path_works_end_to_end_through_fetch_vacancies(
        self, monkeypatch, tmp_path
    ):
        """discovery_config.json's pnet.mode = "manual_pending_verification"
        must still return PNet vacancies sourced from
        data/crawler_seed_urls.json's existing entries, through the real
        fetch_vacancies() integration point (not just get_job_urls in
        isolation, already covered by test_discovery.py)."""
        monkeypatch.setenv("OFFLINE_MODE", "true")

        discovery_config_path = tmp_path / "discovery_config.json"
        discovery_config_path.write_text(
            json.dumps(
                {
                    "pnet": {"mode": "manual_pending_verification"},
                    "careers24": {"mode": "auto"},
                }
            )
        )
        seed_urls_path = tmp_path / "crawler_seed_urls.json"
        seed_urls_path.write_text(
            json.dumps({"pnet": ["https://example.co.za/pnet-seed-job"]})
        )

        with patch(
            "src.vacancy_search.apify_client.DISCOVERY_CONFIG_PATH",
            str(discovery_config_path),
        ), patch("src.vacancy_search.apify_client.SEED_URLS_PATH", str(seed_urls_path)):
            results = fetch_vacancies(limit=25)

        assert any(v.platform == "pnet" for v in results)


class TestFixtureModeDegradedWarning:
    @patch("src.vacancy_search.apify_client.extract_vacancy_fields")
    @patch("src.vacancy_search.apify_client.fetch_raw_page")
    @patch("src.vacancy_search.apify_client.get_job_urls")
    @patch("src.vacancy_search.apify_client.requests.post")
    def test_warns_when_a_non_offline_run_returns_fixture_tagged_pages(
        self,
        mock_post,
        mock_get_job_urls,
        mock_fetch_raw_page,
        mock_extract_vacancy_fields,
        monkeypatch,
        caplog,
    ):
        monkeypatch.setenv("APIFY_API_KEY", "test-key")
        monkeypatch.delenv("OFFLINE_MODE", raising=False)
        monkeypatch.setattr(
            "src.vacancy_search.apify_client.SEARCH_TITLES", ["Operations Foreman"]
        )
        mock_post.return_value = _mock_response([])
        mock_get_job_urls.side_effect = lambda platform, limit: (
            ["https://example.co.za/pnet-job-1"] if platform == "pnet" else []
        )
        mock_fetch_raw_page.return_value = {
            "url": "https://example.co.za/pnet-job-1",
            "title": "t",
            "text_content": "body",
            "_source_mode": "fixture",
        }
        mock_extract_vacancy_fields.return_value = {
            "company": "Degraded Employer",
            "title": "Operations Foreman",
            "description": "desc",
            "url": "https://example.co.za/pnet-job-1",
            "salary": None,
            "deadline": None,
        }

        with caplog.at_level("WARNING"):
            fetch_vacancies(limit=25)

        assert any("fixture" in record.message.lower() for record in caplog.records)

    def test_offline_mode_never_triggers_the_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("OFFLINE_MODE", "true")

        with caplog.at_level("WARNING"):
            fetch_vacancies(limit=25)

        assert not any("fixture" in record.message.lower() for record in caplog.records)
