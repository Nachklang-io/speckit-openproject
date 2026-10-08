# Implementation Plan: Versions and Time Tracking

**Branch**: `005-versions-and-time` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-versions-and-time/spec.md`

## Summary

Add two extension commands as numbered prompts, no shipped runtime code:

- `speckit.openproject.sync-version` (`extension/commands/sync-version.md`): resolves the feature's version name (argument, else `defaults.version`, else the feature directory name), finds the version in the project by exact name, creates it once after the shown plan is confirmed, and assigns every work package of the ledger that has no version yet. Work packages in another version are reported, never moved. Ledger gets an optional top-level `version` object (id, name).
- `speckit.openproject.log-time` (`extension/commands/log-time.md`): parses user-supplied lines (`<task key>: <duration> [on <date>]`), validates them, reads the project's activities, shows a plan, and after one confirmation creates one time entry per item (`create_time_entry`, preview then confirm). A re-run is recognised by a ledger key (work package, date, activity, hours) or by an explicit `--entry-key`. Ledger gets an optional top-level `time_entries` array.

Both commands share the stop rules, plan/dry-run/confirm flow and report shape of features 001–004. Correctness rests on the prompts, additive schema changes, fixture-driven reference implementations of the two decision tables and the duration parser in the tests, prompt-sync tests, and manual scenarios S22–S25 run through the installed skills.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff. Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1 with `OPENPROJECT_ENABLE_VERSION_WRITE=true` (version command) and the time-entry write enabled (log-time; flag name verified in T001)

**Storage**: reads `.specify/openproject/config.yml` and the ledger `.specify/openproject/mapping-<feature>.json`; writes the ledger (new optional keys `version`, `time_entries`); writes a version, work package version fields and time entries in OpenProject

**Testing**: pytest (schemas, manifests, prompt sync, version decision table, duration parser, time-entry key and plan); manual scenarios S22–S25 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit extension (prompt package) in a monorepo, plus additive ledger and config schema changes

**Performance Goals**: SC-007: ten work packages (version) or five entries (time), one confirmation, under 2 minutes of user time. Version run: one `list_versions`, one `get_version`, one `get_work_package` per ledger item (select fields only), writes batched in one `bulk_update_work_packages` preview/confirm pair. Time run: one `list_time_entry_activities`, one `get_work_package` per distinct work package, one preview/confirm pair per entry

**Constraints**: MCP-only (ADR-0002); no secrets, hosts or URLs in files or output; writes only through preview-then-confirm; ledger updated right after each write (after each confirmed bulk call for assignments, see R6); no deletes or edits of versions, time entries or other data (FR-008); work packages in another version are never moved

**Scale/Scope**: one feature per run; version command up to ~100 work packages; time command up to ~20 items

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | specify → clarify (session 2026-10-07) → plan; tasks and analyze follow |
| II MCP-only | Pass | capability ids resolved through `docs/mcp-tool-map.md` rows embedded per prompt |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass | `--dry-run`, plan table, one confirmation, preview/confirm per write, ledger after each write, unchanged inputs are a no-op (SC-002), no deletions at all |
| IV Test-first incl. prompts | Pass, with caveat | decision tables and parser have reference implementations and fixtures; S22–S25 manual; T001 live check precedes the prompts; commands untested until S22–S25 ran |
| V Compatibility | Pass | skills + command mode; schema changes additive (`schema_version` stays 1.0); new config key is optional |
| VI Simplicity/transparency | Pass | no scripts; ambiguous states are `blocked` and named, never guessed; the activity is asked, not guessed |

Post-design re-check: Pass. No amendment needed. Open risks are in the Risks section.

## Project Structure

### Documentation (this feature)

```text
specs/005-versions-and-time/
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
├── extension.yml                          # version 0.0.4 → 0.0.5, two new commands
├── README.md                              # usage, server flags, untested paths
└── commands/
    ├── sync-version.md                    # embeds capability rows, config-rules, ledger-rules, decision table
    └── log-time.md                        # embeds capability rows, config-rules, ledger-rules, duration grammar
