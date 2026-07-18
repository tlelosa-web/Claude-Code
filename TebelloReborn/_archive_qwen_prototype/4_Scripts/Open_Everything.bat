@echo off
title Tebello - Open Everything
echo Opening files and job sites...

set BASE=%~dp0..\3_Live_Reports

start "" "%BASE%\Job_Application_Tracker.md"
start "" "%BASE%\Cold_Email_Templates.md"
start "" "%BASE%\Recruiter_Contact_Database.md"
start "" "%BASE%\Cold_Email_Quick_Reference.md"
start "" "%BASE%\Tebello_Lelosa_CV_2026.pdf"
start "" "https://www.pnet.co.za/jobs/supply-chain/in-johannesburg"
start "" "https://www.careerjunction.co.za/jobs/project-engineer/gauteng"
start "" "https://www.careerjet.co.za/operation-foreman-jobs/Gauteng"
start "" "https://kontak.co.za"
start "" "https://www.trsstaffing.com/engineering-staffing-and-recruitment-agency-in-johannesburg-south-africa"

echo Done.
timeout /t 2 >nul
