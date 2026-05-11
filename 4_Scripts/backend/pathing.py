from __future__ import annotations

import os
from pathlib import Path


def resolve_existing_path(env_key: str, *candidates: Path) -> Path | None:
    env_val = os.getenv(env_key)
    if env_val:
        p = Path(env_val).expanduser()
        if p.exists():
            return p
    for c in candidates:
        if c and c.exists():
            return c
    return None


def find_first_matching(directory: Path, pattern: str) -> Path | None:
    try:
        matches = sorted(directory.glob(pattern))
    except Exception:
        return None
    for p in matches:
        if p.exists():
            return p
    return None


def resolve_paths(base_dir: Path) -> dict:
    project_root = base_dir.parents[1]
    raw_sources_dir = project_root / "2_Source_Data" / "raw_sources"
    live_reports_dir = project_root / "3_Live_Reports"

    errors: dict[str, str] = {}

    default_motor_pdf = base_dir / "2025 - CTP 022- PB4  Performance Data Rev 0.pdf"
    motor_pdf = resolve_existing_path(
        "MOTOR_PDF_PATH",
        raw_sources_dir / "2025 - CTP 022- PB4  Performance Data Rev 0.pdf",
        default_motor_pdf,
        find_first_matching(raw_sources_dir, "*Performance*Data*.pdf") if raw_sources_dir.exists() else None,
    )
    if motor_pdf is None:
        errors["MOTOR_PDF_PATH"] = f"Motor performance PDF not found in {raw_sources_dir}"

    nameplate_excel = resolve_existing_path(
        "NAMEPLATE_EXCEL_PATH",
        raw_sources_dir / "NAME PLATE PROCEDURE.xlsx",
        raw_sources_dir / "Copy of NAME PLATE PROCEDURE.xlsx",
        find_first_matching(raw_sources_dir, "*NAME*PLATE*PROCEDURE*.xlsx") if raw_sources_dir.exists() else None,
    )
    if nameplate_excel is None:
        errors["NAMEPLATE_EXCEL_PATH"] = f"Nameplate Excel not found in {raw_sources_dir}"

    test_sheet_template = resolve_existing_path(
        "TEST_SHEET_TEMPLATE_PATH",
        raw_sources_dir / "Test Sheet Template v4.pdf",
        raw_sources_dir / "Test Sheet Template v3.pdf",
        raw_sources_dir / "Test Sheet Template v2.pdf",
        raw_sources_dir / "Test Sheet Tmp.pdf",
        raw_sources_dir / "Test SheetFM3768.pdf",
        find_first_matching(raw_sources_dir, "Test Sheet*.pdf") if raw_sources_dir.exists() else None,
    )
    if test_sheet_template is None:
        errors["TEST_SHEET_TEMPLATE_PATH"] = f"Test Sheet template PDF not found in {raw_sources_dir}"

    output_dir = resolve_existing_path(
        "OUTPUT_DIR",
        live_reports_dir / "backend_pdfs",
        base_dir,
    ) or base_dir

    return {
        "project_root": project_root,
        "raw_sources_dir": raw_sources_dir,
        "live_reports_dir": live_reports_dir,
        "motor_pdf_path": motor_pdf,
        "nameplate_excel_path": nameplate_excel,
        "test_sheet_template_path": test_sheet_template,
        "output_dir": output_dir,
        "errors": errors,
    }
