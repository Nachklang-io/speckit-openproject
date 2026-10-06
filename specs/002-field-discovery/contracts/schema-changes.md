# Contract: schema and manifest changes

## `schemas/config.schema.json` (additive)

New optional top-level property:

```json
"statuses": {
  "type": "object",
  "properties": {
    "open": {"type": "string", "minLength": 1},
    "in_progress": {"type": "string", "minLength": 1},
    "done": {"type": "string", "minLength": 1}
  },
  "additionalProperties": false
}
```

- `required` is unchanged (`project`, `types`): every config valid before stays valid.
- No key is renamed or removed (CLAUDE.md hard rule); no major bump, no migration note.
- `statuses` is read by feature 003; `speckit.taskstoissues` accepts and ignores it.

## Template `preset/openproject-config.template.yml`

Add, after `defaults`:

```yaml
# Status names used by status sync (feature 003). Written by speckit.openproject.discover-fields.
# Each key is optional. Names must exist in the project.
statuses: {}
```

## Prompt-embedded rules (kept identical to the schema by `tests/test_prompt_sync.py`)

`config-rules` block, both prompts, gains:

- top-level keys: `…, statuses, types` (sorted)
- `- statuses keys: done, in_progress, open`
- value types line: `statuses values are non-empty strings`

## Manifests

| File | Change |
|---|---|
| `preset/preset.yml` | version 0.2.0 → 0.3.0 |
| `extension/extension.yml` | version 0.0.1 → 0.0.2; description of the `discover-fields` command updated; no new command names |
| `docs/mcp-tool-map.md` | new row `list-statuses`; text of the sync rule changed to "embedded rows are a subset of this table" |
