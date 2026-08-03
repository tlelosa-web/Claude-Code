from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from pathlib import Path
from datetime import datetime
import io
from pypdf import PdfReader, PdfWriter

# ============================================================
# PLATE SIZE (mm)
# ============================================================
PLATE_W_MM = 105.0
PLATE_H_MM = 104.0

PLATE_W = PLATE_W_MM * mm
PLATE_H = PLATE_H_MM * mm

# ============================================================
# BORDER
# ============================================================
BORDER_MARGIN_MM = 4.0
LABEL_LEFT_X_MM = BORDER_MARGIN_MM + 1.0  # 1mm from border

# ============================================================
# BOX GEOMETRY
# ============================================================
BOX_H_MM = 5.5
BOX_GAP_MM = 1.0
ROW_PITCH_MM = BOX_H_MM + BOX_GAP_MM  # 6.5mm pitch

# Top reference: Series/Size box TOP is 34mm from TOP edge
TOP_BOX_TOP_FROM_TOP_MM = 34.0
ROW0_BOX_TOP_Y_MM = PLATE_H_MM - TOP_BOX_TOP_FROM_TOP_MM

# Fill/stroke/text
BOX_FILL = colors.Color(0.85, 0.85, 0.85)  # light grey
STROKE = colors.black
TEXT = colors.black

# Fonts
LABEL_FONT = 8
BOX_FONT = 8
UNIT_FONT = 7  # slightly smaller to prevent overlap near the border

HEADER_MAIN_FONT = 18
HEADER_SUB_FONT = 12
HEADER_TAGLINE_FONT = 8
HEADER_TITLE_FONT = 14

# ============================================================
# X POSITIONS + WIDTHS (FROM YOUR MEASUREMENTS)
# ============================================================
# Left boxes
SERIES_X_MM = 17.0
SERIES_W_MM = 35.0

LEFT_STD_X_MM = 17.0
LEFT_STD_W_MM = 29.0

LEFT_SMALL_X_MM = 20.0
LEFT_SMALL_W_MM = 24.0

# Right boxes
SIZE_W_MM = 36.5
SIZE_RIGHT_MARGIN_MM = 5.5
SIZE_X_MM = PLATE_W_MM - SIZE_RIGHT_MARGIN_MM - SIZE_W_MM  # 63.0

# Right standard box initial rule: 12mm from right edge (historical baseline)
RIGHT_STD_W_MM = 24.5
RIGHT_STD_RIGHT_MARGIN_MM = 12.0
RIGHT_STD_X_MM = PLATE_W_MM - RIGHT_STD_RIGHT_MARGIN_MM - RIGHT_STD_W_MM  # 68.5

# Reduce these boxes by 4mm from the RIGHT (do not move left edge) -> width 20.5mm
RIGHT_STD_W_MM = RIGHT_STD_W_MM - 4.0  # 20.5

# === LAST ADJUSTMENT: move these boxes 2mm RIGHT to clear overlap ===
# This keeps RPM/Hz spacing (1mm from box edge) unchanged because unit X is computed from box edge.
RIGHT_STD_X_MM = RIGHT_STD_X_MM + 2.0  # now 70.5mm

# Ensure right-side standard boxes do not overlap left-side boxes; enforce a minimum gap
min_gap_mm = 2.0
min_allowed_x = LEFT_STD_X_MM + LEFT_STD_W_MM + min_gap_mm
if RIGHT_STD_X_MM < min_allowed_x:
    RIGHT_STD_X_MM = min_allowed_x

# Relube
RELUBE_X_MM = 38.0
RELUBE_W_MM = 29.0

# Label alignment
RIGHT_LABEL_X_MM = 54.0
LEFT_LABEL_X_MM = LABEL_LEFT_X_MM

# Logo
BACKEND_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BACKEND_DIR.parents[1] / "2_Source_Data" / "raw_sources"
LOGO_PATH = TEMPLATES_DIR / "FM - LOGO.jpg"


# ============================================================
# HELPERS
# ============================================================
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


