# MCP capability → tool map

Single place that maps capabilities used by the commands to tool names. Add a column per supported server.

| Capability | Tool (jtauschl/openproject-ce-mcp v0.4.1) | Parameters | Verified |
|---|---|---|---|
| list-projects | `list_projects` | search, limit, offset | yes |
| list-types | `list_types` | project | yes |
| get-write-context | `get_project_work_package_context` | project, type | yes |
| list-statuses | `list_statuses` | (none) | yes |
| search-work-packages | `search_work_packages` | search, project, limit, offset | yes |
| get-work-package | `get_work_package` | work_package_id | yes |
| create-work-package | `create_work_package` | project, type, subject, description, parent, custom_fields, priority, assignee, confirm | yes |
| update-work-package | `update_work_package` | work_package_id, subject, description, status, confirm | yes |
| get-relations | `get_work_package_relations` | work_package_id | yes |
| create-relation | `create_work_package_relation` | work_package_id, related_to_work_package_id, relation_type, confirm | yes |
| create-attachment | `create_work_package_attachment` | work_package_id, file_path, description, confirm | yes |
| list-attachments | `list_work_package_attachments` | work_package_id, limit, offset | yes |
| delete-attachment | `delete_attachment` | attachment_id, confirm | yes |

Rules for this table: one row per capability; commands use the capability id in the first column only. Each command embeds only the rows it uses; `tests/test_prompt_sync.py` checks that the embedded header and rows are identical to the rows here. Writes are two-step: call without `confirm` for a preview, then with `confirm=true`. `create_work_package` has no `status` parameter, so a configured default status cannot be applied at creation. "Verified" = exercised against a real instance (see below).

## Verified parameters (jtauschl/openproject-ce-mcp, tool schemas read via MCP `list_tools`, 2026-10-05)
Source: tool input schemas of the running server (147 tools). Schemas only unless a later note says the behaviour was verified live.

| Tool | Parameters (required in bold) |
|---|---|
| `create_work_package` | **project**, **type**, **subject**, description, parent (string id), custom_fields (object), version, target_versions, priority, assignee, category, start_date, due_date, confirm |
| `create_subtask` | **parent_work_package_id**, **type**, **subject**, description, custom_fields, confirm |
| `bulk_create_work_packages` | **items** (each: project, type, subject, optional description, parent_work_package_id or parent, custom_fields, ...), select, confirm; results matched by `index` |
| `update_work_package` | **work_package_id**, subject, description, type, status, parent (`none` removes), custom_fields, percentage_done, confirm |
| `search_work_packages` | **search** (matches subject and numeric id only), project, status, open_only, limit, offset (page, default 1), select |
| `list_work_packages` | project, type, version, status, ... **no subject search, no parent filter**; limit, offset, select |
| `create_work_package_relation` | **work_package_id**, **related_to_work_package_id**, **relation_type**, description, lag, confirm |
| `get_work_package_relations` | **work_package_id**, offset, limit, select |
| `list_types` | project |
| `get_project_work_package_context` | **project**, type (returns writable schema for a type) |

Differences from the server's published docs: relation parameters are `related_to_work_package_id` / `relation_type` (not `to_id` / `type`); custom fields go in `custom_fields`, not `cf_<N>` top-level.

### Live checks against the sandbox (read-only and write previews, no `confirm=true`)
- `list_projects` returns the sandbox (identifier `speckit-sandbox`, `can_update: true`); the sandbox had 0 work packages. `get_project("speckit-sandbox")` returned `not_found` (use the numeric id or check the resolver); `list_types` without `project` lists the global types (Task, Milestone, Summary task, Feature, Epic, User story, Bug); with `project` it returned an empty list because no types were enabled in the sandbox yet. (State before the types were enabled; see the section below for the current behaviour.)
- `create_work_package` (no confirm) for an unknown/disabled type fails with `[validation_error] OpenProject type '<name>' was not found in project '<id>'`. **Through the Python MCP client the tool result only said "Error executing tool create_work_package"**; the detailed message appeared only on the server's stderr. Commands must therefore not rely on parsing `validation_errors` text from failed previews until this is checked in the real Claude Code client.
- There is no type named "Phase" in a default instance; use an existing type (e.g. "Summary task" or "Milestone") for phases.

### After enabling types in the sandbox (previews only, nothing written; sandbox still had 0 work packages)
- `create_work_package` preview for types Feature and Summary task: `state: "preview"`, `ready: true`, `validation_errors: {}`, `payload` echoes subject, markdown description, type, status "New", priority "Normal". Unknown parent id (`999999`) fails (generic client error).
- `bulk_create_work_packages` preview (no confirm): response has `total/succeeded/failed` and per-item `{index, success, result|error}`; a bad type yields `error: "OpenProject type 'Nope' was not found in project '3'."` as readable text. Bulk therefore gives usable per-item diagnostics, unlike a failed single preview.
- `get_project_work_package_context(project, type)` works (earlier failure was caused by missing types): returns `fields` (required/writable), `custom_fields`, statuses, priorities. The sandbox has no custom fields, no categories, no versions, no project phases, so S6 (mandatory custom field) cannot be exercised until one is created in the admin UI.

