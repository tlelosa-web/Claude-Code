"""
Cold Email Automation Script
Sends personalized cold emails to verified recruiter contacts via Gmail SMTP.
Attaches CV automatically. Logs every action.
Only sends to recruiter contacts — zero interaction with personal contacts.
"""
import smtplib
import json
import os
import re
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "4_Scripts", "gmail_config.json")

# ============================================================
# VERIFIED RECRUITER CONTACTS
# Only these contacts will receive emails. No personal contacts.
# ============================================================
RECRUITERS = [
    {
        "id": "R1",
        "name": "Candice Berisford-Maynard",
        "email": "candice@cdconsult.co.za",
        "company": "Kontak Recruitment / cdconsult",
        "specialization": "engineering and manufacturing placements — I saw your recent Mechanical Project Engineer posting for Boksburg",
        "tier": 1,
    },
    {
        "id": "R2",
        "name": "Dawn McIntyre",
        "email": "recruit@cdconsult.co.za",
        "company": "cdconsult / Kontak Recruitment",
        "specialization": "engineering placements across Johannesburg",
        "tier": 1,
    },
    {
        "id": "R3",
        "name": "E&D Recruiters Team",
        "email": "cv@edrecruiters.co.za",
        "company": "E&D Recruiters",
        "specialization": "engineering recruitment and recently posted Mechanical Process and Design Engineer roles",
        "tier": 1,
    },
    {
        "id": "R4",
        "name": "Hire Resolve Engineering Team",
        "email": "engineers@hireresolve.za.com",
        "company": "Hire Resolve",
        "specialization": "premier engineering recruitment",
        "tier": 1,
    },
    {
        "id": "R5",
        "name": "TRS Staffing Team",
        "email": "info@trsstaffing.com",
        "company": "TRS Staffing Solutions",
        "specialization": "world-leading engineering recruitment across South Africa",
        "tier": 1,
    },
    {
        "id": "R6",
        "name": "TAKORA Team",
        "email": "lThandiswa@takora.co.za",
        "company": "TAKORA",
        "specialization": "you're currently advertising Intermediate and Junior Project Engineer roles",
        "tier": 1,
    },
]

# ============================================================
# CAREER HOOK (used in every email)
# ============================================================
CAREER_HOOK = (
    "Over 19 years, I've earned 5 promotions across three companies — "
    "progressing from CNC Programmer to Operations Foreman, including two tenures "
    "as Project Engineer at Howden Africa where they re-hired me based on prior "
    "performance. I currently lead workshop operations at FanMovement (Pty) Ltd."
)

# ============================================================
# BUILD PERSONALIZED EMAIL
# ============================================================
def build_email(recruiter, config):
    """Build a personalized email for a recruiter."""
    subject = (
        f"Tebello Lelosa — Operations Foreman / Project Engineer "
        f"— 19 Years Experience — Gauteng"
    )

    body = f"""Dear {recruiter['name']},

I'm reaching out because your firm specializes in {recruiter['specialization']}, and my 19-year background in mechanical engineering, manufacturing operations, and project engineering aligns directly with the roles you fill.

{CAREER_HOOK}

I'm exploring new opportunities in Operations Management, Project Engineering, Supply Chain, and Production Planning. I hold a National Diploma in Mechanical Engineering (TUT) and work with Microsoft AX ERP, MS Project, AutoCAD, and Pro/Engineer.

My compensation expectation is market-related and negotiable based on the role. I'm available for a brief call on most weekdays between 08:00 and 17:00 — whatever suits your schedule.

I've attached my CV and would appreciate being added to your database for relevant opportunities.

Best regards,

{config['sender_name']}
{config['sender_phone']}
{config['gmail_address']}
{config['sender_linkedin']}"""

    return subject, body

# ============================================================
# CREATE MIME EMAIL WITH ATTACHMENT
# ============================================================
def create_mime_email(from_addr, to_addr, subject, body, cv_path, config):
    """Create a MIME email with CV attachment."""
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{config['sender_name']} <{from_addr}>"
    msg["To"] = to_addr
    msg["Subject"] = subject

    # Body
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # CV Attachment
    if os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=Tebello_Lelosa_CV_2026.pdf",
            )
            msg.attach(part)
    else:
        print(f"\n  [WARNING] CV not found at: {cv_path}")
        print("  Continuing without attachment.\n")

    return msg

# ============================================================
# SEND EMAIL VIA GMAIL SMTP
# ============================================================
def send_email(msg, from_addr, app_password):
    """Send email via Gmail SMTP."""
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_addr, app_password)
        server.send_message(msg)
        server.quit()
        return True, "Sent successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Check App Password in gmail_config.json"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

