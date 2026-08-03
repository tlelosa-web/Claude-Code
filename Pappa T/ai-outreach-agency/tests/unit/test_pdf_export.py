from src.asset_gen.pdf_export import export_asset_pdf
from src.lead_import.schema import Lead


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
    )
    defaults.update(overrides)
    return Lead(id=1, **defaults)


ASSET_TEXT = (
    "# AI Automation Insight: Acme Engineering\n\n"
    "Acme Engineering could benefit from targeted automation.\n\n"
    "## Key Opportunity\n\n"
    "Reduce manual reporting time by up to 40%."
)


class TestExportAssetPDF:
    def test_creates_pdf_file(self, tmp_path):
        lead = _make_lead()
        path = export_asset_pdf(lead, ASSET_TEXT, output_dir=tmp_path)

        assert path.exists()
        assert path.suffix == ".pdf"
        assert path.stat().st_size > 0

    def test_filename_includes_company_name_and_lead_id(self, tmp_path):
        lead = _make_lead()
        path = export_asset_pdf(lead, ASSET_TEXT, output_dir=tmp_path)

        assert "Acme" in path.name
        assert "1" in path.name

    def test_sanitizes_special_characters_in_company_name(self, tmp_path):
        lead = _make_lead(company_name="Acme & Sons (Pty) Ltd.")
        path = export_asset_pdf(lead, ASSET_TEXT, output_dir=tmp_path)

        assert path.exists()
        for char in ("&", "(", ")", "/", "\\"):
            assert char not in path.name

    def test_creates_output_dir_if_missing(self, tmp_path):
        lead = _make_lead()
        output_dir = tmp_path / "exports" / "nested"

        path = export_asset_pdf(lead, ASSET_TEXT, output_dir=output_dir)

        assert path.exists()
        assert path.parent == output_dir
