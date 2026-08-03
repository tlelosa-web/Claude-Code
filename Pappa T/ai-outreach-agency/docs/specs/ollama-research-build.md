# Spec: Local Ollama Inference for the Research Summariser — Build Plan

**Project:** ai-outreach-agency
**Owner:** Tebello Lelosa
**Status:** Ready for Executor (pending Tebello's prerequisite install — see §Prerequisites)
**Pattern:** DCOE Pattern 1 (New Feature)
**ADR:** `docs/decisions/ADR-004-local-ollama-research-inference.md`
**Branch:** `feature/handoff-tracking` (shared with the asset_gen handoff track;
independently orderable — touches different modules, zero file overlap).

---

## 1. Goal

Replace the OpenRouter call in `research/claude_summariser.py::summarise_lead()`
with a local Ollama call (`qwen3:8b`, native `/api/generate` endpoint at
`http://localhost:11434` by default), at $0 marginal cost. This is the second of
two parallel cost-elimination tracks — the first (asset_gen → headless Claude
Code) is `docs/specs/handoff-tracking-build.md`. Together they let the whole
pipeline run end-to-end at $0.

Embeddings (`nomic-embed-text`) are **out of scope** — no consumer exists in the
codebase today (see ADR-004 Context). Not built.

---

## 2. What changes (code that is buildable now)

- **New:** `src/research/ollama_client.py` — `call_ollama(prompt)` +
  `OllamaError` / `OllamaUnreachableError`, module-level `RateLimiter`, no API
  key, short connect-timeout reachability check. Placement in `research/` (not
  `shared/`) justified in ADR-004 §Decision.2 against the `apify_client.py`
  precedent.
- **Edit:** `src/config.py` — add `OLLAMA_BASE_URL` (default
  `http://localhost:11434`) and `OLLAMA_MODEL` (default `qwen3:8b`) to `Settings`
  + `load_settings`.
- **Edit:** `src/research/claude_summariser.py` — non-offline branch calls
  `call_ollama` instead of `call_openrouter`. The `OFFLINE_MODE` guard and
  `_stub_summary` are preserved byte-for-byte (see §4).
- **Edit:** `.env.example` — add `OLLAMA_BASE_URL` + `OLLAMA_MODEL`.
- **Docs:** `docs/api-patterns.md`, `docs/architecture.md`, `CLAUDE.md`,
  `docs/todo.md`.
- **No migration file** — no schema change (ADR-004 §Decision.6).

---

## 3. Convention anchors (read before building)

- **OFFLINE_MODE lives in the caller, not the client** — mirror
  `claude_summariser.py`'s existing structure and `apify_client.py`. The client
  is a thin real-call wrapper; the offline stub short-circuits upstream.
- **Rate limiter** — module-level `RateLimiter` acquired before the request,
  env override `OLLAMA_RATE_LIMIT_PER_MIN` (default `120`), same shape as
  `openrouter_client.py` / `apify_client.py`.
- **Config** — `Settings` dataclass field + `os.environ.get` in
  `load_settings`, identical to every existing field.
- **Tests** — unit `conftest.py` already forces `OFFLINE_MODE=true`; client
  tests mock `requests.post` directly (as done for OpenRouter). No real HTTP to
  `localhost:11434` in any test.

---

## 4. OFFLINE_MODE — preserve, do not re-add

`summarise_lead()` already reads:

```python
if os.environ.get("OFFLINE_MODE", "").lower() in ("1", "true"):
    return _stub_summary(lead, raw_data)
```

Keep this exactly. The only line that changes is the final
`return call_openrouter(prompt)` → `return call_ollama(prompt)`. This guarantees
the full suite stays green offline with zero Ollama dependency.

---

## 5. Fallback behaviour — fail loudly

On unreachable Ollama, raise `OllamaUnreachableError` and let it propagate. No
silent fallback to OpenRouter (which is itself out of credits). Full reasoning in
ADR-004 §Decision.5.

---

## 6. Reviewer sign-off assessment

**No step here requires mandatory pre-execution Reviewer sign-off.** Checked
against this project's criteria (approval-gate-adjacent, or output reaching the
human review queue via an unreviewed path):

