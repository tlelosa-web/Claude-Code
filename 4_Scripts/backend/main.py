import sys
import os
from datetime import date
from pathlib import Path
from io import BytesIO
from functools import lru_cache
import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# ------------------------------------------------------------
# 1. Centralized Engineering Configuration & Pathing
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PROJECT_ROOT = BASE_DIR.parents[1]
RAW_SOURCES_DIR = PROJECT_ROOT / "2_Source_Data" / "raw_sources"
LIVE_REPORTS_DIR = PROJECT_ROOT / "3_Live_Reports"

from pathing import resolve_paths

_resolved = resolve_paths(BASE_DIR)

CONFIG = {
    "APP_VERSION": "0.8.4",
    "ENGINEERING_REVISION": "2025-Rev0",
    "MOTOR_PDF_PATH": _resolved["motor_pdf_path"],
    "NAMEPLATE_EXCEL_PATH": _resolved["nameplate_excel_path"],
    "OUTPUT_DIR": _resolved["output_dir"],
    "DEFAULT_FREQ": "50",
    "DEFAULT_TEMP": "20",
    "TEST_SHEET_TEMPLATE_PATH": _resolved["test_sheet_template_path"] or (BASE_DIR / "templates" / "test_sheet_blank.pdf"),
    "DOC_HISTORY_PATH": BASE_DIR / "doc_history.json",
    "CONFIG_ERRORS": _resolved["errors"],
}

try:
    if CONFIG.get("OUTPUT_DIR"):
        Path(CONFIG["OUTPUT_DIR"]).mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# ------------------------------------------------------------
# Centralized logging (rotating file)
# ------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "backend.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("nameplate.backend")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(str(LOG_FILE), maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
logger = _logger

# --------------------------------------------
# Local imports (Post Path Setup)
# --------------------------------------------
from pdf_generator import make_nameplate_pdf, generate_test_record_sheet
from motor_fla_lookup import lookup_fla_safe, _load_motor_table
from excel_source import read_nameplate_from_excel, read_test_sheet_from_excel
from connection_lookup import (
    suggest_connection,
    STAR_RULES,
    DELTA_RULES_380_MIN,
    DELTA_RULES_MAX,
)

def _config_error(key: str) -> str | None:
    errs = CONFIG.get("CONFIG_ERRORS") or {}
    return errs.get(key)

def _motor_pdf_path() -> Path | None:
    p = CONFIG.get("MOTOR_PDF_PATH")
    if isinstance(p, Path) and p.exists():
        return p
    return None

def _excel_path() -> Path | None:
    p = CONFIG.get("NAMEPLATE_EXCEL_PATH")
    if isinstance(p, Path) and p.exists():
        return p
    return None

app = FastAPI(
    title="Name Plate Tool",
    version=CONFIG["APP_VERSION"],
    description=f"Engineering Revision: {CONFIG['ENGINEERING_REVISION']}"
)

# ------------------------------------------------------------
# 2. CORS (LAN Deployment Ready)
# ------------------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# 3. Models
# ------------------------------------------------------------
class TestLinePayload(BaseModel):
    motor_serial_number: str = ""
    blade_pitch_deg: str = ""
    tacho_clamp_serial_no: str = ""
    speed_actual: str = ""
    current_ph1: str = ""
    current_ph2: str = ""
    current_ph3: str = ""
    voltage_ph1: str = ""
    voltage_ph2: str = ""
    voltage_ph3: str = ""
    connection: str = ""

class NameplatePayload(BaseModel):
    customer_name: str = ""
    series: str = ""
    class_pitch: str = ""
    imp_form: str = "FORM B"
    motor: str = ""
    pole: str = ""
    voltage: str = ""
    fla: str = ""
    op_temp: str = CONFIG["DEFAULT_TEMP"]
    serial_no: str = ""
    size: str = ""
    op_speed: str = ""
    phase: str = ""
    frequency: str = CONFIG["DEFAULT_FREQ"]
    connection: str = ""
    date_of_manuf: str = ""
    quantity: int = 1
    relube_interval: str = "N/A"
    manufacturer: str = ""

