# Feature Specification: Parent Status Roll-up

**Feature Branch**: `007-parent-status-rollup`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "docs/briefs/007-parent-status-rollup.md" — the status sync command also sets the phase and feature work packages from the state of their children, so that after a full sync a phase whose tasks are all done is done, and the feature is done when all its phases are. It builds on the status sync (feature 003) and on the mapping ledger (feature 001).

## Clarifications

### Session 2026-10-09

- Q: Move a parent back from done when a task is reopened? → A: No. A parent never leaves the done status through this command.
- Q: Roll-up on by default? → A: Yes; a new optional config key switches it off.
- Q: Behavior in the `after_implement` hook? → A: Unchanged; the hook runs the sync including the roll-up, no separate flag.
- Q: How does a task whose work package is in a closed status other than done (for example Rejected) count for its phase? → A: It counts as done (finished); a phase of done and rejected tasks is closed, and the report names the rejected tasks.
- Q: How does a phase count for the feature when the roll-up leaves it alone (hand-set Rejected, hand-set On hold, or no tasks)? → A: A closed one (Rejected) counts as finished, an open unmapped one (On hold) counts as in progress, a phase without tasks is ignored.
- Q: Does the roll-up get its own confirmation? → A: No. One plan lists tasks and parents, and the single "Apply this plan?" question covers both.
- Q: How is the feature rolled up when a phase write in the same run is blocked or fails? → A: From the actual status of that phase in OpenProject; a phase that was not closed does not count as finished.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Close phases and the feature when all tasks are done (Priority: P1)

A spec-kit user finishes a feature. All tasks are done in `tasks.md` and in OpenProject, but the phase work packages and the feature work package still show "New", because OpenProject does not derive a parent's status from its children. The user runs the status sync and afterwards every phase and the feature work package show the done status, without any manual bulk update.

**Why this priority**: This is the observed need. The dogfood sync of this repository on 2026-10-09 needed a manual bulk update of 53 parent work packages.

**Independent Test**: With a feature whose tasks are all done, whose phases and feature are "New", run the sync. Every phase and the feature are in the done status, the ledger records it, and a second run changes nothing.

**Acceptance Scenarios**:

1. **Given** all tasks of a phase are done, **When** the sync runs and the user accepts the plan, **Then** the phase work package is in the done status and the ledger records it.
2. **Given** all phases are done, **When** the sync runs, **Then** the feature work package is in the done status.
3. **Given** the parents already have the status the roll-up yields, **When** the sync runs again, **Then** nothing is written and the report says so.
4. **Given** the roll-up reaches the done status, **When** the parent is closed, **Then** the report notes that the server sets its percent complete to 100.

---

### User Story 2 - Show partial progress on parents (Priority: P2)

A feature is under way: some tasks are done, one is open. The user runs the sync and sees the phase that contains the open task, and the feature, as "in progress", while phases with all tasks done are done and untouched phases stay open.

**Why this priority**: Without it, parents only change at the very end and give no overview during the work.

**Independent Test**: With a feature of three phases (all done / one task open and the rest done / nothing started), run the sync. The phases are done, in progress and open in that order, and the feature is in progress.

**Acceptance Scenarios**:

1. **Given** a phase has at least one task done or in progress and at least one task not done, **When** the sync runs, **Then** the phase is in the in-progress status.
2. **Given** no task of a phase is done or in progress, **When** the sync runs, **Then** the phase is in the open status.
3. **Given** any phase is in progress or done and not all phases are done, **When** the sync runs, **Then** the feature is in the in-progress status.
4. **Given** no phase is in progress or done, **When** the sync runs, **Then** the feature is in the open status.

---

### User Story 3 - Preview and protect (Priority: P2)

The user wants to see what the roll-up would change before it writes anything, and wants parents that someone set on purpose to stay as they are.

**Why this priority**: The constitution requires every write to be previewable and safe; parents are visible to the whole team.

**Independent Test**: Run with `--dry-run` on a feature with one parent set to "Rejected" and one set to "On hold": the plan lists the roll-up for the other parents, reports the two as left alone, and nothing is written.

