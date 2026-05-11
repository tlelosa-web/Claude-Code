from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def draw_labeled_box(c: canvas.Canvas, x: float, y: float, w: float, h: float, label: str, font_size: int = 8) -> None:
    """Draw a box with label positioned above it."""
    c.setFont("Helvetica", font_size)
    c.drawString(x, y + h + 2, label)
    c.rect(x, y, w, h, stroke=1, fill=0)


def draw_box(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    """Draw a simple box."""
    c.rect(x, y, w, h, stroke=1, fill=0)


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    out_pdf = project_root / "2_Source_Data" / "raw_sources" / "Test Sheet Template v4.pdf"
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    page_w, page_h = A4

    # ============================================
    # HEADER SECTION
    # ============================================
    margin = 10 * mm
    header_y = page_h - 15 * mm

    # FAN MOVEMENT branding
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, header_y, "FAN MOVEMENT")
    c.setFont("Helvetica", 9)
    c.drawString(margin, header_y - 5 * mm, "AIR AND GAS MOVEMENT SOLUTIONS")

    # Title on the right
    c.setFont("Helvetica-Bold", 14)
    c.drawString(page_w - 80 * mm, header_y, "TEST RECORD SHEET")

    # ============================================
    # CONTRACT GRID (2x4)
    # ============================================
    grid_y = header_y - 12 * mm
    grid_row_h = 9 * mm
    grid_col_w = [50 * mm, 50 * mm, 50 * mm, 40 * mm]
    grid_x_positions = [margin, margin + grid_col_w[0], margin + grid_col_w[0] + grid_col_w[1], 
                        margin + grid_col_w[0] + grid_col_w[1] + grid_col_w[2]]

    # Row 1: Contract No, Fan Series, Fan Size, Imp. Form
    c.setFont("Helvetica-Bold", 8)
    c.drawString(grid_x_positions[0] + 2, grid_y + grid_row_h + 1, "Contract No")
    draw_box(c, grid_x_positions[0], grid_y, grid_col_w[0], grid_row_h)

    c.drawString(grid_x_positions[1] + 2, grid_y + grid_row_h + 1, "Fan Series")
    draw_box(c, grid_x_positions[1], grid_y, grid_col_w[1], grid_row_h)

    c.drawString(grid_x_positions[2] + 2, grid_y + grid_row_h + 1, "Fan Size")
    draw_box(c, grid_x_positions[2], grid_y, grid_col_w[2], grid_row_h)

    c.drawString(grid_x_positions[3] + 2, grid_y + grid_row_h + 1, "Imp. Form")
    draw_box(c, grid_x_positions[3], grid_y, grid_col_w[3], grid_row_h)

    # Row 2: Date
    grid_y -= grid_row_h
    c.setFont("Helvetica-Bold", 8)
    c.drawString(grid_x_positions[0] + 2, grid_y + grid_row_h + 1, "Date (DD/MM/YYYY)")
    draw_box(c, grid_x_positions[0], grid_y, grid_col_w[0], grid_row_h)

    # ============================================
    # CUSTOMER & MOTOR SPECS
    # ============================================
    customer_y = grid_y - 12 * mm
    spec_row_h = 8 * mm

    # Customer Name
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin + 2, customer_y + spec_row_h + 1, "Customer Name:")
    draw_box(c, margin, customer_y, 140 * mm, spec_row_h)

    # Motor Make
    motor_make_y = customer_y
    c.drawString(page_w - 90 * mm + 2, motor_make_y + spec_row_h + 1, "MAKE:")
    draw_box(c, page_w - 90 * mm, motor_make_y, 80 * mm, spec_row_h)

    # ACTUAL VALUES section header
    actual_values_y = customer_y - 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, actual_values_y, "ACTUAL VALUES")

    # Motor Current, Voltage, Fan Speed, Connection
    specs_y = actual_values_y - 9 * mm
    spec_box_h = 8 * mm
    spec_col_w = 45 * mm

    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(margin + 2, specs_y + spec_box_h + 1, "Motor Current (A)")
    draw_box(c, margin, specs_y, spec_col_w, spec_box_h)

    c.drawString(margin + spec_col_w + 3, specs_y + spec_box_h + 1, "Motor Voltage (V)")
    draw_box(c, margin + spec_col_w, specs_y, spec_col_w, spec_box_h)

    c.drawString(margin + 2 * spec_col_w + 3, specs_y + spec_box_h + 1, "Fan Speed (r/min)")
    draw_box(c, margin + 2 * spec_col_w, specs_y, spec_col_w, spec_box_h)

    c.drawString(margin + 3 * spec_col_w + 3, specs_y + spec_box_h + 1, "Connection")
    draw_box(c, margin + 3 * spec_col_w, specs_y, spec_col_w, spec_box_h)

    # Description field
    desc_y = specs_y - 10 * mm
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin + 2, desc_y + spec_box_h + 1, "Description:")
    draw_box(c, margin, desc_y, 140 * mm, spec_box_h)

    # ============================================
    # TEST READINGS TABLE
    # ============================================
    table_y = desc_y - 12 * mm
    table_header_h = 10 * mm
    table_data_h = 40 * mm
    table_x = margin
    table_w = page_w - 2 * margin

    # Table outer border
    c.rect(table_x, table_y - table_header_h - table_data_h, table_w, table_header_h + table_data_h, stroke=1, fill=0)

    # Column definitions
    col_defs = [
        ("Motor Serial No", 30 * mm),
        ("Blade Pitch (Deg)", 22 * mm),
        ("Tacho # & Clamp", 22 * mm),
        ("Speed (r/min)", 18 * mm),
        ("I1 (A)", 14 * mm),
        ("I2 (A)", 14 * mm),
        ("I3 (A)", 14 * mm),
        ("V1 (V)", 14 * mm),
        ("V2 (V)", 14 * mm),
        ("V3 (V)", 14 * mm),
        ("Connection", 18 * mm),
    ]

    # Draw vertical lines and headers
    c.setFont("Helvetica-Bold", 7)
    cx = table_x
    for i, (header, col_w) in enumerate(col_defs):
        # Draw vertical line
        if i < len(col_defs) - 1:
            next_cx = cx + col_w
            c.line(next_cx, table_y - table_header_h, next_cx, table_y - table_header_h - table_data_h)
        # Draw header text (centered)
        c.drawString(cx + 2, table_y - 2, header)
        cx += col_w

    # Horizontal line between header and data
    c.line(table_x, table_y - table_header_h, table_x + table_w, table_y - table_header_h)

    # ============================================
    # SIGNATURE & REMARKS SECTION
    # ============================================
    sig_y = table_y - table_header_h - table_data_h - 12 * mm
    sig_box_h = 8 * mm

    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin + 2, sig_y + sig_box_h + 1, "Testing Operator Signature")
    draw_box(c, margin, sig_y, 90 * mm, sig_box_h)

    sig_x2 = margin + 100 * mm
    c.drawString(sig_x2 + 2, sig_y + sig_box_h + 1, "Quality Inspector Signature")
    draw_box(c, sig_x2, sig_y, 90 * mm, sig_box_h)

    # Remarks
    remarks_y = sig_y - 10 * mm
    c.setFont("Helvetica", 7)
    c.drawString(margin, remarks_y, "Remarks: Operator and Quality to sign on completion of work, with date completed.")

    # Footer date
    footer_y = remarks_y - 8 * mm
    c.drawString(margin, footer_y, "Date Completed: _______________")

    c.save()
    print(f"FM4043 Test Record Sheet template created: {out_pdf}")

    c.showPage()
    c.save()
    print(f"Created template: {out_pdf}")


if __name__ == "__main__":
    main()
