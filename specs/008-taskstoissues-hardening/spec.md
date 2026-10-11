# Feature Specification: taskstoissues Hardening

**Feature Branch**: `008-taskstoissues-hardening`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "docs/briefs/008-taskstoissues-hardening.md" — four small defects of the preset command that publishes `tasks.md` as work packages, found in the command-mode runs of 2026-10-09 (GitHub issues #20, #21, #22, #23): condensed plans for large features, a misleading stop message for read-only roles, no specific message for a missing plan, and an undocumented limit of the `generic` integration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the full plan of a large feature (Priority: P1)

A spec-kit user publishes a feature with more than a hundred tasks. Before anything is written, the command shows the plan. Today the plan can come back condensed into ranges (`T001–T020`) without hashes, so the user cannot check the single items they are about to create, and a hash comparison of a re-run cannot be followed.

**Why this priority**: The plan and the preview are the safety mechanism of every write path (constitution III). A plan the user cannot read item by item weakens the confirmation that follows it.

**Independent Test**: Run the command with `--dry-run` on a `tasks.md` with 120 tasks in several phases. The plan has one row per feature, phase and task, each with its action and hash, and no row stands for a range of items.

**Acceptance Scenarios**:

1. **Given** a `tasks.md` with 120 tasks, **When** the command prints the plan, **Then** it has exactly one row for every task, phase and the feature, with the action and the hash of each.
2. **Given** a plan in which many items have the same action (for example all `create`), **When** it is printed, **Then** the items are still listed one by one; the counts line may summarize, the rows may not.
3. **Given** a re-run on the same feature, **When** the plan is printed, **Then** every row shows its stored and its current hash where the rules of the command compare them.

---

### User Story 2 - Understand why a read-only role stops (Priority: P1)

A user whose OpenProject role may read but not create work packages runs the command. Today the run stops with a message that work package types are missing, because the server returns an empty type list for such a role. The user then searches for a configuration error that does not exist.

**Why this priority**: A wrong stop reason sends the user in the wrong direction and costs more time than a missing feature.

**Independent Test**: Run the command with a project where the user's role has read access only. The run stops before any write and says that the write permission is missing, naming the project and not claiming that types are missing.

**Acceptance Scenarios**:

1. **Given** the user's role cannot create work packages in the project, **When** the command runs (with or without `--dry-run`), **Then** it stops before any write with a message that names the missing write permission and the project.
2. **Given** the role may create work packages but a configured type does not exist, **When** the command runs, **Then** it still stops with the existing message that names the missing type and lists the available ones.
3. **Given** the role may create work packages and all types exist, **When** the command runs, **Then** nothing changes compared to today.

---

### User Story 3 - Be told when plan.md is missing (Priority: P2)

A user runs the command on a feature that has a `tasks.md` but no `plan.md` (for example after copying files by hand). Today the run stops in the prerequisite script without saying which file is missing or what to do. A missing `tasks.md` already has a specific message.

**Why this priority**: It is a small paper cut, but it is the first thing a new user meets and the fix is the same kind as the one for `tasks.md`.

**Independent Test**: Remove `plan.md` from a feature directory and run the command. It stops before any write and names `plan.md` and the command that creates it.

**Acceptance Scenarios**:

1. **Given** a feature directory without `plan.md`, **When** the command runs, **Then** it stops before any write, names `plan.md` and tells the user to run the plan command (`/speckit-plan` in skills mode, `/speckit.plan` otherwise).
2. **Given** a feature directory with `plan.md` but without `tasks.md`, **When** the command runs, **Then** the existing message for `tasks.md` is unchanged.
3. **Given** both files exist, **When** the command runs, **Then** nothing changes compared to today.

---

### User Story 4 - Know that the generic integration gets no override (Priority: P3)

A user installs the preset in a project that uses spec-kit's `generic` integration and finds that `/speckit.taskstoissues` still creates GitHub issues. spec-kit registers no preset command overrides for that integration, so this is not a defect of the preset, but nothing in the documentation says so.

**Why this priority**: Documentation only; it prevents a support question and does not change behavior.

**Independent Test**: Read `README.md` and `preset/README.md`. Both state that the `generic` integration gets no preset override and say what the user can do instead.

**Acceptance Scenarios**:

1. **Given** a reader of the main README, **When** they look at the installation section, **Then** it names the limitation of the `generic` integration.
2. **Given** a reader of the preset README, **When** they look at the installation section, **Then** it names the same limitation and the integrations on which the override is registered.

---

### Edge Cases

- A plan with several hundred items: the plan stays one row per item; if it is too long for one message it is printed in consecutive parts, never condensed.
- A feature whose `tasks.md` has no tasks: unchanged (nothing to list).
- Both `tasks.md` and `plan.md` are missing: the message names `plan.md`, because the prerequisite check tests it first (as today); `tasks.md` is reported on the next run.
- A role that can create work packages but not in this project's type: unchanged; the existing type and mandatory-field messages apply.
- The write permission cannot be determined (server answers with an error or an unknown shape): the run stops and reports the answer verbatim; it never guesses the cause (existing rule for tool errors).
- An unknown integration other than `generic` that registers no override: not covered by this feature; the documentation names `generic` only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plan and the dry-run output MUST list every feature, phase and task as its own row with its action; a row that stands for a range or a group of items is not allowed.
- **FR-002**: Every plan row MUST show the hash fields that the command's rules compare for that row (the current hash, and the stored hash where a ledger entry exists); a plan MUST NOT omit them because of its size.
- **FR-003**: The plan MAY end with a counts line that summarizes the rows; the summary never replaces them.
- **FR-004**: When the user's role cannot create work packages in the selected project, the command MUST stop before any write, in a dry run as well as in a real run, with a message that names the missing write permission and the project.
- **FR-005**: The message of FR-004 MUST NOT say that types are missing; the existing "missing type" message applies only when the role may create work packages and a configured type is not in the type list.
- **FR-006**: The check of FR-004 MUST NOT create, change or delete anything in OpenProject, and MUST NOT rely on a write call.
- **FR-007**: When `plan.md` is missing from the feature directory and `tasks.md` exists, the command MUST stop before any write with a message that names `plan.md` and the plan command for the current mode (`/speckit-plan` in skills mode, `/speckit.plan` otherwise).
- **FR-008**: The existing stop message for a missing `tasks.md` MUST remain unchanged (it names `tasks.md` and the tasks command for the current mode). When both files are missing, the file that the prerequisite check reports first (`plan.md`) is named, as today; the other one is reported on the next run.
- **FR-009**: `README.md` and `preset/README.md` MUST state that spec-kit registers no preset command overrides for the `generic` integration, so `/speckit.taskstoissues` stays the core command there, and MUST say what to do instead.
- **FR-010**: The change MUST NOT add or rename a configuration key, MUST NOT change the ledger format or a schema, and MUST NOT change what is written to OpenProject on any path that works today (constitution III and V).
- **FR-011**: The command MUST keep working in skills mode and in command mode, and the install of the preset must keep working with spec-kit 1.1.0 and later.
- **FR-012**: Every changed stop path and the plan format MUST be covered by a prompt test and by a scenario in `docs/TESTING.md` that records what was actually run; a scenario that was not run is listed as untested.

### Key Entities

- **Plan row**: one line of the printed plan for one feature, phase or task: key, action, current hash and, where a ledger entry exists, the stored hash.
- **Stop message**: the text printed when the run stops before any write; has a reason (missing file, missing permission, missing type) and a next step for the user.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A dry run on a feature with 120 tasks prints 120 task rows plus one row per phase and the feature, with no range rows; a reader can find any task by its key.
- **SC-002**: A user with a read-only role learns the real reason (missing write permission) from the first stop message, in one run, and no run of that case names missing types.
- **SC-003**: A user with a missing `plan.md` learns the file and the command to run from the first stop message, without reading the prerequisite script's output.
- **SC-004**: A reader of either README can answer "does the preset work with the generic integration?" without trying it.
- **SC-005**: No scenario that passed before (S1–S9, S34-style re-runs of the preset) changes its result; a re-run on an existing feature writes nothing new.

## Assumptions

- The sandbox user can be given a read-only role for the read-only scenario (S7 variant) by the maintainer; this needs an admin action in the web UI and a run with that user.
- How the write permission is detected (a field of the project context or another read-only call of the verified tool map) is a plan decision and must be verified against the live server before it is relied on; the spec only fixes the observable behavior.
- The hash fields of the plan are those the command already computes and compares; this feature does not add new ones.
- The release is a patch version of the preset (1.0.3) and ships with extension 0.2.0 unchanged; the bundle is bumped to pin it.
- Issue #24 (file hints in backticks) is out of scope: it is already fixed since preset 1.0.0.
