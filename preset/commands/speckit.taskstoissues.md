---
description: Convert existing tasks into OpenProject work packages (phases, tasks, relations) for the feature based on available design artifacts.
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

You **MUST** consider the user input before proceeding (if not empty). Arguments may contain a project identifier, `--dry-run`, or `--update`.

## Pre-Execution Checks

Check whether `.specify/extensions.yml` exists in the project root. If it does and has `hooks.before_taskstoissues` entries, list the enabled ones (skip `enabled: false`) and surface them to the user as optional or mandatory hooks following the standard spec-kit hook protocol. Do not evaluate `condition` expressions yourself. If the file is missing or unparsable, continue silently.

## Outline

1. Run `{SCRIPT}` from the repo root and parse `FEATURE_DIR` and `AVAILABLE_DOCS`. Derive the path of `tasks.md`. All paths must be absolute. If `tasks.md` is missing, stop and tell the user to run the tasks command (`/speckit-tasks` in skills mode, `/speckit.tasks` otherwise).

2. **Resolve configuration** (first hit wins, per value):
   1. Command arguments
   2. `.specify/presets/openproject/openproject-config.yml`
   3. Environment variables (`SPECKIT_OPENPROJECT_PROJECT`, ...)
   4. Ask the user (only for the project; use defaults for everything else)

   If no config file exists, point to `openproject-config.template.yml` in the preset and continue with asked values.

3. **Verify the MCP server.** Confirm that OpenProject MCP tools are available. Needed capabilities: list projects, list types, list statuses, list priorities, list/search work packages, create work package, update work package, create relation. With `jtauschl/openproject-ce-mcp` (verified against v0.4.1) these are `list_projects`, `list_types`, `list_statuses`, `list_priorities`, `list_versions`, `list_work_packages`, `create_work_package`, `update_work_package` and `create_work_package_relation`. Writes must be enabled on the server (`OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE`) and the project listed in `OPENPROJECT_WRITE_PROJECTS`. Match tool names by capability if another server is configured. If no OpenProject tools are available, stop and show the install hint from the README. Never fall back to GitHub Issues and never call the OpenProject REST API directly.

4. **Validate the target project.**
   - Check that the project exists and is in the write allowlist (`OPENPROJECT_WRITE_PROJECTS`) if the server enforces one.
   - Fetch the types, statuses and priorities of the project. Verify that the configured `types.phase` and `types.task` exist. If not, show the available types and ask which to use.
   - Check `required_custom_fields`. If creation later fails on a missing required custom field, report the field and stop for that item instead of guessing values.

5. **Parse `tasks.md`.** Extract:
   - Phases (`## Phase N: Title`)
   - Tasks: ID (`T001`), `[P]` marker, `[US#]` story label, description, file path
   - Dependencies (explicit "depends on", the Dependencies section, phase ordering)

6. **Idempotency check.**
   - Load the mapping file (`mapping_file`, default `.specify/presets/openproject/openproject-mapping.json`; create it if missing). Format: `{ "project": "...", "feature": "...", "items": { "T001": { "id": 123, "url": "..." }, "phase-1": { "id": 120 } } }`.
   - Additionally search the project for existing work packages whose subject starts with the task ID (`T001`) or whose description contains `speckit:<feature>`.
   - Items already mapped or found are **skipped** (or updated if the user passed `--update`). Report the skipped items.

7. **Plan.** Build the full list of work packages to create and show it as a table (ID, type, subject, parent, relations). If `--dry-run` was passed, stop here.

8. **Create work packages** in this order:
   1. One phase work package per phase (type `types.phase`), subject `Phase N: <title>`.
   2. One task work package per task (type `types.task`), subject `<TaskID> <description>`, parent = its phase.
   3. Description (Markdown): the task text, file path, `[P]` note if `mark_parallel`, link to `spec.md`/`plan.md` paths, and the tag line `speckit:<feature-branch-name>` (using `feature_tag_prefix`).
   4. Apply defaults (status, priority, assignee, version) only if configured.
   5. Relations: if `create_relations`, create `follows` (successor -> predecessor) for explicit dependencies. Do not create relations between `[P]` tasks.

   **Preview-and-confirm:** the OpenProject MCP server requires a preview call followed by a confirm call for every write. Do not try to bypass it. Batch efficiently: show the user the validated preview of the first work package and the plan table, ask once for confirmation to proceed with all remaining items of the same shape, then confirm each call. If the server rejects a payload, show the validation error and stop for that item.

   After every successful creation, **immediately write the ID to the mapping file**, so an interrupted run can resume.

9. **Report.** Output a summary table: Task ID, work package ID, subject, parent, link. List skipped, failed and unrelated items separately. Include the project URL.

## Rules

- ONLY create work packages in the project resolved in step 2/4. Never in another project.
- Never create duplicates (step 6).
- Never write the API token or any secret to disk, to the mapping file or into work package text.
- Never modify `tasks.md`. Optionally suggest appending the work package IDs.
- If a step fails with an unexpected error, report it verbatim and stop; do not guess workarounds.

## Post-Execution Checks

If `.specify/extensions.yml` has `hooks.after_taskstoissues` entries, handle them exactly like the pre-execution hooks.