class TestRecordSheetPayload(BaseModel):
    date: str = Field(..., description="Date e.g. 22/01/2026")
    contract_no: str = Field(..., description="Serial No.")
    fan_size: str = Field(..., description="Fan size")
    fan_series: str = Field(..., description="Fan series")
    customer_name: str = Field(...)
    motor_current: str = Field(..., description="F.L.A.")
    make: str = Field(...)
    procedure_used: str = Field(..., description="QC-WI-05")
    motor_voltage: str = Field(...)
    fan_speed: str = Field(...)
    connection: str = Field(..., description="STAR or DELTA")
    imp_form: str = Field(default="FORM B", description="Impeller form e.g. FORM B")
    description: str = ""

    motor_serial_number: str = ""
    blade_pitch_deg: str = ""
    tacho_clamp_serial_no: str = ""
    speed_actual: str = ""
    current_ph1: str = ""; current_ph2: str = ""; current_ph3: str = ""
    voltage_ph1: str = ""; voltage_ph2: str = ""; voltage_ph3: str = ""
    test_lines: list[TestLinePayload] = Field(default_factory=list)

# ------------------------------------------------------------
# 4. Helpers
# ------------------------------------------------------------
def _to_float(v: str):
    try:
        s = str(v).strip().lower().replace("kw", "").replace(" ", "")
        return float(s)
    except: return None

def _to_int(v: str):
    try:
        return int(float(str(v).strip().lower().replace("pole", "").strip()))
    except: return None

def _clean(s: str) -> str: return "" if s is None else str(s).strip()

def _speed_from_pole(poles: int) -> str:
    return {2: "2880", 4: "1440", 6: "960", 8: "720"}.get(int(poles), "")

def _fmt_kw(x: float) -> str: return f"{float(x):g}"

def _motor_description(motor: str, pole: str) -> str:
    motor_s = _clean(motor)
    pole_s = _clean(pole)
    if motor_s:
        motor_f = _to_float(motor_s)
        motor_part = f"{_fmt_kw(motor_f)}kW" if motor_f is not None else motor_s
    else:
        motor_part = ""

    pole_i = _to_int(pole_s)
    pole_part = f"{pole_i} Pole" if pole_i is not None else (f"{pole_s} Pole" if pole_s else "")
    return " ".join(part for part in (motor_part, pole_part) if part)

@lru_cache(maxsize=1)
def _options_cached() -> dict:
    """Centralized options source for UI dropdowns."""
    keys = set(STAR_RULES.keys()) | set(DELTA_RULES_380_MIN.keys()) | set(DELTA_RULES_MAX.keys())
    voltages = sorted({int(v) for (v, _p) in keys})
    poles_from_conn = sorted({int(p) for (_v, p) in keys})

    motor_pdf = _motor_pdf_path()
    table = _load_motor_table(str(motor_pdf)) if motor_pdf else {}

    motors_by_pole: dict[str, list[str]] = {}
    poles_from_motor = sorted({int(p) for (_kw, p) in table.keys()}) if table else []
    validated_poles = sorted(set(poles_from_conn).intersection(set(poles_from_motor))) if table else []

    for p in validated_poles:
        kws = sorted({float(kw) for (kw, pp) in table.keys() if int(pp) == int(p)})
        motors_by_pole[str(p)] = [_fmt_kw(k) for k in kws]

    motor_err = _config_error("MOTOR_PDF_PATH") if not motor_pdf else None

    return {
        "voltages": [str(v) for v in voltages],
        "poles": [str(p) for p in validated_poles],
        "motors_by_pole": motors_by_pole,
        "revision": CONFIG["ENGINEERING_REVISION"],
        "error": None if table else (motor_err or "Motor PDF table missing or unreadable"),
    }

