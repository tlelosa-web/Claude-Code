"""
Gmail Compose Link Generator
Generates pre-filled Gmail compose URLs for cold email outreach.
Opens Gmail compose window with recipient, subject, and body ready to send.
"""
import os
import urllib.parse
import webbrowser
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
GMAIL_BASE = "https://mail.google.com/mail/?view=cm&fs=1"

CONTACTS = [
    # Tier 1 - Engineering Recruiters
    {"name": "Kontak Recruitment", "email": "recruit@cdconsult.co.za", "tier": 1,
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear Kontak Recruitment Team,

I'm reaching out because your firm specializes in engineering and manufacturing placements — I saw your recent Mechanical Project Engineer posting for Boksburg — and my background aligns directly with the roles you fill.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable based on the role. I'm available for a brief call on most weekdays between 08:00 and 17:00 — whatever suits your schedule.

I've attached my CV and would appreciate being added to your database for relevant opportunities.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "TRS Staffing (Engineering)", "email": "info@trsstaffing.com", "tier": 1,
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear TRS Staffing Engineering Team,

I'm reaching out because your engineering staffing division places professionals across South Africa's industrial sector, and my 19-year background in mechanical engineering, manufacturing operations, and project engineering could be valuable for your current and future client requirements.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would appreciate being added to your engineering candidate database.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "TRS Staffing (Manufacturing)", "email": "info@trsstaffing.com", "tier": 1,
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear TRS Staffing Manufacturing Team,

I'm reaching out because your manufacturing division specializes in industrial placements across Johannesburg, and my 19-year background in mechanical engineering, manufacturing operations, and supply chain management aligns directly with the roles you fill.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would appreciate being added to your manufacturing candidate database.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "EDM Recruitment", "email": "info@edm.co.za", "tier": 1,
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear EDM Recruitment Team,

I'm reaching out because your agency places mechanical engineering professionals, and my 19-year background in mechanical engineering, manufacturing operations, and project engineering aligns directly with your specialization.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would appreciate being added to your candidate database.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "TAKORA", "email": "lThandiswa@takora.co.za", "tier": 1,
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear TAKORA Team,

I'm reaching out because you're currently advertising Intermediate and Junior Project Engineer roles, and my 19-year background in mechanical engineering and project delivery could be a strong fit for your clients.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would welcome a conversation about your current openings.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "Technical Placements", "email": "", "tier": 1, "note": "Find email via https://www.technicalplacements.co.za",
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear Technical Placements Team,

I'm reaching out because your agency specializes in technical and engineering placements across Gauteng, and my 19-year background in mechanical engineering, manufacturing operations, and project engineering aligns directly with the roles you fill.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would appreciate being added to your candidate database.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "Network Recruitment", "email": "", "tier": 1, "note": "Find email via https://www.networkrecruitment.co.za | Phone: +27 12 348 4940",
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear Network Recruitment Team,

I'm reaching out because your firm has a strong presence in engineering recruitment, and my 19-year background in mechanical engineering, manufacturing operations, and project engineering could be valuable for your current client requirements.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV and would welcome a conversation about potential placements.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "Kwena Human Capital", "email": "", "tier": 1, "note": "Apply via CareerJunction — they're posting Project Engineer roles",
     "subject": "Tebello Lelosa — Operations Foreman / Project Engineer — 19 Years Experience — Gauteng",
     "body": """Dear Kwena Human Capital Team,

I'm reaching out because you're currently advertising Project Engineer (Mechanical & Piping) and Piping Design Engineer roles in Sandton/Rivonia, and my 19-year background in mechanical engineering and project execution aligns directly with these positions.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV for your review.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    # Tier 2 - SCM & Operations Recruiters
    {"name": "Clarkhouse Human Capital", "email": "", "tier": 2, "note": "Apply via PNet — they're posting Supply Chain Manager (FMCG)",
     "subject": "Tebello Lelosa — Operations & Supply Chain Professional — 19 Years Experience — Gauteng",
     "body": """Dear Clarkhouse Human Capital Team,

I'm reaching out because you're advertising a Supply Chain Manager (FMCG) role in Johannesburg North, and my background includes 8 years of supply chain management at Morgan Advanced Materials — including S&OP facilitation, demand forecasting, and inventory optimization.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV for your review.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "FROGG Recruitment", "email": "", "tier": 2, "note": "Apply via PNet — they're posting Technical Buyer/Supply Chain Officer",
     "subject": "Tebello Lelosa — Operations & Supply Chain Professional — 19 Years Experience — Gauteng",
     "body": """Dear FROGG Recruitment Team,

I'm reaching out because you're advertising a Technical Buyer/Supply Chain Officer role in steel manufacturing, and my 19-year background includes extensive procurement, supplier negotiation, and materials cost analysis across Morgan Advanced Materials and Howden Africa.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV for your review.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},

    {"name": "Top Talent Professional Services", "email": "", "tier": 2, "note": "Apply via PNet — they're posting Operations Manager – Metallurgy",
     "subject": "Tebello Lelosa — Operations Manager Candidate — 19 Years Experience — Gauteng",
     "body": """Dear Top Talent Professional Services,

I'm reaching out because you're advertising an Operations Manager – Metallurgy role on the East Rand, and my 19-year background includes workshop operations supervision, production planning, and cross-functional team leadership in heavy industrial environments.

Over 19 years, I've earned 5 promotions across three companies — progressing from CNC Programmer to Operations Foreman, including two tenures as Project Engineer at Howden Africa where they re-hired me based on prior performance. I currently lead workshop operations at FanMovement (Pty) Ltd.

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable. I'm available for a brief call most weekdays between 08:00 and 17:00.

I've attached my CV for your review.

Best regards,

Tebello Lelosa
078 481 8711
tlelosa@gmail.com
linkedin.com/in/tebello-lelosa-45613a26"""},
]

# ============================================================
# GENERATE GMAIL COMPOSE URL
# ============================================================
def gmail_url(email, subject, body):
    """Build Gmail compose URL with pre-filled fields."""
    if not email:
        return None
    params = {
        "view": "cm",
        "fs": "1",
        "to": email,
        "su": subject,
        "body": body
    }
    encoded = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"https://mail.google.com/mail/?{encoded}"

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  TEBELLO LELOSA — GMAIL COMPOSE DASHBOARD")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()

    # Tier 1
    tier1 = [c for c in CONTACTS if c["tier"] == 1]
    tier2 = [c for c in CONTACTS if c["tier"] == 2]

    print(f"TIER 1 — Active Engineering Recruiters ({len(tier1)} contacts):")
    print()
    for i, c in enumerate(tier1, 1):
        has_email = "✓" if c["email"] else "✗ (find email via website)"
        note = f" | {c['note']}" if c.get("note") else ""
        print(f"  {i:2d}. {c['name']:35s} {has_email}{note}")

    print()
    print(f"TIER 2 — SCM & Operations Recruiters ({len(tier2)} contacts):")
    print()
    for i, c in enumerate(tier2, 1):
        has_email = "✓" if c["email"] else "✗ (find email via website)"
        note = f" | {c['note']}" if c.get("note") else ""
        print(f"  {i:2d}. {c['name']:35s} {has_email}{note}")

    print()
    print("-" * 60)
    print()

    # Open selected
    print("Enter number to open Gmail compose (or 'all' for Tier 1):")
    print("  1-{} for Tier 1 | 'all' to open all Tier 1 | 'x' to exit".format(len(tier1) + len(tier2)))
    print()

    choice = input("Choice: ").strip().lower()

    if choice == "x":
        print("Done.")
        return

    if choice == "all":
        count = 0
        for c in tier1:
            url = gmail_url(c["email"], c["subject"], c["body"])
            if url:
                webbrowser.open(url, new=2)
                count += 1
        print(f"Opened {count} Gmail compose windows for Tier 1 recruiters.")
    elif choice.isdigit():
        idx = int(choice) - 1
        all_contacts = tier1 + tier2
        if 0 <= idx < len(all_contacts):
            c = all_contacts[idx]
            if c["email"]:
                url = gmail_url(c["email"], c["subject"], c["body"])
                webbrowser.open(url, new=2)
                print(f"Opened Gmail compose for: {c['name']}")
            else:
                print(f"No email for {c['name']}. {c.get('note', 'Find via website.')}")
        else:
            print("Invalid number.")
    else:
        print("Unknown choice.")

    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        input("Press Enter to exit...")