**Acceptance Scenarios**:

1. **Given** the roll-up would change parents, **When** the sync runs with `--dry-run`, **Then** the plan shows each parent with its current status, the status the roll-up yields and the reason, and nothing is written.
2. **Given** a parent is in a closed status other than the done status (for example "Rejected"), **When** the sync runs, **Then** it is reported and not changed.
3. **Given** a parent has a status outside the three configured statuses (for example "On hold"), **When** the sync runs, **Then** it is reported and not changed.
4. **Given** a parent write is rejected by the server or fails, **When** the sync runs, **Then** that parent is reported as blocked or failed in the same way as a task push, and the other parents continue.

---

### User Story 4 - Switch the roll-up off (Priority: P3)

A team that manages phase and feature statuses by hand disables the roll-up in the configuration; the sync then behaves exactly as before this feature.

**Why this priority**: Teams with their own parent workflow must not be surprised; existing configurations must keep working.

**Independent Test**: With the switch set to off, run the sync on a feature with all tasks done: no parent is read for the roll-up or written, and the report has no Parents section and no parents counts line; phase and feature work packages appear only as informational lines, as in 003.

**Acceptance Scenarios**:

1. **Given** the roll-up is switched off in the configuration, **When** the sync runs, **Then** no phase or feature work package is written.
2. **Given** a configuration written before this feature (no new key), **When** the sync runs, **Then** it stays valid and the roll-up is on (FR-014).

---

### Edge Cases

- A phase without any task line in `tasks.md`: the phase is left alone, reported, and ignored for the feature roll-up. A phase whose tasks are not published still has task lines; they count as not finished.
- A hand-set phase (Rejected or On hold) is not written, but still counts for the feature: Rejected as finished, On hold as in progress.
- A task without a work package (unpublished), stale or orphan: it does not count as done and is named in the report; the parent is not closed because of it.
- A phase whose tasks are all in a closed status other than done (for example all Rejected): the phase is closed with the done status, and the report names those tasks.
- A task is blocked or failed in the same run: the roll-up uses the state after the writes of this run, so a failed push does not count as done.
- `--dry-run`: the roll-up is computed from the planned task states, as if the task writes had happened.
- A parent work package is missing in OpenProject: reported as stale, never recreated.
- The ledger has a phase entry but `tasks.md` has no matching `## Phase N` heading, or the other way round: reported, no write.
- A task sits above the first phase heading or was moved under another heading after publishing, while its work package is a child of a phase in OpenProject: it counts for that phase (FR-002) and the report names it. If that phase has no heading, the task counts for no phase.
- A heading with leading zeros (`## Phase 01`) is the phase `phase-1` for both the preset and the sync; a legacy ledger key `phase-01` equals `phase-1` and is never renamed or adopted again.
- Two phase headings with the same key (`## Phase 1` and `## Phase 01`), or two ledger phase entries with the same key: the preset and the sync stop before any write and name them.
- The sync accepts any `## Phase N` heading; the preset publishes only `## Phase N:` with a colon, so a heading without a colon is an `unpublished phase`.
- The configured statuses `open`, `in_progress` or `done` are missing: the roll-up cannot run and the command stops with the existing message that points to field discovery.
- A task is reopened after its phase was closed: the phase stays done (FR-013); a manual reopen of the phase in OpenProject is needed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sync MUST derive the status of each phase work package from the statuses of its tasks after the task pushes and pulls of the same run: done if all tasks are finished, in progress if at least one task is finished or in progress, otherwise open. A task is finished when its work package is in the done status or in any other closed status (for example Rejected); the report names every task that counted as finished through a closed status other than done.
- **FR-002**: A task line belongs to the phase whose ledger `id` equals the `parent_id` of the task work package as read by the sync. If no ledger phase matches, or the work package has no parent or was not read, it belongs to the phase of the nearest `## Phase N` heading above it, which is the ledger entry `phase-N` (N without leading zeros). A task line with neither, an orphan ledger entry, a task line whose parent phase has no heading, and a task line whose heading phase has no ledger entry belong to no phase and are named in the report (`T### not counted: …`). A task counted for another phase than the heading it sits under is named in the report.
- **FR-003**: The sync MUST derive the status of the feature work package from its phases: done if all phases are finished, in progress if any phase is in progress or finished, otherwise open. A phase is finished when its status (rolled up in this run, or left alone) is the done status or another closed status; a left-alone phase in an open status outside the three configured statuses (for example On hold) counts as in progress; a phase without tasks is ignored. If every phase is ignored, the feature is left alone and reported. Phases are written before the feature; a phase whose write was blocked or failed counts with the status it actually has in OpenProject, never with the rolled-up status.
- **FR-004**: The sync MUST write only the status of a parent, using the same two-step flow (preview, then confirm) and the same failure classes as the task pushes. The parent changes are part of the one plan of the run and are covered by its single confirmation question; there is no separate question for parents.
- **FR-005**: The sync MUST NOT change a parent that is in a closed status other than the configured done status, and MUST report it.
- **FR-006**: The sync MUST NOT change a parent whose status is outside the three configured statuses, and MUST report it.
- **FR-007**: The ledger MUST record the status of a parent the same way as for a task, after each confirmed write and after a read that finds the parent already in the rolled-up status.
- **FR-008**: A second run with unchanged tasks MUST write nothing and change nothing.
- **FR-009**: `--dry-run` MUST show the parent plan (parent, current status, rolled-up status, reason) and write nothing.
- **FR-010**: The configuration MUST offer an optional new key to switch the roll-up off. Existing keys are neither renamed nor removed and existing configurations stay valid.
- **FR-011**: The report MUST list the parents that were rolled up, left alone and why, blocked, failed or stale, and MUST state that closing a parent makes the server set its percent complete to 100.
- **FR-012**: The roll-up MUST NOT run when the task part of the run stopped before finishing; tasks that are blocked, failed, stale, orphan or unpublished never count as done.
- **FR-013**: The roll-up MUST NOT move a parent out of the done status, even when one of its tasks is reopened (consistent with feature 003, which never moves a work package out of done). Reopening a task in a done phase is not reported as an error.
- **FR-014**: The roll-up MUST be on by default; the configuration switch only turns it off.
- **FR-015**: The `after_implement` hook runs the status sync unchanged, so the roll-up is part of it; there is no separate flag for the hook.

