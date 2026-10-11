# Changelog

All notable changes per package. Format based on Keep a Changelog; versions follow SemVer.

## Preset

### Unreleased

Planned as 1.0.2.

#### Fixed
- `speckit.taskstoissues`: the phase key has no leading zeros (`## Phase 01:` → `phase-1`), so the roll-up of `sync-status` finds the phase; the subject and the adopt search keep the number as written. Two headings with the same key stop the run before any write. A ledger written earlier with `phase-01` keeps working: the old entry counts as `phase-1`, is not renamed, duplicated or adopted again.

#### Changed
- `speckit.taskstoissues` accepts the new optional configuration key `rollup_parents` (boolean). The preset never reads or writes it; it only stops rejecting a configuration that contains it. Use preset 1.0.2 together with extension 0.2.0.

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

Planned as 0.2.0.

#### Added
- `speckit.openproject.sync-status` rolls the status of phase and feature work packages up from their children: all finished → done, at least one finished or in progress → in progress, otherwise open. A Rejected task counts as finished. Phases are rolled up from their task lines, the feature from its phases. Parent writes use preview and confirm and are part of the single confirmation of the run; the plan and the report have a `Parents` section and a `parents:` counts line. On by default; set `rollup_parents: false` in `.specify/openproject/config.yml` to keep the 0.1.0 behaviour.
- Phase membership of a task follows its work package: the roll-up reads `parent_id` in the existing status read and counts the task for the phase it is a child of in OpenProject; without a matching phase it falls back to the nearest `## Phase N` heading. A task counted for another phase than its heading is named in the `Parents` section. Needs preset 1.0.2 for `## Phase 01` headings.
- New optional configuration key `rollup_parents` (boolean, default on). `discover-fields` keeps an existing value unchanged.

#### Changed
- While the roll-up is on, `sync-status` needs `statuses.open` and `statuses.in_progress` in the configuration (run `discover-fields`, or switch the roll-up off).
- A parent is never moved out of done, and a parent in another closed status (for example Rejected) or in a status outside `statuses.open`, `statuses.in_progress` and `statuses.done` (for example On hold) is never written. The server sets percent complete to 100 when a parent gets a closed status.
- All prompts accept `rollup_parents` in the configuration. Older prompts (extension 0.1.0, preset 1.0.1) reject a configuration that contains it.

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

Planned as 0.2.0.

#### Changed
- Pins preset 1.0.2 and extension 0.2.0 (parent status roll-up in `sync-status`, on by default, switch `rollup_parents: false`).

### 0.1.1 - 2026-10-09

#### Changed
- Pins preset 1.0.1 (short headline subjects for task work packages, 255-character subject cap). The extension pin stays at 0.1.0.

### 0.1.0 - 2026-10-08

#### Added
- First bundle: preset 1.0.0 + extension 0.1.0.
