---

description: "Task list for feature 001: tasks.md → OpenProject work packages"
---

# Tasks: Tasks → Work Packages

**Input**: Design documents from `specs/001-tasks-to-work-packages/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R15), data-model.md, contracts/, quickstart.md

**Tests**: Requested. FR-018 and constitution principle IV require schema/fixture tests and executed prompt scenarios (S1–S9 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The shipped runtime is one Markdown prompt (`preset/commands/speckit.taskstoissues.md`), so prompt-editing tasks touch the same file and are **not** marked `[P]`; they are ordered to build the prompt up section by section.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US6 as numbered in `spec.md`
- The installed command is self-contained (research R14): the prompt uses **capability ids only**; concrete tool and parameter names appear once, in the capability table embedded in the prompt (constitution II).

## Path Conventions

Monorepo: `preset/`, `schemas/`, `tests/`, `docs/`. `extension/` is not touched.

---

## Phase 1: Setup

- [X] T001 Create `tests/fixtures/config/`, `tests/fixtures/mapping/`, `tests/fixtures/tasks/`; `git rm tests/fixtures/mapping.valid.json tests/fixtures/mapping.invalid.json` (they lack the new required `schema_version` and `kind`) and remove their two tests from `tests/test_schemas.py`; T009 re-adds coverage with the new fixtures
- [X] T002 [P] Add `tests/fixtures/tasks/s1-tasks.md`: 3 phases, 10 tasks (`T001`–`T010`), at least one `[P]` and one `[US1]` label, no dependencies; header comment states "1 feature + 3 phases + 10 tasks = 14 items"
- [X] T003 [P] Add `tests/fixtures/tasks/s4-tasks.md`: 2 phases, 6 tasks, explicit dependencies (e.g. T004 depends on T002), three `[P]` tasks without dependencies between them; header comment lists the expected `follows` pairs and states that `[P]` alone creates none
- [X] T004 [P] Add `tests/fixtures/tasks/s-large-tasks.md`: 6 phases, 120 tasks; header comment: "dry-run only, not run live" (FR-015 plan check)

---

## Phase 2: Foundational (blocks all user stories)

**Purpose**: shared schemas, config template, capability map. Contract: `contracts/schema-changes.md`, `data-model.md`.

- [X] T005 Update `schemas/config.schema.json`: add `types.feature` (string, `minLength` 1) and append it to `types.required`; remove `mapping_file` and `feature_tag_prefix` from `properties`; keep `additionalProperties: false`; add `$comment` on `defaults.version`: "ignored by speckit.taskstoissues"
- [X] T006 Update `schemas/mapping.schema.json`: add required `schema_version` (`const` "1.0"); in `items.*` add required `kind` (enum `feature`, `phase`, `task`), keep `id` as `integer` with `minimum` 1; add optional `relations` array of objects with required `from`, `to`, `type` (enum `follows`) and optional `id`; `url` description: "path only, no host"
- [X] T007 [P] Add config fixtures in `tests/fixtures/config/`: `valid-minimal.yml`, `valid-full.yml`, `invalid-missing-feature-type.yml`, `invalid-mapping-file-key.yml`, `invalid-feature-tag-prefix-key.yml`
- [X] T008 [P] Add mapping fixtures in `tests/fixtures/mapping/`: `valid-s1.json` (top-level `feature` = full feature directory name; 14 items with keys `feature`, `phase-1`..`phase-3`, `T001`..`T010`), `valid-with-relations.json`, `invalid-no-kind.json`, `invalid-id-zero.json`, `invalid-relation-type.json`, `invalid-no-schema-version.json`
- [X] T009 Extend `tests/test_schemas.py`: parametrised valid/invalid tests over all config and mapping fixtures; the S1 ledger test asserts exactly 14 items and unique `id` values (uniqueness is not expressible in JSON Schema, see `data-model.md` rules)
- [X] T010 Update `preset/openproject-config.template.yml`: header path `.specify/openproject/config.yml`; add `types.feature: "Feature"`; set `types.phase: "Summary task"` and keep `types.task: "Task"` with a comment that a default instance has no "Phase" type (research R13); remove `mapping_file` and `feature_tag_prefix`; keep `defaults.version` with the comment "ignored by this command"; the existing template test must pass
- [X] T011 [P] Update `docs/mcp-tool-map.md`: turn the capability table into the single source with stable capability ids (e.g. `list-projects`, `list-types`, `get-write-context`, `search-work-packages`, `get-work-package`, `create-work-package`, `update-work-package`, `get-relations`, `create-relation`), tool name and verified parameter names per id, one row each; format must be machine-comparable (one table, header row fixed) because `tests/test_prompt_sync.py` (T021) parses it
- [X] T012 Run `uv run pytest tests/test_schemas.py tests/test_manifests.py` and `uv run ruff check . && uv run ruff format --check .`; fix until green

**Checkpoint**: schemas, fixtures and capability map exist; prompt work can start.

---

## Phase 3: User Story 1 - Publish tasks as a work package hierarchy (Priority: P1) 🎯 MVP

**Goal**: One run creates Feature → Phase → Task work packages with parents and a complete ledger.

**Independent Test**: Scenario S1 on an empty sandbox (`quickstart.md` steps 1–3): 14 work packages, correct parents, 14 ledger entries.

- [X] T013 [US1] Rewrite the header and steps 1–2 of `preset/commands/speckit.taskstoissues.md`: keep front matter (`description`, `argument-hint`, `scripts`); config path `.specify/openproject/config.yml`, ledger path `.specify/openproject/mapping-<feature>.json`; resolution order argument → config file → `SPECKIT_OPENPROJECT_*` env → ask; add the embedded block `<!-- BEGIN config-rules -->…<!-- END config-rules -->` listing allowed keys, required keys, enums and defaults exactly as in `schemas/config.schema.json`; stop with the violations on invalid config (contracts/command-contract.md stop condition 2)
- [X] T014 [US1] Embed the capability table in `preset/commands/speckit.taskstoissues.md` between `<!-- BEGIN capability-map -->` and `<!-- END capability-map -->`, copied verbatim from `docs/mcp-tool-map.md` (T011); state in the prompt that all steps use capability ids and that no other tool name may be used
- [X] T015 [US1] Rewrite the verification steps in `preset/commands/speckit.taskstoissues.md` using capability ids only: stop and name the missing capability and the README install hint if one has no tool in the session (no GitHub-issue fallback, no REST, ADR-0002); `list-projects` to confirm the project; `list-types` and `get-write-context` for the types; stop and list available types when `types.feature`, `phase` or `task` is missing (S5)
- [X] T016 [US1] Rewrite the parsing step in `preset/commands/speckit.taskstoissues.md` as numbered rules with explicit stop conditions: phase heading `## Phase N: Title`, task line `- [ ] T### [P]? [US#]? text`, optional file hint, dependency sources (explicit statements and Dependencies section only; phase order creates no relations); empty or no-phase file stops without writing; a task outside any phase is reported and the user is asked where to place it (spec edge cases)
- [X] T017 [US1] Define subjects and descriptions in `preset/commands/speckit.taskstoissues.md` per `data-model.md`: feature `<feature-dir-name> <title>` (research R15), phase `Phase N: <title>`, task `T### <headline>` (short headline, see FR-007); description first line `Labels: US1 · parallel` (only present parts), then task text, file hint, repo-relative links to `spec.md`/`plan.md`; no instance URLs, no tokens (FR-013, FR-017)
- [X] T018 [US1] Write the create step in `preset/commands/speckit.taskstoissues.md`: order feature → phases → tasks; `create-work-package` with the parent's work package id as parent; apply `defaults.priority/assignee` only when non-empty (status cannot be set on create); ignore `defaults.version` (FR-004); per-item writes (no bulk, research R10): preview first, require `ready: true` and empty `validation_errors`, then confirm (research R4); a blocked parent blocks its children and is reported as "blocked: parent"
- [X] T019 [US1] Write the ledger step in `preset/commands/speckit.taskstoissues.md` with the embedded block `<!-- BEGIN ledger-rules -->…<!-- END ledger-rules -->` mirroring `schemas/mapping.schema.json`: after **each** confirmed write update `.specify/openproject/mapping-<feature>.json` (schema_version "1.0", project, feature, `items.<key>` with `kind`, `id`, relative `url` path without host); create the file if missing; refuse to overwrite a ledger that violates the rules (FR-005, constitution III)
- [X] T020 [US1] Write the report step in `preset/commands/speckit.taskstoissues.md`: counts created/adopted/skipped/updated/blocked/stale/failed, table key → work package id → relative link, reasons per blocked/failed item (contracts/command-contract.md "Report")
- [X] T021 [US1] Add `tests/test_prompt_sync.py`: (a) the three marker blocks in `preset/commands/speckit.taskstoissues.md` match `docs/mcp-tool-map.md` and `schemas/*.json` (keys, required, enums); (b) prompt steps mention no tool name outside the capability block; (c) `preset/commands/` and `tests/fixtures/` contain no `http://`/`https://` URLs, no token-like strings and no delete capability (FR-012, FR-013); `preset/preset.yml` and `preset/README.md` are excluded because they legitimately carry the public repository URL; the test must fail if a block is edited in only one place

