# AGENTS.md - TebelloReborn Project Brain

# DCOE Agent Architecture: Domain -> Context -> Orchestrate -> Execute

> This file is the single source of truth for TebelloReborn.
> The folder is a personal operating system for improving Tebello's life, identifying strengths, organizing projects, and turning useful work into career, personal-growth, and business outcomes.

---

## Project Overview

```
Project:     TebelloReborn
Type:        Personal operating system + project/business incubator
Owner:       Tebello Lelosa
Location:    South Africa
Role:        Operations Foreman / Strategic Operations Builder
Core Goal:   Improve Tebello's life by identifying strengths and converting existing projects into growth, income, and strategic leverage.
```

This workspace contains career material, operational automation, business/project experiments, financial/risk tools, and strategic notes. All work must preserve important personal information and turn scattered material into usable systems.

Core docs:

- `docs/domain-brief.md`: active DCOE domain classification.
- `docs/todo.md`: live task queue.
- `docs/life-domains.md`: life/project domain map.
- `docs/strengths-inventory.md`: evolving strengths and leverage map.
- `docs/session-log.md`: chronological session memory.

---

## DCOE Rules

Every meaningful task follows this sequence:

1. **Domain**: classify what kind of life/project problem this is.
2. **Context**: load only the relevant files and facts.
3. **Orchestrate**: decide which specialist executor owns each part.
4. **Execute**: complete one bounded task with a clear output and verification.

Hard rules:

- Domain before planning.
- Context before implementation.
- No large multi-file work without a plan.
- One task equals one clear output.
- Preserve source data and personal records.
- Never expose or hardcode secrets.
- Update `docs/todo.md` after completed work.
- Update `docs/session-log.md` when durable context changes.
- The orchestrator coordinates; executors build, analyze, or maintain.

---

## Orchestrator Role

Codex acts as the orchestrator for TebelloReborn.

The orchestrator:

- Classifies the active domain.
- Loads targeted context.
- Selects the right executor agent.
- Keeps work atomic.
- Maintains system memory.
- Integrates outputs into the broader life architecture.

The orchestrator does not allow one generic agent to handle everything. Each executor must operate inside its domain and report back in DCOE format.

---

## Life Domains

| Domain | Purpose | Primary Folder(s) | Executor Agent |
|---|---|---|---|
| Identity & Strengths | Identify Tebello's strengths, values, story, decision style, and leverage points. | `docs/`, `04_Professional_Brand/` | `identity-strengths` |
| Career & Professional Brand | CV, LinkedIn, job search, recruiter outreach, career positioning. | `TebelloReborn/`, `04_Professional_Brand/` | `career-brand` |
| Operations & Automation | Manufacturing, inventory, ERP, scripts, shop-floor systems. | `MIMS App/`, `03_Operational_Mastery/` | `operations-systems` |
| Business & Ventures | Turn projects into services, products, workflows, or income streams. | all project folders | `venture-builder` |
| Finance & Risk | Trading, betting, bankroll, personal finance, risk management. | `02_Financial_Strategy/`, `IQ/` | `finance-risk` |
| Governance & Strategy | Legal, fiduciary, architecture, decision systems, long-range planning. | `01_Strategic_Architecture/` | `strategy-governance` |
| Learning & Capability | Skills, tools, coding growth, AI workflows, technical learning. | all folders | `learning-capability` |
| Wellbeing & Rhythm | Energy, routines, boundaries, recovery, consistency. | `docs/` | `wellbeing-rhythm` |
| Tender & Opportunity Engine | Tender discovery, qualification, pursuit, and pipeline discipline. | `Tenders/` | `tender-opportunities` |

---

## Existing Project Map

