# Operations — Fan Movement (Pty) Ltd

Internal working folder for tools, projects, and business data. If you're
Claude Code (or a human) landing here cold, read [`CLAUDE.md`](CLAUDE.md)
first — it's the hub brain and links out to everything else.

## Active projects

| Folder | What it is |
| --- | --- |
| [`2. SOPS/`](2.%20SOPS) | Sales Order Processing System — Flask app, live production, own DCOE workflow |
| [`7. DELIVERY NOTE/delivery-note-system/`](7.%20DELIVERY%20NOTE/delivery-note-system) | Delivery note generator — Next.js app |
| [`1. Daily Sales Order Files/`](1.%20Daily%20Sales%20Order%20Files) | Python pipeline: Sage export → daily sales order report |
| [`8. AvgMovement/`](8.%20AvgMovement) | Python pipeline: inventory movement reporting |
| [`Inventory Management & Reports/`](Inventory%20Management%20%26%20Reports) | Python pipeline: extract → build inventory → report |
| [`3. Nameplate & Test Sheet/`](3.%20Nameplate%20%26%20Test%20Sheet) | Nameplate / test sheet generator — full-stack app |

## Data folders (no code)

`4. Casing Analysis/`, `Sage Inventory Report/`, `Stock Report Reference/`,
`Workshop Stock - */`, `FM Planning & Stock Control/` — xlsx masters and
ERP exports.

## Reference

`0. Agents/` — the DCOE agent/prompt template library this whole setup is
based on. `IDE/` — editor shortcuts only, not a project.

## Working method

This folder runs on **DCOE** (Domain → Context → Orchestrate → Execute).
See [`CLAUDE.md`](CLAUDE.md) for the full model, [`docs/todo.md`](docs/todo.md)
for the current task queue, and [`docs/patterns.md`](docs/patterns.md) for
workflow patterns proven across projects.