**Checkpoint**: US1 prompt complete; S1 can be tried after T043.

---

## Phase 4: User Story 2 - Safe re-runs and resume (Priority: P1)

**Goal**: Re-run, interrupted run and edited `tasks.md` never duplicate.

**Independent Test**: S2 (re-run: 0 creations) and S3 (interrupt after 5 creations, re-run).

- [X] T022 [US2] Add the planning step in `preset/commands/speckit.taskstoissues.md`: for every parsed item decide `skip` (in ledger and work package still exists), `create`, `adopt`, `stale` or `blocked`; build the plan table (key, kind, subject, parent, action, reason)
- [X] T023 [US2] Add the search-and-adopt rule in `preset/commands/speckit.taskstoissues.md` (FR-007, research R2/R13/R15): `search-work-packages` is a **substring** match, so accept a result only if its subject starts with the item id (tasks) or the full feature directory name (feature) followed by a space **and** its ancestors lead to the feature work package; exactly one match → adopt into the ledger; several matches → report and skip, never guess
- [X] T024 [US2] Add stale-entry handling in `preset/commands/speckit.taskstoissues.md` (research R9): a ledger id with no matching work package (existence check by `search-work-packages`, not `get-work-package`) → action `stale`, reported, not recreated, ledger untouched
- [X] T025 [US2] Add resume semantics in `preset/commands/speckit.taskstoissues.md`: a re-run replans from ledger plus search; new tasks in `tasks.md` are created, existing ones skipped; a tool failure stops the run with the ledger current to the last confirmed write (spec edge case "mid-run failure")
- [X] T026 [US2] Update `docs/TESTING.md`: S1 stays at 14 entries; state exact expectations for S2 (0 created, 14 skipped) and S3 (remaining items created, 0 duplicates; simulate by stopping after the second phase confirmation); add **S8** (`--dry-run` on S1 input: plan with 14 entries, 0 work packages created, ledger file unchanged) and **S9** (change one task title, run without then with `--update`; plus a ledger entry pointing to a non-existent work package → reported as stale, not recreated)

