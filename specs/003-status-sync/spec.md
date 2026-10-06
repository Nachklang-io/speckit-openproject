# Feature Specification: Status Sync between OpenProject and tasks.md

**Feature Branch**: `003-status-sync`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "docs/briefs/003-status-sync.md" — a command that keeps task progress consistent between a feature's `tasks.md` and the OpenProject work packages created for it: progress made in OpenProject flows back into the task checkboxes and the ledger, completed tasks flow forward as a status change, conflicts are handled by a clear policy, and every run can be previewed with `--dry-run`. It builds on the optional `statuses` section of the config (feature 002) and on the mapping ledger (feature 001).

## Clarifications

### Session 2026-10-06

- Q: How is a task resolved that changed differently on both sides since the last sync? → A: OpenProject wins (it owns the status). `tasks.md` is adjusted to the OpenProject status; the report names every such conflict with the overwritten `tasks.md` state, so nothing is lost silently. No extra file keeps the overwritten state.
- Q: Where is the assignee kept? → A: In the ledger and in the report only; `tasks.md` carries nothing but the checkboxes.
- Q: What happens on the first sync when a ledger entry has no last synced status? → A: Baseline run: the missing base counts as "not done". A checked task whose work package is not done is pushed; a done work package with an open task is pulled; a baseline run never yields a conflict.
- Q: What happens when a task is checked but its work package is in a closed status that is not done (e.g. "Rejected")? → A: Nothing is written on either side: the task is reported as "closed, not done", the checkbox stays, no push happens, and the ledger records the OpenProject status so the next run reports no change.
- Q: May the sync reach the done status through intermediate statuses when the workflow does not allow a direct transition? → A: No. The task is reported as blocked with the server's reason and the statuses available for the type; there is no switch and no automatic path.
- Q: What happens when a task is reopened in `tasks.md` (checkbox removed) while its work package is still done and the last synced status was done? → A: OpenProject wins: the checkbox is set again and the report lists the task as "reverted" with the reason that OpenProject is still done. This feature never moves a work package out of the done status.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pull progress from OpenProject into tasks.md (Priority: P1)

Team members work in OpenProject and move work packages to "In progress" or "Closed". The spec-kit user runs the sync command and sees `tasks.md` reflect that progress: a task whose work package reached the configured "done" status is checked, a task whose work package was reopened is unchecked, and the ledger records the last synced status (and the assignee) of every task.

**Why this priority**: Without this, OpenProject progress never reaches the file that `/speckit-implement` and the user read; the two sources drift apart immediately.

**Independent Test**: With a published feature (ledger exists) and two work packages moved to "Closed" and "In progress" in OpenProject, run the command. Exactly the "Closed" task is checked in `tasks.md`; the "In progress" task stays unchecked; the ledger holds the new status of both; nothing else in `tasks.md` changes (scenario S14).

**Acceptance Scenarios**:

1. **Given** a task whose work package is in the configured done status and whose checkbox is open, **When** the command runs and the user accepts the plan, **Then** the checkbox is checked, the ledger status of that task is the done status, and every other byte of `tasks.md` is unchanged.
2. **Given** a checked task whose work package was reopened in OpenProject (status no longer the done status, ledger still says done), **When** the command runs, **Then** the checkbox is unchecked and the report says so.
3. **Given** a work package that is in an intermediate status ("In progress"), **When** the command runs, **Then** the checkbox stays as it is (a checkbox only knows open and done), the ledger records the new status, and the report lists the task as "in progress".
4. **Given** a work package with an assignee, **When** the command runs, **Then** the assignee is recorded in the ledger and shown in the report.

---

### User Story 2 - Push completed tasks to OpenProject (Priority: P1)

After implementing, tasks in `tasks.md` are checked. The user runs the sync and the matching work packages move to the configured done status, but only along transitions that the OpenProject workflow allows. A transition the workflow does not allow is reported and left alone, never forced.

**Why this priority**: This is the other half of the round trip and the reason for the optional hook after `implement`: progress made by the coding agent must become visible to the rest of the team.

**Independent Test**: Check two tasks in `tasks.md` whose work packages are "New"; run the command. Both work packages end in the done status (or, if the workflow forbids the transition for one, that one is listed as blocked with the reason), the ledger records the new statuses, and `tasks.md` is untouched (scenario S14).