# ------------------------------------------------------------
# 4a. Document History (Persistent JSON)
# ------------------------------------------------------------
def _ensure_history_file():
    try:
        CONFIG["DOC_HISTORY_PATH"].parent.mkdir(parents=True, exist_ok=True)
        if not CONFIG["DOC_HISTORY_PATH"].exists():
            CONFIG["DOC_HISTORY_PATH"].write_text("[]", encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to ensure history file at {CONFIG['DOC_HISTORY_PATH']}: {e}")

def _load_history() -> list:
    _ensure_history_file()
    try:
        import json
        return json.loads(CONFIG["DOC_HISTORY_PATH"].read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load history from {CONFIG['DOC_HISTORY_PATH']}: {e}")
        return []

def _append_history(record: dict):
    _ensure_history_file()
    try:
        import json, datetime
        hist = _load_history()
        stamped = {"generated_at": datetime.datetime.now().isoformat(timespec="seconds"), **record}
        hist.append(stamped)
        CONFIG["DOC_HISTORY_PATH"].write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"History appended: {stamped}")
    except Exception as e:
        logger.error(f"Failed to append history record {record}: {e}")

def _sanitize_filename(s: str) -> str:
    return "" if s is None else (
        str(s).strip().replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("?", "")
            .replace('"', "").replace("<", "").replace(">", "").replace("|", "").replace(" ", " ").strip()
    )

def _today_ddmmyyyy() -> str:
    import datetime
    return datetime.datetime.now().strftime("%d/%m/%Y")

def _normalise_test_lines(lines: list[TestLinePayload], fallback: dict) -> list[dict]:
    normalised = []
    for line in lines[:20]:
        data = line.dict()
        normalised.append({
            "motor_serial_number": _clean(data.get("motor_serial_number")) or _clean(fallback.get("motor_serial_number")),
            "blade_pitch_deg": _clean(data.get("blade_pitch_deg")) or _clean(fallback.get("blade_pitch_deg")),
            "tacho_clamp_serial_no": _clean(data.get("tacho_clamp_serial_no")) or "N/A",
            "speed_actual": _clean(data.get("speed_actual")) or _clean(fallback.get("speed_actual")),
            "current_ph1": _clean(data.get("current_ph1")) or _clean(fallback.get("current_ph1")),
            "current_ph2": _clean(data.get("current_ph2")) or _clean(fallback.get("current_ph2")),
            "current_ph3": _clean(data.get("current_ph3")) or _clean(fallback.get("current_ph3")),
            "voltage_ph1": _clean(data.get("voltage_ph1")) or _clean(fallback.get("voltage_ph1")),
            "voltage_ph2": _clean(data.get("voltage_ph2")) or _clean(fallback.get("voltage_ph2")),
            "voltage_ph3": _clean(data.get("voltage_ph3")) or _clean(fallback.get("voltage_ph3")),
            "connection": _clean(data.get("connection")) or _clean(fallback.get("connection")),
        })
    return normalised

# ------------------------------------------------------------
# 5. API Endpoints
# ------------------------------------------------------------
@app.get("/api/options")
def api_options():
    return JSONResponse(_options_cached())

@app.get("/api/nameplate/from-excel")
def api_nameplate_from_excel():
    xlsx = _excel_path()
    if not xlsx:
        return JSONResponse(
            {"nameplate": {}, "error": _config_error("NAMEPLATE_EXCEL_PATH") or "Nameplate Excel file not found."},
            status_code=500,
        )
    try:
        data = read_nameplate_from_excel(str(xlsx))
        return JSONResponse({"nameplate": data, "xlsx_path": str(xlsx), "error": None})
    except Exception as e:
        logger.error(f"Failed to read nameplate from Excel: {e}")
        return JSONResponse({"nameplate": {}, "error": str(e)}, status_code=500)

@app.get("/api/fla")
def api_fla(motor: str = "", pole: str = "", voltage: str = ""):
    m_f, p_i, v_f = _to_float(motor), _to_int(pole), _to_float(voltage)
    if None in (m_f, p_i, v_f):
        return JSONResponse({"fla": "", "error": "Incomplete numeric inputs."})

    motor_pdf = _motor_pdf_path()
    if not motor_pdf:
        return JSONResponse({"fla": "", "error": _config_error("MOTOR_PDF_PATH") or "Motor performance PDF not found."}, status_code=500)

    fla, err = lookup_fla_safe(m_f, p_i, v_f, str(motor_pdf))
    return JSONResponse({"fla": fla, "error": err})

@app.get("/api/connection")
def api_connection(voltage: str = "", pole: str = "", motor: str = ""):
    v_f, p_i, m_f = _to_float(voltage), _to_int(pole), _to_float(motor)
    if v_f is None: return JSONResponse({"connection": "", "error": "Numeric voltage required."})
    if p_i is None or m_f is None: return JSONResponse({"connection": "", "error": "Motor and Pole required."}, status_code=400)

    conn, err = suggest_connection(v_f, p_i, m_f)
    return JSONResponse({"connection": conn if conn in ("STAR", "DELTA") else "", "error": err})

@app.post("/api/generate-pdf")
def api_generate_pdf(payload: NameplatePayload):
    m_f, p_i, v_f = _to_float(payload.motor), _to_int(payload.pole), _to_float(payload.voltage)

    op_speed = _clean(payload.op_speed) or (_speed_from_pole(p_i) if p_i else "")

    fla = None
    motor_pdf = _motor_pdf_path()
    if all(x is not None for x in (m_f, p_i, v_f)) and motor_pdf:
        fla, _ = lookup_fla_safe(m_f, p_i, v_f, str(motor_pdf))
    if not fla:
        fla = _clean(payload.fla)

    conn = ""
    if all(x is not None for x in (m_f, p_i, v_f)):
        c, _ = suggest_connection(v_f, p_i, m_f)
        if c in ("STAR", "DELTA"):
            conn = c
    if not conn:
        conn = _clean(payload.connection)

    # Server-side validation to enforce engineering correctness before any PDF is generated
    errors = []
    if m_f is None or p_i is None or v_f is None:
        errors.append("Motor (kW), Poles and Voltage must be numeric and non-empty.")
    if not motor_pdf:
        errors.append(_config_error("MOTOR_PDF_PATH") or "Motor performance PDF not found.")
    if not fla:
        errors.append("Full Load Amperage (FLA) could not be resolved from performance tables.")
    if conn not in ("STAR", "DELTA"):
        errors.append("A valid connection (STAR or DELTA) could not be determined from the supplied values.")

    if errors:
        return JSONResponse({"error": " ".join(errors)}, status_code=400)

    data = payload.dict()
    data.update({"fla": fla, "op_speed": op_speed, "max_speed": op_speed, "connection": conn})

    out_path = CONFIG["OUTPUT_DIR"] / "nameplate_web.pdf"
    make_nameplate_pdf(data, str(out_path))

    return StreamingResponse(open(out_path, "rb"), media_type="application/pdf")

@app.post("/api/reports/test-record-sheet")
def api_test_record_sheet(payload: TestRecordSheetPayload):
    import shutil

    data = payload.dict()

    if len(payload.test_lines) > 20:
        return JSONResponse({"error": "A single test sheet can hold up to 20 fan lines."}, status_code=400)

    if data["connection"].upper() not in ("STAR", "DELTA"):
        return JSONResponse({"error": "Invalid connection"}, status_code=400)

    # Build nameplate/derived structure for mapping-driven generator
    nameplate_data = {
        "nameplate": {
            "customer_name": _clean(data.get("customer_name")),
            "series": _clean(data.get("fan_series")),
            "size": _clean(data.get("fan_size")),
            "serial_no": _clean(data.get("contract_no")),
            "class_pitch": _clean(data.get("blade_pitch_deg")),
            "voltage": _clean(data.get("motor_voltage")),
            "op_speed": _clean(data.get("fan_speed")),
            "phase": "",
            "connection": _clean(data.get("connection")),
            "fla": _clean(data.get("motor_current")),
            "manufacturer": _clean(data.get("make")),
            "date_of_manuf": "",
            "relube_interval": "N/A",
        },
        "derived": {
            "date": _clean(data.get("date")),
            "motor_description": _clean(data.get("description")),
            "procedure_used": _clean(data.get("procedure_used")),
            "imp_form": _clean(data.get("imp_form")) or "FORM B",
            "motor_serial_number": _clean(data.get("motor_serial_number")),
            "blade_pitch_deg": _clean(data.get("blade_pitch_deg")),
            "tacho_clamp_serial_no": _clean(data.get("tacho_clamp_serial_no")) or "N/A",
            "speed_actual": _clean(data.get("speed_actual")),
            "voltage_ph1": _clean(data.get("voltage_ph1")),
            "voltage_ph2": _clean(data.get("voltage_ph2")),
            "voltage_ph3": _clean(data.get("voltage_ph3")),
            "current_ph1": _clean(data.get("current_ph1")),
            "current_ph2": _clean(data.get("current_ph2")),
            "current_ph3": _clean(data.get("current_ph3")),
            "connection": _clean(data.get("connection")),
        }
    }
    nameplate_data["derived"]["test_lines"] = _normalise_test_lines(
        payload.test_lines,
        nameplate_data["derived"],
    )

    # Generate via mapping-driven generator, then keep existing output filename behavior
    gen_path = Path(generate_test_record_sheet(nameplate_data, out_dir=str(CONFIG["OUTPUT_DIR"])))
    out_path = CONFIG["OUTPUT_DIR"] / "test_record_sheet_web.pdf"
    shutil.copyfile(gen_path, out_path)

    return StreamingResponse(open(out_path, "rb"), media_type="application/pdf")

@app.get("/api/reports/history")
def api_reports_history():
    return JSONResponse(_load_history())

@app.get("/api/reports/download")
def api_reports_download(file: str):
    p = CONFIG["OUTPUT_DIR"] / Path(file).name
    if not p.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    return StreamingResponse(open(p, "rb"), media_type="application/pdf")

@app.post("/api/reports/test-record-sheet/from-nameplate")
def api_test_record_sheet_from_nameplate(payload: NameplatePayload):
    import shutil

    quantity = payload.quantity if payload.quantity and payload.quantity > 0 else 1
    if quantity > 20:
        return JSONResponse({"error": "A single test sheet can hold up to 20 fan lines."}, status_code=400)

    m_f, p_i, v_f = _to_float(payload.motor), _to_int(payload.pole), _to_float(payload.voltage)

    xlsx = _excel_path()
    if not xlsx:
        return JSONResponse({"error": _config_error("NAMEPLATE_EXCEL_PATH") or "Nameplate Excel file not found."}, status_code=500)

    try:
        test_sheet = read_test_sheet_from_excel(str(xlsx), series_hint=payload.series)
    except Exception as e:
        return JSONResponse({"error": "Failed to read Test Sheet tab from Excel.", "detail": str(e)}, status_code=500)

    fan_speed = _clean(payload.op_speed) or _clean(test_sheet.get("fan_speed")) or (_speed_from_pole(p_i) if p_i else "")

    motor_current = None
    motor_pdf = _motor_pdf_path()
    if all(x is not None for x in (m_f, p_i, v_f)) and motor_pdf:
        motor_current, _ = lookup_fla_safe(m_f, p_i, v_f, str(motor_pdf))
    if not motor_current:
        motor_current = _clean(payload.fla) or _clean(test_sheet.get("motor_current"))

    conn = None
    if all(x is not None for x in (m_f, p_i, v_f)):
        c, _ = suggest_connection(v_f, p_i, m_f)
        if c in ("STAR", "DELTA"):
            conn = c
    if not conn:
        conn = _clean(payload.connection) or _clean(test_sheet.get("connection"))

    if conn.upper() not in ("STAR", "DELTA"):
        return JSONResponse({"error": "Invalid connection"}, status_code=400)

    # Mapping-driven input structure: nameplate.* + derived.*
    nameplate_from_payload = payload.dict()
    # Keep user-entered form data authoritative; only use Excel test-sheet as fallback.
    if not _clean(nameplate_from_payload.get("serial_no")) and _clean(test_sheet.get("contract_no")):
        nameplate_from_payload["serial_no"] = _clean(test_sheet.get("contract_no"))
    if not _clean(nameplate_from_payload.get("series")) and _clean(test_sheet.get("fan_series")):
        nameplate_from_payload["series"] = _clean(test_sheet.get("fan_series"))
    if not _clean(nameplate_from_payload.get("size")) and _clean(test_sheet.get("fan_size")):
        nameplate_from_payload["size"] = _clean(test_sheet.get("fan_size"))
    if not _clean(nameplate_from_payload.get("customer_name")) and _clean(test_sheet.get("customer_name")):
        nameplate_from_payload["customer_name"] = _clean(test_sheet.get("customer_name"))
    if not _clean(nameplate_from_payload.get("class_pitch")) and _clean(test_sheet.get("blade_pitch_deg")):
        nameplate_from_payload["class_pitch"] = _clean(test_sheet.get("blade_pitch_deg"))
    if not _clean(nameplate_from_payload.get("voltage")) and _clean(test_sheet.get("motor_voltage")):
        nameplate_from_payload["voltage"] = _clean(test_sheet.get("motor_voltage"))
    if not _clean(nameplate_from_payload.get("manufacturer")) and _clean(test_sheet.get("make")):
        nameplate_from_payload["manufacturer"] = _clean(test_sheet.get("make"))
    if not _clean(nameplate_from_payload.get("motor")) and _clean(test_sheet.get("description")):
        nameplate_from_payload["motor"] = _clean(test_sheet.get("description"))

    # Ensure computed values are set in nameplate before building the data structure
    nameplate_from_payload["op_speed"] = _clean(fan_speed)
    nameplate_from_payload["fla"] = _clean(motor_current)
    nameplate_from_payload["connection"] = _clean(conn)

    derived_fallback = {
        "date": date.today(),
        "motor_description": _motor_description(payload.motor, payload.pole) or _clean(test_sheet.get("description")),
        "procedure_used": "QC-WI-05",
        "imp_form": _clean(payload.imp_form) or _clean(test_sheet.get("imp_form")) or "FORM B",
        "motor_serial_number": _clean(test_sheet.get("motor_serial_number")),
        "blade_pitch_deg": _clean(payload.class_pitch) or _clean(test_sheet.get("blade_pitch_deg")),
        "tacho_clamp_serial_no": _clean(test_sheet.get("tacho_clamp_serial_no")) or "N/A",
        "speed_actual": _clean(payload.op_speed) or _clean(test_sheet.get("speed_actual")) or _clean(fan_speed),
        "current_ph1": _clean(test_sheet.get("current_ph1")),
        "current_ph2": _clean(test_sheet.get("current_ph2")),
        "current_ph3": _clean(test_sheet.get("current_ph3")),
        "voltage_ph1": _clean(test_sheet.get("voltage_ph1")) or _clean(nameplate_from_payload.get("voltage")),
        "voltage_ph2": _clean(test_sheet.get("voltage_ph2")) or _clean(nameplate_from_payload.get("voltage")),
        "voltage_ph3": _clean(test_sheet.get("voltage_ph3")) or _clean(nameplate_from_payload.get("voltage")),
        "connection": _clean(conn),
    }
    derived_fallback["test_lines"] = _normalise_test_lines(
        [TestLinePayload() for _ in range(quantity)],
        derived_fallback,
    )

    nameplate_data = {
        "nameplate": nameplate_from_payload,
        "derived": derived_fallback,
    }

    fname = f"Test Sheet{_sanitize_filename(_clean(nameplate_data['nameplate'].get('serial_no')) or 'UNKNOWN')}.pdf"
    out_path = CONFIG["OUTPUT_DIR"] / fname

    # Generate via mapping-driven generator with robust error reporting
    try:
        gen_path = Path(generate_test_record_sheet(nameplate_data, out_dir=str(CONFIG["OUTPUT_DIR"])))
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    except ValueError as e:
        # Missing required mapping values or invalid data contract
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Failed to generate Test Record Sheet PDF.", "detail": str(e)}, status_code=500)

    shutil.copyfile(gen_path, out_path)

    _append_history({
        "type": "Test Sheet",
        "serial_no": _clean(payload.serial_no),
        "file_name": fname,
        "path": str(out_path),
    })

    return StreamingResponse(open(out_path, "rb"), media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    # Bind to 0.0.0.0 for LAN availability
    uvicorn.run(app, host="0.0.0.0", port=8000)
