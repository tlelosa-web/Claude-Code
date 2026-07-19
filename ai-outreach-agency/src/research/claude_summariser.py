import json
import os

from src.lead_import.schema import Lead
from src.research.ollama_client import call_ollama


def _stub_summary(lead: Lead, raw_data: dict) -> str:
    company = raw_data.get("title", lead.company_name)
    services = ", ".join(raw_data.get("services", []))
    news = raw_data.get("recent_news", "No recent news found.")

    return (
        f"{company} is a {raw_data.get('about', 'company')} "
        f"offering {services}. "
        f"Recent activity: {news}"
    )


def summarise_lead(lead: Lead, raw_data: dict) -> str:
    if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
        return _stub_summary(lead, raw_data)

    prompt = (
        "You are a B2B research analyst. Given this raw company data, write a "
        "200-word summary focused on operational challenges relevant to AI automation. "
        f"Company: {lead.company_name}. "
        f"Data: {json.dumps(raw_data, default=str)}"
    )

    return call_ollama(prompt)
