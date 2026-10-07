# Contract: schema changes

## `schemas/mapping.schema.json` (additive)

```json
"version": {
  "type": "object",
  "required": ["id", "name"],
  "properties": {
    "id": {"type": "integer", "minimum": 1},
    "name": {"type": "string", "minLength": 1}
  },
  "additionalProperties": false
},
"time_entries": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["key", "work_package_id", "spent_on", "activity", "hours", "id"],
    "properties": {
      "key": {"type": "string", "minLength": 1},
      "work_package_id": {"type": "integer", "minimum": 1},
      "spent_on": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
      "activity": {"type": "string", "minLength": 1},
      "hours": {"type": "string", "pattern": "^PT(\\d+H)?(\\d+M)?$"},
      "id": {"type": "integer", "minimum": 1},
      "entry_key": {"type": "string", "minLength": 1}
    },
    "additionalProperties": false
  }
}
```

Key uniqueness is checked by the prompt and the tests, not by the schema (JSON Schema `uniqueItems` would compare whole records).

## `schemas/config.schema.json` (additive)

`defaults.activity`: `{"type": "string", "minLength": 1}`; `$comment`: read by `log-time`, ignored by the other commands. `defaults.version` gets the comment "also the version name for sync-version".

## Compatibility

Ledgers and configs written before this change stay valid. The rule lines in `speckit.taskstoissues`, `sync-status` and `sync-docs` accept and preserve the new keys and never write them. No key is renamed or removed (no major bump).