### Verified with real writes in the sandbox (2026-10-05, 3 work packages + 1 relation, all subjects prefixed `VERIFY-`)
- `create_work_package(..., confirm=true)` returns `state: "confirmed"` and `work_package_id`. `parent` (id as string) sets the parent: `get_work_package` shows `parent_id` and `ancestors`.
- `create_work_package_relation(work_package_id=<successor>, related_to_work_package_id=<predecessor>, relation_type="follows", confirm=true)` is correct: read-back shows `predecessor_id` = predecessor, `successor_id` = successor. `get_work_package_relations` returns `queried_perspective` with `effective_type` (`follows` seen from the successor, `precedes` seen from the predecessor).
- `search_work_packages(search, project)` is a **substring** match on subject and id, not a prefix match: "T0" matched `VERIFY-T001`, "001" matched both `VERIFY-001 Feature` and `VERIFY-T001`. Callers must post-filter (subject starts with the id followed by a space) and check ancestors.

Still unverified live: `bulk_create_work_packages` with `confirm=true` and with parents, lists of 100+ tasks, `exact_match` of `search_work_packages`. (Mandatory custom fields and `update_work_package` are verified, see the notes below.)
- `get_project_work_package_context` (verified 2026-10-05, sandbox with enabled types): each field has `required`, `writable`, `has_default`. `status` and `priority` are required but have defaults, so only fields that are required, writable and without default can block creation. The sandbox reports no custom fields.
- With a mandatory text custom field assigned to type Task only (S6 setup, 2026-10-05): `get_project_work_package_context(type=Task)` lists it under `custom_fields` and in `fields` with key `customField<N>`, `required: true`, `writable: true`, `has_default: false`; for type Feature `custom_fields` is empty. The value is passed as `custom_fields={"customField<N>": "..."}` (verified below).
- Verified live 2026-10-05 (sandbox): `update_work_package` preview shows the full payload (including `lockVersion`) and the confirm updates only the given fields (`lock_version` increments). A rejected preview (e.g. missing mandatory custom field) is `state: "rejected"`, `ready: false` with readable `validation_errors`; it is **not** a tool error. Unknown type, project outside the allowlist, unknown parent and `get_work_package` on a missing id fail with the generic client error `Error executing tool <name>`. `create_work_package` accepts `custom_fields={"customField<N>": "..."}`. Creating a `follows` relation switches the successor to automatic scheduling (`schedule_manually: false`). `search_work_packages` by numeric id returns `total: 0` without error when the id does not exist.
- Verified live 2026-10-05 (sandbox, read-only): `list_statuses` is global (no project parameter) and returns per status `id`, `name`, `is_default`, `is_closed`, `position`. `get_project_work_package_context(project, type)` returns `available_types`, `available_statuses` (narrowed per type: Task showed New, In progress, Closed, On hold, Rejected), `available_priorities`, `available_versions`, `available_categories`, `fields` and `custom_fields`; each field has `key`, `name`, `type`, `required`, `writable`, `has_default`, `allowed_values`. `list_versions(project)` and `list_priorities` exist but the discovery command does not use them. `available_versions` with versions present and list-type custom fields are not yet verified.
- Verified live 2026-10-06 (sandbox, feature 003; work packages 92 and 93 created with `confirm=true`, all other calls read-only or previews): `get_work_package` returns `status` as the status **name** (string) and `assignee` as the display name or `null`, plus `lock_version`; `select` works (`["id","subject","status","assignee","lock_version","type"]`). `update_work_package(work_package_id, status="Closed")` without `confirm` returns `state: preview`, `ready: true`, `validation_errors: {}` and a payload with the status link and `percentageDone: 100` (the server fills it for a closed status). An unknown status name fails with the generic tool error `Error executing tool update_work_package`. The sandbox workflow was unrestricted for the bot at that time (New → Closed accepted in the preview); a forbidden transition was observed later the same day with the transition New → Closed removed for the bot's role: the preview is `state: rejected`, `ready: false`, `validation_errors.status` = "Status is invalid because no valid transition exists from old to new status for the current user's roles." and the write context's `available_statuses` for the type no longer lists `Closed` (it shows what a new work package can reach from its first status). `create_work_package` for type Task still needs `custom_fields={"customField1": ...}` (S6 field is mandatory in the sandbox).

- Verified live 2026-10-06 (sandbox, feature 004, scratch work package 113): `create_work_package_attachment` exists only when the server runs with `OPENPROJECT_ATTACHMENT_ROOT`; it takes `file_path` (no inline content, no file name), the attachment name is the file's base name, a path outside the root fails in the preview with the generic tool error, the confirm returns `attachment_id` and a `download_url` that contains the instance host (never copy it). Two attachments with the same name can coexist. `list_work_package_attachments` returns id, file_name, file_size_bytes, content_type, status, author, container_id, created_at, download_url (no digest). `delete_attachment` has preview and confirm. `get_work_package` returns the description as raw Markdown wrapped in `<user-content>` and keeps HTML-comment markers byte for byte; `attachment:<name>` links render without `href`, path-only links render with it. Fixtures: `tests/fixtures/docs/`.
