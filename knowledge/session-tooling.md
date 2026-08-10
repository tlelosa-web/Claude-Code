## 2026-08-10 — PowerShell's `..` silently turns a git revision range into a number range
**Source:** session — auditing a stranded branch before deleting it
**Status:** active

`git rev-list --count $b..main` does not do what it looks like. In PowerShell `..` is the
**range operator**, so `$b..main` is evaluated *before* git sees it: PowerShell tries to build
a sequence, `main` is an unset variable, and git is handed an argument that has nothing to do
with the revision range that was written.

The damage is that it **succeeds**. It returned `0` — "the branch has nothing `main` lacks" —
which is a plausible, useful-looking answer and the one that gets acted on. The real value was
**625**. Deleting a branch on the strength of that `0` is a real possibility, and the same
shape applies to any `A..B` git range built with a PowerShell variable: `git log`, `git diff`,
`git rev-list`.

Two ways out, both cheap:

- **Quote the whole range as one string:** `git rev-list --count "main..$b"`. The quotes stop
  PowerShell parsing `..` and pass the literal spec through.
- **Prefer the exit-code form for the question actually being asked.**
  `git merge-base --is-ancestor <branch> main` answers "is this branch fully merged?" directly,
  with no range to mis-parse and no count to misread.

Generalisable: this is the third entry in this file where a Windows shell **succeeded** with
the wrong value instead of failing (see the `Get-Content -Raw` mojibake and the `git commit -m`
here-string entries). The recurring shape is that the shell reinterprets a string before the
tool sees it. Where a shell can rewrite an argument, verify the *value* the tool received, not
just that the command exited 0.

## 2026-08-09 — A checksum file written by Python on Windows fails `sha256sum -c` on every line
**Source:** session — staging the Fan Movement handover folder
**Status:** active

`open(path, "w")` on Windows translates `\n` to `\r\n`. A `CHECKSUMS.txt` written that way
looks perfect — correct hashes, correct paths, opens fine in any editor — and then:

```
sha256sum: '04-credentials/… .env'$'\r': No such file or directory
sha256sum: WARNING: 915 listed files could not be read
```

`sha256sum -c` splits each line on the two-space separator and takes **the rest of the line**
as the filename, trailing `\r` included. Every entry fails, so the failure is total rather
than partial — which reads like the *data* is corrupt, not the manifest. Fix is one keyword:

```python
open(path, "w", encoding="utf-8", newline="")   # newline="" is load-bearing
```

**The reusable part is how it was found.** The manifest documented `sha256sum -c CHECKSUMS.txt`
as the verification command, so the command got run — and failed on all 915 files. A Python-side
spot-check had already "passed" the same file minutes earlier, because `splitlines()` strips
`\r` and hid the defect completely. **A verification artifact is only verified by the tool it
tells someone else to use**; checking it with a different tool tests the wrong thing. Same
family as the PowerShell encoding traps below: text-mode round-trips on Windows change bytes
nobody asked them to change.

## 2026-08-08 — Two tool-call shapes that fail silently or confusingly
**Source:** session (this machine, hub `/continue` → TebelloReborn Phase E)
**Status:** active

**1. Never rewrite a source file with `Get-Content -Raw | Set-Content` in Windows
PowerShell 5.1 — it corrupts every non-ASCII character.** Used it to rename a function
across two Python files:

```powershell
(Get-Content src\x.py -Raw) -replace 'old_name','new_name' | Set-Content src\x.py -Encoding utf8
```

Every em-dash in every docstring came back as `â€"`. `Get-Content` decodes a UTF-8 file with
**no BOM** using the system ANSI codepage, so the mojibake is created on *read*; the
`-Encoding utf8` on the write is correct and irrelevant. **It fails silently** — the rename
worked, the module imported, the full test suite passed, and only a deliberate
`'â€' in text` check caught it. Recovery was `git checkout --` on both files and redoing the
rename with the Edit tool.
Use the Edit tool (or Python's `read_text(encoding='utf-8')`) for any file rewrite. This is
the same class as the existing entry about `Add-Content`, and generalises past appending:
**any** PowerShell round-trip of a source file is unsafe here.

**2. Playwright's `on()` rejects a builtin method as a handler.**
`context.on("page", popups.append)` raises
`AttributeError: 'builtin_function_or_method' object has no attribute '_pw_impl_instance_'` —
Playwright stores an attribute on the handler object, which builtins don't accept. Wrap it in
a plain `def`:

```python
def _on_page(new_page):
    popups.append(new_page)
context.on("page", _on_page)
```

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
