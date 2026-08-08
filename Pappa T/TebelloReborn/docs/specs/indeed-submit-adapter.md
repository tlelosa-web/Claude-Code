# Spec: Indeed Submit Adapter (Stage 6, site-specific)

> Status: planned, not implemented. **Codex fold-in complete (Amendment, 2026-08-07)** — read
> §Amendment before building; it is authoritative wherever it conflicts with the sections above.
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

## Findings from live reconnaissance, second pass (2026-08-08, Phase E build session)

Driven by Playwright against the real site with Tebello's signed-in session, read-only. **No form
field was filled and nothing was submitted** — proven rather than asserted: every non-GET request
was recorded, and all of them were telemetry (`beaconrpc/log`, `signals/v1/log`, snowplow,
`frontendlogging`), `graphql` reads, or a `urlSafetyCheck`.

**This pass ended by hitting Cloudflare's bot challenge, and stopped there.** See finding 5.

1. **Indeed refuses an automated sign-in.** The §Session setup design — a Playwright window driven
   through Indeed's login, exporting `context.storage_state()` — does not work. Three attempts, all
   answered with "Something went wrong. Refresh the page and try again" at the email step, in a
   browser that was otherwise functioning. **Defeating that detection is out of scope and stays out
   of scope**, on the same hard line as finding 3's CAPTCHA rule: the accepted ToS/account risk
   covers Indeed *noticing* automation, not hiding it from them, and evasion is the likeliest route
   to a real account being actioned.
   **Resolution, built:** the login left automation entirely. `tools/indeed_login_setup.py` starts
   *ordinary* Chrome as a plain subprocess against a dedicated profile directory; Tebello signs in
   by hand in a browser nothing is driving; Playwright reuses that profile afterwards via
   `launch_persistent_context(channel="chrome")`. The profile is dedicated and never a copy of his
   real one — copying that would pull every site's cookies and his saved passwords into the project
   directory, far more exposure than the single-site session it replaces.

2. **The apply flow reaches the wizard fine once signed in — it is just slow, and slow in stages.**
   The `Apply with Indeed` button initialises asynchronously (Indeed emits its own
   `buttonLoadStart`/`buttonLoadEnd` beacons), and clicking before it settles earns a
   `buttonRageClick` beacon and a bounce straight back to the posting with `&from=iaBackPress`. The
   first attempt did exactly that and wrongly read it as the flow refusing.
   The real sequence, measured: click → `smartapply.indeed.com/beta/indeedapply/applybyapplyablejobid?…`
   (bootstrap) → `/form/resume-selection-module` (shell, 1 `data-testid`, body text is literally
   "loading") → ~10–12s later `/form/resume-selection-module/resume-selection` (53 `data-testid`s,
   21 buttons). **Wait on rendered content, never on the URL** — the URL is correct a full ten
   seconds before the step exists.
   The settled URL segment matches `browser.WIZARD_STEPS["resume_selection"]` exactly, so Phase D's
   constant needs no correction.

