# Spec — TebelloReborn: decide on post-MVP scope

**Machine:** Pappa T only (`Pappa T/TebelloReborn/`).
**Todo item:** `docs/todo.md` "TebelloReborn: decide on post-MVP scope"
**Size:** decision, not a build — no code should be written until Tebello
picks.

## Goal

TebelloReborn's MVP (Phases 0-8, 182 tests) is complete. Three post-MVP
items are undecided backlog, no urgency behind any of them:

1. **Playwright auto-submit** — automating actual job-application
   submission. Currently out of scope by design (structural human-approval
   gate, no auto-submit exists).
2. **Recruiter/cold-outreach revival** — whether to add a recruiter-facing
   or cold-outreach mode, mirroring `ai-outreach-agency`'s pipeline.
3. **Doc-gen volume-cap/scheduler layer** — only relevant if actual usage
   volume ever needs throttling; not committed to.

TebelloReborn's own build deliberately did **not** copy
`ai-outreach-agency`'s fuller `handoff/` scheduler machinery, on the
grounds that copying it "because the sibling project has it" isn't a real
requirement — worth keeping that same discipline here.

## Steps

1. In a Pappa T session, present these three options to Tebello via
   `AskUserQuestion` (multi-select, since they're independent) — don't
   default to building any of them speculatively.
2. For whichever he picks (if any), write a proper spec before building —
   this decision spec is not itself an implementation spec for any of the
   three.
3. If none are picked, that's a valid outcome — record "no post-MVP work
   committed as of <date>" and close the item.

## Definition of done

- An explicit decision recorded (build one/more, or none) — not left
  ambiguous.

## Hub bookkeeping (after the decision)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/tebelloreborn.md` with the decision.
- Remove this item from `docs/todo.md` (replacing with a new build-task
  item + its own spec if something was picked), renumber remaining items,
  add a `docs/session-log.md` entry.
