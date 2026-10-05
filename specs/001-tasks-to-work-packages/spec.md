# Feature Specification: Tasks → Work Packages

**Feature Branch**: `001-tasks-to-work-packages`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "docs/briefs/001-tasks-to-work-packages.md" — turn a feature's `tasks.md` into trackable OpenProject work packages without duplicates, with hierarchy and dependencies.

## Clarifications

### Session 2026-10-05

- Q: How should the feature appear in OpenProject (parent work package, version, both)? → A: Parent work package only (Feature → Phase → Task); no version in this feature.
- Q: How are labels/markers from tasks.md (story reference, `[P]`) represented in OpenProject? → A: As plain text in the work package description; no categories or custom fields.
- Q: How often is confirmation requested for 100+ tasks? → A: Once per phase.
- Q: How is an existing work package without a ledger entry recognised? → A: Task id as subject prefix (e.g. "T012 …"); search by subject and feature membership.
- Q (analyze remediation): How does the feature work package carry the feature identifier? → A: The subject starts with the full feature directory name (e.g. "001-tasks-to-work-packages Tasks → Work Packages"), identical to the ledger field `feature`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish tasks as a work package hierarchy (Priority: P1)

A team has finished `/speckit-tasks` and wants the plan visible in OpenProject. They run the command once and get one work package per phase and one per task, with each task nested under its phase, and a summary of what was created.

**Why this priority**: This is the core value of the integration; without it nothing else matters.

**Independent Test**: Run against an empty sandbox project with a `tasks.md` of 3 phases / 10 tasks (scenario S1). Delivers 14 work packages (1 feature, 3 phases, 10 tasks) with correct parents and 14 ledger entries.

**Acceptance Scenarios**:

1. **Given** a `tasks.md` with 3 phases and 10 tasks and no existing work packages, **When** the user runs the command, **Then** 3 phase work packages and 10 task work packages exist, each task is a child of its phase, and the summary lists all 13 as created.
2. **Given** the same input, **When** the run completes, **Then** every created item is recorded in the mapping ledger with its task identifier and work package identifier.

---

### User Story 2 - Safe re-runs and resume (Priority: P1)

A user re-runs the command after a success, after an interruption, or after editing `tasks.md`. Nothing is duplicated; only missing items are created.

**Why this priority**: Idempotency is a non-negotiable constitutional principle and the main reason teams distrust sync tools.

**Independent Test**: Re-run S1 (S2: zero creations); interrupt after 5 creations and re-run (S3: resumes, no duplicates).

**Acceptance Scenarios**:

1. **Given** all items already exist in the ledger, **When** the command is re-run, **Then** zero work packages are created and the report states all items were skipped.
2. **Given** a run interrupted after 5 creations, **When** the command is re-run, **Then** the remaining items are created and no item exists twice.
3. **Given** a ledger entry is missing but a matching work package exists in the project, **When** the command runs, **Then** the existing work package is adopted into the ledger instead of creating a duplicate.
4. **Given** `tasks.md` gained new tasks since the last run, **When** the command runs, **Then** only the new tasks are created.

---

### User Story 3 - Preview with dry run (Priority: P1)

Before anything is written, the user can see exactly what would be created, skipped or blocked.

**Why this priority**: Required by the constitution for every write command and needed to trust the first real run.

**Independent Test**: Run with `--dry-run` on S1 input; verify the plan is shown and the project and ledger are unchanged.

**Acceptance Scenarios**:

1. **Given** a valid `tasks.md`, **When** the user runs the command with `--dry-run`, **Then** a plan lists every item with its action (create / skip / blocked) and no work package or ledger entry is written.
2. **Given** a dry-run plan, **When** the user runs the command without `--dry-run`, **Then** the actions executed match the plan.

---

### User Story 4 - Dependencies as relations (Priority: P2)

Tasks that really depend on other tasks appear in OpenProject as ordered ("follows") relations; tasks marked parallel do not get spurious relations.

**Why this priority**: Makes the schedule meaningful, but the hierarchy is useful without it.

