---
name: reuse-existing-ui-primitive
description: Use before adding a new modal, dropdown, dialog, tooltip, or other interactive overlay component to a frontend codebase. Checks whether the project's existing design system/component library already has one, and reuses it instead of hand-rolling a new implementation. Trigger whenever a task calls for a popup, dropdown, confirmation dialog, or similar interactive overlay. Skip if the codebase genuinely has no design system/component library yet and this is the first such component being introduced.
---

## Why this exists

Hand-rolled overlay components (a custom `<div>` dropdown, a manually
toggled modal) tend to reinvent problems a design system's existing
primitive already solved — z-index stacking, focus trapping, outside-click
dismissal, keyboard/Escape handling, accessibility. This isn't
hypothetical: a hand-rolled filtered dropdown was replaced by an
already-vendored-but-unused library specifically because the hand-rolled
version caused a transparency bug traced to manual z-index handling, in the
same codebase that had *already* standardized on a shared modal primitive
for other popups — the dropdown was simply built before anyone checked
what already existed. A separate project on a completely different stack
independently reached the same conclusion for dialogs: use the design
system's primitive rather than a custom implementation.

## Steps

1. **Before writing new modal/dropdown/dialog/tooltip code, check what the
   project already uses for this class of UI.** Grep for existing
   modal/dialog imports, check the package manifest for a component library
   (shadcn/ui, Radix, Headless UI, Bootstrap, MUI, etc.), or look for an
   established in-house pattern (a vanilla-JS/Alpine.js modal helper used
   elsewhere in the codebase).

2. **If a primitive already exists and is used elsewhere for a similar
   purpose, use it** — even if that means installing an additional variant
   of an already-installed library (e.g. adding a `dialog` component when
   `button` is already there) rather than writing custom show/hide/z-index
   logic from scratch.

3. **If no primitive exists yet at all**, that's a legitimate case to write
   one — but flag it explicitly as introducing a new shared pattern, so it
   becomes the thing future work reuses rather than one of several
   competing hand-rolled implementations.

4. **Watch for symptoms of a skipped-primitive during review**: manual
   `z-index` tweaking, direct DOM `style.display` toggling, missing
   outside-click/Escape-key handling. These are signals that an existing
   primitive was bypassed rather than reused.

## Evidence this pattern recurs

Confirmed independently on two different stacks — a vanilla-JS/Alpine.js
codebase and a React/component-library codebase — both converging on
"check for what's already there first" after a hand-rolled version caused
a real, traceable bug.
