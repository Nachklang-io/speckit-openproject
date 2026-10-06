---

description: "Task list for feature 003: status sync between OpenProject and tasks.md"
---

# Tasks: Status Sync between OpenProject and tasks.md

**Input**: Design documents from `specs/003-status-sync/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R9, Unresolved), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution principle IV requires schema, sync and decision-table tests and executed prompt scenarios (S14–S17 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The shipped runtime is one Markdown prompt (`extension/commands/sync-status.md`), so prompt-editing tasks touch the same file and are **not** marked `[P]`; they build the prompt up section by section. Tasks that edit `tests/test_prompt_sync.py` are likewise sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US5 as numbered in `spec.md` (US1 pull, US2 push, US3 both sides, US4 preview and safe writes, US5 hook)
- The installed command is self-contained: it uses **capability ids only**; concrete tool names appear once, in the capability rows embedded in the prompt (constitution II). Embedded blocks: `capability-map`, `config-rules`, `ledger-rules`, `decision-table`.
- Tasks marked **(maintainer)** need the maintainer's test instance or an admin action; they are never claimed done without an executed run. This project never deletes work packages; the maintainer removes test work packages by hand.

## Path Conventions

Monorepo: `extension/`, `preset/`, `schemas/`, `tests/`, `docs/`. `preset/` is touched only for the additive `assignee` ledger key and the updated `update-work-package` row (plan, research R6, R8).

---

## Phase 1: Setup (live facts and fixtures)

- [ ] T001 **(maintainer, run from the main session)** Close research "Unresolved" 2 against the sandbox (part a; part b is T001b): publish `tests/fixtures/tasks/s1-tasks.md` as feature `001-sandbox-demo` in `.scratch/proj` (`taskstoissues`, `--dry-run` first), then read one task work package with `get_work_package` (record the exact fields for status name/id and assignee, also for an unassigned and an assigned one) and `list_statuses`; record the `update_work_package` **preview** with `status` for an allowed transition (no `confirm=true`). Save the responses as secret-free fixtures `tests/fixtures/sync/wp-unassigned.json`, `wp-assigned.json`, `preview-allowed.json` (paths only, no host, no token) plus `tests/fixtures/sync/README.md` (which files are recorded, date, OpenProject version). Record the result in `docs/mcp-tool-map.md` (verified parameters) and research "Unresolved"
- [ ] T001b **(maintainer; admin action in the web UI)** Close research "Unresolved" 1: set up a restricted workflow for type Task (New must not go to Closed), then record the `update_work_package` **preview** with `status` for the forbidden transition (no `confirm=true`) as `tests/fixtures/sync/preview-forbidden.json` and note the result in research R4; if the preview is **not** rejected, adapt T018. Blocks only T018 and T021 (depends on T001)
- [ ] T002 [P] Add `assignee` to `schemas/mapping.schema.json` exactly as in `contracts/schema-changes.md`: `{"type": "string", "minLength": 1}` in the item properties; do not change `required` or `additionalProperties`
- [ ] T003 [P] Add ledger fixtures `tests/fixtures/mapping/valid-with-assignee.json` (items with `status` and `assignee`), `invalid-assignee-type.json` (`"assignee": 7`) and `invalid-assignee-empty.json` (`"assignee": ""`)

---

## Phase 2: Foundational (blocks all stories)

**Purpose**: schema, tool map, decision table with tests, prompt frame and manifest. No story can be written before the table and the frame exist.

- [ ] T004 Extend `tests/test_schemas.py`: `valid-with-assignee` validates, both invalid fixtures are rejected, every ledger fixture that was valid before is still valid (depends on T002, T003)
- [ ] T005 Update `docs/mcp-tool-map.md`: parameters of `update-work-package` become `work_package_id, subject, description, status, confirm`; re-embed the changed row into `preset/commands/speckit.taskstoissues.md` (it embeds this row; the identity test must pass); `extension/commands/discover-fields.md` does not embed it and stays unchanged; bump `preset/preset.yml` patch version (depends on T001)
- [ ] T006 Add `assignee` to the `ledger-rules` block of `preset/commands/speckit.taskstoissues.md`: `- ledger item keys: assignee, hash, id, kind, status, url` and `assignee is a non-empty string` in the value types line; the preset never writes it (depends on T002)
- [ ] T007 [P] Add `tests/sync_reference.py`: a reference implementation of the decision table of research R1 (`classify(checked, op_status, base, done, closed_statuses)` → action, labels) and of the checkbox edit rule of R5 (`apply_checkbox_edits(text, edits)`); a header comment states that it mirrors the `decision-table` block of the prompt and is used only by tests
- [ ] T008 Add `tests/fixtures/sync/decision-table.json`: one case per row of research R1 plus baseline (checked/open, done/not done), reverted, closed-not-done with a checked box, in progress, identical on both sides, conflict both directions, and a case each for `unpublished`, `stale`, `orphan`; expected action, labels and new ledger status (depends on T007)
- [ ] T009 Add `tests/test_sync_decision.py`: every case of T008 gives the expected result; applying a result and classifying again yields `none` for every task (idempotence, SC-002); a baseline case never yields `conflict`; `apply_checkbox_edits` changes only bracket characters, keeps `X` when the box stays checked, leaves lines with other keys, text in descriptions and trailing whitespace untouched (SC-005), and fails on a repeated key (depends on T008)
- [ ] T010 Extend `tests/test_prompt_sync.py` for `extension/commands/sync-status.md`: join the parametrized prompts (capability subset in table order, no tool name outside the block, `config-rules` match the schema); `ledger-rules` match `schemas/mapping.schema.json`; the `decision-table` block lists exactly the rows of `tests/sync_reference.py` (red until T011 exists, by design: test first); the capability block contains no `create`, `delete` row; `delete_` does not appear; the prompt contains `<user-content>`, `untrusted data`, "Every run starts from scratch", `Dry run: nothing was written.`, `<redacted-host>`, `<redacted-secret>` and the five result words (depends on T007)
- [ ] T011 Create `extension/commands/sync-status.md` with the frame: frontmatter (`description`, `argument-hint: "[feature] [--dry-run]"`, `tools: ['openproject-ce-mcp/*']`), `## User Input`, the arguments sentence, the pre-execution note (no hook check, as in 002, unless the hook key was verified), the embedded `capability-map` block (rows `list-statuses`, `get-work-package`, `get-write-context`, `update-work-package`, copied from `docs/mcp-tool-map.md`), failure classes (rejected, tool error with generic text and redaction, not found), the `config-rules` and `ledger-rules` blocks, the `decision-table` block (rows of research R1 with the overrides) and the statement of the hard limits of `contracts/command-contract.md` (depends on T005, T006, T009, T010)
- [ ] T012 Register the command in `extension/extension.yml`: version 0.0.3, `provides.commands` entry `speckit.openproject.sync-status` (`commands/sync-status.md`, description from the contract); add `hooks.after_implement` in T029 only (depends on T011)

