import sys
from pathlib import Path
from io import BytesIO

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# ------------------------------------------------------------
# Path setup (so imports work when running from /backend)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ------------------------------------------------------------
# Local imports (your project files)
# ------------------------------------------------------------
from pdf_generator import make_nameplate_pdf
from motor_fla_lookup import lookup_fla_safe
from connection_lookup import suggest_connection  # <-- MUST exist and return STAR or DELTA only

app = FastAPI(title="Name Plate Tool", version="0.6.0")

# ------------------------------------------------------------
# CORS (dev/LAN friendly)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# Models
# ------------------------------------------------------------
class NameplatePayload(BaseModel):
    series: str = ""
    class_pitch: str = ""
    motor: str = ""          # kW (string, but should be numeric like "3" or "3kW")
    pole: str = ""           # 2/4/6/8
    voltage: str = ""
    fla: str = ""            # optional; auto-calculated if blank
    op_temp: str = "20"
    serial_no: str = ""

    size: str = ""
    op_speed: str = ""       # auto from pole (optional)
    phase: str = ""
    frequency: str = "50"
    connection: str = ""     # auto STAR/DELTA (but we will output STAR or DELTA only)
    date_of_manuf: str = ""

    relube_interval: str = "N/A"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _to_float(v: str):
    try:
        s = str(v).strip()
        # allow "3kW" or "3 kW"
        s = s.replace("kW", "").replace("KW", "").replace("kw", "")
        s = s.replace(" ", "")
        return float(s)
    except Exception:
        return None


def _to_int(v: str):
    try:
        return int(float(str(v).strip().lower().replace("pole", "").strip()))
    except Exception:
        return None


def _speed_from_pole(poles: int) -> str:
    mapping = {2: "2880", 4: "1440", 6: "960", 8: "720"}
    return mapping.get(int(poles), "")


# ------------------------------------------------------------
# API endpoints
# ------------------------------------------------------------
@app.get("/api/fla")
def api_fla(
    motor: str = Query(default="", description="Motor in kW, e.g. 3 or 3kW"),
    pole: str = Query(default="", description="2/4/6/8"),
    voltage: str = Query(default="", description="e.g. 380"),
):
    motor_f = _to_float(motor)
    pole_i = _to_int(pole)
    volt_f = _to_float(voltage)

    if motor_f is None or pole_i is None or volt_f is None:
        return JSONResponse(
            {"fla": "", "error": "Enter numeric motor (kW), pole (2/4/6/8), and voltage."}
        )

    pdf_path = BASE_DIR / "2025 - CTP 022- PB4  Performance Data Rev 0.pdf"
    fla, err = lookup_fla_safe(motor_f, pole_i, volt_f, str(pdf_path))
    return JSONResponse({"fla": fla, "error": err})


@app.get("/api/connection")
def api_connection(
    voltage: str = Query(default="", description="e.g. 380, 525, 220"),
    pole: str = Query(default="", description="2/4/6/8"),
    motor: str = Query(default="", description="Motor in kW, e.g. 3 or 3kW"),
):
    """
    Returns STAR or DELTA only, based on your engineering tables (voltage + pole + motor kW).
    NOTE: Voltage-only calls are not sufficient and will return an error instead of a wrong value.
    """
    volt_f = _to_float(voltage)
    pole_i = _to_int(pole)
    motor_f = _to_float(motor)

    if volt_f is None:
        return JSONResponse({"connection": "", "error": "Provide numeric voltage (e.g. 380)."})
    if pole_i is None or motor_f is None:
        # Important: do NOT guess. We must avoid wrong "STAR/DELTA" outputs.
        return JSONResponse(
            {
                "connection": "",
                "error": "Connection requires motor (kW) and pole (2/4/6/8). Example: /api/connection?voltage=380&pole=4&motor=3",
            }
        )

    conn, err = suggest_connection(volt_f, pole_i, motor_f)

    # Enforce output is STAR or DELTA only
    if conn not in ("STAR", "DELTA"):
        conn = ""

    return JSONResponse({"connection": conn, "error": err})


@app.post("/api/generate-pdf")
def api_generate_pdf(payload: NameplatePayload):
    """
    Generates the nameplate PDF.
    - Auto speed from pole if missing
    - Auto FLA if blank
    - Auto connection using suggest_connection() => STAR or DELTA only
    Returns PDF inline so iframe can render it.
    """
    motor_f = _to_float(payload.motor)
    pole_i = _to_int(payload.pole)
    volt_f = _to_float(payload.voltage)

    # Auto speed
    op_speed = (payload.op_speed or "").strip()
    if pole_i is not None:
        op_speed = _speed_from_pole(pole_i) or op_speed
    max_speed = op_speed

    # Auto FLA if blank
    fla = (payload.fla or "").strip()
    if not fla and motor_f is not None and pole_i is not None and volt_f is not None:
        pdf_path = BASE_DIR / "2025 - CTP 022- PB4  Performance Data Rev 0.pdf"
        calc_fla, _err = lookup_fla_safe(motor_f, pole_i, volt_f, str(pdf_path))
        fla = calc_fla

    # Auto connection (STAR or DELTA only)
    connection = ""
    if motor_f is not None and pole_i is not None and volt_f is not None:
        conn, _cerr = suggest_connection(volt_f, pole_i, motor_f)
        if conn in ("STAR", "DELTA"):
            connection = conn

    data = {
        "series": payload.series,
        "class_pitch": payload.class_pitch,
        "motor": payload.motor,
        "voltage": payload.voltage,
        "fla": fla,
        "op_temp": payload.op_temp or "20",
        "serial_no": payload.serial_no,
        "size": payload.size,
        "op_speed": op_speed,
        "max_speed": max_speed,
        "phase": payload.phase,
        "frequency": payload.frequency or "50",
        # Use computed connection; fallback to payload.connection if you want,
        # but safest is: computed only.
        "connection": connection,
        "date_of_manuf": payload.date_of_manuf,
        "relube_interval": "N/A",
    }

    out_path = BASE_DIR / "nameplate_web.pdf"
    make_nameplate_pdf(data, str(out_path))

    with open(out_path, "rb") as f:
        pdf_bytes = f.read()

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="nameplate.pdf"'},
    )
