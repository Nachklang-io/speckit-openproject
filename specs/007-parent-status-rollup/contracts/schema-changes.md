# Contract: schema, manifest and doc changes

## `schemas/config.schema.json` (additive)

New optional top-level property:

```json
"rollup_parents": {"type": "boolean", "description": "false switches off the parent status roll-up of sync-status; absent or true = on"}
```

- `required` and `additionalProperties: false` are unchanged; every config valid before stays valid.
- No key is renamed or removed (CLAUDE.md hard rule): no major bump, no migration note.
- `schemas/mapping.schema.json` does not change.

## Prompt-embedded rules (kept identical by `tests/test_prompt_sync.py`)

`config-rules` block in all six prompts (`sync-status`, `discover-fields`, `sync-docs`, `sync-version`, `log-time`, preset `speckit.taskstoissues`): the top-level key list gains `rollup_parents` and the value types line gains `rollup_parents` next to `create_relations` and `mark_parallel` (booleans). `sync-status.md` additionally embeds a `rollup-table` block (roll-up rule and parent decision table) that must equal the rows of `tests/rollup_reference.py`.

## Manifests and docs

| File | Change |
|---|---|
| `extension/extension.yml` | version 0.1.0 → 0.2.0; command and hook unchanged |
| `preset/preset.yml` | version 1.0.1 → 1.0.2 (embedded config-rules changes) |
| `preset/openproject-config.template.yml` | commented-out `rollup_parents` with a short explanation |
| `bundle/bundle.yml` | version 0.1.1 → 0.2.0; pins preset 1.0.2 and extension 0.2.0 |
| `extension/README.md` | roll-up rules, the switch, versions needed, untested paths |
| `docs/ARCHITECTURE.md` | sync policy: parents are rolled up |
| `docs/TESTING.md` | S34–S38 and run results; untested list |
| `CHANGELOG.md` | extension 0.2.0, preset 1.0.2, bundle 0.2.0 |

Releases and catalog updates follow after merge (`docs/RELEASING.md`), outside this feature's tasks.

## Tests added or changed

| File | Change |
|---|---|
| `tests/rollup_reference.py` | new: `task_state`, `rollup`, `classify_parent`, row list for the prompt block |
| `tests/test_rollup.py` | new: rule cases, guards, feature order, idempotence (second pass = 0 writes), roll-up off |
| `tests/test_schemas.py` | fixtures `valid-rollup-off`, `invalid-rollup-type` |
| `tests/test_prompt_sync.py` | `rollup-table` block equals the reference; config-rules of all six prompts equal the schema |
| `tests/fixtures/sync/rollup-*.json` | secret-free roll-up cases |
