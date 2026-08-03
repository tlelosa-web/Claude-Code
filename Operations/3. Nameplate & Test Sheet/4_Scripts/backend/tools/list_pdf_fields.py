from pathlib import Path

from pypdf import PdfReader


def _resolve_template() -> Path:
    """
    Keep tooling aligned with the app:
      - Prefer env override(s)
      - Otherwise use the authoritative raw_sources test sheet template
    """
    import os

    project_root = Path(__file__).resolve().parents[3]
    raw_sources = project_root / "2_Source_Data" / "raw_sources"

    for env_key in ("TEST_RECORD_TEMPLATE_PATH", "TEST_SHEET_TEMPLATE_PATH", "TEST_RECORD_SHEET_TEMPLATE_PATH"):
        v = os.getenv(env_key)
        if v:
            p = Path(v).expanduser()
            if p.exists():
                return p

    preferred = raw_sources / "Test Sheet Tmp.pdf"
    if preferred.exists():
        return preferred

    direct = raw_sources / "TestRecordSheet.pdf"
    if direct.exists():
        return direct

    candidates = sorted(raw_sources.glob("Test Sheet*.pdf")) if raw_sources.exists() else []
    if candidates:
        return candidates[0]

    raise FileNotFoundError(
        "Test Record Sheet template PDF not found. "
        "Set TEST_RECORD_TEMPLATE_PATH to a valid PDF file."
    )

def main():
    pdf_path = _resolve_template()

    reader = PdfReader(str(pdf_path))
    fields = reader.get_fields() or {}

    print(f"Template: {pdf_path}")
    print(f"Pages: {len(reader.pages)}")
    print(f"Field count: {len(fields)}\n")

    for name, meta in fields.items():
        ft = meta.get("/FT")
        v = meta.get("/V")
        print(f"- {name} | type={ft} | default={v}")

if __name__ == "__main__":
    main()
