---

description: "Task list for feature 002: field discovery and config bootstrap"
---

# Tasks: Field Discovery and Config Bootstrap

**Input**: Design documents from `specs/002-field-discovery/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R11, Unresolved), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution principle IV requires schema, sync and shape tests and executed prompt scenarios (S10–S13 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The shipped runtime is one Markdown prompt (`extension/commands/discover-fields.md`), so prompt-editing tasks touch the same file and are **not** marked `[P]`; they build the prompt up section by section. Tasks that edit `tests/test_prompt_sync.py` are likewise sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US5 as numbered in `spec.md`
- The installed command is self-contained (as in 001): it uses **capability ids only**; concrete tool names appear once, in the capability rows embedded in the prompt (constitution II). The embedded blocks are `capability-map`, `config-rules` and `config-template`.
- Tasks marked **(maintainer)** need the maintainer's test instance or an admin action; they are never claimed done without an executed run.

## Path Conventions

Monorepo: `extension/`, `preset/`, `schemas/`, `tests/`, `docs/`. `preset/` is touched only for the additive `statuses` key (plan, research R8).

---

## Phase 1: Setup

- [ ] T001 [P] Add `tests/fixtures/discovery/statuses.json`: the sandbox `list_statuses` response recorded on 2026-10-05 (14 statuses incl. `is_default`, `is_closed`), without any host or credential
- [ ] T002 [P] Add `tests/fixtures/discovery/context-task-plain.json`: the sandbox `get_project_work_package_context(project, type=Task)` response recorded on 2026-10-05 (keys `available_types`, `available_statuses`, `available_priorities`, `available_versions`, `fields`, `custom_fields`); hrefs are paths only, no host
- [ ] T003 [P] Add `tests/fixtures/discovery/context-task-mandatory.json`: copy of T002 with `customField1` set to `required: true` in both `fields` and `custom_fields` (derived, not recorded)
- [ ] T004 Add `tests/fixtures/discovery/README.md`: which files are recorded (T001, T002) and which are derived (T003), the recording date, and that fixtures must stay free of hosts, tokens and instance URLs

---

## Phase 2: Foundational (blocks all user stories)

**Purpose**: additive schema key, preset acceptance, tool map row, shared test refactor. Contracts: `contracts/schema-changes.md`, research R2, R7, R8.

- [ ] T005 Add the optional `statuses` object to `schemas/config.schema.json` exactly as in `contracts/schema-changes.md`: properties `open`, `in_progress`, `done` (each `{"type": "string", "minLength": 1}`), `additionalProperties: false`; do not change `required`
- [ ] T006 [P] Add config fixtures `tests/fixtures/config/valid-with-statuses.yml` (all three keys), `invalid-statuses-key.yml` (unknown key `blocked` under `statuses`) and `invalid-statuses-empty.yml` (`done: ""`); each carries `project` and the three required `types` keys
- [ ] T007 Extend `tests/test_schemas.py`: `statuses` accepted when absent, partial and full; unknown key and empty name rejected; `statuses` is not in `required`; `additionalProperties` is `false` for `statuses` (depends on T005, T006)
- [ ] T008 [P] Update `docs/mcp-tool-map.md`: add row `| list-statuses | list_statuses | (none) | yes |` after `get-write-context`; replace the sentence about the embedded copy with "each command embeds only the rows it uses; the embedded rows must be identical to the rows here"; add a verified note (2026-10-05, read-only): `list_statuses` is global and returns `is_default`, `is_closed`; the write context returns `available_statuses` (narrowed per type), `available_priorities`, `available_versions` and `custom_fields` with `required`, `writable`, `has_default`, `type`, `allowed_values`
- [ ] T009 Refactor `tests/test_prompt_sync.py`: make the capability, config-rules and no-URL/no-token tests take the prompt path as a parameter, with `preset/commands/speckit.taskstoissues.md` as the only value for now; capability check becomes: header equal, each embedded row identical to the row of the same capability in `docs/mcp-tool-map.md`, in table order; config-rules check gains `- statuses keys: done, in_progress, open` and `statuses values are non-empty strings`; keep every taskstoissues-specific test unchanged; for now only the preset prompt is under test: the extension prompt is still a placeholder until T015, so no extension case may be added here (extension cases are added in T013, where red tests are intended) (depends on T008)
- [ ] T010 Update the `config-rules` block in `preset/commands/speckit.taskstoissues.md`: top-level keys now `create_relations, defaults, mark_parallel, mcp_server, project, required_custom_fields, statuses, types`; add the `statuses keys` line and the `statuses values are non-empty strings` clause; add one sentence that `statuses` is accepted and ignored by this command (depends on T009)
- [ ] T011 [P] Update `preset/openproject-config.template.yml` (`statuses: {}` section with comment, see `contracts/schema-changes.md`), `preset/preset.yml` (version 0.3.0) and `preset/README.md` (one line: optional `statuses` written by `speckit.openproject.discover-fields`, ignored here)
- [ ] T012 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all feature-001 tests pass unchanged except the intended `statuses` additions (depends on T007, T010, T011)

---

## Phase 3: User Story 1 - Bootstrap a valid config from scratch (Priority: P1) 🎯 MVP

**Goal**: one run against a project without a config produces a schema-valid config.

**Independent Test**: S10 against the sandbox in a scratch project without config; the written file validates and `speckit.taskstoissues --dry-run` reports no configuration error.

### Tests for User Story 1

- [ ] T013 [US1] Extend `tests/test_prompt_sync.py` for the extension prompt: capability block rows are a subset of the tool map and are all read rows (no `create`, `update`, `delete` row); no tool name outside the block; `config-rules` block matches the schema; the `config-template` block parses as YAML, validates against `schemas/config.schema.json` and contains every managed key (`project`, `types`, `defaults`, `statuses`, `required_custom_fields`); the prompt contains the safety statements: `<user-content>`, `untrusted data`, "Every run starts from scratch", "double-quoted", a temporary file and move for the write, "`incomplete`"; `delete_` and `confirm=true` do not appear (depends on T009)
- [ ] T014 [P] [US1] Add `tests/test_discovery_fixtures.py`: the recorded responses contain the fields the prompt relies on: `is_default`/`is_closed` per status (T001); `available_statuses`, `available_priorities`, `available_versions`, `custom_fields[].key|required|writable|has_default|type|allowed_values` (T002, T003); T003 has at least one blocker by the rule `required` ∧ `writable` ∧ ¬`has_default`, T002 has none; no `http://` or `https://` in any fixture (depends on T004)

