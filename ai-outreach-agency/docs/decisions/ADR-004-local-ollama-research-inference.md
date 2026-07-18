# ADR-004: Local Ollama Inference for the Research Summariser

**Status:** Proposed (awaiting Tebello's approval + prerequisite install)
**Date:** 2026-07-19
**Decider:** Tebello Lelosa
**Author:** Architect (Opus, escalation tier — ADR / cross-cutting inference-backend change)

## Context

The pipeline has two OpenRouter call sites:

- `asset_gen/generator.py::generate_asset()` — being moved to headless Claude
  Code (`claude -p`) under a separate, already-committed plan
  (`docs/specs/handoff-tracking-build.md` / ADR-003). Out of scope here.
- `research/claude_summariser.py::summarise_lead()` — still calls
  `call_openrouter(prompt)` to turn Apify-scraped `raw_data` into the
  `ResearchResult.summary` string. This is the **only** remaining OpenRouter
  call site once the asset_gen handoff lands.

The whole pipeline is currently blocked: the OpenRouter account is out of
credits (HTTP 402, tracked in `docs/todo.md` Known Issues). A lead cannot reach
`asset_gen` without a working `research` stage first, so even after the
asset_gen handoff work is done, new leads still can't be processed end-to-end
until `research` has a working, zero-cost inference backend.

Tebello had drafted (but never built) a pipeline diagram routing the research
stage through **local Ollama** — `qwen3:8b` for generation and
`nomic-embed-text` for embeddings — instead of OpenRouter. Grep confirms zero
references to `ollama`/`qwen`/`nomic`/`embed`/`similarity`/`search` anywhere in
the codebase today. Ollama is not installed on this machine (no binary on PATH,
nothing listening on `localhost:11434`). Tebello has now confirmed he wants this
folded into the current build effort as a second, parallel cost-elimination
track: **headless Claude Code for `asset_gen`, local Ollama for `research`.**
Combined, the pipeline then runs end-to-end at $0 marginal cost.

### Is `nomic-embed-text` (embeddings) actually needed? No — scoped out.

This was investigated directly, not assumed:

- `ResearchResult` (`research/schema.py`) carries only `lead_id`, `summary`
  (a string), `raw_data` (a dict), and `researched_at`. There is no vector,
  embedding, or similarity field, and nothing downstream consumes one.
- The only consumer of research output is `asset_gen`, which uses
  `research.summary` as **plain text** in a prompt (per the handoff spec's
  §3.3 field audit). No semantic search, no RAG, no vector store, no
  nearest-neighbour retrieval exists anywhere in `src/`.
- Lead **deduplication** — the one place "similarity" might live — is done by
  string normalization (`normalize_company_name`/`find_duplicate` in
  `lead_import/db.py`), not embeddings. It is complete and needs no vectors.

`nomic-embed-text` therefore has **no current use case in this codebase.**
Building an embedding client now would be speculative infrastructure with no
consumer — exactly the "don't build what the codebase doesn't need yet" trap.
It is explicitly **out of scope**. If a real semantic-search / vector-dedup /
retrieval feature is proposed later, it gets its own spec and its own ADR, and
that is the point at which `nomic-embed-text` (or any embedding model) earns its
place. The prerequisites section below therefore does **not** ask Tebello to
pull `nomic-embed-text`.

## Decision

**1. Replace the OpenRouter call in `research/claude_summariser.py` with a local
Ollama HTTP call, using `qwen3:8b`.**

`summarise_lead()`'s existing `OFFLINE_MODE` short-circuit
(`if OFFLINE_MODE: return _stub_summary(...)`) stays **exactly as-is** — see
point 4. Only the non-offline branch changes: instead of
`return call_openrouter(prompt)` it calls a new `call_ollama(prompt)`.

**2. New module: `src/research/ollama_client.py`** (not `src/shared/`).

Placement follows the codebase's established precedent, which is consistent and
worth preserving:

- `shared/openrouter_client.py` lives in `shared/` **because it has two
  consumers** (`research` and `asset_gen`).
- `research/apify_client.py` lives in `research/` **because it has exactly one
  consumer** (research).

Ollama, under this decision, has exactly one consumer: the research summariser.
`asset_gen` goes to headless Claude Code, not Ollama. So Ollama matches the
`apify_client` case, not the `openrouter_client` case, and belongs in
`research/`. This also keeps the research stage's network dependency inside the
research module, consistent with the offline-first module-boundary rule. If a
second consumer ever appears (e.g. a future decision to run asset_gen or
email_draft through Ollama too), promoting the file to `shared/` is a trivial
move-and-reimport — cheap to do then, premature to do now.

The client mirrors `openrouter_client.py`'s shape:

- A module-level `RateLimiter` (`src/shared/rate_limiter.py`), acquired before
  the request, with env override `OLLAMA_RATE_LIMIT_PER_MIN` (default `120`).
  Note this is largely a safety valve — Ollama serializes generation locally and
  a slow local model will never approach 120/min — but it keeps the client's
  shape identical to the other three and guards against a runaway loop.
- A dedicated exception type. Two are defined: `OllamaError` (base, e.g. bad
  response shape / non-200) and `OllamaUnreachableError` (subclass, raised when
  the daemon can't be reached — connection refused or connect-timeout).
- **No API key.** Ollama is local; there is no `OPENROUTER_API_KEY` analogue.
  The `if not api_key: raise` guard from `openrouter_client.py` has no
  equivalent here and must not be copied in.
- **A reachability check matters more than auth.** The single most important
  failure mode is "Ollama isn't running." The client uses a short connect
  timeout so a missing daemon fails **fast and clearly** with
  `OllamaUnreachableError("Ollama not reachable at <url> — is it running? Start
  Ollama or set OFFLINE_MODE=true.")` rather than hanging, retrying forever, or
  silently returning garbage.
- Calls Ollama's native `POST {OLLAMA_BASE_URL}/api/generate` with
  `{"model": OLLAMA_MODEL, "prompt": prompt, "stream": false}` and returns the
  `response` field. (The OpenAI-compatible `/v1/chat/completions` endpoint is an
  equally valid target; `/api/generate` is chosen because it is Ollama's native,
  most stable surface and needs no message-array shaping for a single-prompt
  summarization task.) Implementation note for the executor: `qwen3:8b` is a
  hybrid "thinking" model — pass `"think": false` (or strip a `<think>...</think>`
  block) so the returned summary is clean prose, not visible reasoning. This is a
  behavioural detail to cover in the client's tests, not an architectural point.

**3. Config additions on `Settings` (`src/config.py`)**, following the exact
existing pattern (dataclass field + `os.environ.get` in `load_settings`):

- `OLLAMA_BASE_URL: str = "http://localhost:11434"` (env `OLLAMA_BASE_URL`)
- `OLLAMA_MODEL: str = "qwen3:8b"` (env `OLLAMA_MODEL`)

`.env.example` gets both as non-secret defaults (they are not secrets — same
reasoning as the existing non-secret settings; a local URL and a model name are
safe to commit as placeholders).

**4. `OFFLINE_MODE` behaviour — already correct, must be preserved, not added.**

`summarise_lead()` already branches on `OFFLINE_MODE` **before** any client call
and returns `_stub_summary(lead, raw_data)`. The unit `conftest.py` sets
`OFFLINE_MODE=true` as an autouse fixture, so the entire test suite already
never makes a real inference call from this function. The swap must keep that
guard byte-for-byte: the new `call_ollama` sits only in the `else` branch, so
**no test ever makes a real HTTP call to `localhost:11434`.** This matches how
Apify, OpenRouter, and Gmail all stub out — the offline branch lives in the
caller, the client stays a thin real-call wrapper. No new fixture is needed;
tests that exercise `call_ollama` directly mock `requests.post`, exactly as
`test`-side mocking is done for `openrouter_client`.

**5. Fallback behaviour — fail loudly, do NOT fall back to OpenRouter.**

If Ollama is unreachable, `summarise_lead()` raises `OllamaUnreachableError` and
lets it propagate. It does **not** silently fall back to `call_openrouter`.

Reasoning: OpenRouter is currently *also* broken (out of credits, HTTP 402). A
silent fallback would route from one dead backend to another dead backend and
surface as a confusing OpenRouter 402 — hiding the real, actionable cause
("Ollama isn't running / the model isn't pulled"). A clear, specific
"Ollama not reachable" error tells Tebello exactly what to fix. Even if
OpenRouter credits were topped up later, an *implicit* fallback would silently
resume paid inference — the exact cost this change exists to eliminate — with no
signal that it happened. If a deliberate paid-fallback is ever wanted, it should
be an explicit, logged, opt-in setting proposed in its own change, never a
silent default. Fail loud is the correct default here.

**6. No schema change → no migration file required.**

`ResearchResult.summary` stays a `str`; the `leads` SQLite table is untouched;
`VALID_TRANSITIONS` is untouched. Only the inference backend that *produces* the
string changes. This ADR therefore does not trigger the "no schema changes
without a migration file" hard rule — there is no schema change to migrate.
(Called out explicitly so the absence of a migration file is a verified
decision, not an oversight.)

## Consequences

- The research stage runs at $0 marginal cost on local hardware once Ollama is
  installed and `qwen3:8b` is pulled. Combined with the asset_gen headless-Claude
  track (ADR-003), the full pipeline runs end-to-end at $0.
- A new **local runtime dependency** is introduced: the research stage now
  requires the Ollama daemon running and `qwen3:8b` pulled on whatever machine
  runs a real (non-offline) batch. This cannot be verified at import time; it
  surfaces as a clear `OllamaUnreachableError` at call time. This is analogous to
  the `claude` CLI dependency the asset_gen track introduces — both are local
  desktop prerequisites, not pip-installable, not CI-verifiable.
- Summary quality/characteristics change: `qwen3:8b` is a smaller local model
  than `claude-sonnet` via OpenRouter. Output may be less polished. This is an
  acceptable trade for $0 + unblocking the pipeline; it is downstream of the
  human approval gate anyway (the human reviews the *asset*, and the summary only
  ever feeds an asset prompt), so a weaker summary cannot reach a prospect
  unreviewed.
- `research/claude_summariser.py` keeps its filename despite no longer calling
  Claude. Renaming it (e.g. to `summariser.py`) is churn that breaks
  `research/pipeline.py`'s import and touches unrelated tests; the public
  function `summarise_lead()` is already backend-agnostic in name. The naming
  drift is noted here and left as an optional, separately-scoped cleanup — not
  bundled into this change.
- OpenRouter is fully removed from the research path. After this lands,
  `openrouter_client.py` has a single remaining reference point in the codebase
  only if the asset_gen handoff has *not* yet landed; once both tracks land,
  `call_openrouter` has no live caller and could itself be retired in a future
  cleanup (out of scope; flagged).
- The `nomic-embed-text` / embeddings idea from the draft diagram is recorded as
  **deliberately deferred**, not forgotten — future semantic-search/vector work
  starts from this ADR's scoping note.

## Alternatives considered

- **A. Top up OpenRouter credits, change nothing.** Rejected: recurring
  per-token cost is exactly what this effort eliminates, and it leaves the
  pipeline dependent on a paid balance that can hit 402 again mid-batch. Ollama
  is a one-time local install with no ongoing cost.
- **B. Route research through headless Claude Code too** (same mechanism as the
  asset_gen track), skipping Ollama entirely. Reasonable and would give higher
  summary quality, but: (i) it consumes the Claude subscription's shared rate
  pool for a high-volume, low-stakes step (one summarization per lead), whereas
  Ollama offloads that entirely to local hardware; (ii) Tebello explicitly asked
  for the two-track split (headless Claude for asset_gen, local Ollama for
  research). Deferred rather than dismissed — if local hardware proves too slow
  for `qwen3:8b`, falling back to the headless-Claude mechanism for research is
  the natural next option and would reuse the asset_gen track's runner.
- **C. Build the full draft diagram now, including `nomic-embed-text` embeddings
  and a vector store.** Rejected: no consumer exists (see Context). Speculative
  infrastructure. Deferred to a future ADR when a real retrieval feature is
  specified.
- **D. Put `ollama_client.py` in `src/shared/`** for symmetry with
  `openrouter_client.py`. Rejected: `shared/` placement is earned by having
  multiple consumers (openrouter has two); a single-consumer client belongs in
  its consumer's module, per the `apify_client.py` precedent. Promote later if a
  second consumer appears.
- **E. Silent fallback to OpenRouter when Ollama is down.** Rejected — see
  Decision point 5. Falling back to a currently-broken, paid backend is a worse
  failure mode than a clear local error.
