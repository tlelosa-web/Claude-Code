## 2026-07-28 — What it is, structure, submodule status
**Source:** Pappa T session (cross-project status survey), Tenders' own README.md/AGENT.md, Pappa T docs/todo.md
**Status:** active

South African tender-monitoring automation. Lives at `Pappa T/Tenders/` — folder
inside the Pappa T vault repo, not its own git repo (its `AGENT.md` is the same
generic "MASTER AGENT DIRECTIVE / Directive → Orchestration → Execution /
Self-Annealing" template also found verbatim in `IQ/1_Documentation/AGENT.md` — a
reused scaffold, not project-specific).

Standard `1_Documentation/2_Source_Data/3_Live_Reports/4_Scripts/
5_Archive_and_Debug` layout (same convention as `IQ/`). Primary working script
found: `4_Scripts/find_gauteng_food_tenders.py`, output logged to
`3_Live_Reports/gauteng_food_tenders.txt` — a Gauteng-region, food-sector tender
finder.

**`4_Scripts/tenders-sa/` is a registered git submodule** pointing at
`alfa-rsa/tenders-sa` (resolved 2026-07-18, commit `d6da4c3`, per Pappa T's own
`docs/todo.md` — this closed out the last item in that cleanup pass). Don't
re-investigate this as "untracked nested repo" in a future survey — it's
deliberate and already resolved.

There is also a numbered subfolder (`110320262657/`) containing a tender-bid
working package — role-assignment docs (solution architect, project manager,
commercial/contracts/quality/HSE leads, etc.), a `submission/` tree
(admin/commercial/contracts/planning/portal/quality/service/technical), and
scratch generation scripts. Last touched mid-April 2026; appears to be a
completed or dormant bid package, not a currently-active task — noted here only
structurally (no bid content, company names, or figures) per the no-company-data
rule. If a future session finds this folder still dormant, it's likely fully
closed rather than newly stale.

**Not carried over:** no tender numbers, bid content, company names, or figures
— this entry is structural only.
