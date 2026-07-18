# TEBELLO LELOSA — PROFESSIONAL JOB SEARCH ENGINE
## MASTER DIRECTIVE: QWEN AGENTIC WORKFLOW 2.0 (Trae IDE Optimized)

### 1. DIRECTIVE (The Brain)
**Role:** Senior Autonomous Systems Architect (Qwen-Optimized for Trae IDE)
**Objective:** Build and maintain Tebello Lelosa's complete professional job-search engine — profile extraction, CV generation, multi-platform job profiles, recruiter database, and automated cold-email outreach.
**Operational Principle:** Context-Aware Think-Before-Execute. Leverage Trae's project indexing and Qwen's reasoning engine to analyze workspace structure, dependencies, and existing data before generating or modifying any code.
**Quality Standards:**
- Modular, self-documenting architecture with explicit type hints.
- Atomic execution: Small, verifiable changes over massive rewrites.
- Trae-optimized: Use clean, minimal diffs for inline apply operations.

### 2. SYSTEM ARCHITECTURE
This project strictly adheres to the 5-Folder Agentic Layout to ensure scaling performance and an organized root directory:
```
📁 TebelloReborn/
├── 📁 1_Documentation/
│   ├── QWEN_DIRECTIVE.md          <-- This Master AI Directive & Log
│   └── USER_GUIDE.md              <-- Manual for human operators
├── 📁 2_Source_Data/              <-- 20 CV files, certificates, presentations (2014-2026)
├── 📁 3_Live_Reports/             <-- 11 deliverables (CVs, profiles, templates, tracker, database)
├── 📁 4_Scripts/                  <-- 12 scripts (automation, email, CV generation, job search)
├── 📁 5_Archive_and_Debug/        <-- Debug logs, temp files
├── ⚡ RUN_PIPELINE.bat            <-- Single-click master executable
├── ⚡ Open_Everything.bat         <-- One-click daily launcher (in 4_Scripts/)
└── ⚡ Auto_Send_Cold_Emails.bat   <-- Gmail SMTP automation (in 4_Scripts/)
```
**Pathing Rule:** All scripts must use relative referencing (e.g., `2_Source_Data/file.csv`) assuming execution from the Project Root. Trae's file watcher and Qwen's context resolver rely on consistent relative paths.

### 3. CODING STANDARDS & VALIDATION
1. **Data Safety Protocol (Shadow Copying):**  
   When reading live business files (`.xlsx`, `.csv`, `.db`), scripts MUST use `tempfile` and `shutil.copy2` to create a hidden background copy. Read from the copy to prevent `PermissionError` crashes if a user has the file open.
2. **The UTF-8 File Logging Standard:**  
   Never dump large validation outputs or raw string arrays into the Trae terminal. Write debug outputs natively to `5_Archive_and_Debug/debug_output_utf8.txt` to bypass terminal character limits and encoding errors.
3. **Modular File Architecture:**  
   Never build monolithic scripts. Split features into isolated modules (e.g., `data_extractor.py`, `master_builder.py`, `target_injector.py`) and chain them sequentially in `RUN_PIPELINE.bat`.
4. **Error Handling (Self-Annealing):**  
   Wrap all Python logic in global `try/except` blocks. Print clear, human-readable errors. If a data source is malformed, log the failure to this file's Execution Log and bypass the bad row instead of crashing the pipeline.

### 4. TRAE IDE & QWEN INTEGRATION PROTOCOLS
- **Context Tagging:** Use Trae's `@filename` syntax explicitly when referencing external files in chat to ensure Qwen loads the correct context.
- **Inline Editing:** Prefer surgical, function-level edits over full-file rewrites. Maintain existing indentation, comments, and import structures for clean Trae `Apply` diffs.
- **Terminal Execution:** Run validation scripts directly via Trae's integrated terminal from the Project Root. Do not assume external shell environments.
- **Session Continuity:** After completing a task, Qwen must update the `PROJECT STATE & LOG` section below before requesting the next prompt.

### 5. ORCHESTRATION (The Architect)
**Logic Sequence:**
1. **Discovery:** Index the workspace via Trae. Identify files, configs, and data sources.
2. **Strategy:** Map the implementation path. Present a "High-Level Plan" for user approval.
3. **Execution:** Generate logic in small, testable chunks. Apply via Trae's inline diff editor.
4. **Validation:** Run test scripts or integrity checks via terminal. Handle exceptions natively (Annealing Protocol).
5. **Logging:** Update the Execution Checklist & Project State Log below.

