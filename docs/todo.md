# todo.md — Claude-Code hub (cross-project task queue)

Hub-level tasks only — work that spans projects, or new work started at
root. Each project's own `docs/todo.md` (in its own repo) is authoritative
for anything scoped inside that project; this file doesn't duplicate that
detail, only tracks it at a glance and links out.

Per DCOE: update after every completed task; one task = one commit.

## In progress

- [ ] None currently.

## Next up (priority order, set 2026-07-28; specs added 2026-07-29 so each
machine-bound item is ready to hand to an executor the moment `/continue`
runs on the right machine)

1. [ ] **NamePlateTool: spot-check the Excel-import fix** — commit
      `777be76` fixed the datetime crash + dead sheet-name check
      (2026-07-28), but no session has manually verified the fix against a
      real generated PDF yet. ⚠️ Operations only. Spec (ready):
      `docs/specs/2026-07-29-nameplatetool-excel-spotcheck.md`. Detail:
      `knowledge/nameplatetool.md`.
2. [ ] **codex-gate: Pappa T install + network-off smoke-test.** ⚠️ Pappa T
      only. Spec (ready):
      `docs/specs/2026-07-29-codex-gate-pappa-t-smoketest.md`.
      codex-gate itself stays Pappa T-only regardless — Fan Movement IT
      still needs to confirm OpenAI-egress coverage for Operations before
      install there (no spec for this one — it's a pending external
      answer, not a task any session can execute). Detail:
      `knowledge/tlelosa-claude-config.md`.
3. [ ] **NamePlateTool: add a real automated test suite** — not urgent;
      `tests/` is ad-hoc manual-check scripts only. ⚠️ Operations only.
      Spec (ready, starter scope — confirm before building):
      `docs/specs/2026-07-29-nameplatetool-test-suite.md`.
4. [ ] **TebelloReborn: decide on post-MVP scope** — Playwright auto-submit,
      recruiter/cold-outreach revival, and a doc-gen volume-cap/scheduler
      are all undecided backlog items, no urgency behind them yet. ⚠️
      Pappa T only. Spec (ready, decision brief — not a build spec):
      `docs/specs/2026-07-29-tebelloreborn-scope-decision.md`. Detail:
      `knowledge/tebelloreborn.md`.
5. [ ] **ai-outreach-agency: bump Ollama `READ_TIMEOUT` 60s→120s + add
      `keep_alive: "30m"`** to `/api/generate`. Small, single-file fix. ⚠️
      Pappa T only. Spec (ready):
      `docs/specs/2026-07-29-ollama-timeout-fix.md`. Detail:
      `knowledge/ai-outreach-agency.md`.
6. [ ] **SOPS: give the go-ahead to run the AvgMovement migration against
      `instance/sops.db`** — Supplier/Lead-Time + AMU/Min-Max logic ported
      and fully tested (Batch 32/33, commits `fe06eaa`/`112e321`), held for
      Tebello per SOPS's standing schema-change convention. This is the
      blocking step before `8. AvgMovement` (already Retired in the
      Operations hub project index) can be decommissioned. ⚠️ Operations
      only. Spec (ready, but gated — do not run without explicit
      in-session go-ahead):
      `docs/specs/2026-07-29-sops-avgmovement-migration.md`. Detail:
      `2. SOPS/docs/todo.md`, `knowledge/sops.md`.
7. [ ] **SOPS: Payment Status data-migration review** — a batch of
      historical Sales Orders need human review of migrated/backfilled
      payment-status values before being treated as fully validated. ⚠️
      Operations only. Spec (ready):
      `docs/specs/2026-07-29-sops-payment-status-review.md`. Detail:
      `2. SOPS/docs/todo.md` (2026-07-14 entry onward), `knowledge/sops.md`.

## Backlog / ideas (not committed)

- [ ] None currently.

## Done

