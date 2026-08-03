from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def _resolve_template() -> Path:
    import os

    project_root = Path(__file__).resolve().parents[3]
    raw_sources = project_root / "2_Source_Data" / "raw_sources"

    for env_key in ("TEST_RECORD_TEMPLATE_PATH", "TEST_SHEET_TEMPLATE_PATH", "TEST_RECORD_SHEET_TEMPLATE_PATH"):
        v = os.getenv(env_key)
        if v:
            p = Path(v).expanduser()
            if p.exists():
                return p

    preferred = raw_sources / "Test Sheet Tmp.pdf"
    if preferred.exists():
        return preferred

    direct = raw_sources / "TestRecordSheet.pdf"
    if direct.exists():
        return direct

    candidates = sorted(raw_sources.glob("Test Sheet*.pdf")) if raw_sources.exists() else []
    if candidates:
        return candidates[0]

    raise FileNotFoundError(
        "Test Record Sheet template PDF not found. "
        "Set TEST_RECORD_TEMPLATE_PATH to a valid PDF file."
    )


OUT_DIR = Path("output")
OUT_GRID = OUT_DIR / "TestRecordSheet_GRID.pdf"

def main():
    template = _resolve_template()

    OUT_DIR.mkdir(exist_ok=True)

    reader = PdfReader(str(template))
    page = reader.pages[0]
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)

    # Make an overlay grid PDF (same page size)
    overlay_path = OUT_DIR / "_grid_overlay.pdf"
    c = canvas.Canvas(str(overlay_path), pagesize=(w, h))

    # Draw border
    c.setLineWidth(0.5)
    c.rect(0, 0, w, h)

    # Grid every 10 mm, heavier line every 50 mm
    step = 10 * mm
    major = 50 * mm

    y = 0.0
    while y <= h:
        lw = 0.8 if abs((y % major)) < 0.001 else 0.2
        c.setLineWidth(lw)
        c.line(0, y, w, y)
        if lw > 0.2:
            c.setFont("Helvetica", 7)
            c.drawString(2, y + 2, f"Y={y:.1f}")
        y += step

    x = 0.0
    while x <= w:
        lw = 0.8 if abs((x % major)) < 0.001 else 0.2
        c.setLineWidth(lw)
        c.line(x, 0, x, h)
        if lw > 0.2:
            c.setFont("Helvetica", 7)
            c.drawString(x + 2, 2, f"X={x:.1f}")
        x += step

    # Page size label
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10, h - 15, f"GRID OVERLAY — page size: {w:.2f} x {h:.2f} points")

    c.save()

    # Merge overlay on top of template
    overlay_reader = PdfReader(str(overlay_path))
    overlay_page = overlay_reader.pages[0]

    out = PdfWriter()
    base = reader.pages[0]
    base.merge_page(overlay_page)
    out.add_page(base)

    with open(OUT_GRID, "wb") as f:
        out.write(f)

    print(f"Created: {OUT_GRID}")

if __name__ == "__main__":
    main()
