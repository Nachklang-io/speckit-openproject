# Feature Specification: Field Discovery and Config Bootstrap

**Feature Branch**: `002-field-discovery`

**Created**: 2026-10-05

**Status**: Draft

**Input**: User description: "docs/briefs/002-field-discovery.md" — a command that reads the target OpenProject project's types, statuses, priorities, versions and custom fields (including mandatory ones) and writes or updates the integration config interactively, proposing mappings for phase/task types and status names, never overwriting user edits without showing a diff.

## Clarifications

### Session 2026-10-05

- Q: Does this feature add a status mapping to the config, or only display statuses? → A: It adds an optional, additive `statuses` section (open / in progress / done → OpenProject status name); feature 003 consumes it.
- Q: What happens when the user cannot or will not give a value for a mandatory custom field? → A: The config is still written without that value; the command warns, names the field and type, and reports the result as "incomplete". No placeholder value is invented.
- Q: Does an approved change edit only the approved keys or rewrite the whole file? → A: Only the approved keys are changed; comments, key order and valid keys the command does not manage stay as they are. Keys unknown to the schema make the config invalid (`speckit.taskstoissues` stops on them too); see the invalid-config edge case. Where that is not possible, the diff says so before anything is written.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bootstrap a valid config from scratch (Priority: P1)

A team has installed the integration into a spec-kit project and has no config yet. They run the discovery command once, confirm a few proposals (which project, which type plays feature/phase/task, which defaults), and end up with a complete config that the other commands accept without further editing.

**Why this priority**: This is the acceptance criterion of the brief. Today every user must hand-write the config and learn type and custom-field names by trial and error (feature 001 fails late when a type is not enabled or a custom field is mandatory).

**Independent Test**: In a fresh spec-kit project with no config, run the command against the sandbox project (scenario S10). Exactly one run produces a config file that validates against the shared config schema and with which `speckit.taskstoissues --dry-run` reports no configuration errors.

**Acceptance Scenarios**:

1. **Given** no config file exists and the MCP server is reachable, **When** the user runs the command and accepts the proposals, **Then** a config file is written that validates against the shared config schema and contains project, feature/phase/task types and any mandatory custom fields.
2. **Given** the project has no type named "Phase", **When** proposals are shown, **Then** the closest built-in alternative is proposed for phase and the user is told why; the user can pick any enabled type instead.
3. **Given** the target project has a mandatory custom field for the task type, **When** discovery runs, **Then** the field is listed with its type and allowed values, the user is asked for a value, and the answer is stored so that task creation will not be blocked.

---

### User Story 2 - Update an existing config without losing edits (Priority: P1)

A user already has a config with hand-made edits (comments, extra values, a changed default). They re-run discovery after the OpenProject admin enabled a new type or custom field. The command shows exactly what would change and only applies what the user approves.

**Why this priority**: Constitution principle III (safe by default) and the brief's explicit rule: never overwrite user edits without showing a diff.

**Independent Test**: Edit a generated config by hand, re-run (S11): a diff is shown, declining leaves the file byte-identical, accepting changes only the approved keys.

**Acceptance Scenarios**:

1. **Given** an existing config whose values still match what OpenProject offers, **When** discovery runs, **Then** it reports "no changes" and the file is not modified.
2. **Given** an existing config where the user changed a value that differs from the proposal, **When** discovery runs, **Then** the user's value is kept by default, the difference is shown, and it is replaced only after explicit approval.
3. **Given** a diff is shown, **When** the user declines, **Then** the config file is unchanged.
4. **Given** the config references a type that is no longer enabled in the project, **When** discovery runs, **Then** the stale value is flagged in the diff with a proposed replacement; it is not silently changed.

---

### User Story 3 - Preview with dry run (Priority: P2)

A user wants to see what discovery would write without touching any file.

**Why this priority**: Required by the constitution for every write command; the write here is local, so it is lower risk than OpenProject writes, hence P2.

**Independent Test**: Run with `--dry-run` (S12): proposals and diff are shown, no file is created or modified.

