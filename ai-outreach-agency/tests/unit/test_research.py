from src.lead_import.schema import Lead
from src.research.pipeline import research_lead
from src.research.schema import ResearchResult


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id=1,
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        website="https://acme.co.za",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


class TestResearchPipeline:
    def test_happy_path(self):
        lead = _make_lead()
        result = research_lead(lead)

        assert isinstance(result, ResearchResult)
        assert result.lead_id == 1
        assert "Example Engineering Co." in result.summary
        assert result.raw_data["url"] == "https://acme.co.za"
        assert result.researched_at

    def test_missing_website_handled(self):
        lead = _make_lead(website=None)
        result = research_lead(lead)

        assert isinstance(result, ResearchResult)
        assert result.lead_id == 1
        assert "No website available" in result.summary
        assert "Manual research required" in result.summary
        assert result.raw_data == {}

    def test_summary_contains_services(self):
        lead = _make_lead()
        result = research_lead(lead)

        assert "Steel fabrication" in result.summary

    def test_summary_contains_recent_news(self):
        lead = _make_lead()
        result = research_lead(lead)

        assert "conveyor system" in result.summary
