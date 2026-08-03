"""
Daily Job Search Refresh Script
Searches multiple job platforms and appends new leads to the tracker.
Run this daily before applying to get fresh leads.
"""
import os
import webbrowser
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKER = os.path.join(ROOT, "3_Live_Reports", "Job_Application_Tracker.md")

SEARCH_URLS = [
    ("PNet - Supply Chain JHB", "https://www.pnet.co.za/jobs/supply-chain/in-johannesburg"),
    ("PNet - Project Engineer JHB", "https://www.pnet.co.za/jobs/project-engineer/in-johannesburg"),
    ("CareerJunction - Project Engineer", "https://www.careerjunction.co.za/jobs/project-engineer/gauteng"),
    ("CareerJunction - Production Planner", "https://www.careerjunction.co.za/jobs/production-planner/johannesburg-region"),
    ("CareerJunction - Operations Manager", "https://www.careerjunction.co.za/jobs/operations-manager/gauteng"),
    ("Careerjet - Operations Foreman", "https://www.careerjet.co.za/operation-foreman-jobs/Gauteng"),
    ("Careerjet - Project Engineer", "https://www.careerjet.co.za/project-engineer-jobs/Gauteng"),
    ("Indeed - Mechanical Engineer", "https://za.indeed.com/q-mechanical-engineer-jobs.html"),
    ("LinkedIn Jobs - Project Engineer SA", "https://www.linkedin.com/jobs/search/?keywords=project%20engineer&location=South%20Africa"),
    ("LinkedIn Jobs - Operations Manager SA", "https://www.linkedin.com/jobs/search/?keywords=operations%20manager&location=South%20Africa"),
    ("LinkedIn Jobs - Supply Chain Manager SA", "https://www.linkedin.com/jobs/search/?keywords=supply%20chain%20manager&location=South%20Africa"),
]

RECRUITER_URLS = [
    ("Kontak Recruitment", "https://kontak.co.za"),
    ("TRS Staffing Engineering", "https://www.trsstaffing.com/engineering-staffing-and-recruitment-agency-in-johannesburg-south-africa"),
    ("TRS Staffing Manufacturing", "https://www.trsstaffing.com/manufacturing-staffing-and-recruitment-agency-in-johannesburg-south-africa"),
    ("Technical Placements", "https://www.technicalplacements.co.za"),
    ("EDM Recruitment", "https://edm.co.za"),
    ("Network Recruitment", "https://www.networkrecruitment.co.za"),
]

def main():
    print("=" * 60)
    print(f"  DAILY JOB SEARCH REFRESH - {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)
    print()
    print(f"Opening {len(SEARCH_URLS)} job search pages and {len(RECRUITER_URLS)} recruiter pages...")
    print()
    print("JOBS (review each and note new listings):")
    for i, (name, url) in enumerate(SEARCH_URLS, 1):
        print(f"  {i:2d}. {name}")
        print(f"      {url}")
    print()
    print("RECRUITERS (check for new roles, reach out):")
    for i, (name, url) in enumerate(RECRUITER_URLS, 1):
        print(f"  {i:2d}. {name}")
        print(f"      {url}")
    print()
    
    choice = input("Open all job search pages in browser? (y/n): ").strip().lower()
    if choice == 'y':
        print("Opening job search pages...")
        for name, url in SEARCH_URLS:
            webbrowser.open(url, new=2)
        print("Opening recruiter pages...")
        for name, url in RECRUITER_URLS:
            webbrowser.open(url, new=2)
        print("Done! Review each page and add new leads to the tracker.")
    
    print()
    print(f"Tracker file: {TRACKER}")
    print("Add new leads to the ACTIVE LEADS table, then apply to 5 per day.")
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        input("Press Enter to exit...")
