from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

# ============================================================
# NAMEPLATE PDF (existing)
# ============================================================
PLATE_W_MM = 105.0
PLATE_H_MM = 104.0

PLATE_W = PLATE_W_MM * mm
PLATE_H = PLATE_H_MM * mm

BORDER_MARGIN_MM = 4.0
LABEL_LEFT_X_MM = BORDER_MARGIN_MM + 1.0  # 1mm from border

BOX_H_MM = 5.5
BOX_GAP_MM = 1.0
ROW_PITCH_MM = BOX_H_MM + BOX_GAP_MM  # 6.5mm pitch

TOP_BOX_TOP_FROM_TOP_MM = 34.0
ROW0_BOX_TOP_Y_MM = PLATE_H_MM - TOP_BOX_TOP_FROM_TOP_MM

BOX_FILL = colors.Color(0.85, 0.85, 0.85)  # light grey
STROKE = colors.black
TEXT = colors.black

LABEL_FONT = 8
BOX_FONT = 8
UNIT_FONT = 7

HEADER_MAIN_FONT = 18
HEADER_SUB_FONT = 12
HEADER_TAGLINE_FONT = 8
HEADER_TITLE_FONT = 14

SERIES_X_MM = 17.0
SERIES_W_MM = 35.0

LEFT_STD_X_MM = 17.0
LEFT_STD_W_MM = 29.0

LEFT_SMALL_X_MM = 20.0
LEFT_SMALL_W_MM = 24.0

SIZE_W_MM = 36.5
SIZE_RIGHT_MARGIN_MM = 5.5
SIZE_X_MM = PLATE_W_MM - SIZE_RIGHT_MARGIN_MM - SIZE_W_MM  # 63.0

RIGHT_STD_W_MM = 24.5
RIGHT_STD_RIGHT_MARGIN_MM = 12.0
RIGHT_STD_X_MM = PLATE_W_MM - RIGHT_STD_RIGHT_MARGIN_MM - RIGHT_STD_W_MM  # 68.5
RIGHT_STD_W_MM = RIGHT_STD_W_MM - 4.0  # 20.5
RIGHT_STD_X_MM = RIGHT_STD_X_MM + 2.0  # now 70.5mm

RELUBE_X_MM = 38.0
RELUBE_W_MM = 29.0

RIGHT_LABEL_X_MM = 54.0
LEFT_LABEL_X_MM = LABEL_LEFT_X_MM

def mm_to_pt(x_mm: float) -> float:
    return x_mm * mm

def pt_to_mm(x_pt: float) -> float:
    return x_pt / mm

def row_box_top_y_mm(row_index: int) -> float:
    return ROW0_BOX_TOP_Y_MM - (row_index * ROW_PITCH_MM)

def centered_baseline_y_mm(box_bottom_y_mm: float, box_h_mm: float, font_size: int) -> float:
    y_mid_pt = mm_to_pt(box_bottom_y_mm + box_h_mm / 2.0)
    y_base_pt = y_mid_pt - (font_size * 0.35)
    return pt_to_mm(y_base_pt)

def draw_box(c: canvas.Canvas, x_mm: float, box_top_y_mm: float, w_mm: float, h_mm: float):
    box_bottom_y_mm = box_top_y_mm - h_mm
    c.setStrokeColor(STROKE)
    c.setLineWidth(1)
    c.setFillColor(BOX_FILL)
    c.rect(mm_to_pt(x_mm), mm_to_pt(box_bottom_y_mm), mm_to_pt(w_mm), mm_to_pt(h_mm), stroke=1, fill=1)
    return box_bottom_y_mm

def draw_left_text(c: canvas.Canvas, text: str, x_mm: float, y_baseline_mm: float, bold=False, size=LABEL_FONT):
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(mm_to_pt(x_mm), mm_to_pt(y_baseline_mm), text)

def draw_centered_text_in_box(
    c: canvas.Canvas,
    text: str,
    x_mm: float,
    box_bottom_y_mm: float,
    w_mm: float,
    h_mm: float,
    font_size: int = BOX_FONT,
):
    text = "" if text is None else str(text)
    c.setFillColor(TEXT)
    c.setFont("Helvetica", font_size)

    text_w_pt = stringWidth(text, "Helvetica", font_size)
    x_pt = mm_to_pt(x_mm) + (mm_to_pt(w_mm) - text_w_pt) / 2.0

    y_base_mm = centered_baseline_y_mm(box_bottom_y_mm, h_mm, font_size)
    c.drawString(x_pt, mm_to_pt(y_base_mm), text)

