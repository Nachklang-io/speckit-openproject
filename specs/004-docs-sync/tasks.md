---

description: "Task list for feature 004: documentation sync to the feature work package"
---

# Tasks: Documentation Sync to the Feature Work Package

**Input**: Design documents from `specs/004-docs-sync/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R10), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution principle IV requires schema, decision-table and summary-block tests and executed prompt scenarios (S18–S21 in `docs/TESTING.md`).

**Organization**: Grouped by user story. The shipped runtime is one Markdown prompt (`extension/commands/sync-docs.md`), so prompt-editing tasks touch the same file and are **not** marked `[P]`; they build the prompt up section by section. Tasks that edit `tests/test_prompt_sync.py` are likewise sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US4 as numbered in `spec.md` (US1 publish, US2 update only what changed, US3 preview and safe writes, US4 stop when uploads are not possible)
- The installed command is self-contained: it uses **capability ids only**; concrete tool names appear once, in the capability rows embedded in the prompt (constitution II). Embedded blocks: `capability-map`, `config-rules`, `ledger-rules`, `decision-table`.
- Tasks marked **(maintainer)** need the maintainer's test instance or an admin action; they are never claimed done without an executed run. The only deletion this project performs is the replaced attachment it uploaded itself (ADR-0004); the maintainer removes test work packages and any other test data by hand.

## Path Conventions

Monorepo: `extension/`, `preset/`, `schemas/`, `tests/`, `docs/`, `.specify/memory/`. `preset/` and `extension/commands/sync-status.md` are touched only for the additive `documents` ledger key (plan, research R3).

---

## Phase 1: Setup (constitution, live facts, schema)

- [X] T001 (done 2026-10-06, maintainer decision) Amend principle III in `.specify/memory/constitution.md`: after "Deletions are never performed by this project." add "Exception: an attachment this project uploaded itself, identified by the ledger, may be deleted when a newer version of the same document replaces it, and only after the plan was shown and confirmed."; version 1.1.0 → 1.2.0, `Last Amended` 2026-10-06; add `docs/adr/0004-attachment-replacement-deletes-own-uploads.md` (context, decision, consequences, rejected alternatives: versioned names that accumulate, per-file confirmation); update the "Hard rules" mention in `CLAUDE.md` only if it contradicts the amended text ("This project never deletes work packages" stays true)
- [X] T002 **(maintainer, run from the main session; done 2026-10-06 with the maintainer's go-ahead: scratch work package 113 and attachment 4 remain in the sandbox for the maintainer to delete by hand; the first description update was confirmed without a preview call, later checks used previews)** Task 0 of the plan, closes research R1, R4, R5, R9 against the sandbox: with `OPENPROJECT_ATTACHMENT_ROOT` set to a directory containing the scratch project, create one scratch work package `VERIFY-004 ...`, then record (a) `create_work_package_attachment` preview and confirm for a small file (attachment name, id in the result, behaviour for a file outside the root), (b) `list_work_package_attachments` fields (id, file name, size or digest?), (c) `delete_attachment` parameters and whether it has a confirm step, (d) `update_work_package` description with the marker block of R4 and an `attachment:<name>` link, then `get_work_package` with `select=["description"]`: do the markers and the link survive byte for byte, is the description raw Markdown; (e) fallback decisions if not. Save secret-free responses as fixtures under `tests/fixtures/docs/` (`attachments-*.json`, `description-roundtrip.json`, `README.md` with date and versions), update `research.md` (R1, R4, R5, R9: verified or fallback chosen) and `docs/mcp-tool-map.md` (parameters, "Verified" column). Blocks T011 (depends on nothing; may run beside T001)
- [X] T003 [P] Add `documents` to `schemas/mapping.schema.json` exactly as in `contracts/schema-changes.md` (top-level optional; `propertyNames` enum `spec.md`, `plan.md`, `research.md`, `data-model.md`; entry keys `hash` (pattern `^[0-9a-f]{64}$`), `attachment_id` (integer, minimum 1), `synced` (pattern `^\d{4}-\d{2}-\d{2}$`), `pending_delete` (integer, minimum 1); required `hash`, `attachment_id`, `synced`; `additionalProperties: false`); do not change top-level `required` or `schema_version`
- [X] T004 [P] Add ledger fixtures `tests/fixtures/mapping/valid-with-documents.json` (feature item plus two documents, one with `pending_delete`), `invalid-documents-unknown-name.json` (`notes.md`), `invalid-documents-hash.json` (63 hex chars), `invalid-documents-missing-id.json`

---

## Phase 2: Foundational (blocks all stories)

**Purpose**: schema tests, tool map, ledger-rules in all prompts, decision table with tests, prompt frame and manifest. No story can be written before the table and the frame exist.

- [X] T005 Extend `tests/test_schemas.py`: `valid-with-documents` validates, the three invalid fixtures are rejected, every ledger fixture that was valid before is still valid (depends on T003, T004)
- [X] T006 (done together with T002) Update `docs/mcp-tool-map.md`: add rows `create-attachment` (`create_work_package_attachment`: work_package_id, file_path, description, confirm), `list-attachments` (`list_work_package_attachments`) and `delete-attachment` (`delete_attachment`) with the parameters recorded in T002; "Verified" = yes only for what T002 ran (depends on T002)
- [X] T007 Add `documents` to the `ledger-rules` block in `preset/commands/speckit.taskstoissues.md` and `extension/commands/sync-status.md` exactly as in `contracts/schema-changes.md` (top-level keys gain `documents`; one line for the documents keys); neither prompt writes it; bump `preset/preset.yml` patch version and `extension/extension.yml` is bumped in T013 (depends on T003)
- [X] T008 [P] Add `tests/docs_reference.py`: a reference implementation of the decision table of research R6 (`classify(local_hash, ledger_entry, attachment_ids)` → action, writes) and of the summary block of R4/R5 (`render_block(ledger_documents, link_paths)` where `link_paths` maps a document to the `download_url` path of its attachment with scheme and host removed, or `None` for the backtick fallback; `link_path(download_url)`; `strip_wrapper(description)` that removes exactly the outer `<user-content>` and `</user-content>` (R9); `replace_block(description, block)` with the marker rules and error states); a header comment states that it mirrors the `decision-table` block of the prompt and is used only by tests
- [X] T009 Add `tests/fixtures/docs/decision-table.json`: one case per row of research R6 plus `pending_delete` present and still on the work package, `pending_delete` already gone, `spec.md` missing (stop), optional document absent (skip), a description returned with the `<user-content>` wrapper (taken from `description-roundtrip.json`) and one with `description_truncated: true` (stop before the description step, attachments reported as done); expected action, writes and new ledger entry; and `summary-*.md` fixtures (empty description, description with text before and after the markers, markers duplicated, end before begin) (depends on T008)
- [X] T010 Add `tests/test_docs_decision.py`: every case of T009 gives the expected result; applying a result and classifying again yields `unchanged` for every document (idempotence, SC-002); `replace_block` keeps all text outside the markers byte for byte (SC-001) and refuses the inconsistent marker states; `render_block` of the same ledger and link paths is identical twice, orders rows spec, plan, research, data-model, contains a path-only link (no scheme, no host) or the backtick fallback; `strip_wrapper` removes the wrapper and `replace_block` output is written without it; `link_path` never returns a host (depends on T009)
- [X] T011 Extend `tests/test_prompt_sync.py` for `extension/commands/sync-docs.md`: join the parametrized prompts (capability subset in table order, no tool name outside the block, `config-rules` match the schema); `ledger-rules` identical to the other two prompts and to `schemas/mapping.schema.json`; the `decision-table` block lists exactly the rows of `tests/docs_reference.py`; the capability block contains no `create-work-package` or `delete-work-package` row; the prompt contains `<user-content>`, `untrusted data`, "Every run starts from scratch", `Dry run: nothing was written.`, `<redacted-host>`, `<redacted-secret>`, `OPENPROJECT_ATTACHMENT_ROOT` and the five result words (red until T012 exists, by design: test first) (depends on T008)
- [X] T012 Create `extension/commands/sync-docs.md` with the frame: frontmatter (`description`, `argument-hint: "[feature] [--dry-run]"`, `tools: ['openproject-ce-mcp/*']`), `## User Input`, the arguments sentence, the embedded `capability-map` block (rows `get-work-package`, `update-work-package`, `create-attachment`, `list-attachments`, `delete-attachment`, copied from `docs/mcp-tool-map.md`), failure classes (rejected, tool error with generic text and redaction, not found), the `config-rules`, `ledger-rules` and `decision-table` blocks (rows of research R6), the summary block text of R4 (or its fallback from T002) and the statement of the hard limits of `contracts/command-contract.md` (depends on T001, T002, T006, T007, T010, T011)
- [X] T013 Register the command in `extension/extension.yml`: version 0.0.3 → 0.0.4, `provides.commands` entry `speckit.openproject.sync-docs` (`commands/sync-docs.md`, description from the contract), no hook (depends on T012)

