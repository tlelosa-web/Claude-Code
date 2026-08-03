# Folder Structure — As-Is Snapshot

> Actual on-disk layout of the vault, captured 2026-07-18.
> This reflects **current reality**, not the target structure described in
> [CLAUDE.md](../CLAUDE.md) or [docs/architecture.md](architecture.md).
> `node_modules/`, `.next/`, `.venv/site-packages/`, and `__pycache__/` are
> omitted for brevity.

```
Pappa T/
├── CLAUDE.md
├── AGENTS.md
├── .gitignore
├── .uploads/
│
├── .claude/
│   ├── settings.json
│   ├── settings.local.json
│   ├── commands/                  (empty — .gitkeep only)
│   └── hooks/                     (empty — .gitkeep only)
│
├── .Codex/
│   ├── agents/                    life-domain executor roster (19 files)
│   │   ├── domain.md · context.md · planner.md · architect.md
│   │   ├── executor.md · tester.md · reviewer.md · doc-writer.md · debugger.md
│   │   └── career-brand.md · finance-risk.md · identity-strengths.md
│   │       learning-capability.md · operations-systems.md
│   │       strategy-governance.md · tender-opportunities.md
│   │       venture-builder.md · wellbeing-rhythm.md
│   ├── commands/                  (empty)
│   ├── hooks/                     (empty)
│   └── worktrees/                 (empty)
│
├── docs/
│   ├── architecture.md
│   ├── api-patterns.md
│   ├── code-conventions.md
│   ├── domain-brief.md
│   ├── life-domains.md
│   ├── orchestration-model.md
│   ├── project-portfolio.md
│   ├── strengths-inventory.md
│   ├── strengths-profile.md
│   ├── brand-examples.md
│   ├── session-log.md
│   ├── todo.md
│   ├── folder-structure.md        ← this file
│   ├── decisions/
│   │   └── ADR-001-dcoe-vault-structure.md
│   ├── bugs/                      (empty)
│   ├── research/                  (empty)
│   └── specs/                     (empty)
│
├── tests/
│   ├── unit/                      (empty)
│   └── integration/                (empty)
│
├── 00_Index_&_Logs/
│   └── 00_project_index.md
├── 01_Strategic_Architecture/
│   └── strategic_framework.md
├── 02_Financial_Strategy/
│   └── trading_betting_quest.md
├── 03_Operational_Mastery/
│   └── inventory_automation.md
├── 04_Professional_Brand/
│   ├── AGENT_CORE.md
│   ├── persona_and_tone.md
│   └── professional_presence.md
├── 05_Archive/
│   └── README.md
│
├── MIMS App/                      Next.js / Supabase / Tailwind
│   ├── GEMINI.md · MIMS.txt
│   ├── .env.local · .env.local.example
│   ├── COMPLETE_SUPABASE_MIGRATION.sql
│   ├── next.config.mjs · tailwind.config.ts · tsconfig.json
│   ├── package.json · package-lock.json
│   ├── src/
│   │   ├── app/ (auth)/ (dashboard)/ globals.css · layout.tsx
│   │   ├── components/layout/
│   │   └── lib/actions/ · lib/supabase/ · lib/types.ts · middleware.ts
│   └── supabase/migrations/       001…007 (schema + RPC evolution)
│
├── IQ/                             Python — trading signal generator
│   ├── requirements.txt · signals_20260414.csv
│   ├── .qwen/settings.json(.orig)
│   ├── 1_Documentation/ (AGENT.md, README.md, QUICKSTART.txt)
│   ├── 2_Source_Data/  (indicator .txt exports)
│   ├── 3_Live_Reports/  (empty)
│   ├── 4_Scripts/      (live_data_feed.py, main.py, signal_generator.py,
│   │                     test_signal_generator.py)
│   └── 5_Archive_and_Debug/ (debug_log.txt, memory_buffer.txt)
│
├── TebelloReborn/                  Python — CV / career automation
│   ├── CLAUDE.md
│   ├── .claude/agents/             (9-role project-level roster — NOTE: this
│   │                                 duplicates the user-level roster; flagged
│   │                                 as a v3.2 rule violation, see below)
│   ├── docs/architecture.md · docs/todo.md · docs/decisions/ (empty)
│   ├── data/
│   │   ├── Tebello_Lelosa_Master_CV_2026.md
│   │   └── legacy_reference/ (Job_Application_Tracker.md, Recruiter_Contact_Database.md)
│   ├── src/  doc_gen/ · matching/ · profile/ · review/ · shared/ · vacancy_search/
│   ├── exports/                    (empty)
│   ├── tests/ unit/ integration/   (empty)
│   └── _archive_qwen_prototype/    legacy Qwen-based pipeline (scripts, CVs,
│                                    certificates, old job-search trackers)
│
├── Tenders/                         Python — SA tender monitoring
│   ├── AGENT.md · README.md · cache.db
│   ├── .venv/                       (local virtualenv, not committed logic)
│   ├── 1_Documentation/ · 2_Source_Data/  (empty)
│   ├── 3_Live_Reports/gauteng_food_tenders.txt
│   ├── 4_Scripts/
│   │   ├── find_gauteng_food_tenders.py · cache.db
│   │   └── tenders-sa/              ← UNTRACKED nested project (own .git,
│   │                                   pyproject.toml, tenders/, tests/,
│   │                                   scripts/, PRD.md) — not yet committed
│   ├── 5_Archive_and_Debug/debug_log.txt
│   └── 110320262657/                Eskom tender bid working folder
│       ├── AGENT.md + 10 role-named specialist briefs
│       │   (Alpha–Kilo: Solution Architect, OT Integration, DB Engineer,
│       │    Network/Security, PM, Service Delivery, Quality, HSE,
│       │    Commercial, Contracts/Legal, Bid/Portal Coordinator)
│       ├── 110320262657docs/        (tender pack: ITT annexures, SHE forms,
│       │                              costing schedules, clarifications)
│       ├── scratch_generate_*.py    (contracts/security/service generators)
│       ├── update_agent_finals.py
│       └── submission/              admin/ commercial/ contracts/ planning/
│                                     portal/ quality/ service/ technical/
│
├── ai-outreach-agency/              Python — separate CLAUDE.md-governed project
│   ├── CLAUDE.md
│   ├── .claude/
│   │   ├── commands/continue.md     ← the /continue command lives HERE
│   │   ├── agents/ · hooks/          (empty)
│   │   └── settings.local.json
│   ├── .env · .env.example · credentials.json · token.json
│   ├── dashboard.html · outreach.db · pyproject.toml
│   ├── docs/ (api-patterns.md, architecture.md, session-log.md, todo.md,
│   │          decisions/ADR-001-lead-store.md, ADR-002-retire-n8n.md)
│   ├── src/
│   │   ├── approval/ · asset_gen/ · dashboard/ · email_draft/
│   │   ├── lead_import/ · research/ · shared/
│   │   └── config.py · main.py
│   └── tests/ unit/ (12 files) · integration/test_full_pipeline.py
│
├── Coding/                          Misc standalone HTML/script prototypes
│   ├── COS_26.txt
│   ├── ERP App/MIMS App_v1.0.9.html
│   ├── F1 Clash Resources/           (8 crate-tracker HTML versions)
│   ├── Name Plate Program/           (xlsx procedure doc)
│   ├── Quest App/                    (Aviator + Quest Gem + QuestAi, ~20 versions)
│   └── Trading Indicator/            (Pine/indicator .txt files)
│
├── Job_Applications_and_Cold_Emails_2026-06-03.md
├── Today_Job_Action_Tracker_2026-06-03.md
├── Tebello_Lelosa_CV_Operations_Manager_2026-06-03.{docx,md,pdf}
└── Tebello_Lelosa_CV_Project_Engineer_2026-06-03.{docx,md,pdf}
```

## Deviations from the documented (CLAUDE.md) structure

- **`.claude/commands/` and `.claude/hooks/`** at the root are empty
  (`.gitkeep` only) — no slash commands or hooks are actually wired up here,
  despite CLAUDE.md describing them as active.
- **`TebelloReborn/.claude/agents/`** carries its own full 9-agent roster.
  CLAUDE.md's hard rule says the roster lives at user level
  (`~/.claude/agents/`) and project-level copies should be override-only —
  this looks like a full fork, not an override.
- **`Tenders/4_Scripts/tenders-sa/`** is an untracked nested project with its
  own `.git` — not yet integrated or committed to the vault (seen in
  `git status` as untracked).
- **`ai-outreach-agency/`** is a fully separate DCOE project (own `CLAUDE.md`,
  own agents/hooks/commands) sitting alongside the vault rather than under
  it — and is where the working `/continue` command actually lives.
- **`docs/bugs/`, `docs/research/`, `docs/specs/`, `docs/decisions/`** (partial)
  and both `tests/unit/` and `tests/integration/` at the root are present but
  empty — scaffolding without content yet.
