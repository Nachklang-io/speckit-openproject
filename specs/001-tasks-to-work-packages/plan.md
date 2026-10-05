# Implementation Plan: Tasks → Work Packages

**Branch**: `001-tasks-to-work-packages` | **Date**: 2026-10-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-tasks-to-work-packages/spec.md`

## Summary

Harden the preset's `speckit.taskstoissues` override so `tasks.md` becomes a Feature → Phase → Task work package tree in OpenProject, idempotently, with `follows` relations, `--dry-run`, `--update` and a per-phase confirmation. The runtime is a Markdown command prompt driving an OpenProject MCP server; correctness rests on (a) a rewritten, numbered prompt, (b) tightened shared JSON schemas, (c) fixture-based automated tests, and (d) manual scenarios S1–S9 on the test instance. No runtime code is added to the shipped package.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff (already in `pyproject.toml`). Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1

**Storage**: `.specify/openproject/config.yml`, `.specify/openproject/mapping.json` (ledger)

**Testing**: pytest (schemas, manifests, fixtures, install smoke); manual scenarios S1–S9 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit preset (prompt package) in a monorepo

**Performance Goals**: none beyond spec; record call counts in S1 (≈2 calls per item due to preview+confirm)

**Constraints**: MCP-only (ADR-0002); no secrets or instance hosts in files; no deletes; idempotent writes; skills + command mode

**Scale/Scope**: up to 100+ tasks per feature; one feature per run

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | spec → clarify → plan; tasks and analyze follow |
| II MCP-only | Pass | all access via capability map; no REST (contract) |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass | ledger written after each write; search-and-adopt; `--dry-run`; no deletes; stale entries reported |
| IV Test-first incl. prompts | Pass, with caveat | schema/fixture tests added; prompt scenarios S1–S9 manual. Items not yet verified live are labelled in research "Unresolved" |
| V Compatibility | Pass | skills + command mode; `requires.speckit_version` reviewed in tasks |
| VI Simplicity/transparency | Pass | no scripts shipped; ambiguous matches reported, not guessed |

Post-design re-check: Pass. Config key removals are allowed because nothing was ever released (no tags); recorded in research R7. If a release tag exists before merge, this becomes a major bump with migration note.

## Project Structure

### Documentation (this feature)

```text
specs/001-tasks-to-work-packages/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── command-contract.md
│   └── schema-changes.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
preset/
├── preset.yml                          # review requires/provides, bump to 0.2.0
├── openproject-config.template.yml     # new keys, new path in header
├── README.md                           # paths, config, limitations, untested paths
└── commands/speckit.taskstoissues.md   # rewritten prompt, self-contained: embeds capability map + config/ledger rules (research R14)
schemas/
├── config.schema.json                  # + types.feature, - mapping_file, - feature_tag_prefix
└── mapping.schema.json                 # + schema_version, kind, relations
tests/
├── fixtures/
│   ├── config/{valid-*,invalid-*}.yml
│   ├── mapping/{valid-*,invalid-*}.json
│   └── tasks/{s1-tasks.md,s4-tasks.md,s-large-tasks.md}   # large = 120 tasks, dry-run only
├── test_schemas.py                     # extend
├── test_prompt_sync.py                 # embedded blocks == schemas/*.json and docs/mcp-tool-map.md; no URLs/tokens/delete tools in preset/ and fixtures
└── test_tasks_fixtures.py              # fixtures contain expected counts (14 items, relations, 120 tasks)
docs/
├── TESTING.md                          # S1 updated, new S8 (dry-run) and S9 (--update, stale); run results
├── mcp-tool-map.md                     # verified params after live run
└── ARCHITECTURE.md                     # drop the "unify paths" note once done
```

**Structure Decision**: Existing monorepo layout is kept; this feature touches only `preset/`, `schemas/`, `tests/` and docs. `extension/` is untouched.

## Complexity Tracking

No constitution violations.

## Risks

1. Remaining MCP behaviour not verified live: mandatory custom fields (sandbox has none), `update_work_package`. Verified live on 2026-10-05: parent on create, `follows` direction, substring search (see `docs/mcp-tool-map.md`).
2. 100+ tasks means 200+ tool calls in one agent session. Mitigation: per-phase confirmation, resumable ledger.
3. Only the command text is installed into user projects; schemas and the capability map are embedded in the prompt and kept in sync by a test (research R14).
