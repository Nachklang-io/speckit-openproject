# Data Model: Tasks → Work Packages

## Config (`.specify/openproject/config.yml`, schema `schemas/config.schema.json`)
| Key | Type | Notes |
|---|---|---|
| `project` | string | OpenProject project identifier; empty = ask |
| `mcp_server` | string | informational |
| `types.feature` | string | **new**, required; type of the feature parent WP (default "Feature") |
| `types.phase` | string | required; default "Summary task" (decision 2026-10-05; a default instance has no "Phase" type) |
| `types.task` | string | required; default "Task" |
| `types.subtask` | string | optional |
| `defaults.{status,priority,assignee}` | string | applied on create when non-empty |
| `defaults.version` | string | kept, ignored by this command (FR-004) |
| ~~`feature_tag_prefix`~~ | – | removed; labels are plain description text (FR-017), identity lives in the subject (FR-007) |
| `create_relations`, `mark_parallel` | bool | as before |
| `required_custom_fields` | map | `cf_<N>` → scalar |
| ~~`mapping_file`~~ | – | removed; ledger path fixed |

No secrets, no URLs of instances.

## Ledger (`.specify/openproject/mapping.json`, schema `schemas/mapping.schema.json`)
```
schema_version: "1.0"
project: string
feature: string            # e.g. "001-tasks-to-work-packages"
items:
  "<key>":                 # "feature" | "phase-N" | "T###"
    kind: feature|phase|task
    id: int                # work package id
    url?: string           # relative path preferred (/work_packages/123); no host
    hash?: string          # hash of subject+description source text, used by --update
    status?: string        # reserved for sync-status extension
relations:
  - { from: "T002", to: "T001", type: "follows", id?: int }
```

### Rules
- Key `feature` is the single feature WP; `phase-N` uses the number from the heading; `T###` the task id.
- An entry is written immediately after each confirmed write (FR-005). Relations appended after each confirmed relation write.
- Entries are never removed by the command (FR-012). Stale entries are reported (research R9).
- Uniqueness: key unique; `id` unique across items (validated by tests, not by JSON Schema).
- URL: stored without scheme/host to avoid leaking private instance URLs (CLAUDE.md hard rule).

## Parsed task model (in-memory, per run)
| Entity | Fields |
|---|---|
| Phase | `number`, `title`, ordered tasks |
| Task | `id`, `title`, `parallel`, `story?`, `file_hint?`, `depends_on[]`, `phase` |
| Plan item | `key`, `kind`, `subject`, `parent_key`, `action` ∈ create/skip/adopt/update/blocked/stale, `reason?` |

### Subjects and descriptions
- Feature: `<feature-dir-name> <Feature title>` (e.g. `001-tasks-to-work-packages Tasks → Work Packages`), same string as the ledger field `feature` (research R15).
- Phase: `Phase N: <title>`; Task: `T### <title>`.
- Description first lines: `Story: US1 · parallel` (only present parts), then task text, file hint, repo-relative links to `spec.md`/`plan.md`.

## State transitions per plan item
`planned → (create|adopt|skip|update|blocked|stale) → confirmed → recorded`. `failed` is terminal for the run only; next run replans from ledger + search.