# ============================================================
# LOG EMAIL TO FILE
# ============================================================
def log_email(recruiter, subject, success, message):
    """Log email send attempt to file."""
    log_dir = os.path.join(ROOT, "3_Live_Reports")
    log_file = os.path.join(log_dir, "Email_Send_Log.md")

    os.makedirs(log_dir, exist_ok=True)

    # Create log file if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("# Cold Email Send Log\n\n")
            f.write("| Date/Time | Recruiter | Email | Subject | Status | Details |\n")
            f.write("|-----------|-----------|-------|---------|--------|---------|\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SENT" if success else "FAILED"
    # Escape pipe characters in subject
    safe_subject = subject.replace("|", "\\|")
    line = f"| {timestamp} | {recruiter['name']} ({recruiter['id']}) | {recruiter['email']} | {safe_subject} | {status} | {message} |\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

    print(f"  Logged: {recruiter['id']} - {status}")

# ============================================================
# LOAD CONFIGURATION
# ============================================================
def load_config():
    """Load Gmail configuration."""
    if not os.path.exists(CONFIG_FILE):
        print(f"\n[ERROR] Config file not found: {CONFIG_FILE}")
        print("Run GMAIL_SETUP.md instructions first.")
        return None

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if config.get("gmail_app_password") == "YOUR_APP_PASSWORD_HERE":
        print("\n[ERROR] App Password not set!")
        print("Open 4_Scripts/gmail_config.json and replace 'YOUR_APP_PASSWORD_HERE' with your Gmail App Password.")
        print("See 4_Scripts/GMAIL_SETUP.md for instructions.")
        return None

    return config

# ============================================================
# LOAD PREVIOUSLY SENT EMAILS (avoid duplicates)
# ============================================================
def load_sent_ids():
    """Load IDs of previously sent emails from log."""
    log_file = os.path.join(ROOT, "3_Live_Reports", "Email_Send_Log.md")
    sent = set()

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                for r in RECRUITERS:
                    if f"({r['id']})" in line and "| SENT |" in line:
                        sent.add(r["id"])
    return sent

# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  TEBELLO LELOSA — COLD EMAIL AUTOMATION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()

    # Load config
    config = load_config()
    if config is None:
        input("Press Enter to exit...")
        return

    # Verify CV exists
    cv_path = os.path.join(ROOT, config.get("cv_attachment_path", "3_Live_Reports/Tebello_Lelosa_CV_2026.pdf"))
    if not os.path.exists(cv_path):
        print(f"\n[WARNING] CV PDF not found at: {cv_path}")
        print("Run this first to generate it:")
        print("  python 4_Scripts/generate_cv_pdf.py")
        print()
        choice = input("Continue without CV attachment? (y/n): ").strip().lower()
        if choice != "y":
            input("Press Enter to exit...")
            return
        cv_path = ""

    # Check previously sent
    sent_ids = load_sent_ids()
    remaining = [r for r in RECRUITERS if r["id"] not in sent_ids]

    if not remaining:
        print("\nAll recruiter contacts have been emailed!")
        print("Consider resetting the log file or adding new contacts.")
        input("Press Enter to exit...")
        return

    # Show preview
    daily_limit = config.get("daily_limit", 5)
    batch = remaining[:daily_limit]

    print(f"READY TO SEND ({len(batch)} emails today):\n")
    for i, r in enumerate(batch, 1):
        print(f"  {i}. [{r['id']}] {r['name']:40s} {r['email']}")

    print(f"\n  Daily limit: {daily_limit}")
    print(f"  Remaining after today: {len(remaining) - len(batch)}")
    print(f"  CV attached: {'Yes' if cv_path and os.path.exists(cv_path) else 'No'}")
    print()

    preview = input("Preview emails before sending? (y/n): ").strip().lower()
    if preview == "y":
        for i, recruiter in enumerate(batch, 1):
            subject, body = build_email(recruiter, {
                "sender_name": config["sender_name"],
                "gmail_address": config["gmail_address"],
                "sender_phone": config["sender_phone"],
                "sender_linkedin": config["sender_linkedin"],
            })
            print(f"\n{'=' * 60}")
            print(f"  EMAIL {i}/{len(batch)} — {recruiter['id']} {recruiter['name']}")
            print(f"  To: {recruiter['email']}")
            print(f"  Subject: {subject}")
            print(f"{'=' * 60}")
            print(body)
            print(f"{'=' * 60}")
            print()
            if i < len(batch):
                input("Press Enter for next email...")

        input("Press Enter to continue...")

    confirm = input("Send these emails? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted. No emails sent.")
        input("Press Enter to exit...")
        return

    # Send emails
    print("\nSending...\n")
    success_count = 0
    fail_count = 0

    for recruiter in batch:
        print(f"  [{recruiter['id']}] Sending to {recruiter['name']}...", end=" ")

        subject, body = build_email(recruiter, {
            "sender_name": config["sender_name"],
            "company": recruiter["company"],
            "gmail_address": config["gmail_address"],
            "sender_phone": config["sender_phone"],
            "sender_linkedin": config["sender_linkedin"],
        })

        msg = create_mime_email(
            config["gmail_address"],
            recruiter["email"],
            subject,
            body,
            cv_path,
            {
                "sender_name": config["sender_name"],
            }
        )

        success, message = send_email(msg, config["gmail_address"], config["gmail_app_password"])
        log_email(recruiter, subject, success, message)

        if success:
            success_count += 1
            print("SENT")
        else:
            fail_count += 1
            print(f"FAILED — {message}")

    print("\n" + "=" * 60)
    print(f"  SUMMARY: {success_count} sent | {fail_count} failed | {len(batch)} total")
    print("=" * 60)
    print()
    print(f"Log saved to: 3_Live_Reports/Email_Send_Log.md")
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. No changes made.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        input("Press Enter to exit...")
