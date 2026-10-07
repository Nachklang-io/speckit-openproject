---

description: "Task list for feature 005: versions and time tracking"
---

# Tasks: Versions and Time Tracking

**Input**: Design documents from `specs/005-versions-and-time/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R10), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution principle IV requires schema, decision-table, parser and key tests and executed prompt scenarios (S22–S25 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The shipped runtime is two Markdown prompts (`extension/commands/sync-version.md`, `extension/commands/log-time.md`). Edits of one prompt are sequential and **not** marked `[P]`; the two prompts are independent of each other, so US1 and US2 prompt work may run in parallel. Tasks that edit `tests/test_prompt_sync.py` or `docs/TESTING.md` are sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US4 as numbered in `spec.md` (US1 map a feature to a version, US2 log time, US3 preview and safe writes, US4 clear stops)
- Prompts are self-contained: they use **capability ids only**; concrete tool names appear once per prompt, in the capability rows embedded from `docs/mcp-tool-map.md` (constitution II). Embedded blocks per prompt: `capability-map`, `config-rules`, `ledger-rules`; plus `decision-table` (sync-version) and `duration-grammar` (log-time).
- Tasks marked **(maintainer)** need the maintainer's test instance or an admin action; they are never claimed done without an executed run. This project deletes nothing; the maintainer removes test versions, work packages and time entries by hand.

## Path Conventions

Monorepo: `extension/`, `preset/`, `schemas/`, `tests/`, `docs/`. `preset/` and the existing extension prompts are touched only for the additive rule lines (new optional ledger keys `version`, `time_entries`, config key `defaults.activity`).

---

## Phase 1: Setup (live facts, schemas)

- [x] T001 **(maintainer, run from the main session)** Task 0 of the plan, closes research R1 against the sandbox: with a scratch work package `VERIFY-005 ...` record (a) the tool list of the MCP server: is `create_time_entry` present, and which environment flag enables time-entry writes (read the server's documentation or instructions, do not read `.env`); (b) `create_version` preview and confirm for `VERIFY-005` (id field of the confirm result, `sharing` and `status` defaults), `list_versions(project, search)` result and paging, `get_version` fields (status); (c) `get_work_package` with `select` including the version: field name and whether it holds a name or an id; (d) `bulk_update_work_packages` with `items[{work_package_id, version}]` preview and confirm (per-item result shape, partial failure) and `update_work_package(version=...)` as fallback; behaviour for a work package that already has another version; closed or locked version rejection; (e) `list_time_entry_activities` result fields (name, id, project scope); (f) `create_time_entry` preview and confirm for 30 minutes (`PT30M`) on the scratch work package (result id field, `activity` by name, an unknown activity, project without time tracking); (g) fallbacks if anything differs. Save secret-free responses under `tests/fixtures/version/` and `tests/fixtures/time/` (`README.md` with date and versions), update `research.md` (R1, R4, R7) and `docs/mcp-tool-map.md` ("Verified" column, parameters). Blocks the prompt frames T011 and T012
- [x] T002 [P] Add `version` and `time_entries` to `schemas/mapping.schema.json` exactly as in `contracts/schema-changes.md` (top-level optional; `version`: `id` integer, minimum 1, `name` string, minLength 1, both required, `additionalProperties: false`; `time_entries`: array of objects with required `key` (string, minLength 1), `work_package_id` (integer, minimum 1), `spent_on` (pattern `^\d{4}-\d{2}-\d{2}$`), `activity` (string, minLength 1), `hours` (pattern `^PT(\d+H)?(\d+M)?$`), `id` (integer, minimum 1), optional `entry_key` (string, minLength 1), `additionalProperties: false`); do not change top-level `required` or `schema_version`
- [x] T003 [P] Add `defaults.activity` (`{"type": "string", "minLength": 1}`, `$comment`: read by `log-time`, ignored by the other commands) to `schemas/config.schema.json` and extend the `$comment` of `defaults.version` ("also the version name for sync-version"); no key renamed or removed
- [x] T004 [P] Add ledger fixtures under `tests/fixtures/mapping/`: `valid-with-version-and-time.json` (feature item, `version`, two `time_entries` of which one has `entry_key`), `invalid-version-missing-id.json`, `invalid-time-hours.json` (`1h30`), `invalid-time-missing-id.json`, `invalid-time-date.json`; and a config fixture with `defaults.activity` under `tests/fixtures/config/`

---

## Phase 2: Foundational (blocks all stories)

**Purpose**: schema tests, tool map, rule lines in all prompts, reference implementation with tests, prompt frames and manifest.

- [x] T005 Extend `tests/test_schemas.py`: `valid-with-version-and-time` validates, the four invalid ledger fixtures are rejected, the config fixture with `defaults.activity` validates and an empty `activity` is rejected, every fixture that was valid before is still valid (depends on T002, T003, T004)
- [x] T006 Update `docs/mcp-tool-map.md`: add rows `list-versions`, `get-version`, `create-version`, `bulk-update-work-packages` (fallback uses the existing `update-work-package` row, extended with `version`), `list-time-activities`, `create-time-entry` with the parameters recorded in T001; "Verified" = yes only for what T001 ran (depends on T001)
- [x] T007 Add the new keys to the `ledger-rules` block (top-level `version`, `time_entries`; one line each) and to the `config-rules` block (`defaults.activity`) in `preset/commands/speckit.taskstoissues.md`, `extension/commands/sync-status.md` and `extension/commands/sync-docs.md`; none of them writes the keys; bump the `preset/preset.yml` patch version; `extension/extension.yml` is bumped in T013 (depends on T002, T003)
- [x] T008 [P] Add `tests/version_time_reference.py`: reference implementations of (a) the version decision tables of research R3 (`classify_version(ledger_version, matches, status)` → action, writes; `classify_work_package(wp_version, version_id, exists)` → action), (b) the duration parser of R5 (`parse_line(text, today)` → `{key, minutes, date}` or a rejection reason; `to_iso(minutes)` → `PT1H30M`, `PT45M`, `PT2H`), (c) the time-entry key of R6 (`entry_key(work_package_id, spent_on, activity, iso, entry_key=None)`) and the plan classification (`classify_time(item, ledger_time_entries)` → create, unchanged, unknown, rejected, stale); a header comment states that it mirrors the `decision-table` and `duration-grammar` blocks of the prompts and is used only by tests
- [x] T009 Add fixtures `tests/fixtures/version/decision-table.json` (one case per row of research R3 for the version and per work package, plus a version whose name differs from the ledger name, several matches, closed version, stale ledger version) and `tests/fixtures/time/durations.json` (accepted: `1h30`, `1h30m`, `1:30`, `90m`, `45m`, `1.5h`, `2h`; rejected: `0m`, `-1h`, `25h`, `1.505h`, `abc`, empty, date `2026-13-01`, date in the future, date `07.10.2026`) and `plan-*.json` (key present → unchanged, `--entry-key` given for one item, `--entry-key` with two items → stop, unknown task key, `#<id>` in and not in the ledger) with expected results (depends on T008)
- [x] T010 Add `tests/test_version_decision.py` and `tests/test_time_entries.py`: every case of T009 gives the expected result; applying a result and classifying again yields `unchanged` for every item (idempotence, SC-002); the same line with a different activity or date is a different key; an entry key replaces the computed key; `to_iso` output matches the ledger schema pattern for all accepted durations (depends on T009)
- [x] T011 Extend `tests/test_prompt_sync.py` for the two new prompts: join the parametrized prompts (capability subset in table order, no tool name outside the block, `config-rules` match the schema, `ledger-rules` identical to the other prompts and to `schemas/mapping.schema.json`); the `decision-table` block lists exactly the rows of `tests/version_time_reference.py`; the `duration-grammar` block lists the accepted and rejected forms of T009; neither capability block contains a delete row, `create-work-package`, `delete-version` or `update-version`; both prompts contain `untrusted data`, `Dry run: nothing was written.`, `<redacted-host>`, `<redacted-secret>` and the five result words (red until T012 and T016 exist, by design: test first) (depends on T008)
- [ ] T012 Create the frames of both prompts: `extension/commands/sync-version.md` (frontmatter `description`, `argument-hint: "[feature] [--version <name>] [--dry-run]"`, `tools: ['openproject-ce-mcp/*']`; `capability-map` rows `list-versions`, `get-version`, `create-version`, `get-work-package`, `bulk-update-work-packages`, `update-work-package`; failure classes; `config-rules`, `ledger-rules`, `decision-table`) and `extension/commands/log-time.md` (`argument-hint: "[feature] [--activity <name>] [--entry-key <key>] [--dry-run] [lines]"`; rows `list-time-activities`, `create-time-entry`, `get-work-package`; failure classes; `config-rules`, `ledger-rules`, `duration-grammar`), each with the hard limits of `contracts/command-contract.md` (depends on T001, T006, T007, T010, T011)
- [ ] T013 Register both commands in `extension/extension.yml`: version 0.0.4 → 0.0.5, `provides.commands` entries `speckit.openproject.sync-version` (`commands/sync-version.md`) and `speckit.openproject.log-time` (`commands/log-time.md`) with the descriptions from the contract, no hook (depends on T012)

