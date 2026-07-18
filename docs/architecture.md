# Architecture

This vault is the TebelloReborn personal operating system with multiple project domains:

- `TebelloReborn/`: professional profile, CV generation, recruiter outreach, and job-search automation.
- `MIMS App/`: inventory or operations web application.
- `IQ/`: trading or signal-generation workspace.
- `Tenders/`: South African tender monitoring automation.
- `00_Index_&_Logs/` through `05_Archive/`: vault-level strategy, finance, operations, brand, and archive areas.

The operating model is DCOE:

1. Domain: classify the work.
2. Context: load only relevant files.
3. Orchestrate: split work into atomic tasks.
4. Execute: implement one task at a time and verify.

`AGENTS.md` is the source of truth for workflow and agent behavior. The core operating model is life-domain orchestration: Codex coordinates specialist executors that handle identity, career, operations, ventures, finance, governance, learning, wellbeing, and tender opportunities.
