# Architecture — ai-outreach-agency

> Asset-Based B2B Outreach Pipeline for Heavy Engineering Firms in Gauteng

---

## Pipeline Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Lead     │───▶│  2. Research  │───▶│  3. Asset    │
│    Import    │    │              │    │    Gen       │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  6. Send     │◀───│  5. Email    │◀───│  4. Approval │
│  (manual)    │    │    Draft    │    │    Gate      │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Stage Details

### Stage 1: Lead Import

**Module:** `src/lead_import/`
**Input:** Apollo.io CSV export or Google Sheets manual entry
**Output:** Validated lead records (list of dicts / dataclass objects)
**Network:** Optional (Sheets sync) — core CSV reader works offline

Responsibilities:
- Parse CSV files exported from Apollo.io
- Validate against lead schema (required fields, data types, region filter)
- Deduplicate by company name + contact email
- Normalize company names and contact info
- Store validated leads in the lead store (format TBD — see ADR-001)

Lead schema (minimum fields):
```
company_name:    str   (required)
contact_name:    str   (required)
contact_email:   str   (required, validated format)
contact_title:   str   (required)
industry:        str   (required)
employee_count:  int   (optional)
website:         str   (optional)
phone:           str   (optional)
city:            str   (default: Gauteng region)
source:          str   (apollo | manual | referral)
status:          str   (new | researched | asset_ready | approved | drafted | sent)
```

### Stage 2: Research

**Module:** `src/research/`
**Input:** Validated lead record
**Output:** Enriched lead with research summary
**Network:** Required (Apify + OpenRouter)

Responsibilities:
- Take a lead's company name and website
- Trigger Apify web scrape actor to pull public company info (about page, services, recent news)
- Send scraped content to Claude (Sonnet via OpenRouter) for structured summary
- Extract: what they do, key services, recent projects/news, potential pain points for AI/automation
- Attach research summary to the lead record
- Handle scrape failures gracefully (mark lead as "research_failed", don't block pipeline)

### Stage 3: Asset Generation

**Module:** `src/asset_gen/`
**Input:** Enriched lead with research summary
**Output:** Custom mini-report or insight document
**Network:** Required (OpenRouter)

Responsibilities:
- Use research summary to generate a personalized 1-page insight document
- Asset types (selectable per campaign):
  - **Mini-report**: "3 Ways [Company] Could Use AI to Reduce [Specific Pain Point]"
  - **Benchmark**: "How [Industry Segment] Firms in Gauteng Are Adopting Automation"
  - **Checklist**: "AI Readiness Checklist for [Company Type]"
- Claude Sonnet generates the asset via OpenRouter
- Output as Markdown (convertible to PDF later if needed)
- Store asset linked to the lead record

### Stage 4: Approval Gate

**Module:** `src/approval/`
**Input:** Lead record + generated asset
**Output:** Approved / rejected / edited lead-asset pair
**Network:** None (fully offline)

**THIS IS THE MANDATORY HUMAN CHECKPOINT. NO CODE PATH BYPASSES THIS.**

Responsibilities:
- Present lead details and generated asset to the human operator
- CLI interface: display lead info, then asset content
- Options: `[a]pprove` / `[r]eject` / `[e]dit` / `[s]kip`
- If edited: open asset in default text editor, wait for save, re-display for final approval
- Log all approval decisions with timestamp
- Only approved leads proceed to email drafting
- Batch mode: queue multiple leads for sequential review

### Stage 5: Email Draft

**Module:** `src/email_draft/`
**Input:** Approved lead-asset pair
**Output:** Gmail draft (NOT sent)
**Network:** Required (Gmail API + OpenRouter)

Responsibilities:
- Use approved lead + asset to generate a personalized outreach email via Claude Sonnet
- Email structure:
  - Subject line referencing the company and a specific insight
  - Opening: reference something specific from research
  - Value prop: link to the attached asset / key insight
  - CTA: suggest a 15-min call or reply
  - Sign-off: Tebello's signature
- Create the email as a Gmail draft via Gmail API
- Attach or inline the asset (depending on format)
- Mark lead status as "drafted"
- **Never auto-send. Draft only.**

### Stage 6: Send (Manual)

**No code module.** Tebello opens Gmail and manually reviews + sends each draft. This stage exists only in the pipeline diagram for completeness.

---

## Data Flow

```
Apollo CSV ──┐
             ├──▶ Lead Import ──▶ Lead Store ──▶ Research ──▶ Lead Store (enriched)
Sheets ──────┘                        │
                                      │
                              Asset Gen ──▶ Lead Store (asset attached)
                                      │
                              Approval Gate ──▶ Lead Store (approved/rejected)
                                      │
                              Email Draft ──▶ Gmail Drafts + Lead Store (drafted)
                                      │
                              Manual Send ──▶ Lead Store (sent)
```

### Lead Store

The lead store is the central data layer. All stages read from and write to it. Format decision pending (ADR-001):

**Option A: Google Sheets**
- Pro: visible to Tebello without tooling, easy manual edits, shareable
- Pro: natural dashboard — filter by status, sort by date
- Con: rate limits, network dependency for reads/writes, schema less strict
- Con: concurrent access issues if n8n also writes

**Option B: SQLite local**
- Pro: offline-first, fast, proper schema enforcement, no rate limits
- Pro: easy to query and filter programmatically
- Con: invisible without a viewer tool, harder to manually edit
- Con: needs a sync mechanism if Google Sheets is also used for input

**Option C: Hybrid (recommended for consideration)**
- SQLite as primary local store (source of truth for pipeline)
- Google Sheets as import source + status dashboard (periodic sync)
- Best of both but more complex

---

## Component Boundaries

Each module in `src/` is a self-contained Python package with:
- `__init__.py` exposing the public interface
- Internal implementation files
- No cross-module imports except through the lead store interface

Inter-module communication happens through the lead store — modules never call each other directly. This keeps stages independently testable and allows n8n to orchestrate them externally.

---

## External Integrations

| Service | Purpose | Auth Method | Module |
|---------|---------|-------------|--------|
| OpenRouter | Claude API inference | API key (env var) | research, asset_gen, email_draft |
| Apify | Web scraping | API key (env var) | research |
| Gmail API | Create drafts | OAuth2 (credentials.json) | email_draft |
| Google Sheets API | Lead import/sync | OAuth2 (credentials.json) | lead_import |
| Apollo.io | Lead export | Manual CSV download | lead_import |

---

## n8n Integration

n8n runs externally and orchestrates the pipeline stages. Each Python module exposes a CLI entry point that n8n calls:

```
python -m src.lead_import --file leads.csv
python -m src.research --lead-id 42
python -m src.asset_gen --lead-id 42
python -m src.approval            # interactive — runs locally, not from n8n
python -m src.email_draft --lead-id 42
```

n8n handles: scheduling, retry logic, batch processing, and status webhooks. The Python code handles: business logic, API calls, and data transformation.

---

## Security Constraints

- All API keys in `.env` (gitignored, never committed)
- Gmail OAuth credentials in a secure local path (not in repo)
- No PII logged to files — lead data stays in the lead store only
- Rate limiting on all external API calls
- No auto-send capability exists in the codebase. Period.
