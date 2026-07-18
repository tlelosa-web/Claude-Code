# Task Queue — TebelloReborn (Career Engine)

> Updated: 2026-07-05

---

## Completed

- [x] Archived the old Qwen-era prototype intact into `_archive_qwen_prototype/` (nothing deleted).
- [x] Scaffolded new directory structure: `data/`, `docs/decisions/`, `src/{shared,profile,vacancy_search,matching,doc_gen,review}/`, `tests/{unit,integration}/`, `exports/`.
- [x] Copied forward real reference content: Master CV → `data/`, tracker + recruiter DB → `data/legacy_reference/`.
- [x] Wrote `CLAUDE.md` (project brain, DCOE v3.1 style, mirrors `ai-outreach-agency`).
- [x] Wrote `docs/architecture.md` (pipeline design, data flow, MVP scope: Phases 1–5 of 7).
- [x] Wrote 9 DCOE agent definitions in `.claude/agents/` (domain, planner, architect, executor, tester, reviewer, doc-writer, debugger, data-agent).

---

## Known Issues

- [ ] `OPENROUTER_API_KEY` out of credits (shared blocker with `ai-outreach-agency`) — will block Stage 3 (AI Matching) and Stage 4 (Document Generation) once code exists. Not this project's to fix alone; top up before real runs.
- [ ] No dedicated Apify actor exists for PNet or Careers24 — MVP vacancy fetch covers Indeed + LinkedIn only.

---

## Build Queue (awaiting explicit go-ahead to implement — no source code written yet)

- [ ] Confirm console-script/package name (`career-engine` used as placeholder throughout docs).
- [ ] Confirm target-title weighting for `profile_seed.json` (Operations Foreman/Manager lane vs. Project Engineer lane — the two existing CVs frame this differently).
- [ ] Scaffold `pyproject.toml`, `.env.example`, `.gitignore`, `src/config.py`.
- [ ] Copy `shared/rate_limiter.py` verbatim from `ai-outreach-agency`; adapt `shared/openrouter_client.py`.
- [ ] Build `src/profile/` (schema + db) and author `data/profile_seed.json`.
- [ ] Build `src/vacancy_search/` (schema + db + `apify_client.py` wired to Indeed/LinkedIn actors, `OFFLINE_MODE` fixture).
- [ ] Build `src/matching/` (prompt_builder + scorer).
- [ ] Build `src/doc_gen/` (cv_generator, cover_letter_generator, pdf_export).
- [ ] Build `src/review/` (approval CLI — persist decisions, learn from `ai-outreach-agency`'s earlier unsaved-approval bug).
- [ ] Wire `src/main.py` CLI (`import-profile`, `fetch-vacancies`, `run`, `run-all`, `list`).
- [ ] Write `ADR-001-vacancy-store.md` and `ADR-002-apify-job-scraping.md` under `docs/decisions/`.
- [ ] Unit + integration tests, fully offline, mirroring `ai-outreach-agency`'s conventions.

---

## Future (not yet scheduled)

- [ ] Phase 6: Playwright-based auto-fill/submit, paused before final submission.
- [ ] Phase 7: tracking dashboard (applications, match-score distribution, response rate).
- [ ] PNet/Careers24 coverage via generic Apify crawler + LLM extraction.
- [ ] Decide whether recruiter cold-outreach (in `data/legacy_reference/`, not part of the original 7-phase plan) gets revived as a later phase.