def draw_centered_text_in_box(c: canvas.Canvas, text: str, x_mm: float, box_bottom_y_mm: float, w_mm: float, h_mm: float, font_size: int = BOX_FONT, wrap: bool = False):
    text = "" if text is None else str(text)
    c.setFillColor(TEXT)
    c.setFont("Helvetica", font_size)

    if wrap:
        # Simple wrap for 2 lines
        words = text.split()
        if len(words) > 1 and stringWidth(text, "Helvetica", font_size) > mm_to_pt(w_mm):
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            
            y_mid_pt = mm_to_pt(box_bottom_y_mm + h_mm / 2.0)
            
            w1 = stringWidth(line1, "Helvetica", font_size)
            c.drawString(mm_to_pt(x_mm) + (mm_to_pt(w_mm) - w1) / 2.0, y_mid_pt + 1, line1)
            
            w2 = stringWidth(line2, "Helvetica", font_size)
            c.drawString(mm_to_pt(x_mm) + (mm_to_pt(w_mm) - w2) / 2.0, y_mid_pt - font_size + 1, line2)
            return

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
    gap_mm: float = 1.0,            # keep 1mm gap from box edge
    min_border_gap_mm: float = 1.0, # keep away from inner border
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


def draw_logo(c: canvas.Canvas, page_w_mm: float, page_h_mm: float):
    """Draw the FM logo centered at the top of the plate."""
    if LOGO_PATH.exists():
        logo_w = min(60, page_w_mm * 0.55)
        logo_h = logo_w * 0.35
        logo_x = (page_w_mm - logo_w) / 2.0
        logo_y = page_h_mm - BORDER_MARGIN_MM - logo_h - 2.0
        try:
            c.drawImage(str(LOGO_PATH), mm_to_pt(logo_x), mm_to_pt(logo_y),
                        width=mm_to_pt(logo_w), height=mm_to_pt(logo_h),
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass


# ============================================================
# MAIN PDF
# ============================================================
def make_nameplate_pdf(data: dict, output_path: str = "nameplate.pdf") -> str:
    c = canvas.Canvas(output_path, pagesize=(PLATE_W, PLATE_H))

    # BORDER
    c.setStrokeColor(STROKE)
    c.setLineWidth(2)
    c.rect(
        mm_to_pt(BORDER_MARGIN_MM),
        mm_to_pt(BORDER_MARGIN_MM),
        PLATE_W - mm_to_pt(2 * BORDER_MARGIN_MM),
        PLATE_H - mm_to_pt(2 * BORDER_MARGIN_MM),
        stroke=1,
        fill=0,
    )

    # LOGO (replaces "FAN" / "MOVEMENT" / "AIR AND GAS MOVEMENT SOLUTIONS" text)
    draw_logo(c, PLATE_W_MM, PLATE_H_MM)

    # FAN DATA title
    header_top_y_mm = PLATE_H_MM - (BORDER_MARGIN_MM + 3.0)
    c.setFont("Helvetica-Bold", HEADER_TITLE_FONT)
    c.drawString(mm_to_pt(LEFT_LABEL_X_MM), mm_to_pt(header_top_y_mm - 24.0), "FAN DATA")

    # ROW 0
    y_top = row_box_top_y_mm(0)

    box_bottom = draw_box(c, SERIES_X_MM, y_top, SERIES_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Series:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("series"), SERIES_X_MM, box_bottom, SERIES_W_MM, BOX_H_MM, wrap=True)

    box_bottom = draw_box(c, SIZE_X_MM, y_top, SIZE_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Size:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("size"), SIZE_X_MM, box_bottom, SIZE_W_MM, BOX_H_MM)

    # ROW 1
    y_top = row_box_top_y_mm(1)

    box_bottom = draw_box(c, LEFT_STD_X_MM, y_top, LEFT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Class", LEFT_LABEL_X_MM, y_label_base + 1.6, bold=True, size=LABEL_FONT)
    draw_left_text(c, "Pitch:", LEFT_LABEL_X_MM, y_label_base - 1.6, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("class_pitch"), LEFT_STD_X_MM, box_bottom, LEFT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "°", LEFT_STD_X_MM, LEFT_STD_W_MM, box_bottom, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Op. Speed:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("op_speed"), RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "RPM", RIGHT_STD_X_MM, RIGHT_STD_W_MM, box_bottom, BOX_H_MM)

    # ROW 2
    y_top = row_box_top_y_mm(2)

    box_bottom = draw_box(c, LEFT_STD_X_MM, y_top, LEFT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Motor:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("motor"), LEFT_STD_X_MM, box_bottom, LEFT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "kW", LEFT_STD_X_MM, LEFT_STD_W_MM, box_bottom, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Max Speed:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("max_speed"), RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "RPM", RIGHT_STD_X_MM, RIGHT_STD_W_MM, box_bottom, BOX_H_MM)

    # ROW 3
    y_top = row_box_top_y_mm(3)

    box_bottom = draw_box(c, LEFT_STD_X_MM, y_top, LEFT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Voltage:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("voltage"), LEFT_STD_X_MM, box_bottom, LEFT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "V", LEFT_STD_X_MM, LEFT_STD_W_MM, box_bottom, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Phase:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("phase"), RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)

    # ROW 4
    y_top = row_box_top_y_mm(4)

    box_bottom = draw_box(c, LEFT_STD_X_MM, y_top, LEFT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "F.L.A:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("fla"), LEFT_STD_X_MM, box_bottom, LEFT_STD_W_MM, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Frequency:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("frequency"), RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "Hz", RIGHT_STD_X_MM, RIGHT_STD_W_MM, box_bottom, BOX_H_MM)

    # ROW 5
    y_top = row_box_top_y_mm(5)

    box_bottom = draw_box(c, LEFT_SMALL_X_MM, y_top, LEFT_SMALL_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Op Temp:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("op_temp"), LEFT_SMALL_X_MM, box_bottom, LEFT_SMALL_W_MM, BOX_H_MM)
    draw_unit_with_constraints(c, "°C", LEFT_SMALL_X_MM, LEFT_SMALL_W_MM, box_bottom, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Conn:", RIGHT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("connection"), RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)

    # ROW 6
    y_top = row_box_top_y_mm(6)

    box_bottom = draw_box(c, LEFT_SMALL_X_MM, y_top, LEFT_SMALL_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Serial No:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("serial_no"), LEFT_SMALL_X_MM, box_bottom, LEFT_SMALL_W_MM, BOX_H_MM)

    box_bottom = draw_box(c, RIGHT_STD_X_MM, y_top, RIGHT_STD_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Date of", RIGHT_LABEL_X_MM, y_label_base + 1.6, bold=True, size=LABEL_FONT)
    draw_left_text(c, "Manuf.:", RIGHT_LABEL_X_MM, y_label_base - 1.6, bold=True, size=LABEL_FONT)
    
    # Format Date
    raw_date = data.get("date_of_manuf", "")
    try:
        dt = datetime.strptime(raw_date, "%Y-%m-%d")
        formatted_date = dt.strftime("%b %Y").upper()
    except:
        formatted_date = raw_date

    draw_centered_text_in_box(c, formatted_date, RIGHT_STD_X_MM, box_bottom, RIGHT_STD_W_MM, BOX_H_MM)

    # ROW 7 - proper gap below Row 6
    y_top = row_box_top_y_mm(7)
    relube_box_bottom = draw_box(c, RELUBE_X_MM, y_top, RELUBE_W_MM, BOX_H_MM)
    y_label_base = centered_baseline_y_mm(relube_box_bottom, BOX_H_MM, LABEL_FONT)
    draw_left_text(c, "Re-Lubrication Interval:", LEFT_LABEL_X_MM, y_label_base, bold=True, size=LABEL_FONT)
    draw_centered_text_in_box(c, data.get("relube_interval", "N/A"), RELUBE_X_MM, relube_box_bottom, RELUBE_W_MM, BOX_H_MM)

    # FOOTER (centered) - Shifted UP
    footer_gap_mm = 5.0
    line1_y_mm = relube_box_bottom - footer_gap_mm
    line2_y_mm = line1_y_mm - 3.0
    line3_y_mm = line2_y_mm - 3.0

    c.setFillColor(TEXT)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(line1_y_mm), "FAN MOVEMENT 011 682 3020")

    c.setFont("Helvetica", 8)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(line2_y_mm), "www.fanmovement.co.za")

    c.setFont("Helvetica", 8)
    c.drawCentredString(mm_to_pt(PLATE_W_MM / 2), mm_to_pt(line3_y_mm), "info@fanmovement.co.za")

    c.showPage()
    c.save()
    return output_path


def make_test_nameplate_pdf(output_path="nameplate_layout_final_shift.pdf") -> str:
    sample = {
        "series": "MAXFLO",
        "class_pitch": "34",
        "motor": "2.2",
        "voltage": "380",
        "fla": "4.84",
        "op_temp": "20",
        "serial_no": "FM5107",
        "size": "630",
        "op_speed": "1440",
        "max_speed": "1440",
        "phase": "3",
        "frequency": "50",
        "connection": "STAR",
        "date_of_manuf": "DEC 2025",
        "relube_interval": "N/A",
    }
    return make_nameplate_pdf(sample, output_path)