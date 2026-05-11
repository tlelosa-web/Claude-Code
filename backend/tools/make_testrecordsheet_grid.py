from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pypdf import PdfReader, PdfWriter

TEMPLATE = Path("templates/TestRecordSheet.pdf")
OUT_DIR = Path("output")
OUT_GRID = OUT_DIR / "TestRecordSheet_GRID.pdf"

def main():
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing template: {TEMPLATE.resolve()}")

    OUT_DIR.mkdir(exist_ok=True)

    reader = PdfReader(str(TEMPLATE))
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
