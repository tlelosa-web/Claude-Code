from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import re

@lru_cache(maxsize=1)
def _load_motor_table(pdf_path: str) -> dict[tuple[float, int], float]:
    p = Path(pdf_path)
    if not p.exists():
        return {}

    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages: return {}
            text = pdf.pages[0].extract_text() or ""
    except:
        return {}

    # Regex captures: [kW] [Poles] [Amps@400V]
    row_re = re.compile(
        r"^\s*(\d+(?:\.\d+)?)\s+\S+\s+\S+\s+\d+\s+([2468])\s+(\d+(?:\.\d+)?)\b",
        re.MULTILINE,
    )

    table: dict[tuple[float, int], float] = {}
    for m in row_re.finditer(text):
        table[(float(m.group(1)), int(m.group(2)))] = float(m.group(3))

    return table

def lookup_fla_safe(output_kw: float, poles: int, voltage: float, pdf_path: str) -> tuple[str, str | None]:
    table = _load_motor_table(pdf_path)
    if not table:
        return "", "Motor data source unavailable."

    key = (float(output_kw), int(poles))
    if key not in table:
        return "", f"No match for {output_kw}kW / {poles}P."

    amps_400 = table[key]
    if voltage <= 0: return "", "Invalid voltage."

    # Linear scaling: I2 = I1 * (V1 / V2)
    amps_v = amps_400 * (400.0 / float(voltage))
    return f"{amps_v:.2f}", None
