---

description: "Task list for feature 007: parent status roll-up for phase and feature work packages"
---

# Tasks: Parent Status Roll-up

**Input**: Design documents from `specs/007-parent-status-rollup/`

**Prerequisites**: plan.md, spec.md (FR-001–FR-015, SC-001–SC-006), research.md (R1–R9, Unresolved), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution principle IV requires schema, rule and prompt-sync tests and executed prompt scenarios (S34–S38 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The behaviour change is one Markdown prompt (`extension/commands/sync-status.md`), so prompt-editing tasks touch the same file and are **not** `[P]`; they build the prompt up section by section. Tasks that edit `tests/test_prompt_sync.py` are likewise sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US4 as numbered in `spec.md` (US1 close parents, US2 partial progress, US3 preview and protect, US4 switch off)
- The installed command is self-contained and uses **capability ids only**; no new capability is added (plan, constitution II). Embedded blocks: `capability-map`, `config-rules`, `ledger-rules`, `decision-table`, and the new `rollup-table`.
- Tasks marked **(maintainer)** need the sandbox instance or an admin action; they are never claimed done without an executed run. This project never deletes work packages; the maintainer removes test work packages by hand.
- Version numbers: extension 0.2.0, preset 1.0.2, bundle 0.2.0 (research R9). Releases and catalog updates are outside this task list.

## Path Conventions

Monorepo: `extension/`, `preset/`, `bundle/`, `schemas/`, `tests/`, `docs/`. `preset/` is touched only for the embedded config-rules block, its template and its version.

---

## Phase 1: Setup (schema and config fixtures)

- [X] T001 Add the optional property `rollup_parents` (`{"type": "boolean", ...}`) to `schemas/config.schema.json` exactly as in `contracts/schema-changes.md`; do not change `required` or `additionalProperties`
- [X] T002 [P] Add config fixtures `tests/fixtures/config/valid-rollup-off.yml` (`rollup_parents: false`, otherwise minimal) and `tests/fixtures/config/invalid-rollup-type.yml` (`rollup_parents: "no"`)
- [X] T003 Extend `tests/test_schemas.py`: `valid-rollup-off` validates, `invalid-rollup-type` is rejected, every config fixture that was valid before is still valid (depends on T001, T002)

---

## Phase 2: Foundational (blocks all stories)

**Purpose**: the rule as an executable reference with fixtures and tests, the extended config-rules in all six prompts, and the prompt-sync test written first. No story can be written before the rule and the sync test exist.

- [X] T004 [P] Add `tests/rollup_reference.py`: `task_state(status, statuses, closed)` (research R3), `rollup(children)` (R2), `phase_contribution(...)` and `feature_rollup(...)` (R5), `classify_parent(O, R, statuses, closed, exists)` (R4, data-model "Parent decision") and the row list that the prompt block `rollup-table` must contain; a header comment says it mirrors the prompt and is used only by tests
- [X] T005 Add `tests/fixtures/sync/rollup-cases.json` (secret-free): one case per row of the roll-up rule and of the parent decision (all done, one in progress, nothing started, empty phase, done parent stays done, Rejected and On hold parents left alone, missing parent stale, unmapped task status, unpublished/stale/orphan/blocked/failed task never finished, all tasks Rejected → done with note, ignored phases, feature with all phases ignored, phase blocked counts with its real status, ledger phase without `## Phase N` heading (`no heading`, ignored for the feature), `## Phase N` heading without ledger phase (`unpublished phase`, reported only), dry-run assumption that planned pushes count as confirmed (R3), feature capped at in progress when a phase is `stale` (R5), a failed phase write re-read for the feature, parent present with ledger `B` ≠ `O` in each left-alone label (ledger becomes `O`, R4)); expected `R`, action, label and resulting ledger status (depends on T004)
- [X] T006 Add `tests/test_rollup.py`: every case of T005 gives the expected result; applying a result and classifying again writes nothing (idempotence, FR-008, SC-003); a parent in done is never written (FR-013, SC-004); phases are processed in key order and the feature last using actual phase outcomes (FR-003); with the switch off no parent action is produced (SC-006) (depends on T005)
- [X] T007 Extend `tests/test_prompt_sync.py`: (a) `config-rules` of all six prompts equal the schema, including `rollup_parents` (the existing generic check, verify it covers the key list and the value-types line); (b) `extension/commands/sync-status.md` embeds a `rollup-table` block listing exactly the rows of `tests/rollup_reference.py` (red until T012, by design: test first); (c) the prompt names the new strings `Parents`, `parents: rolled up`, `stays done`, `closed, not done`, `unmapped status`, `plan changed`, `changed meanwhile`, `no tasks`, `no heading`, `unpublished phase`; (d) the capability block still has no `create` or `delete` row (depends on T004)
- [X] T008 Update the `config-rules` block (key list and value-types line: `rollup_parents` is a boolean next to `create_relations` and `mark_parallel`) in all six prompts: `extension/commands/sync-status.md`, `discover-fields.md`, `sync-docs.md`, `sync-version.md`, `log-time.md` and `preset/commands/speckit.taskstoissues.md`; `discover-fields` must keep an existing `rollup_parents` unchanged when it rewrites the config (depends on T001)
- [X] T009 [P] Add a commented-out `rollup_parents` with a one-line explanation to `preset/openproject-config.template.yml`; the preset never writes the key

**Checkpoint**: `uv run pytest` is green except the `rollup-table` check of T007(b) and the new-strings check T007(c); the rule and the config change are done.

---

## Phase 3: User Story 1 - Close phases and the feature when all tasks are done (Priority: P1) MVP

**Goal**: with all tasks done, one run puts every phase and the feature into the done status, the ledger records it, a second run writes nothing.

**Independent Test**: S34.

- [X] T010 [US1] Rewrite the intro, hard limits and overrides in `extension/commands/sync-status.md` for parents (replace "feature and phase entries are read for the report only"): parents are written only by the roll-up and only `status`; config needs `statuses.open`, `statuses.in_progress` and `statuses.done` while the roll-up is on (missing → stop, point to `discover-fields`) (depends on T008)
- [X] T011 [US1] Add the roll-up to the prompt, renumbered to 16 steps per `contracts/command-contract.md`: step 5 also reads the write context for the phase and feature types; step 7 roll-up plan from the planned task states (R3, R5; `## Phase N` heading → `phase-N`, FR-002); step 8 preview of the parent writes after the task previews (the three-consecutive-tool-errors stop counts across tasks and parents, R6); steps 9–11 plan, dry run, one confirmation including parents (the "more than 10" notice counts parent writes too); steps 12–13 as the old 11–12 (depends on T010)
- [X] T012 [US1] Embed the `rollup-table` block (roll-up rule and parent decision rows exactly as `tests/rollup_reference.py`) and add step 14 (parent writes after task push and pull: skipped if step 12/13 stopped the run; recompute from actual outcomes; a differing target is `skipped`/`plan changed`; recheck `O` read; confirm; ledger write before the next call; feature last, from actual phase outcomes), step 15 (ledger: parent `status` after each confirmed write; and, whenever the parent exists and `B` ≠ `O`, set to `O` — this covers a parent already at `R` and every left-alone label `stays done`, `closed, not done`, `unmapped status`, `no tasks`; FR-007, R4); phases without a heading (`no heading`) are ignored for the feature and headings without a ledger phase are reported as `unpublished phase`, nothing is created (depends on T011)
- [X] T013 [US1] Add the report (step 16): Parents section `Key | WP | OpenProject | Rolled up | Action | Reason`, counts line `parents: rolled up N, unchanged N, left alone N, blocked N, failed N, stale N, skipped N`, percent-complete-100 note (FR-011), tasks counted finished through a closed status other than done named per phase (FR-001), `no heading` and `unpublished phase` lines; blocked, failed or skipped parents make the result `incomplete`; task table and task counts line unchanged (SC-006) (depends on T012)
- [X] T014 [US1] Define scenarios S34 (all done, second run 0 writes) in `docs/TESTING.md` with a results table, and the intro "Scenarios S34–S38" naming the installed-skill method and the setup of `quickstart.md` (depends on T013)
- [x] T015 [US1] **(maintainer, main session headless)** Run `scripts/dev-install.sh`, then S34 through the installed skill in `.scratch/proj`: `--dry-run` first, then for real, then again (0 writes); compare ledger and `tasks.md` checksums; one dry run in command mode, labelled untested if it could not be run; record results (depends on T014). **Done 2026-10-10** on feature 971 (see `docs/TESTING.md`, run log S34–S37); the command-mode dry run was not run and is listed as untested

**Checkpoint**: US1 works alone: a finished feature closes its parents in one run.

---

## Phase 4: User Story 2 - Show partial progress on parents (Priority: P2)

**Goal**: phases and the feature show open / in progress / done from their children.

**Independent Test**: S35.

- [X] T016 [US2] Read the rule rows of the `rollup-table` block and step 7 in `extension/commands/sync-status.md` against the T005 cases "one in progress", "nothing started" and "feature capped at in progress"; all three must pass in `uv run pytest tests/test_rollup.py` and the prompt must state each branch (finished or in-progress tasks plus unfinished ones → in progress; none → open; feature from phase contributions per research R5); fix `sync-status.md` and the reference together if a case disagrees, otherwise record "no change needed" in the commit message (depends on T012)
- [X] T017 [US2] Define S35 (three phases: all done / one task open / nothing started; feature in progress; with a second sub-case where a reopened task leaves its done phase done, FR-013) in `docs/TESTING.md` (depends on T016)
- [x] T018 [US2] **(maintainer)** Run S35 through the installed skill, dry run then real, then a second run (0 writes); record results (depends on T015, T017). **Done 2026-10-10**: main case pass; the sub-case pull write failed safely at the step 13 check in the headless session (recorded as untested); the separate 0-write re-run was not repeated on the final revision, the S34 re-run covers it

**Checkpoint**: partial progress is visible on parents.

---

## Phase 5: User Story 3 - Preview and protect (Priority: P2)

**Goal**: parents in a closed status other than done or in an unmapped status are never written; blocked and failed parents are reported like tasks; the dry run shows the parent plan.

**Independent Test**: S36 and S38.

- [X] T019 [US3] Read steps 7, 8 and 14 of `extension/commands/sync-status.md` against `contracts/command-contract.md` and tick each of these paths; the T005 cases for them must pass in `uv run pytest tests/test_rollup.py`: `closed, not done` and `unmapped status` parents left alone and counted for the feature (Rejected as finished, On hold as in progress, FR-003); `stale` for a missing parent work package (never recreated); a preview that is not valid or a tool error makes the parent `blocked` with the write-context hint; an unconfirmed write is `failed` and never retried; the run continues with the other parents; edit `sync-status.md` where a rule is missing (depends on T013)
- [X] T020 [US3] Define S36 (Rejected and On hold parents) and S38 (workflow forbids the parent transition, blocked with the server's reason, other parents continue, `incomplete`) in `docs/TESTING.md`; add the dry-run check (plan of the dry run equals the plan of the following real run, SC-005) to S34 and S35 (depends on T019)
- [x] T021 [US3] **(maintainer; S38 needs an admin action in the web UI)** Run S36 and S38 through the installed skill; for S38 restrict the phase type's workflow, record the preview result (research "Unresolved"), restore the workflow afterwards; record results (depends on T018, T020). **S36 done 2026-10-10** (pass); **S38 done 2026-10-11** (feature 974, blocked preview; see TESTING run log "S38 retry")

**Checkpoint**: parents set on purpose stay as they are; failures are reported honestly.

---

## Phase 6: User Story 4 - Switch the roll-up off (Priority: P3)

**Goal**: `rollup_parents: false` gives exactly the 0.1.0 behaviour; an old config stays valid and has the roll-up on.

**Independent Test**: S37 and the schema tests.

- [X] T022 [US4] Add the switch to the prompt: with `rollup_parents: false` steps 7, 8 and 14 are skipped, no parent is read for the roll-up or written, no Parents section, informational lines as in 003; absent or `true` = on (FR-014); the statuses check of step 5 is skipped for `open` and `in_progress` when off (depends on T013)
- [X] T023 [US4] Define S37 in `docs/TESTING.md` (switch off, all tasks done, report as in 003) (depends on T022)
- [x] T024 [US4] **(maintainer)** Run S37 through the installed skill; record results (depends on T021, T023). **Done 2026-10-10**: no parent write; the report showed an informational "Parents" heading (recorded)

**Checkpoint**: the roll-up can be switched off per project.

---

## Phase 7: Polish & Cross-Cutting

- [ ] T025 [P] Bump versions: `extension/extension.yml` 0.1.0 → 0.2.0, `preset/preset.yml` 1.0.1 → 1.0.2, `bundle/bundle.yml` 0.1.1 → 0.2.0 (pins preset 1.0.2 and extension 0.2.0); the hook in `extension.yml` stays unchanged (FR-015); `uv run pytest tests/test_manifests.py` passes. **Deferred to the release PR** (2026-10-10): `tests/test_release.py` requires a versioned CHANGELOG heading and a catalog entry for every manifest version, so the bump goes together with them, as for preset 1.0.1 (PR #17); the CHANGELOG entries stay under "Unreleased" until then
- [X] T026 [P] Update `extension/README.md`: roll-up rules in plain words, the switch `rollup_parents`, which versions are needed together (config key rejected by older preset/extension prompts), guards, percent complete 100, limitations and untested paths
- [X] T027 [P] Update `docs/ARCHITECTURE.md`: sync policy (parents are rolled up from their children, never moved out of done) and `docs/ROADMAP.md` row 007
- [X] T028 [P] Add the `CHANGELOG.md` entries: extension 0.2.0 (roll-up, default on), preset 1.0.2 (config-rules only), bundle 0.2.0; note that the default-on behaviour can be switched off
- [x] T029 Update `docs/TESTING.md`: results of S34–S38 and an "Untested after feature 007" list (command mode, hook offer, anything not run) (depends on T015, T018, T021, T024)
- [x] T030 Run `scripts/dev-install.sh`; confirm `specify preset list` and `specify extension list` show `openproject` with the new versions and that `.claude/skills/speckit-openproject-sync-status` exists in the scratch project (depends on T025). **Done 2026-10-10** with the current versions (preset 1.0.1, extension 0.1.0), since T025 is deferred
- [x] T031 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all green, including `rollup-table` and config-rules checks (depends on T030). **Done 2026-10-10**: 485 passed, ruff clean
- [x] T032 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings or record the reason for not fixing; rerun once after the last prompt change (depends on T031) **Done 2026-10-10**: both reviewers run; minor conformance findings fixed (spec US4 wording, S34 setup note, T029 note, SC-002 line); API findings (task above first heading, leading-zero phase keys) and earlier #6/#7/#8 recorded in the PR description, not applied.
- [x] T033 Mark finished tasks in this file, update `specs/007-parent-status-rollup/checklists/requirements.md` if scope changed, prepare the PR description (summary, executed scenarios, untested paths); opening the PR is the maintainer's call (depends on T029, T032) **Done 2026-10-10**: PR description drafted, not opened.

---

## Phase 8: Review follow-up (2026-10-10)

- [x] T034 Spec: FR-002 membership by `parent_id` with heading fallback, phase keys without leading zeros; research R3, data model and contract updated. **Done 2026-10-10**
- [x] T035 `sync-status.md`: step 6 reads `parent_id`; "Phases" rule and membership report lines. **Done 2026-10-10**
- [x] T036 `speckit.taskstoissues.md`: phase key without leading zeros, duplicate keys stop. **Done 2026-10-10**
- [x] T037 `tests/rollup_reference.py`, `rollup-cases.json` (`membership`), `test_rollup.py`, `test_prompt_sync.py`. **Done 2026-10-10**: 497 passed
- [x] T038 CHANGELOG, extension README, TESTING (S39, S40). **Done 2026-10-10**
- [x] T039 Live runs S35b (pull write), S39, S40 headless in the sandbox, dry run first; S38 after the maintainer's workflow change. **2026-10-11**: S35b, S39, S40 pass (dry run, real run; see TESTING run log 2026-10-11); S38 on 973: the workflow restriction did not take effect after two changes, the real run closed the phases; S38 retried after the maintainer's corrected workflow change: pass (see TESTING run log "S38 retry").
- [x] T040 Rerun both reviewers on the final diff. **Done 2026-10-11**: no blocker; README/TESTING consistency fixed, M1 (rejected confirm reported verbatim) and L1 (in progress → open documented as intended) applied; M2 (server not pinned) and L2–L6 recorded in the PR description.

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 (builds the prompt) → US2, US3, US4 (each verifies or adds a part of the same prompt; do them in this order because they edit one file) → Polish.
- Within the prompt, tasks T010–T013, T016, T019 and T022 are sequential edits of one file.
- Maintainer runs (T015, T018, T021, T024) need the sandbox and run in this order; S38 (T021) needs an admin action.

## Parallel Opportunities

- T002 beside T001; T004 beside T001–T003; T009 beside T005–T008; T025–T028 beside the maintainer runs.

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): finished features close their parents; guards and the switch follow.
- Then US2 (partial progress), US3 (protect and failures), US4 (switch); Polish last. Do not write code before `/speckit-analyze` is clean.

## Notes

- Success criteria map to tasks: SC-001 → T015; SC-002 → T018; SC-003 → T006, T015, T018; SC-004 → T006, T021; SC-005 → T020; SC-006 → T013, T024.
- The workflow behaviour of the phase and feature types is unverified until S38 (research "Unresolved") and stays labelled in `docs/TESTING.md`.
