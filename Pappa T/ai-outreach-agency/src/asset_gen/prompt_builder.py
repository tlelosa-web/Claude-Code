from src.lead_import.schema import Lead
from src.research.schema import ResearchResult


def build_prompt(lead: Lead, research: ResearchResult) -> str:
    industry = lead.industry or "heavy engineering"
    persona = lead.contact_title or "Operations Manager"

    return (
        f"You are an AI automation consultant writing a short insight document "
        f"for {lead.company_name}, a {industry} firm in {lead.region}.\n\n"
        f"Your reader is {lead.contact_name}, their {persona}.\n\n"
        f"Company research summary:\n{research.summary}\n\n"
        f"Write a concise insight document (300 words max) that:\n"
        f"1. Opens with a specific observation about {lead.company_name} "
        f"based on the research above.\n"
        f"2. Identifies one concrete operational pain point common in {industry}.\n"
        f"3. Explains how AI automation could address that pain point "
        f"with a realistic, practical example.\n"
        f"4. Ends with a clear call to action: invite {lead.contact_name} "
        f"to a 15-minute discovery call to explore this further.\n\n"
        f"Tone: professional, direct, no hype. "
        f"Write for someone who manages real operations, not a tech audience."
    )
