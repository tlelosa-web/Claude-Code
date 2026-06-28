from src.lead_import.schema import Lead

SIGN_OFF = (
    "Best regards,\n"
    "Tebello Lelosa\n"
    "AI Automation Consultant\n"
    "tlelosa@gmail.com"
)


def compose_email(lead: Lead, asset_text: str) -> dict:
    subject = f"A quick insight for {lead.company_name}"

    body = (
        f"Hi {lead.contact_name},\n\n"
        f"I came across {lead.company_name} and put together a short insight "
        f"that I thought might be relevant to your work as {lead.contact_title}.\n\n"
        f"{asset_text}\n\n"
        f"{SIGN_OFF}"
    )

    return {
        "to": lead.email,
        "subject": subject,
        "body": body,
    }
