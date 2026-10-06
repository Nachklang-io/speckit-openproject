# Data Model: Documentation Sync

No new files besides the ledger key. The feature reads config and documents, reads and writes the ledger, writes attachments and one description block.

## Document (from `specs/<feature>/`)

| Name | Rule |
|---|---|
| `spec.md` | mandatory; missing stops the run |
| `plan.md` | expected; missing is a warning |
| `research.md`, `data-model.md` | optional; missing is skipped silently |

Per document: absolute path, base name (= attachment name), SHA-256 hex of the bytes.

## Ledger (`.specify/openproject/mapping-<feature>.json`), new optional top-level key `documents`

| Field | Type | Meaning |
|---|---|---|
| key | `spec.md` / `plan.md` / `research.md` / `data-model.md` | file name |
| `hash` | string, 64 hex chars | SHA-256 of the content last uploaded |
| `attachment_id` | integer ≥ 1 | attachment holding that content |
| `synced` | string `YYYY-MM-DD` | date of the run that uploaded that content |
| `pending_delete` | integer ≥ 1, optional | superseded attachment id still to be deleted |

`additionalProperties: false` for entries; the key set is closed (the four names). The work package for the feature is `items.feature.id` (feature 001), never changed here.

## Sync plan item (in memory, printed as the plan table)

| Field | Values |
|---|---|
| `doc` | file name |
| `local_hash` | short hash or `missing` |
| `ledger_hash` | short hash or `none` |
| `attachments` | ids found by name |
| `action` | `new`, `changed`, `restored`, `unchanged`, `orphan`, `blocked`, `skip`, plus `cleaned` for a pending deletion |
| `reason` | one sentence |

## Summary block

Rendered from the ledger plus the current attachment link paths (R4, R5 in `research.md`): header row, one row per ledger document in fixed order, markers around. Same ledger → same text.