**Checkpoint**: `uv run pytest` is green; both prompts have a frame but no steps yet.

---

## Phase 3: User Story 1 - Map a feature to a version (Priority: P1) MVP

**Goal**: one version for the feature exists, all ledger work packages that have no version carry it, the ledger records the version.

**Independent Test**: S22: first run creates one version and assigns all work packages; second run `no changes`; a work package in another version is reported untouched.

- [ ] T014 [US1] In `extension/commands/sync-version.md` write steps 1–4: arguments and feature resolution, read config (`project`, `defaults.version`) and ledger (`items`, `version`), stop naming the file when missing or invalid; resolve the intended version name (R2: `--version`, `defaults.version`, feature directory name); `list-versions` with the name as search, post-filter for the exact name, `get-version` for the chosen id (status); `get-work-package` per ledger item with `select` for id and version (stale → `stale`, skipped) (depends on T012)
- [ ] T015 [US1] In the same file write step 5 (classification with the `decision-table` of R3: create, reuse, blocked, stale, closed/locked stop, per work package assign, unchanged, other version, stale) and steps 8–9: `create-version` (preview, then confirm), write `version` (`id`, `name`) to the ledger at once; one `bulk-update-work-packages` preview for all `assign` items shown inside the plan, one confirm, per-item result read, failed items counted as `failed` (fallback per item with `update-work-package` as recorded in T001); never move a work package out of another version (depends on T014)
- [ ] T016 [US1] **(maintainer)** Run S22 through the installed skill in `.scratch/proj` (`--dry-run` first, then real, then again for `no changes`; then put one work package into another version by hand and run again); check that neither report nor ledger contains a host or a token; record run, versions and result in `docs/TESTING.md` (depends on T015)

