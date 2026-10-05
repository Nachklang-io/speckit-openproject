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

Then copy `openproject-config.template.yml` to `.specify/presets/openproject/openproject-config.yml` and set at least `project`.

## Usage

```
/speckit.taskstoissues                 # uses the config file
/speckit.taskstoissues my-project      # project identifier as argument
/speckit.taskstoissues --dry-run       # show plan only
/speckit.taskstoissues --update        # update already mapped work packages
```

Configuration order per value: argument → config file → `SPECKIT_OPENPROJECT_*` environment → question.

## Behavior

1. Verifies the MCP tools, the project, and that the configured types exist.
2. Parses phases, tasks, `[P]` markers and dependencies from `tasks.md`.
3. Skips tasks that already exist (mapping file `.specify/presets/openproject/openproject-mapping.json` + search by task ID / `speckit:<feature>` tag).
4. Creates phase work packages, task work packages (parent = phase), then `follows` relations.
5. Prints a summary table with links.

Writes follow the MCP server's preview-then-confirm flow; the command does not bypass it.

## Limitations

- Work packages have no native labels; the feature tag is written into the description.
- Types, statuses, workflows and mandatory custom fields differ per project. The command reports problems instead of guessing.
- LLM execution is not fully deterministic; the mapping file is what guarantees idempotency.
- Installs and overrides the command with spec-kit 1.1.1 (skills mode); re-verify on each spec-kit upgrade.

## Roadmap

A companion extension (`discover-fields`, `sync-status`, mapping management) is planned.

## License

MIT
