# CLAUDE.md — Project Brain

# Architecture: DCOE (Domain → Context → Orchestrate → Execute)

# Version: 1.0 | Based on: SOPS CLAUDE.md v3.2 | Owner: Tebello Lelosa

> Loaded at the start of every Claude Code session opened inside this project
> folder. Takes precedence over the root hub `CLAUDE.md`
> (`C:\Dev\Operations\CLAUDE.md`) for anything under this project — see hub
> hard rule 1. Onboarded to DCOE 2026-07-15 per
> `docs/decisions/ADR-001-dcoe-onboarding.md`.

-----

## 📁 PROJECT OVERVIEW

```
Project:     DELIVERY NOTE (delivery-note-system)
Type:        Full-stack web app, local dev (SQLite)
Stack:       Next.js 16 (App Router) + TypeScript + Prisma ORM + SQLite ·
             shadcn/ui components, sonner for toasts
Deployment:  Local dev via `npm run dev` (localhost:3000). No production
             deployment configured yet (docker-compose.yml exists but is
             unreviewed as part of this onboarding).
Runtime:     Node.js (see package.json), Prisma CLI for schema/migrations
Inference:   Model routing, effort tiers, and escalation rules follow the
             standing policy in root `CLAUDE.md` § Sub-agent roster — not
             duplicated here (ADR-002 pattern: point to the shared source).
Owner:       Tebello Lelosa
```

**What it does:** registers and lists delivery notes. A form captures date,
customer, and description; the DN number auto-increments from the last
issued one (`FM-DN0054` → `FM-DN0055`); submissions are stored via Prisma
into SQLite and shown in a register-history table. See
`docs/decisions/ADR-001-dcoe-onboarding.md` for the history of how this MVP
was found uncommitted and made the onboarding baseline.

-----

## ⚙️ ESSENTIAL COMMANDS

```bash
npm install
npm run dev                          # Dev server (localhost:3000)
npm run build
npm run lint

# Prisma
npx prisma generate                  # Regenerate client after schema changes
npx prisma migrate dev               # Create/apply a migration (dev)
npx prisma studio                    # Browse dev.db in a GUI

# Before every commit:
npm run lint                         # No test runner configured yet — see docs/todo.md
```

-----

## 🏗️ DCOE AGENT ARCHITECTURE

Same architecture as every DCOE project — full description in root
`CLAUDE.md` § DCOE Agent Architecture and § Sub-agent roster (deployed once
at user level, `~/.claude/agents/`, active automatically here). Not
duplicated in this file.

### DCOE Rules (project-specific reminders)

1. **Domain Agent** confirms scope before any schema change — `DeliveryNote`
   in `prisma/schema.prisma` is the single source of truth; a field added
   there needs the API routes (`src/app/api/dn/*`) and the UI
   (`src/app/page.tsx`'s `DeliveryNote` interface and form) updated
   together, in the same task.
2. **Context Agent** writes the plan to `docs/specs/` — never the code.
3. If acceptance criteria are unclear → **STOP and ask** (per hub hard rule
   8). No formal test suite gates changes yet, so unclear scope is easy to
   ship broken.

-----

## 📐 ARCHITECTURE NOTES

- **Data flow:** `page.tsx` form → `POST /api/dn/register` (validates
  required fields, checks `dnNumber` uniqueness, creates a `DeliveryNote`
  row) → `GET /api/dn` (list, newest first) and `GET /api/dn/next`
  (computes the next DN number) refresh the UI.
- **DN-number generation** (`src/app/api/dn/next/route.ts`) takes the
  *most recently created* record and regex-increments its numeric suffix.
  This assumes records are always created in increasing DN order and never
  deleted or backdated — if that assumption is ever broken (a record
  deleted, or `createdAt` manipulated), the "next" number could collide or
  skip. Known limitation, not yet fixed — flag it if a bug report ever
  traces back here.
- **`src/lib/prisma.ts`** uses the standard Next.js dev-mode singleton
  pattern (`globalThis.prismaGlobal`) to avoid exhausting connections on
  hot reload. Don't `new PrismaClient()` directly elsewhere — import from
  here.
- **No auth, no multi-user concerns** — single-operator tool as of this
  onboarding. If that changes, it's a deliberate design decision (ADR), not
  an assumed default.

-----

## 🧪 TESTING STANDARDS

No automated test suite exists yet (no `tests/` folder, no test runner
configured in `package.json`). Not a blocker for small fixes, but any
non-trivial change to the API routes or Prisma schema should be manually
verified (register a note, confirm it lists correctly, confirm the next DN
number increments) before considered done. Building a real suite is
tracked in `docs/todo.md`.

-----

## 🔑 CONTEXT MANAGEMENT

Same discipline as every DCOE project — see root `CLAUDE.md` § Context
Management. `docs/todo.md` is rewritten at the end of every project-level
task (anti-drift pattern).

-----

## 📂 DIRECTORY STRUCTURE

```
7. DELIVERY NOTE/delivery-note-system/
├── CLAUDE.md                    ← You are here (project brain)
├── AGENTS.md                    ← Next.js-version warning, see Hard Rules
├── README.md                    ← Still create-next-app boilerplate, see docs/todo.md
├── docker-compose.yml           ← Unreviewed as part of this onboarding
├── prisma/
│   └── schema.prisma            ← DeliveryNote model (SQLite)
├── prisma.config.ts
├── src/
│   ├── app/
│   │   ├── api/dn/               ← route.ts (list), next/, register/
│   │   ├── page.tsx              ← Register form + history table (client)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/ui/            ← shadcn components (button, card, input, …)
│   └── lib/                      ← prisma.ts (client singleton), utils.ts
├── dev.db                        ← SQLite dev database, gitignored
├── docs/                         ← DCOE planning layer (new, 2026-07-15)
│   ├── todo.md
│   ├── session-log.md
│   ├── decisions/                ← ADR log (ADR-001-*.md, project-scoped)
│   ├── bugs/
│   ├── research/
│   └── specs/
└── .claude/
    ├── commands/continue.md      ← /continue — project session resume
    └── settings.json             ← Allow/deny permission rules
```

-----

## ⚠️ HARD RULES — NEVER VIOLATE

Inherits every hard rule from root `CLAUDE.md` § Hard Rules. Project-specific
additions:

1. **This project's Next.js version (16.2.6) postdates any AI assistant's
   training data and has documented breaking changes.** `AGENTS.md` flags
   this; it's real — `node_modules/next/dist/docs/` genuinely exists here.
   Read the relevant guide there before writing Next.js-specific code
   (routing, config, API route conventions) rather than assuming
   training-data knowledge still applies.
2. **`prisma/schema.prisma` changes are a contract** — update the API
   routes and the frontend's `DeliveryNote` interface/form together, in the
   same task, never one file in isolation.
3. **`dev.db` is gitignored, not committed.** Don't add it to git as a side
   effect of a broad `git add .` — it's local dev data, not source.
4. **Ask before deleting** anything under `docs/decisions/` or before
   running any Prisma command that resets/drops data (`prisma migrate
   reset`, manual `DROP TABLE`) — matches hub hard rule 4 on production/data
   paths, applied here to the dev database since there's no separate
   "production" data path yet.

-----

*Last review: 2026-07-15 — Tebello Lelosa (initial DCOE onboarding)*
