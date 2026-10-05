# Implementation Plan: Field Discovery and Config Bootstrap

**Branch**: `002-field-discovery` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-field-discovery/spec.md`

## Summary

Replace the placeholder `extension/commands/discover-fields.md` with a numbered command prompt that reads the target project's types, statuses, priorities, versions and mandatory custom fields through the MCP server (read capabilities only), proposes mappings by deterministic rules, shows a numbered change list and diff, and writes `.specify/openproject/config.yml` atomically after approval, editing only approved keys. Additively extend the shared config schema with an optional `statuses` section (open / in_progress / done) and make the preset accept it. As in 001 no runtime code is shipped: correctness rests on the prompt, the schemas, fixture and prompt-sync tests, and manual scenarios S10–S13 run through the installed skill.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff (already in `pyproject.toml`). Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1

**Storage**: `.specify/openproject/config.yml` only (created or edited); no ledger

**Testing**: pytest (schemas, manifests, prompt sync, recorded-response shape); manual scenarios S10–S13 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit extension (prompt package) in a monorepo, plus an additive change to the shared schema and the preset

**Performance Goals**: none beyond spec (SC-001: under 5 minutes of user time); read calls: 1 projects + 1 types + 1 statuses + 3 write contexts

**Constraints**: MCP-only (ADR-0002); read capabilities only; no secrets or hosts in files or output; no OpenProject writes; atomic local write; shipped keys stable; skills + command mode

**Scale/Scope**: one config, one project per run

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | spec → clarify → plan; tasks, analyze follow |
| II MCP-only | Pass | capability ids only; four read rows; no REST (contract) |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass, with note | no OpenProject writes, so no preview/confirm and no ledger; the local write has `--dry-run`, a diff, per-change approval, atomic move, and re-run gives `no changes`; nothing is deleted |
| IV Test-first incl. prompts | Pass, with caveat | schema, sync and shape tests added; S10–S13 manual; untested paths labelled (research "Unresolved") |
| V Compatibility | Pass | skills + command mode; new schema key additive; preset 0.3.0 accepts it; `requires.speckit_version` unchanged |
| VI Simplicity/transparency | Pass | no scripts; every mapping is proposed with a reason and decided by the user; limitations documented |

Post-design re-check: Pass. The preset change (accepting `statuses`) is required, not optional: without it a config written by this command is rejected by `speckit.taskstoissues` (research R8).

## Project Structure

### Documentation (this feature)

```text
specs/002-field-discovery/
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
├── extension.yml                          # version 0.0.2, command description
├── README.md                              # usage, rules, untested paths
└── commands/discover-fields.md            # the command prompt (replaces placeholder); embeds capability rows, config-rules, config-template
preset/
├── preset.yml                             # version 0.3.0
├── openproject-config.template.yml        # + statuses section
├── README.md                              # mention statuses
└── commands/speckit.taskstoissues.md      # config-rules block + statuses (accepted, ignored)
schemas/
└── config.schema.json                     # + statuses
tests/
├── fixtures/
│   ├── config/{valid-with-statuses,valid-hand-edited,invalid-statuses-key,invalid-statuses-empty}.yml
│   └── discovery/{statuses,context-task-mandatory,context-task-plain}.json   # recorded, secret-free
├── test_schemas.py                        # extend
├── test_prompt_sync.py                    # parametrize over both prompts; subset capability check; template block; extension safety rules
└── test_discovery_fixtures.py             # shape the prompt relies on
docs/
├── mcp-tool-map.md                        # + list-statuses, sync rule text
├── ARCHITECTURE.md                        # statuses in config; subset embedding
└── TESTING.md                             # S10–S13 and run results
```

**Structure Decision**: Existing monorepo layout. This feature touches `extension/`, and, only for the additive schema key, `schemas/`, `preset/` (config-rules block, template, version) and tests/docs.

## Complexity Tracking

No constitution violations.

## Risks

1. Line-based YAML editing by an agent can corrupt a hand-edited file. Mitigation: validate before and after writing, write to a temp file and move, diff before approval, S11 compares checksums and parses the result.
2. Proposal rules are name-based; instances with localized or custom type/status names fall through to "ask". Accepted: asking is the safe outcome (VI).
3. Not verified live yet (research "Unresolved"): list-type custom fields, `available_versions` with data, per-project enabled types, command mode. They stay labelled untested until run in S10/S13.
4. Touching the preset prompt and the sync test affects feature 001's guarantees. Mitigation: the subset check keeps the row-identity assertion; the existing 001 tests must pass unchanged apart from the `statuses` additions.