### Key Entities

- **Parent work package**: a phase or feature work package from the ledger (`kind` phase or feature). Its status is rolled up from its children and is the only thing written.
- **Roll-up plan**: per parent, the current status, the rolled-up status and the reason, shown before any write.
- **Ledger status of a parent**: the last status the sync saw or wrote, stored like a task status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a feature with all tasks done, one run puts every phase and the feature in the done status; no manual bulk update is needed (the observed case needed 53 manual updates).
- **SC-002**: On a feature with exactly one open task, the phase of that task and the feature are in progress and every other phase is done, after one run.
- **SC-003**: A second run on an unchanged feature writes nothing (0 writes).
- **SC-004**: A parent in "Rejected" or "On hold" is never changed by the sync (0 overwrites) and is named in the report.
- **SC-005**: With `--dry-run`, 0 work packages and 0 files change, and the plan lists every parent.
- **SC-006**: With the roll-up switched off, a run produces the same writes as before this feature.

## Assumptions

- Feature 003 (status sync) and the statuses configuration from feature 002 exist; the three statuses `open`, `in_progress` and `done` are set, as the sync already requires `done`.
- Phase and feature work packages exist in the ledger because `speckit.taskstoissues` created them; this feature creates, deletes and re-parents nothing.
- The server sets percent complete to 100 when a parent moves to a closed status; this cannot be avoided and is only reported.
- A task counts as in progress when its work package status equals the configured in-progress status.
- Workflows for phase and feature types may forbid a transition; this is reported per parent as blocked with the server's reason, like for tasks, with no intermediate steps.
- Out of scope: other fields of a parent (dates, progress, assignee), parents of other features, and any change to the task rules of feature 003.
