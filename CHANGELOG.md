# Changelog

All notable changes per package. Format based on Keep a Changelog; versions follow SemVer.

## Preset

### Unreleased

#### Fixed
- `speckit.taskstoissues`: task work package subjects are short headlines (`T### <headline>`, at most 70 characters) instead of the full task text; the description keeps the complete text. Existing ledgers report "differs, not updated" for tasks synced with the old full-text subjects; `--update` rewrites them. Feature and phase subjects are still capped at 255 characters, measured with `wc -m` instead of estimated. Headlines can be terse: the text is cut at the first `. `, so `Use e.g. foo` becomes `Use e.g`.

### 1.0.0 - 2026-10-08

#### Added
- `speckit.taskstoissues` creates OpenProject work packages from `tasks.md` through an OpenProject MCP server: one work package per phase, task and sub-task, with parent/child hierarchy and dependency relations.
- Idempotent re-runs: the per-feature mapping file `.specify/openproject/mapping-<feature>.json` is the ledger; existing work packages are updated, never duplicated.
- `--dry-run` previews every planned write without touching OpenProject.
- Configuration template `openproject-config.template.yml`; the configuration and the mapping file follow the JSON schemas in the repository.
- Installable from the GitHub release archive with `specify preset add --from <release URL>`.

## Extension

### Unreleased

### 0.1.0 - 2026-10-08

#### Added
- `speckit.openproject.discover-fields`: discovers types, statuses and custom fields and writes the OpenProject section of the configuration.
- `speckit.openproject.sync-status`: syncs status between `tasks.md` and work packages, with a conflict policy and an optional hook after `implement`.
- `speckit.openproject.sync-docs`: uploads `spec.md` and `plan.md` as attachments and keeps a summary in the feature work package description.
- `speckit.openproject.sync-version`: maps a feature to an OpenProject version.
- `speckit.openproject.log-time`: logs time entries against mapped work packages.
- Installable from the GitHub release archive with `specify extension add openproject --from <release URL>`.

## Bundle

### Unreleased

### 0.1.0 - 2026-10-08

#### Added
- First bundle: preset 1.0.0 + extension 0.1.0.
