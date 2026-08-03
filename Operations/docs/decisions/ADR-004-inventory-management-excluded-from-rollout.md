# ADR-004 — `Inventory Management & Reports` excluded from DCOE rollout

**Date:** 2026-07-15
**Status:** Accepted
**Owner:** Tebello Lelosa

## Context

ADR-002 named `Inventory Management & Reports` as one of five projects to
onboard to DCOE, and ADR-003 (pipeline-project lightweight-onboarding
convention) listed it as the third of three pipeline projects that would
reuse the `1. Daily Sales Order Files` precedent mechanically.

Tebello has since decided the project's actual future role: it will be used
as a **reference resource** for SOPS development (and any other project
that needs the extract → build → report work already done here), not
maintained as its own standalone, actively-run pipeline.

## Decision

1. **`Inventory Management & Reports` is removed from the DCOE rollout
   list.** It will not get its own project `CLAUDE.md` or lightweight DCOE
   onboarding under ADR-003 — that convention is for projects run as their
   own ongoing pipeline, which this no longer is.
2. **The project's existing content is left as-is** (five-folder layout,
   `1_Documentation/GEMINI.md`, `USER_GUIDE.md`, scripts) — nothing deleted
   or restructured. It remains available to be read from and copied/adapted
   into SOPS or other projects when useful, as reference material.
3. **DCOE rollout is now four projects**, not five: `7. DELIVERY NOTE`,
   `1. Daily Sales Order Files` (done), `8. AvgMovement` (done), and
   `3. Nameplate & Test Sheet` (done). `Inventory Management & Reports`
   drops off the list entirely rather than staying open indefinitely.

## Consequences

- `docs/todo.md` § In progress: the `Inventory Management & Reports`
  sub-task is removed from the pipeline-reconciliation checklist (not
  marked done — it was never going to be onboarded, so "done" would be
  misleading).
- Root `CLAUDE.md` project index: DCOE-status column updated to reflect
  reference-resource status instead of "not onboarded" (which implied
  onboarding was still pending).
- `docs/patterns.md` § 6 (pipeline folder layout) still lists this project
  as one of the pattern's original sources — that's a historical fact about
  where the convention was observed, unaffected by this decision.
- If a future task pulls specific logic from this project into SOPS (or
  elsewhere), that's a normal cross-project reference, not a DCOE
  onboarding — no ADR needed for reading from it.
