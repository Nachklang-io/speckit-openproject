# Research: Versions and Time Tracking

Status: **V** = verified (tool schema read 2026-10-07 or live earlier), **P** = decided by design, **U** = unverified, checked by T001 before the prompts are written.

## R1 Tool contracts (V schemas, U behaviour)

Schemas read through MCP on 2026-10-07:
- `list_versions(project?, search?, limit?, offset?, select?)`: case-insensitive substring match; `select` fields `id`, `name`. Pages with `offset` (page number) until `next_offset` is null.
- `create_version(project, name, description?, start_date?, end_date?, sharing?, status?, confirm=false)`: preview then confirm; a rejected preview is `ready: false` with `validation_errors`, not a tool error.
- `update_work_package(work_package_id, version, ..., confirm)` and `bulk_update_work_packages(items[{work_package_id, version}], confirm)`: `version` accepts a name or id, `none` unassigns. `version` and `target_versions` write the same data and must not be combined; a work package with several target versions rejects `version` alone.
- `create_time_entry(activity, hours (ISO 8601), spent_on, work_package_id?, project?, comment?, user?, start_time?, ongoing?, confirm)`; `activity` is a string (name), `hours` e.g. `PT1H30M`.
- `list_time_entry_activities()` without parameters.
- Existing flag in the repo: `OPENPROJECT_ENABLE_VERSION_WRITE` (set in `.mcp.json`).

To verify live in T001 (sandbox, scratch version and entries): shape of the `create_version` confirm result (id field), `get_version` fields (status), whether `get_work_package` returns the version (field name, name vs id, `select`), shape and fields of `list_time_entry_activities`, `create_time_entry` preview and confirm result (entry id), the server flag for time entries, whether `activity` is project-specific, and how a project without enabled time tracking fails. Decision for the capability check: the tool missing from the tool list means "capability missing"; the message names the flag once T001 knows it.

## R2 Version name (P)

Order: `--version <name>` argument, `defaults.version` from config (existing optional key, ignored by `speckit.taskstoissues`), feature directory name. Match is exact and case-sensitive after trimming. `defaults.version` is one name for all features; the README says to leave it empty for per-feature versions.
Alternatives: a new `version.name_template` key (rejected: a second shipped key for the same purpose, constitution V).

## R3 Version decision table (P)

Inputs: `L` ledger `version` (none, or id and name), `M` = versions of the project whose name equals the intended name, `S` = status of the version.

| L | M | Action | Writes |
|---|---|---|---|
| none | empty | create | create_version, ledger |
| none | one | reuse | ledger |
| none | several | blocked (ambiguous name) | none |
| id | version with that id exists | use it; if its name differs from the intended name: warning, id wins | none |
| id | id not found | stale: stop, name the ledger entry | none |
| any | chosen version has status closed or locked | stop for assignment, report | none |

Per work package after the version is fixed (`V` = chosen version id, `W` = the work package's version):

| W | Action | Writes |
|---|---|---|
| = V | unchanged | none |
| none | assign | update (bulk) |
| other | other version (reported, never moved) | none |
| work package not found | stale, skip | none |

Ledger items that are phases or the feature work package are treated like tasks (FR-003).

## R4 Assignment write (P)

One `bulk_update_work_packages` preview for all `assign` items (`items[{work_package_id, version: <id>}]`), shown inside the plan, one confirmation, one confirm call, then the per-item results are read. If a per-item failure is reported, that item is `failed`, others are `assigned`. Fallback when bulk is unavailable or rejects the shape (T001): per item `update_work_package`.

## R5 Duration grammar (P)

Input line: `<task key>: <duration> [on <YYYY-MM-DD>]`, lines separated by newline or `;`. A work package id may replace the task key as `#<id>` only if that id is in the ledger. Duration forms: `1h30`, `1h30m`, `1:30`, `90m`, `45m`, `1.5h`, `2h`. Normalised to whole minutes; result sent as ISO 8601 `PT<h>H<m>M` (zero parts dropped, `PT45M`, `PT2H`). Rejected before any write: unparsable, zero, negative, more than 24 h, fractions of a minute, date in the future, date not `YYYY-MM-DD`.
Alternative: decimal hours only (rejected: users think in `1h30`).

## R6 Time-entry key and ledger (P)

`key` = `<work_package_id>|<spent_on>|<activity>|<PTxHyM>` or, if `--entry-key <k>` was given, `entry:<k>`. The entry key applies only when the run has exactly one item (otherwise ambiguous: stop). Ledger `time_entries` is an array of `{key, work_package_id, spent_on, activity, hours, id}`; an item whose key is present is `unchanged`; the ledger id is not verified against OpenProject (no reads of entries, clarification 1). A deliberate second identical entry therefore needs `--entry-key`.

## R7 Activity (P)

Order: `--activity <name>` argument, `defaults.activity` from config, else the user picks from the list read from `list_time_entry_activities` before the plan is shown. The name must equal an activity name exactly; an unknown name stops with the list. No guessing from the task.

## R8 Work package resolution (P)

Task key → ledger `items[key].id`. Keys not in the ledger are `unknown` (skipped, reported). Existence is checked with `get_work_package(select=[id, version])` once per distinct work package (stale → skipped). Time entries do not depend on the version.

## R9 Dates (P)

`spent_on` default is today from the shell (`date +%F`), never from model memory. Future dates rejected (R5).

## R10 Stop rules shared (P)

Mandatory inputs: config with `project`, ledger with the feature item, for version also at least one work package. Missing capability: tool absent → stop before any write also in `--dry-run`. Errors are reported with URLs and host names removed (same redaction rule as 004).
