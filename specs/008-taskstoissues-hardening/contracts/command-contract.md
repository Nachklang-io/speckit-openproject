# Contract: `speckit.taskstoissues` changes

Observable behavior of the preset command after this feature. Everything not listed is unchanged.

## Step 1 (prerequisites)

- Script exit 0: continue.
- Script exit non-zero: print the script's message verbatim, then one line:
  `Missing: <file>. Run <command> first.` with `<file>` = `plan.md` or `tasks.md` as the script reports it (plan first) and `<command>` = `/speckit-plan` or `/speckit.plan` (resp. `/speckit-tasks`, `/speckit.tasks`) for the current mode. Stop; nothing is written.

## Step 5 (project and types)

New sub-step between project selection and `list-types`:

1. `get-my-access` (project) → read `current_user_id`; no other field is used.
2. `list-capabilities` (project, `select` = `id`, `limit` = 50, all pages). Look at the entries whose `id` starts with `work_packages/read/` or `work_packages/create/` and ends with `-<current_user_id>`:
   - read and create found → continue.
   - read found, create not found → stop: `Missing write permission: user <current_user_id> can read but not create work packages in <project identifier> (permission work_packages/create is not listed). Nothing was written. Ask a project admin for a role with that permission.` Applies to `--dry-run` as well.
   - read not found, or the list is empty or has another shape → no evidence; continue with `list-types` as today.
   - tool error → existing rule (stop, report verbatim).
3. Always pass `select`; never print any `url` or host from a capability result.
4. The existing "missing type" stop of `list-types` keeps its text and gets one added sentence: `A role without the permission to create work packages can also cause an empty type list (added only when the permission check found no evidence).`

## Step 9 (plan table)

Columns: key, kind, subject, parent key, action, hash, stored, reason. One row per key. Forbidden: ranges (`T001–T020`), `…`, "and N more", omitted hash cells. Parts of at most 40 rows with the header repeated and `part i of n`.

## Capability map

Two rows are added to the preset's map and to `docs/mcp-tool-map.md`:

| Capability | Tool | Parameters | Verified |
|---|---|---|---|
| get-my-access | `get_my_project_access` | project | yes (admin role) |
| list-capabilities | `list_capabilities` | project, limit, offset, select | yes (admin role: read and create listed); denied case for a real read-only role: no |

## Documentation

`README.md` and `preset/README.md`: a note that spec-kit registers no preset command overrides for the `generic` integration, so `/speckit.taskstoissues` stays the core command there, and what to do instead.
