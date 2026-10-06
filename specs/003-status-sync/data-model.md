# Data Model: Status Sync

No new files. The feature reads the config and `tasks.md`, and reads and writes the ledger and the checkbox characters.

## Task (from `specs/<feature>/tasks.md`)

| Field | Source | Rule |
|---|---|---|
| key | `T\d{3,}` after the checkbox | unique in the file; a repeated key stops the run (ambiguous) |
| checked | `[x]` / `[X]` = true, `[ ]` = false | the only field this feature changes |

## Ledger item (`.specify/openproject/mapping-<feature>.json`, `items.<key>`)

| Field | Type | Status | Meaning for this feature |
|---|---|---|---|
| `kind` | `feature` / `phase` / `task` | existing | only `task` items are synced |
| `id` | integer ≥ 1 | existing | work package id |
| `url` | string (path only) | existing | untouched |
| `hash` | string | existing | untouched (content hash of 001) |
| `status` | string | existing | **last synced status name** (`B`); written after each sync step |
| `assignee` | string | **new, optional** | display name at the last sync; absent if unassigned; never a URL, host or token |

Validation: `additionalProperties` stays `false`; the new key is the only schema change (`contracts/schema-changes.md`).

## Config (`statuses`, from feature 002)

`statuses.open`, `statuses.in_progress`, `statuses.done`, each optional string. Required by this feature: `done` (stop if missing). `open` and `in_progress` are used only for display ("in progress") and for validating that they exist among the type's statuses; a missing key is not an error.

## Sync plan item (in memory, printed as the plan table)

| Field | Values |
|---|---|
| `key` | task key |
| `wp` | work package id |
| `checked` | true / false |
| `op_status` | status name read now |
| `base` | ledger `status` or `none` |
| `action` | `none`, `refresh`, `pull`, `push`, `conflict`, `blocked`, `stale`, `orphan`, `unpublished` |
| `labels` | any of `baseline`, `reverted`, `closed-not-done`, `in-progress` |
| `reason` | one sentence, includes the overwritten `tasks.md` state for a conflict |

State per item over a run: `planned` → (`applied` | `skipped` | `failed` | `blocked`). Only `applied` pushes reach the ledger immediately; pulls reach the ledger after the `tasks.md` write succeeded (so an unwritten checkbox never leaves a ledger entry saying "synced").

## State transitions of the ledger `status` (per task)

```text
none ──(first run, baseline)──► O                     # O = status read in that run
B ──(no change on either side)──► O                   # refresh name only
B ──(push confirmed)──► statuses.done
B ──(pull / conflict / reverted)──► O                 # OpenProject status read in that run
B ──(blocked / failed)──► B                           # unchanged
B ──(closed, not done)──► O                           # recorded so the next run is quiet
```

## Report

Result (`complete`, `incomplete`, `no changes`, `dry run`, `stopped`), counts per outcome, one line per changed item, warnings, redacted error texts.
