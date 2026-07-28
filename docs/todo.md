# todo.md — Claude-Code hub (cross-project task queue)

Hub-level tasks only — work that spans projects, or new work started at
root. Each project's own `docs/todo.md` (in its own repo) is authoritative
for anything scoped inside that project; this file doesn't duplicate that
detail, only tracks it at a glance and links out.

Per DCOE: update after every completed task; one task = one commit.

## In progress

- [ ] None currently.

## Next up (priority order, set 2026-07-28)

1. [ ] **Fix the Excel-import bug in NamePlateTool** — `/api/nameplate/from-excel`
      crashes on a non-serializable `datetime`, and separately checks for a
      sheet name (`"Table 1"`) that doesn't exist in the real workbook. Open
      since 2026-07-17, one reverted fix attempt (regressed to all-blank
      fields). The only active, user-facing defect across all tracked
      projects. Detail: `NamePlateTool/docs/todo.md`, `knowledge/nameplatetool.md`.
2. [ ] **Close out the codex-gate rollout** (`tlelosa-claude-config`) — three
      items outstanding: install + network-off smoke-test on Pappa T, copy
      the drafted ADR into the Operations hub's `docs/decisions/`, and get
      Fan Movement IT to confirm OpenAI-egress coverage for Operations
      (codex-gate stays Pappa T-only until then). Detail:
      `tlelosa-claude-config/docs/todo.md`, `knowledge/tlelosa-claude-config.md`.
3. [ ] **NamePlateTool: add a real automated test suite** — not urgent;
      `tests/` is ad-hoc manual-check scripts only. Bundle with the
      Excel-import fix once that's underway.
4. [ ] **TebelloReborn: decide on post-MVP scope** — Playwright auto-submit,
      recruiter/cold-outreach revival, and a doc-gen volume-cap/scheduler
      are all undecided backlog items, no urgency behind them yet. Detail:
      `knowledge/tebelloreborn.md` (supersedes the pointer to `pappa-t.md`
      this item previously had — see that project's own dedicated file now).
5. [ ] **ai-outreach-agency: top up OpenRouter credits** — `asset_gen` has
      been blocked on HTTP 402 since 2026-07-04; unblocks real (non-offline)
      batch runs until its headless-Claude-Code migration (Build Queue A)
      lands. Detail: `knowledge/ai-outreach-agency.md`.
6. [ ] **ai-outreach-agency: bump Ollama `READ_TIMEOUT` 60s→120s + add
      `keep_alive: "30m"`** to `/api/generate` — local generation sits close
      to the current timeout ceiling on cold-load calls, risking
      intermittent false-positive errors on a real batch. Small, single-file
      fix. Detail: `knowledge/ai-outreach-agency.md`.

## Backlog / ideas (not committed)

- [ ] Decide whether to fold this hub's `docs/todo.md` numbering back into
      a flat checklist once the current priority set clears — numbering
      is a point-in-time snapshot (set 2026-07-28), not a permanent
      convention.

## Done

- [x] **2026-07-28** — Cross-project status survey: cloned and checked
      live GitHub state for all 5 repos, merged `tlelosa-claude-config` PR
      #9, closed this repo's stale/conflicting PR #1, confirmed the
      Pappa T ↔ cloud-environment git-sync bridge end to end, and filled
      the TebelloReborn knowledge gap. Published as a dashboard artifact.
- [x] **2026-07-28** — Set this repo up as the real DCOE hub root per
      `hub-template`: `.claude/commands/continue.md`, this file, and
      `docs/session-log.md` added; root `CLAUDE.md` reconciled against
      `hub-template/HUB-CHECKLIST.md`.
- [x] **2026-07-28** — Pappa T vault survey (second pass, from a Pappa T
      session running concurrently with the hub-setup work above): resolved
      the `Claude-Code/` folder's earlier "untracked nested repo" flag from
      a Pappa T `/continue` run (it's this repo itself — deliberate, not
      stray work); replaced the inline TebelloReborn note in
      `knowledge/pappa-t.md` with a dedicated `knowledge/tebelloreborn.md`
      (more detail, and resolves that note's "[scraping specifics unclear]"
      gap); added four more Pappa T sub-project knowledge files
      (`ai-outreach-agency.md`, `mims-app.md`, `iq-signal-generator.md`,
      `tenders-sa.md`) — none of Pappa T's five sub-projects are independent
      git repos, so none had ever been individually tracked here. Confirmed
      no other dev-root exists on the Pappa T machine; noted `~/OneDrive/`
      and `~/Documents/Codex/` as data-only, `~/python-sdk/` as a runtime
      download, and the extra `~/Downloads/tlelosa-claude-config/` clone as
      already covered by its existing entry.