**Independent Test**: Scenario S4 — `tasks.md` with real dependencies and `[P]` tasks.

**Acceptance Scenarios**:

1. **Given** task B depends on task A, **When** the command runs, **Then** B's work package follows A's work package.
2. **Given** tasks marked `[P]` with no stated dependency between them, **When** the command runs, **Then** no relation is created between them.
3. **Given** a relation already exists, **When** the command is re-run, **Then** it is not duplicated.

---

### User Story 5 - Update existing work packages (Priority: P3)

With `--update`, changes to a task's title or description in `tasks.md` are propagated to the already linked work package; without it, existing items are left untouched.

**Why this priority**: Useful once teams iterate on `tasks.md`, but not needed for first publication.

**Independent Test**: Change a task title in `tasks.md`, run with and without `--update`, compare.

**Acceptance Scenarios**:

1. **Given** a linked task whose title changed, **When** the command runs without `--update`, **Then** the work package is unchanged and the report lists it as "differs, not updated".
2. **Given** the same state, **When** the command runs with `--update`, **Then** the work package reflects the new title and the report lists it as updated.

---

### User Story 6 - Fail early with clear diagnostics (Priority: P2)

Misconfiguration is detected before any write: missing configuration, unavailable OpenProject tools, unknown project, unknown work package type, project not writable, or mandatory custom fields that cannot be filled.

**Why this priority**: Prevents half-created trees and confusing errors.

**Independent Test**: Scenarios S5 (unknown type), S6 (mandatory custom field), S7 (project not writable).

**Acceptance Scenarios**:

1. **Given** the configured task type does not exist in the project, **When** the command runs, **Then** it stops before writing and lists the available types.
2. **Given** the project requires a custom field that the command cannot fill, **When** the command reaches that item, **Then** it skips that item, names the field in the report, and continues with unaffected items.
3. **Given** the project is not writable for the current credentials, **When** the command runs, **Then** it reports a clear error and writes nothing.
4. **Given** required OpenProject tools are not available in the agent session, **When** the command starts, **Then** it stops and states which capability is missing.

---

### Edge Cases

- `tasks.md` contains no phases or no tasks: stop with a clear message, write nothing.
- A task appears in no phase: report it and ask the user how to place it; never guess silently.
- Dependency refers to an unknown task identifier: report it, skip that relation, continue.
- Dependency cycle: report it, skip the relations on the cycle, create everything else.
- Two tasks share the same title: identified by task identifier prefix, never by title alone.
- Very large task lists (100+): see FR-015.
- Network or tool failure mid-run: items already written stay in the ledger; the run reports where it stopped and is resumable.
- Work package deleted in OpenProject but still in the ledger: reported as stale; not silently recreated.
- Ledger file corrupt or schema-invalid: stop and explain, never overwrite.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST read its settings from a single configuration file under `.specify/openproject/` that is validated against the shared config schema before use.
- **FR-002**: The command MUST verify before any write that the required OpenProject capabilities are available, the target project exists and is writable, and the configured work package types exist.
- **FR-003**: The command MUST parse `tasks.md` into phases, tasks, task identifiers, parallel markers (`[P]`) and stated dependencies.
- **FR-004**: The command MUST create one parent work package for the feature, one work package per phase (child of the feature work package) and one per task (child of its phase). The command MUST NOT create or assign OpenProject versions.
- **FR-005**: The command MUST keep a mapping ledger per feature at `.specify/openproject/mapping-<feature>.json` (feature = the feature directory name), validated against the shared mapping schema, and update it immediately after each successful write.
- **FR-006**: The command MUST NOT create a work package for an item that is already in the ledger.
- **FR-007**: Every work package created by the command MUST carry its `tasks.md` identifier as a subject prefix (e.g. "T012 Create schema"); the feature work package subject MUST start with the full feature directory name followed by a space (identical to the ledger field `feature`). Before creating an item that is not in the ledger, the command MUST search the project by that prefix, restricted to the feature's work package tree, and adopt a match instead of duplicating. Multiple matches MUST be reported and the item skipped, never guessed.
- **FR-008**: The command MUST create an ordered ("follows") relation for each real dependency, MUST NOT create relations solely because tasks are marked `[P]`, and MUST NOT duplicate existing relations.
- **FR-009**: The command MUST support `--dry-run`, which shows the full plan (create / skip / update / blocked per item) and writes nothing to OpenProject or the ledger.
- **FR-010**: The command MUST support `--update`; without it, existing linked work packages MUST NOT be modified.
- **FR-011**: The command MUST end with a summary report counting created, skipped, adopted, updated, blocked and failed items, with reasons for blocked and failed ones.
- **FR-012**: The command MUST never delete work packages, relations or ledger entries.
- **FR-013**: The command MUST NOT write secrets, instance URLs or credentials to any file, report or work package.
- **FR-014**: The command MUST work in both skills mode and command mode.
- **FR-015**: The command MUST ask for confirmation once per phase (covering the phase work package and all its tasks), not per work package, regardless of list size (including 100+ tasks). Each confirmation MUST show what will be created in that phase. If the OpenProject tool layer requires its own preview-then-confirm step per write, the command MUST satisfy it without prompting the user again for items already confirmed.
- **FR-016**: The feature MUST be represented in OpenProject by a single parent work package above the phases, tracked in the ledger like any other item.
- **FR-017**: Task labels and markers from `tasks.md` (user-story reference, `[P]`) MUST be written as plain text in the work package description (e.g. a line "Labels: US1 · parallel"). The command MUST NOT create or require categories or custom fields for this purpose.
- **FR-018**: The shared config and mapping JSON schemas MUST exist in `schemas/`, be referenced by the preset, and be covered by automated fixture tests.

