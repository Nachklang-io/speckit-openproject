# Discovery fixtures

Responses of the OpenProject MCP server that `speckit.openproject.discover-fields` relies on. They guard the response shape (`tests/test_discovery_fixtures.py`); the prompt itself is verified by the scenarios in `docs/TESTING.md`.

| File | Origin |
|---|---|
| `statuses.json` | recorded: `list_statuses`, sandbox, 2026-10-05 (OpenProject 17.9.1) |
| `context-task-plain.json` | recorded: `get_project_work_package_context(project, type=Task)`, sandbox, 2026-10-05; `S6 Test Field` was optional at that time |
| `context-task-mandatory.json` | **derived**: copy of `context-task-plain.json` with `customField1` set to `required: true` in `fields` and `custom_fields` |

The recorded files were reconstructed from the server responses; ids, names and flags are unchanged. Fixtures must not contain hosts, tokens or instance URLs (hrefs are paths only).
