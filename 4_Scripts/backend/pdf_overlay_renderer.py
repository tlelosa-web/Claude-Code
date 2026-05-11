from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class MappingItem:
    key: str
    x: float
    y: float
    source: str
    required: bool = False
    value: Optional[str] = None
    transform: Optional[Dict[str, Any]] = None


def _get_nested(data: Dict[str, Any], path: str) -> Any:
    """
    Supports:
      - nameplate.serial_no  (reads data["nameplate"]["serial_no"])
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
        try:
            num = float(str(raw).replace(",", "").strip())
        except Exception:
            return str(raw)
        decimals = transform.get("decimals")
        if decimals is not None:
            s = f"{num:.{int(decimals)}f}"
        else:
            # keep integer-looking values clean
            s = str(int(num)) if num.is_integer() else str(num)
        suffix = transform.get("suffix", "")
        return f"{s}{suffix}"

    if t == "date":
        # raw may be date, datetime, or string; default to today if empty handled elsewhere
        fmt = transform.get("format", "DD/MM/YYYY")
        if isinstance(raw, date):
            d = raw
        else:
            # if it's already a string, just return it
            return str(raw)
        if fmt == "DD/MM/YYYY":
            return d.strftime("%d/%m/%Y")
        return d.isoformat()

    if t == "fan_size_primary":
        # Example: "315 / 165 / 6 A" -> "315"
        s = str(raw).strip()
        s = s.replace(" ", "")
        parts = s.split("/")
        return parts[0] if parts else str(raw)

    # fallback
    return str(raw)


def _resolve_value(item: MappingItem, data: Dict[str, Any]) -> str:
    if item.source == "literal":
        return str(item.value or "")

    if item.source == "derived.report_date":
        return _apply_transform(date.today(), item.transform)

    # normal nameplate.* lookups
    raw = _get_nested(data, item.source)
    return _apply_transform(raw, item.transform)


def render_pdf_from_coordinate_mapping(
    template_path: Path,
    mapping_path: Path,
    data: Dict[str, Any],
    output_path: Path,
) -> None:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    mapping_obj = json.loads(mapping_path.read_text(encoding="utf-8"))

    items = []
    for it in mapping_obj.get("items", []):
        items.append(
            MappingItem(
                key=it["key"],
                x=float(it["x"]),
                y=float(it["y"]),
                source=str(it["source"]),
                required=bool(it.get("required", False)),
                value=it.get("value"),
                transform=it.get("transform"),
            )
        )

    reader = PdfReader(str(template_path))
    base_page = reader.pages[int(mapping_obj.get("page_index", 0))]

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
        c.drawString(item.x, item.y, str(val))

    c.save()
    packet.seek(0)

    if missing_required:
        raise ValueError(f"Missing required mapping values: {', '.join(missing_required)}")

    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    # Merge overlay onto template
    out = PdfWriter()
    merged = reader.pages[0]
    merged.merge_page(overlay_page)
    out.add_page(merged)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        out.write(f)