### Key Entities *(include if feature involves data)*

- **Phase**: A named group of tasks in `tasks.md`; becomes a parent work package.
- **Task**: One item in `tasks.md` with a stable identifier, title, optional parallel marker, optional story reference and dependencies; becomes a child work package.
- **Dependency**: A directed "task B needs task A" statement; becomes a follows relation.
- **Mapping ledger**: Persistent record linking each phase/task identifier to its work package, enabling idempotency and resume.
- **Configuration**: Project identifier, type names for the feature, phases and tasks, and behavior defaults; contains no secrets.
- **Run report**: The per-run summary of actions and problems.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scenarios S1–S9 in `docs/TESTING.md` pass on the maintainer's test instance.
- **SC-002**: Re-running the command on unchanged input creates 0 work packages and 0 relations (S2).
- **SC-003**: After an interruption at any point, a re-run completes the job with 0 duplicates (S3).
- **SC-004**: A user can go from finished `tasks.md` to a complete work package tree for a 10-task feature in under 5 minutes, including the dry-run review.
- **SC-005**: A `--dry-run` leaves the OpenProject project and the ledger byte-for-byte unchanged (S8).
- **SC-006**: Every blocked or failed item in the report names its cause so the user can fix it without reading logs.
- **SC-007**: The automated install smoke test installs the preset into a fresh spec-kit project without errors.

## Assumptions

- Users already have an OpenProject MCP server configured in their agent and credentials with write access to the target project (ADR-0002); credential setup is out of scope.
- The sandbox project, types and bot user from `docs/TESTING.md` exist for acceptance testing.
- The default work package types are "Feature" (feature), "Summary task" (phases) and "Task" (tasks), because a default OpenProject instance has no "Phase" type; all three are configurable.
- The installed command is self-contained: its capability table and the config/ledger rules are embedded in the prompt, because only the command text is installed into a user's project.
- The configuration and ledger live under `.specify/openproject/` (unifying earlier draft paths); old paths are not supported in this release because the preset is unreleased.
- The feature replaces the existing draft of the `speckit.taskstoissues` override in `preset/`.
- Status sync, time tracking, versions management (including grouping work packages into versions) and docs sync belong to the extension and are out of scope here.
- Deleting or archiving work packages for removed tasks is out of scope (constitution III).