### Implementation for User Story 1

- [ ] T015 [US1] Replace the placeholder in `extension/commands/discover-fields.md` with the frame: frontmatter (`description`, `argument-hint: "Optional OpenProject project identifier or --dry-run"`, `tools: ['openproject-ce-mcp/*']`), `## User Input`, the arguments sentence, pre-execution hook check (same wording as `speckit.taskstoissues`; first verify in the installed spec-kit how the hook key of an extension command is formed, and if it cannot be established, omit the hook check and say so in the README instead of guessing a key), the embedded `capability-map` block (rows `list-projects`, `list-types`, `get-write-context`, `list-statuses`, copied from `docs/mcp-tool-map.md`), the failure classes (rejected, tool error with generic text, not found), paging rule, the `config-rules` block and the `config-template` block (comments from the shipped template, `statuses` section included) (depends on T013)
- [ ] T016 [US1] Add steps 1–5 of `contracts/command-contract.md` to the prompt: "Every run starts from scratch"; arguments (`[project] [--dry-run]`, any other flag stops); capability check with stop message naming the capability id; project resolution (argument → config → `SPECKIT_OPENPROJECT_PROJECT` → list readable projects and ask; exact match on identifier or id; zero or several: stop and list); load and validate the existing config; calls `list-types` and `list-statuses`, determines the provisional feature, phase and task types (configured value if it is an enabled type, else the first rule match of research R3), then `get-write-context` once for each provisional type that exists (order as in `contracts/command-contract.md` steps 5–7) (depends on T015)
- [ ] T017 [US1] Add step 7 (proposals) to the prompt in the order (a)–(e) of `contracts/command-contract.md`: the deterministic tables from research R3 (types; when several candidates of a role exist list all and recommend the first) and R4 (statuses), each proposal with a short reason; names compared exactly, a difference shown as mismatch; re-read the write context when the user changes a type; mandatory custom fields per research R5 (blocker rule, value types, list fields marked untested, non-representable types reported, empty answer = no value, `incomplete`); optional defaults only if the user asks (spec FR-006): priority and version from the snapshot, assignee as entered and unverified; one grouped prompt "accept, or change by number" (depends on T016)
- [ ] T018 [US1] Add the fresh-config path to the prompt (steps 8, 9, 12, 13 for an absent file): instantiate the embedded template with the approved values, strings double-quoted with `\` and `"` escaped; validate the text against the embedded rules before writing; write to a temporary file in `.specify/openproject/`, re-read and re-validate, then move it over `config.yml`; create the directory if needed; final report with run state (`complete` / `incomplete`), keys written, warnings, set `SPECKIT_OPENPROJECT_*` variables (FR-016), next command `taskstoissues --dry-run` (depends on T017)
- [ ] T019 [P] [US1] Update `extension/extension.yml` (version 0.0.2; command description from the contract) and `extension/README.md` (usage, arguments, what it reads and writes, rules, limitations, untested paths from research "Unresolved")
- [ ] T020 [US1] Define scenario S10 (bootstrap, incl. the mandatory-field branch; the overview check against the web UI is added in T031) in `docs/TESTING.md` with a results table; add the "Scenarios S10–S13" intro naming the installed-skill method (depends on T018)
- [ ] T021 [US1] **(maintainer)** Prepare the sandbox: make `S6 Test Field` mandatory for type Task again, create one open and one closed version, then run S10 through the installed skill in `.scratch/proj` (`scripts/dev-install.sh`, config removed first), `--dry-run` first, then for real; also run the variant "value declined" (run reported `incomplete`); also run one bootstrap through command mode (`/speckit.openproject.discover-fields`, FR-013), and note the elapsed time of the skills-mode run (SC-001: under 5 minutes of user time); record what was executed in `docs/TESTING.md`, label command mode untested if it could not be run (depends on T019, T020)

