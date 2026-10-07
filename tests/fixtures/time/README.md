# Fixtures recorded for feature 005 (task T001)

Recorded 2026-10-07 against the sandbox (OpenProject 17.9.1, `jtauschl/openproject-ce-mcp` v0.4.1). Scratch work package 115 (`VERIFY-005 ...`) in project `speckit-sandbox`, one time entry (id 1, 30 minutes, activity "Development", 2026-10-07); the maintainer removes it by hand. Secret-free: no host, no URL, no token.

| File | What it shows |
|---|---|
| `list-time-entry-activities.json` | `list_time_entry_activities()` shape: array of `{id, name, position, is_default, projects}` |
| `create-time-entry-confirm.json` | `create_time_entry(..., confirm=true)` result: id field is top-level `time_entry_id` |
| `create-time-entry-unknown-activity-error.json` | an unknown/typo'd `activity` name fails with the generic tool error, not a structured `validation_errors` rejection — commands must validate the name against the activity list themselves before calling the tool |

Not recorded: a project with the time-tracking module disabled; logging time on a work package without permission.
