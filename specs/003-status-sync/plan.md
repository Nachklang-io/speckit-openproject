# Implementation Plan: Status Sync between OpenProject and tasks.md

**Branch**: `003-status-sync` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-status-sync/spec.md`

## Summary

Add the extension command `speckit.openproject.sync-status` (`extension/commands/sync-status.md`): a numbered prompt that reads config, ledger and `tasks.md` from disk, reads status and assignee of every task work package through the MCP server, classifies each task with a fixed decision table (checkbox, OpenProject status, last synced status), shows a plan, and after one confirmation applies pulls (checkbox edits, ledger) and pushes (`update-work-package` with `status`, preview then confirm). OpenProject wins every conflict; the command never reopens, creates, deletes or re-parents a work package. An optional hook after `implement` offers the command. As in 001 and 002 no runtime code is shipped: correctness rests on the prompt, the schemas, a fixture-driven reference implementation of the decision table in the tests, prompt-sync tests and manual scenarios S14–S17 run through the installed skill.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff (already in `pyproject.toml`). Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1

**Storage**: reads `.specify/openproject/config.yml`; reads and writes `.specify/openproject/mapping-<feature>.json` (ledger) and the checkbox characters of `specs/<feature>/tasks.md`

**Testing**: pytest (schema, manifest, prompt sync, decision table against fixtures, `tasks.md` edit rule); manual scenarios S14–S17 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit extension (prompt package) in a monorepo, plus one additive ledger schema change

**Performance Goals**: SC-004: 14 work packages, one confirmation, under 3 minutes of user time; one `get-work-package` per task (no list endpoint returns the assignee reliably, see R3)

**Constraints**: MCP-only (ADR-0002); no secrets, hosts or URLs in files or output; writes only through preview-then-confirm; ledger updated right after each write; `tasks.md` edits touch checkbox characters only and are atomic; no deletes; shipped keys stable (assignee is additive)

**Scale/Scope**: one feature per run, tens of tasks

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | specify → clarify → plan; tasks and analyze follow |
| II MCP-only | Pass | capability ids only, rows embedded from the tool map; no REST |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass | `--dry-run`, plan table, one confirmation, preview/confirm per write, ledger written after each write, decision table makes a second run a no-op (SC-002), nothing is deleted or reopened |
| IV Test-first incl. prompts | Pass, with caveat | decision table has a reference implementation and fixtures in pytest; S14–S17 manual; the transition check (R4) is **unverified** and is labelled untested until S14 ran |
| V Compatibility | Pass | skills + command mode; schema change additive; hook key follows the bundled spec-kit extensions (R7) |
| VI Simplicity/transparency | Pass | no scripts; conflicts and blocked tasks are named, never guessed |

Post-design re-check: Pass. Open risk, not a violation: R4 (how the server rejects a forbidden transition) decides the wording of the blocked message; the prompt is written so that either outcome ends in `blocked`, and the task list verifies it live before the push step is accepted.

## Project Structure

### Documentation (this feature)

```text
specs/003-status-sync/
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
├── extension.yml                          # version 0.0.3, new command, hooks.after_implement (optional)
├── README.md                              # usage, rules, untested paths
└── commands/sync-status.md                # the command prompt; embeds capability rows, config-rules (statuses), ledger-rules, decision-table
schemas/
└── mapping.schema.json                    # + optional assignee per item
preset/
└── commands/speckit.taskstoissues.md      # ledger-rules block gains "assignee" (accepted, never written)
tests/
├── fixtures/
│   ├── sync/{decision-table.json,tasks-*.md,ledger-*.json,wp-*.json}   # secret-free
│   └── mapping/{valid-with-assignee,invalid-assignee-type}.json
├── sync_reference.py                      # reference implementation of the decision table (test helper only)
├── test_sync_decision.py                  # table cases + idempotence + checkbox-only edit
├── test_schemas.py                        # extend
├── test_prompt_sync.py                    # parametrize over the third prompt; decision-table block
└── test_manifests.py                      # hook references an existing command
docs/
├── mcp-tool-map.md                        # update-work-package row gains `status`; get-work-package stays
├── ARCHITECTURE.md                        # sync policy, assignee in the ledger
└── TESTING.md                             # S14–S17 and run results
```

**Structure Decision**: Existing monorepo layout. The feature adds one command file to `extension/`, one optional ledger key to `schemas/` (and the identical rule line to the preset prompt so that its ledger validation accepts it), tests and docs.

## Complexity Tracking

No constitution violations.

## Risks

1. **Transition check is unverified.** `get_project_work_package_context` narrows statuses per type, not per current status. The server may reject a forbidden transition in the update preview (`state: rejected`, readable `validation_errors`) or fail with a generic client error. Mitigation: R4 defines the rule for both outcomes (rejected preview or tool error on the preview → `blocked`, no confirm call); S14 includes a restricted workflow set up in the admin UI by the maintainer.
2. **`get_work_package` field names for status and assignee are unverified in the tool map.** Mitigation: first task records a live response as a fixture; the prompt reads status by name and id and stops with a specific message if the fields are absent.
3. **Agent edits of `tasks.md`.** A wrong regex could damage the file. Mitigation: a single edit rule (`- [ ]`/`- [x]` at line start of a line whose task key matches), SHA-256 of the whole file before the read and again before the write, write through a temporary file, S14 compares a diff, the test helper implements the same rule on fixtures.
4. **Interrupted run between a push and the ledger write.** Mitigation: the ledger is written after each successful push; a repeated run reads the current status, sees done on both sides and records it.
5. **Touching the preset prompt (ledger-rules) affects feature 001.** Mitigation: only the `assignee` key is added; existing 001 tests must pass unchanged apart from that line.
