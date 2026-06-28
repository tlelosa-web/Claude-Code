from src.lead_import.schema import Lead
from src.research.schema import ResearchResult
from src.asset_gen.prompt_builder import build_prompt
from src.asset_gen.pipeline import run_asset_gen
from src.asset_gen.schema import AssetResult, AssetType


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        id=1,
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        website="https://acme.co.za",
        industry="Manufacturing",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


def _make_research(**overrides) -> ResearchResult:
    defaults = dict(
        lead_id=1,
        summary="Acme Engineering is a steel fabrication firm offering plant maintenance.",
        raw_data={"services": ["Steel fabrication", "Plant maintenance"]},
    )
    defaults.update(overrides)
    return ResearchResult(**defaults)


class TestPromptBuilder:
    def test_prompt_contains_company_name(self):
        lead = _make_lead()
        research = _make_research()
        prompt = build_prompt(lead, research)
        assert "Acme Engineering" in prompt

    def test_prompt_contains_industry(self):
        lead = _make_lead(industry="Fabrication")
        research = _make_research()
        prompt = build_prompt(lead, research)
        assert "Fabrication" in prompt

    def test_prompt_contains_contact_name(self):
        lead = _make_lead()
        research = _make_research()
        prompt = build_prompt(lead, research)
        assert "John Smith" in prompt

    def test_prompt_contains_research_summary(self):
        lead = _make_lead()
        research = _make_research(summary="Custom summary about mining equipment.")
        prompt = build_prompt(lead, research)
        assert "Custom summary about mining equipment." in prompt


class TestAssetGenPipeline:
    def test_happy_path_returns_asset_result(self):
        lead = _make_lead()
        research = _make_research()
        result = run_asset_gen(lead, research)

        assert isinstance(result, AssetResult)
        assert result.lead_id == 1
        assert "Acme Engineering" in result.asset_text
        assert result.generated_at

    def test_asset_type_is_valid_enum(self):
        lead = _make_lead()
        research = _make_research()
        result = run_asset_gen(lead, research)

        assert isinstance(result.asset_type, AssetType)
        assert result.asset_type == AssetType.INSIGHT_DOC

    def test_custom_asset_type(self):
        lead = _make_lead()
        research = _make_research()
        result = run_asset_gen(lead, research, asset_type=AssetType.PAIN_POINT_SUMMARY)

        assert result.asset_type == AssetType.PAIN_POINT_SUMMARY

    def test_asset_text_contains_call_to_action(self):
        lead = _make_lead()
        research = _make_research()
        result = run_asset_gen(lead, research)

        assert "15 minutes" in result.asset_text
