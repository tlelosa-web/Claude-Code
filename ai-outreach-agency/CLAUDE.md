# CLAUDE.md — ai-outreach-agency

> DCOE v3.0 — Domain → Context → Orchestrate → Execute

---

## Project Overview

```
Project:     ai-outreach-agency
Type:        B2B outreach automation engine
Owner:       Tebello Lelosa
Stack:       Python · n8n (external orchestration) · Claude API via OpenRouter · Google Sheets · Gmail
Deployment:  Local Windows desktop, offline-capable core logic
Runtime:     Python 3.11+
```

Automated pipeline that researches heavy engineering firms in Gauteng, generates custom insight assets per lead, and prepares Gmail drafts — with a mandatory human approval gate before any email is created.

Core docs:

- `docs/todo.md`: live task queue.
- `docs/architecture.md`: pipeline design and data flow.
- `docs/api-patterns.md`: API integration patterns (OpenRouter, Google Sheets, Gmail, Apify).
- `docs/session-log.md`: chronological session memory.
- `docs/decisions/`: architecture decision records.

---

## DCOE Rules

Every task follows this sequence:

1. **Domain**: classify the pipeline stage this work belongs to.
2. **Context**: load only the relevant module and its upstream/downstream interfaces.
3. **Orchestrate**: decide which module or agent owns the work.
4. **Execute**: complete one bounded task with a clear output and verification.

Hard rules:

- Domain before planning.
- Context before implementation.
- No large multi-file work without a plan.
- One task equals one clear output.
- **NO EMAIL SENDS WITHOUT HUMAN APPROVAL GATE.** This is non-negotiable. The approval module must sit between asset generation and email drafting. No code path may bypass it. Email drafts are created in Gmail as drafts — never auto-sent.
- Never expose or hardcode secrets. All API keys via environment variables or `.env` (gitignored).
- Update `docs/todo.md` after completed work.
- Update `docs/session-log.md` when durable context changes.

---

## ICP (Ideal Customer Profile)

```
Industry:  Heavy manufacturing, engineering, fabrication, mining supply
Region:    Gauteng, South Africa
Size:      10–200 employees
Persona:   Operations Manager, Engineering Manager, Procurement Manager
```

---

## Inference Routing (OpenRouter)

All LLM calls go through OpenRouter. Model selection by task:

| Task | Model | Why |
|------|-------|-----|
| Planning, architecture decisions | `anthropic/claude-opus-4` | Deep reasoning for strategic choices |
| Asset generation, email drafting, research summaries | `anthropic/claude-sonnet-4` | Best balance of quality and cost for content |
| Lead scoring, quick classification, search queries | `anthropic/claude-haiku-4` | Fast and cheap for simple decisions |

Default model: **Sonnet** — use unless the task clearly needs Opus (planning) or Haiku (search/scoring).

---

## Offline-First Rule

Core pipeline logic (lead import, schema validation, approval gate, local data transforms) must work fully offline. Only these stages require network:

- Research (Apify web scraping)
- Asset generation (OpenRouter API)
- Email drafting (Gmail API)
- Lead sync (Google Sheets API)

Design modules so offline stages never import or depend on network-requiring code.

---

## Pipeline Stages

```
1. Lead Import     → CSV/Sheets → validated lead records
2. Research        → Apify scrape → Claude summary → enriched lead
3. Asset Gen       → Claude API → custom mini-report per lead
4. Approval Gate   → Human reviews lead + asset → approve / reject / edit
5. Email Draft     → Claude API → Gmail draft (NOT sent)
6. Send            → Human clicks send in Gmail (fully manual)
```

---

## File Structure

```
ai-outreach-agency/
├── CLAUDE.md                    # This file
├── docs/
│   ├── todo.md                  # Live task queue
│   ├── architecture.md          # Pipeline design doc
│   ├── api-patterns.md          # API integration patterns
│   ├── session-log.md           # Session memory
│   ├── decisions/               # ADRs
│   ├── specs/                   # Feature specifications
│   ├── bugs/                    # Bug reports
│   └── research/                # Research notes
├── .claude/
│   ├── agents/                  # DCOE agent definitions
│   ├── hooks/                   # Pre/post hooks
│   └── commands/                # Custom commands
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
└── src/
    ├── lead_import/             # CSV reader + schema validator
    ├── research/                # Apify integration + Claude summary
    ├── asset_gen/               # Custom asset generation via Claude
    ├── approval/                # CLI human approval gate
    └── email_draft/             # Gmail draft creation
```
