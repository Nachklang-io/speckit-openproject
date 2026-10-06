# spec-kit extension: openproject

Work in progress (version 0.0.3). Implemented: `speckit.openproject.discover-fields`, `speckit.openproject.sync-status`. Planned: `sync-docs`, `log-time` (see `../docs/ROADMAP.md`). Requires the `openproject` preset for `speckit.taskstoissues`.

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
4. Shows the changes as a numbered list and a diff. You approve `all`, `none` or a list of numbers. Only approved keys are changed; comments, key order and valid keys the command does not manage stay as they are. If the existing config is invalid (YAML or schema errors, keys unknown to the schema), all violations are listed and a rebuild is shown as a diff; the file changes only after you approve it.
5. Writes through a temporary file and one move, so the file is either unchanged or fully written. `--dry-run` shows everything and writes nothing.

Run results: `complete`, `incomplete`, `no changes`, `dry run`, `stopped`. Re-running on an unchanged project and config reports `no changes` and does not touch the file.

Rules: it only reads from OpenProject, it never writes tokens, URLs or `.env` content, and it never deletes anything.

### Limitations and untested paths

- Interactive only; there is no non-interactive mode.
- "Read only" is enforced by the prompt, not by the client: spec-kit does not install the `tools` frontmatter of an extension command in skills mode, and Claude Code's `allowed-tools` grants permission without restricting other tools. A session that exposes the server's write tools could call them; the prompt forbids it and the tests check that it names no write tool.
- Custom fields of type list: the chosen title is stored as a string; whether the server accepts that on creation is **untested**. Custom fields of type user, multi-select, hierarchy or formatted text cannot be stored in `required_custom_fields` and are reported.
- Verified against the sandbox (2026-10-06): versions with data (one open, one closed) and the per-project list of enabled types match the web UI, and so do the statuses per type (workflow of the role Member). **Untested:** other instances and OpenProject versions, projects with several hundred versions or types.
- Command mode (`/speckit.openproject.discover-fields`) was run as a dry run and as a real bootstrap in a project set up with spec-kit's generic integration (the Claude integration installs skills only). **Untested:** command mode in a Claude-integration project, and the elapsed time of a skills-mode run (SC-001 was measured in command mode only: 1 min 8 s).
- An invalid config with several violations at once, and the YAML-syntax-error case, were not run; only a single unknown key was (dry run and real rebuild).
- Read-only handling of a project with `can_update` false and the redaction of secrets in server errors are checked by prompt text and string tests only, not by a live run.
- It was not verified how spec-kit forms hook keys for extension commands, so this command has no hook check.
- The project must be readable by the server; if it reports `can_update` false the run warns that write commands will fail. The server's own allowlist cannot be inspected.
- Error text from the server is shown with URLs and host names replaced by `<redacted-host>`, and tokens or Authorization headers by `<redacted-secret>`.

## `sync-status`

Keeps task progress consistent between the checkboxes of a feature's `tasks.md` and the work packages that `speckit.taskstoissues` created for it. OpenProject owns the status.

```text
/speckit-openproject-sync-status [feature] [--dry-run]    # skills mode
/speckit.openproject.sync-status [feature] [--dry-run]    # command mode
```

Needs the config written by `discover-fields` (`project`, `types.task`, `statuses.done`) and the ledger `.specify/openproject/mapping-<feature>.json` of the feature. The feature is the argument, or `.specify/feature.json`, or the current branch.

For every task with a ledger entry it compares the checkbox, the work package status now, and the status recorded at the last sync:

| Situation | Result |
|---|---|
| work package done, box open | box is checked (pull) |
| work package reopened, box checked | box is unchecked (pull) |
| box checked, work package not done | work package moves to `statuses.done` (push), only if the server accepts the transition |
| box unchecked again, work package still done | box is checked again, reported as "reverted"; a work package never leaves the done status |
| both sides changed and disagree (for example checked locally, "On hold" in OpenProject) | OpenProject wins, the report names the overwritten checkbox |
| status changed without changing done-ness (New → In progress) | only the ledger changes; shown as "in progress" |
| closed but not done (for example Rejected) | reported as "closed, not done"; never pushed, box unchanged |
| first sync of a ledger without a last synced status | "baseline": a missing status counts as not done, never a conflict |

A transition the server does not accept is reported as `blocked` (with the server's reason and the statuses available for the task type) and left alone; no intermediate statuses are tried. The assignee is recorded in the ledger and shown in the report, never written to `tasks.md`.

A run prints a plan table first. `--dry-run` shows it and writes nothing; otherwise you confirm the whole plan once. Writes: the `status` of task work packages (preview, then confirm, ledger updated after each), checkbox characters of `tasks.md` (through a temporary file and one move; nothing is written if the file changed while the command ran), and the ledger. Results: `complete`, `incomplete` (a task failed, is blocked or was skipped because `tasks.md` changed while the command ran), `no changes`, `dry run`, `stopped`. A second run on unchanged inputs reports `no changes`.

Optional hook: the manifest registers an optional `after_implement` hook (`optional: true`), so the host offers the sync after `/speckit-implement` and it never runs unasked. That the offer actually appears was **not** checked (see below).

### Limitations and untested paths

- Interactive only. Only task work packages are synced; phase and feature work packages are shown in the report only.
- "Writes only the status" is enforced by the prompt, not by the client (same caveat as `discover-fields`).
- A closed status sets the percentage done to 100 on the server (observed in the preview); the command does not touch that field itself.
- Run so far (2026-10-06, skills mode, headless, sandbox, 7 work packages created by hand, hand-written ledger): pull, push, baseline, conflict, reverted, the stop conditions and the `tasks.md`-changed-during-the-run case (S14, S15, S17; details and defects in `../docs/TESTING.md`). **Untested:** the hook offer after `implement`, command mode, a transition the server rejects (the blocked path), the 14-item run and its timing, a stale work package, a failed single confirm, and a ledger written by `speckit.taskstoissues` followed by a sync.