**Checkpoint**: `uv run pytest` is green; the prompt has a frame but no steps yet.

---

## Phase 3: User Story 1 - Publish the design documents (Priority: P1) MVP

**Goal**: spec and plan (and optional documents) are attached to the feature work package, the description holds the generated summary, the ledger records hash and attachment id.

**Independent Test**: S18: first sync; two attachments, summary block, ledger `documents`; second run `no changes`.

- [X] T014 [US1] In `extension/commands/sync-docs.md` write steps 1–3: prerequisites and arguments (feature directory; `FEATURE`), read config (`project`) and ledger (`items.feature.id`, `documents`) and stop with a message naming the file; read the documents and compute SHA-256 with `shasum -a 256` (or `sha256sum`); `get-work-package` for the feature work package (stale → stop) and `list-attachments`; warn when `plan.md` is missing and skip absent optional documents (`research.md`, `data-model.md`) silently; classify with the decision table and print the plan table (document, local hash, ledger hash, attachments found, action, reason) (depends on T013)
- [X] T015 [US1] In the same file write the `new` path of step 5: upload with `create-attachment` (absolute path of the document, preview, then confirm), obtain the new attachment id (source as verified in T002), take the attachment id from the confirm result and never use or print its `download_url` host (only the path part, R5), then write `documents.<file>` (`hash`, `attachment_id`, `synced` = today) into the ledger right after the upload via a temporary file and rename (depends on T014)
- [X] T016 [US1] In the same file write step 6: render the summary block from the ledger and the link paths (path of each attachment's `download_url` from `list-attachments`, host removed; fallback: file name in backticks, R5) exactly as R4 defines it, `get-work-package` again for the description (`select` description, lock version, truncation flag; truncated → stop before this step, attachments reported as done), strip the `<user-content>` wrapper (R9), replace or append the block with the marker rules (inconsistent markers: stop and name it), `update-work-package` with preview then confirm only if the text differs (depends on T015)
- [X] T017 [US1] **(maintainer)** Run S18 through the installed skill in `.scratch/proj` (`--dry-run` first, then real, then again for `no changes`); check that neither the description nor the report contains a host or a token, record the run, versions and result in `docs/TESTING.md`, including the elapsed time and the number of confirmations for four documents (SC-006: one confirmation, under 2 minutes of user time) (depends on T013, T016)

**Checkpoint**: first publication works and is repeatable without writes.

---

## Phase 4: User Story 2 - Update only what changed (Priority: P1)

**Goal**: a changed document is replaced (upload first, then delete the replaced attachment), unchanged documents cause no write, interrupted runs recover.

**Independent Test**: S19: one line changed in `spec.md` gives one new attachment, the old one gone, `plan.md` untouched, summary updated.

- [X] T018 [US2] In `extension/commands/sync-docs.md` write the `changed` path: upload (as T015), ledger (`attachment_id` new, `pending_delete` old id, new hash, `synced`), `delete-attachment` for the old id (with its confirm step if T002 found one), ledger (remove `pending_delete`); the old id is only ever taken from the ledger, never from the attachment list (depends on T016)
- [X] T019 [US2] In the same file write the remaining rows: `unchanged` (no call, no ledger write), `restored` (upload only), `orphan` and `blocked` (report only, nothing deleted, reason names the attachment ids), `cleaned` for a `pending_delete` that still exists or is gone, and the order of documents (spec, plan, research, data-model) (depends on T018)
- [X] T020 [US2] **(maintainer)** Run S19 (change one line, real run; then no change) through the installed skill; verify attachment content in the UI and the text outside the markers is identical; record in `docs/TESTING.md` (depends on T019)

---

## Phase 5: User Story 3 - Preview, safe writes and an honest report (Priority: P2)

**Goal**: plan before every write, `--dry-run`, one confirmation, failures isolated, accurate report.

**Independent Test**: S20: dry run changes nothing; interruption after the upload recovers without duplicates; a foreign attachment with a document's name is `blocked`.

- [X] T021 [US3] In `extension/commands/sync-docs.md` write steps 3–4 around the plan: `--dry-run` ends with `Dry run: nothing was written.` and result `dry run`; otherwise ask for confirmation once for the whole plan and stop on "no" (depends on T019)
- [X] T022 [US3] In the same file write failure handling and the report (step 7): a failed document does not stop the others; error text with URLs and host names replaced by `<redacted-host>` and secrets by `<redacted-secret>`; counts attached, replaced, restored, cleaned, unchanged, orphan, blocked, failed, skipped; result `complete`, `incomplete`, `no changes`, `dry run` or `stopped` (`no changes` only if nothing was written, not even the ledger) (depends on T021)
- [X] T023 [US3] **(maintainer)** Run S20: dry run with checksums of ledger and attachment list before and after; interrupt a real run after the upload (stop the session at the delete step) and rerun; delete `plan.md`'s attachment in the UI and rerun; add a foreign attachment named `spec.md` to a scratch state and rerun; record in `docs/TESTING.md` (depends on T022)

---

## Phase 6: User Story 4 - Clear stop when uploads are not possible (Priority: P2)

**Goal**: missing capability and other stop conditions end with a specific message and zero writes.

**Independent Test**: S21 on a server without upload root and on broken inputs.

- [X] T024 [US4] In `extension/commands/sync-docs.md` write step 0 and the stop conditions of `contracts/command-contract.md`: capability `create-attachment` not callable → stop naming the capability and `OPENPROJECT_ATTACHMENT_ROOT` (also with `--dry-run`, before any read-for-write step); missing config or ledger, no `items.feature.id`, missing `spec.md`, stale work package, MCP server not connected, inconsistent markers; oversize or rejected upload is a `failed` document with the server's reason, not a stop; when the server rejects the path, the message also names the upload root (`OPENPROJECT_ATTACHMENT_ROOT` must contain the feature directory) as the likely cause (depends on T022)
- [ ] T025 [US4] **(maintainer)** Run S21: start the server without `OPENPROJECT_ATTACHMENT_ROOT` (tool absent) for the capability stop in `--dry-run` and real mode; no `spec.md`; no ledger; broken markers in the description; record in `docs/TESTING.md` (depends on T024)

---

## Phase 7: Polish & Cross-Cutting

- [X] T026 [P] Update `extension/README.md`: usage and arguments, upload-root prerequisite and how to set it in the MCP client config, what it reads and writes (attachments, one description block, ledger `documents`), the decision table in plain words, the deletion exception, limitations and untested paths
- [X] T027 [P] Update `docs/ARCHITECTURE.md`: docs sync flow, ledger `documents`, upload root as MCP server prerequisite; update the status line of `docs/adr/0003-docs-sync-without-wiki-pages.md` ("re-verified 2026-10-06 in feature 004" if T002 confirms no wiki write tool) and `docs/ROADMAP.md`
- [ ] T028 Update `docs/TESTING.md`: scenarios S18–S21 in the checklist, "Untested after feature 004" (command mode (FR-014: the command-mode name is not run), `research.md`/`data-model.md` documents, files above the server's size limit, crash between upload and ledger write, concurrent description edit) (depends on T017, T020, T023, T025)
- [X] T029 Run `scripts/dev-install.sh`; confirm `specify preset list` and `specify extension list` show `openproject` in both and that `.claude/skills/speckit-openproject-sync-docs` exists in the scratch project (depends on T013, T024)
- [ ] T030 Run `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`; all green (depends on T029)
- [ ] T031 Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff; fix findings or record the reason for not fixing; rerun once after the last prompt change (depends on T030)
- [ ] T032 Mark finished tasks in this file, prepare the PR description (summary, executed scenarios, untested paths, the constitution amendment called out); opening the PR is the maintainer's call (depends on T028, T031)

---

## Dependencies & Execution Order

- Phase 1 (T001, T002, T003, T004 largely parallel) → Phase 2 (T012 needs T001, T002) → US1 → US2 → US3 → US4 (each builds on the prompt steps before it) → Polish.
- The prompt is written only after T002: the upload name, the id source, the marker survival and the link syntax decide its text.
- Within the prompt, tasks T014–T016, T018–T019, T021–T022, T024 are sequential edits of one file.
- Maintainer runs (T002, T017, T020, T023, T025) need the sandbox and the upload root; T017 can only start after T013 and T016.

## Parallel Opportunities

- T001, T002, T003, T004 together; T008 beside T005–T007; T026 and T027 beside any maintainer run.

## Implementation Strategy

- **MVP**: Phases 1–3 (US1): first publication works, repeatable, no deletion yet.
- Then US2 (replacement and deletion, needs T001 landed), US3 (preview, report), US4 (stop conditions). Do not open the PR before `/speckit-analyze` is clean and S18–S21 results are recorded.
