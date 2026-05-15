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
from pdf_generator_backup import make_nameplate_pdf


# ============================================================
# Authoritative paths (do not hardcode templates elsewhere)
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PROJECT_ROOT / "2_Source_Data" / "raw_sources"
MAPPINGS_DIR = BACKEND_DIR / "mappings"
OUTPUT_DIR_DEFAULT = PROJECT_ROOT / "3_Live_Reports" / "output"

TEST_RECORD_MAPPING = MAPPINGS_DIR / "test_record_sheet.json"

def _resolve_test_record_template() -> Path:
    for env_key in ("TEST_RECORD_TEMPLATE_PATH", "TEST_SHEET_TEMPLATE_PATH", "TEST_RECORD_SHEET_TEMPLATE_PATH"):
        env_val = os.getenv(env_key)
        if env_val:
            p = Path(env_val).expanduser()
            if p.exists():
                return p

    preferred = TEMPLATES_DIR / "Test Sheet Template v4.pdf"
    if preferred.exists():
        return preferred

    preferred = TEMPLATES_DIR / "Test Sheet Template v3.pdf"
    if preferred.exists():
        return preferred

    preferred = TEMPLATES_DIR / "Test Sheet Template v2.pdf"
    if preferred.exists():
        return preferred

    preferred = TEMPLATES_DIR / "Test Sheet Tmp.pdf"
    if preferred.exists():
        return preferred

    direct = TEMPLATES_DIR / "TestRecordSheet.pdf"
    if direct.exists():
        return direct

    if TEMPLATES_DIR.exists():
        candidates = sorted(TEMPLATES_DIR.glob("Test Sheet*.pdf"))
        if candidates:
            return candidates[0]

    raise FileNotFoundError(
        "Test Record Sheet template PDF not found. "
        "Set TEST_RECORD_TEMPLATE_PATH to a valid PDF file."
    )


# ============================================================
# Mapping-driven coordinate overlay renderer (generic)
# ============================================================
@dataclass(frozen=True)
class MappingItem:
    key: str
    x: float
    y: float
    source: str
    required: bool = False
    value: Optional[str] = None
    transform: Optional[Dict[str, Any]] = None
    clear: Optional[Dict[str, Any]] = None
    font: Optional[Dict[str, Any]] = None
    align: str = "left"


def _get_nested(data: Dict[str, Any], path: str) -> Any:
    """
    Resolves dotted-path lookup in a dict.
    Example: "nameplate.serial_no" -> data["nameplate"]["serial_no"]
    """
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
        # robust parse
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
            months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            s = f"{months[d.month - 1]} {d.year}"
        else:
            s = d.isoformat()
        prefix = transform.get("prefix", "")
        suffix = transform.get("suffix", "")
        return f"{prefix}{s}{suffix}"

    if t == "fan_size_primary":
        # "315 / 165 / 6 A" -> "315"
        s = str(raw).strip().replace(" ", "")
        parts = s.split("/")
        return parts[0] if parts else str(raw)

    if t == "motor_make":
        s = str(raw).strip().upper()
        for brand in ("ACTOM", "ASKARI", "WEG"):
            if brand in s:
                return brand
        return s

    # fallback
    return str(raw)


def _resolve_value(item: MappingItem, data: Dict[str, Any]) -> str:
    if item.source == "literal":
        return str(item.value or "")

    if item.source == "derived.report_date":
        # deterministic: generation date (today)
        return _apply_transform(date.today(), item.transform)

    raw = _get_nested(data, item.source)
    return _apply_transform(raw, item.transform)


