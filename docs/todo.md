# Outreach Engine — Task Queue

## In Progress
- [ ] Task 5: Scaffold email_draft module

## Scaffold Phase (complete these in order)
- [ ] Task 6: Config layer + main CLI runner

## API Wiring Phase (after all scaffolds done)
- [ ] Task 7: Wire OpenRouter → research + asset_gen
- [ ] Task 8: Wire Apify → research scraper  
- [ ] Task 9: Wire Gmail API → email_draft

## Polish Phase
- [ ] Task 10: Lead status lifecycle tracking
- [ ] Task 11: End-to-end integration test (OFFLINE_MODE)

## Backlog (post-MVP)
- [ ] Export approved leads to CSV for reporting
- [ ] Batch run with daily limit cap (max N leads per session)
- [ ] Asset template variants (PAIN_POINT_SUMMARY, QUICK_WIN types)
- [ ] Simple HTML report of pipeline run results
- [ ] Retry queue for failed research or asset_gen calls

## Completed
- [x] ADR-001: Lead store — SQLite source of truth
- [x] Task 1: DCOE scaffold
- [x] Task 2: CLAUDE.md
- [x] Task 3: architecture.md + todo.md
- [x] Task 4: lead_import module (16 tests)
- [x] Research module stubs (4 tests)
- [x] asset_gen module stubs (8 tests)
- [x] approval module (in review)