---

## Phase 5: User Story 3 - Preview with dry run (Priority: P1)

**Goal**: `--dry-run` shows the full plan and writes nothing; real runs confirm once per phase.

**Independent Test**: S8 — `--dry-run` on S1 input leaves OpenProject and ledger unchanged (SC-005).

- [X] T027 [US3] Add `--dry-run` handling in `preset/commands/speckit.taskstoissues.md`: after the plan table stop; no write call, no ledger write, no file created (FR-009); the plan shows the same actions the real run would take
- [X] T028 [US3] Add the confirmation protocol in `preset/commands/speckit.taskstoissues.md` (FR-015, contracts/command-contract.md): show the plan, then ask **once per phase** (the feature work package is confirmed together with phase 1); inside a confirmed phase run preview then confirm per item without asking again; any state other than `preview` stops that item with the server message
- [X] T029 [US3] Add the write-permission pre-check in `preset/commands/speckit.taskstoissues.md` (S7, research R6/R11): before the first confirm, run the preview of the first item to create (the feature work package on a first run); a rejected or erroring preview stops the run with a clear message and writes nothing; do not rely on parsing error texts from failed single previews (generic in some clients)

---

## Phase 6: User Story 4 - Dependencies as relations (Priority: P2)

**Goal**: Real dependencies become `follows` relations; `[P]` alone creates none.

