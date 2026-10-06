# Architecture

## Goal
Run a project with spec-kit and OpenProject fully integrated: specification artifacts and tasks flow into OpenProject, progress and time flow back, and nothing is copied by hand.

## Components
```
spec-kit project                         OpenProject (CE)
  specs/NNN/{spec,plan,tasks}.md   ──►    work packages, relations, versions, attachments
  .specify/openproject/                      ▲
    config.yml (user)                        │ MCP (preview → confirm)
    mapping-<feature>.json (ledger)◄──  openproject-ce-mcp (stdio)
        ▲
        │ commands (Markdown prompts)
  preset/     speckit.taskstoissues  (override)
  extension/  speckit.openproject.discover-fields | sync-status | sync-docs | versions | log-time
              (sync-status: implemented in feature 003; sync-docs: feature 004)
```

## Packages
- **Preset** (`preset/`): overrides the core command, because extensions cannot override core commands (spec-kit issue #2223). Smallest unit that is useful alone.
- **Extension** (`extension/`): new commands and lifecycle hooks (e.g. after `implement`). Depends on the preset's config and mapping format.
- **Schemas** (`schemas/`): `config.schema.json`, `mapping.schema.json`. Both packages and tests use them.

## Config and state
- `.specify/openproject/config.yml` – user config (project, type mapping, optional `statuses` mapping open / in_progress / done, defaults, mandatory custom field values). Created and updated by `speckit.openproject.discover-fields` (read-only towards OpenProject, diff and approval before every change, atomic write); read by the write commands. `speckit.taskstoissues` ignores `statuses`; is read by `sync-status` (feature 003). Resolution order: argument → file → `SPECKIT_OPENPROJECT_*` env → ask.
- `.specify/openproject/mapping-<feature>.json` – ledger (one file per feature): task/phase/feature ID → work package ID, URL, content hash, last synced status, assignee (optional, display name, written by `sync-status`); optional top-level `documents`: per design document the SHA-256 of the last uploaded content, attachment id, sync date and, during a replacement, the superseded attachment id (`pending_delete`), written by `sync-docs`. Written after every successful write.
- Hierarchy created by the preset: Feature work package → Phase work packages → Task work packages (subjects start with the feature directory name, `Phase N:` and the task id). The ledger also records `follows` relations (`relations` list).
- The installed command is self-contained: only the command text reaches a user's project, so each command embeds the capability rows it uses (a subset of `docs/mcp-tool-map.md`) and the config/ledger rules between marker comments; `tests/test_prompt_sync.py` keeps them identical to the tool map and `schemas/*.json`.

## Data flow principles
1. Discover before write (types, statuses, custom fields).
2. Plan table → user confirmation → writes (each preview/confirm) → ledger.
3. Sync is explicit (command or hook), conflict policy: spec-kit is source of truth for structure/subject, OpenProject is source of truth for status, assignee, time. `sync-status` applies it per task: a decision table over checkbox, current status and last synced status (ledger `status`); a conflict goes to OpenProject and is named in the report; the assignee lives in the ledger only; a work package never leaves the done status and is never moved through intermediate statuses.
4. No deletes. Orphans are reported.

## Compatibility
spec-kit ≥ 1.1 (skills mode and command mode), OpenProject Community Edition, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1. Other servers via the capability map (`docs/mcp-tool-map.md`).

## Documentation sync (feature 004)
`sync-docs` publishes `spec.md`, `plan.md` (and optionally `research.md`, `data-model.md`) to the feature work package: one attachment per document, one generated summary block in the description between fixed markers (rendered from the ledger, links are paths without a host). A changed document is replaced by uploading first and deleting the superseded attachment second; the ledger records the old id as `pending_delete` in between so that an interrupted run finishes the cleanup. It deletes only attachments it uploaded itself (ADR-0004). The MCP server's upload tool needs `OPENPROJECT_ATTACHMENT_ROOT` (the file must lie under it); without it the command stops. Wiki pages remain out of reach (ADR-0003).
