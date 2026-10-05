# Architecture

## Goal
Run a project with spec-kit and OpenProject fully integrated: specification artifacts and tasks flow into OpenProject, progress and time flow back, and nothing is copied by hand.

## Components
```
spec-kit project                         OpenProject (CE)
  specs/NNN/{spec,plan,tasks}.md   ──►    work packages, relations, versions, attachments
  .specify/openproject/                      ▲
    config.yml (user)                        │ MCP (preview → confirm)
    mapping.json (ledger)  ◄─────────  openproject-ce-mcp (stdio)
        ▲
        │ commands (Markdown prompts)
  preset/     speckit.taskstoissues  (override)
  extension/  speckit.openproject.discover-fields | sync-status | sync-docs | versions | log-time
```

## Packages
- **Preset** (`preset/`): overrides the core command, because extensions cannot override core commands (spec-kit issue #2223). Smallest unit that is useful alone.
- **Extension** (`extension/`): new commands and lifecycle hooks (e.g. after `implement`). Depends on the preset's config and mapping format.
- **Schemas** (`schemas/`): `config.schema.json`, `mapping.schema.json`. Both packages and tests use them.

## Config and state
- `.specify/openproject/config.yml` – user config (project, type/status mapping, defaults). Resolution order: argument → file → `SPECKIT_OPENPROJECT_*` env → ask.
- `.specify/openproject/mapping.json` – ledger: task/phase/feature ID → work package ID, URL, content hash, last synced status. Written after every successful write.
- Hierarchy created by the preset: Feature work package → Phase work packages → Task work packages (subjects start with the feature directory name, `Phase N:` and the task id). The ledger also records `follows` relations (`relations` list).
- The installed command is self-contained: only the command text reaches a user's project, so the capability map and the config/ledger rules are embedded in it between marker comments and kept identical to `docs/mcp-tool-map.md` and `schemas/*.json` by `tests/test_prompt_sync.py`.

## Data flow principles
1. Discover before write (types, statuses, custom fields).
2. Plan table → user confirmation → writes (each preview/confirm) → ledger.
3. Sync is explicit (command or hook), conflict policy: spec-kit is source of truth for structure/subject, OpenProject is source of truth for status, assignee, time.
4. No deletes. Orphans are reported.

## Compatibility
spec-kit ≥ 1.1 (skills mode and command mode), OpenProject Community Edition, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1. Other servers via the capability map (`docs/mcp-tool-map.md`).