**Independent Test**: S4 with `tests/fixtures/tasks/s4-tasks.md`.

- [X] T030 [US4] Add the relation step in `preset/commands/speckit.taskstoissues.md` (research R3, verified 2026-10-05): `create-relation` with the successor as source and the predecessor as related item, type `follows`; skip when `create_relations` is false; no relation between `[P]` tasks without a stated dependency
- [X] T031 [US4] Add relation idempotency in `preset/commands/speckit.taskstoissues.md`: check the ledger `relations` list and `get-relations` of the successor (`predecessor_id`) before creating; append `{from, to, type: "follows", id}` to the ledger after each confirmed relation
- [X] T032 [US4] Add dependency edge cases in `preset/commands/speckit.taskstoissues.md`: unknown task id → report and skip that relation; cycle → report, skip relations on the cycle, create the rest
- [X] T033 [P] [US4] Add `tests/test_tasks_fixtures.py`: parse the headers of `s1-tasks.md`, `s4-tasks.md` and `s-large-tasks.md` with a small helper inside the test file only (no shipped code); assert counts (S1: 3 phases/10 tasks; large: 120 tasks) and that the documented `follows` pairs in `s4-tasks.md` reference existing task ids

---

## Phase 7: User Story 6 - Fail early with clear diagnostics (Priority: P2)

**Goal**: Misconfiguration stops before any write, with a cause.

**Independent Test**: S5 (unknown type), S6 (mandatory custom field), S7 (project not writable).

- [X] T034 [US6] Add the mandatory-field pre-check in `preset/commands/speckit.taskstoissues.md` (research R5/R12): from `get-write-context` read required fields and custom fields; fill only those given in `required_custom_fields`; an unfillable required field blocks that item, names the field, and unaffected items continue (US6 scenario 2)
- [X] T035 [US6] Add the error-presentation rule in `preset/commands/speckit.taskstoissues.md`: report server messages verbatim, no guessed workarounds; show `validation_errors` or per-item `error` text when present

---

## Phase 8: User Story 5 - Update existing work packages (Priority: P3)

**Goal**: `--update` propagates subject/description changes; without it nothing existing is touched.

**Independent Test**: S9.

- [X] T036 [US5] Add change detection in `preset/commands/speckit.taskstoissues.md`: compute a content hash of subject + description source text per item, store it in the ledger `hash`; without `--update` report "differs, not updated" and call no update capability (FR-010)
- [X] T037 [US5] Add the update step in `preset/commands/speckit.taskstoissues.md`: with `--update`, `update-work-package` (subject, description) via preview then confirm; never change status, assignee or time (OpenProject owns those, ARCHITECTURE principle 3); update the ledger `hash` after the confirmed write
- [X] T038 [US5] Verify `update-work-package` live in the sandbox (after T043) and record preview shape and conflict behaviour in `docs/mcp-tool-map.md`; until done, `preset/README.md` labels `--update` as untested (constitution IV)

