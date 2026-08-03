---
name: safe-office-file-read
description: Use before programmatically opening an Excel/Office file (.xlsx, .xlsm, .docx, .csv-from-Excel, etc.) that a human user might currently have open on their machine. Shadow-copies the file to a temp location first and reads the copy, avoiding a PermissionError or file-lock crash. Trigger whenever a script, pipeline, or report generator reads a shared or user-facing spreadsheet/document as an input. Skip for files your own process exclusively owns and writes (e.g. a temp output file nothing else touches) — the overhead only pays for itself on files a human might realistically have open.
---

## Why this exists

Office applications (Excel especially) take an exclusive or partial lock on
a file while it's open, even just for viewing. A script that opens that
same path directly for reading will intermittently fail with a
`PermissionError` (Windows) or, in some library/OS combinations, silently
succeed but read a stale or partially-written state instead of erroring —
which is worse, because it looks like success. This is a recurring failure
mode for any pipeline, importer, or report generator whose input file is
also a file a human routinely opens to check or edit by hand — the failure
is intermittent and timing-dependent, so it's easy to dismiss as a fluke the
first few times it's seen.

## Steps

1. **Never open the original source path directly for read** when it's
   plausible a human has it open — this includes shared network files,
   manually-maintained workbooks, or any file mentioned in documentation as
   something a person edits.

2. **Copy the file to a temp location before reading.** In Python, this is
   typically `shutil.copy2(source_path, temp_path)` into a
   `tempfile`-managed location (preserves metadata, doesn't require the
   source to be free of a read-lock — copying a file that's merely open for
   viewing/editing generally succeeds even when direct read access would
   intermittently fail).

3. **Read from the temp copy, not the original**, for every subsequent
   operation on that data.

4. **Clean up the temp copy afterward** — either explicitly or by relying on
   `tempfile`'s own cleanup semantics, but be deliberate about which one is
   in effect rather than leaving temp files to accumulate silently.

5. **Distinguish a genuinely-locked source (e.g. mid-save) from a
   missing-file error.** If even the *copy* step fails, that's a different,
   rarer condition — surface an actionable message ("this file is being
   written right now — retry in a moment") rather than treating it the same
   as "file not found."

6. **Don't apply this to files your own process fully owns.** The
   protection is for inputs a human or another system might be touching
   concurrently — adding it to purely-internal, self-generated files is
   unnecessary overhead with no corresponding risk.

## Evidence this pattern recurs

Confirmed independently across multiple unrelated data-pipeline and
report-generation projects, each reading manually-maintained or shared
spreadsheet inputs — one project's own troubleshooting docs even describe
"close the file before running" as a manual fallback in the exact places
this technique would have made that instruction unnecessary.
