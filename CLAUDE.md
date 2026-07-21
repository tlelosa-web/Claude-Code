# CLAUDE.md — Project Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 1.0 | Based on: SOPS CLAUDE.md v3.2 | Owner: Tebello Lelosa

> Loaded at the start of every Claude Code session opened inside this project
> folder. Takes precedence over the root hub `CLAUDE.md`
> (`C:\Dev\Operations\CLAUDE.md`) for anything under this project — see hub
> hard rule 1. Onboarded to DCOE 2026-07-15 per
> `docs/decisions/ADR-001-dcoe-onboarding.md`.

**At the start of every session, read
`~/.claude/plugins/marketplaces/tlelosa-claude-config/dcoe-roster/CORE.md`
and treat its contents as part of this project's operating instructions** —
it carries the shared DCOE architecture, sub-agent roster, model routing,
and universal hard rules (ADR-007, decided in the `Operations` hub). A
session opened directly in this project folder does **not** load the root
hub's `CLAUDE.md`, so the DCOE/roster content has to be sourced from
`CORE.md` directly rather than via a pointer to root — `@import` can't reach
that path either (verified 2026-07-18), so this is a plain read instruction,
not an automatic import. Follow it explicitly each session.

-----

## 📁 PROJECT OVERVIEW

```
Project:     Nameplate & Test Sheet (NamePlate Tool)
Type:        Full-stack desktop web app (local-only)
Stack:       FastAPI (Python) + ReportLab/pypdf/pdfplumber backend ·
             React 19 + Vite frontend
Deployment:  Local Windows desktop, launched via RUN_PIPELINE.bat /
             "Nameplate Tool.lnk" — backend on uvicorn, frontend on
             localhost:5173 (Vite dev) or built static bundle
Runtime:     Python 3.11+ (see 4_Scripts/backend/requirements.txt) ·
             Node (see 4_Scripts/frontend/package.json)
Inference:   Model routing, effort tiers, and escalation rules follow the
             standing policy in `CORE.md` § Model routing (see the read
             instruction above) — not duplicated here.
Owner:       Tebello Lelosa
```

**What it does:** generates two PDF outputs from one data-entry form — a
motor **Nameplate** and a **Test Record Sheet** — for Fan Movement's fan/motor
assemblies. Source concept: the `NAME PLATE PROCEDURE` Excel workbook
(`NamePlateProc` tab, `Info+Data Entry Form`).

See @README.md for the folder-layout overview and @1_Documentation/USER_GUIDE.md
for the operator manual.

-----

## 🗂️ TWO LAYOUTS, ONE PROJECT

This project predates DCOE and already uses a **5-folder data/pipeline
layout** (`1_Documentation/` → `2_Source_Data/` → `3_Live_Reports/` →
`4_Scripts/` → `5_Archive_and_Debug/`), documented in
`1_Documentation/GEMINI.md` (legacy AI-brain file from before this project
used Claude Code — kept for history, superseded by this CLAUDE.md for Claude
sessions).

DCOE's `docs/` structure (`todo.md`, `specs/`, `decisions/`, `bugs/`,
`research/`, `session-log.md`) sits **alongside** that layout, not inside it —
same relationship the root hub has with its own project folders. Application
source stays under `4_Scripts/backend` and `4_Scripts/frontend`; planning
artifacts go in `docs/`. Do not move application code into the DCOE layout or
vice versa.

-----

## ⚙️ ESSENTIAL COMMANDS

```bash
# Backend (FastAPI) — from 4_Scripts/backend
pip install -r requirements.txt
uvicorn main:app --reload            # Dev server

# Frontend (React/Vite) — from 4_Scripts/frontend
npm install
npm run dev                          # Dev server (localhost:5173)
npm run build
npm run lint

# Full pipeline launch (both backend + frontend)
RUN_PIPELINE.bat                     # From project root

# Before every commit:
# Frontend →  npm run lint
# Backend  →  no test runner configured yet — see docs/todo.md
```

-----

## 🏗️ DCOE AGENT ARCHITECTURE

Same architecture as every DCOE project — full description in `CORE.md` §
DCOE Agent Architecture and § Sub-agent roster (see the read instruction
above). The 9-agent roster is deployed once at user level
(`~/.claude/agents/`) and is active automatically here. Not duplicated in
this file.

### DCOE Rules (project-specific reminders)

1. **Domain Agent** confirms scope before touching frontend *and* backend in
   the same task — this app has a strict payload-shape contract between
   `App.jsx`'s `TestLinePayload`-shaped objects, `main.py`'s
   `TestLinePayload` pydantic model, and `pdf_generator.py`'s table
   renderer. Changing one without checking the other two breaks PDF output
   silently (no shared type system across the Python/JS boundary).
