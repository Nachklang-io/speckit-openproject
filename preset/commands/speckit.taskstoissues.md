---
description: Convert existing tasks into OpenProject work packages (feature, phases, tasks, relations) for the feature based on available design artifacts.
argument-hint: "Optional OpenProject project identifier, --dry-run or --update"
tools: ['openproject-ce-mcp/*']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Arguments may contain a project identifier, `--dry-run`, or `--update`. Any other flag: stop and list the supported arguments.

## Pre-Execution Checks

Check whether `.specify/extensions.yml` exists in the project root. If it does and has `hooks.before_taskstoissues` entries, list the enabled ones (skip `enabled: false`) and surface them to the user as optional or mandatory hooks following the standard spec-kit hook protocol. Do not evaluate `condition` expressions yourself. If the file is missing or unparsable, continue silently.

## Capability map

All OpenProject access goes through an MCP server (never the REST API, never GitHub Issues). This command refers to OpenProject operations **only by capability id**. The table maps each id to the tool of the tested server; with another server, map by capability and stop if a capability has no tool.

<!-- BEGIN capability-map -->
| Capability | Tool (jtauschl/openproject-ce-mcp v0.4.1) | Parameters | Verified |
|---|---|---|---|
| list-projects | `list_projects` | search, limit, offset | yes |
| list-types | `list_types` | project | yes |
| get-write-context | `get_project_work_package_context` | project, type | yes |
| search-work-packages | `search_work_packages` | search, project, limit, offset | yes |
| get-work-package | `get_work_package` | work_package_id | yes |
| create-work-package | `create_work_package` | project, type, subject, description, parent, custom_fields, priority, assignee, confirm | yes |
| update-work-package | `update_work_package` | work_package_id, subject, description, confirm | no |
| get-relations | `get_work_package_relations` | work_package_id | yes |
| create-relation | `create_work_package_relation` | work_package_id, related_to_work_package_id, relation_type, confirm | yes |
<!-- END capability-map -->

Writes are two-step: call without `confirm` (preview), then repeat the identical call with `confirm=true`. The preview is valid only if `state` is `preview`, `ready` is `true` and `validation_errors` is empty. A failed preview is reported verbatim and the item is not written. There is no way to skip the preview and none may be attempted.

## Configuration and ledger rules

Validate the configuration and the ledger against these rules. Any violation is an error: print every violation and stop; never repair or overwrite the file.

<!-- BEGIN config-rules -->
- top-level keys: create_relations, defaults, mark_parallel, mcp_server, project, required_custom_fields, types
- required top-level keys: project, types
- types keys: feature, phase, subtask, task
- required types keys: feature, phase, task
- defaults keys: assignee, priority, status, version
- unknown keys are errors
<!-- END config-rules -->

<!-- BEGIN ledger-rules -->
- ledger top-level keys: feature, items, project, relations, schema_version
- ledger required top-level keys: feature, items, project, schema_version
- ledger schema_version: 1.0
- ledger item keys: hash, id, kind, status, url
- ledger required item keys: id, kind
- ledger kind values: feature, phase, task
- ledger id: integer >= 1
- ledger relation keys: from, id, to, type
- ledger required relation keys: from, to, type
- ledger relation type values: follows
- unknown keys are errors
<!-- END ledger-rules -->

Defaults: `types.feature` = "Feature", `types.phase` = "Summary task", `types.task` = "Task". `defaults.version` is ignored by this command. `defaults.status` cannot be applied on creation (no status parameter); the type's default status applies.

## Outline

1. **Prerequisites.** Run `{SCRIPT}` from the repo root and parse `FEATURE_DIR` and `AVAILABLE_DOCS`. Use absolute paths. `FEATURE` = the last path segment of `FEATURE_DIR` (for example `001-tasks-to-work-packages`). If `tasks.md` is missing, stop and tell the user to run the tasks command (`/speckit-tasks` in skills mode, `/speckit.tasks` otherwise).

