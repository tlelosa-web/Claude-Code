# Spec — NamePlateTool: spot-check the Excel-import fix

**Machine:** Operations only (`C:\Dev\Operations\...\NamePlateTool`, or
wherever it's cloned on this machine — confirm path if unsure).
**Todo item:** `docs/todo.md` "NamePlateTool: spot-check the Excel-import
fix"
**Size:** verification only, no code change expected unless the spot-check
fails.

## Goal

Commit `777be76` fixed the `/api/nameplate/from-excel` datetime-crash bug
(`date_of_manuf` now goes through `_fmt_month_year()`) and removed the dead
`"Table 1"` primary-sheet check. No session has manually verified the fix
against a real generated PDF since it landed (2026-07-28).

## Steps

1. Launch NamePlateTool locally (`RUN_PIPELINE.bat` or
   `Launch_NamePlate_Tool.vbs`, per `knowledge/nameplatetool.md`).
2. Run the Excel-import path (`/api/nameplate/from-excel`) against a real
   `NAME PLATE PROCEDURE` workbook using the `Info+Data Entry Form` /
   `NamePlateProc` sheet.
3. Confirm: no `datetime is not JSON serializable` crash, and the generated
   PDF has correctly formatted (non-blank) `date_of_manuf` and other
   Excel-sourced fields.
4. If it fails: capture the exact error/output and treat as a new bug —
   don't attempt a fresh fix in this same pass without re-reading
   `knowledge/nameplatetool.md`'s history of the two prior attempts (one
   reverted for reintroducing blank fields).

## Definition of done

- A real Excel-import → PDF-generation run confirmed correct, or a new bug
  filed with concrete repro details if not.

## Hub bookkeeping (after the check)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Update `knowledge/nameplatetool.md`'s 2026-07-28 fix entry to note manual
  verification is now confirmed (or add a new entry if a new bug surfaced).
- Remove this item from `docs/todo.md`, renumber remaining items, add a
  `docs/session-log.md` entry.
