# Project Portfolio Map

## DCOE Pass

Domain: Business & Ventures / Project Portfolio  
Context used:

- `MIMS App/GEMINI.md`
- `MIMS App/package.json`
- `MIMS App/src/lib/types.ts`
- `MIMS App/src/app/`
- `MIMS App/src/lib/actions/`
- `IQ/1_Documentation/README.md`
- `IQ/5_Archive_and_Debug/memory_buffer.txt`
- `IQ/4_Scripts/test_signal_generator.py`
- `Tenders/4_Scripts/tenders-sa/PRD.md`
- `Tenders/4_Scripts/tenders-sa/README.md`
- `Tenders/4_Scripts/tenders-sa/tenders/client.py`
- `Tenders/4_Scripts/tenders-sa/tenders/search.py`
- `Tenders/4_Scripts/find_gauteng_food_tenders.py`
- `TebelloReborn/1_Documentation/QWEN_DIRECTIVE.md`
- `TebelloReborn/3_Live_Reports/Job_Application_Tracker.md`
- `docs/strengths-profile.md`

## Portfolio Summary

| Project | Current Classification | Primary Domain | Leverage | Risk | Recommended Status |
|---|---|---|---|---|---|
| MIMS App | Business Candidate + Career Leverage | Operations & Automation | Very High | High build scope | Focus Candidate |
| TebelloReborn Career Engine | Career Leverage | Career & Brand | Very High | Needs current data hygiene | Maintain and use weekly |
| Tenders | Business Candidate + Opportunity Engine | Tender & Opportunity | Medium-High | API/deployment unfinished | Validate cheaply |
| IQ | Personal Growth + Risk Discipline | Finance & Risk | Medium | High financial/gambling risk | Bound and de-prioritize |

## 1. MIMS App

Classification: **Business Candidate + Career Leverage**

What it is:

A Next.js 14, Supabase, Tailwind manufacturing resource planning app. It already has app routes, dashboard pages, typed entities, server actions, migrations, inventory, products, production, purchase orders, sales orders, dispatch, suppliers, and customers. The project directive positions it as MRP Stage 3 moving toward shop-floor operator dashboards, real-time work orders, time tracking, scanning, material consumption, completion, defects, downtime, genealogy, and RLS.

Why it matters:

This is the project most aligned with Tebello's core strength: Strategic Operations Builder. It converts manufacturing experience into visible software and operational IP.

Best use:

- Career portfolio proof for operations/MRP/process improvement roles.
- Demo artifact for interviews.
- Possible service/product seed for small manufacturers who need lightweight planning, stock, and production visibility.

Next 30-day outcome:

Build a **demo-grade MIMS Operations Walkthrough**:

- 1 clean sample dataset.
- 1 dashboard story: stock risk -> purchase order -> production order -> dispatch.
- 1 short README explaining the business problem and Tebello's operational insight.

Do not try to finish the full Stage 3 system yet.

Risks:

- Large scope can swallow months.
- `.env.local` exists; secrets hygiene is required before sharing.
- Stage 3 requires careful auth/RLS and data-integrity work.

Executor routing:

- Primary: `operations-systems`
- Secondary: `venture-builder`, `career-brand`, `learning-capability`

## 2. TebelloReborn Career Engine

Classification: **Career Leverage**

What it is:

A professional job-search and positioning system with CV source files, generated CV PDF, LinkedIn guide, PNET/Indeed/platform profiles, job tracker, recruiter database, cold email templates, Gmail compose automation, and outreach scripts.

Why it matters:

This is the fastest route to external opportunities. It is already structured, already has deliverables, and directly supports income and career movement.

Best use:

- Weekly application/outreach execution.
- Interview narrative and LinkedIn positioning.
- Proof of self-directed system building.

Next 30-day outcome:

Run a **weekly career cadence**:

- Refresh job leads.
- Send targeted recruiter/outreach messages.
- Request 2-3 LinkedIn recommendations.
- Post one practical operations insight per week.
- Track results in `Job_Application_Tracker.md`.

Risks:

