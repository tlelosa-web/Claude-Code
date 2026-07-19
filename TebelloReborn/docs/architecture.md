# Architecture — TebelloReborn (Career Engine)

> Updated: 2026-07-05
> Status: MVP scaffolding in progress — no pipeline code written yet, this document defines the target design.

---

## Purpose

Continuously find job vacancies matching Tebello Lelosa's profile, score them, generate a tailored CV and cover letter per vacancy, and stop for mandatory human review before anything leaves the system. Reduce a ~20–30 minute manual application to a ~2–5 minute review-and-decide action.

This supersedes the earlier `_archive_qwen_prototype/` build: a hand-authored, untracked scaffold with hardcoded recruiter/email data and one automation script that never successfully ran. That content is preserved for reference, not deleted, and is not part of the active pipeline.

---

## Pipeline Stages (MVP — Phases 1–5 of the original 7-phase plan)

### Stage 1: Profile Import

**Module:** `src/profile/`
**Input:** `data/profile_seed.json` (hand-authored structured profile, sourced from `data/Tebello_Lelosa_Master_CV_2026.md`)
**Output:** `CandidateProfile` record in SQLite
**Network:** None — fully offline

Responsibilities:
- Load structured profile: skills, 19-year experience timeline, target titles, target industries, region, salary floor.
- Validate against schema.
- Store as the single source of truth for matching (Stage 3).

### Stage 2: Vacancy Fetch

**Module:** `src/vacancy_search/`
**Input:** search parameters (titles, locations, keywords, limit)
**Output:** `Vacancy` records in SQLite, `status: new`
**Network:** Required — Apify

Responsibilities:
- Call the Apify Indeed scraper actor and the Apify LinkedIn Jobs scraper actor.
- Normalize results into the `Vacancy` schema (company, title, description, url, platform, salary, deadline, scraped_at).
- Deduplicate by `(company, title, url)`.
- **PNet and Careers24 are out of scope for MVP** — no dedicated Apify actor exists for either as of 2026-07-05. Future option: point Apify's generic `website-content-crawler` actor (already used by `ai-outreach-agency`) at their search-result pages and use Claude to extract structured fields from unstructured crawled text.

### Stage 3: AI Matching

**Module:** `src/matching/`
**Input:** `CandidateProfile` + one `Vacancy`
**Output:** match score, strengths, weaknesses, recommendation → `Vacancy.status: scored`
**Network:** Required — local Ollama daemon

Responsibilities:
- Build a comparison prompt (profile skills/experience/titles vs. vacancy requirements).
- Call a local Ollama daemon (`qwen3:8b`, native `POST /api/generate`) via `matching/ollama_client.py` — no API key, a single fixed local model with no model/effort-tier routing, per ADR-003 (`docs/decisions/ADR-003-inference-provider-split.md`).
- Parse and persist score + rationale.

### Stage 4: Document Generation

**Module:** `src/doc_gen/`
**Input:** `CandidateProfile` + scored `Vacancy`
**Output:** tailored CV text + cover letter text + PDF exports → `Vacancy.status: asset_ready`
**Network:** Required — headless Claude Code (local subprocess)

