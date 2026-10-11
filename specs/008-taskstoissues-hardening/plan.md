# Implementation Plan: taskstoissues Hardening

**Branch**: `008-taskstoissues-hardening` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-taskstoissues-hardening/spec.md`

## Summary

Four fixes in the preset command `speckit.taskstoissues` (`preset/commands/speckit.taskstoissues.md`), released as preset 1.0.3: (1) the plan table has one row per key with `hash` and `stored` columns, never ranges, printed in parts of at most 40 rows (#23); (2) a read-only lookup of the user's work package permissions in the project (`list_capabilities`) stops a role that can read but not create with a "missing write permission" message before `list-types`, and lets every unclear case through (#22); (3) step 1 handles a non-zero exit of the prerequisite script by printing its message and naming the missing file and the command for the current mode (#21); (4) both READMEs state that the `generic` integration gets no preset override (#20). No config key, ledger or schema change.

Research changed the brief in one point: `can_update` from `get_my_project_access` describes the membership record, not work package rights, so the check lists the project's capabilities and stops only with positive evidence (read listed, create missing), instead of building a capability id by hand (research R1, analysis F1). It also corrected the spec's precedence rule for two missing files (R4).

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff (already in `pyproject.toml`). Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1 (live-checked on 0.4.2)

**Storage**: none new; the mapping ledger and `config.yml` are read as today

**Testing**: pytest prompt-sync tests (capability map rows in the prompt and in `docs/mcp-tool-map.md`, plan table rule, step 1 and step 5 wording, README note); scenarios S-large, S-plan, S1/S2 regression, S7b in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit preset (prompt package) in a monorepo

**Performance Goals**: one `get-my-access` call plus one to three `list-capabilities` pages (50 per page) per run; no extra writes

**Constraints**: MCP-only (ADR-0002); no secrets, hosts or URLs in files or output (the capability result's `url` is never printed); nothing is written on any new stop path; behavior of every working path unchanged (FR-010)

**Scale/Scope**: plans up to several hundred rows (printed in parts)

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | specify → plan; tasks and analyze follow before any prompt edit |
| II MCP-only | Pass | two read capabilities (`get-my-access`, `list-capabilities`) added to the single map (`docs/mcp-tool-map.md`) and the prompt's embedded map; no REST |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass | new stop paths write nothing, also in `--dry-run`; the plan becomes more complete, which strengthens the confirmation; no write path changes |
| IV Test-first incl. prompts | Pass, with caveat | prompt-sync tests first; S7b needs a read-only user and may stay untested, then labelled so (R2) |
| V Compatibility | Pass | skills and command mode named in the step 1 message; no config key; patch version 1.0.3; spec-kit ≥ 1.1.0 unchanged |
| VI Simplicity/transparency | Pass | two read calls, one table rule, one message; limitations documented (generic, informational capabilities) |

Post-design re-check: Pass. The one risk is a false "missing permission" (R2); it is limited to positive evidence (read listed, create missing) and covered by an allowed-case regression run.

## Project Structure

### Documentation (this feature)

```text
specs/008-taskstoissues-hardening/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── command-contract.md
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
preset/
├── preset.yml                          # version 1.0.3
├── README.md                           # generic note
└── commands/speckit.taskstoissues.md   # step 1, step 5 (permission), step 9 (plan table), capability map
docs/
├── mcp-tool-map.md                     # two rows: get-my-access, list-capabilities
└── TESTING.md                          # scenarios S-large, S-plan, S7b; run log
tests/
├── test_prompt_sync.py                 # new checks
README.md                               # generic note
bundle/bundle.yml                       # pin 1.0.3 (release PR, not in this feature)
CHANGELOG.md                            # Unreleased entry for preset
```

**Structure Decision**: prompt-only change in one command file plus two docs and tests; versions and bundle pin move in the release PR, as for 007.

## Complexity Tracking

No violations.
