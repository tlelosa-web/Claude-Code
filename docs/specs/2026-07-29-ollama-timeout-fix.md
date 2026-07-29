# Spec — ai-outreach-agency: Ollama timeout + keep_alive fix

**Machine:** Pappa T only (`Pappa T/ai-outreach-agency/` — not a hosted repo,
filesystem-only).
**Todo item:** `docs/todo.md` "ai-outreach-agency: bump Ollama `READ_TIMEOUT`
60s→120s + add `keep_alive: "30m"`"
**Size:** small, single-file.

## Goal

Local Ollama generation latency sits close to the current 60s `READ_TIMEOUT`
ceiling on this CPU-only machine — a cold-load call can exceed 60s and raise
a correctly-typed `OllamaError`, risking intermittent false-positive errors
mid-batch.

## Steps

1. In `Pappa T/ai-outreach-agency/`, find the Ollama client used by the
   `research` stage — the file making the `POST /api/generate` call to
   `qwen3:8b` (per ADR-004; near wherever `OllamaError`/
   `OllamaUnreachableError` are defined, see the exception-conflation fix in
   commit `338002f`).
2. Change the `READ_TIMEOUT` constant (or equivalent value passed to the
   `requests`/`httpx` call) from 60 to 120.
3. Add `"keep_alive": "30m"` to the JSON payload dict sent to
   `/api/generate`, so Ollama's default 5-minute idle-unload doesn't force a
   repeat cold-load mid-batch.
4. Do not touch the `OllamaError`/`OllamaUnreachableError` distinction —
   already correct, out of scope here.
5. Run the existing test suite; confirm it's still green.
6. Commit in the `ai-outreach-agency` folder with a message referencing the
   timeout/keep_alive fix.

## Definition of done

- `READ_TIMEOUT` = 120, `keep_alive: "30m"` present in the `/api/generate`
  payload, tests pass, committed.

## Hub bookkeeping (after the fix lands)

- Pull `origin/main` on this hub repo first (Hard Rule 6).
- Append a dated entry to `knowledge/ai-outreach-agency.md` superseding the
  2026-07-28 "recommended fix, not yet implemented" note.
- Remove this item from `docs/todo.md`, renumber remaining items, add a
  `docs/session-log.md` entry.
