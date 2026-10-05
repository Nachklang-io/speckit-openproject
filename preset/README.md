# spec-kit-preset-openproject

A [spec-kit](https://github.com/github/spec-kit) preset that overrides `speckit.taskstoissues` so that `tasks.md` becomes **OpenProject work packages** (phase → task hierarchy, dependency relations) instead of GitHub Issues. It talks to OpenProject through an MCP server; it does not call the REST API itself.

## Prerequisites

- spec-kit with preset support (`specify preset add`)
- An OpenProject instance and an API token
- An OpenProject MCP server. Tested target: [`jtauschl/openproject-ce-mcp`](https://github.com/jtauschl/openproject-ce-mcp) (MIT, works with Community Edition). The official OpenProject MCP server is an Enterprise add-on; other community servers use different tool names and may need adjustments.

```bash
pipx install openproject-ce-mcp
openproject-ce-mcp configure     # writes the client config (.mcp.json etc.) incl. API token
```

Restrict write access in the MCP server environment: `OPENPROJECT_WRITE_PROJECTS=<your-project>`.

## Install

```bash
# local development
specify preset add --dev ./spec-kit-preset-openproject
# afterwards, from a release
specify preset add openproject
```

Then copy `openproject-config.template.yml` to `.specify/openproject/config.yml` and set at least `project`. The three work package types (`feature`, `phase`, `task`) must be enabled in the target project; a default OpenProject instance has no type "Phase", so the template uses "Summary task".

## Usage

```
/speckit-taskstoissues                 # skills mode; uses the config file
/speckit-taskstoissues my-project      # project identifier as argument
/speckit-taskstoissues --dry-run       # show plan only, write nothing
/speckit-taskstoissues --update        # also update linked work packages whose title/description changed
```

In command mode use `/speckit.taskstoissues`. Configuration order per value: argument → config file → `SPECKIT_OPENPROJECT_*` environment → question.

## Behavior

1. Validates the config, verifies the MCP capabilities, the project and the three types.
2. Parses phases, tasks, `[P]` markers, `[US#]` labels and dependencies from `tasks.md`.
3. Plans every item: skip (already in the ledger), adopt (found in OpenProject by its subject prefix), create, stale (ledger entry whose work package is gone, reported only), blocked.
4. Asks for confirmation once per phase, then creates the hierarchy Feature → Phase → Task, one work package at a time (preview, then confirm), and writes the ledger `.specify/openproject/mapping-<feature>.json` after every write. Subjects start with the task id (`T012 …`); the feature subject starts with the feature directory name.
5. Creates `follows` relations for real dependencies only (not for `[P]` tasks).
6. Prints a report with counts, work package ids and reasons for blocked, stale and failed items.

Labels (`[US#]`, `[P]`) are written as plain text in the first line of the description. Nothing is ever deleted. The command works through the capability table embedded in the command; the tested server is `jtauschl/openproject-ce-mcp`.

## Untested paths

Labelled honestly until a scenario in `docs/TESTING.md` has been run:
- `--update` was exercised only in a manual walkthrough against a sandbox (see `docs/TESTING.md`), not through the installed command.
- Mandatory custom fields: exercised in a manual walkthrough only.
- Lists of 100+ tasks beyond a dry run.
- Command mode (`/speckit.taskstoissues`) and other MCP servers.
- The installed skill itself: tool filter in the front matter (`tools: ['openproject-ce-mcp/*']`), argument parsing and the confirmation dialogue; all runs so far were manual walkthroughs of the prompt steps (see `docs/TESTING.md`).
- Scenarios S5 (unknown type, logic only), S7 (project outside the server allowlist only, not the OpenProject read-only role) and S8 (dry run, partial) as well as the S1 duration (SC-004).
- spec-kit 1.0.x: not tested, so `requires.speckit_version` is `>=1.1.0`.

## Limitations

- Work packages have no native labels; markers are written into the description.
- The server cannot set a status when creating; the default status of the type applies (`defaults.status` is not applied).
- Searching for existing work packages is a substring search on the subject; the command filters the hits itself. Re-runs search once per ledger item to detect stale entries, so large lists need many tool calls.
- The ledger is kept per feature (`.specify/openproject/mapping-<feature>.json`), so several features in one repository do not collide. The configuration is shared per project.
- Each write is a separate preview and confirm call; bulk creation is not used.
- Types, statuses, workflows and mandatory custom fields differ per project. The command reports problems instead of guessing.
- LLM execution is not fully deterministic; the mapping file is what guarantees idempotency.
- Installs and overrides the command with spec-kit 1.1.1 (skills mode); re-verify on each spec-kit upgrade.

## Roadmap

A companion extension (`discover-fields`, `sync-status`, mapping management) is planned.

## License

MIT
