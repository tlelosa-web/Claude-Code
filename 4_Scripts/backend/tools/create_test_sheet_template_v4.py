from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def box(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.rect(x, y, w, h, stroke=1, fill=0)


def text(c: canvas.Canvas, x: float, y: float, value: str, size: float = 7.0, bold: bool = False) -> None:
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, value)


def center(c: canvas.Canvas, x: float, y: float, value: str, size: float = 7.0, bold: bool = False) -> None:
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, value)


def main() -> None:
    project_root = Path(__file__).resolve().parents[3]
    out_pdf = project_root / "2_Source_Data" / "raw_sources" / "Test Sheet Template v4.pdf"
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    page_w, page_h = A4
    margin_x = 17 * mm
    table_w = page_w - 2 * margin_x

    c.setLineWidth(0.55)

    row_h = 8 * mm
    meta_x = margin_x
    meta_w = table_w

    # Level 1: branding is the primary header.
    brand_y = page_h - 15 * mm
    text(c, margin_x, brand_y, "FAN MOVEMENT", 18, True)
    text(c, margin_x, brand_y - 7 * mm, "AIR AND GAS MOVEMENT SOLUTIONS", 8.0)

    # Level 2: document title, generation date, and contract metadata grid.
    title_y = page_h - 35 * mm
    box(c, meta_x, title_y, meta_w, row_h)
    text(c, meta_x + 2, title_y + 3 * mm, "Test Record Sheet", 9.0, True)
    text(c, meta_x + meta_w - 72 * mm, title_y + 3 * mm, "DATE:", 8.5, True)

    contract_y = title_y - row_h
    box(c, meta_x, contract_y, meta_w, row_h)
    meta_cells_mm = [22, 26, 25, 25, 23, 27, 23, 29]
    scale = meta_w / sum(w * mm for w in meta_cells_mm)
    meta_cells = [w * mm * scale for w in meta_cells_mm]
    cx = meta_x
    labels = ["Contract No.", "", "Fan Series", "", "Fan Size", "", "Imp. Form", ""]
    for idx, cell_w in enumerate(meta_cells):
        if idx:
            c.line(cx, contract_y, cx, contract_y + row_h)
        if labels[idx]:
            center(c, cx + cell_w / 2, contract_y + 3 * mm, labels[idx], 5.6, True)
        cx += cell_w

    # Level 3: customer and motor specifications.
    customer_y = contract_y - 11 * mm
    box(c, meta_x, customer_y, meta_w, row_h)
    c.line(meta_x + 25 * mm, customer_y, meta_x + 25 * mm, customer_y + row_h)
    text(c, meta_x + 2, customer_y + 3 * mm, "Customer Name:", 6.4)

    # Motor actual values and make/description block.
    spec_y = customer_y - 3 * row_h
    spec_h = 3 * row_h
    left_w = 65 * mm
    mid_w = 50 * mm
    right_w = meta_w - left_w - mid_w
    box(c, meta_x, spec_y, left_w, spec_h)
    for i in range(1, 3):
        c.line(meta_x, spec_y + i * row_h, meta_x + left_w, spec_y + i * row_h)
    c.line(meta_x + 21 * mm, spec_y, meta_x + 21 * mm, spec_y + spec_h)
    c.line(meta_x + 43 * mm, spec_y, meta_x + 43 * mm, spec_y + spec_h)
    text(c, meta_x + 2, spec_y + 2 * row_h + 3 * mm, "Motor Current:", 6.4, True)
    text(c, meta_x + 2, spec_y + row_h + 3 * mm, "Motor Voltage:", 6.4, True)
    text(c, meta_x + 2, spec_y + 3 * mm, "Fan Speed:", 6.4, True)
    center(c, meta_x + 54 * mm, spec_y + 2 * row_h + 3 * mm, "Amp", 6.4, True)
    center(c, meta_x + 54 * mm, spec_y + row_h + 3 * mm, "Volt", 6.4, True)
    center(c, meta_x + 54 * mm, spec_y + 3 * mm, "r/min", 6.4, True)

    box(c, meta_x + left_w, spec_y, mid_w, spec_h)

    rx = meta_x + left_w + mid_w
    box(c, rx, spec_y, right_w, spec_h)
    for i in range(1, 3):
        c.line(rx, spec_y + i * row_h, rx + right_w, spec_y + i * row_h)
    make_label_w = 22 * mm
    c.line(rx + make_label_w, spec_y, rx + make_label_w, spec_y + spec_h)
    c.line(rx + make_label_w + (right_w - make_label_w) / 3, spec_y + 2 * row_h, rx + make_label_w + (right_w - make_label_w) / 3, spec_y + spec_h)
    c.line(rx + make_label_w + 2 * (right_w - make_label_w) / 3, spec_y + 2 * row_h, rx + make_label_w + 2 * (right_w - make_label_w) / 3, spec_y + spec_h)
    text(c, rx + 6 * mm, spec_y + 2 * row_h + 3 * mm, "MAKE:", 6.4, True)
    brand_w = (right_w - make_label_w) / 3
    for i, brand in enumerate(("ACTOM", "ASKARI", "WEG")):
        center(c, rx + make_label_w + i * brand_w + brand_w / 2, spec_y + 2 * row_h + 3 * mm, brand, 6.8, True)
    text(c, rx + 3 * mm, spec_y + row_h + 3 * mm, "Description:", 6.4, True)

    actual_y = spec_y - row_h
    box(c, meta_x, actual_y, meta_w, row_h)
    text(c, meta_x + 2, actual_y + 3 * mm, "ACTUAL VALUES", 6.5)

    # Level 4: main readings table.
    table_top = actual_y
    header_1_h = 12 * mm
    header_2_h = 8 * mm
    data_row_h = 7 * mm
    data_rows = 19
    sig_h = 15 * mm
    remarks_h = 8 * mm
    bottom_blank_h = 8 * mm
    table_h = header_1_h + header_2_h + data_rows * data_row_h + sig_h + remarks_h + bottom_blank_h
    table_bottom = table_top - table_h
    box(c, meta_x, table_bottom, meta_w, table_h)

    col_mm = [30, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5]
    scale = meta_w / sum(w * mm for w in col_mm)
    cols = [w * mm * scale for w in col_mm]
    xs = [meta_x]
    for w in cols:
        xs.append(xs[-1] + w)

    data_top = table_top - header_1_h - header_2_h
    sig_top = data_top - data_rows * data_row_h
    remarks_top = sig_top - sig_h
    final_blank_top = remarks_top - remarks_h

    c.line(meta_x, table_top - header_1_h, meta_x + meta_w, table_top - header_1_h)
    c.line(meta_x, data_top, meta_x + meta_w, data_top)
    for r in range(data_rows + 1):
        yy = data_top - r * data_row_h
        c.line(meta_x, yy, meta_x + meta_w, yy)
    c.line(meta_x, sig_top, meta_x + meta_w, sig_top)
    c.line(meta_x, remarks_top, meta_x + meta_w, remarks_top)
    c.line(meta_x, final_blank_top, meta_x + meta_w, final_blank_top)

    for x in xs[1:-1]:
        c.line(x, table_top, x, sig_top)

    # Signature row split only in half; remarks are full-width.
    c.line(meta_x + meta_w / 2, sig_top, meta_x + meta_w / 2, remarks_top)

    center(c, (xs[0] + xs[1]) / 2, table_top - 8 * mm, "Motor Serial Number", 6.0, True)
    center(c, (xs[1] + xs[2]) / 2, table_top - 7 * mm, "Blade Pitch", 5.8, True)
    center(c, (xs[1] + xs[2]) / 2, table_top - 10 * mm, "Deg.", 5.8, True)
    center(c, (xs[2] + xs[3]) / 2, table_top - 4.5 * mm, "Tacho &", 5.5, True)
    center(c, (xs[2] + xs[3]) / 2, table_top - 7.5 * mm, "Clamp Meter", 5.5, True)
    center(c, (xs[2] + xs[3]) / 2, table_top - 10.5 * mm, "Serial No", 5.5, True)
    center(c, (xs[3] + xs[4]) / 2, table_top - 5.5 * mm, "Speed", 6.0, True)
    center(c, (xs[3] + xs[4]) / 2, table_top - header_1_h - 5 * mm, "r/min", 6.0, True)
    center(c, (xs[4] + xs[7]) / 2, table_top - 6 * mm, "Current", 6.0, True)
    center(c, (xs[7] + xs[10]) / 2, table_top - 6 * mm, "Voltage", 6.0, True)
    center(c, (xs[10] + xs[11]) / 2, table_top - 8 * mm, "Connection", 6.0, True)
    for idx, phase in zip(range(4, 7), ("PH1", "PH2", "PH3")):
        center(c, (xs[idx] + xs[idx + 1]) / 2, table_top - header_1_h - 5 * mm, phase, 6.0, True)
    for idx, phase in zip(range(7, 10), ("PH1", "PH2", "PH3")):
        center(c, (xs[idx] + xs[idx + 1]) / 2, table_top - header_1_h - 5 * mm, phase, 6.0, True)

    # Level 5: sign-offs and remarks.
    text(c, meta_x + 2, sig_top - 9 * mm, "Testing Operator Signature:", 6.0)
    text(c, meta_x + meta_w / 2 + 2, sig_top - 9 * mm, "Quality Inspector Signature:", 6.0)
    text(c, meta_x + 2, remarks_top - 5 * mm, "Remarks:  Operator and Quality to sign on completion of work, with date completed.", 6.0)

    c.showPage()
    c.save()
    print(f"FM4043 Test Record Sheet template created: {out_pdf}")


if __name__ == "__main__":
    main()
