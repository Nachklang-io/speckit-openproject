# Fixtures for status sync (feature 003)

Recorded on 2026-10-06 from the sandbox (OpenProject 17.9.1, MCP server `jtauschl/openproject-ce-mcp` 0.4.1), reduced to the fields the prompt relies on; hrefs are paths only, no host, no token.

| File | Source |
|---|---|
| `wp-assigned.json`, `wp-unassigned.json` | `get_work_package` / `create_work_package` result shape of work packages 92 and 93: `status` is the status **name** (string), `assignee` is the display name or `null`, `lock_version` is present |
| `preview-allowed.json` | `update_work_package(work_package_id, status="Closed")` without `confirm`: `state: preview`, `ready: true`; note `percentageDone: 100` (the server fills it when a closed status is set) |
| `decision-table.json` | derived, not recorded: cases of research R1 for `tests/test_sync_decision.py` |

Not recorded yet: `preview-forbidden.json` (needs the restricted workflow of task T001b). Observed without a fixture: `update_work_package` with an unknown status name fails with the generic tool error `Error executing tool update_work_package` (no `validation_errors`), so the prompt treats a tool error on the preview as `blocked`.

Fixtures must stay free of hosts, tokens and instance URLs (`tests/test_prompt_sync.py` scans this directory).
