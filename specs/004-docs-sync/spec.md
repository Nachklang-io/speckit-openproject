# Feature Specification: Documentation Sync to the Feature Work Package

**Feature Branch**: `004-docs-sync`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "docs/briefs/004-docs-sync.md" — a command that publishes a feature's design documents (`spec.md`, `plan.md`, optionally `research.md` and `data-model.md`) to the feature work package in OpenProject: each file is attached, an outdated attachment is replaced when the file's content changed, and a generated summary with links is kept in the work package description. Wiki pages cannot be created through the API (ADR-0003). It builds on the mapping ledger (feature 001), which knows the feature work package.

## Clarifications

### Session 2026-10-06

- Q: In which order is a changed attachment replaced? → A: Upload the new attachment first, then delete the old one (identified by the attachment id in the ledger). An interruption can leave two attachments for a moment; the next run deletes the old one.
- Q: What does the generated summary contain? → A: A purely mechanical list per document: file name, link to its attachment, short hash and the date the document was last synced as changed. No excerpts and no model-written text, so the same input always yields the same summary.
- Q: What happens when the attachment upload capability is missing? → A: The command stops before any write (also with `--dry-run`) and names the missing capability and the server setting that enables it; there is no description-only fallback, because it would link to attachments that do not exist.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish the design documents (Priority: P1)

After specify and plan, the spec-kit user runs the sync command. Team members who only use OpenProject find `spec.md` and `plan.md` as attachments on the feature work package, and a summary in its description that names each document and links to it.

**Why this priority**: This is the point of the feature: stakeholders read the contract and the plan where they work, without access to the repository.

**Independent Test**: With a published feature (ledger with a feature work package) and a `spec.md` and `plan.md` in the feature directory, run the command and accept the plan. The parent work package has exactly two attachments with the file names and a summary block in its description (scenario S18).

**Acceptance Scenarios**:

1. **Given** a feature with `spec.md` and `plan.md` that were never synced, **When** the command runs and the user accepts the plan, **Then** both files are attached to the feature work package, the description holds a generated summary listing both with links, and the ledger records the content hash of each file.
2. **Given** the optional documents (`research.md`, `data-model.md`) exist, **When** the command runs, **Then** they are synced as well; if they do not exist, they are skipped without a warning.
3. **Given** a feature directory without `spec.md`, **When** the command runs, **Then** it stops and names the missing file; nothing is written.

---

### User Story 2 - Update only what changed (Priority: P1)

The user edits `spec.md` and runs the command again. Only that document is replaced: the outdated attachment is removed, the new content is attached under the same file name, and the summary shows the new state. Unchanged documents cause no write at all.

**Why this priority**: It is the acceptance criterion of the brief and the idempotence rule of the constitution.

**Independent Test**: After one sync, change one line of `spec.md` and run the command: one attachment is replaced, the summary is updated, `plan.md`'s attachment is untouched. Run again without changes: nothing is written anywhere (scenario S19).

**Acceptance Scenarios**:

1. **Given** a synced feature and a changed `spec.md`, **When** the command runs, **Then** the feature work package ends with exactly one attachment named `spec.md` holding the new content, the other attachments are untouched, and the summary and the ledger hash are updated.
2. **Given** no document changed, **When** the command runs, **Then** nothing is written to OpenProject or the ledger and the report says "no changes".
3. **Given** a document whose attachment was removed in OpenProject by someone else, **When** the command runs, **Then** the file is attached again and the report lists it as "restored".
4. **Given** a document was deleted from the feature directory, **When** the command runs, **Then** its attachment is left in place and the report lists it as "orphan"; nothing is deleted.

---

### User Story 3 - Preview, safe writes and an honest report (Priority: P2)

Every run starts with a plan table (one line per document: file, hash state, action, reason). With `--dry-run` nothing is written. Without it the user confirms once; uploads and description changes go through the server's preview-then-confirm flow; an interrupted run can simply be repeated without duplicate attachments.

