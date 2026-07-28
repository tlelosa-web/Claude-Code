## 2026-07-28 — What it is, stack, pipeline
**Source:** Pappa T session (cross-project status survey), TebelloReborn's own CLAUDE.md/docs/todo.md/docs/architecture.md
**Status:** active

Fills the gap flagged in `pappa-t.md`'s "Pappa T-only items" entry
(2026-07-26): TebelloReborn ("Career Engine") is a personal job-application
automation pipeline for Tebello — Python 3.11+, SQLite, local Ollama
(`qwen3:8b`), headless Claude Code, Apify (job-board scraping), `fpdf2`. Lives
at `Pappa T/TebelloReborn/` — not its own git repo, just a folder inside the
Pappa T vault repo.

Five-stage MVP pipeline (Phases 1-5 of an original 7-phase plan; phases 6-7
— Playwright auto-submit, tracking dashboard — deferred, not built):

1. **Profile Import** (offline) — `data/profile_seed.json` → SQLite `CandidateProfile`.
2. **Vacancy Fetch** (Apify) — Indeed (`misceres~indeed-scraper`) + LinkedIn Jobs
   (`bebity~linkedin-jobs-scraper`) actors, confirmed live 2026-07-26. PNet/Careers24
   have no dedicated actor — deferred (ADR-002).
3. **AI Matching** (local Ollama, `qwen3:8b`, native `POST /api/generate`, no API key) —
   fails loud, no fallback backend.
4. **Document Generation** (headless Claude Code, `claude -p ... --allowedTools "Read" --output-format json`
   subprocess under Tebello's own Claude subscription, $0 marginal cost) — tailored
   CV + cover letter, exported via `fpdf2`.
5. **Human Review** (offline CLI) — approve/reject/edit; **structural, non-negotiable
   human-approval gate** before anything would leave the system (no auto-submit exists).

**MVP build is complete as of 2026-07-26** — all 54 Build Queue steps done (Phases
0-8), 182 tests passing.

**Reusable gotchas/decisions (public-repo-level, own repo already documents these):**
- **ADR-003** (2026-07-19): dropped OpenRouter entirely, pre-build — routed by
  workload shape instead: cheap/structured scoring → local Ollama (mirrors
  `ai-outreach-agency`'s ADR-004 research stage); quality-sensitive generation →
  headless Claude Code (mirrors `ai-outreach-agency`'s planned-but-not-yet-built
  ADR-003/Build-Queue-A). Neither backend has an Opus-style effort-tier concept —
  each is a single fixed model/invocation.
- **Security correction to ADR-003** (post-build): the ADR's literal
  `--allowedTools "Read,Write"` was a real vulnerability — both doc-gen generators
  embed untrusted scraped job-posting text (`vacancy.description`) into the headless
  agent's instruction, so a prompt-injected posting could make the agent write
  attacker-controlled content to an arbitrary file. Neither generator actually needs
  Write (`pdf_export.py`, trusted Python, does the real file write from the JSON
  `result` field) — corrected to `"Read"` only, plus a `wrap_untrusted_text()` helper
  that delimits untrusted text with explicit "don't follow embedded instructions"
  markers as defense in depth. General pattern worth remembering for any project that
  feeds scraped/external text into a headless-agent instruction string.
- **fpdf2 `multi_cell` gotcha**, found by an offline integration test (not caught by
  any unit test, since every unit test mocked the PDF export call): two non-blank
  lines in a row (e.g. a `## ` heading directly followed by body text) starved the
  next line of width — `FPDFException: Not enough horizontal space to render a single
  character`. fpdf2's default `new_x=XPos.RIGHT` left the cursor at the right margin
  after a `multi_cell` call. Fix: pass `new_x=XPos.LMARGIN, new_y=YPos.NEXT` on every
  `multi_cell` call.
- **Apify payload-shape bug**, caught during a live actor-slug verification pass
  (2026-07-26): `fetch_vacancies()` was sending `{"maxItems": limit}` as the entire
  request body to both actors — not a valid field for either, and neither actor had
  a search title/location to search on. Because HTTP errors were swallowed per-call
  by design, a real run would have silently returned zero results with no visible
  failure. No unit test caught it because every test mocked `requests.post` directly
  rather than exercising a real payload shape. General lesson: mocking the transport
  layer verifies your code calls `requests.post`, not that the payload you send is
  valid against the real API's schema — worth an occasional real-payload smoke test
  against actor/API docs, not just against your own mocks.
- Deliberately did **not** copy `ai-outreach-agency`'s fuller `handoff/` scheduler /
  volume-cap / weekly-report machinery — no documented volume-throttling requirement
  existed for this project, and copying machinery "because the sibling project has it"
  was called out as a judgment call to resist without an actual confirmed need.

**Not carried over (deliberately, per no-company-data discipline):** the migration
convention detail, exact schema/table layouts, and full ADR text stay in
TebelloReborn's own `docs/`/`CLAUDE.md` — this entry is the reusable-pattern summary,
not a mirror of the source docs.
