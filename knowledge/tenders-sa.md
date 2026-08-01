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

There is also a numbered subfolder — now renamed with an `ARCHIVED_` prefix
plus an `ARCHIVED_STATUS.md` marker (2026-08-01) — containing a tender-bid
working package: role-assignment docs (solution architect, project manager,
commercial/contracts/quality/HSE leads, etc.), a `submission/` tree
(admin/commercial/contracts/planning/portal/quality/service/technical), and
scratch generation scripts. **Correction to the 2026-07-28 entry below:** that
survey called this folder "dormant... no bid content" — wrong on inspection.
It's a fully worked, git-tracked bid package (real client ITT/annexures,
drafted returnables, costing, a final packaged submission archive), not an
empty scaffold. Project owner confirmed 2026-08-01 the bid was abandoned; it's
now formally archived (folder rename + status marker), not merely dormant.
Treat a future session finding it archived as closed, not newly stale — no
need to re-investigate. (No bid content, company names, tender numbers, or
figures carried into this note, per the no-company-data rule — see the actual
project folder for specifics.)

**Not carried over:** no tender numbers, bid content, company names, or figures
— this entry is structural only.
