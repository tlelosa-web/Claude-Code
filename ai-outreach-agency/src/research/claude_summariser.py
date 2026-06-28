from src.lead_import.schema import Lead


# TODO: replace with OpenRouter claude-sonnet-4-6 call
def summarise_lead(lead: Lead, raw_data: dict) -> str:
    company = raw_data.get("title", lead.company_name)
    services = ", ".join(raw_data.get("services", []))
    news = raw_data.get("recent_news", "No recent news found.")

    return (
        f"{company} is a {raw_data.get('about', 'company')} "
        f"offering {services}. "
        f"Recent activity: {news}"
    )
