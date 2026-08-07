# Spec: Indeed Submit Adapter (Stage 6, site-specific)

> Status: planned, not implemented.
> Author: Planner · Date: 2026-08-07
> Builds the first `SubmitAdapter` (per `docs/specs/submission-core.md`'s `Protocol`) against the
> registry that ships empty in that spec. Closes the "Future" item in `docs/todo.md`: "Playwright
> site adapter for Stage 6."
> Written after the two `docs/specs/submission-core.md` §Open Items were answered directly by
> Tebello (2026-08-07, hub `/continue` session): **platform = Indeed's own apply form only**, and
> the **ToS/account-risk exposure is explicitly accepted**. A third decision was also made this
> session, prompted by a finding below: **screening-question answers are LLM-drafted but held for
> Tebello's per-question approval before any submission** — not auto-answered unsupervised.

---

## Goal

Give the 6 already-`approved` Indeed vacancies (and every future one) a real path to `submitted`
that doesn't require Tebello to do the mechanical form-filling by hand — while never letting an
AI-generated answer reach an employer without him having seen that specific answer first.

`career-engine submit --vacancy-id <id>` on an `approved` Indeed vacancy should, when the posting
uses Indeed's own apply form:

- drive a real browser session (your saved Indeed login) to Indeed's SmartApply wizard,
- select the AI-generated CV/cover-letter PDFs instead of the default on-file Indeed Resume,
- fill every screening-question field the system can answer with **either** a deterministic
  profile fact **or** an answer you've already explicitly approved for this exact posting,
- refuse to proceed — abort to manual, not guess — the moment it hits anything it can't handle
  safely: an external-ATS redirect, an unapproved question, or a CAPTCHA challenge,
- submit, confirm the success screen, and record the outcome.

When the posting redirects to an external ATS, or Tebello hasn't yet reviewed its screening
questions, it falls back to the existing `not_supported`/pending path — same honest "still needs
you" signal `submission-core.md` already built, never a false `submitted`.

---

## Findings from live reconnaissance (2026-08-07, this session)

Verified directly against Indeed's real SmartApply flow on one of the 6 approved vacancies
(`Utopia — Project Engineer (Mechanical/Electrical)`, `jk=d7d04674eabafbac`), signed in as Tebello,
via a `claude-in-chrome` walkthrough. **Nothing was submitted** — the walkthrough stopped at the
screening-questions step and navigated away (`force: true` past Chrome's own "unsaved changes"
guard) without filling or submitting anything. Recorded here so the Build Queue below isn't written
blind, per this project's own mocks-lesson (the Apify payload-shape bug).

1. **The flow is a separate app, not the job-posting page.** "Apply with Indeed" navigates to
   `smartapply.indeed.com/beta/indeedapply/form/<module-name>/<step-name>` — a multi-step wizard
   with a visible `%`-complete progress bar. Each step has its own URL segment
   (`resume-selection-module/resume-selection`, `questions-module/questions/1`, …), which is a much
   more reliable "what step am I on" signal than DOM state alone, and should be the adapter's
   primary navigation-state check.

2. **Resume selection defaults away from the generated CV.** Step 1 pre-selects "Use your Indeed
   Resume" (the resume already on Tebello's Indeed account) as the `Recommended` option, with any
   previously-uploaded PDF (a `Tebello Lelosa CV - 2025.pdf` was already on file from prior manual
   use) listed as an alternative. **The adapter must actively select/upload the vacancy's generated
   CV PDF (`src/doc_gen/pdf_export.py`'s output) on every run** — the default is silently the wrong
   document.

3. **reCAPTCHA is present on the flow**, disclosed via a standard "This site is protected by
   reCAPTCHA" notice with Google Privacy Policy/ToS links on the resume-selection step. No visible
   challenge rendered during this walkthrough (consistent with invisible/score-based v3, not a
   solve-a-puzzle v2 challenge) — but this cannot be assumed to hold on every run, every posting, or
   every account-trust state. **Non-negotiable design constraint:** if any CAPTCHA challenge is ever
   rendered mid-flow, the adapter detects it and aborts to `failed` immediately. It never attempts
   to solve, click through, or otherwise defeat it — that is a hard line regardless of the
   already-accepted ToS/account risk, which covers *Indeed noticing automation*, not *defeating
   Google's bot-detection*, and the two are treated as separate risks here.

4. **Screening questions are real, per-employer, and often open-ended.** The one posting inspected
   had three: a plain location text field (trivially fillable from `profile.region`), a
   nominally-yes/no "Are you proficient in AutoCAD?" rendered as a **free-text box, not a
   checkbox**, and a genuinely open-ended essay prompt — *"Please describe your most recent
   hospitality or residential project briefly. Include the project type, scale, the specific design
   phases you handled, and your primary responsibilities."* This is the finding that reshaped this
   spec: there is no deterministic selector for an essay answer about Tebello's own work history.
   Any adapter that fills these has to either fabricate answers (unacceptable — false claims to a
   real employer under Tebello's name) or generate a real answer for review. **Decision: generate
   for review, per §Screening Question Review below.**

---

## Design

### New concept: screening questions are untrusted, employer-authored content

Same exposure class as `vacancy.description` (the prompt-injection risk that produced the ADR-003
security correction to `doc_gen/runner.py`) — a screening question's *text* comes from the
employer's posting/form, unvalidated. Any question text handed to an LLM for drafting goes through
`wrap_untrusted_text()` (already built, `src/doc_gen/runner.py`), exactly as `vacancy.description`
does today. **Drafting reuses the existing headless-Claude-Code path (ADR-003 §3-4), not local
Ollama** — this is generation (write a real answer from profile + context), not scoring, matching
`doc_gen`'s workload shape rather than `matching`'s.

### New module: `src/submission/adapters/`

```
src/submission/adapters/
├── __init__.py
└── indeed.py         ← IndeedAdapter: SubmitAdapter Protocol implementation
```

Playwright itself is imported only here (plus `src/submission/browser.py` below) — no other module
in the project gains a `playwright` import. `pyproject.toml` gains `playwright` as a fourth runtime
dependency (Tebello's explicit go-ahead, 2026-08-07); `playwright install chromium` is a documented
one-time setup step, not run automatically by any pipeline command.

### New sub-stage: Screening Question Prep, Draft, and Review (between `approved` and `submit`)

`career-engine submit`'s existing single-call `adapter.submit(vacancy, session_state_path)` contract
(`submission-core.md`'s `SubmitAdapter.submit()`) assumes everything needed to submit is already
known. Screening questions aren't knowable until a real browser has loaded that specific posting's
form — so filling them can't happen inside one synchronous `submit()` call without either skipping
human review (rejected) or making `submit()` itself block on an interactive approval prompt (rejected
— breaks `--all` batch runs and is a UX regression from every other CLI command in this project).
**Resolution: three new commands, run in sequence, each independently offline/online as noted:**

```
career-engine prep-submission --vacancy-id <id>     (network — opens Playwright, read-only recon)
career-engine review-questions --vacancy-id <id>     (offline — approve/edit drafted answers)
career-engine submit --vacancy-id <id>               (network — unchanged command, now question-aware)
```

**1. `prep-submission` (network, read-only against the real site).** For an `approved` Indeed
vacancy with `is_auto_submittable() == True` (i.e. `IndeedAdapter.can_handle()` returns True — see
below), opens a real browser with the saved session, walks to the screening-questions step, and
extracts each question's exact text and field type (`text`, `textarea`, `select`, `checkbox`,
`file`). **Never fills or submits anything in this pass.** Aborts (records `prep_failed`, vacancy
stays `approved`) on: an external-ATS redirect, a CAPTCHA challenge, a missing saved session, or an
unrecognized field type. Extracted questions are persisted (new `screening_questions` table, below)
with `decision = 'pending'`, then a **local, network-optional** drafting pass runs immediately after
for every free-text/textarea question: `run_claude_code(wrap_untrusted_text(question_text) + profile
context)` produces a `drafted_answer`, stored on the same row. Deterministic fields (a plain
"Location" text field matched confidently to `profile.region`, for example) are drafted the same
way but flagged `auto_fillable = True` — see the confidence rule below.

**2. `review-questions` (fully offline).** Mirrors `src/review/cli.py`'s existing approval-gate
pattern exactly (same `Decision` shape: approve / reject / edit) but scoped to one vacancy's
screening questions instead of its CV/cover letter. Prints each question and its drafted answer;
Tebello approves, edits, or rejects each one individually. **A vacancy cannot proceed to `submit`
while any of its questions are `pending` or `rejected`.** This is Hard Rule 1's principle extended
to new content, not just the CV/cover letter: nothing generated by this system reaches an employer
without Tebello having seen that specific text.

**3. `submit` (network, unchanged command name).** Before calling `adapter.submit()`, the pipeline
now also checks `all_questions_reviewed(vacancy_id)` (new `submission/eligibility.py` function,
alongside the existing `can_handle()` check) — if any question is still `pending`/`rejected`, the
outcome is a new `pending_review` (see table below), **not** `not_supported` — the operator needs to
run `review-questions`, not "submit it by hand." If everything is reviewed, `IndeedAdapter.submit()`
re-opens the browser, re-navigates to the same wizard, selects the generated CV/cover-letter PDFs,
fills every question from its `final_answer` (the approved or edited text), aborts to `failed` on
any CAPTCHA challenge or structural mismatch (the questions changed since `prep-submission` — treat
as untrusted-content drift, never guess), reaches the final review screen, clicks submit, and
confirms the success state before returning `(True, detail)`.

### Outcome vocabulary — extends `submission-core.md`'s table

| `outcome`        | vacancy status after     | meaning                                                        |
|-------------------|--------------------------|------------------------------------------------------------------|
| `submitted`       | `submitted`               | unchanged from submission-core                                   |
| `failed`          | `submission_failed`       | unchanged — now also covers CAPTCHA-abort and posting drift      |
| `not_supported`   | `approved` *(unchanged)*  | unchanged — no adapter, or an external-ATS redirect declined via `can_handle()` |
| `pending_review`  | `approved` *(unchanged)*  | **new** — an adapter exists and the posting is native, but its screening questions aren't fully reviewed yet. Operator action is `review-questions`, not "submit by hand." |

`pending_review` is deliberately its own outcome rather than reusing `not_supported` — conflating
"no automated path exists" with "an automated path exists and is one command away" would hide real
progress from the operator and from any future Stage 7 dashboard reading `submissions` history.

### `screening_questions` table (new)

```sql
CREATE TABLE IF NOT EXISTS screening_questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id     INTEGER NOT NULL REFERENCES vacancies(id),
    question_text  TEXT NOT NULL,
    field_type     TEXT NOT NULL CHECK (field_type IN ('text','textarea','select','checkbox','file')),
    drafted_answer TEXT,
    final_answer   TEXT,
    decision       TEXT NOT NULL DEFAULT 'pending' CHECK (decision IN ('pending','approved','edited','rejected')),
    extracted_at   TEXT NOT NULL,
    decided_at     TEXT
)
```

Lives in `src/submission/db.py` (extends the module built in `submission-core.md`, same file — one
adapter-specific table doesn't earn its own module). **No migration** — same precedent as
`submissions`: net-new table, `CREATE TABLE IF NOT EXISTS` in `init_db()`.

### `IndeedAdapter.can_handle()` — the deterministic-vs-generated confidence rule

`can_handle(vacancy)` returns `True` only when: the vacancy's `url` is a `za.indeed.com/viewjob`
link (not already known to redirect externally — `prep-submission`'s first real check, since this
can't be known from the scraped URL alone) **and** at least the resume-selection step is reachable
without a CAPTCHA challenge. It does not (and cannot) know about screening-question content at this
point — that gate is `pending_review` at `submit` time, not a `can_handle()` decision, because the
questions aren't visible until `prep-submission` actually loads the form.

### Contact info: `CandidateProfile` gains `email` and `phone`

Neither field exists today (`src/profile/schema.py`, `data/profile_seed.json`) — verified, not
assumed. Both are `REQUIRED_FIELDS` additions, Python-validation only (no DB migration — profile
fields aren't `CHECK`-constrained, same precedent as `VALID_PLATFORMS`/`VALID_STATUSES`). Real
values go in `data/profile_seed.json` directly from Tebello (never invented) before this build's
integration test can use anything but a fixture profile.

### Session setup (one-time, manual, outside the pipeline)

`submission-core.md` already built `session.py`'s path resolution
(`SESSION_STATE_PATH`/`session_state_available()`). This spec adds the one piece that actually
writes that file: a standalone script (`tools/indeed_login_setup.py`, **not** a `career-engine`
subcommand — this is a one-time interactive action, not something `--all` or any automated run
should ever trigger) that opens a real, visible (non-headless) Chromium window, lets Tebello log in
to Indeed by hand, and saves `context.storage_state(path=...)` on his explicit confirmation. Rerun
whenever the saved session expires (`prep-submission`/`submit` detect an expired session — landing
back on Indeed's own login page instead of the wizard — and abort with an actionable message, never
a silent failure).

---

## Acceptance Criteria

- `IndeedAdapter` implements `SubmitAdapter` (`platform = "indeed"`, `can_handle()`, `submit()`)
  exactly per `submission-core.md`'s pinned `Protocol` — no change to that contract's shape.
- `career-engine prep-submission --vacancy-id <id>` never fills or submits any form field on the
  real site — read-only recon only, enforced by a real-site smoke test that asserts no `POST`/form
  submission network request fires during this command (see `docs/api-patterns.md`'s network-flag
  convention).
- Screening questions extracted by `prep-submission` are drafted (headless Claude Code,
  `wrap_untrusted_text()`-wrapped) but **never** auto-approved — `decision` starts and stays
  `pending` until `review-questions` records a real human decision.
- `career-engine submit --vacancy-id <id>` on a vacancy with any `pending`/`rejected` question
  returns `pending_review`, leaves status `approved`, and never invokes `IndeedAdapter.submit()`.
- A CAPTCHA challenge detected at any point in either `prep-submission` or `submit` aborts
  immediately to the appropriate outcome (`prep_failed`/`failed`) with that reason recorded in
  `detail` — no retry-through-the-challenge logic exists anywhere in the adapter.
- The adapter selects the vacancy's generated CV/cover-letter PDFs (via
  `src/doc_gen/pdf_export.py`'s existing output paths) on every submit — never relies on Indeed's
  default on-file resume. Asserted by a real-site smoke test checking the uploaded filename in the
  final review step before backing out.
- `CandidateProfile` requires `email`/`phone`; `data/profile_seed.json` carries Tebello's real
  values before the integration test suite exercises anything beyond a fixture profile.
- No module outside `src/submission/adapters/` and `src/submission/browser.py` imports `playwright`.
  `black . && ruff check . && python -m pytest` clean; existing 344 tests continue passing with zero
  regressions; new code ≥ 80% covered on everything that **can** be covered offline (Playwright-driven
  code paths are exempted from the coverage gate and covered by the real-site smoke test instead —
  same reasoning `submission-core.md` never applied to itself, since it had no browser code at all).

---

## Explicitly out of scope

- **Any platform other than Indeed's own native apply form.** PNet, Careers24, LinkedIn, and every
  Indeed posting that redirects to an external ATS all stay `not_supported` — this spec adds exactly
  one adapter.
- **Solving, clicking through, or otherwise defeating a CAPTCHA challenge**, under any framing. If
  this is ever needed to make the adapter "work reliably," that is a stop-and-ask moment for Tebello,
  not an engineering problem to route around.
- **Unsupervised LLM-answered screening questions.** Every drafted answer is reviewed before it can
  reach `submit`. This spec does not build a "trust the draft" fast path, even as an opt-in flag.
- **A tracking dashboard** (Stage 7) reading `screening_questions`/`submissions` history.
- **Any change to `pipeline.py`'s core `run_submission()` gate logic** from `submission-core.md` —
  this spec adds a pre-check (`all_questions_reviewed`) and a new outcome value, not a rewrite of the
  approval-gate structure.

---

## Build Queue (phase-level — full TDD step numbering to be written at build-dispatch time,
matching this project's existing spec convention, once a build session actually starts)

| Phase | Description | Network | Notes |
|---|---|---|---|
| A | `CandidateProfile.email`/`.phone` + `profile_seed.json` real values | offline | Blocks everything below — nothing else can be tested meaningfully without real contact data |
| B | `screening_questions` table + `db.py` extensions (`save_question`, `get_questions_for_vacancy`, `all_questions_reviewed`) | offline | Extends existing `submission/db.py`, no new module |
| C | `pending_review` outcome — `pipeline.py` pre-check, `eligibility.py` extension | offline | Existing `submission-core.md` acceptance criteria (A5-style stable-substring CLI assertions apply here too) |
| D | `src/submission/browser.py` — Playwright session load/expiry-detection, CAPTCHA-detection helper (shared by prep and submit) | offline for the helper logic itself; only exercised live in E/F | The one place `session_state_available()` (built in `submission-core.md`) gets a real consumer |
| E | `IndeedAdapter.can_handle()` + `prep-submission` CLI + question extraction + Claude-Code drafting | network (real Indeed recon required — mocks alone would repeat the Apify payload-shape mistake) | The one-time login-setup script (`tools/indeed_login_setup.py`) is a prerequisite, built first in this phase |
| F | `review-questions` CLI (mirrors `src/review/cli.py`) | offline | |
| G | `IndeedAdapter.submit()` — fill, CAPTCHA-abort, file upload, final submit, success confirmation | network, **real submission** | The one phase that can actually apply for a real job — gets its own explicit Tebello go-ahead per posting before first real use, not just a generic "tests pass" |
| H | `pyproject.toml` (`playwright` runtime dep), docs closeout (`architecture.md`, `CLAUDE.md`, `docs/todo.md`) | offline | |

Phase G's smoke test is necessarily the first real submission this system ever makes — recommend
running it against one specific, Tebello-nominated posting with him watching, not unattended.

---

## Open Items (require Tebello)

1. **Real `profile_seed.json` email/phone values** — needed before Phase A can close.
2. **Which posting is the Phase G smoke test?** A real submission needs to go somewhere; recommend
   picking one of the 6 already-`approved` vacancies deliberately rather than defaulting to
   whichever sorts first.
3. **Login-setup script timing** — `tools/indeed_login_setup.py` (Phase E) needs Tebello present at
   a keyboard to actually log in; not something any agent can do unattended (this is a credential
   action, same hard line as the browser walkthrough that started this spec).

---

## Codex second opinion (advisory) — 2026-08-07

I'll review this as a spec critique, not as an implementation task. I'm grounding the feedback in the text you provided rather than inspecting the repo, since you asked for a second opinion on the spec itself.

The spec is directionally sound: it recognizes the big risks, separates discovery/review/submit, refuses CAPTCHA handling, and avoids unsupervised generated answers. I would not rubber-stamp it as implementation-ready, though. Several acceptance criteria are either too vague to test or conflict with the proposed architecture.

**1. Buried Or Unstated Assumptions**

- The spec assumes Indeed's SmartApply URLs are stable enough to be a "primary navigation-state check": "should be the adapter's primary navigation-state check". That is a useful signal, but brittle as a primary contract. Indeed can A/B test paths, module names, beta routes, or localization. The adapter should combine URL, visible step headings, form landmarks, and expected controls.

- It assumes questions extracted during `prep-submission` will still match during `submit`. The spec handles drift by failing, which is good, but it does not define the matching rule. Exact text match? Normalized whitespace? Same question text but reordered? Required vs optional changed? This needs a concrete drift policy.

- It assumes `prep-submission` can be "read-only" while navigating a live multi-step wizard. Even clicking "Continue" through wizard steps may trigger analytics, draft application state, autosave, or server-side mutations. The spec says "Never fills or submits anything in this pass" — that is narrower than "read-only." It should distinguish "no application submission" from "no network writes at all," because the current smoke-test criterion may be impossible.

- It assumes generated CV and cover-letter PDF paths are unambiguous ("via `src/doc_gen/pdf_export.py`'s existing output paths") but does not define how the adapter maps vacancy ID to the correct PDF pair, verifies freshness, or handles missing/stale PDFs.

- It assumes cover-letter upload is always available in Indeed's native flow. Many flows may ask only for resume, make cover letter optional, or have no upload field. The spec does not define behavior when only one upload control exists.

- It assumes `can_handle()` can safely open the real site and inspect reachability ("returns True only when… at least the resume-selection step is reachable"). That makes `can_handle()` a networked/browser action, which is unusual for a capability predicate and may surprise callers. If `submission-core.md` treats `can_handle()` as cheap/deterministic, this is an architectural mismatch.

- It assumes "local, network-optional" drafting using headless Claude Code ("review-questions (fully offline)" / "local, network-optional drafting pass"). Claude Code may not be offline depending on configuration. If offline operation matters, this needs a hard definition.

**2. Missing Or Untestable Acceptance Criteria**

- CAPTCHA detection is underspecified — needs concrete detectable states: visible iframe? `g-recaptcha` badge? challenge modal? URL to Google challenge endpoint? The spec already notes invisible reCAPTCHA presence is normal, so the adapter must not confuse "protected by reCAPTCHA" with "challenge rendered."

- The "no POST/form submission network request" smoke test is likely overbroad. Modern apps POST for telemetry, CSRF/session validation, autosave, feature flags, or step transitions. A better criterion is "no request to known application-submit endpoints" plus "no filled applicant field values sent."

- `pending_review` has no persistence detail — does a repeated `submit` attempt create a new `submissions` row, update the latest, or dedupe?

- `prep_failed` is referenced ("records `prep_failed`", "appropriate outcome (`prep_failed`/`failed`)") but not included in the outcome table. If it's a submission outcome, it needs table semantics; if not, where is it recorded?

- `all_questions_reviewed(vacancy_id)` is insufficient without a prep-completed condition — a vacancy with zero extracted questions could mean "no questions" or "prep never ran." The submit gate needs to distinguish these states.

- Acceptance for "structural mismatch" (questions changed since `prep-submission`) doesn't define what is compared: count, text, field type, requiredness, options, labels, normalized prompt, hidden metadata.

- Field types are too coarse — `checkbox` can be boolean, multi-select, consent, or required acknowledgement; `select` needs allowed options persisted. The schema stores no `required`, `options`, or field identifier.

- "Matched confidently" for deterministic fields (e.g. Location → `profile.region`) is not concretely testable — regex? label whitelist? LLM classification? exact match? This is an important safety boundary and needs real acceptance criteria.

- "≥ 80% covered on everything that can be covered offline" is vague — should name exempt modules/functions explicitly rather than leaving it a build-time negotiation.

**3. Failure Modes Not Considered**

- Indeed may ask work-authorization, salary-expectation, or EEO/demographic-style questions — legally/sensitively different from ordinary screening questions.
- File upload can fail silently, upload the wrong stored document, or get truncated in the filename shown — the final-review filename check alone isn't enough if Indeed stores multiple similarly-named files.
- A flow may allow editing the Indeed Resume but not uploading a fresh PDF — the spec assumes active upload is always possible.
- Session state may expire mid-flow, not only at initial navigation.
- Success confirmation may be ambiguous ("Application submitted" vs "Next steps" vs a bare redirect) — needs conservative positive *and* negative patterns.
- Partial side effects during submit aren't classified — a failure after files are uploaded but before final submit may leave a modified draft application on Indeed that `failed` doesn't capture.
- No duplicate-submission detector — a prior manual application, or a prior automated success that failed to record locally, could cause a resubmit attempt.
- No rate-limiting/backoff/lockout-escalation policy, despite the accepted account-risk exposure.
- Prompt-injection handling wraps the question text but doesn't explicitly instruct the drafting prompt to answer only from profile facts and never invent — worth being explicit here, not just relying on the wrap.
- Recovery path for a `rejected` question is unclear — can `review-questions` change `rejected` → `edited` later, or does rejection block that vacancy permanently?

**4. Alternatives I Would Seriously Weigh**

- Split `can_handle()` into a cheap static check (platform/URL metadata) and a separate live check (`inspect_apply_flow()` / `prep-submission`) — avoids turning an adapter predicate into a browser workflow with side effects.
- Add an explicit prep-status concept (a `submission_preps` table, or a status column) instead of inferring state from `screening_questions` rows alone — "not prepped," "prepped with zero questions," "prep failed (CAPTCHA)," "external ATS," and "questions extracted" are all distinct states the current table can't cleanly represent.
- Store extracted field metadata as structured JSON (`required`, `options`, `field_key`, `step_url`, `position`, `label`, normalized hash) rather than the current flat columns — makes drift detection and safe filling much more robust.
- Require review for *all* employer-authored questions in the first implementation, including nominally "deterministic" ones — a profile fact can still be wrong in context, and the goal's own promise ("never letting an AI-generated answer reach an employer without him having seen that specific answer first") arguably should extend to any employer-facing answer, not just generated ones.
- Make Phase G a documented supervised live run with explicit confirmation and logging rather than calling it a "smoke test" — that framing blurs test and production behavior for what is, in fact, the first real job application this system will ever submit.
- Consider Playwright trace/video capture for supervised failures, with explicit privacy handling since application pages carry personal data.

Bottom line: the spec has the right safety posture, but it needs tighter state modeling, clearer live-site side-effect boundaries, and more precise criteria for CAPTCHA, question drift, deterministic autofill, and success detection before I would call it build-ready.

_Advisory only — reviewer agent retains sole APPROVE/BLOCK authority._
