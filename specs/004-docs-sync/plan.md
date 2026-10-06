# Implementation Plan: Documentation Sync to the Feature Work Package

**Branch**: `004-docs-sync` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-docs-sync/spec.md`

## Summary

Add the extension command `speckit.openproject.sync-docs` (`extension/commands/sync-docs.md`): a numbered prompt that reads config, ledger and the feature's design documents from disk, hashes each document (SHA-256 of the file bytes), compares hash, ledger and the attachments currently on the feature work package with a fixed decision table, shows a plan, and after one confirmation uploads new or changed documents (`create_work_package_attachment`, preview then confirm, file path under the server's upload root), deletes the replaced attachment it uploaded earlier, and rewrites one generated summary block in the work package description. The ledger gets a new optional top-level `documents` object (hash, attachment id, sync date, optional pending deletion) and is written right after each write. Constitution principle III gets a narrow deletion exception (ADR-0004, constitution 1.2.0). As in 001–003 no runtime code is shipped: correctness rests on the prompt, the schemas, a fixture-driven reference implementation of the decision table in the tests, prompt-sync tests and manual scenarios S18–S21 run through the installed skill.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff. Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1 started with `OPENPROJECT_ATTACHMENT_ROOT` set (otherwise the upload tool is not registered)

**Storage**: reads `.specify/openproject/config.yml` and `specs/<feature>/{spec,plan,research,data-model}.md`; reads and writes `.specify/openproject/mapping-<feature>.json` (ledger); writes attachments and one description block in OpenProject

**Testing**: pytest (schema, manifest, prompt sync, decision table and summary block rendering against fixtures); manual scenarios S18–S21 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit extension (prompt package) in a monorepo, plus an additive ledger schema change and a constitution amendment

**Performance Goals**: SC-006: four documents, one confirmation, under 2 minutes of user time; one `list_work_package_attachments` plus one `get_work_package` per run

**Constraints**: MCP-only (ADR-0002); no secrets, hosts or URLs in files or output (attachment links are path-only, host removed, R5); writes only through preview-then-confirm; ledger updated right after each write; deletes only attachments this command uploaded and replaced; the file handed to the upload tool must lie under the server's upload root (R1)

**Scale/Scope**: one feature per run, at most four documents

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | specify → clarify → plan; tasks and analyze follow |
| II MCP-only | Pass | capability ids only, rows embedded from the tool map; no REST, no reading of the upload root setting |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass (amendment landed 2026-10-06, ADR-0004, constitution 1.2.0) | `--dry-run`, plan table, one confirmation, preview/confirm per write, ledger after each write, unchanged inputs are a no-op (SC-002). "Deletions are never performed" conflicts with replacing an attachment: resolved by the maintainer's decision of 2026-10-06 to amend III (exception: attachments uploaded by this project, ledger id, only when replaced, only after the confirmed plan) via ADR-0004 and constitution 1.2.0. The amendment was task T001 (done) |
| IV Test-first incl. prompts | Pass, with caveat | decision table and summary rendering have a reference implementation and fixtures; S18–S21 manual; Task 0 (T002) ran on 2026-10-06; the full command is untested until S18–S21 ran |
| V Compatibility | Pass | skills + command mode; schema change additive (`schema_version` stays 1.0) |
| VI Simplicity/transparency | Pass | no scripts; ambiguous states are `blocked` and named, never guessed |

Post-design re-check: Pass given T001. Open risks are in the Risks section; none is a violation.

## Project Structure

### Documentation (this feature)

```text
specs/004-docs-sync/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── command-contract.md
│   └── schema-changes.md
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
extension/
├── extension.yml                          # version 0.0.3 → 0.0.4, new command
├── README.md                              # usage, upload-root prerequisite, untested paths
└── commands/sync-docs.md                  # the command prompt; embeds capability rows, config-rules, ledger-rules, decision-table
schemas/
└── mapping.schema.json                    # + optional top-level `documents`
preset/
└── commands/speckit.taskstoissues.md      # ledger-rules block gains `documents` (accepted, never written)
extension/commands/sync-status.md          # same ledger-rules change (test_prompt_sync keeps blocks identical)
tests/
├── fixtures/
│   ├── docs/{decision-table.json,summary-*.md,ledger-*.json,attachments-*.json}   # secret-free
│   └── mapping/{valid-with-documents,invalid-documents-*}.json
├── docs_reference.py                      # reference implementation of the decision table and the summary block (test helper only)
├── test_docs_decision.py                  # table cases, idempotence, block replacement keeps outside text
├── test_schemas.py                        # extend
├── test_prompt_sync.py                    # parametrize over the fourth prompt; decision-table block
└── test_manifests.py                      # unchanged logic, new command
docs/
├── adr/0004-attachment-replacement-deletes-own-uploads.md
├── adr/0003-docs-sync-without-wiki-pages.md   # status line: re-verified in feature 004
├── mcp-tool-map.md                        # rows: upload-attachment, list-attachments, delete-attachment
├── ARCHITECTURE.md                        # docs sync flow, ledger `documents`
└── TESTING.md                             # S18–S21 and run results
.specify/memory/constitution.md            # principle III exception, version 1.2.0
```

**Structure Decision**: Existing monorepo layout. One new command file in `extension/`, one additive ledger key in `schemas/` (and the identical rule line in the two existing prompts that validate the ledger), the amendment of principle III, tests and docs.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| Constitution amendment (III) | Replacing an attachment needs one delete | Versioned names that pile up were offered and not chosen by the maintainer |
| `pending_delete` field in the ledger | Makes the "upload first, delete second" order safe after an interruption | Without it the next run cannot tell the superseded attachment from a foreign one |

## Risks

1. **Upload path and name (verified 2026-10-06).** The attachment name is the file's base name; a path outside the upload root fails in the preview with a generic tool error. The upload root is the maintainer's setting and not readable by the command: a rejected path surfaces as a failed document with a message naming the upload-root prerequisite.
2. **Markers and description round trip (verified 2026-10-06).** The comment markers survive byte for byte; the description arrives wrapped in `<user-content>` tags, which the command strips (R9).
3. **Link form (verified 2026-10-06).** `attachment:<name>` renders without `href`; path-only links work and use the `download_url` path (host removed), R5. The upload result contains the instance host in `download_url`: it must never reach a file or the report.
4. **Attachment list fields (verified).** `id`, `file_name`, `file_size_bytes`, `download_url`, no digest; the ledger hash decides what is current. Content edited outside this command is not detected (listed under untested/limitations).
5. **Crash between upload and ledger write.** The next run sees an attachment with the document's name that the ledger does not know: state `blocked` (ambiguous), nothing is deleted, the report names it; the maintainer removes it by hand. Window is one tool call wide; accepted.
6. **Description edited concurrently.** The update carries `lock_version`; a stale write is rejected by the server. The command re-reads the description immediately before the preview and replaces only the block.
7. **Touching the preset and sync-status prompts (ledger-rules)** affects features 001 and 003. Mitigation: only the `documents` key is added; their tests must pass unchanged apart from that line.
