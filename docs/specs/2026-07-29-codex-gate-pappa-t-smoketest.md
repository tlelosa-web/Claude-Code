# Spec — codex-gate: Pappa T install + network-off smoke-test

**Machine:** Pappa T only.
**Todo item:** part of `docs/todo.md` "Close out the codex-gate rollout"
(the Pappa T sub-item).
**Size:** small, verification-focused.

## Goal

`codex-gate` (the `/codex-review` advisory plugin in `tlelosa-claude-config`
— sends one spec file to the OpenAI Codex CLI for a second opinion,
warn-only, never blocks) needs to be installed and smoke-tested on Pappa T,
including its fail-warn behavior when network is off.

## Steps

1. Confirm `codex-gate` is installed via the `tlelosa-claude-config`
   marketplace on this machine (`/plugin marketplace update
   tlelosa-claude-config` if not current — check Step 1.5 of `/continue`
   for whether there are upstream commits to pull first).
2. Run `/codex-review` against a real spec file with network available —
   confirm it reaches the OpenAI Codex CLI and returns a second opinion.
3. Disable network (or otherwise force an unreachable state) and run
   `/codex-review` again — confirm it fails **loud but warn-only**: a clear
   message that it couldn't reach Codex, and does **not** block whatever
   task triggered it.
4. Record both outcomes (pass/fail, exact behavior observed).

## Definition of done

- Both the network-available and network-off paths have been run once and
  their actual behavior recorded — not assumed from the plugin's design
  intent.

## Hub bookkeeping (after the smoke-test)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/tlelosa-claude-config.md`'s open-items entry to mark
  this sub-item done (or note what broke, if the smoke-test failed).
- Don't remove the parent "Close out the codex-gate rollout" item from
  `docs/todo.md` yet — the Operations ADR-copy and Fan Movement IT
  sub-items are independent and may still be open (see
  `2026-07-29-codex-gate-operations-adr-copy.md`).
