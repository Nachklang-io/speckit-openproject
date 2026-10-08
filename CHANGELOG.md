# Changelog

All notable changes per package. Format based on Keep a Changelog; versions follow SemVer.

## Preset

### Unreleased

### 1.0.0 - 2026-10-08

#### Added
- `speckit.taskstoissues` creates OpenProject work packages from `tasks.md` through an OpenProject MCP server: one work package per phase, task and sub-task, with parent/child hierarchy and dependency relations.
- Idempotent re-runs: the per-feature mapping file `.specify/openproject/mapping-<feature>.json` is the ledger; existing work packages are updated, never duplicated.
- `--dry-run` previews every planned write without touching OpenProject.
- Shared JSON schemas for the configuration and the mapping file.
- Release archives built and verified by the release workflow.

## Extension

### Unreleased

### 0.1.0 - 2026-10-08

#### Added
- `speckit.openproject.discover-fields`: discovers types, statuses and custom fields and writes the OpenProject section of the configuration.
- `speckit.openproject.sync-status`: syncs status between `tasks.md` and work packages, with a conflict policy and an optional hook after `implement`.
- `speckit.openproject.sync-docs`: uploads `spec.md` and `plan.md` as attachments and keeps a summary in the feature work package description.
- `speckit.openproject.sync-version`: maps a feature to an OpenProject version.
- `speckit.openproject.log-time`: logs time entries against mapped work packages.
- Release archives built and verified by the release workflow.

## Bundle

### Unreleased

### 0.1.0 - 2026-10-08

#### Added
- First bundle: preset 1.0.0 + extension 0.1.0.