2. **Context Agent** writes the plan to `docs/specs/` — never the code.
3. If acceptance criteria are unclear → **STOP and ask** (per hub hard rule
   8). This app has no formal test suite gating changes yet, so unclear
   scope is easy to ship broken.

-----

## 📐 ARCHITECTURE NOTES

- **Data flow:** React form state (`App.jsx`) → `buildRequestPayload()` →
  FastAPI endpoint (`main.py`) → `_normalise_test_lines()` fills blanks from
  order-level fallback values → `generate_nameplate_pdf()` /
  `generate_test_record_sheet()` (`pdf_generator.py`) → PDF bytes returned to
  browser. No database — every save is a stateless request/response producing
  a PDF; `doc_history.json` is just a log of what was generated, not a
  source of truth.
- **Test Sheet Fan Lines:** an order can have multiple identical fans, each
  needing its own row of measured readings (motor serial, blade pitch, tacho
  serial, speed, currents, voltages, connection) on the Test Record Sheet.
  The PDF (`pdf_generator.py` `test_line_row()`) has always rendered this as
  **one table, one row per fan** (`MAX_ROWS = 20`). The frontend's `Add Fan`
  UI should mirror that — a compact table, not a duplicated full-form panel
  per fan (see `docs/decisions/` / `docs/specs/` for the fix that aligned
  these).
- **Offline-first:** matches hub/SOPS convention — no CDN dependencies, no
  internet required at runtime.
- **Env vars:** `VITE_API_BASE` (frontend, `.env` in `4_Scripts/frontend`)
  points the React app at the FastAPI backend origin.

-----

## 🧪 TESTING STANDARDS

No TDD gate exists yet for this project (unlike SOPS). `tests/` at project
root currently holds ad-hoc manual-check scripts (`autofill_tests.py`,
`check_api.py`, `check_connection.py`, `inspect_excel.py`,
`test_read_excel.py`), not an automated pytest/vitest suite. Building a real
suite is tracked in `docs/todo.md` — not a blocker for small fixes, but any
non-trivial backend change should be manually verified against a generated
PDF before considered done (see root skill `/verify`).

-----

## 🔑 CONTEXT MANAGEMENT

Same discipline as every DCOE project — see root `CLAUDE.md` § Context
Management. `docs/todo.md` is rewritten at the end of every project-level
task (anti-drift pattern).

-----

## 📂 DIRECTORY STRUCTURE

```
3. Nameplate & Test Sheet/
├── CLAUDE.md                    ← You are here (project brain)
├── README.md                    ← Folder-layout overview
├── RUN_PIPELINE.bat             ← Launches backend + frontend
├── 1_Documentation/             ← GEMINI.md (legacy), USER_GUIDE.md, etc.
├── 2_Source_Data/                ← Raw motor-spec / Excel procedure sources
├── 3_Live_Reports/               ← Generated nameplate/test-sheet PDFs
├── 4_Scripts/
│   ├── backend/                 ← FastAPI app (main.py, pdf_generator.py, …)
│   └── frontend/                ← React/Vite app (src/App.jsx, …)
├── 5_Archive_and_Debug/          ← Legacy/obsolete files, debug logs
├── docs/                         ← DCOE planning layer (new, 2026-07-15)
│   ├── todo.md
│   ├── session-log.md
│   ├── decisions/                ← ADR log (ADR-001-*.md, project-scoped)
│   ├── bugs/
│   ├── research/
│   └── specs/
├── .claude/
│   ├── commands/continue.md      ← /continue — project session resume
│   └── settings.json             ← Allow/deny permission rules
└── tests/                        ← Ad-hoc manual-check scripts (not a suite yet)
```

-----

## ⚠️ HARD RULES — NEVER VIOLATE

Inherits the universal hard rules from `CORE.md` (see the read instruction
above) — hub-specific rules in root `CLAUDE.md` (e.g. the no-git-repo-at-root
rule) don't apply to this project, which has its own git repo. Project-
specific additions:

1. **Frontend/backend payload shape is a contract.** Any change to a
   `test_lines` field name/shape must be made in `App.jsx`,
   `main.py`'s `TestLinePayload`, and `pdf_generator.py`'s row renderer
   together, in the same task — never one file in isolation.
2. **No DB migrations to reason about** — this app is stateless
   request→PDF. Don't invent persistence without a deliberate decision
   (ADR) — it's not part of the current design.
3. **Ask before deleting** anything under `2_Source_Data/`, `3_Live_Reports/`,
   or `doc_history.json` — matches hub hard rule 4 on production/data paths.

-----

*Last review: 2026-07-15 — Tebello Lelosa (initial DCOE onboarding)*