def draw_unit_with_constraints(
    c: canvas.Canvas,
    unit_text: str,
    box_x_mm: float,
    box_w_mm: float,
    box_bottom_y_mm: float,
    box_h_mm: float,
    gap_mm: float = 1.0,
    min_border_gap_mm: float = 1.0,
):
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", UNIT_FONT)

    y_base_mm = centered_baseline_y_mm(box_bottom_y_mm, box_h_mm, UNIT_FONT)

    desired_x_mm = box_x_mm + box_w_mm + gap_mm

    unit_w_pt = stringWidth(unit_text, "Helvetica-Bold", UNIT_FONT)
    unit_w_mm = pt_to_mm(unit_w_pt)

    right_inner_border_mm = PLATE_W_MM - BORDER_MARGIN_MM
    max_x_mm = right_inner_border_mm - min_border_gap_mm - unit_w_mm

    x_mm = min(desired_x_mm, max_x_mm)
    c.drawString(mm_to_pt(x_mm), mm_to_pt(y_base_mm), unit_text)

def make_nameplate_pdf(data: dict, output_path: str = "nameplate.pdf") -> str:
    c = canvas.Canvas(output_path, pagesize=(PLATE_W, PLATE_H))

    customer_title = str(data.get("customer_name", "") or "").strip()
    if customer_title:
        c.setTitle(customer_title)
    else:
        c.setTitle("Nameplate")

    # BORDER
    c.setStrokeColor(STROKE)
    c.setLineWidth(2)
    c.rect(
        mm_to_pt(BORDER_MARGIN_MM),
        mm_to_pt(BORDER_MARGIN_MM),
        mm_to_pt(PLATE_W_MM - 2 * BORDER_MARGIN_MM),
        mm_to_pt(PLATE_H_MM - 2 * BORDER_MARGIN_MM),
        stroke=1,
        fill=0,
    )

    # HEADER
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", HEADER_MAIN_FONT)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(PLATE_H_MM - 10), "FAN")

    c.setFont("Helvetica-Bold", HEADER_TITLE_FONT)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(PLATE_H_MM - 17), "MOVEMENT")

    c.setFont("Helvetica-Bold", HEADER_TAGLINE_FONT)
    c.drawCentredString(
        mm_to_pt(PLATE_W_MM / 2),
        mm_to_pt(PLATE_H_MM - 22),
        "AIR AND GAS MOVEMENT SOLUTIONS",
    )

    # SECTION TITLE
    c.setFont("Helvetica-Bold", 12)
    c.drawString(mm_to_pt(LABEL_LEFT_X_MM), mm_to_pt(PLATE_H_MM - 30), "FAN DATA")

    # ROW 0
    top = row_box_top_y_mm(0)

    # Left: Series
    yb = draw_box(c, SERIES_X_MM, top, SERIES_W_MM, BOX_H_MM)
    draw_left_text(c, "Series:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("series", ""), SERIES_X_MM, yb, SERIES_W_MM, BOX_H_MM)

    # Right: Size
    yb_r = draw_box(c, SIZE_X_MM, top, SIZE_W_MM, BOX_H_MM)
    draw_left_text(
        c,
        "Size:",
        RIGHT_LABEL_X_MM,
        centered_baseline_y_mm(yb_r, BOX_H_MM, LABEL_FONT),
        bold=True,
    )
    draw_centered_text_in_box(c, data.get("size", ""), SIZE_X_MM, yb_r, SIZE_W_MM, BOX_H_MM)

    # ROW 1
    top = row_box_top_y_mm(1)

    # Left: Class / Pitch
    yb = draw_box(c, LEFT_STD_X_MM, top, LEFT_STD_W_MM, BOX_H_MM)
    base_label_y = centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Class /", LEFT_LABEL_X_MM, base_label_y + 1.3, bold=True, size=7)
    draw_left_text(c, "Pitch:", LEFT_LABEL_X_MM, base_label_y - 1.3, bold=True, size=7)
    draw_centered_text_in_box(c, data.get("class_pitch", ""), LEFT_STD_X_MM, yb, LEFT_STD_W_MM, BOX_H_MM)

    # Right: Op. Speed
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Op. Speed:", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("op_speed", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "RPM", RIGHT_STD_X_MM, RIGHT_STD_W_MM, yb, BOX_H_MM)

    # ROW 2
    top = row_box_top_y_mm(2)

    # Left: Motor kW
    yb = draw_box(c, LEFT_STD_X_MM, top, LEFT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Motor:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("motor", ""), LEFT_STD_X_MM, yb, LEFT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "kW", LEFT_STD_X_MM, LEFT_STD_W_MM, yb, BOX_H_MM)

    # Right: Max Speed
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Max Speed:", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("max_speed", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "RPM", RIGHT_STD_X_MM, RIGHT_STD_W_MM, yb, BOX_H_MM)

    # ROW 3
    top = row_box_top_y_mm(3)

    # Left: Voltage
    yb = draw_box(c, LEFT_STD_X_MM, top, LEFT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Voltage:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("voltage", ""), LEFT_STD_X_MM, yb, LEFT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "V", LEFT_STD_X_MM, LEFT_STD_W_MM, yb, BOX_H_MM)

    # Right: Phase
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Phase:", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("phase", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM)

    # ROW 4
    top = row_box_top_y_mm(4)

    # Left: FLA
    yb = draw_box(c, LEFT_STD_X_MM, top, LEFT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "F.L.A:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("fla", ""), LEFT_STD_X_MM, yb, LEFT_STD_W_MM, BOX_H_MM)

    # Right: Frequency
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(
        c,
        "Frequency:",
        RIGHT_LABEL_X_MM,
        centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT),
        bold=True,
    )
    draw_centered_text_in_box(c, data.get("frequency", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "Hz", RIGHT_STD_X_MM, RIGHT_STD_W_MM, yb, BOX_H_MM)

    # ROW 5
    top = row_box_top_y_mm(5)

    # Left: Op Temp
    yb = draw_box(c, LEFT_SMALL_X_MM, top, LEFT_SMALL_W_MM, BOX_H_MM)
    draw_left_text(c, "Op Temp:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("op_temp", ""), LEFT_SMALL_X_MM, yb, LEFT_SMALL_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "°C", LEFT_SMALL_X_MM, LEFT_SMALL_W_MM, yb, BOX_H_MM)

    # Right: Connection
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Conn:", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("connection", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM)

    # ROW 6
    top = row_box_top_y_mm(6)

    # Left: Serial No
    yb = draw_box(c, LEFT_SMALL_X_MM, top, LEFT_SMALL_W_MM, BOX_H_MM)
    draw_left_text(c, "Serial No:", LEFT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True)
    draw_centered_text_in_box(c, data.get("serial_no", ""), LEFT_SMALL_X_MM, yb, LEFT_SMALL_W_MM, BOX_H_MM)

    # Right: Date of Manuf.
    yb = draw_box(c, RIGHT_STD_X_MM, top, RIGHT_STD_W_MM, BOX_H_MM)
    draw_left_text(c, "Date of", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT), bold=True, size=7)
    draw_left_text(c, "Manuf.:", RIGHT_LABEL_X_MM, centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT) - 2.7, bold=True, size=7)
    draw_centered_text_in_box(c, data.get("date_of_manuf", ""), RIGHT_STD_X_MM, yb, RIGHT_STD_W_MM, BOX_H_MM, font_size=7)

    # Bottom: Relube Interval
    # Moved up by one row (ROW_PITCH_MM = 6.5mm)
    relube_top = BORDER_MARGIN_MM + 9.0 + ROW_PITCH_MM
    relube_box_top = relube_top + BOX_H_MM
    yb = draw_box(c, RELUBE_X_MM, relube_box_top, RELUBE_W_MM, BOX_H_MM)
    draw_left_text(
        c,
        "Re-Lubrication Interval:",
        LABEL_LEFT_X_MM,
        centered_baseline_y_mm(yb, BOX_H_MM, LABEL_FONT),
        bold=True,
        size=7,
    )
    draw_centered_text_in_box(c, data.get("relube_interval", "N/A"), RELUBE_X_MM, yb, RELUBE_W_MM, BOX_H_MM, font_size=7)

    # Footer - Moved up by 6.5mm
    footer_shift = ROW_PITCH_MM
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(10 + footer_shift), "FAN MOVEMENT 011 682 3020")
    c.setFont("Helvetica", 7)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(7 + footer_shift), "www.fanmovement.co.za")
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(4.5 + footer_shift), "info@fanmovement.co.za")

    c.showPage()
    c.save()
    return output_path

