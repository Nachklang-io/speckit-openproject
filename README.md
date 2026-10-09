# speckit-openproject

Run projects end to end with [spec-kit](https://github.com/github/spec-kit) and [OpenProject](https://www.openproject.org): tasks become work packages with hierarchy and dependencies, status and time flow back, specs and plans are attached, features map to versions. OpenProject is accessed through an MCP server (default: [`openproject-ce-mcp`](https://github.com/jtauschl/openproject-ce-mcp), Community Edition compatible).

| Package | Path | Version | Tag |
|---|---|---|---|
| Preset `openproject` (overrides `speckit.taskstoissues`) | [`preset/`](preset) | 1.0.0 | `preset-v*` |
| Extension `openproject` (discover-fields, sync-status, sync-docs, sync-version, log-time) | [`extension/`](extension) | 0.1.0 | `extension-v*` |
| Bundle `openproject` (preset + extension, pinned) | [`bundle/`](bundle) | 0.1.0 | `bundle-v*` |

Requires spec-kit ≥ 1.1.0 and an OpenProject MCP server configured in your agent's MCP client.

## Install

From the GitHub releases (see [releases](https://github.com/Nachklang-io/speckit-openproject/releases) for the current versions):

```bash
specify preset add --from https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip
specify extension add openproject --from https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip
```

`specify extension add` asks you to confirm the download source; answer `y`. To install both in one step, use the bundle: see [`bundle/README.md`](bundle/README.md). Changes per package: [`CHANGELOG.md`](CHANGELOG.md).

For development, from a clone: `scripts/dev-install.sh` (installs both packages with `--dev` into `.scratch/`).

## Setup guide

The examples use Claude Code in skills mode (`/speckit-<name>`). In command mode the same commands are called `/speckit.<name>`, for example `/speckit.openproject.sync-status`.

### 1. Prepare OpenProject (once per project)

1. Create the OpenProject project, or pick an existing one, and note its identifier (for example `my-project`).
2. Under *Project settings → Work package types*, enable three types: one for features, one for phases and one for tasks. A default instance has no "Phase" type; `Feature`, `Summary task` and `Task` work.
3. Under *Project settings → Modules*, enable *Work packages*. Also enable *Versions* (for `sync-version`) and *Time and costs* (for `log-time`) if you want to use them.
4. Create an API token (*My account → Access tokens*) for the user the agent acts as. That user needs a role in the project that can create and edit work packages, and if you use those commands, also manage versions, log time and add attachments.

### 2. Configure the MCP server (once per machine or repository)

The commands talk to OpenProject only through an MCP server. The tested server is [`openproject-ce-mcp`](https://github.com/jtauschl/openproject-ce-mcp) (v0.4.1). Add it to the MCP client config of your agent. For Claude Code, put a `.mcp.json` in the project root that only references environment variables, so that no token or URL ends up in the repository:

```json
{
  "mcpServers": {
    "openproject": {
      "command": "uvx",
      "args": ["openproject-ce-mcp"],
      "env": {
        "OPENPROJECT_BASE_URL": "${OPENPROJECT_BASE_URL}",
        "OPENPROJECT_API_TOKEN": "${OPENPROJECT_API_TOKEN}",
        "OPENPROJECT_READ_PROJECTS": "${OPENPROJECT_READ_PROJECTS}",
        "OPENPROJECT_WRITE_PROJECTS": "${OPENPROJECT_WRITE_PROJECTS}",
        "OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE": "true",
        "OPENPROJECT_ENABLE_VERSION_WRITE": "true",
        "OPENPROJECT_ATTACHMENT_ROOT": "${OPENPROJECT_ATTACHMENT_ROOT}"
      }
    }
  }
}
```

| Variable | Value | Needed for |
|---|---|---|
| `OPENPROJECT_BASE_URL`, `OPENPROJECT_API_TOKEN` | your instance and the token from step 1 | everything |
| `OPENPROJECT_READ_PROJECTS`, `OPENPROJECT_WRITE_PROJECTS` | the project identifier; the server only sees and writes these projects | everything |
| `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE=true` | | `taskstoissues`, `sync-status`, `sync-docs`, `log-time` |
| `OPENPROJECT_ENABLE_VERSION_WRITE=true` | | `sync-version` |
| `OPENPROJECT_ATTACHMENT_ROOT` | absolute path of a directory that contains the project, for example the project root | `sync-docs` (without it the upload tool is missing and the command stops) |

Export the variables in your shell (for example from a git-ignored `.env`) and start the agent from that shell: `set -a; source .env; set +a; claude`. Started without them, the server does not connect. In Claude Code, `/mcp` shows whether `openproject` is connected. Keep `.env` out of git.

### 3a. New project

1. Install spec-kit: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
2. Create the project: `specify init my-project --integration claude`, then `cd my-project`.
3. Install the preset and the extension with the two commands under [Install](#install), or with the [bundle](bundle/README.md). Check with `specify preset list` and `specify extension list`.
4. Add `.mcp.json` from step 2 and start the agent from a shell with the variables exported.
5. Create the config: `/speckit-openproject-discover-fields my-project --dry-run` shows what it would write. Run it again without `--dry-run`, accept or change the proposals by number and approve the diff. This writes `.specify/openproject/config.yml` (types, status names, mandatory custom fields). Commit it.
6. Work through spec-kit as usual: `/speckit-constitution`, `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`.
7. Create the work packages: `/speckit-taskstoissues --dry-run`, then `/speckit-taskstoissues`. You confirm once per phase. The result is Feature → Phase → Task in OpenProject, plus `follows` relations for task dependencies (asked separately; off with `create_relations: false`). The ledger `.specify/openproject/mapping-<feature>.json` records the ids; commit it.
8. Optional: `/speckit-openproject-sync-version` assigns the feature's work packages to a version, and `/speckit-openproject-sync-docs` attaches `spec.md` and `plan.md` to the feature work package.
9. Implement with `/speckit-implement`, then keep both sides in sync as described in [Keeping OpenProject in sync](#4-keeping-openproject-in-sync).

### 3b. Existing spec-kit project

1. Update spec-kit to ≥ 1.1.0 (`uv tool upgrade specify-cli`, or reinstall it with the command in step 3a).
2. In the project root (the directory with `.specify/`), install the preset and the extension as in step 3a.3. Your specs, plans and `tasks.md` files stay as they are. The preset only replaces `speckit.taskstoissues`.
3. Add `.mcp.json` and run `discover-fields` as in steps 3a.4–3a.5.
4. Bring each feature that already has a `tasks.md` into OpenProject. `/speckit-taskstoissues` works on the active feature, like `/speckit-implement`. spec-kit reads it from `.specify/feature.json` (`{"feature_directory": "specs/<feature>"}`) or from the environment variable `SPECIFY_FEATURE_DIRECTORY`, not from the git branch. Point one of them at the feature, then run `/speckit-taskstoissues --dry-run` and `/speckit-taskstoissues`. The extension commands also take the feature directory name as an argument (`/speckit-openproject-sync-status 001-my-feature`).
   - Work packages that already exist are adopted instead of created, if their subject starts with the task id followed by a space (`T012 …`) and they sit below the feature work package. If several work packages match, the task is reported as `blocked` (ambiguous) and left alone.
   - Work packages are created with the default status of their type. Checked boxes are not copied at creation.
5. Transfer the progress you already made: `/speckit-openproject-sync-status --dry-run`, then `/speckit-openproject-sync-status`. Every checked box whose work package is not done moves to the done status. If the OpenProject workflow forbids that transition, the task is reported as `blocked`. The first run is a baseline and reports no conflicts.
6. Repeat steps 4–5 per feature. You can skip features that are finished and that you do not want in OpenProject.

### 4. Keeping OpenProject in sync

Every command is idempotent: a re-run only does what is still missing, and it reports `no changes` when there is nothing to do. Every command takes `--dry-run`.

| When | Command | What it syncs |
|---|---|---|
| `tasks.md` changed (new tasks, new phase) | `/speckit-taskstoissues` | creates the missing work packages; `--update` also updates titles and descriptions of linked ones |
| tasks done locally, or status changed in OpenProject | `/speckit-openproject-sync-status` | checkbox ↔ status, only `statuses.done` is pushed; OpenProject wins conflicts and the command never reopens a work package |
| `spec.md`, `plan.md`, `research.md` or `data-model.md` changed | `/speckit-openproject-sync-docs` | replaces changed attachments, keeps the summary block in the feature description |
| feature planned for a release | `/speckit-openproject-sync-version [--version <name>]` | creates or reuses the version and assigns unassigned work packages |
| time spent | `/speckit-openproject-log-time T012: 1h30` | one time entry per line, no duplicates on re-run |
| types, statuses or mandatory fields changed in OpenProject | `/speckit-openproject-discover-fields` | updates `config.yml` after a diff |

Commit `.specify/openproject/` after each run; the ledger files are what prevent duplicates for the next person.

### 5. Automatic sync

Every command shows a plan and asks once before it writes. A run without a person to confirm is not supported. Three ways to start the sync without typing the command:

1. **Hook after `/speckit-implement` (built in).** The extension registers an optional `after_implement` hook in `.specify/extensions.yml`. At the end of `/speckit-implement`, the agent offers `/speckit-openproject-sync-status`. Accept it, and it shows the plan and asks for confirmation as usual. The offer was seen in skills mode; accepting it from inside the `implement` flow has not been tested yet.
2. **More hooks (untested).** spec-kit's core commands read hooks for other events from `.specify/extensions.yml` (`after_tasks`, `after_plan`, …). You can add entries in the same format as the installed `after_implement` entry, for example `after_tasks` → `speckit.taskstoissues` or `after_plan` → `speckit.openproject.sync-docs`. With `optional: true` the agent offers the command; with `optional: false` it starts it right away, and the command still asks before writing. This is not tested, and `specify extension update` or `remove` may rewrite the file.
3. **Scheduled check (dry run).** A scheduled job (cron, CI) can run `claude -p "/speckit-openproject-sync-status --dry-run"` in the project, with the MCP variables exported. It reports what is out of sync without writing anything. Headless runs were tested (`discover-fields`, and `sync-status` on earlier prompt revisions); running them from a scheduler was not. Scripting the confirmation for real writes is not supported.

### 6. When something goes wrong

Every command reports what it did and why it stopped. Error texts from the server are shown verbatim (URLs and host names redacted); the commands do not guess the cause. Start here:

**Nothing was written yet**

| Message or symptom | What to do |
|---|---|
| No OpenProject tools in the session, `/mcp` shows the server as failed | Start the agent from a shell where the variables of step 2 are exported, then check `/mcp`. Use `MCP_TIMEOUT` if the server starts slowly. |
| A capability id is missing (for example `create-work-package`) | The server runs without write access. Set `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE` (or `OPENPROJECT_ENABLE_VERSION_WRITE` for `sync-version`) and restart the server. |
| `create-attachment` is missing (`sync-docs`) | Set `OPENPROJECT_ATTACHMENT_ROOT` to an absolute directory that contains the feature directory, restart the server. |
| Project not found, or several projects listed | Use the exact project identifier. The project must be in `OPENPROJECT_READ_PROJECTS` (and `OPENPROJECT_WRITE_PROJECTS` for writes). |
| A type or status is missing | Enable the type in the project settings (Work packages → Types), or pick other names with `discover-fields`. Types, statuses and workflows cannot be created through the API. |
| Configuration or ledger violation | The command prints every violation and stops; it never repairs the file. Fix the named key, or run `discover-fields` for the configuration. A ledger whose `project` or `feature` does not match belongs to another project or feature: do not edit ids by hand. |
| `Error executing tool …` on the first preview | Typical causes: unknown type, parent or project, a project outside the allowlist, a token without permission. Check these in OpenProject and in the server variables; nothing was written. |

**Some items were not written**

| State in the report | Meaning and fix |
|---|---|
| `blocked` – "mandatory field …" | A required custom field has no default. Run `discover-fields` and give it a value, or set it under `required_custom_fields`, then re-run. |
| `blocked` – "ambiguous" | Several work packages match the same key. Delete or rename the duplicates in OpenProject, then re-run. |
| `blocked` – "parent …" | The parent failed or is blocked; fix the parent first. |
| `failed` or `blocked` with `validation_errors` | The server rejected the preview of this item, for example a workflow that does not allow the transition to `statuses.done` (`sync-status`). Fix it in OpenProject or the configuration and re-run; the other items were written. |
| `blocked (closed or locked)` (`sync-version`) | The target version is closed or locked; nothing is assigned. Reopen it in OpenProject or choose another one with `--version`. |
| `stale` | The ledger points to a work package that no longer exists. The commands never recreate it. Remove the entry from the ledger if you want `speckit.taskstoissues` to create a new one. |
| "differs, not updated" | `tasks.md` changed since the last sync. Run `speckit.taskstoissues --update`. |
| `unpublished` (`sync-status`) | The task has no work package yet. Run `speckit.taskstoissues`. |
| `orphan` (`sync-status`, `sync-docs`) | The ledger has an entry for a task or document that is gone locally. Nothing is changed in OpenProject; remove the work package or attachment there by hand if it is no longer needed. |

**The run stopped in the middle**

The ledger is written after every confirmed write, so it always matches what was created.

- `speckit.taskstoissues`: run it again. It skips what is done and finds a work package from an interrupted write by its key (adoption).
- `sync-status`, `sync-docs`, `sync-version`: run the command again. It reads the current state from OpenProject and only writes what is still missing.
- Never repeat a write by hand in OpenProject while a command is running.
- `log-time`: time entries have no natural key. If a line was `failed` after confirmation, check the work package's time entries in OpenProject before you log that line again.

**Cleaning up**

The commands never delete work packages, attachments they did not upload, versions or time entries. To start over, delete the work packages in OpenProject and remove `.specify/openproject/mapping-<feature>.json`. Keep the ledger as long as the work packages exist; without it the next run adopts them by key.

Report bugs with the command's report (it contains no tokens or instance URLs) at the [issue tracker](https://github.com/Nachklang-io/speckit-openproject/issues).

## Docs

[architecture](docs/ARCHITECTURE.md) · [roadmap](docs/ROADMAP.md) · [first session](docs/BOOTSTRAP.md) · [testing](docs/TESTING.md) · [releasing](docs/RELEASING.md) · [publishing](docs/PUBLISHING.md).

Development is AI-assisted with Claude Code and follows spec-kit itself; see [`CLAUDE.md`](CLAUDE.md) and the [constitution](.specify/memory/constitution.md).

License: MIT
