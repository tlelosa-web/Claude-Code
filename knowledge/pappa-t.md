## 2026-07-26 — What Pappa T is
**Source:** session
**Status:** active

Pappa T is Tebello's personal machine, running Claude Code locally — the
counterpart to **Operations** (the Fan Movement work PC). Not a registered
Claude Code Remote/on-the-web environment (`list_environments` only shows
the cloud `Default` sandbox); there's no live bridge between it and remote
sessions. The only working sync channel between Pappa T and any other
session (Operations, remote environments) is git: push from one side, pull
from the other, per `CLAUDE.md`'s knowledge-cache rules. See
`tlelosa-claude-config.md` for the repos it shares with Operations, and
`knowledge/INDEX.md` for the machine/repo split.

## 2026-07-26 — Pappa T-only items
**Source:** session
**Status:** active

- `codex-gate` (OpenAI egress plugin, in `tlelosa-claude-config`) is
  installed/tested Pappa T-only for now — not yet cleared for Operations
  pending a separate OpenAI-egress confirmation from Fan Movement IT. See
  `tlelosa-claude-config.md` for the open smoke-test item.
- **TebelloReborn** — see dedicated entry below; gap now filled.

## 2026-07-28 — TebelloReborn ("Career Engine"): what it is & status
**Source:** Pappa T session (direct look at the project folder)
**Status:** active

Semi-automated job-application pipeline for Tebello's own job search — not
a Fan Movement project. Finds vacancies matching his profile, scores them
with AI, generates a tailored CV + cover letter per vacancy, and stops at
a mandatory human approval gate. **No auto-submission in this build.**

Stack:
- Python 3.11+; package name `career-engine` (`pyproject.toml`, console
  script entry point). No `README.md` yet — `pyproject.toml` is the
  closest thing to project metadata.
- AI matching: local **Ollama** (`qwen3:8b`) — fixed local model, no cloud
  LLM routing for the matching step (keeps that stage at marginal/zero
  cost).
- Document generation: headless **Claude Code** (`claude -p ...`) invoked
  as a local subprocess for CV/cover-letter drafting.
- Vacancy scraping: **Apify** actors (Indeed + LinkedIn).
- Sibling project of **ai-outreach-agency** — deliberately mirrors its
  architecture (rate limiting, structural human-approval gate as a design
  pattern, not just a TebelloReborn-specific choice).

Pipeline (MVP, 5 stages): Profile Import → Vacancy Fetch (Apify) → AI
Matching (Ollama) → Document Generation (headless Claude Code) → Human
Review (approve / reject / edit). Auto-submit (Playwright) and a
tracking/recruiter dashboard are explicitly out of scope for this MVP.

Status: **MVP complete** (2026-07-26), 182 tests passing. Notable fixes
caught during the build:
- An Apify payload bug (wrong field name breaking result parsing).
- A security correction: the headless Claude Code subprocess's
  `--allowedTools` was dropped from `Write` down to **`Read`-only**, to
  close a prompt-injection risk from untrusted scraped job descriptions
  flowing into the doc-gen step.

Open items (post-MVP, none urgent):
- No dedicated Apify actor for [scraping specifics unclear from the
  summary] — deferred in favor of a generic crawler + LLM-extraction
  approach.
- Auto-submit via Playwright — deferred, undecided.
- Recruiter/cold-outreach revival — undecided.
- A volume-cap/scheduler layer for doc-gen generation — only if actually
  needed, not committed to.
