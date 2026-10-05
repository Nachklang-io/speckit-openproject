# Data Model: Field Discovery and Config Bootstrap

No new persistent entity. The only file written is the existing integration config; the snapshot, proposals and diff live in the conversation.

## Discovery snapshot (in memory, read-only)

| Field | Source | Notes |
|---|---|---|
| project | `list-projects` | `identifier` (used in config), numeric `id`, `name` |
| types | `list-types(project)` ∩ context `available_types` | `name`, `is_milestone` |
| statuses | context `available_statuses` of the task type, joined by id with `list-statuses` | `name`, `is_default`, `is_closed`, `position` |
| priorities | context `available_priorities` | `name` |
| versions | context `available_versions` | `name`; assumed open only (research Unresolved 2) |
| mandatory fields | context `custom_fields` of feature, phase and task type | `key` (`customField<N>`), `name`, `type`, `allowed_values`, per type; blocker = `required` ∧ `writable` ∧ ¬`has_default` |

A snapshot is rebuilt on every run; nothing is cached or written.

## Config (existing file `.specify/openproject/config.yml`, schema `schemas/config.schema.json`)

Managed by this command:

| Key | Rule |
|---|---|
| `project` | identifier of the resolved project; string |
| `types.feature`, `types.phase`, `types.task` | name of an enabled type; non-empty string |
| `types.subtask` | never proposed; left as is |
| `defaults.priority`, `defaults.version`, `defaults.assignee` | only if the user asks; value must exist in the snapshot; `defaults.status` is never written (not applied on create) |
| `statuses.open`, `statuses.in_progress`, `statuses.done` | **new, optional, additive**; name of a status available for the task type; non-empty string; each key individually optional |
| `required_custom_fields` | `customField<N>` → string, number or boolean, for mandatory fields of the used types |

Not managed (kept byte for byte): `mcp_server`, `create_relations`, `mark_parallel`, comments, unknown lines, key order.

Validation: every value must come from the snapshot (type, status, priority, version names) or from the user (custom-field values, assignee); schema rules as embedded in the command.

## Proposal

`{key, old value | absent, new value, reason}`. State: proposed → approved | declined. Only approved proposals reach the file.

## Run result (reported, not stored)

| State | Condition |
|---|---|
| `complete` | file written or already up to date; every mandatory field of the used types has a value |
| `incomplete` | file written (or up to date) but at least one mandatory field has no value or cannot be stored (FR-007) |
| `no changes` | no proposal differs from the file; file not touched (FR-012) |
| `dry run` | proposals and diff shown; nothing written (FR-010) |
| `stopped` | prerequisite failure or user stop; nothing written |

## State transitions of the config file

```
absent ──(bootstrap, approved)──► present (valid)
present ──(diff approved, all/some)──► present (valid, only approved keys changed)
present ──(diff declined | dry run | error)──► unchanged
present(invalid) ──(rebuild shown as diff, approved)──► present (valid)
```

Writes are one atomic move from a temporary file in the same directory; there is no intermediate state on disk.
