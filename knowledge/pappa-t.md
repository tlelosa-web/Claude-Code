## 2026-07-28 — Vault survey: sub-projects catalogued, Claude-Code hub resolved, data-only folders noted
**Source:** Pappa T session (cross-project status survey)
**Status:** active

Full survey of this machine for projects not yet in `knowledge/INDEX.md`, mirroring
the Operations vault survey pattern. Findings:

- **This very `Claude-Code/` repo lives physically inside the Pappa T vault**
  (`Desktop/Pappa T/Claude-Code/`), as its own independent git repo (remote
  `tlelosa-web/Claude-Code`, clean working tree) — not a submodule, just a sibling
  folder. A prior `/continue` run in a Pappa T session flagged it as an
  "untracked nested repo, unclear origin" (it shows up as untracked in `git status`
  from the Pappa T repo's own perspective, since Pappa T's `.gitignore` doesn't
  cover it and it isn't a submodule either). Resolved: this is expected and fine —
  it's a deliberate, already-committed, already-pushed repo, not stray in-progress
  work. Not a violation to "clean up."
- **TebelloReborn's "known gap" is now filled** — see `tebelloreborn.md` (new file).
- Four more Pappa T sub-projects had no dedicated knowledge file yet and got one:
  `ai-outreach-agency.md`, `mims-app.md`, `iq-signal-generator.md`, `tenders-sa.md`.
  None of these five sub-projects are independent git repos — they're folders inside
  the single Pappa T vault repo, so there was no remote to dedupe against; the
  survey's "genuinely new project" test applied by absence of any dedicated file.
- **Data-only, no code — noted and skipped, no dedicated file:** `~/OneDrive/` (CVs,
  personal spreadsheets, scanned documents — a synced personal-data folder, not a
  project) and `~/Documents/Codex/` (empty). `~/python-sdk/` is a downloaded Python
  runtime (`python3.13.2/`), not a git repo or project — skipped as tooling, not a
  project.
- `~/Downloads/tlelosa-claude-config/` (+ a `.zip` of the same) is a redundant extra
  clone of the already-tracked `tlelosa-claude-config` repo (same remote) — already
  covered by the existing `tlelosa-claude-config.md` entry, skipped per the
  remote-match dedupe rule.
- No other dev-root candidates found: no `~/Dev`, `~/Projects`, or similar folder
  exists on this machine — Desktop's only project folder is `Pappa T/` itself.

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
**Status:** superseded — see dedicated `tebelloreborn.md` (written the same day from
a fuller read of the project's own `CLAUDE.md`/`docs/architecture.md`/`docs/todo.md`;
resolves this entry's "[scraping specifics unclear from the summary]" gap — PNet and
Careers24 simply have no dedicated Apify actor yet, per that project's own ADR-002)

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
