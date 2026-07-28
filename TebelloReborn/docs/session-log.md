# Session Log — TebelloReborn (Career Engine)

> Chronological record of durable context changes. Ready for the
> `post-task` hook once wired up (currently scaffolded, not firing —
> see hub `CLAUDE.md`'s Hooks section); until then, updated manually
> per Hard Rule #11.

---

## 2026-07-29 — codex-review pnet-careers24-coverage.md: ran

## 2026-07-29 — codex-review pnet-careers24-coverage.md: warned (codex exec argument-list-too-long, exit 126)

## 2026-07-26 — MVP build complete (Phases 0–7)

All 54 Build Queue steps in `docs/specs/mvp-pipeline-build.md` are done —
the 5-stage pipeline (Profile Import → Vacancy Fetch → AI Matching →
Document Generation → Human Review) is wired end-to-end behind the
`career-engine` CLI, with the mandatory human approval gate as the terminal
state. No auto-submission exists past `approved` (Hard Rule #1).

- Phases 0–3 (scaffolding, shared rate-limiter, Profile Import, Vacancy
  Fetch) and Phase 3.5 (ADR-001, ADR-002) were completed in earlier
  sessions.
- ADR-003 (accepted 2026-07-19, ahead of ADR-001/002 for timing reasons)
  dropped OpenRouter from this project entirely: AI Matching routes to
  local Ollama (`qwen3:8b`), Document Generation to headless Claude Code
  (`claude -p`) — both fixed, flat-cost backends with no model/effort
  routing table.
- Phase 4 (AI Matching) and Phase 5 (Document Generation) landed with two
  corrective fixes caught mid-build rather than assumed away:
  - The `vacancies` table had no score/rationale columns when Phase 4 was
    actually built (ADR-003 §2 had assumed otherwise) — added via a proper
    migration (`vacancy_search/migrations.py` versions 1–4) plus
    `save_match_result()`, not by editing the committed baseline schema.
  - ADR-003 §3's literal `--allowedTools "Read,Write"` for the headless
    Claude Code runner was a real vulnerability: both generators embed
    untrusted scraped `vacancy.description` text in the instruction, so
    Write access would let a prompt-injected posting make the agent write
    attacker-controlled content to an arbitrary path. Corrected to
    `"Read"` only, with `runner.wrap_untrusted_text()` added as defense in
    depth. ADR-003 itself was left unedited as the historical record; the
    correction is noted in `docs/todo.md`.
- Phase 6 (Human Review) required Reviewer sign-off before the RED/GREEN
  commits landed (steps 48–49), per the mandatory gate around this stage —
  `review/cli.py` guarantees `save_approval()` is committed before the
  vacancy status transitions, so a failure after persistence never leaves
  an "approved" vacancy with no recorded decision.
- Phase 7 (this session): wired `src/main.py` — the `career-engine` CLI's
  5 subcommands (`import-profile`, `fetch-vacancies`, `list`, `run`,
  `run-all`) dispatching through matching → doc-gen → review in order,
  stopping a `run-all` batch cleanly on the review gate's Quit choice
  instead of crashing it. Added `Vacancy.cv_text`/`cover_letter_text` as
  transient (non-persisted) fields so `run` hands the review gate the
  exact generated text instead of a second generation round-trip.
  - Wrote `tests/integration/test_full_pipeline.py` — the first test in
    this project to exercise the real PDF export path (every prior unit
    test mocks it). That surfaced a genuine bug in `pdf_export.py`:
    fpdf2's `multi_cell` defaults to leaving the cursor at the right
    margin, so two non-blank lines in a row (e.g. a heading directly
    followed by body text) starved the next line of rendering width and
    raised `FPDFException`. Fixed by resetting the cursor
    (`new_x=XPos.LMARGIN, new_y=YPos.NEXT`) after every line — exactly
    the class of bug an integration test exists to catch.
- Phase 8 (this session): wrote `docs/api-patterns.md` (Ollama, headless
  Claude Code, Apify — no OpenRouter section) and this file.

**Known open items carried forward** (see `docs/todo.md`):
- Apify actor slugs (`misceres~indeed-scraper`,
  `bebity~linkedin-jobs-scraper`) are unconfirmed placeholders — verify
  against the live Apify Store before the first non-`OFFLINE_MODE`
  `fetch-vacancies` run.
- PNet/Careers24 coverage, the post-MVP auto-submit phase, and the
  tracking dashboard are all deferred, not scheduled.