**Acceptance Scenarios**:

1. **Given** a checked task whose work package is not in the done status and the workflow allows the done status for it, **When** the user accepts the plan, **Then** the work package moves to the configured done status through the server's preview-then-confirm flow and the ledger is updated immediately after that write.
2. **Given** a checked task whose work package cannot move to the done status in the current workflow, **When** the command runs, **Then** the task is reported as blocked with the server's reason and the statuses available for the task type, nothing is written for it, and the run result says so.
3. **Given** a task that is open in `tasks.md` and in the open status in OpenProject, **When** the command runs, **Then** nothing happens for it.
4. **Given** a task unchecked in `tasks.md` whose work package is still done (the last sync saw it done), **When** the command runs, **Then** the checkbox is checked again, the report lists the task as "reverted", and nothing is written to OpenProject.

---

### User Story 3 - Deterministic handling of changes on both sides (Priority: P1)

Between two syncs, a task may have changed in `tasks.md` and in OpenProject. The command compares both sides with the status recorded at the last sync, applies the changes that exist on only one side, and treats a task that changed differently on both sides as a conflict, resolved in favour of OpenProject. The result is always reported per task, and no change is lost silently.

**Why this priority**: This is the acceptance criterion of the brief (round trip with changes on both sides).

**Independent Test**: After one sync, check task A in `tasks.md`, close task B's work package in OpenProject, and change task C on both sides in different ways. Run the command: A is pushed, B is pulled, C is resolved in favour of OpenProject, the report names each outcome, and a second run reports no changes (scenario S15).

**Acceptance Scenarios**:

1. **Given** a task changed only in `tasks.md` since the last sync, **When** the command runs, **Then** it is treated as a push (User Story 2).
2. **Given** a task changed only in OpenProject since the last sync, **When** the command runs, **Then** it is treated as a pull (User Story 1).
3. **Given** a task changed on both sides and the two results agree (checked and done), **When** the command runs, **Then** nothing is changed except that the ledger records the status.
4. **Given** a task changed on both sides with different results, **When** the command runs, **Then** OpenProject wins: the checkbox is set to match the OpenProject status (done checks it, any other status leaves it open), the ledger records that status, and the report lists the task as a conflict with the overwritten `tasks.md` state and the winning OpenProject status.
5. **Given** the same input twice, **When** the command runs twice without changes in between, **Then** the second run changes nothing and its report states "no changes".

---

### User Story 4 - Preview, safe writes and an honest report (Priority: P2)

Every run starts with a plan table (one line per task: key, work package, `tasks.md` state, OpenProject status, action, reason). With `--dry-run` nothing is written on any side. Without it, the user confirms the plan once; writes to OpenProject go through the server's preview-then-confirm flow; the ledger and `tasks.md` are written so that an interrupted run can simply be repeated.

**Why this priority**: The constitution requires dry-run, preview-then-confirm and idempotence for every write path; without them the P1 stories are not safe to use.

**Independent Test**: Run with `--dry-run` on the S15 setup and compare checksums of `tasks.md` and the ledger before and after: identical, and no work package changed. Then run for real, interrupt after the first write, run again: no duplicated or contradictory writes.

**Acceptance Scenarios**:

1. **Given** `--dry-run`, **When** the command runs, **Then** the plan and the report are shown, the line `Dry run: nothing was written.` appears, and `tasks.md`, the ledger and OpenProject are unchanged.
2. **Given** a real run, **When** a write to OpenProject for one task fails, **Then** the other tasks are still processed, the failed task is reported with the error text (URLs and host names redacted), and the result is `incomplete`.
3. **Given** `tasks.md` changed on disk while the command was running, **When** the command is about to write it, **Then** it does not write, tells the user, and asks to run it again.

---

### User Story 5 - Optional hook after implement (Priority: P3)

When `/speckit-implement` finishes, the user is offered to run the sync so that finished tasks reach OpenProject without a manual step. The hook is optional: it asks, it never runs unasked.

**Why this priority**: Convenience on top of the command; the command alone already closes the loop.

