# Task Queue — TebelloReborn (Career Engine)

> Updated: 2026-07-18

---

## Completed

- [x] Archived the old Qwen-era prototype intact into `_archive_qwen_prototype/` (nothing deleted).
- [x] Scaffolded new directory structure: `data/`, `docs/decisions/`, `src/{shared,profile,vacancy_search,matching,doc_gen,review}/`, `tests/{unit,integration}/`, `exports/`.
- [x] Copied forward real reference content: Master CV → `data/`, tracker + recruiter DB → `data/legacy_reference/`.
- [x] Wrote `CLAUDE.md` (project brain, DCOE v3.1 style, mirrors `ai-outreach-agency`).
- [x] Wrote `docs/architecture.md` (pipeline design, data flow, MVP scope: Phases 1–5 of 7).
- [x] Wrote 9 DCOE agent definitions in `.claude/agents/` (domain, planner, architect, executor, tester, reviewer, doc-writer, debugger, data-agent).
- [x] Confirmed console-script/package name: **`career-engine`** (no longer a placeholder).
- [x] Confirmed target-title weighting for `profile_seed.json`: **Operations Foreman/Manager is the primary lane**, Project Engineer (Mechanical) is a secondary lane carried in the same file.
- [x] Full MVP build plan written: `docs/specs/mvp-pipeline-build.md` (46 atomic tasks, Phases 0–8, Stages 1–5 only).

---

## Known Issues

- [ ] `OPENROUTER_API_KEY` out of credits (shared blocker with `ai-outreach-agency`) — will block real Stage 3 (AI Matching) and Stage 4 (Document Generation) runs once code exists (tests themselves run fully offline via `OFFLINE_MODE`). Not this project's to fix alone; top up before real runs.
- [ ] No dedicated Apify actor exists for PNet or Careers24 — MVP vacancy fetch covers Indeed + LinkedIn only (see planned ADR-002).

---

## Build Queue — ordered, atomic (see `docs/specs/mvp-pipeline-build.md` for full detail: inputs, outputs, verification, network flags, per-step agent)

### Phase 0 — Scaffolding & Config
- [x] 1. `pyproject.toml` (deps + `career-engine` console script)
- [x] 2. `.env.example` + `.gitignore` (do NOT blanket-ignore `data/`)
- [x] 3. `tests/conftest.py` + `tests/unit/conftest.py` (autouse `OFFLINE_MODE`)
- [x] 4. [RED] `tests/unit/test_config.py`
- [x] 5. [GREEN] `src/config.py`

### Phase 1 — Shared External-Client Infra
- [ ] 6. [RED] `tests/unit/test_rate_limiter.py`
- [ ] 7. [GREEN] `src/shared/rate_limiter.py` (copied verbatim from `ai-outreach-agency`)
- [ ] 8. [RED] `tests/unit/test_openrouter_client.py`
- [ ] 9. [GREEN] `src/shared/openrouter_client.py` (adapted from `ai-outreach-agency`)

### Phase 2 — Stage 1: Profile Import (offline)
- [ ] 10. [RED] `tests/unit/test_profile_schema.py`
- [ ] 11. [GREEN] `src/profile/schema.py`
- [ ] 12. [RED] `tests/unit/test_profile_db.py`
- [ ] 13. [GREEN] `src/profile/db.py` + `src/profile/migrations.py`
- [ ] 14. [RED] `tests/unit/test_profile_seed_data.py`
- [ ] 15. [GREEN] `data/profile_seed.json` (Ops Foreman/Manager primary, Project Engineer secondary)

### Phase 3 — Stage 2: Vacancy Fetch (Apify for real runs)
- [ ] 16. [RED] `tests/unit/test_vacancy_schema.py`
- [ ] 17. [GREEN] `src/vacancy_search/schema.py`
- [ ] 18. [RED] `tests/unit/test_vacancy_db.py`
- [ ] 19. [GREEN] `src/vacancy_search/db.py` + `src/vacancy_search/migrations.py`
- [ ] 20. [RED] `tests/unit/test_apify_client.py`
- [ ] 21. [GREEN] `src/vacancy_search/apify_client.py`

### Phase 3.5 — ADRs
- [ ] 22. `docs/decisions/ADR-001-vacancy-store.md`
- [ ] 23. `docs/decisions/ADR-002-apify-job-scraping.md`

### Phase 4 — Stage 3: AI Matching (OpenRouter for real runs)
- [ ] 24. [RED] `tests/unit/test_matching.py`
- [ ] 25. [GREEN] `src/matching/prompt_builder.py`
- [ ] 26. [GREEN] `src/matching/scorer.py`
- [ ] 27. [RED] `tests/unit/test_matching_pipeline.py`
- [ ] 28. [GREEN] `src/matching/pipeline.py`

### Phase 5 — Stage 4: Document Generation (OpenRouter for text; PDF export offline)
- [ ] 29. [RED] `tests/unit/test_doc_gen.py`
- [ ] 30. [GREEN] `src/doc_gen/cv_generator.py`
- [ ] 31. [GREEN] `src/doc_gen/cover_letter_generator.py`
- [ ] 32. [RED] `tests/unit/test_pdf_export.py`
- [ ] 33. [GREEN] `src/doc_gen/pdf_export.py`
- [ ] 34. [RED] `tests/unit/test_doc_gen_pipeline.py`
- [ ] 35. [GREEN] `src/doc_gen/pipeline.py`

### Phase 6 — Stage 5: Human Review (offline) — **steps 40–41 require Reviewer sign-off BEFORE execution, not just before merge**
- [ ] 36. [RED] `tests/unit/test_review_schema.py`
- [ ] 37. [GREEN] `src/review/schema.py`
- [ ] 38. [RED] `tests/unit/test_review_db.py`
- [ ] 39. [GREEN] `src/review/db.py` + `src/review/migrations.py`
- [ ] 40. [RED] `tests/unit/test_review_cli.py` — **REVIEWER SIGN-OFF REQUIRED FIRST**
- [ ] 41. [GREEN] `src/review/cli.py` — **REVIEWER SIGN-OFF REQUIRED FIRST**

### Phase 7 — CLI Wiring & Integration
- [ ] 42. [RED] `tests/unit/test_main.py`
- [ ] 43. [GREEN] `src/main.py`
- [ ] 44. `tests/integration/test_full_pipeline.py` (offline end-to-end)

### Phase 8 — Docs Closeout
- [ ] 45. `docs/api-patterns.md`
- [ ] 46. `docs/session-log.md`

---

## Resolved Items

- [x] Migration-file convention for net-new tables (Phases 2/3/6): confirmed against
      `ai-outreach-agency/src/lead_import/db.py` — initial `CREATE TABLE IF NOT EXISTS` statements live
      directly in each module's `init_db()`, not in `migrations.py`. `migrations.py` (empty `MIGRATIONS`
      list + `PRAGMA user_version` runner) only tracks schema changes *after* that baseline, mirroring
      exactly how `ai-outreach-agency` added its `campaign` column. Steps 13/19/39 follow this pattern.

---

## Future (not yet scheduled)

- [ ] Phase 6 (post-MVP numbering — original 7-phase plan): Playwright-based auto-fill/submit, paused before final submission.
- [ ] Phase 7 (post-MVP numbering): tracking dashboard (applications, match-score distribution, response rate).
- [ ] PNet/Careers24 coverage via generic Apify crawler + LLM extraction.
- [ ] Decide whether recruiter cold-outreach (in `data/legacy_reference/`, not part of the original 7-phase plan) gets revived as a later phase.
