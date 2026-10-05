# Research: Tasks → Work Packages

Sources: `jtauschl/openproject-ce-mcp` docs (`docs/tools.md`) and, where marked **[schema]**, the tool input schemas read from the running server over MCP on 2026-10-05. Schemas are verified; behaviour against a live project is not yet (a `get_project` call for the sandbox returned `not_found`; project visibility still to be clarified), repo docs (`docs/ARCHITECTURE.md`, `docs/mcp-tool-map.md`), existing draft `preset/commands/speckit.taskstoissues.md`.

## R1. Setting the parent on create
- **Decision**: Pass `parent` (work package id, string) to `create_work_package` **[schema]**. Create in order feature → phase → task so the parent id is known.
- **Rationale**: Documented optional parameter `parent`; no second update call needed.
- **Alternatives**: Create flat, then `update_work_package` with `parent` — doubles writes and confirmations.
- **Verify (S1)**: parent actually set; behaviour with parent/child date derivation.

## R2. Finding existing work packages (FR-007)
- **Decision**: Use the search capability (`search_work_packages(search="T012", project=…)`) **[schema]**: it matches subject and numeric id only. `list_work_packages` has no subject search and no parent filter. Filter results client-side to subjects that start with the task id followed by a space, and whose parent chain leads to the feature work package (feature WP: subject contains the feature id).
- **Rationale**: Client-side prefix + tree check is correct whether the server does contains or starts-with matching; `T01` must not match `T012`.
- **Alternatives**: Description-tag search (`speckit:<feature>`) — rejected in clarify (identifier lives in subject).
- **Verify (S2/S3)**: exact search parameter name, paging for projects with many work packages, case sensitivity.

## R3. Follows relations (FR-008)
- **Decision**: `create_work_package_relation(work_package_id=<successor>, related_to_work_package_id=<predecessor>, relation_type="follows")` **[schema]** (the server docs say `to_id`/`type`; the live schema says otherwise). Before creating, read `get_work_package_relations` of the successor and skip if a `follows` to that predecessor exists.
- **Rationale**: Docs list `work_package_id`, `to_id`, `type`; read-back shows `predecessor_id`/`successor_id` for precedes/follows, which makes direction checkable.
- **Alternatives**: `blocks` — rejected, does not drive scheduling; `precedes` from predecessor side — equivalent, but "follows" matches existing draft.
- **Verified live (2026-10-05)**: direction as above is correct; read-back via `get_work_package_relations` shows `predecessor_id`/`successor_id`.

## R4. Preview-then-confirm friction (FR-015)
- **Decision**: Every write is called twice (preview, then `confirm=true`) by the command. User-facing confirmation is once per phase; the agent runs preview+confirm for each item in the confirmed phase. Preview `state` other than `"preview"`/`ready=true` stops that item and is reported with `validation_errors`.
- **Rationale**: Server forbids skipping preview; response shape (`ready`, `state`, `validation_errors`, `message`) is documented. Per-phase user confirmation is the clarified decision.
- **Alternatives**: Skip the preview call — impossible; batch tool — none documented.
- **Cost**: 2 tool calls per item → 100 tasks ≈ 200+ calls. Accepted; no timing target in spec. Measure in S1 and record in `docs/TESTING.md`.

## R5. Required custom fields (S6)
- **Decision**: Rely on preview `validation_errors` to detect unfilled mandatory fields; report the field and block that item. Fill only fields given in `required_custom_fields` (`cf_<N>` / `customField<N>`).
- **Rationale**: Docs show custom fields are passed as `cf_<N>`; the preview validates against the project.
- **Alternatives**: Pre-discovery through `get_project_configuration` — richer but its payload shape is unverified; defer to feature "discover-fields" in the extension.

## R6. Write permission check (S7)
- **Decision**: Do not read server env. Detect via `list_projects`/`get_project` access and by the first preview being `rejected`; stop with the server's message before any confirm call. Run a preview of the feature work package as the first write step, before the first `confirm=true`.
- **Rationale**: Command cannot see MCP server env vars; the preview is side-effect free.

## R7. Ledger and config format
- **Decision**: Config `.specify/openproject/config.yml` (adds `types.feature`; drops `mapping_file`, ledger path is fixed). Ledger `.specify/openproject/mapping.json` gets `schema_version`, per-item `kind`, and a `relations` list so relations are idempotent without a server read. Details in `data-model.md`.
- **Rationale**: Spec FR-001/FR-005, ADR docs. Preset has never been tagged (two commits on `main`), so reshaping keys is not a breaking change under the constitution; recorded here instead of an ADR.
- **Alternatives**: Keep `mapping_file` configurable — adds an untested axis.
- **Open**: `defaults.version` stays in the schema because the extension will use it, but this command ignores it (FR-004).

