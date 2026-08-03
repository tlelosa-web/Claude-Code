import csv
from pathlib import Path
from typing import List

from .schema import Lead

COLUMN_MAP = {
    "company_name": "company_name",
    "company": "company_name",
    "contact_name": "contact_name",
    "name": "contact_name",
    "contact_title": "contact_title",
    "title": "contact_title",
    "email": "email",
    "contact_email": "email",
    "phone": "phone",
    "website": "website",
    "url": "website",
    "industry": "industry",
    "region": "region",
    "city": "region",
    "employee_count": "employee_count",
    "employees": "employee_count",
    "source": "source",
    "campaign": "campaign",
}


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_")


def _map_row(row: dict) -> dict:
    mapped = {}
    for raw_key, value in row.items():
        norm = _normalize_header(raw_key)
        schema_field = COLUMN_MAP.get(norm)
        if schema_field and value and value.strip():
            mapped[schema_field] = value.strip()
    return mapped


def read_csv(filepath: str | Path) -> List[Lead]:
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    leads = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            mapped = _map_row(row)
            try:
                lead = Lead(**mapped)
                leads.append(lead)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Row {i}: {e}") from e

    return leads