schemas/
├── mapping.schema.json                    # + optional top-level `version`, `time_entries`
└── config.schema.json                     # + optional `defaults.activity`
preset/commands/speckit.taskstoissues.md   # ledger-rules / config-rules lines gain the new keys (accepted, never written)
extension/commands/{sync-status,sync-docs}.md  # same rule-line change (prompt-sync keeps blocks identical)
tests/
├── fixtures/
│   ├── version/{decision-table.json,versions-*.json,wp-*.json}      # secret-free
│   ├── time/{durations.json,plan-*.json,ledger-*.json}
│   └── mapping/{valid-with-version-and-time,invalid-version-*,invalid-time-*}.json
├── version_time_reference.py              # reference implementation: version decision table, duration parser, entry key (test helper only)
├── test_version_decision.py
├── test_time_entries.py
├── test_schemas.py                        # extend
├── test_prompt_sync.py                    # parametrize over the new prompts
└── test_manifests.py                      # unchanged logic, new commands
docs/
├── mcp-tool-map.md                        # rows: list-versions, get-version, create-version, bulk-update-work-packages, list-time-activities, create-time-entry
├── ARCHITECTURE.md                        # version and time flows, ledger keys
├── ROADMAP.md                             # 005 status
└── TESTING.md                             # S22–S25 and run results
```

**Structure Decision**: Existing monorepo layout. Two new command files in `extension/`, additive keys in the two schemas and the identical rule lines in the existing prompts that validate the ledger or config, tests and docs. No ADR: no principle is touched.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| Two commands instead of one | Different inputs, tools, flags and cadence (once per feature vs. repeatedly while working) | One command with modes would need two plans and two stop rule sets in one prompt |
| `time_entries` ledger array | Spec Q1: re-run recognition by key | Reading OpenProject entries was declined in clarification |
| `defaults.activity` config key | Spec FR-006 "configured default" | Asking every run is tedious for a developer logging time daily |

## Risks

1. **Resolved by T001 (2026-10-07, live sandbox check, see research.md R1).** No separate time-entry write flag exists: `create_time_entry` and the other time-entry writes are registered under the same `work_package` write scope as `update_work_package`/`bulk_update_work_packages`, gated by the already-set `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE`. The capability check for log-time is therefore identical in shape to the one for sync-version/other work-package writes: "tool is not in the tool list" means the capability is missing, naming `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE`. T001 also found and fixed a design bug: the plan's assumed `version` write parameter (singular, on `update_work_package`/`bulk_update_work_packages`) is silently ineffective on the verified server build; the correct parameter is `target_versions` (a list). R1, R3 and R4 in research.md are corrected accordingly — **sync-version.md must write `target_versions`, and must compare a work package's current version by name (not id), since `get_work_package` returns the version as a name string.**
2. **Crash between a confirmed write and the ledger write.** For a time entry the next run cannot recognise it and would create a duplicate (window: one tool call). Accepted and documented; the report tells the user to check the work package after an interrupted run. Version creation is safe (found by name on re-run); assignments are safe (read from the work package).
3. **Version name lookup.** `list_versions(project, search)` is a substring search and may include versions shared from other projects; the command post-filters for the exact name and treats more than one match as `blocked`.
4. **Closed or locked version.** Assignment to such a version is rejected by OpenProject; the command reads the status first (`get_version`) and stops with a message (edge case in spec).
5. **Bulk update partial failures.** `bulk_update_work_packages` reports per item; the ledger records only the version, assignments are re-derived from OpenProject on every run, so a partial failure is repaired by the next run.
6. **Touching existing prompts (rule lines)** affects features 001–004. Mitigation: only the new optional keys are added; their tests must pass unchanged apart from those lines.
7. **Hours resolution.** Durations are normalised to whole minutes and sent as ISO 8601 (`PT1H30M`); finer input is rejected in the plan, not rounded silently.
