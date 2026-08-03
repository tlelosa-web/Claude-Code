# Gmail SMTP Automation Setup

## One-Time Setup (2 minutes)

1. Go to: https://myaccount.google.com/security
2. Make sure **2-Step Verification** is ON (required for App Passwords)
3. In the search bar at the top, type: **App Passwords**
4. Click **App Passwords** → Name it: **Job Search**
5. Google generates a **16-character password** — copy it
6. Open `gmail_config.json` (same folder as this file)
7. Paste the password where it says `"YOUR_APP_PASSWORD_HERE"`
8. Save the file

## Security Notes

- `gmail_config.json` is **not committed** to any version control
- The App Password only gives send-only access to your Gmail
- Revoke it anytime from myaccount.google.com → App Passwords → Delete
- Your main Gmail password is **never** stored anywhere

## How It Works

1. Script reads contacts from `Recruiter_Contact_Database.md`
2. Sends personalized cold emails via Gmail SMTP
3. Attaches `Tebello_Lelosa_CV_2026.pdf` automatically
4. Logs every action to `3_Live_Reports/Email_Send_Log.md`
5. **Only sends to recruiter contacts** — zero interaction with your personal contacts

## Daily Usage

```
Double-click: 4_Scripts\Auto_Send_Cold_Emails.bat
```

It will:
- Show you which contacts will be emailed (preview)
- Ask for confirmation before sending
- Send in batches of 5 (your daily target)
- Log everything automatically