### 6. EXECUTION CHECKLIST (The Worker)
- [x] Task 1: Initialize Project Structure
  - [x] Step A: Create 5-folder agentic layout
  - [x] Step B: Move QWEN.md to 1_Documentation/QWEN_DIRECTIVE.md
  - [x] Step C: Create USER_GUIDE.md
  - [x] Step D: Create RUN_PIPELINE.bat
  - [x] Step E: Create placeholder script in 4_Scripts/
- [x] Task 2: Build Professional Profile & Job Application System
  - [x] Step A: Extract and merge all CV data (10 files, 2014-2026)
  - [x] Step B: Create LinkedIn profile improvement guide
  - [x] Step C: Create PNET, Indeed, and 22+ platform profiles
  - [x] Step D: Create modern master CV (full MD + PDF) + one-page MD
  - [x] Step E: Build daily job application tracker (25 job leads + 11 verified recruiters)
  - [x] Step F: Create daily execution pipeline script (Daily_Job_Search.bat, Open_Everything.bat)
- [x] Task 3: Cold Email Persona & Templates
  - [x] Step A: Run Q&A session to determine tone, persona, and messaging style
  - [x] Step B: Build 6 cold email templates (Recruiters, HR, Managers, Subordinates, Follow-Up, LinkedIn)
  - [x] Step C: Create daily email checklist and follow-up calendar
  - [x] Step D: Build Gmail compose dashboard (browser-based, no setup)
  - [x] Step E: Build Gmail SMTP automation (auto_send_emails.py — requires App Password)
  - [x] Step F: Source HR personnel contacts (Howden, ACTOM, Caterpillar, Bureau Veritas, Weir, thyssenkrupp)