2. **Arguments.** `--dry-run` → plan only. `--update` → allow updating linked work packages. The first argument that is not a flag is the project identifier.

3. **Configuration.** Resolve every value in this order, first hit wins: command argument → `.specify/openproject/config.yml` → environment variable `SPECKIT_OPENPROJECT_<KEY>` → ask the user (only for `project`; other values use the defaults above). If the config file exists, validate it against the config rules and stop on violations. If it does not exist, point to `openproject-config.template.yml` in the preset and continue with the asked project and the defaults.

4. **Capabilities.** Confirm that a tool exists in this session for every capability id in the capability map. If one is missing, stop, name the capability id and tell the user to configure an OpenProject MCP server (see the preset README). Do not fall back to anything else.

5. **Project and types.**
   1. `list-projects` (search = project). The project must exist. If not, stop and list the projects found.
   2. `list-types` (project). Each of `types.feature`, `types.phase`, `types.task` must be in the list. If one is missing, stop before any write, name it, and list the available types.
   3. `get-write-context` (project, type) once for each of `types.feature`, `types.phase`, `types.task`. Note required fields and custom fields. A field counts as a blocker only if it is `required`, `writable` and has `has_default` false, and is not subject, type, project or parent (status and priority are required but have defaults and never block), and is not covered by `required_custom_fields`; each blocker makes every item of that type `blocked` with the reason "mandatory field <name>"; their children become `blocked` too. Items of other types are not affected and the run continues.

6. **Parse `tasks.md`.** Apply these rules in order:
   1. A phase starts at a line `## Phase N: Title`. Phase key `phase-N`.
   2. A task is a line `- [ ] T### [P]? [US#]? text` (checkbox may be `[X]`). `T###` is the task key. `[P]` sets parallel. `[US#]` sets story. A file path in the text is the file hint.
   3. Dependencies: text `(depends on T###, T###)` on a task line, and lines `T### depends on T###[, T###]` in a section titled Dependencies. Phase order and `[P]` alone never create a dependency.
   4. If there is no phase or no task: stop, write nothing.
   5. A task before the first phase heading is reported; ask the user which phase it belongs to and wait.
   6. A dependency on an unknown task id is reported and ignored. Dependencies that form a cycle are reported and all relations on the cycle are ignored.

7. **Subjects and descriptions.**
   - Feature: subject `<FEATURE> <title>` where title is the first `# Tasks:` heading text after the colon (or `FEATURE` if absent). Key `feature`.
   - Phase: `Phase N: <title>`. Task: `T### <text without markers and file hint>`.
   - Description (Markdown), only the parts that exist: first line `Story: US1 · parallel` (story and, if `mark_parallel`, parallel); blank line; the task text; ``File: `<hint>` `` (the path in backticks, otherwise Markdown turns `__init__.py` into bold text); `Spec: specs/<FEATURE>/spec.md · Plan: specs/<FEATURE>/plan.md`. Never put URLs of the OpenProject instance, tokens or credentials into subjects or descriptions.
   - Content hash of an item: lowercase hex SHA-256 of `subject`, a newline, `description`, computed with `shasum -a 256` (or `sha256sum`).

8. **Load the ledger.** Read `.specify/openproject/mapping.json`. If it exists, validate it against the ledger rules and stop on violations; its `project` and `feature` must equal the resolved project and `FEATURE`, otherwise stop. If it does not exist, treat it as empty; do not create it yet.