---

## Phase 9: Polish & Cross-Cutting

- [X] T039 [P] Update `preset/README.md`: paths under `.specify/openproject/`, config keys incl. `types.feature`, per-phase confirmation, `--dry-run`/`--update`, ledger format, limitations (no deletes, stale entries reported, substring search post-filter, per-item writes), list of untested paths (`--update` until T038, 100+ tasks beyond dry-run)
- [X] T040 [P] Update `preset/preset.yml`: bump `version` to `0.2.0`, review `requires.speckit_version` against `.specify/init-options.json` (`speckit_version` 1.1.x) and the constitution's "current and previous minor" rule; `uv run pytest tests/test_manifests.py` must pass
- [X] T041 [P] Update `docs/ARCHITECTURE.md`: remove the "unify paths in feature 001" note, describe the Feature → Phase → Task hierarchy, the ledger `relations` list and the self-contained command (research R14)
- [X] T042 Re-read `preset/commands/speckit.taskstoissues.md` end to end against `contracts/command-contract.md`: numbered steps, explicit stop conditions, capability ids only, works in skills and command mode (hard rules in `CLAUDE.md`); `uv run pytest tests/test_prompt_sync.py` green
- [X] T043 Manual prerequisites for the maintainer (document in `docs/TESTING.md` test-instance setup): (a) delete the `VERIFY-*` work packages 38–40 from the sandbox, (b) types Feature, Summary task, Task are enabled in `speckit-sandbox` (done), (c) create one **mandatory** custom field in the sandbox for S6 and remove it afterwards, (d) start Claude Code with the variables from `.env` exported so the `openproject` MCP server connects
- [X] T044 Run `uv run pytest`, `uv run ruff check . && uv run ruff format --check .`, then `scripts/dev-install.sh`; `specify preset list` shows `openproject` (verification steps 1–2 in `CLAUDE.md`)
- [ ] T045 Execute S1–S9 per `quickstart.md`, always `--dry-run` first; run S1 and S2 in **both** skills mode and command mode (or mark one mode untested); measure the S1 duration for SC-004; run `s-large-tasks.md` as `--dry-run` only; record date, OpenProject version, MCP server version, spec-kit version and result per scenario in `docs/TESTING.md`; report exactly what was executed, mark anything not run as untested
- [X] T046 Fill remaining unverified items in `docs/mcp-tool-map.md` from T038 and T045 (mandatory custom field behaviour, `update-work-package`); `bulk_create_work_packages` stays deferred (research R10)
- [X] T047 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings
- [X] T048 Commit in small Conventional Commits on branch `001-tasks-to-work-packages` (schemas, fixtures/tests, prompt, docs, preset manifest) and open one PR

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → user stories → Phase 9.
- All prompt-editing tasks (T013–T020, T022–T025, T027–T032, T034–T037) edit one file and run **sequentially in the listed order**; story phases build on US1.
- T014 needs T011; T021 needs T013, T014, T019 (all three marker blocks).
- US1 (P1) is the base; US2 and US3 (both P1) extend the same prompt; then US4, US6 (P2), US5 (P3). T034 needs T015.
- Live tasks (T038, T045) need T043 done and a connected MCP server.

## Parallel Opportunities

- T002 ∥ T003 ∥ T004 (fixtures); T007 ∥ T008 ∥ T011 after T005/T006.
- T033 anytime after T002–T004.
- T039 ∥ T040 ∥ T041.

## Implementation Strategy

1. MVP: Phases 1–3 (US1), then run S1 with `--dry-run` and one real run.
2. Add US2 + US3 (still P1) before any use outside the sandbox: without idempotency and dry-run the command is not safe (constitution III).
3. Then US4, US6, US5, polish and the full S1–S9 run.