**Checkpoint**: `uv run pytest` is green; the prompt has a frame but no steps yet.

---

## Phase 3: User Story 1 - Pull progress from OpenProject into tasks.md (Priority: P1) MVP

**Goal**: done/reopened/in-progress work packages update checkboxes and the ledger; assignee is recorded.

**Independent Test**: S14 pull part: T002 closed, T003 in progress in OpenProject; only T002 is checked, ledger has both statuses and the assignee, nothing else in `tasks.md` changes.

- [ ] T013 [US1] Add steps 1–6 of `contracts/command-contract.md` to the prompt: "Every run starts from scratch"; arguments (`[feature] [--dry-run]`, any other flag stops); capability check naming the missing capability id; read and validate the config (`statuses.done` required, stop naming `speckit.openproject.discover-fields`); resolve the feature directory; read and validate the ledger (`project` and `feature` match; stop naming the file; never rebuild) and `tasks.md` (task keys unique); remember the `tasks.md` content; read `list-statuses` and check the `statuses.*` names with `get-write-context` (stop naming the status, never guess another); one `get-work-package` per ledger task item for status name and assignee; `feature` and `phase` items are read for the report only (depends on T011)
- [ ] T014 [US1] Add the classification to the prompt (step 6): apply the `decision-table` block row by row with the overrides (closed-not-done is informational and never pushes or changes the box; `unpublished`, `stale`, `orphan`; status not representable in `tasks.md` like "In progress" refreshes the ledger and is shown as "in progress"); untrusted server text rule (strip `<user-content>`, compare only) (depends on T013)
- [ ] T015 [US1] Add the pull path to the prompt (steps 12–13): after confirmation re-read `tasks.md`; apply the checkbox edits of research R5 (regex `^(\s*)- \[( |x|X)\] (T\d{3,})\b`, only the bracket character, via `tasks.md.tmp`, read back, verify that only the planned characters differ, move); then write the ledger (`status` and `assignee` for all processed items) through `mapping-<feature>.json.tmp` and a move; a pull enters the ledger only after the `tasks.md` write succeeded (depends on T014)
- [ ] T016 [US1] Define scenario S14 in `docs/TESTING.md` (pull part first, push part after T020) with a results table, and the intro "Scenarios S14–S17" naming the installed-skill method and the setup of `quickstart.md` (depends on T015)
- [ ] T017 [US1] **(maintainer)** Run S14 pull part through the installed skill in `.scratch/proj` (`scripts/dev-install.sh` first), `--dry-run` first, then for real; also one dry run in command mode (`/speckit.openproject.sync-status`, FR-017), labelled untested in `docs/TESTING.md` if it could not be run; compare `tasks.md` with `git diff --no-index` (one bracket character per change) and check the ledger; record what was executed in `docs/TESTING.md` (depends on T012, T016)

