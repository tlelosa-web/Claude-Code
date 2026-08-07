# Session Log — TebelloReborn (Career Engine)

> Chronological record of durable context changes. Ready for the
> `post-task` hook once wired up (currently scaffolded, not firing —
> see hub `CLAUDE.md`'s Hooks section); until then, updated manually
> per Hard Rule #11.

---

## 2026-08-07 — Indeed submit adapter: spec written, screening-question review scope discovered

Unblocked from hub `docs/todo.md` #1 by Tebello answering the two `submission-core.md` Open Items
directly in a hub `/continue` session: platform = **Indeed's own apply form only**; ToS/account-risk
exposure **explicitly accepted**. A third decision (`playwright` as a new runtime dependency) was
also confirmed.

Before writing the Build Queue, did a live `claude-in-chrome` walkthrough of Indeed's real
SmartApply flow (signed in as Tebello, one of the 6 approved vacancies) rather than guessing
selectors — this project's own Apify-payload-shape lesson. **Nothing was submitted.** Found: the
flow is a separate multi-step app (`smartapply.indeed.com`) with per-step URLs; resume selection
defaults away from the generated CV; the flow is reCAPTCHA-protected (CAPTCHA-abort is now a hard,
non-negotiable design rule — never solve/defeat it, distinct from the already-accepted ToS risk);
and **employer screening questions are real, per-posting, and often open-ended free-text** (one
posting asked for an essay describing a recent project). That last finding reshapes the whole
adapter: it can't be a pure deterministic form-filler. Tebello decided screening-question answers
get **LLM-drafted (headless Claude Code, `wrap_untrusted_text()`-wrapped) but held for his explicit
per-question approval** before any submission — never auto-answered unsupervised.

Wrote `docs/specs/indeed-submit-adapter.md`: three new CLI commands
(`prep-submission`/`review-questions`/`submit`), a new `screening_questions` table, a new
`pending_review` outcome distinct from `not_supported`, `CandidateProfile` gaining `email`/`phone`
(neither existed — verified, not assumed), and a phase-level Build Queue. Ran `/codex-review` per
Hard Rule 13 — real second opinion, not a rubber stamp: flagged `can_handle()` as accidentally a
networked/browser action (architectural mismatch with the cheap-predicate contract), missing drift
policy for questions changing between prep and submit, an underspecified CAPTCHA-detection
criterion, missing `prep_failed` outcome-table semantics, and several failure modes (duplicate
submission risk, session expiry mid-wizard, ambiguous success detection). Folded in as the spec's
own advisory section, not yet resolved into the design — that's the next session's first task before
any executor is dispatched.

**No code written this session** — Hard Rule 2 (plan before code >2 files) and Hard Rule 10 (stop
and ask when acceptance criteria are unclear) both applied throughout; three separate
`AskUserQuestion` checkpoints resolved the platform, risk, dependency, and screening-question-review
decisions before the spec was drafted.

**Last completed:** Indeed submit adapter spec drafted + Codex-reviewed (this entry).
**Next task:** Resolve Codex's spec-level findings (concrete CAPTCHA-detection states, question-drift
policy, `can_handle()` static/live split, `prep_failed` table semantics) before dispatching a build
session. Real `profile_seed.json` email/phone values are also needed first (spec Open Item 1).
**Known risks:** None new beyond what the spec itself now documents (reCAPTCHA, screening-question
variability, account-risk — all explicitly accepted or hard-ruled-around, not hidden).
**Blockers:** Build session needs the spec's Open Items answered first (real contact info, which
posting is the Phase G smoke-test target, login-setup script timing).

## 2026-08-06 — Stage 6 submission core built (Phase 16, steps 81–102)

Built the platform-agnostic half of Stage 6: status vocabulary, the `submissions`
attempt log, session-state path handling, capability-based adapter dispatch, and
outcome recording. **249 → 344 tests, zero regressions, 100% coverage on
`src/submission/`.** No `playwright` dependency, no browser binary, nothing on
the wire. Spec: `docs/specs/submission-core.md`.

