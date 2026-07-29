# ADR-009 — Codex cross-family second-opinion gate (advisory, spec-stage)

**Date:** 2026-07-21
**Status:** Accepted — implemented in `tlelosa-claude-config` (PR #7)
**Owner:** Tebello Lelosa

## Context

The DCOE pipeline's planner and reviewer are both Claude-family models, so
their failure modes are correlated: a wrong assumption shared by the family
can pass the Opus review gate untouched. A second opinion from a different
model family (OpenAI Codex) addresses that correlated-blind-spot risk — but
only if it is placed where changing course is cheap (the plan, not the
diff), and only within existing constraints:

- **Offline-first hard rule (#11):** no feature may depend on internet
  connectivity, so a fail-stop external gate is a hard-rule violation by
  construction — fail-warn is mandatory, not a preference.
- **Egress control:** the vault holds personal records and
  company-adjacent material; any call to an external model is a context
  egress and must be default-deny, allow-listed by construction.
- **IT clearance gap:** clearance on the Operations (work) machine covers
  the personal Anthropic account, not OpenAI egress. Until that clears,
  the gate cannot be universal (no `CORE.md` rule, no roster entry).

Full analysis: readiness audit and phase-1 spec in `tlelosa-claude-config`
(`docs/specs/2026-07-21-codex-gate-readiness-audit.md`,
`docs/specs/2026-07-21-codex-gate-spec.md`).

## Decision

Ship a single self-owned slash command, `/codex-review <spec-file>`, as a
standalone marketplace plugin (`codex-gate`), inserted at Pattern 1 step 2:
Planner writes spec → `/codex-review` (advisory) → human approves or
iterates.

1. **Payload: specs only, by construction.** The command accepts exactly
   one existing `.md` file under `docs/specs/` of the project it runs in.
   No CLAUDE.md, no `@imports`, no diffs, no other files — nothing else is
   ever read into the payload. YAML frontmatter is stripped before sending.
2. **Mechanism: self-owned.** The command shells out to the Codex CLI
   (`codex exec`, non-interactive) with a fixed review prompt (buried
   assumptions, missing acceptance criteria, unconsidered failure modes,
   cross-family architectural alternatives). No third-party plugin
   (`codex-plugin-cc` not adopted — provenance unvetted, payload control
   stays in-house).
3. **Advisory only, logged-note disagreement handling.** Output is appended
   to the spec under `## Codex second opinion (advisory)`, date-stamped.
   Codex has no veto; the reviewer agent retains sole APPROVE/BLOCK
   authority, and the human decides at spec approval as usual.
4. **Fail-warn, always.** Any failure — CLI missing, no credentials,
   network down, rate limit, non-zero exit, or the 90 s hard timeout (no
   retry) — prints a visible warning and exits successfully. The gate can
   never block spec approval, commit, or push. Outcome is logged one-line
   to `docs/session-log.md` where present, so degradation is visible.
5. **Scope of rollout: Pappa T only** until IT confirms OpenAI egress from
   the Operations machine. Credentials live in the Codex CLI's own
   user-scope auth store (`~/.codex/`) — never in any repo, `.env`, or
   plugin content.
6. **No `ExitPlanMode` hook.** The spec-stage command is the only
   mechanism; plan-mode sessions outside the DCOE spec flow get no Codex
   opinion.

## Alternatives considered

- **`pre-push` hook** — rejected: fires after code is written (expensive
  place to catch plan-level disagreement), adds a network dependency to a
  blocking gate (offline-first violation), and double-reviews the diff.
- **Stacking Codex onto the reviewer stage** — rejected: the diff already
  has a permanent Opus blocking gate; cross-family value concentrates at
  the plan, where course changes are cheap.
- **New roster agent** — rejected: Codex is not addressable via `model:`
  frontmatter, and the roster auto-deploys user-level to both machines,
  which would force an OpenAI egress path onto the employer machine.
- **Third-party `codex-plugin-cc`** — rejected pending vetting; a thin
  self-owned command keeps payload construction auditable.
- **`ExitPlanMode` hook as primary gate** — rejected: DCOE Pattern 1 does
  not run through plan mode, so the hook would silently not fire for most
  feature work.

## Consequences

- Genuinely fresh cross-family eyes on every spec (Codex's lack of project
  context is a feature at plan stage), at exactly one call per feature —
  never per-commit or per-push. Slim-profile edits and Pattern 2 bug fixes
  are exempt.
- The gate can never block anything, so its failure cost is bounded at
  "one warning line"; the trade-off is that outages degrade silently to
  solo planning, mitigated by the session-log line.
- Coverage is single-machine until the IT egress question is answered
  (tracked in the config repo's `docs/todo.md`); `CORE.md` stays unchanged
  — at most a one-line routing note once both machines are cleared.
- Spec files accumulate appended advisory sections as part of their
  approval record.
- Config surface shipped with the decision: `codex-gate` marketplace
  entry, `CLAUDE.md.template` v3.3 (warn-only hooks sentence, HOOKS table
  row, default-deny egress bullet), README install + IT-scope notes.

## References

- Spec: `tlelosa-claude-config/docs/specs/2026-07-21-codex-gate-spec.md`
- Readiness audit:
  `tlelosa-claude-config/docs/specs/2026-07-21-codex-gate-readiness-audit.md`
- Implementation: `tlelosa-claude-config` PR #7 (merged 2026-07-21)
- Related: ADR-007 (`@path` import limitation — why CORE.md is read, not
  imported)