**Checkpoint**: US1 is complete when T021 is recorded; a config exists that `speckit.taskstoissues --dry-run` accepts.

---

## Phase 4: User Story 2 - Update an existing config without losing edits (Priority: P1)

**Goal**: re-running shows a diff and changes only approved keys; everything else survives.

**Independent Test**: S11: hand-edit, re-run, decline (byte-identical), partially approve (only chosen keys change).

- [ ] T022 [P] [US2] Add `tests/fixtures/config/valid-hand-edited.yml`: valid config with comments, irregular spacing, `create_relations: false`, a type name containing `: ` and `#` in double quotes, a custom field entry; header comment lists the expectations used by S11
- [ ] T023 [US2] Extend `tests/test_schemas.py`: `valid-hand-edited.yml` validates, the special-character type name round-trips through `yaml.safe_load` unchanged, and the file still contains its comments (guards the fixture S11 relies on) (depends on T022)
- [ ] T024 [US2] Add the existing-config path to the prompt (steps 4, 8, 9, 11, 12): invalid existing file → print all violations, continue in rebuild mode, still only after an approved diff; numbered change list `N. <key>: <old> → <new> (reason)` plus unified diff; stale values flagged with a proposed replacement; stale `required_custom_fields` entries reported and kept; existing values kept by default; "no changes" stops without touching the file; approval `all` / `none` / numbers; line-based editing rules of research R6 (only approved keys, comments and order untouched, missing key inserted at end of its section, constructs that cannot be edited safely reported in the diff, stop if the file cannot be edited at all); names compared exactly, a case or whitespace difference is a mismatch shown in the diff, never auto-corrected; the run state `no changes` (depends on T018)
- [ ] T025 [US2] Define scenario S11 in `docs/TESTING.md` (steps from `quickstart.md`: checksum before and after, parse after write, comment and extra key survive, partial approval) (depends on T022, T024)
- [ ] T026 [US2] **(maintainer)** Run S11 through the installed skill in `.scratch/proj` using `valid-hand-edited.yml` as the starting config; record results (depends on T021, T025)

**Checkpoint**: US1 and US2 give the full bootstrap-and-maintain loop.

---

## Phase 5: User Story 3 - Preview with dry run (Priority: P2)

**Goal**: `--dry-run` shows proposals and diff and writes nothing.

**Independent Test**: S12: file checksum unchanged, no config created when none existed.

- [ ] T027 [US3] Extend `tests/test_prompt_sync.py`: the extension prompt contains the line `Dry run: nothing was written.` and states that no file is created or changed with `--dry-run` (depends on T013)
- [ ] T028 [US3] Add step 10 to the prompt: with `--dry-run` print the overview, proposals (all defaults assumed accepted for display) and diff, then `Dry run: nothing was written.` and stop; no temporary file is created either (depends on T024, T027)
- [ ] T029 [US3] Define scenario S12 in `docs/TESTING.md`, then **(maintainer)** run it through the installed skill (config absent and config present; checksum and directory listing before and after); record results (depends on T028)

---

## Phase 6: User Story 4 - Inspect what the project offers (Priority: P2)

**Goal**: a readable overview of types, statuses, priorities, versions and mandatory fields before any proposal.

**Independent Test**: S10 overview compared with the OpenProject web UI.

