"""RED: src/vacancy_search/schema.py doesn't exist yet — these imports must fail first."""

import pytest

from src.vacancy_search.schema import Vacancy


class TestVacancyValidation:
    def test_valid_vacancy_defaults(self):
        vacancy = Vacancy(
            company="FanMovement (Pty) Ltd",
            title="Operations Foreman",
            url="https://za.indeed.com/viewjob?jk=abc123",
        )

        assert vacancy.status == "new"
        assert vacancy.platform == "indeed"
        assert vacancy.scraped_at

    def test_missing_company_raises(self):
        with pytest.raises(ValueError, match="company"):
            Vacancy(company="", title="Operations Foreman", url="https://example.com")

    def test_missing_title_raises(self):
        with pytest.raises(ValueError, match="title"):
            Vacancy(company="Acme", title="", url="https://example.com")

    def test_missing_url_raises(self):
        with pytest.raises(ValueError, match="url"):
            Vacancy(company="Acme", title="Operations Foreman", url="")

    def test_invalid_platform_raises(self):
        with pytest.raises(ValueError, match="platform"):
            Vacancy(
                company="Acme",
                title="Operations Foreman",
                url="https://example.com",
                platform="glassdoor",
            )

    def test_pnet_platform_accepted(self):
        vacancy = Vacancy(
            company="Acme",
            title="Operations Foreman",
            url="https://www.pnet.co.za/jobs/123",
            platform="pnet",
        )

        assert vacancy.platform == "pnet"

    def test_careers24_platform_accepted(self):
        vacancy = Vacancy(
            company="Acme",
            title="Operations Foreman",
            url="https://www.careers24.com/jobs/123",
            platform="careers24",
        )

        assert vacancy.platform == "careers24"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="status"):
            Vacancy(
                company="Acme",
                title="Operations Foreman",
                url="https://example.com",
                status="bogus",
            )

    def test_linkedin_platform_accepted(self):
        vacancy = Vacancy(
            company="Acme",
            title="Project Engineer",
            url="https://www.linkedin.com/jobs/view/123",
            platform="linkedin",
        )

        assert vacancy.platform == "linkedin"

    def test_optional_fields_default_sane(self):
        vacancy = Vacancy(
            company="Acme", title="Operations Foreman", url="https://example.com"
        )

        assert vacancy.description == ""
        assert vacancy.salary is None
        assert vacancy.deadline is None
        assert vacancy.id is None
