# Contract: schema, manifest and doc changes

## `schemas/mapping.schema.json` (additive)

New optional top-level property:

```json
"documents": {
  "type": "object",
  "propertyNames": {"enum": ["spec.md", "plan.md", "research.md", "data-model.md"]},
  "additionalProperties": {
    "type": "object",
    "required": ["hash", "attachment_id", "synced"],
    "properties": {
      "hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
      "attachment_id": {"type": "integer", "minimum": 1},
      "synced": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
      "pending_delete": {"type": "integer", "minimum": 1}
    },
    "additionalProperties": false
  }
}
```

Top-level `required` and `additionalProperties: false` unchanged otherwise; every ledger valid before stays valid; `schema_version` stays `"1.0"`; no key renamed or removed.

## Prompt-embedded rules (kept identical by `tests/test_prompt_sync.py`)

`ledger-rules` block in `preset/commands/speckit.taskstoissues.md`, `extension/commands/sync-status.md` and the new `sync-docs.md` (identical in all three): `- ledger top-level keys: documents, feature, items, project, relations, schema_version` and the line `- ledger documents keys: spec.md, plan.md, research.md, data-model.md; entry keys: attachment_id, hash, pending_delete, synced; required entry keys: attachment_id, hash, synced`. Each prompt states in prose outside the block whether it writes `documents` (only `sync-docs.md` does).

## Manifests

| File | Change |
|---|---|
| `extension/extension.yml` | version 0.0.3 → 0.0.4; `provides.commands` + `speckit.openproject.sync-docs` (`commands/sync-docs.md`); no hook |
| `preset/preset.yml` | patch bump (shipped prompt's ledger-rules block changes) |
| `docs/mcp-tool-map.md` | rows `create-attachment` (`create_work_package_attachment`: work_package_id, file_path, description, confirm), `list-attachments` (`list_work_package_attachments`: work_package_id), `delete-attachment` (`delete_attachment`: attachment_id; parameters read from the schema in T002); "Verified" stays `no` until T002 ran |

## Constitution and ADRs

| File | Change |
|---|---|
| `.specify/memory/constitution.md` | principle III: "Deletions are never performed by this project" gains the exception "except an attachment this project uploaded itself, identified by the ledger, when a newer version of the same document replaces it, and only after the confirmed plan"; version 1.1.0 → 1.2.0, amended date |
| `docs/adr/0004-attachment-replacement-deletes-own-uploads.md` | new; context, decision, consequences, rejected alternatives (versioned names, per-file confirmation) |
| `docs/adr/0003-docs-sync-without-wiki-pages.md` | status line "re-verified 2026-10-06 (feature 004)" after T002 |

## Tests added or changed

| File | Change |
|---|---|
| `tests/test_schemas.py` | fixtures `valid-with-documents`, `invalid-documents-unknown-name`, `invalid-documents-hash`, `invalid-documents-missing-id` |
| `tests/test_prompt_sync.py` | `sync-docs.md` joins the parametrized prompts (capability subset, no tool names outside the block, config-rules, ledger-rules); decision-table block equals the table in `tests/docs_reference.py` |
| `tests/test_docs_decision.py` | every row of R6, idempotence, `pending_delete` cleanup, block replacement keeps outside text byte for byte, marker error states |
