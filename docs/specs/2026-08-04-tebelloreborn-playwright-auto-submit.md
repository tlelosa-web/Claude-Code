# Spec — TebelloReborn: Playwright auto-submit (post-MVP)

**Machine:** Pappa T only (`Pappa T/TebelloReborn/`).
**Todo item:** `docs/todo.md` "TebelloReborn: Playwright auto-submit"
**Decided:** 2026-08-04, cloud session, via `docs/specs/2026-07-29-tebelloreborn-scope-decision.md`'s decision process (see that spec — Tebello picked this one of the three post-MVP options, explicitly rejected recruiter/cold-outreach revival and doc-gen volume-cap/scheduler for now).
**Size:** build task — first real addition to the pipeline since MVP closed (Phases 0-5, 182 tests, 2026-07-26).

## Decision that scopes this spec

Tebello explicitly chose to **keep the human-approval gate** (Stage 5) as-is.
Playwright's job is narrower than "auto-submit": it automates the mechanical
form-filling/clicking on the job site **after** a human has already approved
that specific application's documents — it does not remove human judgment
from the loop. Full unattended auto-submit (no review step) was explicitly
declined as too risky given documents are AI-generated and vacancy postings
are untrusted scraped text (see `knowledge/tebelloreborn.md`'s prompt-injection
correction to ADR-003 — the same untrusted-input risk applies here: a
malicious job posting could try to manipulate a Playwright agent the same way
it could try to manipulate the headless-Claude-Code doc generator).

## Goal

Extend TebelloReborn's Stage 5 (Human Review) so that after Tebello approves
an application, Playwright drives the actual job-site submission form instead
of Tebello doing it by hand. Scope is the **approved-application submission
step only** — no change to Stages 1-4, no change to the approval UI/flow
itself beyond adding a "submit via Playwright" action after approval.

## Known constraints to design around

1. **Site variability.** Indeed and LinkedIn (the two live Apify sources)
   have different application flows — LinkedIn's "Easy Apply" is a bounded,
   scriptable multi-step modal; Indeed's flow varies per employer (some use
   Indeed's own apply form, many redirect to an external ATS with no fixed
   shape). A single generic Playwright script won't cover both reliably.
   Recommend starting with **LinkedIn Easy Apply only** as the first
   supported path, and treating any posting outside that shape as
   "not auto-submittable — fall back to manual" rather than trying to build
   a universal form-filler up front.
2. **Untrusted input reaches the browser.** Scraped vacancy data (title,
   company, any auto-fill hints) flows into whatever Playwright uses to
   match/fill form fields. Apply the same discipline as the doc-gen
   correction: never let scraped text become an executable instruction to
   the automation (e.g. don't feed raw posting text into an LLM-driven
   "figure out the form" step without the same untrusted-text wrapping
   already used in `pdf_export.py`/generators, if an LLM is involved in
   field-matching at all — prefer deterministic selectors over LLM-driven
   form interpretation where the form shape is known and stable).
3. **Credentials.** Whatever LinkedIn/Indeed session Playwright drives needs
   Tebello's own logged-in session (cookies/storage state), not stored
   plaintext credentials checked into the repo — use Playwright's
   `storageState` export/import against a path already covered by the
   project's existing `.gitignore` (mirrors how `.env`/`credentials.json`
   are already excluded per this hub's `docs/todo.md` O-P-C consolidation
   note).
4. **Failure visibility.** A submission that silently fails (form validation
   error, changed page layout, CAPTCHA) must surface as a clear failure back
   to the human review flow, not report false success — same "fails loud"
   principle already used for the Ollama matching stage.

## Proposed steps (to confirm with Tebello in the Pappa T session before building)

1. Read TebelloReborn's actual `docs/architecture.md`, current Stage 5 CLI
   code, and DB schema (`CandidateProfile`/application/vacancy tables) to
   confirm exact integration point — this spec is written without direct
   access to that code (Pappa T-only), so treat the file/module names above
   as informed guesses, not confirmed paths.
2. Add a `storageState`-based Playwright login/session setup (one-time
   manual login, saved session reused across runs).
3. Build the LinkedIn Easy Apply submission flow: locate the application
   modal from a job URL, fill fields from `CandidateProfile` +
   generated-document paths (upload CV/cover letter as files, not pasted
   text), submit, confirm success screen, record submission status back to
   the DB.
4. Explicitly detect and reject (fall back to manual) any non-Easy-Apply
   flow rather than guessing at a generic form-fill.
5. Add tests: at minimum a mocked/fixture-based test of the field-fill logic
   (matches the existing test discipline — 182 tests all mock external
   calls) plus one documented manual smoke-test run against a real (or
   sandboxed/test) LinkedIn posting before calling this done, given
   Playwright-against-a-real-site behavior won't be caught by mocks (same
   lesson as the Apify payload-shape bug in `knowledge/tebelloreborn.md`).
6. Update TebelloReborn's own `README.md`/`docs/architecture.md` to reflect
   the new Stage 5 sub-step, and its own `docs/todo.md`/session log per its
   own conventions.

## Explicitly out of scope

- Indeed direct-apply or third-party ATS redirects — flagged as a possible
  future extension only, not part of this build.
- Removing or weakening the human-approval gate.
- Any recruiter/cold-outreach or volume-cap/scheduler work — those were
  separately declined in the same decision round.

## Definition of done

- LinkedIn Easy Apply postings can be submitted via Playwright after human
  approval, with the submission outcome recorded and visible.
- Non-Easy-Apply postings are cleanly detected and routed to manual
  submission, not silently mishandled.
- At least one real (or realistic sandboxed) end-to-end smoke test run
  logged, not just mocked unit tests.

## Hub bookkeeping (after this is built, or if scope changes once the real
code is reviewed)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/tebelloreborn.md` with the outcome/any design changes
  found once the real code is read.
- Mark this item done in `docs/todo.md`, add a `docs/session-log.md` entry.
