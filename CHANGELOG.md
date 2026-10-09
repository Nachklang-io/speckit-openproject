# Changelog

All notable changes per package. Format based on Keep a Changelog; versions follow SemVer.

## Preset

### Unreleased

### 1.0.1 - 2026-10-09

#### Fixed
- `speckit.taskstoissues`: task work package subjects are short headlines (`T### <headline>`, at most 70 characters plus `…`) instead of the full task text; the description keeps the complete text. Existing ledgers report "differs, not updated" for tasks synced with the old full-text subjects; `--update` rewrites them, subject and description (description edits made in OpenProject are overwritten). Work packages adopted without a ledger entry keep their old subjects. Feature and phase subjects longer than 255 characters (OpenProject's limit) are cut to 254 characters plus `…`, measured with `wc -m` in a UTF-8 locale (`C.UTF-8` or `en_US.UTF-8`; the command stops without one). Subjects and descriptions are passed to the shell as single-quoted literals. Headlines can be terse: the text is cut at the first `. `, so `Use e.g. foo` becomes `Use e.g`. A file path is removed from the headline only together with a preposition in front of it (`Create schema in db/schema.sql` → `Create schema`); without one it stays (`Write docs/RELEASING.md`).

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

### 0.1.1 - 2026-10-09

#### Changed
- Pins preset 1.0.1 (short headline subjects for task work packages, 255-character subject cap). The extension pin stays at 0.1.0.

### 0.1.0 - 2026-10-08

#### Added
- First bundle: preset 1.0.0 + extension 0.1.0.