Responsibilities:
- Tailor CV emphasis (which experience/skills to foreground) per vacancy, via a headless Claude Code subprocess (`claude -p ... --allowedTools "Read,Write" --output-format json`) run under Tebello's own Claude subscription — $0 marginal cost, real content generation, per ADR-003 (`docs/decisions/ADR-003-inference-provider-split.md`).
- Generate a personalized cover letter per vacancy.
- Export both to PDF via `fpdf2` (reusing the working logic pattern from the archived `generate_cv_pdf.py` and `ai-outreach-agency`'s `asset_gen/pdf_export.py`).

### Stage 5: Human Review

**Module:** `src/review/`
**Input:** generated CV + cover letter + vacancy details
**Output:** approve / reject / edit decision → `Vacancy.status: approved | rejected`
**Network:** None — fully offline

Responsibilities:
- CLI gate mirroring `ai-outreach-agency/src/approval/cli.py` exactly: show the vacancy, show the generated assets, take a decision, **persist it** (that repo had a real bug where approval decisions were computed but never saved to the DB — this project must not repeat it).
- `approved` is the current terminal state.

---

## Deferred Phases (not built in this MVP)

```
6. Auto-Submit   → Playwright form-fill on supported job boards, paused before final click
7. Dashboard     → tracking view: applications over time, match-score distribution,
                     interview/offer/response-rate metrics
```

These map to Phase 6–7 of the original Drive-doc plan and will be scoped as separate, later work once the MVP pipeline (Stages 1–5) is proven end-to-end.

---

## Vacancy Status State Machine

```
new → scored → asset_ready → approved
                            → rejected
```

Enforced the same way as `ai-outreach-agency`'s lead status machine (`VALID_TRANSITIONS` dict) — no stage may skip ahead, transitions checked on every write.

---

## Data Flow

```
data/profile_seed.json ──▶ Profile Import ──▶ SQLite (CandidateProfile)
                                                     │
Apify (Indeed) ──┐                                  │
Apify (LinkedIn)─┼──▶ Vacancy Fetch ──▶ SQLite (Vacancy, status=new)
                 │                                  │
                 ▼                                  ▼
                                    AI Matching (Local Ollama)
                                                     │
                                                     ▼
                                    SQLite (Vacancy, status=scored)
                                                     │
                                                     ▼
                                    Document Gen (Headless Claude Code + fpdf2)
                                                     │
                                                     ▼
                                    SQLite (Vacancy, status=asset_ready) + exports/*.pdf
                                                     │
                                                     ▼
                                    Human Review (CLI)
                                                     │
                                        ┌────────────┴────────────┐
                                        ▼                         ▼
                              status=approved            status=rejected
```

---

## External Integrations

| Service              | Purpose                | Access method                                                     | Module      |
|----------------------|-------------------------|--------------------------------------------------------------------|-------------|
| Apify                | Job vacancy scraping   | Indeed + LinkedIn Jobs actors (paid, cheap: LinkedIn ~$0.4/1,000 jobs) | `vacancy_search/` |
| Local Ollama         | AI matching            | Native `POST /api/generate` to a local daemon, no API key (`qwen3:8b`) | `matching/` |
| Headless Claude Code | Document generation     | Local `claude -p ...` subprocess under Tebello's own Claude subscription, no API key | `doc_gen/`  |

`APIFY_API_KEY` is shared with `ai-outreach-agency` (same account), already funded and working. Ollama and headless Claude Code both run against local resources (a local daemon, a local authenticated CLI) rather than a metered account — **no OpenRouter dependency exists in this project as of ADR-003** (`docs/decisions/ADR-003-inference-provider-split.md`), so there is no shared-credit blocker here anymore.

---

## Orchestration

Pure in-process CLI orchestration, no external workflow engine (same decision as `ai-outreach-agency`'s ADR-002 — n8n is not part of this stack either):

```
career-engine import-profile --file data/profile_seed.json
career-engine fetch-vacancies [--titles ...] [--locations ...] [--limit N]
career-engine list [--status <status>]
career-engine run --vacancy-id <id>
career-engine run-all [--status <status>]
```

(`career-engine` is a placeholder console-script name pending user confirmation.)

---

## Relationship to `ai-outreach-agency`

This project deliberately mirrors that repo's proven architecture rather than the generic stack recommended in the original Drive-doc plan (which suggested n8n, FastAPI, Streamlit — none of which are used here or there). Specifically reused patterns:

- SQLite as source of truth, status state machine with enforced transitions
- Rate-limited external clients with an `OFFLINE_MODE` fixture short-circuit
- A structural (not advisory) human-approval gate before any consequential output
- `.env` + `Settings` dataclass configuration, never hardcoded secrets
- pytest with autouse offline fixtures, unit + integration split

Where the domains differ (B2B sales leads vs. personal job vacancies), the schema and prompts differ accordingly — but the shape of the pipeline is intentionally the same.
