# Contract: `speckit.taskstoissues` changes

Observable behavior of the preset command after this feature. Everything not listed is unchanged.

## Step 1 (prerequisites)

- Script exit 0: continue.
- Script exit non-zero: print the script's message verbatim, then one line:
  `Missing: <file>. Run <command> first.` with `<file>` = `plan.md` or `tasks.md` as the script reports it (plan first) and `<command>` = `/speckit-plan` or `/speckit.plan` (resp. `/speckit-tasks`, `/speckit.tasks`) for the current mode. Stop; nothing is written.

## Step 5 (project and types)

New sub-step between project selection and `list-types`:

1. `get-my-access` (project) → read `project_id` and `current_user_id`; no other field is used.
2. `get-capability` (project, capability id `work_packages/create/w<project_id>-<current_user_id>`):
   - `total` = 1 → continue.
   - tool error with `[not_found]` → stop: `Missing write permission: <user id> cannot create work packages in <project identifier> (capability work_packages/create/w<project_id>-<user id> not granted). Nothing was written. Ask a project admin for a role with that permission.` Applies to `--dry-run` as well.
   - any other error or shape → tool error (existing rule), report verbatim.
3. Never print the `url` field of the capability result (it holds the server address).

## Step 9 (plan table)

Columns: key, kind, subject, parent key, action, hash, stored, reason. One row per key. Forbidden: ranges (`T001–T020`), `…`, "and N more", omitted hash cells. Parts of at most 40 rows with the header repeated and `part i of n`.

## Capability map

Two rows are added to the preset's map and to `docs/mcp-tool-map.md`:

| Capability | Tool | Parameters | Verified |
|---|---|---|---|
| get-my-access | `get_my_project_access` | project | yes (admin role) |
| get-capability | `list_capabilities` | project, capability_id | yes (allowed and unknown principal); denied case for a real read-only role: no |

## Documentation

`README.md` and `preset/README.md`: a note that spec-kit registers no preset command overrides for the `generic` integration, so `/speckit.taskstoissues` stays the core command there, and what to do instead.