**The hub spec it came from targeted the wrong platform.** It scoped the build to
LinkedIn Easy Apply only, with Indeed explicitly out of scope. LinkedIn was
dropped from this project on 2026-08-01 (actor `403 actor-is-not-rented`, renting
declined, `_normalize_linkedin()` and the POST block removed) — three days before
that spec was written — and all 10 rows in `career.db` are Indeed. Built as
written it would have shipped a feature able to submit nothing. Scope became the
core; the adapter is a separate task, and it is blocked on Tebello, not on code.

**Codex review found a real contradiction in the spec, pre-build.** Acceptance
criterion 1 refused anything not `approved`, while the transition table allowed
`submission_failed → submitted` and called failures retryable — the retry path was
unreachable from the only CLI that would use it. Resolved by admitting
`submission_failed` to the gate: it is reachable *only* from `approved`, so the
invariant enforced is "this vacancy passed the human gate," not "it is currently
in one exact state." Nine further points folded in as Amendment A1–A9/B1–B6/C1–C3.

**Two corrections to the pre-build verification notes:**

- **No migration was needed after all.** A net-new table's `CREATE TABLE` belongs
  in `init_db()` per this project's own convention, and `vacancies.status` is
  unconstrained `TEXT`, so extending `VALID_STATUSES` is Python-level only —
  exactly the step-59 `VALID_PLATFORMS` precedent. The shared-`user_version` trap
  is real but this build never steps in it. `src/submission/` deliberately has
  **no** `migrations.py`, since an empty stub invites a `(1, …)` entry that would
  be silently skipped forever. The rule is now written into `CLAUDE.md` Hard Rule 6.
- **`.gitignore` genuinely did not cover the session file** — that one held.
  `.session/` added, with a test that reads `.gitignore` so the protection cannot
  regress silently.

**Two deviations from the spec, both recorded in `docs/todo.md`:** steps 90–91
landed as one commit (the `.gitignore` entry alone leaves the suite failing
collection, and Hard Rule 4 requires green tests before a commit); and step 97's
CLI moved from `main.py` to `src/submission/cli.py` after inlining it pushed
`main.py` to 354 lines, past this project's own 300-line standard — matching how
`run_review_gate` already lives in `src/review/cli.py`.

