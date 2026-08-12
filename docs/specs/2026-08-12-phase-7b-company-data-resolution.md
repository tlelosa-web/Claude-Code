# Phase 7b: Resolve Company-Data Rule Contradiction

**Date:** 2026-08-12  
**Status:** Awaiting Owner Decision  
**Scope:** CLAUDE.md hard rule clarification + GitHub visibility decision

## The Contradiction

The hub's hard rule 4 states:  
> No company or project data beyond what's already public in the source project's own repo

But the current state is:
- `Operations/` folder (69 MB) contains 641 tracked files
- Includes 64 `.xlsx`, 14 `.csv`, 13 `.pdf` files
- Material includes: `CustomerInvoicesReport.csv`, `CustomerSalesOrdersByCustomer.csv`, `Contract register 2025.xlsx`, monthly sales order reports
- All 5 GitHub repositories (tlelosa-web/) are **private**

The hub-and-spoke design intends sub-projects to live here; the hard rule 4 and the layout contradict each other.

## Context Shift (2026-08-09)

Fan Movement contract was **terminated 2026-08-03**. This changes the question from "how should we organize shared data" to "should retained company data reach cloud sessions?"

## Two Live Concerns

1. **Cloud sessions clone this entire vault** into Anthropic containers, including all Operations company data
2. **The IT clearance on record** was granted by Fan Movement (company Tebello no longer contracts to), so its conditions may no longer apply

## Current State

- A copy was staged to `Desktop/Fan Movement - Company IP/` on 2026-08-09 (917 files, 85.8 MB, checksummed)
- Original data remains: this repo, private GitHub repos, OneDrive backups, local backups
- **Retention is still a contract question**, not yet decided — nothing should be deleted before the answer

## Options

### Option A: Keep in repo (maintain status quo)
- ✅ No action needed
- ⚠️ Cloud sessions will continue cloning company data
- ⚠️ Rule 4 remains contradicted by the layout

### Option B: Move to separate private repo
- New repo: `tlelosa-web/operations-company-data` (or similar)
- Update CLAUDE.md hard rule 4 to reflect the split
- This hub stays clean; company data has its own home
- ⚠️ Requires a migration plan and removal from this repo (with history decision)

### Option C: Keep in repo + clarify rule 4
- Reword hard rule 4 to acknowledge company data is present
- Add explicit note: "Company data stored under `Operations/` due to active projects; retention governed by contract terms; cloud sessions inherit full access"
- Cloud sessions document this in their onboarding

### Option D: Remove to archive only
- Delete `Operations/` from main branch (history rewrite needed)
- Keep in Fan Movement staged copy + backups pending contract resolution
- Rule 4 becomes literal and enforced
- ⚠️ History rewrite breaks all clones; massive disruption for spec reason

## Recommendation

**Option C (clarify rule 4)** is lowest-cost and most honest:
1. Reword hard rule 4 to state company data's presence and governance
2. Document cloud-session implications in `knowledge/cloud-sessions.md`
3. Retain data pending contract resolution (irreversible to delete after the fact)
4. Unblock Phase 7 while contract terms are decided separately

**Avoid Option D** (delete + rewrite) — the spec explicitly says "do not rewrite history" and all clones would break on both Operations and Pappa T machines.

## Next Step

**Owner decision required:**
1. Pick Option A, B, or C (or alternative)
2. If C: approve the CLAUDE.md rewording below
3. If B: approve migration scope + timeline

---

## Proposed CLAUDE.md Rewording (Option C)

Replace current hard rule 4:
```
4. No company or project data beyond what's already public in the source
   project's own repo — same discipline as `tlelosa-claude-config`.
```

With:
```
4. **Company data governance:** `Operations/` holds company business data
   from terminated projects (Fan Movement contract ended 2026-08-03). All
   GitHub repos are private. Retention is governed by contract terms, still
   being resolved. Cloud sessions inherit full vault access, including this
   data — document any implications in session onboarding. No deletion or
   rewrite of history without explicit owner approval.
```

This honest rewording:
- Acknowledges what's actually in the repo
- Marks it as transient pending contract resolution
- Warns cloud sessions about the scope
- Removes the contradiction with hub-and-spoke layout