- `TebelloReborn/`: professional job-search engine, CV generation, recruiter contact database, outreach automation.
- `MIMS App/`: Next.js/Supabase manufacturing resource planning app, currently pointed toward Stage 3 shop-floor execution.
- `IQ/`: IQ Option signal generator with market-regime filtering and risk management.
- `Tenders/`: tender automation/project workspace.
- `00_Index_&_Logs/`: vault index and project timeline.
- `01_Strategic_Architecture/`: governance and fiduciary strategy.
- `02_Financial_Strategy/`: financial/risk notes and BettingQuest context.
- `03_Operational_Mastery/`: MIMS, inventory automation, hardware/niche tooling.
- `04_Professional_Brand/`: persona, professional presence, voice, brand strategy.
- `05_Archive/`: inactive or retained material.

---

## Career Engine (Job Search) — Status Snapshot

### Domain
Career & Professional Brand

### Canonical task queue (where “what to do next” lives)
- `docs/todo.md` (vault-wide orchestration queue)

### System assets already built (evidence)
- Master CV (source): `TebelloReborn/3_Live_Reports/Tebello_Lelosa_Master_CV_2026.md`
- Job + outreach tracker: `TebelloReborn/3_Live_Reports/Job_Application_Tracker.md`
  - Contains a large “ACTIVE LEADS” list (jobs + recruiters) and email templates
  - Daily log + weekly stats sections exist
- Verified recruiter contact database (ready-to-send emails): `TebelloReborn/3_Live_Reports/Recruiter_Contact_Database.md`
  - Includes confirmed emails + pre-filled personalized outreach messages

### Current execution state (where you are right now)
- The “engine” is **built**, but the tracker shows **execution hasn’t started or hasn’t been logged yet**:
  - Weekly stats currently show **0 applications / 0 recruiter emails / 0 interviews / 0 responses**
  - Daily log entries are blank for the last logged week

### Decision required: current strategy (pick one primary lane for the next 7–14 days)
1. **Volume lane**: 5 applications/outreaches per day (optimize for throughput + consistency)
2. **Warm lead lane**: prioritize warmest HR/recruiter targets first (optimize for response rate)
3. **Hybrid lane**: 2 warm contacts + 3 applications per day (balance response + volume)

### Next recommended task (if the goal is to regain clarity fast)
Run a 30-minute “restart” pass:
1. Pick the strategy lane above.
2. Send the first 5 emails/applications.
3. Log them immediately in `Job_Application_Tracker.md` (DAILY LOG + WEEKLY STATS).

---

## Executor Contract

Every executor must return:

1. Domain handled.
2. Context used.
3. Output produced.
4. Strength or leverage discovered.
5. Risk, blocker, or open question.
6. Next recommended task.

Executors must not overwrite source data, remove important records, or drift outside their assigned domain without orchestration approval.

---

## Tool Router

Prefer the lightest effective tool:

| Need | Primary Tool |
|---|---|
| Find files/text | `rg`, `Get-ChildItem` |
| Read docs/code | targeted file reads |
| Write docs/code | `apply_patch` |
| Validate code | local test/typecheck/lint commands |
| Current external facts | web search with sources |
| Browser/app inspection | Browser plugin when needed |

---

## Session Start Checklist

At the start of every session:

1. Read `docs/domain-brief.md`.
2. Read `docs/todo.md`.
3. Check the relevant life/project domain in `docs/life-domains.md`.
4. Load only relevant project files.
5. Decide whether this is Domain, Context, Orchestrate, or Execute work.

---

## Quality Gates

For code projects:

- Run the project's existing validation commands when available.
- For `MIMS App/`, inspect `package.json` before choosing npm commands.
- For Python projects, prefer targeted syntax checks or tests before broad changes.

For personal/career docs:

- Preserve factual accuracy.
- Flag assumptions.
- Keep source files and generated outputs distinct.
- Avoid generic motivational language; use evidence from Tebello's actual work.

---

## Current North Star

TebelloReborn should become a life operating system that helps Tebello:

- Know his strengths clearly.
- Build confidence from evidence.
- Turn operational experience into career leverage.
- Convert useful projects into business opportunities.
- Reduce scattered effort by giving every project a domain, owner, next action, and measurable purpose.