**Hard Rule 1 is now structural at two layers**: `run_submission()` gates on
`vacancy.status` (never on the presence of an `approvals` row, as
`src/review/cli.py`'s closing comment demands), and adapters never write to the
database or transition status, so no future adapter can route around the gate.

**Found and left unfixed, deliberately:** `black . && ruff check .` — the gate
this project's own CLAUDE.md documents — no longer passes on a clean checkout
under this machine's tooling. It reformats 17 untouched files, 7 of them inside
the Hard-Rule-12-protected `_archive_qwen_prototype/`, and `ruff` reports 10
pre-existing errors. Worked around by scoping both tools to the files actually
changed. A repo-wide reformat is its own decision and its own commit; it should
not ride along inside a feature build. Logged as a Known Issue.

**Next:** the site adapter, blocked on two answers from Tebello — which platform
gets the first adapter, and an explicit ToS/account-risk acknowledgement. Neither
is a coding question.

## 2026-08-06 — codex-review submission-core.md: ran

## 2026-08-01 — Review-gate bug fix: skip gate when doc-gen doesn't reach asset_ready

Real bug found 2026-08-01: a CV generation timeout (headless `claude -p`) left a vacancy at
status `scored` with `cv_text`/`cover_letter_text` still `None`, but `_run_pipeline_for_vacancy()`
in `src/main.py` sent it to the human review gate anyway — a human would see "CV: None / Cover
Letter: None" presented for approval. `run_doc_gen` only transitions status to `asset_ready` if
both documents generate successfully, so the fix checks that status before calling
`run_review_gate` and skips (with a diagnostic print pointing at `generation_log`) otherwise.
Built TDD: `6bbd0d8` (RED — `TestDispatchRun` asserts the mock's `asset_ready_vacancy.status` is
`asset_ready`, exposing the missing guard), `1403c47` (GREEN — the status-check guard in
`_run_pipeline_for_vacancy`). Full suite: 239 passing, zero regressions.

## 2026-08-01 — Live vacancy pipeline dashboard (dev tool, not pipeline code)

Added `tools/dashboard_server.py` + `tools/dashboard.html` (`1be39ca`): a
local stdlib-only dev server that polls `career.db` every 4s and renders
vacancies as a kanban board across the 5 pipeline statuses. `asset_ready`
cards get Approve/Reject buttons that call the *same* review-gate DB
functions `src/review/cli.py::run_review_gate()` uses — `save_approval()`
committed before `update_vacancy_status()` — so the dashboard is a second
front end onto the real human-approval gate, not a bypass of it (Hard
Rule #1). Launched via the Browser pane's `preview_start` using a new
`.claude/launch.json` in this project folder.

Not part of the Build Queue or MVP pipeline — a visualization/control aid
only, requested ad hoc. Also added `*.db-shm`/`*.db-wal` to `.gitignore`
(the dashboard's concurrent read access started generating these SQLite
WAL sidecar files; they were previously absent because nothing else read
`career.db` outside of a single process at a time).

No vacancies have reached `asset_ready` yet (all 20 currently-stored
vacancies are `new`), so the Approve/Reject buttons are wired but
untested against a real click — verify once matching + doc-gen has run.

## 2026-07-31 — W1/W2 reviewer nits fixed, PNet/Careers24 build merged to master, PNet mode flipped to auto

The PNet/Careers24 Automated Discovery build (worktree `agent-a6eb29f112cbc6764`,
steps 63–80) was reviewer-approved "APPROVE WITH NITS" — no blockers, two
follow-ups. Both fixed TDD in the same worktree before merge:

- **W1 (extraction-prompt untrusted-text wrap).** `build_extraction_prompt()`
  embedded `raw_page_text` (untrusted, scraped job-posting text) directly
  into the Ollama extraction prompt with no defense-in-depth wrap — the same
  sink shape as `vacancy.description` in `doc_gen`'s `cv_generator.py`/
  `cover_letter_generator.py`, which already uses `runner.wrap_untrusted_text()`.
  RED test asserted the wrapped-text markers appear in the prompt output
  (`4633dd8`); GREEN applied `wrap_untrusted_text()` to `raw_page_text`
  before embedding it (`a5c3285`).
- **W2 (normalize_url over-strips Indeed's `?jk=`).** `normalize_url()`
  stripped the entire query string before building the
  `(company, title, normalize_url(url))` dedupe key — since Indeed's
  canonical job identity lives in `?jk=<id>`, every Indeed URL collapsed to
  the same bare path, silently merging genuinely distinct postings (e.g.
  two reqs from the same employer, same title). RED test asserted
  `?jk=1` and `?jk=2` normalize to *different* strings, while `?jk=1` and
  `?jk=1&utm_source=x` still normalize the same (`5ffc010`); GREEN switched
  `normalize_url()` to an allowlist-based strip of only known tracking
  params (`utm_source`, `utm_medium`, `utm_campaign`, `utm_term`,
  `utm_content`, `gclid`, `fbclid`), preserving `jk` and any other
  significant identifier param (`6068db4`).

`docs/api-patterns.md` updated to document both behaviors in place (the
extraction-prompt untrusted-text wrap, and the tracking-param allowlist).
Full suite: 232 passing, zero regressions, after both fixes.

Worktree branch fast-forward merged into `master` (`9319b5a` — no separate
merge commit needed, `master` was already the merge-base). Full suite
re-run against merged `master`: 232 passing. Worktree removed
(`git worktree remove`) after the merge was confirmed clean.

Per Tebello's earlier in-browser confirmation that
`https://www.pnet.co.za/jobs/operations-foreman/in-gauteng` (bare path, no
query string) renders a working PNet results page with real matches,
`data/discovery_config.json`'s `pnet.mode` was flipped from
`"manual_pending_verification"` to `"auto"` as its own atomic commit on
`master` (`bd72266`) — resolves Open Item 4 from the Amendment. Verified
this doesn't break the PNet-fallback tests: they all construct their own
`tmp_path` discovery-config fixtures rather than reading the real
`data/discovery_config.json`, so the flip is fully test-isolated (232
still passing after the flip).

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
