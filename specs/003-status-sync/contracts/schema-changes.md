# Contract: schema, manifest and doc changes

## `schemas/mapping.schema.json` (additive)

New optional property of a ledger item:

```json
"assignee": {"type": "string", "minLength": 1, "description": "display name at last sync; never a URL, host or token"}
```

- `required` and `additionalProperties: false` of the item are unchanged; every ledger valid before stays valid.
- `schema_version` stays `"1.0"`. No key is renamed or removed (CLAUDE.md hard rule): no major bump, no migration note.
- `status` (existing) now has a writer: this feature records the last synced status name there.

## Prompt-embedded rules (kept identical by `tests/test_prompt_sync.py`)

`ledger-rules` block in `preset/commands/speckit.taskstoissues.md` (accepted, never written by 001): `- ledger item keys: assignee, hash, id, kind, status, url` and, in the value types line, `assignee is a non-empty string`. The new `sync-status.md` embeds the same block.

## Manifests

| File | Change |
|---|---|
| `extension/extension.yml` | version 0.0.2 → 0.0.3; `provides.commands` + `speckit.openproject.sync-status` (`commands/sync-status.md`); `hooks.after_implement`: `command: speckit.openproject.sync-status`, `optional: true`, `description`, `prompt` |
| `preset/preset.yml` | version bump (patch) because the ledger-rules block of the shipped prompt changes |
| `docs/mcp-tool-map.md` | `update-work-package` row: parameters `work_package_id, subject, description, status, confirm`; the embedded copy in both prompts is updated in the same commit |

## Tests added or changed

| File | Change |
|---|---|
| `tests/test_manifests.py` | every `hooks.*.command` is a command provided by the extension; `optional` is `true` |
| `tests/test_prompt_sync.py` | `sync-status.md` joins the parametrized prompts (capability subset, no tool names outside the block, config-rules, ledger-rules); decision-table block equals the table in `tests/sync_reference.py` |
| `tests/test_schemas.py` | fixtures `valid-with-assignee`, `invalid-assignee-type`, `invalid-assignee-empty` |
| `tests/test_sync_decision.py` | decision table, idempotence, checkbox-only edit, baseline never conflicts |
