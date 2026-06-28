from src.lead_import.schema import Lead
from .apify_client import ApifyClient
from .claude_summariser import summarise_lead
from .schema import ResearchResult


def research_lead(lead: Lead, apify: ApifyClient | None = None) -> ResearchResult:
    apify = apify or ApifyClient()

    if not lead.website:
        return ResearchResult(
            lead_id=lead.id,
            summary=f"No website available for {lead.company_name}. Manual research required.",
            raw_data={},
        )

    raw_data = apify.scrape_company(lead.website)
    summary = summarise_lead(lead, raw_data)

    return ResearchResult(
        lead_id=lead.id,
        summary=summary,
        raw_data=raw_data,
    )
