# Research: Field Discovery and Config Bootstrap

Facts marked *live* were read from the sandbox (OpenProject 17.9.1, project `speckit-sandbox`, read-only calls, 2026-10-05). Anything not verified is listed under "Unresolved".

## R1. Data sources for the discovery snapshot

**Decision**: Build the snapshot from three capabilities already in the tool map plus one new one:
`list-projects` (project resolution), `list-types` (project), `get-write-context` (project, type; once per used type), `list-statuses` (global; new row in the map).

**Rationale** (live):
- `get_project_work_package_context(project, type)` returns, in one call: `available_types`, `available_statuses`, `available_priorities`, `available_versions`, `available_categories`, `fields` (each with `required`, `writable`, `has_default`, `type`, `allowed_values`) and `custom_fields` (same shape, key `customField<N>`). That covers types, priorities, versions and custom fields (including the mandatory flag) without separate list calls.
- `list_statuses` has no project parameter and returns `is_default`, `is_closed`, `position` per status. The context's `available_statuses` has only id/title but is narrowed per type (Task showed 5 of 14 statuses: New, In progress, Closed, On hold, Rejected). Status proposals need both: the narrowed set and the `is_closed` flag.
- `list_priorities` and `list_versions` are not needed: the context carries `available_priorities` and `available_versions`.

**Alternatives**: separate `list_versions`/`list_priorities` calls (more calls, same data, `list_versions` results only guarantee `id`, `name`); `get_project` (returned `not_found` for the identifier in 001, not needed).

## R2. Capability map: embed a subset

**Decision**: `docs/mcp-tool-map.md` stays the single table and gains one row, `list-statuses | list_statuses | (none) | yes`. Each command embeds only the rows it uses; `tests/test_prompt_sync.py` checks that the header matches and every embedded row is identical to the row in the table, in table order, and that the prompt uses no tool name outside its block. The existing equality test for `speckit.taskstoissues` becomes this subset test.

**Rationale**: Without this, adding any row for the extension would force every preset release to re-embed rows it never uses.

**Alternatives**: duplicate tables per package (drift); one embedded table in both prompts (couples the preset to extension-only capabilities).

## R3. Type proposal rules (deterministic, first match wins, case-insensitive exact name)

| Role | Candidates in order | If none matches |
|---|---|---|
| feature | Feature, Epic | ask, list all enabled types |
| phase | Phase, Summary task | ask |
| task | Task, User story | ask |

Milestone is never proposed for phase (a point in time, not a container; `is_milestone: true` in the type list). Every proposal states its reason ("exact name", "closest built-in"). `subtask` is not proposed and not written unless it already exists in the config.

**Rationale**: A default instance has no "Phase" type (001 research, live). Rules must be deterministic (CLAUDE.md: prompts are code).

## R4. Status mapping proposal rules

Source: the Task type's `available_statuses` intersected with `list-statuses` by id. Keys written to the config: `statuses.open`, `statuses.in_progress`, `statuses.done`.

| Key | Rule | If none |
|---|---|---|
| open | the status with `is_default: true` | ask |
| in_progress | name `In progress` (case-insensitive, exact) among available | ask among non-closed, non-default |
| done | among `is_closed: true`: first of Done, Closed, Completed, Resolved; if none of these but exactly one closed status, that one | ask among closed statuses |

`Rejected` (closed) is never proposed for done. If the user declines a key, it is omitted (all three keys are individually optional).

**Rationale** (live): default instance statuses are New (default), In progress, Closed (closed), Rejected (closed). The `done` rule must not pick Rejected.

## R5. Mandatory custom fields

**Decision**: For each used type, a custom field is a blocker if it appears in `custom_fields` with `required: true`, `writable: true`, `has_default: false` (same test as 001 step 5.3). Handling by field `type`:
- `String`, `Text`, `Integer`, `Float`, `Bool`, `Date`: ask for a value; store as string, number or boolean as the schema allows (`required_custom_fields` accepts string | number | boolean). Date as ISO string.
- A field with non-empty `allowed_values` (list): show the allowed titles, store the chosen title as string. **Untested**, see Unresolved.
- Anything else (user, multi-select, hierarchy, formattable text): cannot be represented in `required_custom_fields`; say so, ask for nothing, count it as "incomplete" (spec FR-007).
`required_custom_fields` is a flat map keyed by `customField<N>`, so a field mandatory for two types is asked once. A config entry whose key is no longer a mandatory field is reported as "stale, kept"; it is never removed by this command.

**Live**: `S6 Test Field` (`customField1`, String, Task) currently reports `required: false`, so S10 needs the maintainer to make it mandatory again for the mandatory-field path.

## R6. How the config file is written