def render_pdf_from_coordinate_mapping(
    template_path: Path,
    mapping_path: Path,
    data: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Loads a coordinate mapping JSON, draws values at (x,y) on a transparent overlay,
    merges overlay onto the template page, and writes output.

    NOTE: This works even when template has 0 AcroForm fields.
    """
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping not found: {mapping_path}")

    mapping_obj = json.loads(mapping_path.read_text(encoding="utf-8"))

    items = []
    for it in mapping_obj.get("items", []):
        items.append(
            MappingItem(
                key=str(it["key"]),
                x=float(it["x"]),
                y=float(it["y"]),
                source=str(it["source"]),
                required=bool(it.get("required", False)),
                value=it.get("value"),
                transform=it.get("transform"),
                clear=it.get("clear"),
                font=it.get("font"),
                align=str(it.get("align", "left")),
                wrap_width=it.get("wrap_width"),
                line_height=it.get("line_height", 10.0),
            )
        )

    reader = PdfReader(str(template_path))
    page_index = int(mapping_obj.get("page_index", 0))
    base_page = reader.pages[page_index]

    page_w = float(base_page.mediabox.width)
    page_h = float(base_page.mediabox.height)

    # Build overlay PDF in memory
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_w, page_h))

    font = mapping_obj.get("font", {})
    font_name = font.get("name", "Helvetica")
    font_size = float(font.get("size", 9))
    c.setFont(font_name, font_size)

    missing_required = []
    for item in items:
        val = _resolve_value(item, data)
        if item.required and (val is None or str(val).strip() == ""):
            missing_required.append(item.key)
            continue
        if val is None or str(val).strip() == "":
            continue
        if item.clear and item.align == "left":
            w = float(item.clear.get("w", 120))
            h = float(item.clear.get("h", font_size + 4))
            baseline_offset = float(item.clear.get("baseline_offset", 2))
            c.saveState()
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(1, 1, 1)
            c.rect(item.x, item.y - baseline_offset, w, h, fill=1, stroke=0)
            c.restoreState()
        text = str(val)

        def draw_value() -> None:
            lines = [text]
            if item.wrap_width:
                from reportlab.pdfbase.pdfmetrics import stringWidth
                f_name = item.font.get("name", font_name) if item.font else font_name
                f_size = float(item.font.get("size", font_size) if item.font else font_size)
                words = text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = " ".join(current_line + [word])
                    if stringWidth(test_line, f_name, f_size) <= item.wrap_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(" ".join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)
                if current_line:
                    lines.append(" ".join(current_line))

            y = item.y
            if len(lines) > 1:
                # Center vertically over the bounding box
                y += (len(lines) - 1) * item.line_height / 2.0
                
            for line in lines:
                if item.align == "center":
                    c.drawCentredString(item.x, y, line)
                elif item.align == "right":
                    c.drawRightString(item.x, y, line)
                else:
                    c.drawString(item.x, y, line)
                y -= item.line_height

        if item.font:
            c.saveState()
            c.setFont(
                item.font.get("name", font_name),
                float(item.font.get("size", font_size)),
            )
            draw_value()
            c.restoreState()
        else:
            draw_value()

    # Draw LOGO
    logo_path = TEMPLATES_DIR / "FM - LOGO.jpg"
    if logo_path.exists():
        # Position logo at the top. 
        # Coordinates for Test Sheet Template v4.pdf:
        # "FAN MOVEMENT" is around x=PLATE_W/2? No, test sheet is A4 probably.
        # page_w is around 595.
        # Header is usually at the top. 
        logo_w = 60
        logo_h = 60
        # Draw it near the top left or center.
        # Let's try top left of the header area.
        c.drawImage(str(logo_path), 50, page_h - 80, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

    c.save()
    packet.seek(0)

    if missing_required:
        raise ValueError(f"Missing required mapping values: {', '.join(missing_required)}")

    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    # Merge overlay onto template
    out = PdfWriter()
    merged = reader.pages[page_index]
    merged.merge_page(overlay_page)
    out.add_page(merged)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        out.write(f)


# ============================================================
# Public API: generate Test Record Sheet (mapping-driven)
# ============================================================
def generate_test_record_sheet(payload: Dict[str, Any], out_dir: Optional[str] = None) -> str:
    """
    Generates a print-ready Test Record Sheet PDF using:
      - 2_Source_Data/raw_sources/Test Sheet Template v4.pdf (authoritative template by default)
      - 4_Scripts/backend/mappings/test_record_sheet.json (authoritative mapping)

    payload must already contain the keys referenced by the mapping under:
      - "nameplate": authoritative Nameplate data
      - "derived": computed / test data
    """
    out_base = Path(out_dir) if out_dir else OUTPUT_DIR_DEFAULT

    mapping_obj = json.loads(TEST_RECORD_MAPPING.read_text(encoding="utf-8"))
    output_name = str(mapping_obj.get("output_name") or "TestRecordSheet_filled.pdf")
    output_path = out_base / output_name

    data = payload

    # Prefer mapping-declared template path (relative to project root), then fall back to resolver.
    template_path = None
    template_decl = mapping_obj.get("template")
    if isinstance(template_decl, str) and template_decl.strip():
        candidate = (PROJECT_ROOT / template_decl).resolve()
        if candidate.exists():
            template_path = candidate
    if template_path is None:
        template_path = _resolve_test_record_template()

    render_pdf_from_coordinate_mapping(
        template_path=template_path,
        mapping_path=TEST_RECORD_MAPPING,
        data=data,
        output_path=output_path,
    )

    return str(output_path)
