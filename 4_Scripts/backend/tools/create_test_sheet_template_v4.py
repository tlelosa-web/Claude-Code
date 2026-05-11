from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def draw_labeled_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str) -> None:
    c.setFont("Helvetica", 8)
    c.drawString(x, y + h + 3, label)
    c.rect(x, y, w, h, stroke=1, fill=0)


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    out_pdf = project_root / "2_Source_Data" / "raw_sources" / "Test Sheet Template v4.pdf"
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    page_w, page_h = A4

    # Page title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(page_w / 2, page_h - 24 * mm, "TEST RECORD SHEET")
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_w / 2, page_h - 30 * mm, "Fan Movement - New Template v4")

    # Outer content border
    margin = 12 * mm
    c.rect(margin, margin, page_w - (2 * margin), page_h - (2 * margin), stroke=1, fill=0)

    # Header section
    header_top = page_h - 45 * mm
    row_h = 11 * mm
    col_x = [18 * mm, 52 * mm, 88 * mm, 128 * mm, 168 * mm]

    draw_labeled_box(c, col_x[0], header_top, 30 * mm, row_h, "Contract No")
    draw_labeled_box(c, col_x[1], header_top, 32 * mm, row_h, "Fan Series")
    draw_labeled_box(c, col_x[2], header_top, 36 * mm, row_h, "Fan Size")
    draw_labeled_box(c, col_x[3], header_top, 34 * mm, row_h, "Form")
    draw_labeled_box(c, col_x[4], header_top, 26 * mm, row_h, "Date")

    # Customer and motor section
    y2 = header_top - 16 * mm
    draw_labeled_box(c, 18 * mm, y2, 90 * mm, row_h, "Customer Name")
    draw_labeled_box(c, 112 * mm, y2, 46 * mm, row_h, "Motor Make")
    draw_labeled_box(c, 162 * mm, y2, 32 * mm, row_h, "Description")

    y3 = y2 - 16 * mm
    draw_labeled_box(c, 18 * mm, y3, 38 * mm, row_h, "Motor Current (A)")
    draw_labeled_box(c, 60 * mm, y3, 38 * mm, row_h, "Motor Voltage (V)")
    draw_labeled_box(c, 102 * mm, y3, 38 * mm, row_h, "Fan Speed (RPM)")
    draw_labeled_box(c, 144 * mm, y3, 50 * mm, row_h, "Connection")

    # Measurement table
    c.setFont("Helvetica-Bold", 11)
    c.drawString(18 * mm, y3 - 12 * mm, "TEST READINGS")

    table_top = y3 - 17 * mm
    table_x = 18 * mm
    table_w = 176 * mm
    table_h = 34 * mm
    c.rect(table_x, table_top - table_h, table_w, table_h, stroke=1, fill=0)

    # Vertical separators
    col_widths = [24 * mm, 14 * mm, 16 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 24 * mm]
    cx = table_x
    for w in col_widths[:-1]:
        cx += w
        c.line(cx, table_top, cx, table_top - table_h)

    # Horizontal midline
    c.line(table_x, table_top - (table_h / 2), table_x + table_w, table_top - (table_h / 2))

    headers = ["Motor Serial", "Pitch", "Tacho #", "RPM", "I1", "I2", "I3", "V1", "V2", "V3", "Conn"]
    c.setFont("Helvetica", 8)
    cx = table_x + 2
    for label, w in zip(headers, col_widths):
        c.drawString(cx, table_top + 3, label)
        cx += w

    # Footer notes and signature area
    y_footer = table_top - table_h - 16 * mm
    draw_labeled_box(c, 18 * mm, y_footer, 120 * mm, 22 * mm, "Notes")
    draw_labeled_box(c, 142 * mm, y_footer + 11 * mm, 52 * mm, 11 * mm, "Technician")
    draw_labeled_box(c, 142 * mm, y_footer, 52 * mm, 11 * mm, "Date")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(18 * mm, 14 * mm, "Template version: v4 (newly generated, not cloned)")

    c.showPage()
    c.save()
    print(f"Created template: {out_pdf}")


if __name__ == "__main__":
    main()