**Decision**: The agent edits the file as text, key by key, and never regenerates a file that exists.
1. Fresh config: instantiate the template embedded in the command (comments from the shipped template, values substituted).
2. Existing config: change only approved keys by replacing the value on its line; add a missing key by inserting it at the end of its section (or the end of the file for a missing top-level key) with the template's comment; never reorder, never touch comments or unknown lines.
3. Strings are always written double-quoted with `\` and `"` escaped, so names containing `:`, `#` or leading/trailing spaces survive.
4. Before writing, validate the full proposed text against the embedded config rules; after writing to a temporary file in the same directory, re-read and validate again, then move it over `config.yml` in one step (`mv`). On any failure the original stays untouched (FR-010).
5. If the existing file has a construct that line editing cannot preserve (flow-style mapping on one line, anchors, a key repeated), the diff says so for that key before approval (spec Q2); if it cannot be edited safely at all, the command stops and tells the user what to change by hand.

**Alternatives**: parse-and-dump with a YAML library (loses comments; needs a runtime dependency, which the constitution rules out for the shipped packages); ask the user to paste a patch (not "one run").

## R7. Validation without runtime code

**Decision**: The command embeds `config-rules` (same marker block as 001, extended with `statuses`) and a `config-template` block; `tests/test_prompt_sync.py` asserts both against `schemas/config.schema.json`, and that the embedded template parses and validates against the schema. The agent validates by the rules; the schema remains the source of truth for tests.

**Rationale**: Same approach as 001 (R14 there); no scripts shipped.

## R8. Impact on the preset

`speckit.taskstoissues` treats unknown config keys as errors. A config written by this feature contains `statuses`, so the preset must accept it, otherwise discovery would produce files the preset rejects. Changes: `config-rules` block in the preset prompt gains `statuses`; the template gains an optional commented `statuses` section; the preset ignores it (used by feature 003). Preset version 0.2.0 → 0.3.0 (additive key). No shipped key is renamed or removed (no major bump, no migration note).

## R9. Diff and approval

**Decision**: Changes are shown as a numbered list `N. <key>: <old> → <new> (reason)` followed by a unified-style diff of the file. The user answers `all`, `none` or a list of numbers. Unapproved changes are dropped; approved ones are applied together in one atomic write. Existing values are kept by default. A change that only fills a missing key (no old value) is also listed and also needs approval.

**Rationale**: Per-key approval satisfies "applies a change only after explicit user approval" and keeps the interaction to one prompt in the common case.

## R10. Out of scope / deferred

- Non-interactive mode (`--yes`): not in the brief; the run needs answers. Revisit with feature 006 if CI use appears.
- Writing `defaults.priority`/`defaults.version`: proposed only when the user asks for it in the defaults step; empty is the default answer (OpenProject's own default applies).
- Environment variables: if any `SPECKIT_OPENPROJECT_*` variable is set, the final report lists it, because write commands resolve env after the file and before asking, so a stale env value can hide the discovered config.

## R11. Tests and fixtures

- `tests/fixtures/config/`: add `valid-with-statuses.yml`, `valid-hand-edited.yml` (comments, extra spacing, special characters in names), `invalid-statuses-key.yml`, `invalid-statuses-empty.yml`.
- `tests/fixtures/discovery/`: recorded, secret-free responses (statuses, a task write context with a mandatory field, one without) from the sandbox, used by a test that guards the response shape the prompt relies on (`is_closed`, `is_default`, `available_statuses`, `custom_fields[].required|writable|has_default|type`).
- `tests/test_schemas.py`: statuses valid/invalid.
- `tests/test_prompt_sync.py`: subset capability test, rules block, template block, safety rules text (no write capability in the extension prompt, atomic write, dry run line, no secrets).
- Manual scenarios S10–S13 in `docs/TESTING.md`, run through the installed skill (memory: manual walkthroughs miss defects).

## Unresolved (must be labelled "untested" until run)

1. **List-type custom fields**: how `create_work_package` accepts a list custom field (title string vs option id/href). Needs a list custom field in the sandbox. Until verified the path is documented as untested.
2. **`available_versions` with versions present**: the sandbox has none. Assumption: contains only versions assignable (open) to work packages. To verify in S10 after the maintainer creates one open and one closed version.
3. **Enabled types per project**: `list_types(project)` returned all 7 types today, while the 001 note recorded an empty list before types were enabled. Cross-check against `available_types` of the write context; verify by disabling a type in the sandbox.
4. **`available_statuses` per type** appears narrowed by workflow (5 of 14 for Task, for the bot user's roles). Whether it differs per role is unverified; the command treats it as "statuses this user can use for this type".
5. **Command mode** (`/speckit.openproject.discover-fields`) is untested, as for 001.
