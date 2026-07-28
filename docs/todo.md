# todo.md — Claude-Code hub (cross-project task queue)

Hub-level tasks only — work that spans projects, or new work started at
root. Each project's own `docs/todo.md` (in its own repo) is authoritative
for anything scoped inside that project; this file doesn't duplicate that
detail, only tracks it at a glance and links out.

Per DCOE: update after every completed task; one task = one commit.

## In progress

- [ ] None currently.

## Next up (priority order, set 2026-07-28)

1. [ ] **Close out the codex-gate rollout** (`tlelosa-claude-config`) — three
      items outstanding: install + network-off smoke-test on Pappa T, copy
      the drafted ADR into the Operations hub's `docs/decisions/`, and get
      Fan Movement IT to confirm OpenAI-egress coverage for Operations
      (codex-gate stays Pappa T-only until then). Detail:
      `tlelosa-claude-config/docs/todo.md`, `knowledge/tlelosa-claude-config.md`.
2. [ ] **NamePlateTool: add a real automated test suite** — not urgent;
      `tests/` is ad-hoc manual-check scripts only.
3. [ ] **TebelloReborn: decide on post-MVP scope** — Playwright auto-submit,
      recruiter/cold-outreach revival, and a doc-gen volume-cap/scheduler
      are all undecided backlog items, no urgency behind them yet. Detail:
      `knowledge/tebelloreborn.md` (supersedes the pointer to `pappa-t.md`
      this item previously had — see that project's own dedicated file now).
4. [ ] **ai-outreach-agency: top up OpenRouter credits** — `asset_gen` has
      been blocked on HTTP 402 since 2026-07-04; unblocks real (non-offline)
      batch runs until its headless-Claude-Code migration (Build Queue A)
      lands. Detail: `knowledge/ai-outreach-agency.md`.
5. [ ] **ai-outreach-agency: bump Ollama `READ_TIMEOUT` 60s→120s + add
      `keep_alive: "30m"`** to `/api/generate` — local generation sits close
      to the current timeout ceiling on cold-load calls, risking
      intermittent false-positive errors on a real batch. Small, single-file
      fix. Detail: `knowledge/ai-outreach-agency.md`.
6. [ ] **SOPS: give the go-ahead to run the AvgMovement migration against
      `instance/sops.db`** — Supplier/Lead-Time + AMU/Min-Max logic ported
      and fully tested (Batch 32/33, commits `fe06eaa`/`112e321`), held for
      Tebello per SOPS's standing schema-change convention. This is the
      blocking step before `8. AvgMovement` (already Retired in the
      Operations hub project index) can be decommissioned. Detail:
      `2. SOPS/docs/todo.md`, `knowledge/sops.md`.
7. [ ] **SOPS: Payment Status data-migration review** — a batch of
      historical Sales Orders need human review of migrated/backfilled
      payment-status values before being treated as fully validated.
      Detail: `2. SOPS/docs/todo.md` (2026-07-14 entry onward),
      `knowledge/sops.md`.

## Backlog / ideas (not committed)

- [ ] Decide whether to fold this hub's `docs/todo.md` numbering back into
      a flat checklist once the current priority set clears — numbering
      is a point-in-time snapshot (set 2026-07-28), not a permanent
      convention.

## Done

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
      already covered by its existing entry. Surfaced two new tasks from the
      survey (ai-outreach-agency credits + Ollama timeout, above).
- [x] **2026-07-28** — Added a machine-bound-task check to `/continue`
      (Step 2.5 in `.claude/commands/continue.md`): before reporting,
      flag candidate next-tasks that need local access on a specific
      machine (Pappa T, Operations) this session can't reach, and surface
      that in both the Step 3 report and the `AskUserQuestion` option
      descriptions. Prompted by this session offering the Pappa T vault
      survey as pickable from a cloud session where it wasn't actually
      runnable.
- [x] **2026-07-28** — Confirmed NamePlateTool's Excel-import bug (former
      #1 priority) was fixed in a separate session (commit `777be76`):
      datetime crash and dead `"Table 1"` sheet check both resolved.
      Discovered while syncing repo state across all 5 tracked repos after
      the Operations vault survey — only NamePlateTool had new activity.
      Updated `knowledge/nameplatetool.md`, removed the item from this
      queue. Not yet manually re-verified against a generated PDF from this
      session — worth a spot-check.
- [x] **2026-07-28** — Operations vault survey: enumerated every project
      folder on the Operations machine, confirmed no new project roots
      beyond the already-tracked ones plus three gaps (SOPS,
      delivery-note-system, Daily Sales Order Files — `8. AvgMovement`
      folded into `sops.md` as a note, not a separate file, since it's
      Retired and its logic was ported into SOPS). Wrote
      `knowledge/sops.md`, `knowledge/delivery-note-system.md`,
      `knowledge/daily-sales-order-files.md`; updated `knowledge/INDEX.md`;
      added two new outstanding items (#5, #6 above) to this queue.
- [x] **2026-07-28** — Set up Operations (work PC) as a DCOE hub client of
      this repo, mirroring the Pappa T setup: confirmed already cloned at
      `C:\Dev\Claude-Code` (sibling of `C:\Dev\Operations`, on `main`),
      confirmed the git-sync bridge end to end (`fetch` + `pull` pulled a
      real fast-forward of 8 files, `push --dry-run` confirmed clean),
      read root `CLAUDE.md` + `knowledge/INDEX.md`, and recorded the
      confirmation in `knowledge/operations-hub.md`.
- [x] **2026-07-28** — Cross-project status survey: cloned and checked
      live GitHub state for all 5 repos, merged `tlelosa-claude-config` PR
      #9, closed this repo's stale/conflicting PR #1, confirmed the
      Pappa T ↔ cloud-environment git-sync bridge end to end, and filled
      the TebelloReborn knowledge gap. Published as a dashboard artifact.
- [x] **2026-07-28** — Set this repo up as the real DCOE hub root per
      `hub-template`: `.claude/commands/continue.md`, this file, and
      `docs/session-log.md` added; root `CLAUDE.md` reconciled against
      `hub-template/HUB-CHECKLIST.md`.