- The research stage sits well upstream of the approval gate. `research.summary`
  only ever feeds an `asset_gen` prompt; the human reviews the generated *asset*
  at the gate, never the raw summary directly.
- This is a like-for-like inference-backend swap of an LLM call that already fed
  that same downstream path — it introduces no new path to the approval queue
  and does not touch the approval-gate interaction.

Standard rule still applies: **Reviewer (Opus) approves before merge**, as for
all file-write / network-client code (`ollama_client.py` is a new network
client). That is the normal gate, not a pre-execution block.

---

## 7. Ordered atomic task list (buildable now)

Executor legend: **architect**, **tester**, **executor**, **doc-writer**,
**reviewer**. TDD-paired (RED before GREEN).

| # | Description | Executor | Input files | Expected output | Verification |
|---|---|---|---|---|---|
| 1 | Write ADR-004 (decision, embedding scope-out, placement, fallback, no-migration) | architect | `research/*`, `src/config.py`, `docs/specs/handoff-tracking-build.md` | `docs/decisions/ADR-004-local-ollama-research-inference.md` | Read-through: covers backend swap, embeddings scoped out, `research/` placement justified, fail-loud fallback, no-migration rationale — **done in this commit** |
| 2 | RED: config tests for `OLLAMA_BASE_URL` / `OLLAMA_MODEL` (defaults + env override) | tester | `src/config.py` | `tests/unit/test_config.py` (new or extended) | `pytest` fails (fields don't exist yet) |
| 3 | GREEN: add `OLLAMA_BASE_URL`, `OLLAMA_MODEL` to `Settings` + `load_settings` | executor | Step 2 test | `src/config.py` | Step 2 passes; existing config/CLI tests still green |
| 4 | RED: ollama client tests — mocked `requests.post`: success/`response` parse, connection-refused → `OllamaUnreachableError`, connect-timeout → `OllamaUnreachableError`, non-200 → `OllamaError`, bad JSON shape → `OllamaError`, rate-limiter `.acquire()` called, `think:false`/clean-prose handling, no API-key logic | tester | ADR-004, `shared/openrouter_client.py` (shape) | `tests/unit/test_ollama_client.py` | `pytest` fails (module doesn't exist) |
| 5 | GREEN: ollama client (`call_ollama`, `OllamaError`, `OllamaUnreachableError`, module `RateLimiter`, `OLLAMA_RATE_LIMIT_PER_MIN`) | executor | Step 4 test | `src/research/ollama_client.py` | Step 4 passes; zero real HTTP in test run |
| 6 | RED: summariser swap tests — OFFLINE_MODE still returns `_stub_summary`; non-offline calls `call_ollama` (not `call_openrouter`); `OllamaUnreachableError` propagates (no OpenRouter fallback) | tester | `research/claude_summariser.py` | `tests/unit/test_claude_summariser.py` (new or extended) | `pytest` fails |
| 7 | GREEN: swap `call_openrouter` → `call_ollama` in `summarise_lead()`'s non-offline branch only; OFFLINE guard untouched | executor | Step 6 test, Step 5 client | `src/research/claude_summariser.py` | Step 6 passes; grep confirms no `call_openrouter` / `openrouter` import remains in `research/` |
| 8 | `.env.example` entry (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`) | executor | ADR-004 | `.env.example` | Valid; no secrets; defaults match `Settings` |
| 9 | RED: integration test — full offline pipeline research stage produces a `summary`, zero real HTTP to `localhost:11434` | tester | `tests/integration/test_full_pipeline.py` | Same file, extended | `pytest` fails |
| 10 | GREEN: close any gaps Step 9 surfaces | executor | Step 9 test | Whichever file needs a small fix | Step 9 passes; full suite green (129 + new) |
| 11 | Acceptance verification pass | tester + reviewer | §8 checklist | Checklist ticked | Every box re-verified independently |
| 12 | `docs/api-patterns.md` — add "Local Ollama Inference (research)" section | doc-writer | ADR-004, this spec | `docs/api-patterns.md` | Mirrors existing OpenRouter/Apify/Gmail section format; notes no-auth + reachability |
| 13 | `docs/architecture.md` + `CLAUDE.md` research-stage / stack description update | doc-writer | This spec | `docs/architecture.md`, `CLAUDE.md` | Research stage no longer implies OpenRouter; notes local Ollama + local runtime dependency |
| 14 | Final `docs/todo.md` update | doc-writer | All of the above | `docs/todo.md` | Ollama Build Queue cleared to done; Known Issues updated (research no longer OpenRouter-blocked once prerequisites met) |

**Total buildable steps: 14** (Step 1 = this ADR, satisfied in this commit;
13 remaining for executors).

### Dependency ordering

- Steps 2–3 (config) before Step 5 (client reads `Settings`) and Step 7.
- Step 5 (client) before Step 7 (summariser swap).
- Step 7 before Step 9 (integration).
- Steps 12–14 (docs) last, after Step 11 confirms behaviour.
- Steps 2–3 and 4–5 can run in parallel worktrees (config vs. client are
  independent until Step 7 joins them).

---

## 8. Acceptance criteria

- [ ] `OLLAMA_BASE_URL` / `OLLAMA_MODEL` present on `Settings` with correct
      defaults and env overrides.
- [ ] `src/research/ollama_client.py` exists; `call_ollama` returns the model
      `response` on success, raises `OllamaUnreachableError` (fast, clear) when
      the daemon is down, `OllamaError` on non-200 / bad shape. No API-key logic.
- [ ] Rate limiter `.acquire()` is called before the request.
- [ ] `summarise_lead()` OFFLINE branch unchanged; non-offline branch calls
      `call_ollama`; no `call_openrouter` reference remains in `research/`.
- [ ] No silent OpenRouter fallback — unreachable Ollama propagates the error.
- [ ] Full suite (129 + new) green; `OFFLINE_MODE` autouse fixture means **zero**
      real HTTP to `localhost:11434` in any test.
- [ ] No migration file added / needed (no schema change).
- [ ] `nomic-embed-text` / embeddings **not** built (confirmed out of scope).

---

## Prerequisites (Tebello only — manual, not executor-agent steps)

These are **local system changes on Tebello's actual desktop**. An executor
agent must **not** run these unprompted — they require Tebello's explicit action
(they change what's installed on the machine and pull multi-gigabyte data). The
code in §7 is buildable and its tests pass **offline regardless** of whether
these are done; these must only be satisfied before the wired-in research stage
can be exercised for **real** (a live, non-offline batch run).

**P1 — Install the Ollama application (Windows):**

- **Primary (reliable):** download the official installer `OllamaSetup.exe` from
  <https://ollama.com/download> and run it. On Windows it installs Ollama as a
  background service that auto-starts and listens on `http://localhost:11434`.
- **Alternative (winget):** `winget install Ollama.Ollama`
  — ⚠️ **verify the exact package ID first** with `winget search ollama`; the
  ID `Ollama.Ollama` is the expected identifier but has not been verified on this
  machine, so confirm before trusting it. If it doesn't resolve, use the official
  installer above.

**P2 — Pull the generation model (multi-GB download, ~5 GB):**

```
ollama pull qwen3:8b
```

**P3 — (NOT needed) embeddings model:**

Do **not** run `ollama pull nomic-embed-text`. It is scoped out (ADR-004) — no
consumer exists in the codebase. Listed here only to state explicitly that it is
intentionally skipped, not forgotten.

**P4 — Verify Ollama is live before a real run:**

```
ollama list                         # should show qwen3:8b
curl http://localhost:11434/api/tags   # should return 200 with the model listed
```

If `curl` refuses the connection, Ollama isn't running — start it (it normally
auto-starts as a Windows service after P1).

---

## 9. Rollback

Additive / swap-only. Rollback = revert Step 7 (`summarise_lead` calls
`call_openrouter` again), remove `src/research/ollama_client.py`, drop the two
`Settings` fields + `.env.example` lines. No table, no approval-gate logic, and
no other module is touched.