9. **Plan.** For every item in the order feature, phases, tasks decide exactly one action:
   - `skip`: key is in the ledger and `get-work-package` finds the work package. With `--update`, compare the stored hash with the current hash (see step 14); without it, differing items are reported as "differs, not updated".
   - `stale`: key is in the ledger but `get-work-package` reports not found. Report it; do not recreate; do not change the ledger.
   - `adopt`: key is not in the ledger and exactly one matching work package exists. Matching: `search-work-packages` (search = task key, or `Phase N:`, or `FEATURE`; project). The search is a **substring** match on subject and id, so accept a hit only if its subject starts with the key text followed by a space (phase: starts with `Phase N:`), and, except for the feature itself, its parent chain (`parent_id` and `ancestors` from `get-work-package`) contains the feature work package. Read all result pages. Several matches: report them, action `blocked` (reason "ambiguous"); never guess.
   - `create`: nothing matches.
   - `blocked`: the parent is `blocked`, or an earlier problem applies.
   Also plan relations (step 13): `create` or `skip`.
   Show the plan as a table: key, kind, subject, parent key, action, reason.

10. **Dry run.** If `--dry-run`: print the plan and the line "Dry run: nothing was written." and stop. No write capability may be called and no file may be created or changed.

11. **Write permission check.** Before the first write, run the preview of the first item to create. If it fails or is rejected, stop with the message verbatim; write nothing. Do not interpret generic error texts.

12. **Create, phase by phase.** Ask the user for confirmation **once per phase** (the feature work package is confirmed together with the first phase): show the items of that phase that will be created or adopted and wait for yes. On "no" or "stop", stop and go to the report. For each confirmed item, in order:
    1. `create-work-package` with project, type (`types.feature` / `types.phase` / `types.task`), subject, description, parent = the work package id of the parent item (none for the feature), `defaults.priority` / `defaults.assignee` if non-empty, `custom_fields` from `required_custom_fields`.
    2. Preview, check validity, then confirm. Take the new id from the response.
    3. **Immediately** write the ledger (create the file if missing): `items.<key>` = `kind`, `id`, `url` = `/work_packages/<id>` (path only, no host), `hash`. Adopted items are written the same way without a write call.
    4. If the preview fails: the item is `failed` with the server message; its children become `blocked`. If the feature fails, stop.
    A tool failure (connection, unexpected error) stops the run; the ledger already reflects every confirmed write and a re-run resumes.

13. **Relations.** Only if `create_relations` is true and both items have ledger ids. For each dependency "T_b depends on T_a" (successor T_b, predecessor T_a):
    1. If the ledger `relations` already contains `from` = T_b and `to` = T_a: skip.
    2. Else read `get-relations` of the successor; if it contains a `follows` relation whose predecessor is T_a's id: adopt it into the ledger and skip.
    3. Else `create-relation` with work_package_id = successor id, related_to_work_package_id = predecessor id, relation_type = `follows`; preview, confirm; append `{from, to, type: follows, id}` to the ledger `relations` immediately.
    No relation is created between `[P]` tasks without a stated dependency.

14. **Update (only with `--update`).** For each `skip` item whose current hash differs from the stored hash: show the old and new subject; after the per-phase confirmation, `update-work-package` (subject, description) with preview and confirm, then store the new hash. Never change status, assignee or time. Without `--update` no update capability may be called.

15. **Report.** Counts: created, adopted, skipped, updated, blocked, stale, failed; relations created, skipped. A table: key, work package id, subject, parent key, path `/work_packages/<id>`. Below it, one line per blocked, stale or failed item with the reason. If the run stopped early, say where and that a re-run resumes.

## Rules

- Write only in the project resolved in step 3; never in another project.
- Never create duplicates (steps 8, 9, 13). Never delete work packages, relations or ledger entries. Never modify `tasks.md`.
- Never write the API token, the instance URL or any credential to disk, the ledger or work package text.
- Use capability ids only; do not call any tool that is not in the capability map.
- Report server messages verbatim (`message`, `validation_errors`, per-item `error`). On an unexpected error: report it verbatim and stop. Do not guess workarounds.

## Post-Execution Checks

If `.specify/extensions.yml` has `hooks.after_taskstoissues` entries, handle them exactly like the pre-execution hooks.
