# Research: Versions and Time Tracking

Status: **V** = verified (tool schema read 2026-10-07 or live earlier), **P** = decided by design, **U** = unverified, checked by T001 before the prompts are written.

## R1 Tool contracts (V, live-verified 2026-10-07 against the sandbox)

Schemas read through MCP, then live-verified against `speckit-sandbox` (OpenProject 17.9.1, MCP server v0.4.1):

- `list_versions(project?, search?, limit?, offset?, select?)`: case-insensitive substring match; `select` fields `id`, `name`. Pages with `offset` (page number) until `next_offset` is null. **Verified.**
- `create_version(project, name, description?, start_date?, end_date?, sharing?, status?, confirm=false)`: preview then confirm; a rejected preview is `ready: false` with `validation_errors`, not a tool error. Confirm result's id field is top-level `version_id`. Defaults: `status: "open"`, `sharing: "none"` when omitted. **Verified.**
- `get_version(version_id)`: `status` is a direct top-level string field (`"open"`, `"closed"`, `"locked"`). **Verified.**
- **Correction, supersedes the schema docstring:** `update_work_package` / `bulk_update_work_packages` accept both a singular `version` parameter and a list `target_versions` parameter, and the tool docstring says they "write the same underlying data." Live-tested, this is **not true for this server build**: passing `version: "<name>"` (or `version: "<id>"`) is **silently ineffective** — the preview payload's `_links.targetVersions` stays `[]` and, on confirm, nothing is written (observed three times, including a repeat to rule out a glitch). The write only takes effect through `target_versions: [<name-or-id-as-string>]` (a list), confirmed via both `update_work_package` and `bulk_update_work_packages`, with both id-as-string and name accepted. **The prompts (sync-version.md) MUST use `target_versions`, never the singular `version` parameter, for any write.** `bulk_update_work_packages(items[{work_package_id, target_versions}])` is the batch shape.
- Reads are unaffected by this bug: `get_work_package` returns the assigned version under the field name `version`, and its value is the version's **name as a string**, not an id (confirmed: after assigning by `target_versions: ["VERIFY-005"]`, `get_work_package(..., select=["version"])` returned `version: "VERIFY-005"`). `target_versions` (plural) on a read returns the list form. **Any decision logic comparing "work package's current version" to the intended version must compare by name, not id** (see corrected R3).
- Closed-version rejection is caught at **preview** time (not a tool crash): `update_work_package`/`bulk_update_work_packages` with `target_versions` pointing at a closed version returns a structured `validation_errors` entry (e.g. under `targetVersions`) inside the (per-item, for bulk) result; `ready`/per-item state is rejected, no exception. **Verified.**
- `create_time_entry(activity, hours (ISO 8601), spent_on, work_package_id?, project?, comment?, user?, start_time?, ongoing?, confirm)`; `activity` is a string, matched by exact name (confirmed against `list_time_entry_activities`); `hours` e.g. `PT1H30M`. Confirm result's id field is top-level `time_entry_id`. **Verified.** An unknown/typo'd `activity` name surfaces as a generic tool-level error (`Error executing tool create_time_entry`), not a structured `validation_errors` rejection — the prompt must treat this the same as any other hard tool error (stop the item, report, continue others), and should validate the activity name against the list read in the same run *before* calling `create_time_entry`, to avoid relying on this crash path.
- `list_time_entry_activities()` without parameters; returns an array of objects with `id`, `name`, `position`, `is_default`, `projects` (so an activity can be project-restricted; the 6 named activities on the sandbox project were all listed). **Verified.**
- **No dedicated time-entry write flag exists.** Read the installed `openproject_ce_mcp` package source (`tools.py`): `create_time_entry`, `update_time_entry`, `create_time_entry_until`, `update_time_entry_until`, `delete_time_entry` are registered under the `work_package` write scope, gated by the existing `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE` flag — the same flag that gates `update_work_package`/`bulk_update_work_packages`. `list_time_entry_activities`, `list_time_entries`, `get_time_entry` are under the `work_package` **read** scope (`OPENPROJECT_ENABLE_WORK_PACKAGE_READ`). Version write/read use their own scope (`OPENPROJECT_ENABLE_VERSION_WRITE`/`_READ`), as already assumed. Both flags are already `true` in this repo's tracked `.mcp.json`. **Risk 1 in plan.md is resolved: there is no separate time-entry flag to document or check for.**
- Not tested: a project with the "time tracking" module disabled (would require an invasive sandbox change); a mixed-batch `bulk_update_work_packages` call containing both a succeeding and a rejected item in one call (not exercised live — the per-item independence is documented by the tool and consistent with the single-item behaviour observed, but the exact per-item result array shape for a *mixed* batch is unconfirmed). Both are left as documented assumptions for the prompt/tests rather than live-verified.

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

Per work package after the version is fixed (`V` = chosen version **name**, `W` = the work package's current version — `get_work_package` returns this as a name string, not an id, R1):

| W | Action | Writes |
|---|---|---|
| = V (by name) | unchanged | none |
| none | assign | update (bulk) |
| other | other version (reported, never moved) | none |
| work package not found | stale, skip | none |

Ledger items that are phases or the feature work package are treated like tasks (FR-003).

## R4 Assignment write (V, corrected by T001)

**Correction (R1):** the write parameter is `target_versions` (a list), not the singular `version` parameter — the latter is silently ineffective on this server build despite the tool docstring claiming they write the same data.

One `bulk_update_work_packages` preview for all `assign` items (`items[{work_package_id, target_versions: [<name>]}]`), shown inside the plan, one confirmation, one confirm call, then the per-item results are read. If a per-item failure is reported, that item is `failed`, others are `assigned`. Fallback when bulk is unavailable or rejects the shape: per item `update_work_package(work_package_id, target_versions: [<name>], confirm)`. The exact shape of a *mixed* (partial-success) bulk result array was not exercised live (R1); the prompt must not assume a specific shape beyond "one entry per item" and should re-derive actual state from `get_work_package` after confirm, consistent with plan.md Risk 5.

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
