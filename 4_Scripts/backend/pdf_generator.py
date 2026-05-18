from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from pdf_generator_backup import make_nameplate_pdf


# ============================================================
# Authoritative paths
# ============================================================
PROJECT_ROOT  = Path(__file__).resolve().parents[2]
BACKEND_DIR   = Path(__file__).resolve().parent
TEMPLATES_DIR = PROJECT_ROOT / "2_Source_Data" / "raw_sources"
MAPPINGS_DIR  = BACKEND_DIR / "mappings"
OUTPUT_DIR_DEFAULT = PROJECT_ROOT / "3_Live_Reports" / "output"

TEST_RECORD_MAPPING = MAPPINGS_DIR / "test_record_sheet.json"


# ============================================================
# Helpers
# ============================================================
def _fmt_date(dt_or_str):
    """Return DD/MM/YYYY string from a date object or string."""
    if isinstance(dt_or_str, date):
        return dt_or_str.strftime("%d/%m/%Y")
    s = str(dt_or_str).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return s


# ============================================================
# Direct Test Sheet Renderer — builds from scratch
# ============================================================
def _render_test_sheet_direct(data: Dict[str, Any], output_path: Path) -> None:
    """
    Build a complete test sheet PDF from scratch using ReportLab.
    Replicates the original controlled document layout exactly.
    """
    np_data = data.get("nameplate", {})
    dr      = data.get("derived",   {})

    # ── Page setup ──────────────────────────────────────────────────────────
    PAGE_W, PAGE_H = 612.0, 792.0   # Letter
    LM = 30.0                        # left  margin
    RM = 30.0                        # right margin
    CW = PAGE_W - LM - RM           # content width = 552

    BLACK = (0, 0, 0)
    GREY  = (0.85, 0.85, 0.85)

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))

    # ── Drawing helpers ──────────────────────────────────────────────────────
    def hline(y, x1=LM, x2=PAGE_W - RM, lw=0.75):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(lw)
        c.line(x1, y, x2, y)

    def box(x, y_bot, w, h, fill=None, lw=0.5):
        """Draw bordered rectangle. y_bot = bottom edge of the cell."""
        c.setLineWidth(lw)
        c.setStrokeColorRGB(0, 0, 0)
        if fill:
            c.saveState()
            c.setFillColorRGB(*fill)
            c.rect(x, y_bot, w, h, fill=1, stroke=1)
            c.restoreState()
        else:
            c.rect(x, y_bot, w, h, fill=0, stroke=1)

    def txt(x, y, s, font="Helvetica", size=9, align="left"):
        c.setFont(font, size)
        c.setFillColorRGB(0, 0, 0)
        s = str(s) if s is not None else ""
        if align == "center":
            c.drawCentredString(x, y, s)
        elif align == "right":
            c.drawRightString(x, y, s)
        else:
            c.drawString(x, y, s)

    # ── Data values ──────────────────────────────────────────────────────────
    date_str    = _fmt_date(dr.get("date") or date.today())
    serial_no   = str(np_data.get("serial_no",      "") or "")
    series      = str(np_data.get("series",          "") or "").upper()
    size        = str(np_data.get("size",            "") or "")
    imp_form    = str(dr.get("imp_form",             "") or "")
    cust_name   = str(np_data.get("customer_name",   "") or "")
    fla         = str(np_data.get("fla",             "") or "")
    voltage     = str(np_data.get("voltage",         "") or "")
    op_speed    = str(np_data.get("op_speed",        "") or "")
    blade_pitch = str(np_data.get("class_pitch",     "") or "")
    connection  = str(dr.get("connection",           "") or "")
    motor_desc  = str(dr.get("motor_description",    "") or "")
    make_val    = str(np_data.get("manufacturer",    "") or "").upper()

    # ── y cursor — starts at the top of the content area ────────────────────
    y = PAGE_H - LM

    # ── TOP BORDER ───────────────────────────────────────────────────────────
    hline(y, lw=1.0)

    # ── LOGO ─────────────────────────────────────────────────────────────────
    logo_path = TEMPLATES_DIR / "FM - LOGO.jpg"
    LOGO_H, LOGO_W = 54, 158
    logo_y = y - LOGO_H - 5
    if logo_path.exists():
        try:
            c.drawImage(
                str(logo_path),
                (PAGE_W - LOGO_W) / 2, logo_y,
                width=LOGO_W, height=LOGO_H,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass
    y = logo_y - 6

    # ── ROW 1 — "Test Record Sheet" | DATE ───────────────────────────────────
    R1H = 18
    box(LM, y - R1H, CW, R1H, lw=0.75)
    txt(LM + 4,          y - R1H + 5, "Test Record Sheet", "Helvetica-Bold", 11)
    txt(PAGE_W - RM - 4, y - R1H + 5, f"DATE:   {date_str}", "Helvetica", 9, "right")
    y -= R1H

    # ── ROW 2 — Contract No. | Fan Series | Fan Size | Imp. Form ─────────────
    R2H = 30
    # Column widths — must sum to CW = 552
    W_CN, W_FS, W_SZ = 84, 184, 142
    W_IF = CW - W_CN - W_FS - W_SZ   # = 142

    for cx, cw, lbl, val in [
        (LM,                       W_CN, "Contract No.", serial_no),
        (LM + W_CN,                W_FS, "Fan Series",   series),
        (LM + W_CN + W_FS,         W_SZ, "Fan Size",     size),
        (LM + W_CN + W_FS + W_SZ,  W_IF, "Imp. Form",    imp_form),
    ]:
        box(cx, y - R2H, cw, R2H)
        txt(cx + 4, y - 9, lbl, "Helvetica-Bold", 7)
        fs = 7 if len(val) > 14 else 9
        txt(cx + cw / 2, y - R2H + 9, val, "Helvetica-Bold", fs, "center")
    y -= R2H

    # ── ROW 3 — Customer Name ────────────────────────────────────────────────
    R3H = 20
    box(LM, y - R3H, CW, R3H)
    txt(LM + 4,   y - R3H + 12, "Customer Name:", "Helvetica-Bold", 8)
    txt(LM + 100, y - R3H + 7,  cust_name,        "Helvetica-Bold", 9)
    y -= R3H

    # ── ROW 4 — Motor Current + MAKE ─────────────────────────────────────────
    R4H = 20
    box(LM, y - R4H, CW, R4H)
    txt(LM + 4, y - R4H + 7, "Motor Current:", "Helvetica-Bold", 8)
    VB_X, VB_W = LM + 88, 50
    box(VB_X, y - R4H + 3, VB_W, R4H - 6)
    txt(VB_X + VB_W / 2, y - R4H + 7, fla, "Helvetica", 9, "center")
    txt(VB_X + VB_W + 4, y - R4H + 7, "Amp", "Helvetica-Bold", 8)
    # MAKE boxes
    txt(PAGE_W - RM - 232, y - R4H + 7, "MAKE:", "Helvetica-Bold", 8)
    MK_W, mk_x = 52, PAGE_W - RM - 180
    for mk in ["ACTOM", "ASKARI", "WEG"]:
        box(mk_x, y - R4H + 3, MK_W, R4H - 6,
            fill=GREY if mk == make_val else None)
        txt(mk_x + MK_W / 2, y - R4H + 7, mk, "Helvetica", 8, "center")
        mk_x += MK_W + 2
    y -= R4H

    # ── ROW 5 — Motor Voltage + Description ──────────────────────────────────
    R5H = 20
    box(LM, y - R5H, CW, R5H)
    txt(LM + 4, y - R5H + 7, "Motor Voltage:", "Helvetica-Bold", 8)
    box(VB_X, y - R5H + 3, VB_W, R5H - 6)
    txt(VB_X + VB_W / 2, y - R5H + 7, voltage, "Helvetica", 9, "center")
    txt(VB_X + VB_W + 4, y - R5H + 7, "Volt", "Helvetica-Bold", 8)
    txt(PAGE_W - RM - 232, y - R5H + 7, "Description:", "Helvetica-Bold", 8)
    DS_X = PAGE_W - RM - 168
    DS_W = PAGE_W - RM - DS_X
    box(DS_X, y - R5H + 3, DS_W, R5H - 6)
    txt(DS_X + DS_W / 2, y - R5H + 7, motor_desc, "Helvetica", 8, "center")
    y -= R5H

    # ── ROW 6 — Fan Speed ────────────────────────────────────────────────────
    R6H = 20
    box(LM, y - R6H, CW, R6H)
    txt(LM + 4, y - R6H + 7, "Fan Speed:", "Helvetica-Bold", 8)
    box(VB_X, y - R6H + 3, VB_W, R6H - 6)
    txt(VB_X + VB_W / 2, y - R6H + 7, op_speed, "Helvetica", 9, "center")
    txt(VB_X + VB_W + 4, y - R6H + 7, "r/min", "Helvetica-Bold", 8)
    y -= R6H + 5

    # ── ACTUAL VALUES label ───────────────────────────────────────────────────
    txt(LM, y - 10, "ACTUAL VALUES", "Helvetica-Bold", 9)
    y -= 16

    # ── ACTUAL VALUES TABLE ───────────────────────────────────────────────────
    # 11 columns — widths must sum to CW = 552
    # [Motor Serial No, Blade Pitch, Tacho&Clamp, Speed,
    #  PH1 PH2 PH3 (Current), PH1 PH2 PH3 (Voltage), Connection]
    TCW = [96, 50, 62, 50, 38, 38, 38, 38, 38, 38, 66]
    # Verify: 96+50+62+50 + (38*6) + 66 = 258 + 228 + 66 = 552 ✓

    col_xs = []
    cx = LM
    for w in TCW:
        col_xs.append(cx)
        cx += w

    # Sub-header band — "Current" over cols 4-6, "Voltage" over cols 7-9
    SB_H = 10
    cur_x1, cur_x2 = col_xs[4], col_xs[6] + TCW[6]
    vol_x1, vol_x2 = col_xs[7], col_xs[9] + TCW[9]

    box(cur_x1, y - SB_H, cur_x2 - cur_x1, SB_H, fill=GREY)
    txt((cur_x1 + cur_x2) / 2, y - SB_H + 3,
        "Current", "Helvetica-Bold", 6, "center")
    box(vol_x1, y - SB_H, vol_x2 - vol_x1, SB_H, fill=GREY)
    txt((vol_x1 + vol_x2) / 2, y - SB_H + 3,
        "Voltage", "Helvetica-Bold", 6, "center")
    y -= SB_H

    # Header row — multi-line column labels
    HDR_H = 28
    HDR_LABELS = [
        ["Motor Serial", "Number"],
        ["Blade Pitch", "Deg."],
        ["Tacho &", "Clamp Meter", "Serial No"],
        ["Speed", "r/min"],
        ["PH1"], ["PH2"], ["PH3"],
        ["PH1"], ["PH2"], ["PH3"],
        ["Connection"],
    ]
    for i, (cx, cw) in enumerate(zip(col_xs, TCW)):
        box(cx, y - HDR_H, cw, HDR_H, fill=GREY)
        lines = HDR_LABELS[i]
        n = len(lines)
        block_h = n * 8
        start_y = y - HDR_H + (HDR_H - block_h) / 2 + block_h - 5
        for li, line in enumerate(lines):
            txt(cx + cw / 2, start_y - li * 8,
                line, "Helvetica-Bold", 6, "center")
    y -= HDR_H

    # First data row — auto-populated; Current PH columns left blank
    DRH = 14
    row1 = [
        "",           # Motor Serial Number  — filled in manually
        blade_pitch,  # Blade Pitch Deg.
        "N/A",        # Tacho & Clamp Meter Serial No
        op_speed,     # Speed r/min
        "",           # Current PH1 — blank (measured during physical testing)
        "",           # Current PH2 — blank
        "",           # Current PH3 — blank
        voltage,      # Voltage PH1
        voltage,      # Voltage PH2
        voltage,      # Voltage PH3
        connection,   # Connection
    ]
    for i, (cx, cw) in enumerate(zip(col_xs, TCW)):
        box(cx, y - DRH, cw, DRH)
        txt(cx + cw / 2, y - DRH + 4, row1[i], "Helvetica", 7, "center")
    y -= DRH

    # 19 additional blank rows
    for _ in range(19):
        for cx, cw in zip(col_xs, TCW):
            box(cx, y - DRH, cw, DRH)
        y -= DRH

    y -= 6

    # ── SIGNATURE ROW ─────────────────────────────────────────────────────────
    SIG_H = 24
    half = CW / 2
    box(LM,        y - SIG_H, half, SIG_H)
    box(LM + half, y - SIG_H, half, SIG_H)
    txt(LM + 4,        y - SIG_H + 8,
        "Testing Operator Signature:",  "Helvetica-Bold", 8)
    txt(LM + half + 4, y - SIG_H + 8,
        "Quality Inspector Signature:", "Helvetica-Bold", 8)
    y -= SIG_H

    # ── REMARKS ROW ───────────────────────────────────────────────────────────
    REM_H = 24
    box(LM, y - REM_H, CW, REM_H)
    txt(LM + 4, y - REM_H + 8,
        "Remarks:  Operator and Quality to sign on completion of work, "
        "with date completed.",
        "Helvetica", 8)
    y -= REM_H

    # ── BOTTOM BORDER ─────────────────────────────────────────────────────────
    hline(y, lw=1.0)

    c.showPage()
    c.save()


# ============================================================
# Mapping-driven coordinate overlay renderer — kept for reference
# ============================================================
@dataclass(frozen=True)
class MappingItem:
    key:       str
    x:         float
    y:         float
    source:    str
    required:  bool                   = False
    value:     Optional[str]          = None
    transform: Optional[Dict[str, Any]] = None
    clear:     Optional[Dict[str, Any]] = None
    font:      Optional[Dict[str, Any]] = None
    align:     str                    = "left"
    wrap_width: Optional[float]       = None
    line_height: float                = 10.0


def _get_nested(data: Dict[str, Any], path: str) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _apply_transform(raw: Any, transform: Optional[Dict[str, Any]]) -> str:
    if raw is None:
        return ""
    if transform is None:
        return str(raw)

    t = transform.get("type")

    if t == "upper":
        return str(raw).upper()

    if t == "number":
        try:
            num = float(str(raw).replace(",", "").strip())
        except Exception:
            return str(raw)
        decimals = transform.get("decimals")
        if decimals is not None:
            s = f"{num:.{int(decimals)}f}"
        else:
            s = str(int(num)) if num.is_integer() else str(num)
        prefix = transform.get("prefix", "")
        suffix = transform.get("suffix", "")
        return f"{prefix}{s}{suffix}"

    if t == "date":
        fmt = transform.get("format", "DD/MM/YYYY")
        if isinstance(raw, date):
            d = raw
        else:
            s = str(raw).strip()
            d = None
            for parse_fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    d = datetime.strptime(s, parse_fmt).date()
                    break
                except ValueError:
                    continue
            if d is None:
                return s
        if fmt == "DD/MM/YYYY":
            s = d.strftime("%d/%m/%Y")
        elif fmt == "MONTH YEAR":
            months = ["JAN","FEB","MAR","APR","MAY","JUN",
                      "JUL","AUG","SEP","OCT","NOV","DEC"]
            s = f"{months[d.month - 1]} {d.year}"
        else:
            s = d.isoformat()
        prefix = transform.get("prefix", "")
        suffix = transform.get("suffix", "")
        return f"{prefix}{s}{suffix}"

    if t == "fan_size_primary":
        s = str(raw).strip().replace(" ", "")
        parts = s.split("/")
        return parts[0] if parts else str(raw)

    if t == "motor_make":
        s = str(raw).strip().upper()
        for brand in ("ACTOM", "ASKARI", "WEG"):
            if brand in s:
                return brand
        return s

    return str(raw)


def _resolve_value(item: MappingItem, data: Dict[str, Any]) -> str:
    if item.source == "literal":
        return str(item.value or "")
    if item.source == "derived.report_date":
        return _apply_transform(date.today(), item.transform)
    raw = _get_nested(data, item.source)
    return _apply_transform(raw, item.transform)


# ============================================================
# Public API
# ============================================================
def generate_test_record_sheet(
    payload: Dict[str, Any],
    out_dir: Optional[str] = None,
) -> str:
    """
    Generate a print-ready Test Record Sheet PDF.
    Builds the document from scratch to match the original controlled layout.
    """
    out_base    = Path(out_dir) if out_dir else OUTPUT_DIR_DEFAULT
    output_path = out_base / "TestRecordSheet_filled.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _render_test_sheet_direct(payload, output_path)

    return str(output_path)