**Checkpoint**: versions are mapped and repeatable without writes.

---

## Phase 4: User Story 2 - Log time on work packages (Priority: P1)

**Goal**: one time entry per accepted line with the right work package, hours, date and activity; a re-run creates nothing new; a deliberate second entry works with `--entry-key`.

**Independent Test**: S23: two lines, one activity picked, accepted: two entries; same input again: `unchanged`; with `--entry-key`: one more entry.

- [ ] T017 [US2] In `extension/commands/log-time.md` write steps 1–5: arguments and feature resolution, read config (`project`, `defaults.activity`) and ledger (`items`, `time_entries`); parse the input lines with the `duration-grammar` (R5; lines from the arguments or asked for), today's date from `date +%F`, rejections listed in the plan; activity resolution (R7: `--activity`, `defaults.activity`, else list `list-time-activities` and ask the user to choose before the plan; an unknown name stops with the list); work package resolution through `items.<key>.id` or `#<id>` that is in the ledger, `get-work-package` once per distinct work package (stale → skipped); `--entry-key` only with exactly one item, otherwise stop (depends on T012)
- [ ] T018 [US2] In the same file write step 6 and step 9: compute the key (R6: `<work_package_id>|<spent_on>|<activity>|<iso>` or `entry:<k>`), classify (create, unchanged, unknown, rejected, stale), and for every `create` item `create-time-entry` (preview, then confirm; `hours` as ISO 8601, `spent_on`, `activity` by name, `work_package_id`), take the entry id from the confirm result (source verified in T001) and append the `time_entries` record (`key`, `work_package_id`, `spent_on`, `activity`, `hours`, `id`, `entry_key` when given) to the ledger at once; never edit or delete an existing entry (depends on T017)
- [ ] T019 [US2] **(maintainer)** Run S23 through the installed skill: two lines (`T001: 1h30`, `T002: 45m`), activity picked from the list, accepted; verify hours (`PT1H30M`, `PT45M`), date and activity in the UI; run the same input again (`unchanged`); run once with `--entry-key second` and identical values (one more entry); an unknown task key and an invalid duration in one run (reported, others continue); record in `docs/TESTING.md` (depends on T018)

**Checkpoint**: time logging works and is repeatable without duplicates.

---

## Phase 5: User Story 3 - Preview, safe writes and an honest report (Priority: P2)

**Goal**: plan before every write, `--dry-run`, one confirmation, failures isolated, accurate report, in both prompts.

**Independent Test**: S24: dry runs change nothing; a version run interrupted after the version was created recovers with one version; one failing item does not stop the others.

