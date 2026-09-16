## 2026-09-01 — Headless/scheduled `claude -p` has no browser tool unless explicitly wired up; the mode degrades quietly rather than failing
**Source:** session (ai-product-factory hub) — setting up a Windows Task Scheduler job to run `career-ops`'s `/career-ops scan` + `pipeline` headlessly via `claude -p "prompt" --allowedTools ...`
**Status:** active

`career-ops`'s scan mode has explicit levels: Level 0/2 are zero-token local
parsers/ATS APIs; Level 1 (direct Playwright) and Level 3 (WebSearch discovery)
require verifying every hit's liveness through the interactive browser tool
before it's trusted. A headless `claude -p` invocation has no MCP browser
server attached by default — only whatever's named in `--allowedTools`
(`Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch` here). The agent correctly
recognized it couldn't complete the Level-3 liveness check and **silently
skipped that whole level** rather than erroring — the run still exited 0,
still produced a clean summary, and only mentioned the skip in prose
("Playwright wasn't available this session, so Level 1 and Level 3 didn't
run"). Nothing about the task's exit code or log structure flagged this as
degraded.

The generalizable shape: **a headless/scheduled Claude Code session that
depends on a mode's browser-verification step will quietly narrow to a
cheaper path instead of failing loudly**, because the mode's own conservative
design (don't trust an unverified hit) reads, from the outside, identical to
"nothing new was found today." Anyone wiring up unattended `claude -p`
automation for a mode that has a Playwright/browser-tool step should either
(a) attach a browser MCP server to the headless invocation if the mode truly
needs to run unattended end-to-end, or (b) explicitly scope the automation to
the tool-independent levels only (as done here — daily automation kept to
pipeline hygiene/re-evaluation; real new-lead discovery stayed a manual,
interactive `/career-ops scan`) and say so in the automation's own docs, so a
future session doesn't mistake "0 new" for "checked thoroughly, found none."

## 2026-08-21 — `claude-in-chrome`: stale refs, native selects, and blank screenshots in repeated-form flows
**Source:** session (ai-product-factory hub) — live PNet/Careers24/LinkedIn job-alert and profile automation for TebelloReborn, ~15 repeated "click Add → fill → Save" cycles across 2 real sites
**Status:** active

Four `claude-in-chrome` tool behaviors bit a session that repeatedly filled the same one-item
form pattern (add a job alert, add a skill tag, add a work-experience entry):

1. **A `find()`/`read_page()` ref goes stale the moment the form it points into re-renders**
   (e.g. an Enter-to-add collapses the form back to a static list) — even reusing the *same*
   ref within one batch call silently does nothing on the second use, no error. A later
   `find()` can return a ref with the identical numeric ID, which is misleading: same ID does
   not mean same live binding. **Re-find immediately before every click that opens/reopens a
   repeating form — never reuse a ref across an open→submit→reopen cycle.**
2. **Native `<select>` elements don't reliably take click+type.** Sometimes the browser's
   native type-ahead jump happens to match what was typed, sometimes the field silently stays
   unset — no visible difference between the two until a `get_page_text` check. `form_input(ref,
   value)` with the exact visible option text was 100% reliable across every dropdown tested
   (dates, sectors, contract types, provinces). **Default to `form_input` for every `<select>`,
   never click+type.**
3. **`computer:screenshot` can return a fully blank image, or `CDP sendCommand
   "Page.captureScreenshot" timed out`, with no other symptom** — happened repeatedly right
   after `scroll_to(ref)`. `get_page_text` (reads the DOM directly, doesn't rasterize) worked
   every time as a fallback. **Treat a blank/failed screenshot as "unknown," not "empty page" —
   confirm via `get_page_text` before concluding a field is empty or an action didn't land.**
4. **A Save spinner can keep animating client-side after the server-side save already
   succeeded.** One modal spun 15+ seconds with no resolution; `get_page_text` in a parallel
   check showed the underlying data had already updated behind the still-spinning overlay.
   Reloading the page (not re-clicking Save, not waiting indefinitely) both cleared the stuck
   overlay and confirmed the save had landed. Re-clicking Save on an already-succeeded form
   risks a duplicate submission if the site's own idempotency isn't guaranteed.

Generalisable: none of these are bugs in the site being automated — they're `claude-in-chrome`
tool/interaction quirks that surface because a scripted agent chains actions faster and more
mechanically than a human naturally re-orients between them. Same underlying shape as this
file's other entries: verify the actual value/state a layer produced, don't trust that a
call returning without an error means the intended effect happened. Full write-up:
`ai-product-factory/shared-memory/learnings/process/claude-in-chrome-stale-refs-and-native-selects.md`.

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

## 2026-09-14 — A multi-line `Edit` `new_string` silently breaks a markdown table row it targets
**Source:** session (ai-product-factory hub) — `docs/specs/2026-09-11-dashboard-realignment.md`, pass-6-to-pass-7 fix session
**Status:** active

A markdown table row meant to stay one physical line (dense per-task cells in
a `| ... |` row) silently split across 23 physical lines after an `Edit` call
whose `new_string` argument contained literal newlines — the kind that come
from composing a multi-paragraph replacement directly rather than writing the
whole block as one continuous line. Nothing in the tool call failed or
warned: the edit applied exactly as written, producing syntactically valid
markdown text that no longer rendered as a table row past the first embedded
newline (everything after it became bare paragraph lines sitting between two
`|`-delimited rows).

**Nothing about the break was visible without checking line length directly.**
File line count stayed plausible, `grep` for content still found every phrase
(it matches across lines same as within one), and a normal `Read` of the
region showed correct *content*, just no longer laid out as a table — easy to
skim past when reviewing for words rather than row structure.

**Caught by:** `awk 'NR==<line>{print NR": "length($0)}'` across the suspect
region — a genuine one-physical-line table row with dense cells runs
thousands of characters; a handful of ~70-character lines immediately after
it is the signature of a broken row, not a formatting choice.

**Fix:** compose table-cell replacement text as one continuous string with no
literal newlines, even when drafting feels more natural with paragraph
breaks. After editing inside a markdown table row, spot-check integrity with
a line-length scan (`awk '/^\| [0-9#-]/{print NR": len="length($0)}'`) rather
than assuming a successful `Edit` call preserved row structure.

Single instance so far — not yet promoted past a documented habit.