**Acceptance Scenarios**:

1. **Given** any state of the config, **When** the user runs the command with `--dry-run`, **Then** the proposed content or diff is shown and no file is written.

---

### User Story 4 - Inspect what the project offers (Priority: P2)

A user wants a readable overview of the project's enabled types, statuses, priorities, versions and custom fields (marking which are mandatory for which type), for example to decide on mappings or to brief an admin.

**Why this priority**: The discovered data is the basis for the proposals, and showing it makes the proposals explainable (constitution VI: decisions are surfaced, not guessed).

**Independent Test**: Run the command and stop at the overview step; the overview matches what the OpenProject web UI shows for the project (S10).

**Acceptance Scenarios**:

1. **Given** a reachable project, **When** discovery runs, **Then** the overview lists enabled types, statuses, priorities, open versions and custom fields, and marks mandatory custom fields per type.

---

### User Story 5 - Fail early with clear diagnostics (Priority: P2)

A user runs discovery with the MCP server unavailable, the project unknown, or a project they may not read. The command stops before writing anything and says what to fix, without exposing secrets.

**Why this priority**: First contact with the integration is this command; unclear failures here cost the most goodwill.

**Independent Test**: Run with an unknown project, with a project outside the server's allowlist, and with the MCP server not configured (S13); each stops with a specific message and no file change.

**Acceptance Scenarios**:

1. **Given** the MCP server is not configured or unreachable, **When** the command runs, **Then** it stops, names the missing capability and how to configure the server, and writes nothing.
2. **Given** the project identifier is unknown or not readable, **When** the command runs, **Then** it stops with a message naming the project and writes nothing.
3. **Given** the project is not set anywhere, **When** the command runs, **Then** it lists the readable projects and asks the user to choose.

---

### Edge Cases

- A project with no versions, or only closed versions: versions are shown as "none open" and no default version is proposed.
- Several types plausibly fit one role (for example two summary-like types): all candidates are shown with a recommendation; the user decides.
- A custom field is mandatory for the task type but not for the feature type (or vice versa): the config stores values only for what is required for the types actually used.
- A mandatory custom field has a type for which no sensible value can be proposed (for example a user or multi-select field): the user is asked, and the command does not invent a value; if no value is given, the config is written without it and the run is reported as "incomplete" (FR-007).
- The existing config file is invalid (YAML or schema errors): the command reports the problems and offers to rebuild from discovery results, showing the diff; it never discards the file silently.
- The existing config contains comments or valid keys the command does not manage: they are kept as they are and the diff only touches approved keys. Keys unknown to the schema are rule violations: the command lists them and, only after approval of the rebuild shown as a diff, drops them (as with any other invalid config).
- Names differing only by case or whitespace between config and OpenProject: treated as a mismatch and shown, not auto-corrected.
- The user interrupts mid-way: the config file is either unchanged or fully written, never half-written.
- The instance is large (many projects, many versions): the command reads only what is needed for the target project and reports when a list was truncated.
- The user runs the command in a project that has the preset but not the extension config location yet: the directory is created as needed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST read from the target project: enabled work package types, statuses, priorities, open versions and custom fields, including which custom fields are mandatory for which type.
- **FR-002**: The command MUST access OpenProject only through the configured MCP server and MUST report a clear error and stop when a required capability is not available.
- **FR-003**: The command MUST determine the target project from, in order, a command argument, the existing config, an environment variable, and finally by listing readable projects and asking the user.
- **FR-004**: The command MUST present an overview of the discovered data before proposing any mapping.
- **FR-005**: The command MUST propose a type for each of feature, phase and task from the project's enabled types, explain the reasoning, and let the user pick any enabled type instead.
- **FR-006**: The command MUST set optional defaults (priority, version, assignee) only when the user asks for them. Priority and version MUST be chosen from values that exist in the project; the assignee is taken as the user enters it and is not verified. Defaults the user does not ask for stay empty.
- **FR-007**: The command MUST ask the user for a value for every custom field that is mandatory for a used type and not yet in the config, and store the answers in the config's required-custom-fields section. If the user gives no value, the command MUST still write the config without that value, MUST warn naming the field and the type it is mandatory for, MUST NOT invent a placeholder value, and MUST report the run result as "incomplete" in the final summary.
- **FR-008**: The command MUST write a config that validates against the shared config schema; it MUST validate before writing and refuse to write invalid content.
- **FR-009**: When a config already exists, the command MUST keep all existing values by default, show a diff of every proposed change, and apply a change only after explicit user approval.
- **FR-010**: Declining the diff, `--dry-run`, or an interruption MUST leave the config file unchanged.
- **FR-011**: The command MUST NOT write API tokens, instance URLs or other secrets to any file or output, and MUST NOT modify anything in OpenProject.
- **FR-012**: Re-running the command with an unchanged project and unchanged config MUST report "no changes" and MUST NOT modify the file (idempotent).
- **FR-013**: The command MUST work in skills mode and command mode and MUST support a `--dry-run` argument.
- **FR-014**: The command MUST apply an approved change by editing only the approved keys, leaving comments, key order and valid keys it does not manage untouched. Where an edit cannot preserve something (for example a comment attached to a replaced value), the diff MUST say so before anything is written.
- **FR-015**: The command MUST propose, from the project's statuses, a mapping of spec-kit task states (open, in progress, done) to OpenProject status names and store it in a new optional config section `statuses`. The section is additive: configs without it stay valid, no shipped key is renamed or removed, and the shared config schema is extended accordingly. The mapping is consumed by feature 003 (status sync); this feature only writes it.
- **FR-016**: The command MUST summarize at the end what was read, what was proposed, what was written or skipped, and the next recommended command. It MUST also list any `SPECKIT_OPENPROJECT_*` environment variable that is set, because write commands resolve those after the config file and a stale value can hide the discovered config.