# ============================================================
# TEST RECORD SHEET PDF
# ============================================================
def _draw_label_value(
    c: canvas.Canvas,
    x_mm: float,
    y_mm: float,
    label: str,
    value: str,
    label_size: int = 10,
    value_size: int = 10,
    value_bold: bool = False,
):
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", label_size)
    c.drawString(mm_to_pt(x_mm), mm_to_pt(y_mm), label)

    c.setFont("Helvetica-Bold" if value_bold else "Helvetica", value_size)
    c.drawString(mm_to_pt(x_mm + 35), mm_to_pt(y_mm), "" if value is None else str(value))

def _draw_boxed_value(
    c: canvas.Canvas,
    x_mm: float,
    y_mm: float,
    w_mm: float,
    h_mm: float,
    text: str,
    font_size: int = 10,
):
    c.setStrokeColor(STROKE)
    c.setLineWidth(1)
    c.setFillColor(colors.white)
    c.rect(mm_to_pt(x_mm), mm_to_pt(y_mm - h_mm + 1.2), mm_to_pt(w_mm), mm_to_pt(h_mm), stroke=1, fill=0)

    c.setFillColor(TEXT)
    c.setFont("Helvetica", font_size)
    c.drawString(mm_to_pt(x_mm + 2), mm_to_pt(y_mm - h_mm / 2), "" if text is None else str(text))