3. **`FrameView.visible` must be computed with a real visibility check, not a bounding box.** This
   is the most load-bearing finding of the pass. The reCAPTCHA v3/enterprise **badge** is an
   `recaptcha/enterprise/anchor` iframe measuring 256×60 at `visibility: hidden` — it has a real,
   non-zero bounding box. An adapter that derives `visible` from the box alone reports it as visible;
   `captcha_reason()` then correctly applies A7 rule 5 ("a visible anchor frame means the flow
   escalated to v2") and **aborts a perfectly healthy run**. Observed and measured on the live page.
   `browser.py`'s docstring already specifies the right definition — "a real, non-zero bounding box
   *that isn't `visibility:hidden`/`display:none`*" — and the first recon implemented half of it.
   `inspect_apply_flow()` must use Playwright's own `is_visible()`, which accounts for display,
   visibility and box together. **Phase D's judgment layer was correct throughout; only the
   observation lied to it**, which is the split working as designed.

4. **The resume-selection step confirms finding 2 of the 2026-08-07 pass, unchanged.** Rendered
   text shows "Use your Indeed Resume … Recommended" pre-selected, with
   `Tebello Lelosa CV - 2025.pdf` (uploaded Feb 24, 2025) as the alternative. The adapter must
   actively select the generated CV on every run. The step also carries the standard
   "This site is protected by reCAPTCHA…" notice on a completely healthy run — the never-abort case
   Phase D wrote seven tests for, now observed a second time.

5. **Cloudflare bot-challenges the job page after repeated automated visits.** After four
   Playwright runs against the same posting inside about fifteen minutes, `za.indeed.com/viewjob`
   began returning a page titled "Just a moment..." with no apply button. The escalation was visible
   one run earlier as a `za.indeed.com/cdn-cgi/challenge-platform/h/b/jsd/oneshot/…` POST.
   **The recon stopped here and no attempt was made to pass the challenge.** Consequences for the
   remaining build, all of which are real and none of which are worked around:
   - **The questions step was never reached this pass**, so its selectors, its URL segment and the
     review step's segment are still unknown. `WIZARD_STEPS["questions"]` remains unverified beyond
     the 2026-08-07 walkthrough.
   - **Automated runs must be paced.** Whatever `inspect_apply_flow()` ends up doing, a rapid
     sequence of them against one posting is enough to trip this. `prep-submission` having no
     `--all` already helps; it is not sufficient on its own.
   - **This is evidence about Phase G, not just Phase E.** The same detection sits in front of the
     submit path, where the cost of hitting it is a real application to a real employer.

---

## Findings from live reconnaissance (2026-08-07, first pass)

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

## Amendment — 2026-08-07 (Codex review fold-in)

Per `CLAUDE.md` Hard Rule 13, the strongest points from the Codex second opinion below are folded
back here **before** any Executor is dispatched. Same convention as `submission-core.md`'s
amendment: this section is authoritative where it conflicts with the sections above, and nothing
above is edited in place so the original reasoning stays readable.

Groups: **A** — accepted, they change the build; **B** — accepted as clarifications that were
implicit and are now explicit; **C** — considered and deliberately not adopted, with the reason.

Four findings below (**A2**, **A3**, **A9**, **A11**) came from reading the actual code and the live
`career.db` while folding this in, not from Codex. They are recorded in the same groups because they
change the build the same way.

---

### A. Accepted — these change the build

**A1. `can_handle()` splits into a cheap static predicate and a separate live check.**
Codex is right, and this is the finding with the widest blast radius. `submission-core.md`'s pinned
`SubmitAdapter.can_handle()` is consumed by `eligibility.get_adapter()`, which is called by
`pipeline._decide()` on **every** `submit` run — including `--manual` paths and every
`not_supported` case. Making it open a browser would put a network action inside what the core
treats as a dict-lookup-plus-predicate, and this spec's own §Acceptance Criteria promises "no change
to that contract's shape."

Resolution — `IndeedAdapter.can_handle(vacancy)` is **pure, offline, and side-effect-free**:

```python
def can_handle(self, vacancy: Vacancy) -> bool:
    # Static URL shape only. No network, no browser, no DB. Live reachability
    # is inspect_apply_flow()'s job, run by prep-submission.
    host, path = urlsplit(vacancy.url).hostname or "", urlsplit(vacancy.url).path
    return (
        vacancy.platform == "indeed"
        and host.endswith("indeed.com")
        and path.startswith("/viewjob")
    )
```

Everything live moves to a new adapter method **outside** the Protocol,
`inspect_apply_flow(vacancy, session_state_path) -> PrepResult`, called only by `prep-submission`.
The external-ATS redirect, the resume-selection step's reachability, and the CAPTCHA check are all
its findings — persisted as prep state (A2), never re-derived at `submit` time by reopening a
browser inside a predicate.

Consequence: a vacancy that redirects to an external ATS **passes** `can_handle()`. It is declined
at `submit` by the prep-state gate (A2), recording `not_supported` with the ATS reason — the same
operator-visible outcome the original text intended, reached without a networked predicate.

**A2. Prep state gets its own table — `submission_preps`. Adopted from Codex §4.**
`all_questions_reviewed(vacancy_id)` over `screening_questions` alone cannot distinguish "prep never
ran" from "prepped, this posting genuinely has zero questions" — both are zero rows, and one of them
must be submittable while the other must not. Inferring state from the absence of rows is the bug.

```sql
CREATE TABLE IF NOT EXISTS submission_preps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id   INTEGER NOT NULL REFERENCES vacancies(id),
    status       TEXT NOT NULL CHECK (status IN (
                     'questions_extracted','no_questions','external_ats',
                     'captcha_detected','session_expired','unsupported_form','error')),
    detail       TEXT,
    step_url     TEXT,
    prepped_at   TEXT NOT NULL
)
```

Append-only, same discipline as `submissions` and `approvals`: several rows per vacancy are
expected (a failed prep, then a successful re-prep). `get_latest_prep(vacancy_id)` resolves
multiplicity with `ORDER BY id DESC LIMIT 1`, exactly as `get_approval_by_vacancy_id` does. "Not
prepped" is the absence of any row — the one state that genuinely *is* an absence.

The submit gate becomes, in order:

| latest prep state | `submit` outcome | operator's next move |
|---|---|---|
| *(no row)* | `pending_review` | run `prep-submission` |
| `external_ats` | `not_supported` | submit by hand |
| `captcha_detected`, `session_expired`, `unsupported_form`, `error` | `pending_review` | re-run `prep-submission` (after the login setup, for `session_expired`) |
| `no_questions` | proceeds to `IndeedAdapter.submit()` | — |
| `questions_extracted`, all questions decided `approved`/`edited` | proceeds to `IndeedAdapter.submit()` | — |
| `questions_extracted`, any question `pending` or `rejected` | `pending_review` | run `review-questions` |

`all_questions_reviewed(vacancy_id)` is renamed **`submission_prep_ready(vacancy_id)`** and returns
this decision, not just the question tally. The old name described half the check.

**A3. `prep_failed` is removed from the outcome vocabulary — it was never a submission outcome.**
Codex flagged it as referenced-but-undefined. The right resolution is deletion, not definition:
`prep-submission` does not attempt a submission, so recording its failure in `submissions` would put
non-attempts in an attempt log and mislead any Stage 7 reader counting rows. Every prep failure is a
`submission_preps` row (A2) with a specific `status`, which carries strictly more information than a
single `prep_failed` value could.

`submissions.outcome` therefore gains exactly **one** new value, `pending_review`. Amended outcome
table — replaces the version in §Design:

| `outcome` | vacancy status after | meaning |
|---|---|---|
| `submitted` | `submitted` | unchanged from submission-core |
| `failed` | `submission_failed` | unchanged — now also covers CAPTCHA-abort mid-submit, question drift, session expiry mid-flow, and unconfirmed submits (A13) |
| `not_supported` | `approved` *(unchanged)* | no adapter, **or** prep found an external-ATS redirect |
| `pending_review` | `approved` *(unchanged)* | an adapter exists and the posting is native, but prep hasn't run or its questions aren't fully reviewed. Operator action is `prep-submission`/`review-questions`, not "submit by hand" |

**A4. Changing `submissions.outcome`'s CHECK constraint is a real schema change with a real trap —
and the window to do it cleanly is open right now.** Verified 2026-08-07 against the live
`career.db`: `PRAGMA user_version = 4`, tables are `candidate_profile`, `vacancies`,
`generation_log`, `approvals` — **`submissions` does not exist yet**. Stage 6 has never been run
against the live database.

That matters because `src/submission/db.py`'s `init_db()` uses `CREATE TABLE IF NOT EXISTS` with the
outcome CHECK inlined as `('submitted','failed','not_supported')`. Editing that DDL string is
sufficient **only while the table doesn't exist**. The moment anyone runs `career-engine submit`
once before Phase B lands, `IF NOT EXISTS` silently keeps the old constraint and every
`pending_review` insert fails at runtime with a CHECK violation — far from the code that caused it.
This is the same class of trap as Hard Rule 6's shared `user_version`, in a different disguise.

Two-part resolution:

1. Phase B edits the DDL to `CHECK (outcome IN ('submitted','failed','not_supported','pending_review'))`.
2. `init_db()` gains a **DDL-drift guard**: after the `CREATE TABLE IF NOT EXISTS`, read
   `sqlite_master.sql` for `submissions` and raise a named error if the stored DDL's outcome list
   doesn't contain every `SubmissionOutcome` value. A test asserts this by creating a table with the
   old 3-value constraint and confirming `init_db()` refuses loudly. Failing at init with an
   actionable message beats failing at insert with a CHECK violation.

If the guard ever does fire on a real database, the fix is SQLite's standard table rebuild
(`CREATE TABLE submissions_new` … `INSERT INTO … SELECT` … `DROP` … `ALTER … RENAME`) inside a
migration at a globally-unique `user_version ≥ 5` — **not** an in-place constraint edit, which
SQLite does not support.

**A5. `CandidateProfile.email`/`.phone` DO need a migration. The spec's "no DB migration" claim is
a false analogy and would not have worked.** Verified against `src/profile/db.py` and the live
schema: `candidate_profile` is a real table with named columns
(`id, name, region, skills, experience, target_titles, industries, salary_floor`), and
`upsert_profile()` writes them by name. The cited precedents do not apply — `VALID_PLATFORMS` and
`VALID_STATUSES` validate *values* in a column that already exists (`vacancies.status`, unconstrained
`TEXT`). `email` and `phone` are **new columns that do not exist**; `upsert_profile()` would fail
with `no such column: email` the first time it ran.

Resolution — Phase A adds to `src/profile/migrations.py` (currently `MIGRATIONS = []`):

```python
MIGRATIONS: list[tuple[int, str]] = [
    (5, "ALTER TABLE candidate_profile ADD COLUMN email TEXT"),
    (6, "ALTER TABLE candidate_profile ADD COLUMN phone TEXT"),
]
```

Versions **5 and 6**, not 1 and 2 — Hard Rule 6 exactly. `vacancy_search` holds 1–4 and the live DB
is at 4, so `(1, …)` here would be skipped forever with no error. This is the first migration this
project has written since that rule was recorded, and it is the case the rule was written for.

Both columns are nullable at the DB level and required at the Python level (`REQUIRED_FIELDS`
addition) — an existing row cannot be back-filled by a migration with values only Tebello has, and
`ALTER TABLE ADD COLUMN NOT NULL` without a default is rejected by SQLite anyway. The Python
requirement is what enforces presence going forward; a test asserts `CandidateProfile` refuses to
construct without both.

**Note before Phase A runs:** these migrations auto-apply to the live `career.db` on the next
`init_db()` — including from `career-engine list`. `ADD COLUMN` is additive and does not touch
existing data, but back up `career.db` first regardless; it holds the 6 approved applications.

**A6. Question-drift policy — concrete, testable, and conservative.** Codex is right that "structural
mismatch" wasn't defined. Each extracted question stores a **fingerprint**:

```
fingerprint = sha256(
    norm(question_text) + "\x1f" + field_type + "\x1f" + str(required) + "\x1f" + norm_options
).hexdigest()
```

- `norm(s)` = casefold → collapse every whitespace run to a single space → strip → strip one
  trailing `*` or `:` (required-markers and label punctuation are styling, not identity).
- `norm_options` = for `select`/`checkbox`, the option labels each `norm()`'d, **sorted**, joined by
  `\x1f`; empty string for free-text types.

At `submit`, the adapter re-extracts the live form and compares **sets** of fingerprints:

- `live_set == stored_set` → proceed. Order and on-page position are deliberately excluded from the
  fingerprint: a reordered form is the same form, and position is stored separately for filling, not
  for identity.
- `live_set != stored_set` → **abort to `failed`**, in both directions. A question that appeared is
  obviously unsafe; a reviewed question that vanished means the form changed underneath the review,
  and guessing which change was benign is exactly the judgment this spec refuses to make.
- `detail` records the counts and the first differing `norm()`'d question text, truncated to 120
  chars — enough to diagnose, short enough not to dump employer content into the log.

Re-running `prep-submission` is the recovery path: it writes a fresh `submission_preps` row and a
fresh question set for review.

**A7. CAPTCHA detection — concrete states, and the distinction Codex correctly insisted on.** The
recon already established that a reCAPTCHA *notice* is present on a normal, healthy flow. Confusing
"protected by reCAPTCHA" with "a challenge is being shown" would abort every single run.

**Abort** (`captcha_detected` at prep, `failed` at submit) on any of:

1. A **visible** iframe (non-zero bounding box, not `visibility:hidden`/`display:none`) whose `src`
   contains `recaptcha/api2/bframe` or `recaptcha/enterprise/bframe` — the challenge frame,
   distinct from `anchor`.
2. A visible iframe matching `iframe[title*="recaptcha" i][title*="challenge" i]`.
3. hCaptcha equivalent: a visible iframe whose `src` contains `hcaptcha.com` **and** `challenge`.
4. Navigation to a URL on `google.com` whose path contains `/sorry/` (Google's block interstitial).
5. A visible `recaptcha/api2/anchor` iframe — the "I'm not a robot" checkbox. Invisible v3 never
   renders this; if it is on screen and interactive, the flow has escalated to v2.

**Not a challenge — never abort on these:**

- The "This site is protected by reCAPTCHA and the Google Privacy Policy and Terms of Service
  apply" text notice.
- The floating `.grecaptcha-badge` element.
- Any `api2/anchor` or `bframe` iframe with a zero-size or hidden bounding box (the normal
  invisible-v3 case observed during recon).

Detection runs at three points: after every navigation, before every field fill, and immediately
before the final submit click. On detection: no screenshot is captured (C3), `detail` records
`"captcha challenge detected at <step-url>"`, and the run aborts. **No retry, no reload, no
wait-and-see loop exists anywhere in the adapter** — a reload after a challenge is a retry through
it by another name.

**A8. "Read-only" is redefined into something achievable and testable.** Codex is right that the
"no `POST` fires" criterion is likely impossible — analytics, session validation, feature flags and
step transitions all POST on a live wizard. Replaces that acceptance criterion with two assertions,
both enforced by Playwright request interception during `prep-submission`:

1. **No request to an application-submit endpoint.** A denylist of URL patterns observed in recon
   plus obvious variants (`*/apply/submit*`, `*/indeedapply/*/submit*`, `*graphql*` operations whose
   body names an apply/submit mutation). Any match fails the test.
2. **No applicant-supplied value leaves the browser.** No request body during prep may contain the
   profile's `email`, `phone`, or any `final_answer` text. This is the assertion that actually
   encodes the intent — prep may talk to Indeed, but nothing of Tebello's is sent.

`prep-submission` is documented as "no application data submitted," not "no network writes."

**A9. `prep-submission` is a network command in two separate senses — the spec's "local,
network-optional" drafting claim is wrong.** Verified in `src/doc_gen/runner.py`: `run_claude_code()`
shells out to `claude -p`, which is a subscription-backed CLI that requires connectivity. It is a
*local subprocess*, which is what ADR-003 says and what `CLAUDE.md`'s External Client Patterns table
means by excluding it from rate limiting — it is not an *offline* operation.

Corrected: `prep-submission` requires network for **both** the browser walkthrough and the drafting
pass, and its failure modes include `claude` being unreachable or throttled. When drafting returns
`throttled`/`error` (the runner returns these as data, never raises), the extracted questions are
still persisted with `drafted_answer = NULL` and `decision = 'pending'`, and the prep row is
`questions_extracted` — a throttle costs the draft, not the extraction. `review-questions` then
shows an empty draft and Tebello writes the answer himself. Only `review-questions` is genuinely
offline; `CLAUDE.md`'s Offline-First Rule is satisfied by that command and by the whole gate/state
layer, not by prep.

**A10. Every employer-authored question is reviewed. The `auto_fillable` "matched confidently"
concept is deleted.** Codex's §4 point lands squarely on this spec's own stated goal — "never
letting an AI-generated answer reach an employer without him having seen that specific answer
first." A location field auto-filled from `profile.region` is still an answer Tebello's name goes on,
and "matched confidently" was never going to be testable (regex? label whitelist? LLM classification?
all three were in scope and none were specified).

Removed entirely: no `auto_fillable` column, no confidence rule, no deterministic-fill fast path.
Every extracted question is `pending` until `review-questions` records a decision. Deterministic
ones are pre-drafted from profile facts so approving them is one keystroke — the cost is a keystroke,
and the thing bought is that the promise in §Goal is literally true.

**A11. Sensitive question classes are never LLM-drafted.** Codex's §3 point. Work-authorization,
compensation, and EEO/demographic questions are legally and personally different from "describe a
recent project," and a drafted answer to any of them is a liability even with review — the draft
anchors the answer.

`screening_questions` gains `sensitivity TEXT NOT NULL DEFAULT 'ordinary' CHECK (sensitivity IN
('ordinary','compensation','work_authorization','demographic'))`, classified at extraction by a
conservative keyword list (documented in the module, not inline in a query). For any value other
than `ordinary`: **no drafting call is made at all**, `drafted_answer` stays `NULL`, and
`review-questions` prints the classification alongside the question so Tebello knows why it is blank.
He types the answer or the vacancy stays unsubmittable. Misclassifying an ordinary question as
sensitive costs one typed answer; the reverse costs a drafted answer about his immigration status or
salary floor, so the list errs toward over-matching.

**A12. Field metadata is stored structurally, not as three flat columns.** Codex's §4 point, adopted
— `field_type` alone cannot fill a `select` (no options), cannot honor a required marker, and gives
drift detection nothing to compare. Amended table, replacing the version in §Design:

```sql
CREATE TABLE IF NOT EXISTS screening_questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id     INTEGER NOT NULL REFERENCES vacancies(id),
    prep_id        INTEGER NOT NULL REFERENCES submission_preps(id),
    question_text  TEXT NOT NULL,
    field_type     TEXT NOT NULL CHECK (field_type IN ('text','textarea','select','checkbox','radio','file')),
    field_key      TEXT,
    required       INTEGER NOT NULL DEFAULT 0,
    options_json   TEXT,
    step_url       TEXT NOT NULL,
    position       INTEGER NOT NULL,
    fingerprint    TEXT NOT NULL,
    sensitivity    TEXT NOT NULL DEFAULT 'ordinary' CHECK (sensitivity IN ('ordinary','compensation','work_authorization','demographic')),
    drafted_answer TEXT,
    final_answer   TEXT,
    decision       TEXT NOT NULL DEFAULT 'pending' CHECK (decision IN ('pending','approved','edited','rejected')),
    extracted_at   TEXT NOT NULL,
    decided_at     TEXT
)
```

`radio` added to `field_type` — Codex is right that `checkbox` was carrying too many meanings, and
the recon's "nominally yes/no rendered as free text" finding shows the mapping cannot be assumed
from the question's wording. `prep_id` ties each question set to the prep run that produced it, so a
re-prep's questions never mix with a stale set. `options_json` is a JSON array of labels, `NULL` for
free-text types — the same `json.dumps` convention `profile/db.py` already uses for list fields
rather than a second serialization style.

Still no migration: both tables are net-new, so `CREATE TABLE IF NOT EXISTS` in `init_db()` per the
project's convention (unchanged from the original text — that part was right).

**A13. Success detection needs positive *and* negative patterns, and ambiguity is not "failed".**
Codex's §3 point, and the most dangerous one in the list: reporting `failed` on a submission that
actually went through invites a duplicate application on retry.

- **Confirmed success:** the post-submit URL matches a known confirmation route **and** the page
  shows a confirmation phrase from a conservative positive list (`"application submitted"`,
  `"your application has been submitted"`, `"applied"` as a status label — exact strings pinned at
  Phase G against the real screen, not guessed now). → `(True, detail)`.
- **Confirmed failure:** still on the questions/review step, a visible validation error, or a
  CAPTCHA/session-expiry abort. → `(False, detail)`.
- **Ambiguous** — anything else, including a bare redirect or a timeout after the submit click. →
  `(False, "UNCONFIRMED: submit clicked, outcome not confirmed — check Indeed before retrying")`.
  The `UNCONFIRMED:` prefix is load-bearing, not cosmetic: **the duplicate-submission guard (A14)
  refuses any further automated attempt on a vacancy whose latest attempt detail starts with it.**
  Tebello resolves it by checking Indeed and either running `submit --manual` (it went through) or
  re-running `prep-submission` (it did not), which clears the block by writing a fresh prep row.

**A14. Duplicate-submission guard.** Codex's §3 point; three independent checks, all before any
form interaction:

1. Any prior `submissions` row for this vacancy with `outcome = 'submitted'` → refuse. Should be
   unreachable (`submitted` is terminal), but a manual DB edit is exactly how it becomes reachable.
2. The latest attempt's detail starts with `UNCONFIRMED:` → refuse with the A13 message.
3. The live posting shows an already-applied state ("You applied", an applied badge, or Indeed
   declining to re-open the apply flow) → record `failed` with detail
   `"already applied — Indeed reports an existing application; use --manual to record it"`. This is
   honest: something applied, but this run did not, and claiming `submitted` would assert an action
   the system did not take (the same reasoning behind `--manual`'s wording in submission-core A9).

**A15. `--all` does not auto-submit in this build.** This is the answer to Codex's "no
rate-limiting/backoff/lockout-escalation policy," and it is a policy rather than an engine.
`submit --all` continues to work exactly as `submission-core.md` A6 specified for `not_supported`,
`pending_review`, and `--manual` — but a vacancy that would reach `IndeedAdapter.submit()` under
`--all` is instead reported as `pending_review` with detail `"auto-submit requires an explicit
--vacancy-id"`. Real applications go out one at a time, by explicit id, in this build.

Rationale: the accepted account-risk exposure is per-account, and a batch that submits six real
applications in ninety seconds is a materially different risk from six deliberate single runs. A
backoff/jitter policy can be designed later against observed behavior; refusing the batch needs no
tuning and cannot be mis-tuned.

**A16. Generated-PDF resolution gets a real helper, plus explicit missing/stale/optional handling.**
Codex's §1 point. Verified: `src/doc_gen/pdf_export.py`'s `_export()` builds
`{sanitize(vacancy.company)}_{vacancy.id}_{cv|cover_letter}.pdf` under `output_dir` (default
`exports`, `Settings.EXPORTS_DIR`), and `generation_log` stores **no path column** — so there is
nothing in the database to look the path up from, and the adapter must reconstruct it.

- Phase G promotes the naming into a public `resolve_export_paths(vacancy, output_dir) ->
  tuple[Path, Path]` in `pdf_export.py`, used by both `_export()` and the adapter. The format string
  is never duplicated into the adapter — that is how the two drift apart.
- **Missing CV PDF** → abort before opening the browser, `failed`, detail names the expected path
  and says to re-run `career-engine run --vacancy-id <id>`.
- **Staleness** is explicitly *not* checked against `generation_log` timestamps in this build (the
  PDF's mtime vs. an approval time proves nothing useful — an edit at review time is recorded as
  text in `approvals`, not re-rendered). Recorded as a known limitation rather than a silent
  assumption.
- **Cover letter optional:** if the form exposes no cover-letter upload control, proceed with the CV
  alone and say so in `detail`. If it exposes **no document-upload control at all** (only "use your
  Indeed Resume"), abort prep as `unsupported_form` — submitting the wrong document is worse than
  not submitting.

**A17. Navigation state is a combined signal, not a URL contract.** Codex's §1 point. The recon's URL
observation stands as the *primary* signal, but each step check requires the URL segment **and** at
least one structural landmark (the step heading, or a control the step must have — the resume list,
the question fieldset, the review summary). A URL match with no matching landmark is treated as an
unrecognized state: `unsupported_form` at prep, `failed` at submit. Indeed A/B-testing a route
should degrade to an honest abort, not to filling the wrong step.

**A18. Session expiry is checked continuously, not just at startup.** Codex's §3 point. The
navigation check (A17) also fails when the current URL is an Indeed auth host/path or the page shows
the login form. At prep → `session_expired`; at submit → `failed`, detail
`"session expired mid-flow at <step-url> — re-run the login setup"`. Both name the setup script.

**A19. The coverage exemption is named explicitly, not negotiated at build time.** Codex's §2 point.
Phase H adds to `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "src/submission/browser.py",
    "src/submission/adapters/*",
    "tools/*",
]
```

Everything else under `src/submission/` stays under
`python -m pytest --cov=src/submission --cov-fail-under=80` (the gate `submission-core.md` A7 added).
The omitted files are covered by the Phase H supervised live run instead. The list is in version
control, so widening it is a reviewable diff rather than a build-time judgment call.

**A20. The drafting prompt states the constraint; the wrapper is not assumed to carry it.** Codex's
§3 point. `wrap_untrusted_text()` marks the question as data, which stops it being read as an
instruction — it says nothing about what the answer may contain. The drafting instruction therefore
states explicitly: answer only from the supplied profile facts; never invent an employer, date,
qualification, certification, or figure; if the profile does not support an answer, return the exact
token `INSUFFICIENT_PROFILE_DATA`. That token is stored as the `drafted_answer` verbatim and
`review-questions` renders it as a prompt for Tebello to write the answer himself, rather than
hiding it as an empty draft.

**A21. Phase G/H is a supervised live run, not a "smoke test".** Codex's §4 point, and it is a
naming problem with real consequences: calling the first real job application a test invites it
being run the way tests are run. Renamed throughout to **supervised live run**, requires Tebello
present, targets one posting he nominates, and is documented as production behavior that happens to
be observed — not as a gate that CI could ever execute.

**A22. A `rejected` question is recoverable.** Codex's §3 point. `review-questions` may be re-run at
any time and may move a question from `rejected` to `edited`/`approved` (`decided_at` updates,
append-only history is not kept for question decisions — the row is the current decision, and
`submissions`/`submission_preps` carry the audit trail). Rejection blocks submission; it does not
condemn the vacancy.

---

### B. Accepted as clarifications (implicit before, explicit now)

**B1. `prep-submission` requires the same status gate as `submit`.** Not stated before. It acts only
on `approved`/`submission_failed` — the same `ELIGIBLE_STATUSES` set `pipeline.py` already enforces,
imported rather than re-declared. Prep opens an authenticated browser against a real employer's
posting, so it sits behind the human gate for the same reason `submit` does, even though it submits
nothing.

**B2. Prep never transitions vacancy status.** Every prep outcome leaves the vacancy where it was.
Prep state lives in `submission_preps`; `vacancies.status` continues to mean what
`submission-core.md` B4 established — current state of the *application*, with the attempt log as
history. A third writer to that column would break that reading.

**B3. Adapters still never touch the database.** Unchanged from `submission-core.md` A2, and worth
restating because this spec adds two tables an adapter is obviously tempted to write.
`inspect_apply_flow()` **returns** a `PrepResult` dataclass; the `prep-submission` CLI persists it.
That keeps the property that makes Hard Rule 1 structural: no adapter can write a row that changes
what the gate sees.

**B4. Nothing here weakens the Stage 5 gate — it adds a second one.** `review-questions` is an
additional human checkpoint on top of the CV/cover-letter approval, never a substitute. A vacancy
still cannot reach `submit` without `status == approved`.

**B5. Employer question text is personal-data-adjacent and stays out of logs.** Consistent with
`CLAUDE.md`'s Security section: question text and answers are never logged at INFO, never written to
committed fixtures, and appear in `detail` only truncated (A6). Test fixtures use invented questions,
not the real recon ones.

**B6. Concurrency stays out of scope, explicitly** — inherited unchanged from `submission-core.md`
B6. Two simultaneous runs on one vacancy remain possible and unhandled; A14's guards reduce the
consequence but do not lock.

---

### C. Considered, not adopted

**C1. A `prep_failed` submission outcome with defined table semantics.** Codex asked for either
semantics or removal; removal is better (A3). Prep failures are not submission attempts, and the
seven-state `submission_preps.status` says more than one outcome value could.

**C2. LLM classification for deterministic autofill confidence.** Moot — A10 deletes the autofill
concept entirely rather than making its confidence rule testable. Reviewing one extra pre-drafted
answer is cheaper than any classifier, and it cannot be wrong in a way that reaches an employer.

**C3. Playwright trace/video capture on supervised failures.** Not adopted. Application pages carry
Tebello's contact details, CV content, and employer-authored text, and a trace file is a rich,
easily-forgotten artifact of all of it sitting on disk outside `.gitignore`'s current coverage.
Adopted instead: a **plain-text step log** (timestamp, step URL, action taken, no field values) that
`prep-submission` and `submit` write under `.session/logs/` — same gitignored directory as the
session credential, same treatment. Enough to reconstruct where a run went wrong; nothing in it that
would hurt if it leaked.

**C4. Deferring the whole thing until an Indeed API exists.** Not raised by Codex, considered here
and rejected on the record: there is no public Indeed apply API for individual applicants, so this
is not a "wait for the supported path" situation — the choice is browser automation or manual
submission, which is precisely the trade-off the ToS acknowledgement already covered.

---

### Build Queue changes from this amendment

Phases keep their letters; **A, B, C, E, G and H change in content**, and the amendment governs
where it conflicts with the table in §Build Queue.

| Phase | Amended description | Network | Changed by |
|---|---|---|---|
| A | `CandidateProfile.email`/`.phone` + `REQUIRED_FIELDS` + **`profile/migrations.py` versions 5 and 6** + `upsert_profile`/`get_profile`/`from_dict` + real `profile_seed.json` values. Back up `career.db` first | offline | A5 |
| B | **Two** tables — `submission_preps` and the expanded `screening_questions` — + `db.py` extensions (`save_prep`, `get_latest_prep`, `save_question`, `get_questions_for_prep`, `submission_prep_ready`) + **the `submissions.outcome` CHECK change and the DDL-drift guard** | offline | A2, A3, A4, A12 |
| C | `pending_review` outcome + the prep-state submit gate (A2's table) + `--all` auto-submit refusal | offline | A2, A3, A15 |
| D | `src/submission/browser.py` — session load, expiry detection (A18), CAPTCHA detection (A7), combined navigation-state check (A17), step logging (C3) | offline for the logic; exercised live in E/G | A7, A17, A18, C3 |
| E | `can_handle()` **static predicate only** + `inspect_apply_flow()` + `prep-submission` CLI + extraction with fingerprints/metadata/sensitivity + drafting (A20). Login-setup script first | network — Indeed **and** `claude -p` | A1, A6, A9, A11, A12, A20 |
| F | `review-questions` CLI (mirrors `src/review/cli.py`'s A/R/E/Q shape) — unchanged | offline | — |
| G | `IndeedAdapter.submit()` — `resolve_export_paths()` (A16), duplicate guard (A14), drift check (A6), CAPTCHA abort, upload, fill, success/ambiguity detection (A13) | network, **real submission** | A6, A13, A14, A16 |
| H | Supervised live run (A21) + `pyproject.toml` (`playwright` runtime dep, `[tool.coverage.run] omit`) + docs closeout | offline except the live run | A19, A21 |

Full TDD step numbering is still written at build-dispatch time, continuing `docs/todo.md`'s
sequence from step 102, per this project's convention.

### Open Items added by this amendment

4. ~~**Back up `career.db` before Phase A**~~ — **done 2026-08-07.**
   `career.pre-migration-5-6-20260807.db`, taken via sqlite3's backup API (not a file copy — a raw
   copy of a live WAL-mode database can capture a torn state) and verified:
   `PRAGMA integrity_check = ok`, `user_version = 4` on both, and per-table row counts matching
   source exactly (`vacancies` 10, `approvals` 10, `generation_log` 43, `candidate_profile` 1). The
   name ends in `.db` so the existing `*.db` gitignore rule covers it, and the daily runtime-data
   backup task picks it up by the same pattern. Rolling back means stopping, copying it over
   `career.db`, and resetting `PRAGMA user_version` to 4 if a migration has already run.
5. **Confirm the `--all` refusal (A15) is the wanted behavior**, not a surprise. It means submitting
   the 6 approved Indeed vacancies is six deliberate commands, by design.

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
