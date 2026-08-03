---
name: sweep-shared-ui-convention-fix
description: Use when fixing a bug in a UI convention that's shared across multiple templates, pages, or components — a status badge color, a date/number format, a shared icon or label. Ensures the fix is applied everywhere the convention renders, not just at the one reported instance. Trigger whenever a fix touches a badge, formatter, or other small shared display convention likely duplicated across list/detail/dashboard/print views. Skip for a genuinely one-off, single-location UI bug with no shared convention involved.
---

## Why this exists

Small display conventions — a status color, a date format, a label — tend
to get copy-pasted across every page that renders that field, rather than
centralized in one component or helper. A fix scoped only to the page where
the bug was reported leaves every other render site still broken. This has
happened concretely twice in the same codebase: a status-badge color fix
had to be explicitly re-scoped as "affects every usage app-wide" once
someone checked, and a date-format fix had to sweep every place a
particular date field rendered as text across list, detail, dashboard, and
print templates — which had silently drifted into an inconsistent mix of
raw ISO strings and formatted dates before the sweep.

## Steps

1. **Before considering a shared-convention UI fix complete, grep for every
   other place the same convention renders** — the same CSS class name, the
   same formatting helper/filter/function, or the same field name being
   displayed as text.

2. **Check list pages, detail pages, dashboards, and print/export templates
   separately.** These are the most common categories where the same field
   renders through a *different* code path — a print template especially
   often re-implements formatting rather than reusing the helper the live
   page uses.

3. **If the convention is duplicated (not centralized in one shared
   component/helper), fix every instance found**, and flag the duplication
   itself — a future fix will hit the same gap again if the convention
   isn't centralized in the meantime.

4. **If it is centralized, confirm the fix actually lives in the shared
   component/helper** and isn't accidentally being overridden by a
   page-specific style or format applied on top of it.

## Evidence this pattern recurs

Confirmed in one project across two separate incidents — a badge-color
convention and a date-format convention — each requiring an explicit sweep
across list/detail/dashboard/print templates that had drifted out of sync
without anyone noticing until the sweep was done.
