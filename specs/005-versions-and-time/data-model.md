# Data Model: Versions and Time Tracking

## Ledger additions (`mapping-<feature>.json`, optional, additive)

| Key | Shape | Meaning |
|---|---|---|
| `version` | `{id: int ≥ 1, name: string}` | the feature version found or created by `sync-version`; id wins over name on later runs |
| `time_entries` | array of `TimeRecord` | time entries created by `log-time` |

`TimeRecord`: `key` (string, see research R6), `work_package_id` (int ≥ 1), `spent_on` (`YYYY-MM-DD`), `activity` (string), `hours` (ISO 8601 duration `PT…`), `id` (int ≥ 1, the time entry id), optional `entry_key` (string, present when supplied). Keys unique within the array.

Neither key is present in ledgers written by features 001–004; they stay valid. `schema_version` stays `1.0`.

## Config addition (`config.yml`, optional)

`defaults.activity` (string, exact activity name). Existing `defaults.version` is reused as the version name (research R2).

## Entities (from the spec)

- **Feature version**: ledger `version` + the OpenProject version of that id.
- **Version assignment**: not stored; derived on every run from the work package's version field.
- **Time entry request**: transient: `{key|#id, duration, date, activity}` parsed from user input.
- **Plan item** (both commands): `{target, action, reason}`; version actions: create, reuse, assign, unchanged, other-version, stale, blocked; time actions: create, unchanged, unknown, rejected, stale.
- **Ledger time record**: `TimeRecord`.

## State transitions

Version: `none → (reuse|create) → recorded`; recorded stays until the user removes it from the ledger by hand. Time record: created once, never updated or removed by the commands.
