# Data Model: Parent Status Roll-up

No new files and no ledger schema change. The feature reads the config, `tasks.md` and the ledger, and writes the `status` of `phase` and `feature` ledger items plus the status of the matching work packages.

## Config (`.specify/openproject/config.yml`)

| Key | Type | Status | Meaning |
|---|---|---|---|
| `rollup_parents` | boolean | **new, optional** | `false` switches the roll-up off; absent or `true` = on (FR-014). Never written by any command. |
| `statuses.open`, `statuses.in_progress`, `statuses.done` | non-empty string | existing | all three are required while the roll-up is on (a missing one stops the run and points to `discover-fields`) |

## Parent (ledger item with `kind` `phase` or `feature`)

| Field | Source | Rule |
|---|---|---|
| key | ledger item key: `phase-N` or `feature` | a phase belongs to the `## Phase N` heading of `tasks.md` (FR-002) |
| `id` | ledger | work package id |
| `status` | ledger (`B`) | last status the sync saw or wrote; the only field this feature changes (assignee keys of parents are not written) |
| `O` | `get-work-package` in step 6 | status read now, no extra call |
| `R` | computed | rolled-up status: `done`, `in progress`, `open` or `none` |

## Task state for the roll-up (in memory)

| State | When (after the task part of the run) |
|---|---|
| `finished` | status is `statuses.done` or another closed status |
| `in progress` | status equals `statuses.in_progress` |
| `open` | everything else: `statuses.open`, unmapped open status, `unpublished`, `stale`, `blocked`, `failed`, skipped pull or conflict |

`orphan` entries belong to no phase.

## Roll-up rule

| Input states of the children | `R` |
|---|---|
| empty | `none` (left alone, `no tasks`) |
| all `finished` | `done` |
| at least one `finished` or `in progress` | `in progress` |
| otherwise | `open` |

Phase contribution to the feature: see research R5 (closed → finished; `statuses.in_progress` or unmapped open → in progress; `statuses.open` → open; `no tasks` and `no heading` → ignored; `stale` capped at in progress).

## Parent decision (checks in order, first match wins)

| # | Condition | Action | Label |
|---|---|---|---|
| 2 | work package missing | stale | `stale` |
| 3 | `R` = none | left alone | `no tasks` |
| 4 | `O` = done | none | `stays done` if `R` ≠ done |
| 5 | `O` closed, not done | left alone | `closed, not done` |
| 6 | `O` outside `statuses.open`, `statuses.in_progress` | left alone | `unmapped status` |
| 7 | `O` = `R` | none | — |
| 8 | otherwise | write `R` | `roll-up` |

(Row 1, roll-up off, is not evaluated. Numbers match research R4.) If the parent exists and `B` ≠ `O`, the ledger `status` becomes `O`; after a confirmed write it becomes `R`.

## Parent plan item (printed as the Parents section)

| Field | Values |
|---|---|
| `key`, `wp` | parent key, work package id |
| `op_status` | `O` |
| `rolled_up` | `R` |
| `action` | `rolled up`, `unchanged`, `left alone`, `blocked`, `failed`, `stale`, `skipped` |
| `reason` | one sentence; `plan changed` and `changed meanwhile` for the run-time skips and failures |
