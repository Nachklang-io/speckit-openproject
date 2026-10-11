---

description: "Task list for feature 008: taskstoissues hardening (preset 1.0.3)"
---

# Tasks: taskstoissues Hardening

**Input**: Design documents from `specs/008-taskstoissues-hardening/`

**Prerequisites**: plan.md, spec.md (FR-001–FR-012, SC-001–SC-005), research.md (R1–R5), data-model.md, contracts/command-contract.md, quickstart.md

**Tests**: Requested. Constitution principle IV requires prompt-sync tests and executed prompt scenarios (S-large, S-plan, S7b in `docs/TESTING.md`). Write each test before the prompt edit it covers and see it fail.

**Organization**: Grouped by user story. The behaviour change is one Markdown prompt (`preset/commands/speckit.taskstoissues.md`), so prompt-editing tasks touch the same file and are **not** `[P]`. Tests are added to `tests/test_prompt_sync.py` one by one (same file, not `[P]` among themselves).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US4 as numbered in `spec.md` (US1 plan rows #23, US2 read-only role #22, US3 missing plan.md #21, US4 generic note #20)
- The prompt is self-contained and refers to OpenProject only by capability id. Two read capabilities are new: `get-my-access` and `get-capability` (research R1). Never print the `url` field of a capability result.
- Tasks marked **(maintainer)** need the sandbox instance or an admin action; they are never claimed done without an executed run. Report what was actually executed.
- Versions: preset 1.0.3 and the bundle pin move in the release PR (as for 007), not here. This feature adds items under "Unreleased" in `CHANGELOG.md` only.

## Path Conventions

Monorepo: `preset/`, `docs/`, `tests/`, root `README.md`. `extension/` and `schemas/` are not touched.

---

## Phase 1: Setup

- [ ] T001 Baseline: `uv run pytest && uv run ruff check . && uv run ruff format --check .` pass on branch `008-taskstoissues-hardening`; confirm `tests/fixtures/tasks/s-large-tasks.md` has 120 tasks (`grep -c '^- \[' tests/fixtures/tasks/s-large-tasks.md`)

---

## Phase 2: Foundational (capability map)

**Purpose**: the two new capabilities exist in the single map before any prompt step uses them

- [ ] T002 Add two rows to `docs/mcp-tool-map.md` directly after `list-projects`: `get-my-access` (`get_my_project_access`, parameters `project`, verified `yes (admin role)`) and `get-capability` (`list_capabilities`, parameters `project, capability_id`, verified `yes (allowed and unknown principal); denied case for a real read-only role: no`), matching the table in `contracts/command-contract.md`
- [ ] T003 Copy the same two rows, in the same order, into the `capability-map` block of `preset/commands/speckit.taskstoissues.md`; `uv run pytest tests/test_prompt_sync.py` passes (rows identical to the tool map, order kept, no tool name outside the block) (depends on T002)

**Checkpoint**: tool map and prompt agree; no step uses the new capabilities yet.

---

## Phase 3: User Story 1 - Read the full plan of a large feature (Priority: P1) 🎯 MVP

**Goal**: one plan row per key with `hash` and `stored`, no ranges, parts of at most 40 rows (FR-001–FR-003, SC-001).

**Independent Test**: `--dry-run` on the 120-task fixture prints 120 task rows plus phases and the feature, each with both hash cells.

- [ ] T004 [US1] Add a failing test to `tests/test_prompt_sync.py`: the plan step of the preset prompt names the columns `hash` and `stored`, forbids ranges, `…` and "and N more", and requires parts of at most 40 rows with `part i of n` (depends on T003)
- [ ] T005 [US1] Edit step 9 of `preset/commands/speckit.taskstoissues.md` per `contracts/command-contract.md` ("Step 9"): table columns key, kind, subject, parent key, action, hash, stored, reason; hash cells are the first 12 hex characters of the hash computed by the step 7 shell command (current) and of the ledger hash (`—` without an entry); one row per key; long plans in parts; the counts line follows the last part; T004 passes (depends on T004)
- [ ] T006 [US1] **(maintainer or headless sandbox run, `--dry-run` only)** Run scenario S-large through the installed skill (`scripts/dev-install.sh`, `tasks.md` = the 120-task fixture, placeholder `plan.md`): count the rows, check the hash cells and the parts; record the result (depends on T005, T015)

**Checkpoint**: US1 delivers readable plans; MVP.

---

## Phase 4: User Story 2 - Understand why a read-only role stops (Priority: P1)

**Goal**: a role without `work_packages/create` stops before any write with a "missing write permission" message (FR-004–FR-006, SC-002).

**Independent Test**: with a read-only user, `--dry-run` stops with the permission message, no types message, nothing written.

- [ ] T007 [US2] Add a failing test to `tests/test_prompt_sync.py`: step 5 calls `get-my-access` and `get-capability` before `list-types`, builds the id `work_packages/create/w<project_id>-<current_user_id>`, stops only on `[not_found]` with the message of the contract, treats every other error as a tool error, never prints the `url` field, and says the check runs in `--dry-run` too (depends on T003)
- [ ] T008 [US2] Edit step 5 of `preset/commands/speckit.taskstoissues.md` per `contracts/command-contract.md` ("Step 5"): new sub-step between project selection and `list-types`; wording of the stop message exactly as in the contract; the "missing type" message stays unchanged and applies only after the check passed; T007 passes (depends on T007, T005 because both edit the same file)
- [ ] T009 [US2] **(maintainer; needs a read-only role for the sandbox user in the web UI)** Run S7b: `--dry-run` with the read-only user, expect the permission message and no write; restore the role afterwards. Then run the allowed case (S1 or S2 with the write role) through the changed prompt and expect the same result as before. If the read-only run is not possible, record the denied case as untested in `docs/TESTING.md` and the CHANGELOG entry (research R2) (depends on T008, T015)

**Checkpoint**: US2 reports the right reason; the allowed case is unchanged.

---

## Phase 5: User Story 3 - Be told when plan.md is missing (Priority: P2)

**Goal**: a non-zero exit of the prerequisite script is reported with the missing file and the command for the current mode (FR-007, FR-008, SC-003).

**Independent Test**: a feature directory without `plan.md` stops with the script's message and `Missing: plan.md. Run /speckit-plan first.`, nothing written.

- [ ] T010 [US3] Add a failing test to `tests/test_prompt_sync.py`: step 1 prints the script's message verbatim on a non-zero exit, names the missing file (`plan.md` or `tasks.md` as the script reports it) and the command for skills mode and command mode for both files (`/speckit-plan`, `/speckit.plan`, `/speckit-tasks`, `/speckit.tasks`) (depends on T008)
- [ ] T011 [US3] Edit step 1 of `preset/commands/speckit.taskstoissues.md` per `contracts/command-contract.md` ("Step 1"): replace the "If `tasks.md` is missing" sentence by the explicit non-zero-exit handling; the existing `tasks.md` wording keeps its content; T010 passes (depends on T010)
- [ ] T012 [US3] **(headless sandbox run, no OpenProject call needed)** Run S-plan: delete `plan.md` from a scratch feature directory, run the installed skill; then restore `plan.md` and delete `tasks.md`. Expect the messages of the contract and no write; record (depends on T011, T015)

**Checkpoint**: US3 gives a specific stop message for both files.

---

## Phase 6: User Story 4 - Know that the generic integration gets no override (Priority: P3)

**Goal**: both READMEs state the limitation (FR-009, SC-004).

**Independent Test**: read both READMEs.

- [ ] T013 [P] [US4] Add the `generic` note to `README.md` (installation section) and `preset/README.md` (installation section): spec-kit registers no preset command overrides for the `generic` integration, so `/speckit.taskstoissues` stays the core command there; say what to do instead and how to check (`specify preset list`, the command output); name the spec-kit version where it was observed (see `docs/TESTING.md`, run log 2026-10-09)
- [ ] T014 [US4] Add a test to `tests/test_prompt_sync.py` (or the README test module if one exists) that both READMEs contain the sentence about the `generic` integration (depends on T013)

**Checkpoint**: all four stories implemented.

---

## Phase 7: Polish & Cross-Cutting

- [ ] T015 Add the scenarios S-large, S-plan and S7b to the scenario table in `docs/TESTING.md` (steps, expected result, status "not run" until T006, T009, T012) and extend the "Untested" list (depends on T005, T008, T011)
- [ ] T016 [P] Add `### Unreleased` items for the preset to `CHANGELOG.md` under "Planned as 1.0.3": `#### Fixed` for the plan rows (#23), the permission message (#22) and the missing-file message (#21); `#### Changed` or a note for the two new read capabilities and the README note (#20); keep the denied case labelled untested if S7b did not run
- [ ] T017 Record the executed runs (T006, T009, T012) in the run log of `docs/TESTING.md`: what was actually executed, what was not; update the scenario statuses and the "Untested" list (depends on T006, T009, T012)
- [ ] T018 Verification before done: `uv run pytest && uv run ruff check . && uv run ruff format --check .`; `scripts/dev-install.sh` installs both packages and `specify preset list` / `specify extension list` show them; run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff and fix or record their findings (depends on T016, T017)
- [ ] T019 Open the PR `feat(preset): harden taskstoissues (plan rows, permission and missing file messages)` with the executed and unexecuted scenarios listed; add `docs/ROADMAP.md` row 008 (depends on T018)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → US2 → US3 (all three edit the one prompt, so they run in this order) → US4 (independent files, may run beside any story) → Polish.
- T015 (scenario rows) comes before the live runs T006, T009, T012, because the runs fill them in.
- Maintainer runs: T006 (dry run only), T009 (admin action for the read-only role), T012 (no OpenProject needed).

## Parallel Opportunities

- T013 beside T004–T012 (different files); T016 beside T015.

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): plans become readable. Then US2, US3, US4, Polish. Do not write code before `/speckit-analyze` is clean.
- Prompt changes are small; each is test-first.

## Notes

- Success criteria map to tasks: SC-001 → T005, T006; SC-002 → T008, T009; SC-003 → T011, T012; SC-004 → T013, T014; SC-005 → T009 (allowed case), T018.
- The denied case of the capability check is unverified until S7b (research R1, R2) and stays labelled in `docs/TESTING.md` and the CHANGELOG.