def make_test_record_sheet_pdf(data: dict, output_path: str = "test_record_sheet.pdf") -> str:
    """
    Generates the Test Record Sheet PDF (QC-FR-01).
    Prints values as provided (no inference). Required-field enforcement in API layer.
    """
    # A4 portrait
    PAGE_W_MM = 210.0
    PAGE_H_MM = 297.0
    c = canvas.Canvas(output_path, pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))

    margin = 15.0
    x0 = margin
    y = PAGE_H_MM - margin

    # Header
    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), "FAN MOVEMENT")

    y -= 12
    c.setFont("Helvetica-Bold", 12)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), "Title:  Test Record Sheet")

    # Right side identifiers
    c.setFont("Helvetica", 10)
    c.drawRightString(mm_to_pt(PAGE_W_MM - margin), mm_to_pt(PAGE_H_MM - margin), "QC-FR-01")
    c.drawRightString(mm_to_pt(PAGE_W_MM - margin), mm_to_pt(PAGE_H_MM - margin - 6), "Issue. 1")

    y -= 14
    c.setFont("Helvetica-Bold", 10)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), f"DATE: {data.get('date', '')}")

    y -= 14

    # Left header block (as form)
    c.setFont("Helvetica-Bold", 10)
    _draw_label_value(c, x0, y, "Contract No.", data.get("contract_no", ""), value_bold=True)
    y -= 10
    _draw_label_value(c, x0, y, "Fan Size", data.get("fan_size", ""), value_bold=True)
    y -= 10
    _draw_label_value(c, x0, y, "Imp. Form", data.get("imp_form", ""))
    y -= 10
    _draw_label_value(c, x0, y, "Fan Series", data.get("fan_series", ""), value_bold=True)

    # Right header block
    y_right = PAGE_H_MM - margin - 38
    xr = 110
    _draw_label_value(c, xr, y_right, "Customer Name:", data.get("customer_name", ""), value_bold=True)
    y_right -= 10
    _draw_label_value(c, xr, y_right, "Motor Current:", data.get("motor_current", ""))
    c.setFont("Helvetica", 10)
    c.drawString(mm_to_pt(xr + 35 + 35), mm_to_pt(y_right), "Amp")
    y_right -= 10

    # ✅ Insert "Make" (required, user defined)
    _draw_label_value(c, xr, y_right, "Make:", data.get("make", ""), value_bold=True)
    y_right -= 10

    _draw_label_value(c, xr, y_right, "Specification / Procedure Used", data.get("procedure_used", ""))
    y_right -= 10
    _draw_label_value(c, xr, y_right, "Motor Voltage:", data.get("motor_voltage", ""))
    c.setFont("Helvetica", 10)
    c.drawString(mm_to_pt(xr + 35 + 35), mm_to_pt(y_right), "Volt")
    y_right -= 10
    _draw_label_value(c, xr, y_right, "Fan Speed:", data.get("fan_speed", ""))
    c.setFont("Helvetica", 10)
    c.drawString(mm_to_pt(xr + 35 + 35), mm_to_pt(y_right), "r/min")

    # Move y to below both columns
    y = min(y, y_right) - 14

    # ACTUAL VALUES title
    c.setFont("Helvetica-Bold", 11)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), "ACTUAL VALUES")
    y -= 10

    # Extra fields above the table
    c.setFont("Helvetica-Bold", 10)
    _draw_label_value(c, x0, y, "Motor Serial Number:", data.get("motor_serial_number", ""))
    y -= 10
    _draw_label_value(c, x0, y, "Blade Pitch Deg.", data.get("blade_pitch_deg", ""))
    y -= 10
    _draw_label_value(c, x0, y, "Tacho & Clamp Meter Serial No", data.get("tacho_clamp_serial_no", ""))
    y -= 10

    # Table layout
    table_x = x0
    table_w = PAGE_W_MM - 2 * margin
    row_h = 10.0

    col_speed = 28.0
    col_current = 55.0
    col_voltage = 55.0
    col_conn = table_w - (col_speed + col_current + col_voltage)

    def cell(x_mm: float, y_top_mm: float, w_mm: float, h_mm: float, txt: str, bold=False, center=False):
        c.setStrokeColor(STROKE)
        c.setLineWidth(1)
        c.rect(mm_to_pt(x_mm), mm_to_pt(y_top_mm - h_mm), mm_to_pt(w_mm), mm_to_pt(h_mm), stroke=1, fill=0)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 9)
        s = "" if txt is None else str(txt)
        if center:
            c.drawCentredString(mm_to_pt(x_mm + w_mm / 2), mm_to_pt(y_top_mm - h_mm * 0.7), s)
        else:
            c.drawString(mm_to_pt(x_mm + 2), mm_to_pt(y_top_mm - h_mm * 0.7), s)

    # Header row 1
    y_top = y
    cell(table_x, y_top, col_speed, row_h, "Speed", bold=True, center=True)
    cell(table_x + col_speed, y_top, col_current, row_h, "Current", bold=True, center=True)
    cell(table_x + col_speed + col_current, y_top, col_voltage, row_h, "Voltage", bold=True, center=True)
    cell(table_x + col_speed + col_current + col_voltage, y_top, col_conn, row_h, "Connection", bold=True, center=True)

    # Header row 2
    y_top -= row_h
    cell(table_x, y_top, col_speed, row_h, "r/min", bold=True, center=True)

    sub_w = col_current / 3.0
    cell(table_x + col_speed, y_top, sub_w, row_h, "PH1", bold=True, center=True)
    cell(table_x + col_speed + sub_w, y_top, sub_w, row_h, "PH2", bold=True, center=True)
    cell(table_x + col_speed + sub_w * 2, y_top, sub_w, row_h, "PH3", bold=True, center=True)

    sub_vw = col_voltage / 3.0
    cell(table_x + col_speed + col_current, y_top, sub_vw, row_h, "PH1", bold=True, center=True)
    cell(table_x + col_speed + col_current + sub_vw, y_top, sub_vw, row_h, "PH2", bold=True, center=True)
    cell(table_x + col_speed + col_current + sub_vw * 2, y_top, sub_vw, row_h, "PH3", bold=True, center=True)

    cell(table_x + col_speed + col_current + col_voltage, y_top, col_conn, row_h, "", center=True)

    # Data row
    y_top -= row_h
    speed_actual = data.get("speed_actual", "") or data.get("fan_speed", "")
    cell(table_x, y_top, col_speed, row_h, speed_actual, center=True)

    cell(table_x + col_speed, y_top, sub_w, row_h, data.get("current_ph1", ""), center=True)
    cell(table_x + col_speed + sub_w, y_top, sub_w, row_h, data.get("current_ph2", ""), center=True)
    cell(table_x + col_speed + sub_w * 2, y_top, sub_w, row_h, data.get("current_ph3", ""), center=True)

    cell(table_x + col_speed + col_current, y_top, sub_vw, row_h, data.get("voltage_ph1", ""), center=True)
    cell(table_x + col_speed + col_current + sub_vw, y_top, sub_vw, row_h, data.get("voltage_ph2", ""), center=True)
    cell(table_x + col_speed + col_current + sub_vw * 2, y_top, sub_vw, row_h, data.get("voltage_ph3", ""), center=True)

    cell(
        table_x + col_speed + col_current + col_voltage,
        y_top,
        col_conn,
        row_h,
        data.get("connection", ""),
        center=True,
        bold=True,
    )

    # Signatures
    y = y_top - 18
    c.setFont("Helvetica-Bold", 10)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), "Testing Operator Signature:")
    c.drawString(mm_to_pt(x0 + 95), mm_to_pt(y), "Quality Inspector Signature:")

    y -= 14
    c.setFont("Helvetica", 9)
    c.drawString(
        mm_to_pt(x0),
        mm_to_pt(y),
        "Remarks:  Operator and Quality to sign on completion of work, with date competed.",
    )

    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(mm_to_pt(x0), mm_to_pt(y), "CONTROLLED COPY")

    c.showPage()
    c.save()
    return output_path

