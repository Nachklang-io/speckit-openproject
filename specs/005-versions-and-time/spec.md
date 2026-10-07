# Feature Specification: Versions and Time Tracking

**Feature Branch**: `005-versions-and-time`

**Created**: 2026-10-07

**Status**: Draft

## Clarifications

### Session 2026-10-07

- Q: How does `log-time` recognise a re-run? → A: By a ledger key (work package, date, activity, hours); an optional `--entry-key` allows a deliberate second identical entry. No reading of existing OpenProject time entries for matching.
- Q: What if a work package is already in another version? → A: Keep it and report "other version"; never reassign.

**Input**: User description: "docs/briefs/005-versions-and-time.md" — two commands for the extension. The first maps a feature to an OpenProject version (created once, after confirmation) and assigns the feature's work packages to it. The second, `speckit.openproject.log-time`, logs time entries on work packages from durations the user supplies, with an activity chosen from the project's activity list. Both are idempotent through the mapping ledger (feature 001).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Map a feature to a version (Priority: P1)

After the work packages exist, the project manager wants the feature to appear as a milestone in the OpenProject roadmap. The user runs the version command; it finds the version for the feature or proposes to create it, asks once for confirmation, and assigns all work packages of the feature to that version.

**Why this priority**: Roadmap and release views in OpenProject work on versions; without this the feature is invisible there.

**Independent Test**: With a published feature (ledger with feature, phase and task work packages) and no version for it, run the command and accept the plan. One version exists, and every work package from the ledger shows that version (scenario S22).

**Acceptance Scenarios**:

1. **Given** a published feature and no matching version in the project, **When** the command runs and the user accepts the plan, **Then** exactly one version is created, all ledger work packages are assigned to it, and the ledger records the version.
2. **Given** a version with the intended name already exists in the project, **When** the command runs, **Then** it is reused; no second version is created.
3. **Given** the command already completed, **When** it runs again without changes, **Then** nothing is written and the report says "no changes".
4. **Given** new tasks were added to the feature since the last run, **When** the command runs, **Then** only the new work packages are assigned.

---

### User Story 2 - Log time on work packages (Priority: P1)

A developer who has finished a task tells the command how long it took ("T012: 1h30, T013: 45m"). The command shows the planned entries with the activity, asks once, and creates one time entry per item on the matching work package.

**Why this priority**: Time tracking is the second half of the brief and closes the loop from implementation to project accounting.

**Independent Test**: With a published feature, run the command with two durations for two tasks and accept the plan. Each of the two work packages has one new time entry with the stated hours, today's date (or the given date) and the chosen activity (scenario S23).

**Acceptance Scenarios**:

1. **Given** a task with a work package in the ledger and a duration, **When** the command runs and the user accepts, **Then** a time entry with that duration, date and activity exists on the work package and is recorded in the ledger.
2. **Given** the user does not name an activity, **When** the command runs, **Then** the available activities are listed (from the project) and the user picks one before anything is written; a configured default is used without asking.
3. **Given** the same command input is run again, **When** the entries already exist, **Then** no duplicate entry is created: an entry is recognised by a ledger key made of work package, date, activity and hours.
4. **Given** the user wants a deliberate second entry with identical work package, date, activity and hours, **When** they supply an explicit entry key (`--entry-key`), **Then** the entry is created once and recognised by that key on re-runs.
5. **Given** a task key that is not in the ledger, **When** the command runs, **Then** that item is reported as unknown and nothing is written for it; the other items continue.

---

### User Story 3 - Preview, safe writes and an honest report (Priority: P2)

Both commands start with a plan table, support `--dry-run`, ask for one confirmation, use the server's preview-then-confirm flow for each write, and record each successful write in the ledger immediately, so an interrupted run can be repeated.

**Why this priority**: Constitution rules for every write path.

**Independent Test**: Run each command with `--dry-run`: plan shown, line `Dry run: nothing was written.`, ledger and OpenProject unchanged. Interrupt a real run after the version was created but before all assignments were done and run again: still one version (scenario S24).

**Acceptance Scenarios**:

1. **Given** `--dry-run`, **When** either command runs, **Then** the plan and report are shown and nothing is written on any side.
2. **Given** a run interrupted after the version was created, **When** the command runs again, **Then** the existing version is reused and the remaining work packages are assigned.
3. **Given** one write fails, **When** the command runs, **Then** the other items are still processed, the error is reported with URLs and host names redacted, and the result is `incomplete`.

---

### User Story 4 - Clear stops on missing prerequisites (Priority: P2)

If the ledger, config or the project's write permission for versions or time entries is missing, the user is told what to fix, and nothing is written.

**Why this priority**: Version writes and time entries are feature-flagged on the MCP server; the first real install must fail clearly.

**Independent Test**: Run each command against a server with the matching write capability disabled: the command stops before any write and names the capability and the setting (scenario S25).

**Acceptance Scenarios**:

1. **Given** the version or time-entry write capability is not available, **When** the command runs (also with `--dry-run`), **Then** it stops with a message naming the capability and the server setting that enables it.
2. **Given** the ledger has no feature work package, **When** either command runs, **Then** it stops and names the fix (run `speckit.taskstoissues` first).

---

### Edge Cases