- [ ] T020 [US3] In `extension/commands/sync-version.md` write the plan and confirmation steps: plan table (one line per item: target, action, reason), `--dry-run` ends with `Dry run: nothing was written.` and result `dry run`; otherwise confirm once for the whole plan and stop on "no" (depends on T015)
- [ ] T021 [US3] In the same file write failure handling and the report (step 10): a failed item does not stop the others; error text with URLs and host names replaced by `<redacted-host>` and secrets by `<redacted-secret>`; counts created, reused, assigned, unchanged, other-version, stale, failed, blocked; result `complete`, `incomplete`, `no changes` (only if nothing was written and nothing failed), `dry run` or `stopped` (depends on T020)
- [ ] T022 [US3] In `extension/commands/log-time.md` write the same for time entries: plan table, `--dry-run`, one confirmation, per-item failure isolation with redaction, report counts created, unchanged, unknown, rejected, stale, failed and total hours created; the report states after an interrupted run that the user should check the work package for a double entry (risk 2) (depends on T018)
- [ ] T023 [US3] **(maintainer)** Run S24: dry run of each command with checksums of the ledger before and after and a look at OpenProject; simulate an interrupted version run by hand (ledger without `version`, version already created): rerun gives one version; make one `log-time` item fail (work package without permission or a removed work package) and see the others created; record in `docs/TESTING.md` (depends on T021, T022)

---

## Phase 6: User Story 4 - Clear stops on missing prerequisites (Priority: P2)

**Goal**: missing capability and other stop conditions end with a specific message and zero writes.

**Independent Test**: S25 on a server without the write flags and on broken inputs.

- [ ] T024 [US4] In both prompts write step 0 and the stop conditions of `contracts/command-contract.md`: capability `create-version` (sync-version) or `create-time-entry` (log-time) not callable → stop naming the capability and the server setting from T001, also with `--dry-run`, before any read-for-write step; missing or invalid config or ledger, no `items.feature.id`, no work package in the ledger (sync-version), stale ledger version, server not connected, unknown activity → stop naming what to fix, zero writes (depends on T021, T022)
- [ ] T025 [US4] **(maintainer)** Run S25: server started without version write (and without time-entry write), in `--dry-run` and real mode; no ledger; unknown activity; record in `docs/TESTING.md`; paths not run are labelled untested (depends on T024)

---

## Phase 7: Polish & Cross-Cutting

- [ ] T026 [P] Update `extension/README.md`: usage and arguments of both commands, server flags and how to set them in the MCP client config, input format of `log-time` with examples, what is read and written (versions, work package version fields, time entries, ledger keys), the key rule and `--entry-key`, config keys (`defaults.version`, `defaults.activity`), limitations (no reassign, no reading of existing entries, crash window) and untested paths
- [ ] T027 [P] Update `docs/ARCHITECTURE.md` (version and time flows, ledger keys) and `docs/ROADMAP.md` (005 implemented, see `specs/005-versions-and-time`)
- [ ] T028 Update `docs/TESTING.md`: scenarios S22–S25 in the checklist and an "Untested after feature 005" list (command mode, crash between a confirmed write and the ledger, closed or locked version if not run, version shared across projects, instance with start/end time tracking) (depends on T016, T019, T023, T025)
- [ ] T029 Run `scripts/dev-install.sh`; confirm `specify preset list` and `specify extension list` show `openproject` in both and that the skills `speckit-openproject-sync-version` and `speckit-openproject-log-time` exist in the scratch project (depends on T013, T024)
- [ ] T030 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all green (depends on T029)
- [ ] T031 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings or record the reason for not fixing; rerun once after the last prompt change (depends on T030)
- [ ] T032 Mark finished tasks in this file, prepare the PR description (summary, executed scenarios, untested paths); opening the PR is the maintainer's call (depends on T028, T031)

---

## Dependencies & Execution Order

- Phase 1 (T001–T004 largely parallel) → Phase 2 (T012 needs T001, T006, T007, T010, T011) → US1 and US2 (independent of each other, different prompts) → US3 → US4 → Polish.
- The prompts are written only after T001: the version field shape, the bulk result shape, the time-entry flag and result id decide their text.
- Within one prompt, tasks are sequential edits of one file (sync-version: T014, T015, T020, T021, T024; log-time: T017, T018, T022, T024).
- Maintainer runs (T001, T016, T019, T023, T025) need the sandbox with version and time-entry writes enabled.

## Parallel Opportunities

- T002, T003, T004 together (T001 beside them); T008 beside T005–T007; US1 prompt work (T014–T015) beside US2 prompt work (T017–T018); T026 and T027 beside any maintainer run.

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): the version command works, repeatable, no time entries yet.
- Then US2 (time entries), US3 (preview and report in both prompts), US4 (stop conditions). Do not open the PR before `/speckit-analyze` is clean and S22–S25 results are recorded.