**Independent Test**: Install the extension, finish an implement run, and see the optional hook offered with the command name; declining it changes nothing.

**Acceptance Scenarios**:

1. **Given** the extension is installed, **When** `/speckit-implement` completes, **Then** the sync command is offered as an optional follow-up.
2. **Given** the offer is declined, **When** the user continues, **Then** nothing was read or written in OpenProject.

---

### Edge Cases

- The config has no `statuses` section, or lacks the done status: the command stops before any read or write and tells the user to run `speckit.openproject.discover-fields`.
- A configured status name does not exist in the project or is not allowed for the task type: the command stops (config problem) and names the status; it does not guess another status.
- A ledger entry points to a work package that no longer exists: reported as stale; never recreated, never removed from the ledger by this command.
- A task in `tasks.md` has no ledger entry (not yet published): reported as "unpublished" with a pointer to `speckit.taskstoissues`; nothing is created.
- A ledger entry has no matching task in `tasks.md` (task removed): reported as orphan; nothing is deleted.
- The work package is in a closed status that is not the configured done status (for example "Rejected"): reported as "closed, not done"; the checkbox is not changed, no push happens even if the task is checked, and the ledger records the status so that the next run reports no change.
- Phase and feature work packages: not changed by this feature; their status is shown in the report only.
- The ledger or `tasks.md` is missing, unreadable or invalid: the command stops and names the file; it does not rebuild anything.
- The MCP server is not connected or the project is unreadable: the command stops with a specific message and writes nothing.
- A task is checked in `tasks.md` and the ledger has no last synced status (an entry written by feature 001 before this feature): the first sync is reported as a baseline run and treats the missing base as "not done": the checked task is pushed (User Story 2), a done work package with an open task is pulled (User Story 1), and no conflict can arise because a missing base is never a change on either side.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST read the project configuration, the ledger of the current feature and the feature's `tasks.md` from disk on every run, and MUST stop before any other step if a mandatory input (config `statuses` open/done, ledger, `tasks.md`) is missing or invalid, naming what to fix.
- **FR-002**: For every task that has a ledger entry, the command MUST read the work package's current status and assignee from OpenProject and classify the task against three values: the `tasks.md` checkbox, the OpenProject status, and the status recorded at the last sync.
- **FR-003**: A task counts as done in OpenProject only when its status equals the configured done status; any other status counts as not done, and a closed status that is not the done status MUST be reported as "closed, not done" and MUST NOT trigger a push or a checkbox change (the status is only recorded in the ledger).
- **FR-004**: The command MUST apply changes that exist on one side only: a done work package checks an open task; a reopened work package unchecks a checked task; a checked task whose work package is not done is moved to the configured done status.
- **FR-004a**: If a ledger entry has no last synced status, the task MUST be classified as a baseline run with the base "not done": the result is a push or a pull as in FR-004, never a conflict, and the report MUST label the item "baseline".
- **FR-004b**: A task that was unchecked in `tasks.md` since the last sync while its work package is still in the done status MUST be resolved by OpenProject's status: the checkbox is checked again and the report names the task as "reverted". The command MUST NOT move a work package out of the done status.
- **FR-005**: The command MUST only move a work package to a status that OpenProject allows for it at that moment; a status that is not allowed MUST be reported as blocked, with the reason the server gave and the statuses available for the task type (the server reports them per type, not per current status), and MUST NOT be forced or reached through intermediate statuses (no option for this exists in this feature).
- **FR-006**: A task changed differently on both sides MUST be resolved by OpenProject's status (OpenProject wins), which gives the same result for the same input; the report MUST name every conflict, the overwritten `tasks.md` state and the resolution, and no confirmation per conflict is asked.
- **FR-007**: The command MUST record, per task, the last synced status in the ledger, and MUST record the work package's assignee in the ledger and show it in the report; the assignee MUST NOT be written to `tasks.md`.
- **FR-008**: The command MUST show a plan (one line per task with action and reason) before any write, MUST support `--dry-run` (no write on any side, line `Dry run: nothing was written.`), and without it MUST ask for confirmation once for the whole plan.
- **FR-009**: Writes to OpenProject MUST go through the server's preview-then-confirm flow and MUST be recorded in the ledger immediately after each successful write; edits to `tasks.md` MUST change only the checkbox characters of the affected task lines and leave every other byte unchanged, and MUST be applied so that the file is either unchanged or fully written.
- **FR-010**: Re-running the command on unchanged inputs MUST produce no change on any side and a report stating "no changes"; running it twice on the same input MUST produce the same plan.
- **FR-011**: The command MUST NOT create, delete, rename or re-parent any work package, MUST NOT change subject or description, and MUST NOT write phase or feature work packages.
- **FR-012**: Stale ledger entries, orphans, unpublished tasks and blocked tasks MUST be listed in the report and MUST NOT stop the processing of the other tasks.
- **FR-013**: The final report MUST show counts per outcome (pulled, pushed, unchanged, refreshed, conflicts, blocked, stale, orphan, unpublished, failed, skipped), the changed items, warnings, and one result: `complete`, `incomplete` (some task failed, is blocked or was skipped because `tasks.md` changed), `no changes` (nothing was written on any side, not even the ledger), `dry run` or `stopped`.
- **FR-014**: If a write to one work package fails, the command MUST continue with the remaining tasks, report the error text with URLs and host names redacted, and end as `incomplete`.
- **FR-015**: If `tasks.md` changes on disk between reading and writing, the command MUST NOT write it and MUST tell the user to run it again.
- **FR-016**: The extension MUST offer an optional hook after `implement` that proposes this command and never runs it without asking.
- **FR-017**: The command MUST work in skills mode (`/speckit-openproject-sync-status`) and in command mode (`/speckit.openproject.sync-status`) and MUST NOT write tokens, URLs of private instances or `.env` content anywhere.

