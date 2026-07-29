# Spec — codex-gate: copy drafted ADR into Operations hub's docs/decisions/

**Machine:** Operations only.
**Todo item:** part of `docs/todo.md` "Close out the codex-gate rollout"
(the Operations sub-item).
**Size:** small, mechanical.

## Goal

The codex-gate ADR has already been drafted at
`tlelosa-claude-config/docs/specs/2026-07-21-codex-gate-adr-draft.md` but
has not yet been copied into the Operations hub's own
`docs/decisions/` folder.

## Steps

1. Confirm the Operations hub's root repo has a `docs/decisions/` folder
   (create it if it doesn't exist yet — check the Operations hub's own
   `CLAUDE.md` for its ADR-numbering convention first, don't assume one).
2. Copy `tlelosa-claude-config/docs/specs/2026-07-21-codex-gate-adr-draft.md`
   into `docs/decisions/` on the Operations hub, renaming to match
   whatever ADR-numbering convention that hub already uses (check existing
   files there for the pattern before inventing one).
3. Update any cross-reference in the copied file if the draft referenced
   its old location.

## Definition of done

- The ADR exists in the Operations hub's `docs/decisions/`, following that
  hub's existing naming convention, content otherwise unchanged from the
  draft.

## Note — this is still gated

codex-gate itself stays **Pappa T-only** regardless of this copy landing —
Fan Movement IT still needs to confirm OpenAI-egress coverage for
Operations before the plugin is actually installed there (see
`knowledge/tlelosa-claude-config.md`). This spec only closes the
documentation sub-item, not the install.

## Hub bookkeeping (after the copy)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/tlelosa-claude-config.md`'s open-items entry to mark
  this sub-item done.
- Don't remove the parent "Close out the codex-gate rollout" item from
  `docs/todo.md` yet — the IT-confirmation sub-item is still open and
  isn't machine-bound (it's a pending external answer, not a task any
  session can execute).