### 7. PROJECT STATE & LOG
**Current Status:** `Live & Maintenance`
**Memory Buffer:** *(Qwen's Long-Term Context. Document critical decisions, schemas, data quirks, and architectural rules to prevent context drift across sessions.)*
- Memory Point 1: Project uses 5-Folder Agentic Layout with relative pathing from Project Root.
- Memory Point 2: All scripts must use shadow copying for data safety and UTF-8 logging.
- Memory Point 3: Tebello's phone number changed: 073 004 3460 → **078 481 8711** (updated everywhere).
- Memory Point 4: Career trajectory: CNC Programmer → Production Planner → Supply Chain Supervisor → Contract Stock Controller → Junior PE → PE → Project Officer → **Operations Foreman (current, FanMovement Oct 2025)**. Two tenures at Howden Africa (re-hired May 2023). 19+ years experience.
- Memory Point 5: Daily job application target: 5/day. Mix of job board applications + cold emails to recruiters/HR.
- Memory Point 6: **Cold email persona:** Confident & Direct, Medium length (8-12 lines), Calendar CTA, Career story as hook, One strong voice (all audiences), Values-driven, Market-related salary, One follow-up (3-5 days), Direct subject line, Languages in CV only, Connection-first opening.
- Memory Point 7: **CV file to attach:** `3_Live_Reports/Tebello_Lelosa_CV_2026.pdf` (generated by `4_Scripts/generate_cv_pdf.py`).
- Memory Point 8: **Recruiter contacts (6 verified emails):** Candice (Kontak), Dawn (cdconsult), E&D Recruiters, Hire Resolve, TRS Staffing, TAKORA.
- Memory Point 9: **HR personnel contacts found (LinkedIn — need InMail or email lookup):**
  - Yolanda Mosoeu — HR Manager, Howden Africa (his former employer — strong warm lead)
  - Lindani Ndlovu — HR Director, Howden Africa (UK-based)
  - Kgomotso Mononyane — HR Manager, ACTOM (Pty) Ltd
  - Sydney Khosa — Human Capital Manager, ACTOM
  - Modlay Davids — Talent Acquisition, Caterpillar Inc (Africa)
  - Beatrice Scharneck — HR Director, Bureau Veritas (Southern Africa)
  - Siyabonga Bhengu — HR, Bureau Veritas
  - Gugulethu Mncube — Head of HR, thyssenkrupp Uhde SA
  - Liane Beukes — HR Manager, Weir Minerals
  - Lameez Benjamin — HR Business Partner, Weir Minerals
  - Tshepiso Lekalakala — HR Leader (mining, logistics, manufacturing)
  - Tracey Jones — Mining Talent Acquisition, Johannesburg
  - Nthabeleng Mohlala — Talent Acquisition, CA Mining
- Memory Point 10: Gmail App Password required for auto_send_emails.py. Setup in `4_Scripts/GMAIL_SETUP.md`.

**Deliverables in `3_Live_Reports/` (11 files):**
| File | Purpose |
|---|---|
| `Tebello_Lelosa_CV_2026.pdf` | Master CV PDF — attach to all emails |
| `Tebello_Lelosa_Master_CV_2026.md` | Master CV source (Markdown) |
| `Tebello_Lelosa_One_Page_CV.md` | Condensed one-page CV |
| `LinkedIn_Profile_Improvements.md` | 10-section LinkedIn optimization guide |
| `PNET_Profile_Data.md` | Complete PNET profile |
| `Indeed_Profile_Data.md` | Complete Indeed profile |
| `Other_Job_Platforms_Data.md` | 22 platform profiles + master summaries |
| `Job_Application_Tracker.md` | 25 job leads + 30 recruiters + daily log |
| `Cold_Email_Templates.md` | 6 email templates (Recruiters, HR, Managers, Subordinates, Follow-Up, LinkedIn) |
| `Cold_Email_Quick_Reference.md` | One-page cheat sheet — email DNA, structure, daily routine |
| `Recruiter_Contact_Database.md` | 11 verified contacts (6 email + 5 LinkedIn HR personnel) with pre-filled emails |

**Scripts in `4_Scripts/` (12 files):**
| File | Purpose |
|---|---|
| `Open_Everything.bat` | One-click daily launcher — opens all files + job sites |
| `Daily_Job_Search.bat` | Interactive menu — choose what to open |
| `Auto_Send_Cold_Emails.bat` | Gmail SMTP automation launcher |
| `auto_send_emails.py` | Sends personalized cold emails with CV attachment, logs everything |
| `Gmail_Compose.bat` | Browser-based Gmail compose dashboard |
| `gmail_compose.py` | Generates pre-filled Gmail compose URLs |
| `GMAIL_SETUP.md` | App Password setup instructions |
| `gmail_config.json` | Configuration (requires App Password) |
| `generate_cv_pdf.py` | Converts MD CV to PDF |
| `daily_job_search.py` | Opens 11 job boards + 6 recruiter pages |
| `read_new_cvs.py` | Extracts text from .docx CV files |
| `placeholder.py` | Template script |

**Execution Log:** *(Append chronological milestones. Most recent at the top.)*
- `2026-04-09`: Sourced 13 HR personnel contacts at target companies (Howden, ACTOM, Caterpillar, Bureau Veritas, Weir, thyssenkrupp, CA Mining). All have LinkedIn profiles. Yolanda Mosoeu (HR Manager, Howden Africa) is strongest — former employer, warm lead.
- `2026-04-09`: Built Gmail SMTP automation. auto_send_emails.py sends personalized cold emails to verified recruiter contacts only (6 recruiters), attaches CV PDF, logs everything. App Password setup required. Auto_Send_Cold_Emails.bat launcher.
- `2026-04-09`: Completed cold email Q&A. Built 6 templates (Recruiters, HR, Managers, Subordinates, Follow-Up, LinkedIn). Created daily email checklist and follow-up calendar.
- `2026-04-09`: Rebuilt recruiter database — every entry has confirmed contact method. 6 verified emails + 5 LinkedIn contacts. No "find it yourself" entries.
- `2026-04-09`: Converted master CV to PDF (`Tebello_Lelosa_CV_2026.pdf`, 11 KB). Updated all scripts and templates to reference PDF.
- `2026-04-08`: Built daily job application system. 25 job leads + 30 recruiters sourced. Created Job_Application_Tracker.md, Daily_Job_Search.bat, daily_job_search.py.
- `2026-04-08`: Merged 3 new CV files (2025/2026). Updated all 6 deliverables with FanMovement role, Howden re-hire, new phone, DuPont cert, AutoCAD skill.
- `2026-04-07`: Created LinkedIn guide, PNET profile, Indeed profile, 22-platform guide, master CV, one-page CV.
- `2026-04-07`: Project initialized. Created folder structure, USER_GUIDE.md, RUN_PIPELINE.bat, placeholder script.
```