### Key Entities

- **Task**: a line of `tasks.md` with a key (`T###`) and a checkbox that is open or done.
- **Work package status**: the OpenProject status of the work package that belongs to a task; "done" means the configured done status.
- **Ledger entry**: the record that links a task key to a work package and, new in this feature, holds the last synced status and the assignee.
- **Configured statuses**: the names for open, in progress and done from the config; the vocabulary of the sync.
- **Sync plan item**: one task with its three values (checkbox, OpenProject status, last synced status), the classified action (pull, push, none, refresh, conflict, blocked, stale, orphan, unpublished, info) and the reason.
- **Conflict**: a task whose checkbox and OpenProject status both differ from the last synced status in different ways.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the round-trip scenario (one task changed only in `tasks.md`, one only in OpenProject, one on both sides, one blocked by the workflow), every task ends either in a state that matches the report or is listed as conflict or blocked; no change on either side disappears without being named in the report.
- **SC-002**: A second run directly after a completed sync produces zero modifications to `tasks.md`, the ledger and OpenProject.
- **SC-003**: A `--dry-run` produces zero modifications to `tasks.md`, the ledger and OpenProject, and the plan it shows equals the plan of the following real run on the same input.
- **SC-004**: For a feature with 14 work packages and no conflicts, a user needs at most one confirmation and under 3 minutes of their own time from the command to the final report.
- **SC-005**: Of the changes `tasks.md` receives, 100% touch only checkbox characters: a diff of the file before and after shows no other change.
- **SC-006**: All stop conditions (missing config statuses, missing ledger, MCP server not connected, unreadable project) end with a specific message naming what to fix and with zero changes on any side.

## Assumptions

- The task work packages exist already (feature 001); this feature never creates them.
- Only the tasks' own work packages are synced; phase and feature work packages are out of scope and are shown in the report only.
- A checkbox knows two states, so "in progress" is not representable in `tasks.md`; it is kept in the ledger and the report.
- The done status is the one from `statuses.done` in the config (feature 002); other closed statuses such as "Rejected" never check a task by themselves.
- The ledger gains two optional fields per task entry (the last synced status already exists in the ledger schema; the assignee is new); the change is additive, existing ledgers stay valid.
- One sync run covers one feature (the current feature directory, or the one given as argument).
- OpenProject Community Edition and the MCP server named in `docs/mcp-tool-map.md`; the workflow check is done through what the server reports as allowed for the work package, not by reading the workflow administration.
- The hook after `implement` is optional because an automatic write to a shared system must be the user's decision (constitution III).
