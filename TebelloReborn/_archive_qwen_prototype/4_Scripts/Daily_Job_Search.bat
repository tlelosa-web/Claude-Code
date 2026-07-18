@echo off
title Daily Job Search ^& Cold Email Pipeline
echo ============================================================
echo   TEBELLO LELOSA - DAILY JOB SEARCH ^& COLD EMAIL PIPELINE
echo   Target: 5 Applications/Outreaches Per Day
echo   Date: %date%
echo ============================================================
echo.

cd /d "%~dp0.."

echo [STEP 1] Your Daily Toolkit:
echo.
echo   1. Job_Application_Tracker.md       - Track all applications
echo   2. Cold_Email_Templates.md          - 6 pre-written email templates
echo   3. Recruiter_Contact_Database.md    - 30 recruiters with pre-filled emails
echo   4. Tebello_Lelosa_CV_2026.pdf         - Your CV (PDF — attach this)
echo.
pause

echo.
echo [STEP 2] Quick Links - Copy and paste these into your browser:
echo.
echo JOBS:
echo   PNet Supply Chain:     https://www.pnet.co.za/jobs/supply-chain/in-johannesburg
echo   PNet Project Eng:      https://www.pnet.co.za/jobs/project-engineer/in-johannesburg
echo   CareerJunction ProjEng: https://www.careerjunction.co.za/jobs/project-engineer/gauteng
echo   CareerJunction ProdPlan: https://www.careerjunction.co.za/jobs/production-planner/johannesburg-region
echo   CareerJunction OpsMgr: https://www.careerjunction.co.za/jobs/operations-manager/gauteng
echo   Careerjet Ops Foreman: https://www.careerjet.co.za/operation-foreman-jobs/Gauteng
echo   Careerjet ProjEng:     https://www.careerjet.co.za/project-engineer-jobs/Gauteng
echo   Indeed Mech Engineer:  https://za.indeed.com/q-mechanical-engineer-jobs.html
echo   LinkedIn ProjEng:      https://www.linkedin.com/jobs/search/?keywords=project%%20engineer^&location=South%%20Africa
echo   LinkedIn OpsMgr:       https://www.linkedin.com/jobs/search/?keywords=operations%%20manager^&location=South%%20Africa
echo   LinkedIn SCM:          https://www.linkedin.com/jobs/search/?keywords=supply%%20chain%%20manager^&location=South%%20Africa
echo.
echo RECRUITERS (Cold Email Targets):
echo   Kontak Recruitment:    https://kontak.co.za
echo     Email: recruit@cdconsult.co.za  Phone: +27 11 431 3542
echo   TRS Staffing Eng:      https://www.trsstaffing.com/engineering-staffing-and-recruitment-agency-in-johannesburg-south-africa
echo   TRS Staffing Mfg:      https://www.trsstaffing.com/manufacturing-staffing-and-recruitment-agency-in-johannesburg-south-africa
echo   Technical Placements:  https://www.technicalplacements.co.za
echo   EDM Recruitment:       https://edm.co.za  Email: info@edm.co.za
echo   Network Recruitment:   https://www.networkrecruitment.co.za  Phone: +27 12 348 4940
echo   TAKORA:                https://www.takora.co.za  Email: lThandiswa@takora.co.za
echo.
pause

echo.
echo [STEP 3] Choose your action:
echo.
echo   A - Open all job search pages in browser
echo   B - Open all recruiter websites
echo   C - Open Job Application Tracker
echo   D - Open Cold Email Templates
echo   E - Open Recruiter Contact Database (pre-filled emails)
echo   F - Open Master CV
echo   G - Open ALL files at once
echo   X - Exit
echo.
set /p choice="Enter choice (A/B/C/D/E/F/G/X): "

if /i "%choice%"=="A" goto openjobs
if /i "%choice%"=="B" goto openrecruiters
if /i "%choice%"=="C" goto opentracker
if /i "%choice%"=="D" goto openemails
if /i "%choice%"=="E" goto openrecdb
if /i "%choice%"=="F" goto opencv
if /i "%choice%"=="G" goto openall
if /i "%choice%"=="X" goto end

:openjobs
echo.
echo Opening job search pages...
start "" "https://www.pnet.co.za/jobs/supply-chain/in-johannesburg"
start "" "https://www.careerjunction.co.za/jobs/project-engineer/gauteng"
start "" "https://www.careerjunction.co.za/jobs/production-planner/johannesburg-region"
start "" "https://www.careerjet.co.za/operation-foreman-jobs/Gauteng"
start "" "https://za.indeed.com/q-mechanical-engineer-jobs.html"
echo Done! Review each page for new listings.
pause
goto end

:openrecruiters
echo.
echo Opening recruiter websites...
start "" "https://kontak.co.za"
start "" "https://www.trsstaffing.com/engineering-staffing-and-recruitment-agency-in-johannesburg-south-africa"
start "" "https://www.technicalplacements.co.za"
start "" "https://edm.co.za"
start "" "https://www.networkrecruitment.co.za"
echo Done! Check for new roles and submit applications.
pause
goto end

:opentracker
echo.
echo Opening Job Application Tracker...
start "" "%~dp0..\3_Live_Reports\Job_Application_Tracker.md"
goto end

:openemails
echo.
echo Opening Cold Email Templates...
start "" "%~dp0..\3_Live_Reports\Cold_Email_Templates.md"
goto end

:openrecdb
echo.
echo Opening Recruiter Contact Database (with pre-filled emails)...
start "" "%~dp0..\3_Live_Reports\Recruiter_Contact_Database.md"
goto end

:opencv
echo.
echo Opening Master CV (PDF)...
start "" "%~dp0..\3_Live_Reports\Tebello_Lelosa_CV_2026.pdf"
goto end

:openall
echo.
echo Opening everything...
start "" "%~dp0..\3_Live_Reports\Job_Application_Tracker.md"
start "" "%~dp0..\3_Live_Reports\Cold_Email_Templates.md"
start "" "%~dp0..\3_Live_Reports\Recruiter_Contact_Database.md"
start "" "%~dp0..\3_Live_Reports\Tebello_Lelosa_CV_2026.pdf"
start "" "https://www.pnet.co.za/jobs/supply-chain/in-johannesburg"
start "" "https://www.careerjunction.co.za/jobs/project-engineer/gauteng"
start "" "https://www.careerjet.co.za/operation-foreman-jobs/Gauteng"
start "" "https://kontak.co.za"
start "" "https://www.trsstaffing.com/engineering-staffing-and-recruitment-agency-in-johannesburg-south-africa"
echo Done! All files and key sites are open.
pause
goto end

:end
echo.
echo ============================================================
echo   READY TO GO! 
echo   Remember: 5 per day = 25 per week = 100+ per month
echo   Mix job applications + cold emails for best results.
echo   Track everything. Follow up after 3-5 days.
echo ============================================================
echo.
pause