**Checkpoint**: US1 works alone: OpenProject progress reaches `tasks.md` and the ledger.

---

## Phase 4: User Story 2 - Push completed tasks to OpenProject (Priority: P1)

**Goal**: checked tasks move their work package to the done status, only where the server accepts it; blocked otherwise.

**Independent Test**: S14 push part and S16 (restricted workflow).

- [ ] T018 [US2] Add the push preview to the prompt (step 7): for each push candidate call `update-work-package` with `status` = `statuses.done` **without** `confirm`; `state: preview`/`ready: true` → keep; `state: rejected` or non-empty `validation_errors` → `blocked` with the errors verbatim (redacted); a tool error on the preview → `blocked` with the redacted text; list the statuses available for the task type from `get-write-context` and say that this set is for the type; never call with `confirm=true` for a blocked item (depends on T014, T001b)
- [ ] T019 [US2] Add the push write to the prompt (step 11): after the single confirmation call `update-work-package` with `confirm=true` for each push item; after each success write the ledger (`status` = `statuses.done`, `assignee`) before the next item; on failure record the redacted error, mark the item `failed` and continue; never reopen a work package, never change subject, description, type, assignee or time (depends on T018, T015)
- [ ] T020 [US2] Add the push part to S14 and define S16 (restricted workflow, blocked task, `incomplete`) in `docs/TESTING.md` (depends on T019)
- [ ] T021 [US2] **(maintainer)** Run S14 push part and S16 through the installed skill; also the case "forbidden transition" with the workflow of T001; record whether the preview rejected it (research R4); a failed confirm of a single task is a finding to record, not skipped (depends on T017, T020, T001b)

---

## Phase 5: User Story 3 - Deterministic handling of changes on both sides (Priority: P1)

**Goal**: one-sided changes pull or push, conflicts resolve to OpenProject, baseline never conflicts, reverted tasks are re-checked, a second run changes nothing.

**Independent Test**: S15.

- [ ] T022 [US3] Add the conflict, baseline and reverted handling to the prompt: report format `T012: tasks.md [x] overwritten by OpenProject "In progress" (open)` for every conflict, labels `baseline` and `reverted` in the plan table, no question per conflict, same plan for the same input; check against `tests/fixtures/sync/decision-table.json` that the prompt block lists the same rows (depends on T019, T009)
- [ ] T023 [US3] Define scenario S15 in `docs/TESTING.md` (T004 pushed, T005 pulled, T006 conflict, T001 reverted, second run `no changes`) (depends on T022)
- [ ] T024 [US3] **(maintainer)** Run S15 through the installed skill after S14; run the second time and confirm `no changes` with checksums of `tasks.md` and the ledger unchanged (SC-002); record the results (depends on T021, T023)

---

## Phase 6: User Story 4 - Preview, safe writes and an honest report (Priority: P2)

**Goal**: plan table and `--dry-run`, one confirmation, atomic writes, concurrent edit protection, report with counts and result.

**Independent Test**: S17 and the dry-run comparisons of S14/S15.

