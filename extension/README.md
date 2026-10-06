# spec-kit extension: openproject

Work in progress (version 0.0.4). Implemented: `speckit.openproject.discover-fields`, `speckit.openproject.sync-status`, `speckit.openproject.sync-docs`. Planned: `log-time` (see `../docs/ROADMAP.md`). Requires the `openproject` preset for `speckit.taskstoissues`.

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

Optional hook: the manifest registers an optional `after_implement` hook (`optional: true`), so the host offers the sync after `/speckit-implement` and it never runs unasked. The offer was seen once in skills mode after a no-op `implement` run (see `../docs/TESTING.md`).

### Limitations and untested paths

- Interactive only. Only task work packages are synced; phase and feature work packages are shown in the report only.
- "Writes only the status" is enforced by the prompt, not by the client (same caveat as `discover-fields`).
- A closed status sets the percentage done to 100 on the server (observed in the preview); the command does not touch that field itself.
- Run so far (2026-10-06, skills mode, headless, sandbox, 7 work packages created by hand, hand-written ledger): on earlier prompt revisions (the prompt changed afterwards): pull, push, baseline, conflict, reverted, a transition the server rejects (`blocked`, restricted workflow), the stop conditions and the `tasks.md`-changed-during-the-run case (S14, S15, S16 blocked path, S17; details and defects in `../docs/TESTING.md`). **Untested:** the label `closed, not done` with a Rejected work package, accepting the hook offer inside the `implement` flow, command mode, a stale work package, a failed single confirm, and a re-run of `speckit.taskstoissues` over a synced ledger. A 14-work-package feature (ledger written by `taskstoissues`) was synced with one confirmation in 88 s of command time.

## `sync-docs`

Publishes the design documents of a feature to its feature work package: `spec.md`, `plan.md` and, if they exist, `research.md` and `data-model.md` become attachments, and one generated summary block in the work package description lists them with a link and a short hash. Wiki pages cannot be created through the OpenProject API (ADR-0003), so attachments and the description are used.

```text
/speckit-openproject-sync-docs [feature] [--dry-run]    # skills mode
/speckit.openproject.sync-docs [feature] [--dry-run]    # command mode
```

**Prerequisite: the upload directory.** The MCP server registers its upload tool only when it runs with `OPENPROJECT_ATTACHMENT_ROOT` set to an absolute directory, and it accepts only files under that directory. Set it in the MCP client configuration (not in this repo's files) to a directory that contains your project, for example the project root, and restart the server. Without it the command stops at its first step (also with `--dry-run`) and names the missing capability; it has no description-only fallback.

Needs the config written by `discover-fields` (`project`) and the ledger `.specify/openproject/mapping-<feature>.json` with the feature work package (created by `speckit.taskstoissues`). The command never creates a work package.

Per document it compares the SHA-256 of the file, the hash in the ledger (`documents.<file>`) and the attachments on the work package:

| Situation | Result |
|---|---|
| never synced, no attachment of that name | uploaded (`new`) |
| file changed since the last sync | the new version is uploaded first, then the outdated attachment is deleted (`changed`) |
| nothing changed | nothing is written, not even the ledger (`unchanged`) |
| the attachment was removed in OpenProject | uploaded again (`restored`) |
| the file no longer exists | the attachment stays, reported as `orphan` |
| an attachment of that name that the ledger does not know | `blocked`: nothing is written or deleted for that document; resolve it by hand |
| an interrupted replacement (ledger has `pending_delete`) | the next run deletes the superseded attachment (`cleaned`) |

The description is changed only between the markers `<!-- speckit-docs:begin -->` and `<!-- speckit-docs:end -->` (appended once if absent); all text outside is kept. The block is rendered from the ledger: file name as a path-only link, short hash (8 characters) and sync date; no excerpts. Text before the block is never trimmed. Inconsistent markers (a marker twice or missing, end before begin) stop the run before any write, also with `--dry-run`; repair the description by hand.

**Deletion.** The only thing this command deletes is the attachment it uploaded itself and replaced, identified by the attachment id in the ledger (ADR-0004, constitution principle III). It never deletes attachments it did not upload.

A run prints a plan table first. `--dry-run` shows it and writes nothing; otherwise you confirm the whole plan once, and the question names every attachment that will be deleted. Uploads and the description update go through the server's preview, then confirm; the ledger is written after every write through a temporary file that is read back and validated.

### Limitations and untested paths

- Interactive only; one feature per run; at most four documents; the file names are fixed.
- OpenProject does not version attachments: "a new version" means a new attachment with the same name replaces the old one. Content changed in OpenProject by someone else is not detected (the ledger hash decides).
- A crash between an upload and the ledger write leaves an attachment the ledger does not know: the next run reports it as `blocked` and deletes nothing; remove it by hand.
- Links are paths without a host (`/…/api/v3/attachments/<id>/content`); they break if the instance's path prefix changes and are rewritten the next time a document changes.
- Run so far (2026-10-06, skills mode, headless, sandbox, scratch ledger written by hand for one feature work package; the last runs on prompt revision a1d7224 after the review, the earlier ones on 42ddf12): first sync, no-change run, replacement of a changed document, `restored`, `cleaned`, `blocked` (foreign and ambiguous), stops for a missing `spec.md` and a missing ledger; a stale work package was observed once by accident (an earlier scratch work package had been deleted). The interrupted run was simulated by writing the ledger state by hand.
- Not run: the stop for an MCP server that is not connected (two runs ended with `CONNECT_TIMEOUT` under host load and stopped at the capability check, which is not a planned scenario), the equality of the dry-run plan and the real-run plan (only the unchanged ledger checksum was compared), command mode, a ledger written by `taskstoissues` in the same run, the stop for a missing upload capability (server without `OPENPROJECT_ATTACHMENT_ROOT`), inconsistent markers in a real description, a truncated description, files above the server's size limit or outside the upload directory through the command, a real interruption, other instances and servers. See `../docs/TESTING.md`.