- [x] **2026-07-31** — pitwall-companion: added Spa (Belgium) to the `TRACKS`
      Track Stats list (driver stat Overtaking, component stat Power Unit),
      transcribed from an in-game screenshot — pushed directly to
      `claude/repo-update-check-mn1wv2` (not yet opened as a PR). Not its
      own queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: made the Loadouts → By Track
      loadout customizable, matching By Attribute — merged as PR #15 (final
      pitwall-companion change of the day; the app was then shared to
      Tebello's Discord for a trusted-tester trial week). The loadout card
      was previously locked to the track's single official component stat;
      it now has its own attribute toggle bar (independent of By Attribute
      mode's selection), defaulting to the track's stat but adjustable from
      there, and resetting to that default whenever the track changes. The
      driver ranking and Suggested Boost stay tied to the track's official
      stats by design — only the loadout became customizable. Hit the same
      class of merge-conflict issue as PR #14 (long-lived branch, several of
      its own prior PRs squash-merged into `main` without the branch ever
      restarting from it) — resolved the same way: keep the branch's newer
      code, then verify with an executability check + full regression pass
      rather than trusting a clean "no conflict markers" diff alone. Not its
      own queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: Loadouts → By Track, Suggested
      Boost, and a Boosts-ownership tab — merged as PR #14 (after resolving a
      real merge conflict that briefly resurrected already-superseded code;
      see `docs/session-log.md` for how). Loadouts gained a mode switch (By
      Attribute / By Track); By Track adds a 21-circuit dropdown showing the
      best 2 owned drivers for the track's driver stat, a Suggested Boost
      (top 3 owned consumable Boosts ranked by driver stat then component
      stat), and the same full loadout card as before for the component
      stat. New 4th Tools tab "Boosts" tracks quantities owned per consumable
      Boost (dropdown picker, not a 65-item scroll) and includes a New Boost
      form for boosts the game adds faster than this app can track — custom
      entries compete in Suggested Boost rankings alongside built-ins. Added
      4 newly-discovered boosts (Livewire Plus, Midnight, Mushroom,
      Succession) transcribed from Tebello's own in-game screenshots.
      Overhauled README.md, which had gone stale across the last several
      merges (still described single-mode Loadouts, no mention of Boosts tab
      or Track Spec, undercounted boosts at 65 instead of 69). Not its own
      queue item for the same reason as the entries below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: follow-up polish batch after the
      workbook audit + Loadouts picker (below) — merged as PRs #11 and #12:
      fixed the header's small icon (was still the pre-rename inline-SVG
      placeholder, now uses the real `icons/icon-192.png` pit-wall artwork)
      and centered the header title; renamed the app's user-facing branding
      from "F1 Clash Resource Sheet" to **PitWall Companion** (title, header,
      manifest name/short_name, export filename/tag, QR alt text) per
      Tebello's copyright-exposure concern about the app's own name leaning
      on the game's trademark — left factual/disclaimed game and workbook
      references untouched (already covered by the existing "unaffiliated
      fan tool" disclaimer), and left the internal `localStorage` keys /
      cache-version string (`f1sheet.*`) untouched since renaming those
      would silently wipe existing users' saved card levels; and laid out
      both the Loadouts attribute-toggle buttons and the aggregate stat
      chips as equal-size grids (2x2 and 2x3) instead of uneven flex-wrap
      rows. Not its own queue item for the same reason as below. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-31** — pitwall-companion: audited the app against the
      community "F1 Clash 2026 Resource Sheet" workbook (v1.1, the
      confirmed source-of-truth version) — no gaps found, driver/part
      rosters, per-level stats, Series unlocks, and CCData/rewards
      constants all in sync. Then, per Tebello's direction, replaced the
      Suggested Loadouts tool's 9 stacked fixed-strategy cards with 4
      multi-select attribute toggle buttons (Speed/Cornering/Power
      Unit/Qualifying) rendering a single live card, removing the need to
      scroll; selection persists via its own localStorage key. Verified
      with a headless-browser smoke test (single-card render, multi-select
      combine, last-attribute deselect guard, reload persistence, zero
      console errors) before pushing. Merged as PR #9
      (tlelosa-web/pitwall-companion), then updated `README.md`'s Loadouts
      description to match (PR #10, merged) since it still described the
      old fixed-strategy list. Not tracked as its own queue item since
      pitwall-companion isn't part of this hub's machine-bound spec queue
      and has no `docs/todo.md` of its own — logged here per Hard Rule 5
      since Tebello asked for the hub log to be updated. See
      `docs/session-log.md` for full detail.
- [x] **2026-07-29** — codex-gate: copied the drafted ADR into this hub's
      `docs/decisions/` (`ADR-009-codex-second-opinion-gate.md`), closing
      the documentation sub-item — done via git directly from a cloud
      session (no Operations machine access needed, since this hub repo
      is git-synced there, not filesystem-only). Discovered `docs/decisions/`
      didn't exist yet and neither ADR-007 nor ADR-008 were actually
      recorded there despite being referenced from `tlelosa-claude-config`.
      codex-gate install itself stays Pappa T-only, unaffected by this.
- [x] **2026-07-29** — Wrote up `ADR-007-core-md-read-not-import.md` and
      `ADR-008-hub-template-promotion.md` in this hub's `docs/decisions/`,
      closing the gap found above — both reconstructed from what's
      documented across `tlelosa-claude-config` (CORE.md's own
      distribution note, README, `HUB-CHECKLIST.md`), not from source
      commits (this session doesn't have `tlelosa-claude-config`'s git
      history). ADR-008's date is approximate.
- [x] **2026-07-29** — Wrote a ready-to-execute spec for every machine-bound
      item in this queue (`docs/specs/2026-07-29-*.md`, 8 files: NamePlateTool
      spot-check + test suite, codex-gate Pappa T smoke-test + Operations
      ADR copy, TebelloReborn scope decision, ai-outreach-agency Ollama
      timeout, SOPS AvgMovement migration (gated) + Payment Status review)
      — so the moment `/continue` runs on Pappa T or Operations, the next
      task on that machine already has exact steps, no fresh research
      needed. Linked each spec from its `docs/todo.md` item and split the
      3-part codex-gate item into 3 numbered items (2 machine-bound specs +
      1 externally-gated item with no spec) since they don't share a
      machine. Fixed a numbering gap (item "3" had been skipped since the
      2026-07-29 renumbering).
- [x] **2026-07-29** — Removed the "ai-outreach-agency: top up OpenRouter
      credits" item per Tebello's direction — treated as a dead end, not
      pursued. `asset_gen` stays blocked on OpenRouter until the
      headless-Claude-Code migration (Build Queue A) lands instead; see
      `knowledge/ai-outreach-agency.md` for the superseded entry.
- [x] **2026-07-29** — Hub process review: promoted the NamePlateTool
      Excel-import spot-check (previously just a prose caveat in
      `session-log.md`) to a tracked `docs/todo.md` item; resolved the
      numbering-backlog question by keeping fixed numbering (renumbered
      1-9) since the priority set hasn't cleared yet and the "fold to flat
      checklist" question only mattered once it does; added `CLAUDE.md`
      Hard Rule 6 and `/continue` Step 1.75 ("Sync Check") to fix the root
      cause of the two real merge conflicts already hit on
      `docs/todo.md`/`session-log.md`/`knowledge/INDEX.md` — pull
      `origin/main` before editing any of the three contention files.
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
