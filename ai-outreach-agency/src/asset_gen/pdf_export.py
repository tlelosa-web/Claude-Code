import re
from pathlib import Path

from fpdf import FPDF

from src.lead_import.schema import Lead

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_-]+")


def _sanitize_filename(name: str) -> str:
    return _UNSAFE_FILENAME_CHARS.sub("_", name.strip()).strip("_")


def export_asset_pdf(lead: Lead, text: str, output_dir: str | Path = "exports") -> Path:
    """Render an asset's final text to a single PDF file. Pure local I/O, no network."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            pdf.ln(4)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 8, stripped[3:])
        elif stripped.startswith("# "):
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 10, stripped[2:])
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, stripped)

    filename = f"{_sanitize_filename(lead.company_name)}_{lead.id}.pdf"
    output_path = output_dir / filename
    pdf.output(str(output_path))
    return output_path
