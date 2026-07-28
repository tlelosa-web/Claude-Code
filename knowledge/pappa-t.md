## 2026-07-28 — Vault survey: sub-projects catalogued, Claude-Code hub resolved, data-only folders noted
**Source:** Pappa T session (cross-project status survey)
**Status:** active

Full survey of this machine for projects not yet in `knowledge/INDEX.md`, mirroring
the Operations vault survey pattern. Findings:

- **This very `Claude-Code/` repo lives physically inside the Pappa T vault**
  (`Desktop/Pappa T/Claude-Code/`), as its own independent git repo (remote
  `tlelosa-web/Claude-Code`, clean working tree) — not a submodule, just a sibling
  folder. A prior `/continue` run in a Pappa T session flagged it as an
  "untracked nested repo, unclear origin" (it shows up as untracked in `git status`
  from the Pappa T repo's own perspective, since Pappa T's `.gitignore` doesn't
  cover it and it isn't a submodule either). Resolved: this is expected and fine —
  it's a deliberate, already-committed, already-pushed repo, not stray in-progress
  work. Not a violation to "clean up."
- **TebelloReborn's "known gap" is now filled** — see `tebelloreborn.md` (new file).
- Four more Pappa T sub-projects had no dedicated knowledge file yet and got one:
  `ai-outreach-agency.md`, `mims-app.md`, `iq-signal-generator.md`, `tenders-sa.md`.
  None of these five sub-projects are independent git repos — they're folders inside
  the single Pappa T vault repo, so there was no remote to dedupe against; the
  survey's "genuinely new project" test applied by absence of any dedicated file.
- **Data-only, no code — noted and skipped, no dedicated file:** `~/OneDrive/` (CVs,
  personal spreadsheets, scanned documents — a synced personal-data folder, not a
  project) and `~/Documents/Codex/` (empty). `~/python-sdk/` is a downloaded Python
  runtime (`python3.13.2/`), not a git repo or project — skipped as tooling, not a
  project.
- `~/Downloads/tlelosa-claude-config/` (+ a `.zip` of the same) is a redundant extra
  clone of the already-tracked `tlelosa-claude-config` repo (same remote) — already
  covered by the existing `tlelosa-claude-config.md` entry, skipped per the
  remote-match dedupe rule.
- No other dev-root candidates found: no `~/Dev`, `~/Projects`, or similar folder
  exists on this machine — Desktop's only project folder is `Pappa T/` itself.

## 2026-07-26 — What Pappa T is
**Source:** session
**Status:** active

Pappa T is Tebello's personal machine, running Claude Code locally — the
counterpart to **Operations** (the Fan Movement work PC). Not a registered
Claude Code Remote/on-the-web environment (`list_environments` only shows
the cloud `Default` sandbox); there's no live bridge between it and remote
sessions. The only working sync channel between Pappa T and any other
session (Operations, remote environments) is git: push from one side, pull
from the other, per `CLAUDE.md`'s knowledge-cache rules. See
`tlelosa-claude-config.md` for the repos it shares with Operations, and
`knowledge/INDEX.md` for the machine/repo split.

## 2026-07-26 — Pappa T-only items
**Source:** session
**Status:** active

- `codex-gate` (OpenAI egress plugin, in `tlelosa-claude-config`) is
  installed/tested Pappa T-only for now — not yet cleared for Operations
  pending a separate OpenAI-egress confirmation from Fan Movement IT. See
  `tlelosa-claude-config.md` for the open smoke-test item.
- **TebelloReborn** — a project that lives on Pappa T. No further details
  captured yet; flagged here as a known gap to fill in from a Pappa T
  session.