- [ ] T030 [US4] Add step 6 to the prompt: overview tables before proposals, shown also in dry run: types (milestone marked), statuses (default and closed marked, narrowed set noted), priorities, versions ("none open" when empty), mandatory custom fields per type with value type and allowed values; truncated lists reported (depends on T028)
- [ ] T031 [US4] **(maintainer)** Add the overview check to S10 in `docs/TESTING.md`, then in an S10 re-run compare the overview with the web UI (types, statuses, priorities, versions open and closed, mandatory field) and record deviations; this also settles research Unresolved 2 and 3 (versions with data, enabled types per project) in `docs/TESTING.md` and `docs/mcp-tool-map.md` (depends on T021, T030)

---

## Phase 7: User Story 5 - Fail early with clear diagnostics (Priority: P2)

**Goal**: every failure ends with a specific message and no file change.

**Independent Test**: S13 (a)–(e).

- [ ] T032 [US5] Extend `tests/test_prompt_sync.py`: the extension prompt names the stop for a missing capability, for an unknown or unreadable project and for a tool error ("do not guess the cause"), and states that nothing is written in each case (depends on T013)
- [ ] T033 [US5] Complete the failure handling in the prompt: missing capability message with README pointer, project not set → list readable projects and ask (empty list: stop), project not found or outside the server allowlist stated in the message, generic tool error reported verbatim and stopped, no secrets or hosts printed in any message (depends on T030, T032)
- [ ] T034 [US5] Define scenario S13 (a) no projects readable / project not set, (b) unknown project, (c) project outside the allowlist, (d) MCP server not connected, (e) invalid existing config (file unchanged when the rebuild diff is declined; valid result when approved), in `docs/TESTING.md` (depends on T033)
- [ ] T035 [US5] **(maintainer)** Run S13 (a)–(e) through the installed skill (for (d) start Claude Code without the exported `.env`); record results; a failed variant is a finding, not skipped (depends on T034)

---

## Phase 8: Polish & Cross-Cutting

- [ ] T036 [P] Update `docs/ARCHITECTURE.md`: config now includes the optional `statuses` section; embedded capability rows are a subset of the tool map; one line for `discover-fields` writing the config
- [ ] T037 Update `docs/TESTING.md` results and "untested" labels: command mode untested, list-type custom field untested, anything not executed in S10–S13 labelled as such (depends on T021, T026, T029, T031, T035)
- [ ] T038 Run `scripts/dev-install.sh` and confirm `specify preset list` and `specify extension list` show `openproject` in both, and `.claude/skills/speckit-openproject-discover-fields` exists in the scratch project (depends on T019, T011)
- [ ] T039 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all green (depends on T014, T023, T038)
- [ ] T040 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings or record the reason for not fixing (depends on T039)
- [ ] T041 Mark finished tasks in this file, update `specs/002-field-discovery/checklists/requirements.md` if scope changed, and prepare the PR description (summary, executed scenarios, untested paths); opening the PR is the maintainer's call (depends on T037, T040)

---

## Dependencies & Execution Order

- Phase 1 has no dependencies; T004 depends on T001, T002, T003.
- Phase 2 blocks all stories. Order: T005 → T007; T006 → T007; T008 → T009 → T010; T011 parallel to T010; T012 last.
- US1 (Phase 3) depends on Phase 2. US2 (Phase 4) depends on US1 prompt tasks (T018). US3, US4 and US5 depend on US2's prompt tasks because they extend the same file in order.
- T021 depends on T019 and T020. T026 depends on T021 and T025. T031 depends on T021 and T030.
- Tests for each story are written before the matching prompt tasks and are expected to fail until the prompt exists.

T007 depends on T005, T006.
T009 depends on T008.
T010 depends on T009.
T012 depends on T007, T010, T011.
T013 depends on T009.
T015 depends on T013.
T016 depends on T015.
T017 depends on T016.
T018 depends on T017.
T021 depends on T019, T020.
T024 depends on T018.
T028 depends on T024, T027.
T030 depends on T028.
T033 depends on T030, T032.

## Parallel Opportunities

- Phase 1: T001, T002, T003 together.
- Phase 2: T006 and T008 together after T005; T011 together with T010.
- US1: T014 and T019 are independent of the prompt tasks.
- US2: T022 can be written while the US1 prompt is finished.
- Phase 8: T036 independent of the rest.

## Implementation Strategy

- **MVP**: Phases 1–3 (through T021): bootstrap works end to end, schema extended, preset accepts the new key.
- Then US2 (safe updates, also P1), then dry run, overview and failures as small increments, each ending with its own manual scenario.
- Do not mark a user story done before its scenario was executed; paths not executed are labelled untested (constitution IV, CLAUDE.md verification).
- One feature, one branch (`002-field-discovery`), one PR; small Conventional Commits per task group.
