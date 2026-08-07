# session-tooling

Shell and tool gotchas that bite sessions working in this hub, regardless of
which project they're in. Machine-specific facts live in `operations-hub.md` /
`pappa-t.md`; this file is about the tooling itself.

## 2026-08-07 — `git commit -m` with a PowerShell here-string splits into pathspecs
**Source:** session (this machine), hub commit `5904833`
**Status:** active

Passing a PowerShell here-string that contains double quotes to `git commit -m`
fails with a wall of `error: pathspec '<word>' did not match any file(s)`. The
message gets split on whitespace and each fragment is treated as a pathspec.

Cause: PowerShell 5.1 re-quotes arguments on their way to a native executable,
and an embedded `"` closes the argument early. The here-string being
single-quoted (`@'…'@`, literal, no interpolation) does **not** protect against
this — the breakage happens at the native-command argument boundary, after
PowerShell has already resolved the string.

**Reliable form — write the message to a file and use `-F`:**

```
git -C <repo> commit -F <path-to-message-file>
```

Write the file with the `Write` tool (UTF-8, no BOM), not `Set-Content`, whose
PS 5.1 default is the system ANSI codepage and will mangle em dashes and arrows
in commit messages.

This matters here because every hub commit goes through the PowerShell tool, and
this hub's commit messages routinely quote file contents and error strings.

## 2026-08-07 — Appending to a docs file: use Python, not `Add-Content`
**Source:** session (this machine), appending the 2026-08-07 `session-log.md` entry
**Status:** active

`docs/session-log.md` and `docs/todo.md` are full of em dashes, arrows and box
characters. `Add-Content`/`Out-File` under PS 5.1 have inconsistent encoding
defaults and can corrupt those or introduce a stray BOM mid-file.

Appending via a short Python script (`io.open(..., encoding="utf-8",
newline="")`) is deterministic and lets the same script verify the result —
e.g. printing the last few `## ` headings to confirm the new entry actually
landed last, which `/session-end` Step 3 requires checking explicitly.