**Why this priority**: Constitution rules for every write path: dry-run, preview-then-confirm, idempotence.

**Independent Test**: Run `--dry-run` on the S19 setup: plan shown, the line `Dry run: nothing was written.`, checksums of the ledger and the attachment list unchanged. Interrupt a real run after the upload of one file and run again: no duplicate attachment (scenario S20).

**Acceptance Scenarios**:

1. **Given** `--dry-run`, **When** the command runs, **Then** the plan and report are shown and nothing is written on any side.
2. **Given** a run interrupted after the new attachment was uploaded but before the old one was deleted, **When** the command runs again, **Then** it deletes the outdated attachment (the one named by the ledger) and no duplicate remains.
3. **Given** one upload fails, **When** the command runs, **Then** the other documents are still processed, the error is reported with URLs and host names redacted, and the result is `incomplete`.

---

### User Story 4 - Clear stop when uploads are not possible (Priority: P2)

The attachment upload tool of the MCP server is only available when the server is configured with an upload directory. If the tool is not available, the user is told exactly what to configure, and nothing is written.

**Why this priority**: Without it the feature fails in a confusing way on the first real install.

**Independent Test**: Run the command against a server without the upload tool: the command stops before any write and names the missing capability and the server setting to change (scenario S21).

**Acceptance Scenarios**:

1. **Given** the upload capability is missing, **When** the command runs (also with `--dry-run`), **Then** it stops with a message naming the capability and the fix, and no write happens.
2. **Given** a document is larger than the server accepts, **When** the command runs, **Then** that document is reported as failed with the limit, the others continue.

---

### Edge Cases

