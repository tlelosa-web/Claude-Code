## 2026-07-30 — Where Claude Code sessions actually live, and what moves them
**Source:** bensimon.dev, "Your sessions are in a folder called projects, and it
has nothing to do with Projects" (2026-07-27)
**Status:** active

**Path and encoding.** Claude Code writes one plaintext JSONL file per session:
`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`. The encoding takes the
absolute working directory and replaces every non-alphanumeric character with a
hyphen (`/Users/ben/Source/myrepo` → `-Users-ben-Source-myrepo`) — lossy, not
reversible. This `projects/` folder is unrelated to claude.ai's "Projects"
feature (knowledge-base-grouped chats); same word, different product, different
storage.

**Two different keys, one tree.** Transcripts key on the **working directory**.
Auto memory (Claude's self-written notes) lives in the same `projects/` tree but
keys on the **git repository**. Consequence for worktrees: three worktrees of one
repo produce three separate transcript folders but share one memory folder — all
sitting side by side with nothing in the folder names indicating which addressing
scheme applies to which.

**Sidecars and siblings.** `<session-id>/subagents/` holds subagent conversations,
`<session-id>/tool-results/` holds tool outputs too large to inline. Elsewhere in
`~/.claude/`: `file-history/<session>/` (pre-edit snapshots for `/rewind`, capped
at 100 checkpoints), plus `plans/`, `debug/`, `session-env/`, `tasks/`. Two more
worth knowing: `~/.claude.json` (app state, auth state, personal MCP config) and
`~/.claude/history.jsonl` (every prompt ever typed, with its project path, for
up-arrow recall).

**What each entry point does to the file:**
- `--continue` / `--resume` — reopens the same session ID, appends to the same file.
- `/branch` / `--fork-session` — new session ID, history copied in, IDs rewritten,
  original untouched. Gotcha: per-session-approved permissions do *not* carry into
  the branch.
- `/rewind` — docs say it forks the conversation, but there's an open GitHub issue
  (anthropics/claude-code#55347) reporting it mutates the session in place instead
  and the original disappears from the picker. Behavior unconfirmed as of this
  writing — branch first if you need the old path preserved for certain.
- `/cd`, or entering a Claude-created worktree — **relocates** the transcript file
  to the new directory's store. This is correct/documented behavior but easy to
  forget mid-session.
- `--add-dir` — moves nothing; only widens what the session picker can search.
  In the picker itself: `Ctrl+W` widens to every worktree of the repo, `Ctrl+A` to
  every project on the machine.
- `-p --no-session-persistence` — writes no transcript at all, not resumable.
- `CLAUDE_CODE_SKIP_PROMPT_HISTORY=1` — skips both the transcript and prompt history.

**Security note (from Anthropic's own docs, quoted in the source article):**
transcripts and history are **not encrypted at rest** — OS file permissions are
the only protection. Anything the agent reads (a `.env` file, a command that
echoes a credential) gets written verbatim into
`projects/<project>/<session>.jsonl`, retained 30 days by default. Documented
mitigations: lower `cleanupPeriodDays`, set `CLAUDE_CODE_SKIP_PROMPT_HISTORY`, and
(the only one that addresses the actual cause) deny permission rules for reading
credential files.

**Retention gotcha.** `cleanupPeriodDays` (default 30, minimum 1, `0` is a
validation error not "off") sweeps transcripts, subagent transcripts,
tool-results, file-history, plans, caches, debug — but **not**
`~/.claude/history.jsonl`, which is never swept by age. `claude project purge`
is the only command that removes a project's transcripts, auto memory,
per-session data, *and* the matching lines in `history.jsonl` together; plain
`rm -rf` misses the history-index lines.

**Cowork storage** depends on execution mode: remote (the default since July
2026, after a disclosed local-mode sandbox escape) saves sessions/files to your
Claude account in a per-session sandbox destroyed at session end — nothing lands
in `~/.claude/`. Local mode runs the agent loop on-device with code executing in
a local VM; Anthropic documents the architecture but does not publish where
local-mode session data is written. Governance note: Cowork activity is excluded
from audit logs, the Compliance API, and data exports — Team/Enterprise gets a
separate OpenTelemetry stream (prompts + tool invocations) but that's operational
telemetry, not audit evidence.

**Practical takeaways applied to this hub:** don't parse session JSONL directly
(format is internal, changes between versions — use `/export`,
`--output-format json`, or the `transcript_path` passed to hooks); if asked to
locate a specific past session, give the exact path shape above rather than
guessing; if asked to clean up session data, name `history.jsonl` explicitly and
prefer `claude project purge` over manual deletion.