- Existing job leads are from April 2026 and must be refreshed before acting.
- `gmail_config.json` may contain sensitive mail configuration.
- Outreach automation must not send anything without explicit approval.

Executor routing:

- Primary: `career-brand`
- Secondary: `identity-strengths`, `wellbeing-rhythm`

## 3. Tenders

Classification: **Business Candidate + Opportunity Engine**

What it is:

A Python tender intelligence system for South African government procurement. It has a PRD, CLI package, SQLite cache design, API client with retries, search logic, contact extraction direction, pipeline concepts, and a food/Gauteng report script.

Why it matters:

It could become either a business tool for Tebello's own opportunity scanning or a small service for other South African small businesses. It fits the "find signal in messy public data" pattern.

Best use:

- Opportunity discovery for possible business income.
- A lightweight monitoring tool.
- A test case for turning automation into a service.

Next 30-day outcome:

Validate one narrow watchlist:

- Province: Gauteng.
- Category/keywords: choose one lane only, such as manufacturing supplies, maintenance, food supplies, IT services, or engineering services.
- Output: weekly opportunities report with contact and bid/no-bid notes.

Risks:

- eTenders API may be slow or unreliable.
- WhatsApp/Google Sheets integrations appear planned, not necessarily complete.
- Tender pursuit requires compliance, documents, pricing, and time discipline beyond discovery.

Executor routing:

- Primary: `tender-opportunities`
- Secondary: `venture-builder`, `finance-risk`, `strategy-governance`

## 4. IQ

Classification: **Personal Growth + Risk Discipline**

What it is:

A Python IQ Option signal generator with RSI, Stochastic, ADX regime filtering, confidence scoring, daily loss limit, martingale warnings/blocking, CSV logs, tests, and a live data feed direction.

Why it matters:

It shows risk thinking, logging, discipline, and algorithmic experimentation. It can build technical capability and reinforce decision rules.

Best use:

- Learning project for Python, indicators, logging, and risk controls.
- Personal discipline tool if used only within strict boundaries.
- Not a business or income priority.

Next 30-day outcome:

Freeze feature expansion and write a risk charter:

- Maximum money exposure.
- No martingale escalation beyond pre-defined rules.
- Review logs before any new session.
- Treat all results as learning data, not proof of income.

Risks:

- Trading/betting domains can damage finances and focus.
- The tool may create a false sense of control.
- Time spent here competes with stronger career/business leverage.

Executor routing:

- Primary: `finance-risk`
- Secondary: `learning-capability`, `wellbeing-rhythm`

## Portfolio Priority

### Primary 30-Day Focus

**MIMS App: demo-grade operations walkthrough**

Reason:

It has the best overlap between Tebello's strengths, career story, business potential, and technical learning.

### Weekly Support System

**TebelloReborn Career Engine**

Reason:

Career movement should not wait until MIMS is finished. A small weekly cadence keeps external opportunity alive.

### Validation Lane

**Tenders**

Reason:

Promising, but should be tested narrowly before becoming a full project.

### Bound/Limit Lane

**IQ**

Reason:

Useful for learning and risk discipline, but not the best life-improvement lever right now.

## 30-Day Execution Board

| Week | MIMS Focus | Career Engine | Tenders | IQ |
|---|---|---|---|---|
| Week 1 | Audit current app flow and define demo dataset | Refresh LinkedIn/CV action list | Choose one tender lane | Write risk charter |
| Week 2 | Create/verify demo data path | Contact 5 recruiters or references | Run one cached report | Review existing signal logs only |
| Week 3 | Polish dashboard walkthrough | Publish 1 operations insight post | Add bid/no-bid notes | No feature expansion |
| Week 4 | Produce portfolio README/screenshots | Track responses and next actions | Decide continue/pause | Decide keep/archive |

## Orchestrator Decision

Do not start four builds in parallel.

Start with:

1. MIMS demo walkthrough plan.
2. Career engine weekly cadence.
3. Tenders one-lane validation.
4. IQ risk boundary.

This gives Tebello forward motion without turning the operating system into a burden.
