---
name: verify-ui-cardinality-against-output
description: Use when building or fixing a UI that represents a "one-to-many" or "N-of-something" relationship in a form or list (e.g. multiple line items, repeated sub-records, a quantity of an item) tied to a generated document, print output, or export. Confirms the intended UI shape against what the actual output/print/export logic does before committing to a UI structure. Trigger whenever a "one row of data = one UI element" assumption is being made for a repeatable/quantity-based field. Skip for UI with no corresponding generated document/export, or where the data model's cardinality is already unambiguous and confirmed.
---

## Why this exists

It's easy to assume a UI needs one full form panel (or one table row) per
underlying repeated item, when the actual intended design is a single field
representing a *count*, with the repetition handled entirely server-side or
inside the output generator. This is not a hypothetical failure mode: a UI
feature went through two wrong shapes in the same session — first a
duplicated full form panel per item, then a compact table with one row per
item — before the real intent was clarified as a single Quantity field. The
PDF/print output generator had been producing the correct one-row-per-item
structure the entire time; only the UI's assumption about what it needed to
feed that generator was wrong.

## Steps

1. **Before building UI for a repeated/quantity-based field, check how the
   existing output generator (PDF, print template, export) actually
   represents that repetition.** It may already assume a single input value
   (a count) rather than N discrete UI-supplied entries.

2. **If the output generator expects a count/quantity rather than N
   distinct entries, don't build N-of-something UI** (duplicated panels, one
   row per item) — build the simpler single-field UI and let the existing
   generation logic handle the repetition.

3. **If genuinely unsure whether the intended UI is "N distinct editable
   entries" vs. "one count," ask before building either** — this is a
   design/product judgment call, not something safe to infer from the data
   shape alone.

4. **If a first attempt at this kind of UI doesn't feel right, treat that as
   a signal to re-check the actual output logic and the original intent**,
   rather than iterating straight to a second UI shape without revisiting
   the assumption.

## Evidence this pattern recurs

Confirmed in one project, where two separate wrong UI shapes were built and
discarded within the same session before the actual intent was clarified —
the output/print logic had been correct throughout and was never the
problem.
