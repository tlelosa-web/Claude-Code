## Task: Sales Order Job Numbers
**Domain:** Software
**Goal:** Capture job number(s) during Sales Order upload and reference them on all Sales Order, Works Order, and Picking List documentation.
**Inputs:** Parsed Sales Order PDF data, optional manually entered job number(s), existing Sales Order records.
**Outputs:** Saved job number text on the Sales Order and display references such as `FM4047-FM4055 - SO4556`.
**Constraints:** Preserve multiple job numbers and ranges exactly enough for production use; support existing SQLite databases with a lightweight schema upgrade; do not break Sales Orders without job numbers.
**Acceptance Criteria:** Upload review includes a Job Number(s) field, saved Sales Orders retain it, BOM/WO/PL pages and print documents show the combined job/SO reference, and tests pass.
**Out of Scope:** Separate job-number table, automatic allocation of new job numbers.
