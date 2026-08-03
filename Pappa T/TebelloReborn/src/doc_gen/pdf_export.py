import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from src.vacancy_search.schema import Vacancy

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]+")

# Helvetica (a core PDF font) can't render these Unicode punctuation marks —
# replace with ASCII equivalents rather than let fpdf2 raise/mangle them.
_UNICODE_REPLACEMENTS = {
    "—": "--",
    "–": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "•": "-",
    "…": "...",
}


def _sanitize_filename(name: str) -> str:
    return _UNSAFE_FILENAME_CHARS.sub("_", name.strip()).strip("_")


def _clean_text(text: str) -> str:
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    # Helvetica (a core, non-embedded PDF font) only supports latin-1.
    # Headless-Claude-Code-generated content isn't fully predictable, so
    # anything not covered by the specific substitutions above (currency
    # symbols, CJK, emoji, etc.) must degrade to "?" rather than crash the
    # export — losing a character is recoverable, an unhandled exception
    # aborting a whole run-all batch is not.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _render_markdown_pdf(content: str) -> FPDF:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    for line in content.splitlines():
        stripped = _clean_text(line.strip())
        if not stripped:
            pdf.ln(4)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 8, stripped[3:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 10, stripped[2:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, stripped, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf


def _export(
    vacancy: Vacancy, content: str, doc_type: str, output_dir: str | Path
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = _render_markdown_pdf(content)

    filename = f"{_sanitize_filename(vacancy.company)}_{vacancy.id}_{doc_type}.pdf"
    output_path = output_dir / filename
    pdf.output(str(output_path))
    return output_path


def export_cv_pdf(
    vacancy: Vacancy, content: str, output_dir: str | Path = "exports"
) -> Path:
    """Render a generated CV to a PDF file. Pure local I/O, no network."""
    return _export(vacancy, content, "cv", output_dir)


def export_cover_letter_pdf(
    vacancy: Vacancy, content: str, output_dir: str | Path = "exports"
) -> Path:
    """Render a generated cover letter to a PDF file. Pure local I/O, no network."""
    return _export(vacancy, content, "cover_letter", output_dir)