- A work package from the ledger is already assigned to a different version: it is left unchanged and reported as "other version"; the command never reassigns it (a later opt-in option may).
- The matching version exists but is closed or locked: the command stops for the assignment step, reports it, and creates nothing.
- A work package from the ledger no longer exists in OpenProject: reported as stale, skipped, others continue; nothing is recreated.
- Time entries: a duration that cannot be parsed, is zero or negative, or exceeds 24 hours per entry is rejected in the plan before any write.
- Time entries: a date in the future is rejected; no date means today.
- The user has no permission to log time on a work package: that item fails, the others continue.
- The MCP server is not connected or the project is unreadable: stop with a specific message, no write.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both commands MUST read the configuration, the ledger of the current feature and the feature directory on every run and MUST stop before any write if a mandatory input is missing or invalid (config `project`, ledger with the feature work package), naming what to fix.
- **FR-002**: The version command MUST determine the intended version name (default: the feature directory name; overridable by a config key and by an argument), look for a version of that name in the project, and create it only if none exists and the user has confirmed.
- **FR-003**: The version command MUST assign every work package listed in the ledger (feature, phases, tasks) to the version, and MUST skip work packages that already carry it.
- **FR-004**: The ledger MUST record the version (identifier and name) and, per time entry, what is needed to recognise it on a re-run; the change MUST be additive so that existing ledgers stay valid.
- **FR-005**: The time command MUST accept durations from the user per task key or work package, in a documented human format (for example `1h30`, `45m`, `1.5h`), plus an optional date per item and an optional activity.
- **FR-006**: The time command MUST read the available activities of the project, MUST use the chosen activity by its exact name, and MUST ask the user to choose when none is given and no default is configured.
- **FR-007**: The time command MUST create exactly one time entry per accepted plan item with the correct work package, hours, date and activity, and MUST NOT create a second entry for an item already recorded in the ledger (recognition: ledger key of work package, date, activity and hours, or an explicit user-supplied entry key).
- **FR-008**: Neither command MUST delete or modify existing versions, existing time entries or any other data; the commands only create a version, set the version of work packages, and create time entries.
- **FR-009**: Both commands MUST show a plan before any write, MUST support `--dry-run` (no write, line `Dry run: nothing was written.`), and without it MUST ask for confirmation once for the whole plan.
- **FR-010**: Writes MUST go through the server's preview-then-confirm flow and MUST be recorded in the ledger immediately after each successful write.
- **FR-011**: If the write capability for versions or for time entries is not available on the MCP server, the matching command MUST stop before any write, also in `--dry-run`, naming the capability and the server setting that enables it.
- **FR-012**: Failure of one item MUST NOT stop the others; the report MUST name the error with URLs and host names redacted, and the run ends as `incomplete`.
- **FR-013**: Each final report MUST show counts per outcome (created, assigned, reused, unchanged, skipped, stale, failed), the changed items, warnings, and one result: `complete`, `incomplete`, `no changes`, `dry run` or `stopped`.
- **FR-014**: Both commands MUST work in skills mode (`/speckit-openproject-<name>`) and command mode (`/speckit.openproject.<name>`) and MUST NOT write tokens, private instance URLs or `.env` content anywhere.

### Key Entities

- **Feature version**: the OpenProject version that represents the feature; identified by name within the project, recorded in the ledger.
- **Version assignment**: the link between a work package from the ledger and the feature version.
- **Time entry request**: one line of user input (task or work package, duration, optional date, optional activity).
- **Activity**: a project-defined category of work, chosen from the project's list.
- **Ledger time record**: additive ledger entry that recognises an already created time entry on a re-run.
- **Plan item**: one planned write with its target, action and reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a completed version run, the project contains exactly one version for the feature and 100% of the ledger work packages carry it.
- **SC-002**: A second run of either command with the same input produces zero modifications in OpenProject and the ledger.
- **SC-003**: Every created time entry shows the stated hours, date and activity; a spot check of all entries of a run finds no deviation.
- **SC-004**: A `--dry-run` produces zero modifications, and its plan equals the plan of the following real run on the same input.
- **SC-005**: Interrupting a real run at any point and repeating it never produces a second version or a duplicate time entry.
- **SC-006**: All stop conditions (missing capability, missing ledger, server not connected) end with a message naming what to fix and zero changes.
- **SC-007**: A user needs at most one confirmation and under 2 minutes of their own time from command to final report for ten work packages (version) or five time entries (time).

## Assumptions

- The work packages exist and are listed in the ledger (feature 001); neither command creates work packages.
- Tool names and the exact write flags of `jtauschl/openproject-ce-mcp` v0.4.1 (version creation, version assignment through work package update, time entries, activity list) are verified against a running server in the first task of the plan.
- The version command and the time command are two separate commands in the extension (`speckit.openproject.sync-version` and `speckit.openproject.log-time`); the version command name is a plan decision.
- Time entries are logged for the user of the MCP token; logging for other users is out of scope.
- Hours are stored with a resolution the server accepts; rounding rules are a plan decision.
- Version dates (start, due) are not set by default; whether a config key may set them is a plan decision.
- One run covers one feature (current feature directory, or the one given as argument).
- Time entries created outside this command are not detected as duplicates.