- The ledger has no feature work package, or the ledger or config is missing or invalid: the command stops and names what to fix (run `speckit.taskstoissues` first); it does not create the work package.
- The feature work package no longer exists in OpenProject: reported as stale, stop; nothing is recreated.
- The description of the feature work package contains text written by users: only the generated summary block between fixed markers is replaced; all text outside the markers is preserved byte for byte. If the markers are missing, the block is appended once.
- Two attachments with the same file name exist on the work package (not created by this command): the command stops for that document, reports the ambiguity and changes nothing for it.
- The attachment content cannot be compared with the local file (read failure): the ledger hash decides; the file is treated as unchanged if the hash matches and the attachment exists.
- A document contains secrets or URLs of private instances: the command does not scan for them; the user is responsible for what the documents hold (constitution: nothing from `.env` is ever read).
- The MCP server is not connected or the project is unreadable: stop with a specific message, no write.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST read the configuration, the ledger of the current feature and the feature directory on every run, and MUST stop before any write if a mandatory input is missing or invalid (config `project`, ledger with the feature work package, `spec.md`), naming what to fix.
- **FR-002**: The command MUST sync `spec.md` and `plan.md` when present and MUST sync `research.md` and `data-model.md` when present; absent optional documents are skipped silently, a missing `plan.md` is reported as a warning.
- **FR-003**: For each document the command MUST compare the content hash of the local file with the hash recorded in the ledger and with the attachments currently on the feature work package, and classify it as new, changed, unchanged, restored, orphan or blocked (a state that cannot be resolved without deleting an attachment this command did not create).
- **FR-004**: A changed document MUST end as exactly one attachment under its file name with the new content. The new attachment MUST be uploaded first and the outdated one (identified by the attachment id in the ledger) deleted afterwards; the ledger MUST be updated with the new attachment id right after the upload, so that a repeated run finds and deletes the outdated one.
- **FR-005**: An unchanged document MUST cause no write to OpenProject and no write to the ledger.
- **FR-006**: The command MUST keep a generated summary in the feature work package description, inside fixed markers, listing each synced document with its file name, a working link to its attachment (a path without host), its short hash and the date it was last synced as changed, and nothing else (no excerpts, no model-written text), so that the same input always yields the same summary; text outside the markers MUST NOT be changed.
- **FR-007**: The ledger MUST record, per document, the content hash and the attachment identifier of the last sync; the change MUST be additive so that existing ledgers stay valid.
- **FR-008**: The command MUST show a plan before any write, MUST support `--dry-run` (no write, line `Dry run: nothing was written.`), and without it MUST ask for confirmation once for the whole plan.
- **FR-009**: Writes to OpenProject MUST go through the server's preview-then-confirm flow and MUST be recorded in the ledger immediately after each successful write.
- **FR-010**: If the attachment upload capability of the MCP server is not available, the command MUST stop before any read-for-write step with a message naming the capability and the server setting that enables it, also in `--dry-run`.
- **FR-011**: The command MUST NOT create, delete or re-parent work packages, MUST delete only an attachment it uploaded itself and replaced (identified by the ledger id; this exception to the constitution's no-deletion rule is recorded in ADR-0004), and MUST NOT change anything outside the summary block of the description.
- **FR-012**: Failure of one document MUST NOT stop the others; the report MUST name the error with URLs and host names redacted, and the run ends as `incomplete`.
- **FR-013**: The final report MUST show counts per outcome (attached, replaced, restored, cleaned, unchanged, orphan, blocked, failed, skipped), the changed items, warnings, and one result: `complete`, `incomplete`, `no changes`, `dry run` or `stopped`.
- **FR-014**: The command MUST work in skills mode (`/speckit-openproject-sync-docs`) and in command mode (`/speckit.openproject.sync-docs`) and MUST NOT write tokens, private instance URLs or `.env` content anywhere.

### Key Entities

- **Document**: a design file of the feature directory (`spec.md`, `plan.md`, optionally `research.md`, `data-model.md`) with a content hash.
- **Document attachment**: the attachment on the feature work package that holds the last synced content of a document.
- **Summary block**: the generated, marker-delimited part of the feature work package description.
- **Ledger document entry**: record of a document's hash and attachment identifier at the last sync (new, additive).
- **Sync plan item**: one document with its local hash, ledger hash, attachment state, classified action and reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After changing one line of `spec.md` and running the command, exactly one attachment differs from before, the summary reflects the change, and every other attachment and every character of the description outside the summary block is identical.
- **SC-002**: A second run directly after a completed sync produces zero modifications in OpenProject and the ledger.
- **SC-003**: A `--dry-run` produces zero modifications, and its plan equals the plan of the following real run on the same input.
- **SC-004**: Interrupting a real run at any point after the ledger recorded the upload and running again never leaves two attachments with the same document name. An interruption between an upload and its ledger entry leaves one unknown duplicate; the next run reports it as `blocked` and deletes nothing.
- **SC-005**: All stop conditions (missing upload capability, missing ledger, missing `spec.md`, server not connected) end with a message naming what to fix and zero changes.
- **SC-006**: A user needs at most one confirmation and under 2 minutes of their own time from command to final report for four documents.

## Assumptions

- The feature work package exists in the ledger (feature 001); this feature never creates it.
- OpenProject does not version attachments: "new version" means the old attachment is replaced by one with the same file name and the new content.
- The content hash is computed over the file bytes; the hash algorithm and encoding are a plan decision.
- The upload capability depends on the MCP server being configured with an upload directory (`OPENPROJECT_ATTACHMENT_ROOT`); the tool schema of `jtauschl/openproject-ce-mcp` v0.4.1 was read on 2026-10-06: the tool takes a file path under that directory (no inline content, no file name parameter). Upload, attachment name and path rules are verified against a running server in the first task of the plan.
- Only the documents named in FR-002 are synced; `tasks.md` is out of scope (feature 003 covers its status).
- ADR-0003 stays valid and is re-verified here: no wiki page creation, attachments plus description.
- One run covers one feature (current feature directory, or the one given as argument).