- [ ] T025 [US4] Add the plan and the dry run to the prompt (steps 8–10): the plan table with columns `Key | WP | tasks.md | OpenProject | Last synced | Action | Reason` sorted by task key, the counts line, `Dry run: nothing was written.` and stop with `--dry-run` (no temporary file either); nothing to write (no push, pull or ledger refresh) → report `no changes` without a question; a plan with only ledger refreshes still needs the one confirmation and ends `complete`; otherwise one confirmation for the whole plan (`yes`/`no`; `no` or no answer stops with `stopped`) (depends on T019)
- [ ] T026 [US4] Add the report (step 14) and the stop conditions: counts per outcome, changed items, warnings, one result word (`complete`, `incomplete`, `no changes`, `dry run`, `stopped`) with the rules of research R9; `tasks.md` changed between read and write → no write, pulls `skipped`, tell the user to run again; MCP server not connected and unreadable project → a specific message, nothing written; errors printed with URLs and hosts replaced (depends on T025)
- [ ] T027 [US4] Define scenario S17 (missing `statuses.done`, missing ledger, MCP server not started, `tasks.md` edited between plan and write) in `docs/TESTING.md` and add the dry-run checksum checks (SC-003: the plan of the dry run equals the plan of the following real run) to S14 and S15 (depends on T026)
- [ ] T028 [US4] **(maintainer)** Run S17 through the installed skill (for the MCP case start Claude Code without the exported `.env`; for the edit case change `tasks.md` from a second terminal while the confirmation is pending); record results; time one 14-work-package run (SC-004: one confirmation, under 3 minutes) (depends on T024, T027)

---

## Phase 7: User Story 5 - Optional hook after implement (Priority: P3)

**Goal**: `/speckit-implement` offers the sync, never runs it unasked.

**Independent Test**: S16 hook part.

- [ ] T029 [US5] Add `hooks.after_implement` to `extension/extension.yml`: `command: speckit.openproject.sync-status`, `optional: true`, `description`, `prompt` (text offering the sync and naming `--dry-run`; check that `specify extension add --dev` accepts the `prompt` key, otherwise omit it and rely on `description`); extend `tests/test_manifests.py`: every `hooks.*.command` is a command provided by the extension and `optional` is `true` (depends on T012)
- [ ] T030 [US5] **(maintainer)** In `.scratch/proj` run `scripts/dev-install.sh`, check that `.specify/extensions.yml` contains the hook, finish a `/speckit-implement` run (or the smallest run that reaches the end) and see whether the optional offer appears; decline it and confirm nothing was read or written; record the result and label the hook untested if it did not appear (research R7) (depends on T029)

---

## Phase 8: Polish & Cross-Cutting

- [ ] T031 [P] Update `extension/README.md`: usage and arguments, what it reads and writes (checkbox characters, ledger), the decision table in plain words, OpenProject wins, blocked and "closed, not done" explained, the hook, limitations and untested paths
- [ ] T032 [P] Update `docs/ARCHITECTURE.md`: sync policy (spec-kit owns structure, OpenProject owns status and assignee, conflicts to OpenProject), `assignee` in the ledger, `sync-status` in the component diagram
- [ ] T033 Update `docs/TESTING.md` results and "Untested after feature 003": command mode, transition preview (if not verified), hook, list of what was not executed (depends on T017, T021, T024, T028, T030)
- [ ] T034 Run `scripts/dev-install.sh`; confirm `specify preset list` and `specify extension list` show `openproject` in both and that `.claude/skills/speckit-openproject-sync-status` exists in the scratch project (depends on T012, T029)
- [ ] T035 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all green (depends on T034)
- [ ] T036 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings or record the reason for not fixing; rerun once after the last prompt change (depends on T035)
- [ ] T037 Mark finished tasks in this file, update `specs/003-status-sync/checklists/requirements.md` if scope changed, prepare the PR description (summary, executed scenarios, untested paths); retarget onto `main` after PR #4 (feature 002) is merged (`git rebase --onto main 002-field-discovery 003-status-sync`); opening the PR is the maintainer's call (depends on T033, T036)

---

## Dependencies & Execution Order

- Phase 1 (T001b only blocks T018, T021) → Phase 2 → US1 → US2 → US3 (US2 builds on the prompt steps of US1; US3 needs both) → US4 (plan and report wrap the earlier steps) → US5 (independent of US2–US4 apart from T012, can run in parallel with US4) → Polish.
- Within the prompt, tasks T013–T015, T018–T019, T022, T025–T026 are sequential edits of one file.
- Maintainer runs (T001, T001b, T017, T021, T024, T028, T030) need the sandbox; T017 can only start after T012, T021 needs the workflow of T001.

## Parallel Opportunities

- T002 and T003; T007 beside T004–T006; T031 and T032 beside any maintainer run; T029 beside T025–T026.

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): pull works and is safe (no OpenProject write yet).
- Then US2 (push), US3 (round trip), US4 (preview, report, stop conditions); US5 last. Do not open the PR before feature 002 is merged and `/speckit-analyze` is clean.
