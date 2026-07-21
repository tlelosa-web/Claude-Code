"""RED: src/doc_gen/pdf_export.py doesn't exist yet — these imports must
fail first. Reuses the working fpdf2 pattern from
ai-outreach-agency/src/asset_gen/pdf_export.py and
_archive_qwen_prototype/4_Scripts/generate_cv_pdf.py."""

from src.doc_gen.pdf_export import export_cover_letter_pdf, export_cv_pdf
from src.vacancy_search.schema import Vacancy


def _vacancy(**overrides) -> Vacancy:
    defaults = dict(
        id=42,
        company="Acme Engineering",
        title="Operations Foreman",
        url="https://za.indeed.com/viewjob?jk=abc123",
    )
    defaults.update(overrides)
    return Vacancy(**defaults)


_CONTENT = "# Tebello Lelosa\n\n## Experience\n\n- Operations Foreman, FanMovement\n"


class TestExportCvPdf:
    def test_writes_valid_pdf_file(self, tmp_path):
        output_path = export_cv_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)

        assert output_path.exists()
        assert output_path.suffix == ".pdf"
        with open(output_path, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_filename_includes_company_and_vacancy_id(self, tmp_path):
        output_path = export_cv_pdf(_vacancy(company="Acme Engineering", id=42), _CONTENT, output_dir=tmp_path)

        assert "Acme_Engineering" in output_path.name
        assert "42" in output_path.name

    def test_filename_marks_doc_type_cv(self, tmp_path):
        output_path = export_cv_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)

        assert "cv" in output_path.name

    def test_creates_output_dir_if_missing(self, tmp_path):
        nested = tmp_path / "nested" / "exports"

        output_path = export_cv_pdf(_vacancy(), _CONTENT, output_dir=nested)

        assert output_path.exists()
        assert nested.is_dir()


class TestExportCoverLetterPdf:
    def test_writes_valid_pdf_file(self, tmp_path):
        output_path = export_cover_letter_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)

        assert output_path.exists()
        with open(output_path, "rb") as f:
            assert f.read(5) == b"%PDF-"

    def test_filename_marks_doc_type_cover_letter(self, tmp_path):
        output_path = export_cover_letter_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)

        assert "cover_letter" in output_path.name

    def test_cv_and_cover_letter_filenames_differ(self, tmp_path):
        cv_path = export_cv_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)
        cl_path = export_cover_letter_pdf(_vacancy(), _CONTENT, output_dir=tmp_path)

        assert cv_path != cl_path