### Key Entities *(include if feature involves data)*

- **Discovery snapshot**: The read-only view of the target project at one point in time: enabled types, statuses, priorities, open versions, custom fields with their applicability and mandatory flag per type.
- **Integration config**: The per-project file holding the target project, the type mapping, defaults, and values for mandatory custom fields; the single contract between this command and all write commands.
- **Proposal**: A suggested value for one config key with a short reason, derived from the snapshot; becomes part of the config only after user approval.
- **Config diff**: The human-readable difference between the existing config and the proposals, shown before any write.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with a fresh project and no config reaches a valid config in a single run in under 5 minutes, answering only questions about choices (no file editing).
- **SC-002**: 100% of configs written by the command validate against the shared config schema.
- **SC-003**: After a bootstrap run, `speckit.taskstoissues --dry-run` against the same project reports zero configuration errors (unknown type, missing mandatory custom field) in the sandbox scenario, provided the run was not reported as "incomplete".
- **SC-004**: Re-running on an unchanged project and config produces zero file modifications.
- **SC-005**: In the edit-and-re-run scenario, 100% of user-edited values survive unless the user explicitly approves their replacement.
- **SC-006**: All failure scenarios (no server, unknown project, unreadable project) end with a specific message and zero file changes. For an invalid existing config, the file stays unchanged unless the user approves the proposed rebuild.

## Assumptions

- The user has an MCP server with read access to the target project; the tested target is the default server named in the constitution, and tool names are resolved through the shared capability table.
- Discovery is read-only towards OpenProject; creating types, statuses or custom fields is impossible via the API and out of scope (the command may tell the user what an admin would need to enable).
- The config location and format stay as shipped by feature 001; shipped keys are never renamed or removed. The only addition is the optional `statuses` section (FR-015), a backward-compatible schema change.
- One config per spec-kit project and one target project per config; multi-project configs are out of scope.
- Dependency: feature 001 (shared schemas and config conventions) is merged.
- Out of scope: writing anything to OpenProject, status synchronisation itself (feature 003), version creation (feature 005), and interactive editing of the mapping ledger.