from io import BytesIO
def make_test_record_sheet_pdf_template(data: dict, output_path: str, template_path: str) -> str:
    PAGE_W_MM = 210.0
    PAGE_H_MM = 297.0
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W_MM * mm, PAGE_H_MM * mm))
    c.setFillColor(TEXT)
    c.setFont("Helvetica", 10)

    coords = {
        # Header block (mirrors geometry of make_test_record_sheet_pdf)
        "date": (20.0, 268.0),
        # Left header values (Contract / Fan Size / Imp. Form / Fan Series)
        "contract_no": (50.0, 242.0),
        "fan_size": (50.0, 232.0),
        "imp_form": (50.0, 222.0),
        "fan_series": (50.0, 212.0),
        # Right header values (Customer / Motor Current / Make / Proc. / Voltage / Fan Speed)
        "customer_name": (145.0, 244.0),
        "motor_current": (145.0, 234.0),
        "make": (145.0, 224.0),
        "procedure_used": (145.0, 214.0),
        "motor_voltage": (145.0, 204.0),
        "fan_speed": (145.0, 194.0),
        # Pre-table fields above ACTUAL VALUES (left side column)
        "motor_serial_number": (50.0, 170.0),
        "blade_pitch_deg": (50.0, 160.0),
        "tacho_clamp_serial_no": (50.0, 150.0),
        # ACTUAL VALUES data row (Speed / Current / Voltage / Connection)
        "speed_actual": (29.0, 113.0),
        "current_ph1": (52.0, 113.0),
        "current_ph2": (70.5, 113.0),
        "current_ph3": (88.8, 113.0),
        "voltage_ph1": (107.2, 113.0),
        "voltage_ph2": (125.5, 113.0),
        "voltage_ph3": (143.8, 113.0),
        "connection": (217.5, 113.0),
    }

    def _draw_key(k: str, val: str, size=10):
        x_mm, y_mm = coords[k]
        c.setFont("Helvetica-Bold", size if k in ("contract_no", "fan_series", "customer_name") else size)
        c.drawString(mm_to_pt(x_mm), mm_to_pt(y_mm), "" if val is None else str(val))

    _draw_key("date", data.get("date", ""))
    _draw_key("contract_no", data.get("contract_no", ""))
    _draw_key("fan_size", data.get("fan_size", ""))
    _draw_key("imp_form", data.get("imp_form", ""))
    _draw_key("fan_series", data.get("fan_series", ""))
    _draw_key("customer_name", data.get("customer_name", ""))
    _draw_key("motor_current", data.get("motor_current", ""))
    _draw_key("make", data.get("make", ""))
    _draw_key("procedure_used", data.get("procedure_used", ""))
    _draw_key("motor_voltage", data.get("motor_voltage", ""))
    _draw_key("fan_speed", data.get("fan_speed", ""))
    _draw_key("motor_serial_number", data.get("motor_serial_number", ""))
    _draw_key("blade_pitch_deg", data.get("blade_pitch_deg", ""))
    _draw_key("tacho_clamp_serial_no", data.get("tacho_clamp_serial_no", ""))

    speed_actual = data.get("speed_actual", "") or data.get("fan_speed", "")
    _draw_key("speed_actual", speed_actual)
    _draw_key("current_ph1", data.get("current_ph1", ""))
    _draw_key("current_ph2", data.get("current_ph2", ""))
    _draw_key("current_ph3", data.get("current_ph3", ""))
    _draw_key("voltage_ph1", data.get("voltage_ph1", ""))
    _draw_key("voltage_ph2", data.get("voltage_ph2", ""))
    _draw_key("voltage_ph3", data.get("voltage_ph3", ""))
    _draw_key("connection", data.get("connection", ""))

    c.showPage()
    c.save()
    overlay_bytes = buf.getvalue()

    from pypdf import PdfReader, PdfWriter
    tpl_pdf = PdfReader(template_path)
    overlay_pdf = PdfReader(BytesIO(overlay_bytes))
    page = tpl_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path
