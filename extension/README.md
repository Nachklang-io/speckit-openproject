# spec-kit extension: openproject

Work in progress (version 0.0.2). Implemented: `speckit.openproject.discover-fields`. Planned: `sync-status`, `sync-docs`, `log-time` (see `../docs/ROADMAP.md`). Requires the `openproject` preset for `speckit.taskstoissues`.

## `discover-fields`

Reads the target project's types, statuses, priorities, versions and mandatory custom fields through an OpenProject MCP server and creates or updates `.specify/openproject/config.yml`, so that `speckit.taskstoissues` works without hand-editing.

```text
/speckit-openproject-discover-fields [project] [--dry-run]    # skills mode
/speckit.openproject.discover-fields [project] [--dry-run]    # command mode
```

Requires the MCP server `jtauschl/openproject-ce-mcp` (verified v0.4.1), configured as described in the preset README. The project is resolved from the argument, then `.specify/openproject/config.yml`, then `SPECKIT_OPENPROJECT_PROJECT`, then you are asked.

What a run does:

1. Reads types, statuses, priorities, versions and mandatory custom fields (read-only) and prints an overview.
2. Proposes the types for feature, phase and task (for example "Summary task" for phase, because a default instance has no "Phase" type) and the status names for `statuses.open`, `statuses.in_progress` and `statuses.done`, each with a reason. You accept or change items by number.
3. Asks for a value for every mandatory custom field of the used types. A field you leave empty is reported and the run ends as `incomplete`; no placeholder is invented.
4. Shows the changes as a numbered list and a diff. You approve `all`, `none` or a list of numbers. Only approved keys are changed; comments, key order and unknown keys stay as they are.
5. Writes through a temporary file and one move, so the file is either unchanged or fully written. `--dry-run` shows everything and writes nothing.

Run results: `complete`, `incomplete`, `no changes`, `dry run`, `stopped`. Re-running on an unchanged project and config reports `no changes` and does not touch the file.

Rules: it only reads from OpenProject, it never writes tokens, URLs or `.env` content, and it never deletes anything.

### Limitations and untested paths

- Interactive only; there is no non-interactive mode.
- Custom fields of type list: the chosen title is stored as a string; whether the server accepts that on creation is **untested**. Custom fields of type user, multi-select, hierarchy or formatted text cannot be stored in `required_custom_fields` and are reported.
- `available_versions` with real versions and the per-project list of enabled types are not yet verified against a live instance; see `docs/TESTING.md` for what was executed.
- Command mode (`/speckit.openproject.discover-fields`) is untested unless `docs/TESTING.md` says otherwise.
- It was not verified how spec-kit forms hook keys for extension commands, so this command has no hook check.
- The project must be readable by the server; if it reports `can_update` false the run warns that write commands will fail. The server's own allowlist cannot be inspected.
- Error text from the server is shown with URLs and host names replaced by `<redacted-host>`.
