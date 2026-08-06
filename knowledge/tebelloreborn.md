## 2026-08-06 — Playwright auto-submit: pre-build verification (no code written yet)
**Source:** session (this machine) — first look at the real TebelloReborn code
**Status:** active

The hub spec `docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md` was
written from a cloud session with no access to this code and flagged its own
file names as guesses. They were verified against the live
`Desktop/Pappa T/TebelloReborn/`. Most held; four things did not.

**Confirmed as guessed:** `src/review/` exists with `cli.py` (130 lines),
`db.py`, `migrations.py`, `schema.py`; `doc_gen/pdf_export.py` exists; the
`approvals` table carries a `CHECK (decision IN ('approved','rejected','edited'))`;
the approval gate is structural, enforced by the status state machine.

**1. The spec targets the wrong platform — the blocking finding.** It scopes the
build to **LinkedIn Easy Apply only** and puts Indeed explicitly out of scope.
But every row in `career.db` is Indeed:

```
indeed  approved  6
indeed  rejected  4
```

Zero LinkedIn vacancies exist. Building the spec as written would ship a feature
unable to submit any of the 6 pending approved applications. Tebello chose
(2026-08-06) to **build the platform-agnostic core first** — submission status +
migration, session/`storageState` handling, "not auto-submittable → fall back to
manual" detection, and outcome recording — leaving the site-specific adapter as
a second task once the platform question is settled. No work is wasted either
way, and the core is testable offline under the project's TDD rule.

**2. `PRAGMA user_version` is a single global counter shared by four independent
migration modules.** `profile/`, `vacancy_search/`, `doc_gen/` and `review/`
each own a `MIGRATIONS: list[tuple[int, str]]` and an `apply_migrations()` that
reads and writes the *same* `PRAGMA user_version` on the *same* database.
Currently only `vacancy_search` has entries (1–4) and the live DB sits at
`user_version = 4`.

**The trap:** adding `(1, "ALTER TABLE ...")` to `review/migrations.py` would be
**silently skipped forever** — `apply_migrations` runs `if version > current`,
and `current` is already 4. No error, no warning, no migration. Any new
migration in *any* module must take a globally-unique version ≥ 5. This is not
documented in the project's `CLAUDE.md`, whose rule is only "no schema change
without a migration file."

**3. The spec is wrong about `.gitignore` covering the session file.** It says to
save Playwright's `storageState` to "a path already covered by the project's
existing `.gitignore`". That file covers `.env`, `*.db`, `*.db-shm`, `*.db-wal`,
`exports/` and caches — nothing else. A `storage_state.json` would be
**committed**. That file is a live authenticated session cookie; in git history
it is a session-hijack credential. An explicit ignore entry has to be added as
part of this work, not assumed.

**4. `playwright` is not a dependency.** The project has exactly three
(`requests`, `python-dotenv`, `fpdf2`). Adding it also pulls browser binaries via
`playwright install` — a large, non-pip-clean runtime dependency in a project
whose stated stance is offline-first. Worth a deliberate decision, not a silent
`pip install`.

**Schema change this needs:** `VALID_STATUSES` is
`{new, scored, asset_ready, approved, rejected}` with no `submitted` /
`submission_failed`, and `vacancies` has no column for a submission outcome.
Both are required, and both need a migration file per the project's hard rule.

**Process required before any code** (project `CLAUDE.md`, which takes precedence
over the hub under hub-and-spoke): Hard Rule 13 — `/codex-review` must run on the
spec in the project's own `docs/specs/` and its strongest points folded back as a
dated Amendment *before* an Executor is dispatched. Hard Rule 2 — a plan is
required for anything touching more than 2 files, which this does. Plus TDD
(failing tests first, ≥80% coverage) and `black . && ruff check . && python -m pytest`
before every commit.

**Also flagged, unrelated to this build:** automating submissions while logged in
as Tebello is against LinkedIn's User Agreement, and the account at risk is his.
Scraping via Apify is a different exposure from driving an authenticated session.

## 2026-08-04 — Post-MVP scope decision: Playwright auto-submit picked
**Source:** cloud session, via `docs/specs/2026-07-29-tebelloreborn-scope-decision.md`
**Status:** active

Of the three undecided post-MVP items (Playwright auto-submit,
recruiter/cold-outreach revival, doc-gen volume-cap/scheduler), Tebello
picked **Playwright auto-submit only** — the other two are not committed to
build. Explicit constraint: the Stage 5 human-approval gate stays exactly
as-is; Playwright only automates the mechanical job-site form-filling/
submission step **after** a human has already approved that application's
documents. Full unattended auto-submit (no review step) was considered and
declined as too risky given AI-generated documents and untrusted scraped
vacancy text.

Build spec written: `docs/specs/2026-08-04-tebelloreborn-playwright-auto-submit.md`
— written without direct access to TebelloReborn's actual code (Pappa
T-only), so its proposed file/module names are informed guesses pending
confirmation in a real Pappa T session. Key scoping calls already made:
start with LinkedIn Easy Apply only (bounded, scriptable flow) and
explicitly fall back to manual for anything else (Indeed's flow varies too
much per employer to generic-form-fill reliably); reuse the same
untrusted-scraped-text discipline already applied to the doc-gen ADR-003
correction if any LLM-driven form interpretation is involved; use
Playwright `storageState` for session/login, not stored credentials.

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
