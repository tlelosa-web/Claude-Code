# Code Conventions

## General

- Prefer small, focused edits.
- Preserve source data.
- Use relative paths inside project scripts where existing scripts already do so.
- Keep secrets out of committed or shared files.

## Python

- Use explicit functions and clear names.
- Add type hints when touching non-trivial logic.
- Use shadow copies before reading live business files such as spreadsheets or databases.
- Write large debug output to files under the relevant archive/debug folder.

## Web Apps

- Follow the local framework conventions in the app being edited.
- Run the app's existing typecheck, lint, and test commands when available.
