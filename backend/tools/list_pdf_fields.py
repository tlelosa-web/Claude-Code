from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("templates/TestRecordSheet.pdf")

def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Template not found: {PDF_PATH.resolve()}")

    reader = PdfReader(str(PDF_PATH))
    fields = reader.get_fields() or {}

    print(f"Template: {PDF_PATH}")
    print(f"Pages: {len(reader.pages)}")
    print(f"Field count: {len(fields)}\n")

    for name, meta in fields.items():
        ft = meta.get("/FT")
        v = meta.get("/V")
        print(f"- {name} | type={ft} | default={v}")

if __name__ == "__main__":
    main()
