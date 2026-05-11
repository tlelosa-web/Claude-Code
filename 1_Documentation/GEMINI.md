# [PROJECT NAME]
# MASTER DIRECTIVE: AGENTIC WORKFLOW 2.0

## 1. DIRECTIVE (The Brain)
**Role:** Senior Autonomous Systems Architect.
**Objective:** [Briefly define the primary operational goal of this project].
**Operational Principle:** Think-Before-Execution. Analyze the workspace context, directory structure, and existing data before generating any output.
**Quality Standards:** 
- Modular, self-documenting architecture.
- Atomic execution: Small, verifiable changes over massive code dumps.

## 2. SYSTEM ARCHITECTURE
This project strictly adheres to the 5-Folder Agentic Layout to ensure scaling performance and an organized root directory:

📁 [Project Root]/
├── 📁 1_Documentation/
│   ├── GEMINI.md                  <-- The Master AI Directive & Log
│   └── USER_GUIDE.md              <-- Manual for human operators
├── 📁 2_Source_Data/              <-- Raw inputs, CSV exports, DB dumps
├── 📁 3_Live_Reports/             <-- Final generated outputs, dashboards
├── 📁 4_Scripts/                  <-- Python logic, automation scripts
├── 📁 5_Archive_and_Debug/        <-- Obsolete tools, temp logs, tests
└── ⚡ RUN_PIPELINE.bat            <-- Single-click master executable

*Note: All python scripts must use relative referencing (e.g., `2_Source_Data/file.csv`) assuming execution from the Project Root.*

## 3. CODING STANDARDS & VALIDATION
**1. Data Safety Protocol (Shadow Copying):**
When reading from standard live business files (like `.xlsx`), the script MUST use `tempfile` and `shutil.copy2` to create a hidden background copy, and read from that copy instead. This prevents `PermissionError` crashes if a human user has the file open.

**2. The UTF-8 File Logging Standard:**
Never dump large data validation outputs or raw string arrays into the terminal. Always write debug outputs natively to a `debug_output_utf8.txt` file stored in `5_Archive_and_Debug/` to bypass Windows terminal character limits and encoding errors.

**3. Modular File Architecture:**
Never build monolithic "do-everything" scripts. Split features into isolated modules (e.g., Data Extractors, Master Builders, Targeted Injectors) and chain them together sequentially in the `RUN_PIPELINE.bat` file.

**4. Error Handling (Self-Annealing):**
All Python scripts must be wrapped in global `try/except` blocks that print clear, human-readable errors without failing silently. If a data source is malformed, the script should cleanly log the failure into the `GEMINI.md` Execution Log and bypass the bad row instead of crashing the pipeline.

## 4. ORCHESTRATION (The Architect)
**Logic Sequence:**
1. **Discovery:** Index the workspace. Identify all relevant files, configurations, and data sources.
2. **Strategy:** Map out the implementation path and present a "High-Level Plan" for user approval before modifying data.
3. **Execution:** Write logic/code in small, testable chunks.
4. **Validation:** Run test scripts or data-integrity checks after every change. Handle exceptions natively (Annealing Protocol).
5. **Logging:** Update the Execution list and Project Log below.

## 5. EXECUTION CHECKLIST (The Worker)
- [x] **Task 1:** Reorganize repository to GEMINI 5-folder layout
    - [x] Step A: Identify core application code, raw inputs, outputs, and archive material
    - [x] Step B: Move backend/frontend to `4_Scripts/`, raw sources to `2_Source_Data/`, outputs to `3_Live_Reports/`, and docs to `1_Documentation/`
- [x] **Task 2:** Create root orchestration and repository entrypoint
    - [x] Step A: Add `RUN_PIPELINE.bat`
    - [x] Step B: Add root `README.md` and `.gitignore`

## 6. PROJECT STATE & LOG
**Current Status:** Reorganized / Architecture review complete
**Memory Buffer:**
*Use this section as the AI's "Long-Term Memory." Document critical decisions, database schemas, odd data quirks, and architectural rules so context is never lost across sessions.*
- Memory Point 1: NamePlate Tool is a FastAPI + React/Vite app for motor nameplate PDF and test record sheet generation.
- Memory Point 2: Raw motor spec PDFs and Excel procedure sources live under `2_Source_Data/raw_sources`.
- Memory Point 3: Application code lives under `4_Scripts/backend` and `4_Scripts/frontend`.

**Execution Log:**
*Append chronological milestones here. Most recent at the top.*
- 2026-05-11: Final-polished FM4043 Test Record Sheet hierarchy to metadata-first layout, rebuilt motor spec block, consolidated phase-reading table, and regenerated validated output.
- 2026-05-11: Rebuilt FM4043 Test Record Sheet template geometry, cleaned unit/date formatting, corrected table headers, and regenerated validated FM4043 output.
- 2026-05-07: Repository reorganized to GEMINI 5-folder layout and documentation updated.
