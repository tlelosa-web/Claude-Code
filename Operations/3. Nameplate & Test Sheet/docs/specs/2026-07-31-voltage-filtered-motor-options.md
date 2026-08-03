# Spec: Filter Motor kW options by voltage as well as pole

**Date:** 2026-07-31
**Origin:** `docs/bugs/connection-lookup-no-manual-override.md`, suggested
fix approach item 2 (UX follow-up, optional once the override fallback fix
landed 2026-07-31, but avoids ever needing the override for the common
case).

## Problem

`_options_cached()` in `4_Scripts/backend/main.py` builds `motors_by_pole`
keyed only by pole, listing every kW value present in the motor performance
PDF for that pole count. It ignores voltage entirely, so the frontend Motor
kW dropdown (`FormFields.jsx`) offers kW values that have no STAR/DELTA rule
at the selected voltage (e.g. 5.5kW/4-pole is offered even at 525V, where
`DELTA_RULES_MAX[(525,4)] = 4.0` rules it out). Selecting one of these
combos previously hard-failed PDF generation; it's now rescued by the
override fallback, but the dropdown still steers users into a guaranteed
`suggest_connection()` failure before the override kicks in.

## Root cause confirmed

- `table` (from `motor_fla_lookup._load_motor_table()`) is keyed
  `(kw: float, pole: int) -> fla_value` — no voltage dimension exists in the
  motor PDF data itself.
- Voltage-validity has to come from `connection_lookup.py`'s rule tables
  (`STAR_RULES`, `DELTA_RULES_380_MIN`, `DELTA_RULES_MAX`), cross-referenced
  per `(voltage, pole, kw)` via the existing `suggest_connection()` function
  — no new rule logic needed, just reuse it as a filter.

## Fix

### Backend — `4_Scripts/backend/main.py`, `_options_cached()`

Change `motors_by_pole` from `{pole: [kw, ...]}` to a nested
`{pole: {voltage: [kw, ...]}}`, where each per-voltage kW list only includes
values for which `suggest_connection(voltage, pole, kw)` returns `"STAR"`
or `"DELTA"` (i.e. drops kW values with no rule at that voltage).

```python
for p in validated_poles:
    kws = sorted({float(kw) for (kw, pp) in table.keys() if int(pp) == int(p)})
    per_voltage: dict[str, list[str]] = {}
    for v in voltages:
        valid_kws = [k for k in kws if suggest_connection(v, p, k)[0] in ("STAR", "DELTA")]
        per_voltage[str(v)] = [_fmt_kw(k) for k in valid_kws]
    motors_by_pole[str(p)] = per_voltage
```

`suggest_connection` is already imported in `main.py` (line 72). No change
to the top-level `voltages`/`poles` lists — both are still driven from the
rule-table keys / motor-table intersection as before.

### Frontend — `4_Scripts/frontend/src/components/FormFields.jsx`

`motorsByPole[data.pole]` currently returns the flat kW list directly; it
now returns a per-voltage dict, so the lookup needs a second key:

```jsx
const motorsByPole = options.motors_by_pole || {};
const motorOptions = (motorsByPole[data.pole] || {})[data.voltage] || [];
```

No other consumer of `options.motors_by_pole` exists in the frontend
(confirmed via grep across `src/`).

## Explicitly out of scope

- Resetting `data.motor` when the filtered list changes underneath a
  previously-valid selection (e.g. user picks 5.5kW/4-pole, then switches
  voltage to 525V). This staleness risk is a **pre-existing gap** — the
  current pole-only filtering already has it (changing pole can already
  leave a stale `data.motor` not in the new list), and no reset-on-change
  logic exists for any field today. Not introduced by this change; not
  fixed by this change. Worth a separate UX pass if it becomes a live
  complaint.
- The two other bug-report follow-ups (`excel_source.py` datetime fix,
  dead endpoint decision) — separate items in `docs/todo.md`.

## Verification plan

1. Start `uvicorn main:app --reload`, hit `GET /api/options` (or whatever
   endpoint serves `_options_cached()`), confirm `motors_by_pole["4"]["525"]`
   excludes `5.5`/`7.5`/`9.2` (all above the 4.0kW DELTA ceiling at 525V/4P)
   while `motors_by_pole["4"]["380"]` still includes them.
2. Start the frontend dev server, select Pole=4, Voltage=525 in the live
   form, confirm the Motor kW dropdown only offers 1.5/2.2/... up to the
   4.0kW ceiling (whatever the actual PDF-sourced steps are at/below it) —
   not 5.5/7.5/9.2.
3. Switch Voltage to 380 with Pole still 4, confirm the dropdown now shows
   the full previous range again.
4. Generate a nameplate PDF for a valid in-range combo to confirm the
   payload contract (`options.motors_by_pole` shape change) didn't break
   anything downstream — `pdf_generator.py` never reads `motors_by_pole`
   directly (it's a UI-options-only structure, not part of
   `TestLinePayload`), so this is a sanity check, not an expected break.