## R8. Parsing tasks.md
- **Decision**: The command prompt parses with explicit numbered rules (phase heading, `- [ ] T### [P]? [US#]? text`, dependency section, phase order). The parsing rules also live as fixture-backed examples in `tests/fixtures/tasks/` so a regression is visible without OpenProject.
- **Rationale**: Prompt is the only runtime; fixtures make the rules reviewable and let tests check them against `schemas/`.
- **Alternatives**: A parser script — rejected: constitution VI, no runtime code in shipped packages.
- **Dependency inference**: explicit statements and Dependencies section only; phase ordering yields phase-level `follows` between consecutive phase WPs? **Decision: no** — only explicit task dependencies create relations (spec S4: "only for real dependencies").

## R9. Stale ledger entries
- **Decision**: Existence of a ledger id is checked with `search_work_packages(search=<id>)` (live finding 2026-10-05: `get_work_package` on a missing id fails with a generic error, search returns `total: 0`). If no result has that id, report "stale", do not recreate, do not edit the ledger; user fixes by removing the entry manually (no deletes by the project).
- **Rationale**: Edge case in spec; constitution III.

## Unresolved (to verify during implementation, not blockers for tasks)
1. Paging behaviour of `search_work_packages` on large projects (R2). Substring matching is verified: post-filtering is mandatory.
2. Preview payload when mandatory custom fields are missing (R5).

## R10. Bulk creation (new finding)
- `bulk_create_work_packages` **[schema]** creates many items with one preview and one confirm; items get `parent_work_package_id` (existing ids only). One bulk call per level (feature, phases, tasks) would cut ~200 calls to ~6 and fit the per-phase confirmation of FR-015.
- **Decision (maintainer, 2026-10-05)**: per-item writes in this feature; `bulk_create_work_packages` is deferred to a later feature (ledger must stay exact after each write, constitution III; confirm and parent behaviour of bulk remain unverified).

## R11. Live findings, 2026-10-05
- Sandbox reachable; project `speckit-sandbox` empty; no work package types enabled in it yet (blocks previews).
- Default instance has no type "Phase"; config default must change (candidates: "Summary task", "Milestone", "Epic"). Decision for the maintainer, needed before tasks (affects `config.template`, S5).
- Failed previews surface as a generic tool error in the Python MCP client; the specific message was only on server stderr. Verify in the Claude Code client; if it holds, S5/S6/S7 diagnostics must come from our own pre-checks (`list_types`, project access), not from preview error text.

## R12. Live findings after enabling types
- Single-item preview works (`state: preview`, `ready: true`); failed single previews give only a generic client error, failed bulk items give readable `error` text.
- `get_project_work_package_context` provides required fields and custom fields up-front: use it for the pre-check (S5/S6) instead of parsing preview errors.
- Sandbox has no custom fields; S6 needs one mandatory custom field created in the admin UI.

## R13. Real-write verification and phase type decision
- Verified with real writes (3 work packages `VERIFY-*` in the sandbox, 1 relation): parent on create, `follows` direction, substring search. Details in `docs/mcp-tool-map.md`. These work packages remain in the sandbox (no deletes by this project); the maintainer removes them.
- `search_work_packages` is a substring match, so the prefix post-filter in R2 is required, not optional.
- **Decision (maintainer, 2026-10-05)**: default phase type is **"Summary task"** (no "Phase" type exists in a default instance). Feature type "Feature", task type "Task". To apply in `preset/openproject-config.template.yml`, `data-model.md` and the S5 scenario during implementation.

## R14. Self-contained installed command (analyze finding B1)
- **Problem**: only the command text is installed into a user's project (`.claude/skills/speckit-taskstoissues/SKILL.md`); `schemas/` and `docs/mcp-tool-map.md` do not exist there.
- **Decision (maintainer, 2026-10-05)**: embed the capability table and compact config/ledger rules in the prompt between marker comments (`<!-- BEGIN capability-map -->`, `<!-- BEGIN config-rules -->`, `<!-- BEGIN ledger-rules -->`). A test (`tests/test_prompt_sync.py`) compares each block with `docs/mcp-tool-map.md` and `schemas/*.json` so they cannot drift.
- **Alternative**: ship copies via `preset.yml` — rejected: not verified that spec-kit installs extra preset files, and copies need syncing anyway.
- Prompt steps refer to capability ids only; concrete tool and parameter names appear once, in the embedded table (constitution II).

## R15. Feature identifier in the subject
- **Decision**: feature work package subject = `<feature-dir-name> <title>` (e.g. `001-tasks-to-work-packages Tasks → Work Packages`). Lookup: `search` by the full directory name, accept a hit whose subject starts with it followed by a space. Avoids the substring collisions seen with `001` (research R13).

## R16. Ledger is per project but tied to one feature (finding 2026-10-05)
- Step 8 of the command requires the ledger's `feature` to equal the current feature, but there is exactly one ledger file `.specify/openproject/mapping.json`. A second feature in the same repository therefore stops at step 8, or its ledger would overwrite the first.
- Options: (a) one ledger per feature, e.g. `.specify/openproject/mapping-<feature>.json` (simple, no schema change besides the path); (b) one ledger with a top-level `features` map; (c) keep one file and tell users to archive it.
- **Open decision for the maintainer.** It changes FR-005, `schemas/mapping.schema.json` and the extension commands that read the ledger; no change was made. Recommendation: (a).
